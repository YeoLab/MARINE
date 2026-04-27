import pandas as pd
import numpy as np
from collections import defaultdict
from scipy import sparse
from copy import copy

complements = {
    'A': 'T',
    'C': 'G',
    'G': 'C',
    'T': 'A',
    'N': 'N'
}

def reverse_complement(input_seq):
    """
    Get the reverse complement of a sequence
    """
    rev_input_seq = reversed(input_seq)
    new_seq = []
    for r in rev_input_seq:
        new_seq.append(complements.get(r))
        
    return ''.join(new_seq)


def incorporate_insertions_and_deletions(aligned_sequence, cigar_tuples, insertions=True, deletions=True, junctions=True):
    """
    Update an aligned sequence to reflect any insertions (take away those positions) such
    that it can be better compared base-to-base to a reference sequence.
    """
    new_seq = ''
    
    current_pos = 0
    
    positions_of_deletions = []
    
    for mod, num_bases in cigar_tuples:
        if mod in [0, 7, 8]:
            # 0 = alignment match, 7 = sequence match, 8 = sequence mismatch
            new_seq += aligned_sequence[current_pos:current_pos+num_bases]
            current_pos += num_bases
        if mod in [1]:
            # insertion -- only do this for aligned sequence, not reference
            if insertions:
                current_pos += num_bases
            
        if mod in [2]:
            # deletion -- only do this for aligned sequence, not reference
            if deletions:
                new_seq += ''.join(['*' for r in range(num_bases)])
        if mod in [3]:
            # N
            if junctions:
                new_seq += ''.join(['n' for r in range(num_bases)])
            
    return new_seq


def get_hamming_distance(str1, str2):
    """Compute the Hamming distance between two equal-length strings.

    Args:
        str1: First string.
        str2: Second string; must be the same length as str1.

    Returns:
        Integer count of positions where str1 and str2 differ.
    """
    assert(len(str1) == len(str2))
    distance = 0
    for i, v1 in enumerate(str1):
        v2 = str2[i]
        if v1 != v2:
            distance += 1
    return distance

    
    
def has_edits(read):
    """Return True if the read's MD tag indicates any base substitutions or deletions.

    Checks for the presence of any nucleotide letter in the MD tag. Always
    returns True for reads containing deletions, because the MD tag records
    the deleted reference bases as nucleotide characters.

    Args:
        read: pysam.AlignedSegment with an MD tag.

    Returns:
        True if the MD tag contains A, C, G, or T; None otherwise.
    """
    # Are there any replacements? This will always return true if a read has any deletions,
    # as the deletions will also be followed by ACT or G...
    try:
        md_tag = read.get_tag('MD')
    except Exception as e:
        print("It seems like there is an MD tag missing", e)
        
    if ('G' in md_tag or 'A' in md_tag or 'T' in md_tag or 'C' in md_tag):
        # Edits present in this read, based on MD tag contents
        return True

def get_total_coverage_for_contig_at_position(r, coverage_dict):
    """Look up the coverage depth for a single edit record from a pre-built coverage dict.

    Args:
        r: Named tuple or object with position, contig, and barcode attributes.
        coverage_dict: Nested dict mapping contig -> barcode -> position -> coverage depth.

    Returns:
        Integer coverage depth at the edit's position.
    """
    position = r.position
    contig = r.contig
    barcode = r.barcode
    return coverage_dict.get(contig).get(barcode)[position]


def print_read_info(read):
    """Print diagnostic alignment fields for a single read to stdout.

    Outputs MD tag, CIGAR string, orientation flags, read pairing flags,
    and the full pysam string representation. Used for verbose debugging only.

    Args:
        read: pysam.AlignedSegment to inspect.
    """
    md_tag = read.get_tag('MD')
    read_id = read.query_name
    cigar_string = read.cigarstring

    if read.has_tag('CB'):
        barcode = read.get_tag('CB')
        
    print('MD tag', md_tag)
    print("CIGAR tag", cigar_string)
    print("is_reverse", read.is_reverse)
    print("is_read1", read.is_read1)
    print("is_read2", read.is_read2)
    print("is_paired", read.is_paired)
    print("is_proper_pair", read.is_proper_pair)
    print("mate_is_reverse", read.mate_is_reverse)
    print("read id", read.query_name)

    print(str(read))
    
