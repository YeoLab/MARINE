import math
from glob import glob
import multiprocessing
import os
import pysam
import polars as pl
import pandas as pd
import numpy as np
import sys
from collections import OrderedDict, defaultdict

suffixes = {
    'CB': [
        "A-1", "C-1", "G-1", "T-1"
    ],
    'IS': [
        "00","01","02","03","04","05","06","07","08","09",
        "10","11","12","13","14","15","16","17","18","19",
        "20","21","22","23","24","25","26","27","28","29",
        "30","31","32","33","34","35","36","37","38","39",
        "40","41","42","43","44","45","46","47","48","49",
        "50","51","52","53","54","55","56","57","58","59",
        "60","61","62","63","64","65","66","67","68","69",
        "70","71","72","73","74","75","76","77","78","79",
        "80","81","82","83","84","85","86","87","88","89",
        "90","91","92","93","94","95","96","97","98","99",
        ],
    'IB': [
        "00-A","01-A","02-A","03-A","04-A","05-A","06-A","07-A","08-A","09-A",
        "10-A","11-A","12-A","13-A","14-A","15-A","16-A","17-A","18-A","19-A",
        "20-A","21-A","22-A","23-A","24-A","25-A","26-A","27-A","28-A","29-A",
        "30-A","31-A","32-A","33-A","34-A","35-A","36-A","37-A","38-A","39-A",
        "40-A","41-A","42-A","43-A","44-A","45-A","46-A","47-A","48-A","49-A",
        "50-A","51-A","52-A","53-A","54-A","55-A","56-A","57-A","58-A","59-A",
        "60-A","61-A","62-A","63-A","64-A","65-A","66-A","67-A","68-A","69-A",
        "70-A","71-A","72-A","73-A","74-A","75-A","76-A","77-A","78-A","79-A",
        "80-A","81-A","82-A","83-A","84-A","85-A","86-A","87-A","88-A","89-A",
        "90-A","91-A","92-A","93-A","94-A","95-A","96-A","97-A","98-A","99-A",
        "00-C","01-C","02-C","03-C","04-C","05-C","06-C","07-C","08-C","09-C",
        "10-C","11-C","12-C","13-C","14-C","15-C","16-C","17-C","18-C","19-C",
        "20-C","21-C","22-C","23-C","24-C","25-C","26-C","27-C","28-C","29-C",
        "30-C","31-C","32-C","33-C","34-C","35-C","36-C","37-C","38-C","39-C",
        "40-C","41-C","42-C","43-C","44-C","45-C","46-C","47-C","48-C","49-C",
        "50-C","51-C","52-C","53-C","54-C","55-C","56-C","57-C","58-C","59-C",
        "60-C","61-C","62-C","63-C","64-C","65-C","66-C","67-C","68-C","69-C",
        "70-C","71-C","72-C","73-C","74-C","75-C","76-C","77-C","78-C","79-C",
        "80-C","81-C","82-C","83-C","84-C","85-C","86-C","87-C","88-C","89-C",
        "90-C","91-C","92-C","93-C","94-C","95-C","96-C","97-C","98-C","99-C",
        "00-G","01-G","02-G","03-G","04-G","05-G","06-G","07-G","08-G","09-G",
        "10-G","11-G","12-G","13-G","14-G","15-G","16-G","17-G","18-G","19-G",
        "20-G","21-G","22-G","23-G","24-G","25-G","26-G","27-G","28-G","29-G",
        "30-G","31-G","32-G","33-G","34-G","35-G","36-G","37-G","38-G","39-G",
        "40-G","41-G","42-G","43-G","44-G","45-G","46-G","47-G","48-G","49-G",
        "50-G","51-G","52-G","53-G","54-G","55-G","56-G","57-G","58-G","59-G",
        "60-G","61-G","62-G","63-G","64-G","65-G","66-G","67-G","68-G","69-G",
        "70-G","71-G","72-G","73-G","74-G","75-G","76-G","77-G","78-G","79-G",
        "80-G","81-G","82-G","83-G","84-G","85-G","86-G","87-G","88-G","89-G",
        "90-G","91-G","92-G","93-G","94-G","95-G","96-G","97-G","98-G","99-G",
        "00-T","01-T","02-T","03-T","04-T","05-T","06-T","07-T","08-T","09-T",
        "10-T","11-T","12-T","13-T","14-T","15-T","16-T","17-T","18-T","19-T",
        "20-T","21-T","22-T","23-T","24-T","25-T","26-T","27-T","28-T","29-T",
        "30-T","31-T","32-T","33-T","34-T","35-T","36-T","37-T","38-T","39-T",
        "40-T","41-T","42-T","43-T","44-T","45-T","46-T","47-T","48-T","49-T",
        "50-T","51-T","52-T","53-T","54-T","55-T","56-T","57-T","58-T","59-T",
        "60-T","61-T","62-T","63-T","64-T","65-T","66-T","67-T","68-T","69-T",
        "70-T","71-T","72-T","73-T","74-T","75-T","76-T","77-T","78-T","79-T",
        "80-T","81-T","82-T","83-T","84-T","85-T","86-T","87-T","88-T","89-T",
        "90-T","91-T","92-T","93-T","94-T","95-T","96-T","97-T","98-T","99-T"
    ]
}

def get_contigs_that_need_bams_written(expected_contigs, split_bams_folder, barcode_tag='CB', number_of_expected_bams=4):
    bam_indices_written = [f.split('/')[-1].split('.bam')[0] for f in glob('{}/*/*.sorted.bam.bai'.format(split_bams_folder))]

    subsets_per_contig = defaultdict(lambda:0)
    for bam_index_written in bam_indices_written:
        contig_label = bam_index_written.split('_')[0]
        subsets_per_contig[contig_label] += 1

    if barcode_tag == 'CB':
        number_of_expected_bams = 4
    else:
        number_of_expected_bams = number_of_expected_bams
        
    contigs_to_write_bams_for = []
    for c in expected_contigs:
        num_written_indices = subsets_per_contig.get(c, 0)
        if num_written_indices < number_of_expected_bams:
            #print("Contig {} has {}/{} bams generated".format(c, num_written_indices, number_of_expected_bams))
            contigs_to_write_bams_for.append(c)
    
    return contigs_to_write_bams_for


def make_edit_finding_jobs(bampath, output_folder, strandedness, barcode_tag="CB", barcode_whitelist=None, contigs=[], num_intervals_per_contig=16, verbose=False, min_read_quality = 0):
    jobs = []
    
    contig_lengths_dict = get_contig_lengths_dict(bampath)

    # Skip incorrectly specified contigs
    new_contigs = []
    for contig in contigs:
        if contig not in contig_lengths_dict:
            sys.stderr.write("User-specified contig {} not found in bam header... exiting.\n".format(contig))
        else:
            new_contigs.append(contig)
            
    if verbose:
        print('contig_lengths_dict:{}'.format(contig_lengths_dict))
    if len(contigs) == 0:
        contigs_to_use = set(contig_lengths_dict.keys())
    else:
        contigs_to_use = set(new_contigs)
        
    for contig in contig_lengths_dict.keys():
            
        if contig not in contigs_to_use:
            continue

        pretty_print("\tContig {}".format(contig))
        
        contig_length = contig_lengths_dict.get(contig)
        intervals_for_contig = get_intervals(contig, contig_lengths_dict, num_intervals_per_contig)
        #print('\t\tintervals_for_contig: {}'.format(intervals_for_contig))
        # Set up for pool
        for split_index, interval in enumerate(intervals_for_contig):
            split_index = str(split_index).zfill(3)
            parameters = [bampath, contig, split_index, interval[0], interval[1], output_folder, strandedness, barcode_tag, barcode_whitelist, verbose, min_read_quality]
            jobs.append(parameters)
    return jobs


def get_contig_lengths_dict(bam_path):
    """
    Given a bam file handle, read the header to return a dictionary
    mapping contig names to lengths.
    """
    header_lines = pysam.AlignmentFile(bam_path, "rb").text.split("\t")
    
    contig_lengths = {}
    found_sn = False
    found_ln = False
    for line in header_lines:
        # Clean up line
        line = line.split("\n")[0]
        
        # Extract contig names and lengths
        if line.startswith("SN"):
            found_sn = True
            contig_name = line.split("SN:")[1]
        if found_sn == True:
            if line.startswith("LN"):
                length = int(line.split("LN:")[1])
                contig_lengths[contig_name] = length
                found_sn = False
                
    return contig_lengths