def get_read_information(read, contig, barcode_tag='CB', verbose=False, strandedness=0,
                         min_read_quality=0, min_base_quality=0, dist_from_end=0):
    """Extract edit records from a single aligned read after applying all quality filters.

    Determines strand orientation, validates the read against quality and
    filter criteria, and delegates to get_edit_information_wrapper for the
    per-position edit extraction. Returns a reason code on early exit.

    Args:
        read: pysam.AlignedSegment to process.
        contig: Contig name for position labeling.
        barcode_tag: SAM tag containing the cell barcode. Default 'CB'.
        verbose: Enable verbose per-position logging. Default False.
        strandedness: Strand protocol (0=unstranded, 1=F1R2, 2=F2R1). Default 0.
        min_read_quality: Minimum MAPQ to accept a read. Default 0.
        min_base_quality: Minimum base quality to call an edit. Default 0.
        dist_from_end: Minimum distance from either read end to call an edit. Default 0.

    Returns:
        tuple: (reason_code, list_of_rows, num_edits_of_each_type).
            reason_code is None on success or a string code on early exit.
            list_of_rows is a list of per-edit rows (empty on early exit).
            num_edits_of_each_type is a defaultdict of ref>alt counts.
    """
    if barcode_tag is None:
        read_barcode = 'no_barcode'
    elif read.has_tag(barcode_tag):
        read_barcode = read.get_tag(barcode_tag)
    else:
        read_barcode = None
        
    if not read_barcode:
        return 'no_{}_tag'.format(barcode_tag), [], {}

    # For 10x data, exclude reads that are not counted towards cellranger UMI read counts
    # https://kb.10xgenomics.com/hc/en-us/articles/115003710383-Which-reads-are-considered-for-UMI-counting-by-Cell-Ranger
    if read.has_tag('xf'):
        if not read.get_tag('xf') == 25:
            return 'xf:{}'.format(read.get_tag('xf')), [], {}
    
    is_reverse = read.is_reverse
    reverse_or_forward = '+'

    is_read1 = read.is_read1
    is_read2 = read.is_read2

    if read.has_tag('CB'): # ie == 'CB'
        # Assuming R2 from 10x data contains the seqence 
        is_read1 = False
        is_read2 = True
    
    if is_read1 or is_read2:
        # Paired end or single-cell
        if strandedness == 2:
            if (is_read1 and not is_reverse) or (is_read2 and is_reverse):
                reverse_or_forward = '-'
                
        elif strandedness == 1:
            if (is_read1 and is_reverse) or (is_read2 and not is_reverse):
                reverse_or_forward = '-'
    
    else:
        # Single end
        if is_reverse:
            if strandedness == 2:
                reverse_or_forward = '+'
            else:
                reverse_or_forward = '-'
        else:
            if strandedness == 2:
                reverse_or_forward = '-'
            else:
                reverse_or_forward = '+'
        
        
    reference_start = read.reference_start
    reference_end = read.reference_end
    read_id = read.query_name
    mapq = read.mapping_quality        
    cigarstring = read.cigarstring
    
    
    # ERROR CHECKS, WITH RETURN CODE SPECIFIED        
    if mapq < min_read_quality:
        return 'mapq_low', [], {}
        
    if not has_edits(read):
        return 'no_edits', [], {}

    # Defaults for coverage counting as well 
    # count_coverage function at: https://pysam.readthedocs.io/en/v0.16.0.1/api.html
    
    if read.is_secondary:
        return 'secondary', [], {}

    if read.is_unmapped:
        return 'is_unmapped', [], {}

    if read.is_qcfail:
        return 'is_qcfail', [], {}

    if read.is_duplicate:
        return 'is_duplicate', [], {}
    
    if read.is_supplementary:
        return 'is_supplementary', [], {}
    #if 'N' in cigarstring:
    #    return 'N', [], {}
    
    # PROCESS READ TO EXTRACT EDIT INFORMATION
    if verbose:
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print_read_info(read)
        print('reverse_or_forward:', reverse_or_forward)
        #print("Read ID:", read_id)
        print("----------------------------")
        
    alt_bases, ref_bases, qualities, positions_replaced = get_edit_information_wrapper(read, verbose=verbose)
    if verbose:
        print("Successfully ran get_edit_information_wrapper\nalt bases: {}, ref bases: {}".format(alt_bases, ref_bases))
        
    if len(alt_bases) == 0:
        # These are reads that had deletions, and no edits.
        # They are categorized later because it is hard to tell from the MD tag if they have
        # edits at first when deletions are also indicated.
        return 'no_edits', [], {}
    
    num_edits_of_each_type = defaultdict(lambda:0)
    
    list_of_rows = []
    
    for alt, ref, qual, pos in zip(alt_bases, ref_bases, qualities, positions_replaced):
        if alt == "N" or ref == "N":
            continue

        if verbose:
            print("Getting info:", alt, ref, qual, pos)
            
        assert(alt != ref)
        updated_position = pos+reference_start
        
        distance_from_read_end = np.min([updated_position - reference_start, reference_end - updated_position])

        if distance_from_read_end < dist_from_end:
            continue

        if int(qual) < min_base_quality:
            continue
            
        # If we have been provided with a barcode CB (single-cell), we need to preset our contigs to match
        # the contigs that will be present in the reconfigured bams, ie. 9_GATCCCTCAGTAACGG-1 instead of 9.

        if barcode_tag:
            adjusted_contig = "{}_{}".format(str(contig), read_barcode)
        else:
            adjusted_contig = contig

        contig_position_identity = str(adjusted_contig) + ':' + str(updated_position)
        
        list_of_rows.append([
            read_barcode, str(adjusted_contig), contig_position_identity, str(updated_position), ref, alt, read_id, reverse_or_forward
        ])
    
        num_edits_of_each_type['{}>{}'.format(ref, alt)] += 1
        
                  
    return None, list_of_rows, num_edits_of_each_type