def read_barcode_whitelist_file(barcode_whitelist_file, manager):
    barcode_whitelist = pd.read_csv(barcode_whitelist_file, names=['barcodes']).barcodes.tolist()

    shared_list = manager.list(barcode_whitelist)
    
    pretty_print("Barcodes in whitelist: {}".format(len(shared_list)))
    return shared_list


def pretty_print(contents, style=''):
    if type(contents) == list:
        for item in contents:
            pretty_print(item)
        sys.stdout.write("\n")
        
    else:
        to_write = '{}\n'.format(contents)
        
        before_line = None
        after_line = None
        
        styled_line = ''.join([style for i in range(len(to_write))])
        
        if style != '':
            # Line before
            pretty_print(styled_line)
            
        sys.stdout.write(to_write)
        
        if style:
            # Line after 
            pretty_print(styled_line)
    
def get_intervals(contig, contig_lengths_dict, num_intervals=4):
    """
    Splits contig coordinates into a list of {num_intervals} coordinates of equal size.
    """
    contig_length = contig_lengths_dict.get(contig)
    interval_length = math.ceil(contig_length/num_intervals)
    start = 0
    end = interval_length

    intervals = []
    while start < contig_length:
        if end > contig_length:
            end == contig_length

        interval = [start, end]
        intervals.append(interval)

        start = end
        end = start + interval_length
    return intervals


def index_bam(barcode_bam_file_path):
    index_path = '{}.bai'.format(barcode_bam_file_path)
    if not os.path.exists(index_path):
        pysam.index(barcode_bam_file_path)
    elif os.path.getmtime(index_path) < os.path.getmtime(barcode_bam_file_path):
        print("index is older than bam for {}... reindexing".format(barcode_bam_file_path))
        pysam.index(barcode_bam_file_path)
            
            
def write_rows_to_info_file(list_of_rows, f):
    for info_list in list_of_rows:
        info_line = '\t'.join(info_list) + '\n'
        f.write(info_line)
        
def write_header_to_edit_info(f):
    f.write('barcode\tcontig\tposition\tref\talt\tread_id\tstrand\tdist_from_end\tbase_quality\tmapping_quality\n')
    
def write_read_to_bam_file(read, bam_handles_for_barcodes, barcode_bam_file_path, samfile_template):
    bam_for_barcode = bam_handles_for_barcodes.get(barcode_bam_file_path)

    if not bam_for_barcode:
        bam_for_barcode = pysam.AlignmentFile(barcode_bam_file_path, "wb", template=samfile_template)
        bam_handles_for_barcodes[barcode_bam_file_path] = bam_for_barcode

    bam_for_barcode.write(read)
    
def remove_file_if_exists(file_path):
    if os.path.exists(file_path):
        #print("{} exists... deleting".format(file_path))
        os.remove(file_path)
        
def make_folder(folder_path):
    if not os.path.exists(folder_path):
        try:
            os.mkdir(folder_path)
        except Exception as e:
            pass
            #sys.stderr.write('{}_{}\n'.format(folder_path, e))

def only_keep_positions_for_region(contig, output_folder, positions_for_barcode, verbose=False):
    contig_index = str(contig.split("_")[-1]).zfill(3)
    contig_base = contig.split("_")[0]
    
    #print("Contig: {}, contig_base: {}, contig_index: {}".format(contig, contig_base, contig_index))

    edit_info_filepath_regex = "{}/edit_info/{}_{}*".format(output_folder, contig_base, contig_index)
    #print("edit_info_filepath_regex: {}".format(edit_info_filepath_regex))

    edit_info_filepath = 'Not yet set'
    try:
        edit_info_filepath = glob(edit_info_filepath_regex)[0].split('/')[-1]
        #sys.stderr.write("Contig: {}, edit_info_filepath: {}\n".format(contig, edit_info_filepath))
        
        second_half_of_filepath = edit_info_filepath.split('_{}_'.format(contig_index))[-1]
        #print("Contig: {}, second_half_of_filepath: {}".format(contig,second_half_of_filepath))
        min_pos, max_pos = second_half_of_filepath.split('_edit_info')[0].split('_')
    
        min_pos = int(min_pos)
        max_pos = int(max_pos)
        #print("Contig: {}. Min pos: {}. Max pos: {}.".format(contig, min_pos, max_pos))

        return [p for p in positions_for_barcode if p > min_pos and p < max_pos]

    except Exception as e:
        sys.stderr.write('{}, {}, {}, {}, {}, regex: {}\n'.format(e, contig, contig_base, contig_index, edit_info_filepath, edit_info_filepath_regex))
        return []
        
def check_read(read):
    return True

def get_bulk_coverage_at_pos(samfile_for_barcode, contig_bam, just_contig, pos, paired_end=False, verbose=False):
    if not paired_end:
        if verbose:
            print("~~~~~~\n!!!!SINGLE END!!!!!\n~~~~~~~`")
        # count_coverage does not work with paired end reads, because it counts both ends of the read twice...
        # For more information: https://github.com/pysam-developers/pysam/issues/744 
        coverage_at_pos = np.sum(samfile_for_barcode.count_coverage(just_contig, 
                                                                    pos-1, 
                                                                    pos, 
                                                                    quality_threshold=0, # base quality
                                                                    read_callback='all'
                                                                   ))
        return coverage_at_pos
    else:
        if verbose:
            print("~~~~~~\n!!!!PAIRED END!!!!!\npos: {}\n {}:{}~~~~~~~`".format(contig_bam, just_contig, pos))
        
        # For paired-end sequencing, it is more accurate to use the pileup function
        pileupcolumn_iter = samfile_for_barcode.pileup(just_contig, 
                                                       pos-1, 
                                                       pos, 
                                                       stepper='nofilter',
                                                       #stepper='all', 
                                                       truncate=True, 
                                                       min_base_quality=0, # base quality
                                                       max_depth=1000000)
        
        unique_read_ids = set()
        for pileupcolumn in pileupcolumn_iter:
            for pileupread in pileupcolumn.pileups:
                #if verbose:
                #    print("at pos {}:{}:".format(just_contig, pos), pileupread)
                if not pileupread.is_del and not pileupread.is_refskip:                                        
                    unique_read_ids.add(pileupread.alignment.query_name)
                    
        coverage_at_pos = len(unique_read_ids)

        if verbose:
            print('coverage_at_pos', coverage_at_pos)
            
        return coverage_at_pos