def get_positions_from_md_tag(md_tag, verbose=False):
    """
    Figure out which positions are replaced, from the MD tag.
    """ 
    md_tag_parsed = []
    
    in_deletion = False
    
    for c in md_tag:
        if c == '^':
            in_deletion = True
            continue
        else:
            
            try:
                value = str(int(c))
                
                if in_deletion:
                    in_deletion = False
                    md_tag_parsed.append('-')
                    
                md_tag_parsed.append(value)
                
            except Exception as e:
                if not in_deletion:
                    md_tag_parsed.append('-')
                else:
                    md_tag_parsed.append('+1')

    positions = []

    try:
        position_splitters = [i for i in ''.join(md_tag_parsed).split('-')]
    except Exception as e:
        print("Failed splitting possition on {}, {}".format(md_tag_parsed, e))
        return None
    
    if verbose:
        print(position_splitters)
    
    for s in position_splitters:
        # account for plus signs
        if '+' in s:
            s_sum = np.sum([int(i) for i in s.split('+')])
            s = s_sum - 1
        else:
            s = int(s)
        if len(positions) == 0:
            positions.append(s)
        else:
            positions.append(positions[-1] + s + 1)
            
    if verbose:
        print(positions)
        
    return positions


def incorporate_replaced_pos_info(aligned_seq, positions_replaced, positions_deleted=[], qualities=False):
    """
    Return the aligned sequence string, with specified positions indicated as upper case
    and others as lower case. Also returns the bases at these positions themselves.
    """
    def upper(x):
        """Return x converted to uppercase."""
        return x.upper()

    def lower(x):
        """Return x converted to lowercase."""
        return x.lower()

    def nothing(x):
        """Return x as a string unchanged."""
        return str(x)
    
    if not qualities:
        differences_function = upper
        others_function = lower
    else:
        differences_function = nothing
        others_function = nothing
        
    indicated_aligned_seq = []
    bases_at_pos = []
    for i, a in enumerate(aligned_seq):
        if a == '*':
            indicated_aligned_seq.append(a)
            continue
            
        if i in positions_replaced and i not in positions_deleted:
            indicated_aligned_seq.append(differences_function(a))
            if not qualities:
                bases_at_pos.append(a.upper())
            else:
                bases_at_pos.append(str(a))
        else:
            indicated_aligned_seq.append(others_function(a))
    return ''.join(indicated_aligned_seq), bases_at_pos