def get_coverage_df(edit_info, contig, output_folder, barcode_tag='CB', paired_end=False, 
                    verbose=False):

    if barcode_tag:
        # Single-cell, contig will include barcode ending-based suffix 
        bam_subfolder = "{}/split_bams/{}".format(output_folder, contig)
        contig_bam = '{}/{}.bam.sorted.bam'.format(bam_subfolder, contig)
    else:
        # Bulk -- no barcode ending-based suffixes, just splits
        just_contig = contig.split('_')[0]
        bam_subfolder = "{}/split_bams/{}".format(output_folder, just_contig)
        contig_bam = '{}/{}.bam.sorted.bam'.format(bam_subfolder, contig)

    #print("Contig {}. Loading {} bamfile...".format(contig, contig_bam))
    try:
        index_bam(contig_bam)
        samfile_for_barcode = pysam.AlignmentFile(contig_bam, "rb")
    except OSError:  # If MARINE cannot find a bam to index, return empty
        return pd.DataFrame(columns=['coverage', 'source'])
        
    #print("Contig {}. Loaded bamfile...".format(contig))
    unique_barcodes = sorted(list(edit_info.unique("barcode")["barcode"]))
    coverage_dict = defaultdict(lambda:{})
    
    # print("Contig {}. Iterating through barcodes...".format(contig))
    for i, barcode in enumerate(unique_barcodes):
        if i % 300 == 0:
            #print("{}/{} barcodes for {}...".format(i+1, len(unique_barcodes), contig))
            pass
            
        edit_info_for_barcode = edit_info.filter(pl.col("barcode") == barcode)
        positions_for_barcode = set(edit_info_for_barcode["position"].unique())
                    
        num_positions = len(positions_for_barcode)
        for i, pos in enumerate(positions_for_barcode):
            
            if barcode_tag:
                # For single-cell
                
                barcode_specific_contig = '{}_{}'.format(contig, barcode)
                # Alter from 3_C_AAACCCAAGAACTTCC-1, for example, to 3_AAACCCAAGAACTTCC-1'
                barcode_specific_contig_split = barcode_specific_contig.split("_")
                barcode_specific_contig_without_subdivision = "{}_{}".format(barcode_specific_contig_split[0], barcode_specific_contig_split[2])

                if verbose:
                    #print("contig_bam:", contig_bam)
                    #print("barcode_specific_contig:", barcode_specific_contig)
                    print("barcode_specific_contig_without_subdivision:", barcode_specific_contig_without_subdivision)
                    
                coverage_at_pos = np.sum(samfile_for_barcode.count_coverage(barcode_specific_contig_without_subdivision, 
                                                                            pos-1, 
                                                                            pos,  
                                                                            quality_threshold=0, # base quality
                                                                            read_callback='all'
                                                                           ))

                coverage_dict['{}:{}'.format(barcode, pos)]['coverage'] = coverage_at_pos
                coverage_dict['{}:{}'.format(barcode, pos)]['source'] = contig
                
            else:
                
                # For bulk, no barcodes, we will just have for example 19_no_barcode to convert to 19 to get coverage at that chrom
                just_contig = contig.split('_')[0]
                try:
                    coverage_at_pos = get_bulk_coverage_at_pos(samfile_for_barcode, contig_bam, just_contig, pos, 
                                                               paired_end=paired_end, verbose=verbose)
                                
                    coverage_dict['{}:{}'.format('no_barcode', pos)]['coverage'] = coverage_at_pos
                    coverage_dict['{}:{}'.format('no_barcode', pos)]['source'] = contig

                except Exception as e:
                    print("contig {}".format(contig), "Failed to get coverage", e)
                    return pd.DataFrame(columns=['coverage', 'source'])  # Should we just return empty? Or why would there be an exception here?
                
    coverage_df = pd.DataFrame.from_dict(coverage_dict, orient='index')
    
    return coverage_df


def filter_output_df(output_df, filters, output_filename):
    filter_stats = {}
    filter_stats['original'] = len(output_df)
    if output_df.empty:
        filter_stats['filtered'] = len(output_df)
        output_df['coverage'] = []
        output_df.to_csv(output_filename, sep='\t', header=False)
        return filter_stats
    
    filtered_output_df = output_df[
            (output_df.dist_from_end >= filters.get('dist_from_end')) & 
            (output_df.base_quality >= filters.get('base_quality'))]

    coverage_per_unique_position_df = pd.DataFrame(filtered_output_df.groupby(
        [
            "position_barcode"
        ]).coverage.max())

    distinguishing_columns = [
        "barcode",
        "contig",
        "position",
        "ref",
        "alt",
        "read_id",
        "strand",
        "dist_from_end",
        "base_quality",
        "mapping_quality"
    ]

    
    all_edit_info_unique_position_df = filtered_output_df.drop_duplicates(distinguishing_columns)[distinguishing_columns]

    all_edit_info_unique_position_df.index = all_edit_info_unique_position_df['position'].astype(str)\
+ '_' + all_edit_info_unique_position_df['barcode']

    all_edit_info_unique_position_with_coverage_df = all_edit_info_unique_position_df.join(coverage_per_unique_position_df)

    if filters.get('max_edits_per_read'):
        #pretty_print("\t\tFiltering out reads with more than {} edits...".format(max_edits_per_read))
        read_edits = all_edit_info_unique_position_with_coverage_df.groupby('read_id').count().sort_values('barcode')
        all_edit_info_unique_position_with_coverage_df = all_edit_info_unique_position_with_coverage_df[all_edit_info_unique_position_with_coverage_df.read_id.isin(read_edits[read_edits['barcode'] <= max_edits_per_read].index)]


    distinguishing_columns = [
            "barcode",
            "contig",
            "position",
            "ref",
            "alt",
            "read_id",
            "strand",
            "mapping_quality",
            "coverage"
        ]

    all_edit_info_unique_position_with_coverage_df = all_edit_info_unique_position_with_coverage_df.drop_duplicates(
            distinguishing_columns)[distinguishing_columns]
    
    filter_stats['filtered'] = len(all_edit_info_unique_position_with_coverage_df)

    
    all_edit_info_unique_position_with_coverage_df.to_csv(output_filename, sep='\t', header=False)

    return filter_stats

    
def get_coverage_wrapper(parameters):
    edit_info, contig, output_folder, barcode_tag, paired_end, filters, verbose = parameters

    output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)
    filtered_output_filename = '{}/coverage/{}_filtered.tsv'.format(output_folder, contig, header=False)
    
    if os.path.exists(output_filename):
        # filter
        edit_info_and_coverage_joined = pd.read_csv(output_filename, sep='\t', names=[
            'barcode', 'contig', 'position', 'ref', 'alt', 'read_id', 'strand',
            'dist_from_end', 'base_quality', 'mapping_quality', 'barcode_position',
            'coverage', 'source', 'position_barcode'], dtype={'base_quality': int, 'dist_from_end': int, 'contig': str})
    else:
        edit_info = edit_info.with_columns(
        pl.concat_str(
            [
                pl.col("barcode"),
                pl.col("position")
            ],
            separator=":",
        ).alias("barcode_position"))
    
        edit_info_df = edit_info.to_pandas()
        edit_info_df.index = edit_info_df['barcode_position']
        
        coverage_df = get_coverage_df(edit_info, contig, output_folder, barcode_tag=barcode_tag, 
                                      paired_end=paired_end, verbose=verbose)
    
        # Combine edit i)nformation with coverage information
        edit_info_and_coverage_joined = edit_info_df.join(coverage_df, how='inner')
        edit_info_and_coverage_joined['position_barcode'] = edit_info_and_coverage_joined['position'].astype(str) + '_' + edit_info_and_coverage_joined['barcode'].astype(str)
        edit_info_and_coverage_joined.to_csv(output_filename, sep='\t', header=False)

    filter_stats = filter_output_df(edit_info_and_coverage_joined, filters, filtered_output_filename)
    assert(os.path.exists(output_filename))
    assert(os.path.exists(filtered_output_filename))
    return filtered_output_filename, filter_stats
    


def sort_bam(bam_file_name):
    output_name = bam_file_name + ".sorted.bam"
    pysam.sort("-o", output_name, bam_file_name)  
    return output_name


def rm_bam(bam_file_name):
    os.remove(bam_file_name)

def write_reads_to_file(reads, bam_file_name, header_string, barcode_tag="BC"):
    header = pysam.AlignmentHeader.from_text(header_string)
    
    header_dict = header.as_dict()
    lengths_for_sn = {}
    
    header_dict_sq = header_dict.get("SQ")
    for s in header_dict_sq:
        sn = s.get("SN")
        ln = s.get("LN")
        lengths_for_sn[sn] = ln
        
    #print("\tCurrent header length for {}: {}".format(bam_file_name, len(lengths_for_sn)))
    
    all_barcodes_for_contig = set([r.split('\t')[2] for r in reads])
    #print("\tNum barcodes for {}: {}".format(bam_file_name, len(all_barcodes_for_contig)))
        
    for new_sn in all_barcodes_for_contig:
        original_chrom = new_sn.split("_")[0]
        if not barcode_tag:
            new_sn = new_sn.split("_")[0]
            
        if new_sn not in lengths_for_sn:
            new_ln = lengths_for_sn.get(original_chrom)
            new_entry = {"SN": new_sn, "LN": new_ln}
            header_dict_sq.append(new_entry)
    
    #print("\tExample new entries: {}".format(header_dict_sq[-4:]))
    header_dict['SQ'] = header_dict_sq
    
    #print("\tNew header length: {}".format(len(header_dict.get("SQ"))))
    
    new_header = pysam.AlignmentHeader.from_dict(header_dict)
    
    num_reads = len(reads)
    
    with pysam.AlignmentFile(bam_file_name, "wb", text=str(new_header)) as bam_handle:
        for i, read_str in enumerate(reads):
            if i > 0 and i % 100000 == 0:
                sys.stdout.write('file {}: {}/{} reads\n'.format(bam_file_name.split('/')[-1], i, num_reads))
                
            try:
                read = pysam.AlignedSegment.fromstring(read_str, new_header)
                bam_handle.write(read) 
            except Exception as e:
                sys.stdout.err('{}\n\nfile {}: Failed to write read with str representation of:\n\t {}\n'.format(e,
                                                                                                      bam_file_name.split('/')[-1],
                                                                                                read_str))
                sys.exit(1)
                
            
            
    bam_handle.close()
        
           