def find(s, ch):
    """Return a list of all indices where character ch appears in string s.

    Args:
        s: String to search.
        ch: Single character to find.

    Returns:
        List of integer indices (may be empty).
    """
    return [i for i, ltr in enumerate(s) if ltr == ch]


def remove_softclipped_bases(cigar_tuples, aligned_sequence):
    """Strip soft-clipped bases from both ends of a sequence and its CIGAR tuples.

    Args:
        cigar_tuples: List of (operation, length) CIGAR tuples. Operation 4
            is soft-clip (pysam convention).
        aligned_sequence: Read sequence string (or quality array) to trim.

    Returns:
        tuple: (cropped_sequence, cropped_tuples) with soft-clip entries
            removed from the CIGAR list and the corresponding bases removed
            from the sequence string.
    """
    had_front_clipped = 0
    had_back_clipped = 0
    
    first_tuple = cigar_tuples[0]
    last_tuple = cigar_tuples[-1]
    
    to_clip_from_front = 0
    to_clip_from_back = 0
    
    if first_tuple[0] == 4:
        to_clip_from_front = first_tuple[1]
        had_front_clipped = 1
    if last_tuple[0] == 4:
        to_clip_from_back = last_tuple[1]
        had_back_clipped = 1
        
    cropped_sequence = aligned_sequence[to_clip_from_front:(len(aligned_sequence)-to_clip_from_back)] 
    cropped_tuples = cigar_tuples[had_front_clipped:len(cigar_tuples)-had_back_clipped]
    
    return cropped_sequence, cropped_tuples  


def get_edit_information(md_tag, cigar_tuples, aligned_seq, reference_seq, query_qualities, hamming_check=False, verbose=False):
    """Extract alt bases, ref bases, qualities, and 1-based positions for all edits in a read.

    Clips soft-clipped bases, resolves insertions and deletions using the
    CIGAR string, identifies substituted positions from the MD tag, and
    returns per-edit base and quality information.

    Args:
        md_tag: MD tag string from the BAM record.
        cigar_tuples: List of (operation, length) CIGAR tuples.
        aligned_seq: Read sequence after orientation correction.
        reference_seq: Reference sequence for the aligned region (lowercase).
        query_qualities: Per-base quality array or None.
        hamming_check: When True, assert Hamming distance equals edit count. Default False.
        verbose: Enable step-by-step diagnostic printing. Default False.

    Returns:
        tuple: (alt_bases, ref_bases, qualities, global_positions_replaced_1based)
            where each list has one entry per detected edit.
    """
    if verbose:
            print('CIGAR tuples before clipping (if needed):\n', cigar_tuples)
            print('Aligned sequence before clipping (if needed):\n', aligned_seq)
            print("Qualities before clipping:\n", query_qualities)

    original_cigar_tuples = copy(cigar_tuples)
    aligned_seq, cigar_tuples = remove_softclipped_bases(original_cigar_tuples, aligned_seq)
    

    if query_qualities:
        if verbose:
            print("Soft clipping quality scores ...")
        query_qualities, cigar_tuples = remove_softclipped_bases(original_cigar_tuples, query_qualities)
    else:
        if verbose:
            print("No quality scores...")
        query_qualities, cigar_tuples = query_qualities, original_cigar_tuples
        
    if verbose:
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('CIGAR tuples after clipping (if needed):\n', cigar_tuples)
        print('Aligned sequence after clipping (if needed):\n', aligned_seq)
        print("Qualities after clipping:\n", query_qualities)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


    positions_replaced = get_positions_from_md_tag(md_tag, verbose=verbose)
    # Incorporate insertions, deletions, and splice junctions (N)
    fixed_aligned_seq_for_deletion_locations = incorporate_insertions_and_deletions(aligned_seq, cigar_tuples, junctions=False)
    fixed_aligned_seq = incorporate_insertions_and_deletions(aligned_seq, cigar_tuples)

    # Account for deletions
    if '*' in fixed_aligned_seq_for_deletion_locations:
        # These are coordinates after already fixing the read with deletions, insertions and junctions
        positions_deleted = find(fixed_aligned_seq_for_deletion_locations, '*')
    else:
        positions_deleted = []

    indicated_reference_seq, ref_bases = incorporate_replaced_pos_info(reference_seq, positions_replaced, positions_deleted=positions_deleted)
    fixed_reference_seq = incorporate_insertions_and_deletions(indicated_reference_seq, cigar_tuples, insertions=False, deletions=False)
    indicated_qualities, qualities = incorporate_replaced_pos_info(query_qualities, positions_replaced, qualities=True)


    # Get global coordinates of positions replaced
    global_positions_replaced = []
    finalized_fixed_aligned_seq = ''
    alt_bases = []
    for i, character in enumerate(fixed_reference_seq):
        if character.isupper():
            global_positions_replaced.append(i)
            upper_char = fixed_aligned_seq[i].upper()
            finalized_fixed_aligned_seq += upper_char
            if upper_char != '*':
                alt_bases.append(upper_char)
        else:
            lower_char = fixed_aligned_seq[i].lower()
            finalized_fixed_aligned_seq += lower_char

    if verbose:
        if 'n' in fixed_aligned_seq:
            num_n = fixed_aligned_seq.count("n")
            n_to_replace = ''.join([i for i in fixed_aligned_seq if i == "n"])
        else:
            num_n = 1
            n_to_replace = 'n'
            
        print("Indicated reference seq:\n", indicated_reference_seq.replace(n_to_replace, "{}*n".format(num_n)))
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print("Fixed reference seq:\n", fixed_reference_seq.replace(n_to_replace, "{}*n".format(num_n)))
            
        print("Fixed aligned seq:\n", fixed_aligned_seq.replace(n_to_replace, "{}*n".format(num_n)))
        print("Finalized fixed aligned seq:\n", finalized_fixed_aligned_seq.replace(n_to_replace, "{}*n".format(num_n)))

        print("Indicated qualities:\n", indicated_qualities.replace(n_to_replace, "{}*n".format(num_n)))
        
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('alt bases', alt_bases)
        print('ref bases', ref_bases)


    if hamming_check:
        num_deletions = finalized_fixed_aligned_seq.count('*')
        hamming_distance = get_hamming_distance(finalized_fixed_aligned_seq, fixed_reference_seq) - num_deletions
        print("Hamming distance: {}".format(hamming_distance))
        assert(hamming_distance == len(alt_bases))

    # Make positions 1-based instead of 0-based
    global_positions_replaced_1based = [g+1 for g in global_positions_replaced]
    
    return alt_bases, ref_bases, qualities, global_positions_replaced_1based
    
    
def get_edit_information_wrapper(read, hamming_check=False, verbose=False):
    """Extract edit information from a pysam AlignedSegment.

    Retrieves the MD tag, CIGAR tuples, forward sequence, quality scores,
    and reference sequence from the read object and delegates to
    get_edit_information for the actual edit extraction.

    Args:
        read: pysam.AlignedSegment to process.
        hamming_check: When True, assert Hamming distance equals edit count. Default False.
        verbose: Enable diagnostic logging. Default False.

    Returns:
        tuple: (alt_bases, ref_bases, qualities, global_positions_replaced_1based).
    """
    md_tag = read.get_tag('MD')
    cigarstring = read.cigarstring
       
    cigar_tuples = read.cigartuples
    aligned_seq = read.get_forward_sequence()
    query_qualities = read.query_qualities
    if not query_qualities:
        query_qualities = [40 for i in range(len(aligned_seq))]
        
    if read.is_reverse:
        aligned_seq = reverse_complement(aligned_seq)
    
    reference_seq = read.get_reference_sequence().lower()
    
    if verbose:
        print("MD tag:\n\t", md_tag)
        print("CIGAR string\n\t", cigarstring)
        print("Reference seq:\n\t", reference_seq.upper())
        print("Aligned seq:\n\t", aligned_seq)
        print("Qualities:\n\t", query_qualities)
    
    return(get_edit_information(md_tag,
                                cigar_tuples, 
                                aligned_seq, 
                                reference_seq,
                                query_qualities,
                                hamming_check=hamming_check,
                                verbose=verbose
                               ))