def concat_and_write_bams(contig, df_dict, header_string, split_bams_folder, barcode_tag='CB', number_of_expected_bams=4, verbose=False):
    job_params = []
    
    # Sort the subcontig regions such that the reads are properly ordered 
    sorted_subcontig_names = sorted(df_dict.keys())
    sorted_subcontig_dfs = []
    for n in sorted_subcontig_names:
        subcontig = df_dict.get(n)
        if len(subcontig) > 0:
            sorted_subcontig_dfs.append(subcontig)
        
    if len(sorted_subcontig_dfs) == 0:
        if verbose:
            print("{} was empty".format(contig))
        return []

    if verbose:
        print("\t{}: num subcontigs to concat: {}".format(contig, len(sorted_subcontig_dfs)))
        # All of the reads for all of the barcodes are in this dataframe
        print("\t{}: concatting".format(contig))
        
    all_contents_df = pl.concat(sorted_subcontig_dfs)
                
    # Combine the reads (in string representation) for all rows corresponding to a barcode  
    assert(barcode_tag in ['CB', 'IS', 'IB'])
    
    suffix_options = suffixes.get(barcode_tag)
    #print("\t{} suffixes".format(len(suffix_options)))
    
    for suffix in suffix_options:
        if barcode_tag:
            all_contents_for_suffix = all_contents_df.filter(pl.col('barcode').str.ends_with(suffix))
        else:
            all_contents_for_suffix = all_contents_df.filter(pl.col('bucket') == suffix)
            

        if verbose:
            if len(all_contents_for_suffix) > 0:
                print("\tcontig: {} suffix: {}, all_contents_df length: {}, all_contents_for_suffix length: {}".format(
                        contig,
                        suffix,
                        len(all_contents_df),
                        len(all_contents_for_suffix)
                        ))
        
        try:
            reads_deduped = list(OrderedDict.fromkeys(all_contents_for_suffix.transpose().with_columns(
                pl.concat_str(
                    [pl.col(c) for c in all_contents_for_suffix.transpose().columns],
                    separator="\n"
                     ).alias("combined_text")
            )[['combined_text']][1].item().split('\n')))
        except Exception as e:
            reads_count_for_suffix = len(all_contents_for_suffix)
            
            if reads_count_for_suffix == 0:
                #print("\tWARNING: No reads found in region {}:{}... assuming this is not an issue, but perhaps worth confirming manually using samtools.".format(contig, suffix))
                reads_deduped = []
            else:
                print("\t\t### ERROR EMPTY?: {}, contig: {} suffix: {}, all_contents_df length: {}, all_contents_for_suffix length: {}".format(
                    e,
                    contig,
                    suffix,
                    len(all_contents_df),
                    reads_count_for_suffix
                    ))
                sys.exit(1)
            
        
        # Make a sub-subfolder to put the bams for this specific contig
        contig_folder = '{}/{}_{}/'.format(split_bams_folder, contig, suffix)
        if not os.path.exists(contig_folder):
            os.mkdir(contig_folder)
            
            
        bam_file_name = '{}/{}_{}.bam'.format(contig_folder, contig, suffix)
        
        # Write, sort and index bam immediately
        write_reads_to_file(reads_deduped, bam_file_name, header_string) 
        try:
            # print("\tSorting {}...".format(bam_file_name))
            sorted_bam_file_name = sort_bam(bam_file_name)
            # print("\tIndexing {}...".format(sorted_bam_file_name))
            index_bam(sorted_bam_file_name)
            rm_bam(bam_file_name)
        except Exception as e:
            print("Failed at indexing {}".format(bam_file_name))
            
    
def concat_and_write_bams_wrapper(params):
    contig, df_dict, header_string, split_bams_folder, barcode_tag, number_of_expected_bams, verbose = params
    
    # print("df_dict keys: {}".format(df_dict.keys()))
    concat_and_write_bams(contig, df_dict, header_string, split_bams_folder, barcode_tag=barcode_tag, number_of_expected_bams=number_of_expected_bams, verbose=verbose)
