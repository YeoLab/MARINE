import math
from glob import glob
import os
import pysam
import polars as pl
import pandas as pd
import numpy as np
import sys
import subprocess
import tracemalloc
from collections import OrderedDict, defaultdict
from itertools import product
from scipy.special import betainc
import shutil
from multiprocessing import Pool
import multiprocessing
import time

CB_N = 1

def generate_permutations_list_for_CB(n):
    """
    Generate all permutations of A, C, G, T for strings of length n
    and format the output as a list with "-1" appended to each permutation.

    Output for 2, for example: ['AA-1', 'AC-1', 'AG-1', 'AT-1', 'CA-1', 'CC-1', 'CG-1', 'CT-1', 'GA-1', 'GC-1'...]
    Args:
        n (int): Length of the strings to generate.
        
    Returns:
        list: A list of strings where each string is a permutation with "-1" appended.
    """
    # Generate all combinations of A, C, G, T of length n
    combinations = [''.join(p) for p in product('ACGT', repeat=n)]
    
    # Append "-1" to each permutation
    result = [f"{combo}-1" for combo in combinations]
    
    return result

suffixes = {
    'CB': generate_permutations_list_for_CB(CB_N),
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
        number_of_expected_bams = 4**CB_N
    else:
        number_of_expected_bams = number_of_expected_bams
        
    contigs_to_write_bams_for = []
    for c in expected_contigs:
        num_written_indices = subsets_per_contig.get(c, 0)
        if num_written_indices < number_of_expected_bams:
            print("Contig {} has {}/{} bams generated".format(c, num_written_indices, number_of_expected_bams))
            contigs_to_write_bams_for.append(c)
    
    return contigs_to_write_bams_for


def make_edit_finding_jobs(bampath, output_folder, strandedness, barcode_tag="CB", barcode_whitelist=None, contigs=[], verbose=False, min_read_quality=0, min_base_quality=0, dist_from_end=0, interval_length=2000000):
    
    jobs = []
    
    samfile = pysam.AlignmentFile(bampath, "rb")
    contig_lengths_dict = get_contig_lengths_dict(samfile)

    #if verbose:
    #    print('contig_lengths_dict:{}'.format(contig_lengths_dict))
    
    if len(contigs) == 0:
        contigs_to_use = set(contig_lengths_dict.keys())
    else:
        contigs_to_use = set(contigs)
    
    for contig in contig_lengths_dict.keys():
            
        if contig not in contigs_to_use:
            continue

        pretty_print("\tContig {}".format(contig))
        
        contig_length = contig_lengths_dict.get(contig)
        intervals_for_contig = get_intervals(contig, contig_lengths_dict, interval_length)
        #print('\t\tintervals_for_contig: {}'.format(intervals_for_contig))
        # Set up for pool
        for split_index, interval in enumerate(intervals_for_contig):
            split_index = str(split_index).zfill(3)
            parameters = [bampath, contig, split_index, interval[0], interval[1], output_folder, strandedness, barcode_tag, barcode_whitelist, verbose, min_read_quality, min_base_quality, dist_from_end]
            jobs.append(parameters)
    return jobs


def get_contig_lengths_dict(bam_handle):
    """
    Given a bam file handle, read the header to return a dictionary
    mapping contig names to lengths.
    """
    header_lines = bam_handle.text.split("\t")
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

def read_barcode_whitelist_file(barcode_whitelist_file):
    barcode_whitelist = set(pd.read_csv(barcode_whitelist_file, names=['barcodes']).barcodes.tolist())
    
    pretty_print("Barcodes in whitelist: {}".format(len(barcode_whitelist)))
    return barcode_whitelist


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
    
def get_intervals(contig, contig_lengths_dict, interval_length=2000000):
    """
    Splits contig coordinates into a list of coordinates of equal size specified by interval length.
    """
    contig_length = contig_lengths_dict.get(contig)

    if interval_length > contig_length:
        interval_length = contig_length
    
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

    print("\tContig {}: {} intervals of {} bases".format(contig, len(intervals), interval_length))

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
    f.write('barcode\tcontig\tcontig_position\tposition\tref\talt\tread_id\tstrand\n')
    
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


import subprocess
import pandas as pd
from collections import defaultdict
  

def get_coverage_df(edit_info, contig, output_folder, barcode_tag='CB', paired_end=False, 
                    verbose=False):
    # Just for single-cell, or bulk paired-end
    
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
        if not os.path.exists(contig_bam + '.bai'):
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

        # For single-cell or paired end approach, we will iterate through every single position in this subset of the data
        # and run the appropriate coverage-counting function.
        for i, pos in enumerate(positions_for_barcode):
            # For single-cell
            if barcode_tag:
                barcode_specific_contig = '{}_{}'.format(contig, barcode)
                # Alter from 3_C_AAACCCAAGAACTTCC-1, for example, to 3_AAACCCAAGAACTTCC-1'
                barcode_specific_contig_split = barcode_specific_contig.split("_")
                barcode_specific_contig_without_subdivision = "{}_{}".format(barcode_specific_contig_split[0], barcode_specific_contig_split[2])
                    
                coverage_at_pos = np.sum(samfile_for_barcode.count_coverage(barcode_specific_contig_without_subdivision, 
                                                                            pos-1, 
                                                                            pos,  
                                                                            quality_threshold=0, # base quality
                                                                            read_callback='all'
                                                                           ))

                coverage_dict['{}:{}'.format(barcode, pos)]['coverage'] = coverage_at_pos
                coverage_dict['{}:{}'.format(barcode, pos)]['source'] = contig

                if verbose:
                    #print("contig_bam:", contig_bam)
                    #print("barcode_specific_contig:", barcode_specific_contig)
                    print('contig_bam', contig_bam)
                    print("barcode_specific_contig_split", barcode_specific_contig_split)
                    print("barcode_specific_contig_without_subdivision:", barcode_specific_contig_without_subdivision)
                    print('barcode', barcode, 'position', pos)
                    print(coverage_dict['{}:{}'.format(barcode, pos)])
                    
            # For bulk, no barcodes, we will just have for example 19_no_barcode to convert to 19 to get coverage at that chrom
            else:  
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

    
def get_coverage_wrapper(parameters):
    edit_info, contig, output_folder, barcode_tag, paired_end, verbose = parameters

    output_filename = '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)

    """
    if os.path.exists(output_filename):
        # filter
        edit_info_and_coverage_joined = pd.read_csv(output_filename, sep='\t', names=[
            'barcode_position_index', 'barcode', 'contig', 'position', 'ref', 'alt', 'read_id', 'strand',
            'dist_from_end', 'base_quality', 'mapping_quality', 'barcode_position',
            'coverage', 'source', 'position_barcode'], dtype={'base_quality': int, 'dist_from_end': int, 'contig': str})
    else:
    """
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

    if verbose:
        if not coverage_df.empty:
            print('coverage_df', coverage_df)
        
    # Combine edit information with coverage information
    edit_info_and_coverage_joined = edit_info_df.join(coverage_df, how='inner')
    edit_info_and_coverage_joined['position_barcode'] = edit_info_and_coverage_joined['position'].astype(str) + '_' + edit_info_and_coverage_joined['barcode'].astype(str)

    if verbose:
        if not edit_info_and_coverage_joined.empty:
            print('edit_info_and_coverage_joined', edit_info_and_coverage_joined)

    edit_info_and_coverage_joined = edit_info_and_coverage_joined.drop_duplicates()
    
    edit_info_and_coverage_joined.to_csv(output_filename, sep='\t')

    assert(os.path.exists(output_filename))
    return output_filename
    


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
    print("\t{} suffixes".format(len(suffix_options)))
    
    for suffix in suffix_options:
        # Make a sub-subfolder to put the bams for this specific contig
        contig_folder = '{}/{}_{}/'.format(split_bams_folder, contig, suffix)
        if not os.path.exists(contig_folder):
            os.mkdir(contig_folder)
            
            
        bam_file_name = '{}/{}_{}.bam'.format(contig_folder, contig, suffix)

        if os.path.exists(f"{bam_file_name}.bai"):
            print(f"{bam_file_name}.bai, skipping...")
            return
        
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
            raise e
            
    
def concat_and_write_bams_wrapper(params):
    contig, df_dict, header_string, split_bams_folder, barcode_tag, number_of_expected_bams, verbose = params
    
    # print("df_dict keys: {}".format(df_dict.keys()))
    concat_and_write_bams(contig, df_dict, header_string, split_bams_folder, barcode_tag=barcode_tag, number_of_expected_bams=number_of_expected_bams, verbose=verbose)


def generate_and_run_bash_merge(output_folder, file1_path, file2_path, output_file_path, header_columns, barcode_tag=None):
    # Convert header list into a tab-separated string
    header = "\t".join(header_columns)

    position_adjustment = '1' # for samtools view
    if not barcode_tag:
        position_adjustment = '0'  # for samtools depth
    print(f"position adjustment is {position_adjustment} (barcode_tag is {barcode_tag})")
        
    # Generate the Bash command for processing
    bash_command = f"""#!/bin/bash
    # Step 1: Adjust the depths file by adding a new column that incorporates both contig and position
    # for join purposes, and sort by this column. Output in tab-separated format.
    awk -v OFS='\\t' '{{print $1, $2+{position_adjustment}, $3, $1":"($2+{position_adjustment})}}' "{file2_path}" | sort -k4,4V | uniq > {output_folder}/depth_modified.tsv
    
    # Step 2: Sort the first file numerically by the join column (the column incuding both contig and position information)
    sort -k3,3V "{file1_path}" | uniq > {output_folder}/final_edit_info_no_coverage_sorted.tsv

    # Step 3: Join the files on the specified columns, output all columns, and select necessary columns with tab separation
join -1 3 -2 4 -t $'\\t' {output_folder}/final_edit_info_no_coverage_sorted.tsv {output_folder}/depth_modified.tsv | awk -v OFS='\\t' '{{print $2, $3, $4, $5, $6, $7, $8, $11}}' > "{output_file_path}"

    # Step 4: Add header to the output file
    echo -e "{header}" | cat - "{output_file_path}" > temp && mv temp "{output_file_path}"
    """

    # Write the command to a shell script
    bash_script_path = "{}/merge_command.sh".format(output_folder)
    with open(bash_script_path, "w") as file:
        file.write(bash_command)

    # Run the generated bash script
    print("Running Bash merge script...")
    subprocess.run(["bash", bash_script_path], check=True)
    print(f"Merged file saved to {output_file_path}")
            

def generate_empty_matrix_file(matrix_output_filepath):
    pass


def pivot_depths_output(depths_input_filepath, matrix_output_filepath):
    """
    Transform depths data into a pivoted matrix with reformatted row and column labels.

        The rows will look like this:
        
        9_GATCCCTCAGTAACGG-1	3000448	1
        9_GATCCCTCAGTAACGG-1	3000469	1
        9_GATCCCTCAGTAACGG-1	3000508	3
        
        We want them to look like this:
        
        GATCCCTCAGTAACGG-1	9:3000448	1
        GATCCCTCAGTAACGG-1	9:3000469	1
        GATCCCTCAGTAACGG-1	9:3000508	3
        
        # And after the pivot:
                        9:3000448 9:3000469 9:3000508
        GATCCCTCAGTAACGG        1         1         3
    
    """
    # Read the universal coverage data
    df = pd.read_csv(depths_input_filepath, sep="\t", header=None, names=["Contig", "Position", "Coverage"])


    # Extract sample ID from the Contig and create a combined column for Position
    df["Barcode"] = df["Contig"].str.split("_", n=1).str[1]  # Extract everything after the first underscore
    df["CombinedPosition"] = df["Contig"].str.split("_", n=1).str[0] + ":" + df["Position"].astype(str)

    # Drop the original Contig and Position columns (optional, for clarity)
    df = df[["Barcode", "CombinedPosition", "Coverage"]]

    # Pivot the data to make a matrix of Sample x CombinedPosition with values being Coverage
    pivot = df.pivot(index="CombinedPosition", columns="Barcode", values="Coverage").fillna(0)
    
    # Write to output
    pivot.to_csv(matrix_output_filepath, sep="\t")
    


def run_command(command):
    # Run the samtools depth command
    subprocess.run(command, shell=True, check=True)


def merge_files_by_chromosome(args):
    """
    Helper function to merge files for a single chromosome.
    """
    chromosome, files, output_folder = args
    first_file = files[0]
    other_files = files[1:]
    merged_file = os.path.join(output_folder, f"{chromosome}_comprehensive_coverage_matrix.tsv")

    # Prepare the paste command
    strip_headers_command = " ".join(
        [f"<(cut -f2- {file})" for file in other_files]
    )
    paste_command = f"paste {first_file} {strip_headers_command} > {merged_file}"

    # Use bash to execute the paste command
    run_command(f"bash -c '{paste_command}'")
    print(f"Columnar merge complete for {chromosome}. Output saved to {merged_file}.")


def prepare_matrix_files_multiprocess(output_matrix_folder, 
                                      output_folder, 
                                      processes=4):
    """
    Merges matrix files column-wise, grouping by chromosome, using multiprocessing.
    """
    print("Merging matrices column-wise by chromosome...")

    # Group files by chromosome
    matrix_files = [
        os.path.join(output_matrix_folder, file)
        for file in os.listdir(output_matrix_folder)
        if file.endswith("matrix.tsv") and os.path.getsize(os.path.join(output_matrix_folder, file)) > 20  # Skip empty files
    ]
    
    if not matrix_files:
        print("No non-empty matrix files to merge.")
        return

    # Group files by chromosome
    file_groups = {}
    for file in matrix_files:
        chromosome = os.path.basename(file).split("all_cells_")[-1].split("_")[0]  # Adjust this split logic as needed
        file_groups.setdefault(chromosome, []).append(file)

    # Prepare arguments for multiprocessing
    task_args = [(chromosome, files, output_folder) for chromosome, files in file_groups.items()]

    # Use multiprocessing to run the merge for each chromosome
    with Pool(processes=processes) as pool:
        pool.map(merge_files_by_chromosome, task_args)

    print("All columnar merges complete.")



def merge_depth_files(output_folder, output_suffix=''):
    """
    Merges depth files into a single file.
    """
    print("Merging depths...")
        
    depth_files = f"{output_folder}/coverage/depths_{output_suffix}*.txt"
    merged_depth_file = f"{output_folder}/depths_{output_suffix}.txt"
    run_command(f"cat {depth_files} > {merged_depth_file}")
    print(f"Depths merged into {merged_depth_file}.")



def calculate_coverage(bam_filepath, bed_filepath, output_filepath, output_matrix_folder):
    """
    Mimic samtools depth -a by including positions with zero coverage and applying equivalent filters.
    """

    depths_file = output_filepath
    
    print(f"Running samtools view on {bed_filepath} for {bam_filepath}, outputting to {output_filepath}")
    
    regions = []
    with open(bed_filepath, "r") as bed:
        for line in bed:
            fields = line.strip().split()
            chrom, start, end = fields[0], int(fields[1]), int(fields[2])
            regions.append((chrom, start, end))

    if len(regions) > 0:
        print(f"\t{len(regions)} regions")
        
        with pysam.AlignmentFile(bam_filepath, "rb") as bam, open(depths_file, "w") as out:
            try:
                for chrom, start, end in regions:
                    # Get coverage, applying base quality filter
                    coverage = bam.count_coverage(
                        chrom, start, end, quality_threshold=0  # Mimics -Q 13 in samtools depth
                    )
        
                    # Calculate total coverage for each position and include zero-coverage positions
                    for pos in range(start, end):
                        total_coverage = sum(base[pos - start] for base in coverage)
                        out.write(f"{chrom}\t{pos}\t{total_coverage}\n")
            except Exception as e:
                # Return the exception and the arguments for debugging
                raise RuntimeError(
                        f"Error processing bam {bam_filepath} using bed {bed_filepath} at {chrom}:{start}-{end}, "
                        f"outputting to {depths_file}: {e}"
                    )
                    
        if output_matrix_folder:
            matrix_output_file = os.path.join(output_matrix_folder, f"{os.path.basename(depths_file).split('.')[0]}_matrix.tsv")
        
            if not os.path.exists(matrix_output_file) or os.path.getsize(matrix_output_file) == 0:
                # Pivot the depths output file into a matrix
                pivot_depths_output(depths_file, matrix_output_file)


def run_pysam_count_coverage(args_list, processes):
    """
    Runs pysam.count_coverage in parallel using multiprocessing.
    """
    try:
        with Pool(processes=processes) as pool:
            pool.starmap(calculate_coverage, args_list)

    except Exception as e:
        print(f"Aborting: One or more coverage calculations failed with an error: {e}", file=sys.stderr)
        sys.exit(1)  # Exit with an error code


def prepare_pysam_coverage_args(bam_filepaths, output_folder, output_suffix='', pivot=False, barcode_tag=None):
    """
    Prepare arguments for pysam coverage calculation for each BAM file and its BED file.
    """
    # Create a folder for matrix outputs if pivoting is enabled
    if pivot:
        output_matrix_folder = f"{output_folder}/matrix_outputs"
        os.makedirs(output_matrix_folder, exist_ok=True)
    else:
        output_matrix_folder = None

    args_list = []

    # Format output suffix
    if len(output_suffix) > 0:
        output_suffix = f"_{output_suffix}"

    print("prepare_pysam_coverage_args, barcode_tag is {}".format(barcode_tag))

    for bam_filepath in bam_filepaths:
        # Extract suffix from BAM filename
        bam_filename = os.path.basename(bam_filepath)
        bam_prefix, bam_suffix = bam_filename.split("_")[0], bam_filename.split("_")[1].split(".")[0]

        if barcode_tag:
            # Path to the corresponding split BED file
            bed_filepath = f"{output_folder}/combined{output_suffix}_split_by_suffix/combined{output_suffix}_{bam_prefix}_{bam_suffix}.bed"
            output_filepath = f"{output_folder}/coverage/depths{output_suffix}_{bam_prefix}_{bam_suffix}.txt"
            
        else:
            # bulk case
            bed_filepath = f"{output_folder}/combined{output_suffix}.bed"
            output_filepath = f"{output_folder}/coverage/depths{output_suffix}_{bam_filename.split('_')[1]}.txt"
            
            
        if os.path.exists(bed_filepath):
            args_list.append((bam_filepath, bed_filepath, output_filepath, output_matrix_folder))
        else:
            print(f"Did not find {bed_filepath}")
        
        
    return args_list



def make_depth_command_script_single_cell(paired_end, bam_filepaths, output_folder, all_depth_commands=[], 
                              output_suffix='', run=False, pivot=False, processes=4, barcode_tag=None):
    """
    Main function to generate and execute samtools depth commands, and optionally pivot and merge matrices.
    """
    samtools_depth_start_time = time.perf_counter()

     # Prepare pysam coverage arguments
    pysam_coverage_args = prepare_pysam_coverage_args(bam_filepaths, output_folder, output_suffix=output_suffix, pivot=pivot, barcode_tag=barcode_tag)
    
    print(f"\tPrepared coverage arguments for {len(pysam_coverage_args)} BAM files.")

    #all_depth_commands += samtools_depth_commands
    #print(f"\tsamtools_depth_commands: {len(samtools_depth_commands)}")

    with open('{}/depth_commands_{}.txt'.format(output_folder, output_suffix), 'w') as f:
        for d in all_depth_commands:
            f.write('{}\n\n'.format(d))
            
    if run:
        print("Calculating depths using multiprocessing with pysam...")
        run_pysam_count_coverage(pysam_coverage_args, processes)

        merge_depth_files(output_folder, output_suffix)

        if pivot:
            output_matrix_folder = f"{output_folder}/matrix_outputs"
            final_combined_matrices_folder = f"{output_folder}/final_matrix_outputs"
            os.makedirs(final_combined_matrices_folder, exist_ok=True)
        
            print("\nRunning pivot...\n")
            prepare_matrix_files_multiprocess(
                output_matrix_folder, 
                final_combined_matrices_folder,
                processes=processes
            )

    samtools_depth_total_time = time.perf_counter() - samtools_depth_start_time

    
    if pivot:
        print(f"Total seconds for samtools depth and matrix generation commands to run: {samtools_depth_total_time}")
    else:
        print(f"Total seconds for samtools depth commands to run: {samtools_depth_total_time}")



def calculate_sailor_score(sailor_row):
    edits = sailor_row['count']
    num_reads = sailor_row['coverage']
    original_base_counts = num_reads - edits
    
    cov_margin = 0.01
    alpha, beta = 0, 0

    num_failures = 0
    failure_messages = []
    try:
        edit_frac = float(edits) / float(num_reads)
    except Exception as e:
        num_failures += 1
        print("Bad Row: {}".format(sailor_row))
        return None
        
    # calc smoothed counts and confidence
    destination_base_smoothed = edits + alpha
    origin_base_smoothed = original_base_counts + beta

    ########  MOST IMPORTANT LINE  ########
    # calculates the confidence of theta as
    # P( theta < cov_margin | A, G) ~ Beta_theta(G, A)
    confidence = 1 - betainc(destination_base_smoothed, origin_base_smoothed, cov_margin)
    return confidence
    

def get_sailor_sites(final_site_level_information_df, conversion="C>T", skip_coverage=False):
    final_site_level_information_df = final_site_level_information_df[final_site_level_information_df['strand_conversion'] == conversion]

    if skip_coverage:
        # Case where we want to skip coverage counting, we will just set it to -1 in the sailor-style output
        coverage_col = "-1"
        weird_sites = pd.DataFrame()
    else:
        # Normally, assume that there is a coverage column
        coverage_col = final_site_level_information_df['coverage'].astype(str)

        weird_sites = final_site_level_information_df[
            (final_site_level_information_df.coverage == 0) |\
            (final_site_level_information_df.coverage < final_site_level_information_df['count'])]
    
        print("{} rows had coverage of 0 or more edits than coverage... filtering these out, but look into them...".format(
            len(weird_sites)))
              
        final_site_level_information_df = final_site_level_information_df[
        (final_site_level_information_df.coverage > 0) & \
        (final_site_level_information_df.coverage >= final_site_level_information_df['count'])
        ]

    
    final_site_level_information_df['combo'] = final_site_level_information_df['count'].astype(str) + ',' + coverage_col

    if skip_coverage:
        final_site_level_information_df['score'] = -1
    else:
        final_site_level_information_df['score'] = final_site_level_information_df.apply(calculate_sailor_score, axis=1)

    final_site_level_information_df['start'] = final_site_level_information_df['position']
    final_site_level_information_df['end'] = final_site_level_information_df['position'] + 1
    
    final_site_level_information_df = final_site_level_information_df[['contig', 'start', 'end', 'score', 'combo', 'strand']]
    return final_site_level_information_df, weird_sites


def concatenate_files(source_folder, file_pattern, output_filepath, run=False):
    # Create the concatenation command with numeric sorting and header skipping
    concat_command = (
        f"for f in $(ls -v {source_folder}/{file_pattern}); do "
        "tail -n +2 \"$f\"; "  # Skip the header row for each file
        "done > {}".format(output_filepath)
    )

    # Write the command to a shell script
    concat_bash = f"{source_folder}/concat_command.sh"
    with open(concat_bash, 'w') as f:
        f.write(concat_command)

    if run:
        print("Concatenating files in numerical order without headers...")
        subprocess.run(['bash', concat_bash])
        print("Done concatenating.")


def get_edits_with_coverage_df(output_folder,
                               barcode_tag=None):

    all_edit_info_unique_position_with_coverage_df = pd.read_csv('{}/final_edit_info.tsv'.format(output_folder), sep='\t',
                                                                     dtype={'coverage': int, 'position': int,
                                                                                             'contig': str})
    # If there was a barcode specified, then the contigs will have been set to a combination of contig and barcode ID.
    # For example, we will find a contig to be 9_GATCCCTCAGTAACGG-1, and we will want to simplify it back to simply 9,
    # as the barcode information is separately already present as it's own column in this dataframe. To ensure code continuity,
    # this will still be true even with no barcode specified, in which case the contig will be <contig>_no_barcode
    
    # Therefore: replace the contig with the part before the barcode
    if len(all_edit_info_unique_position_with_coverage_df) > 0:
        all_edit_info_unique_position_with_coverage_df['contig'] = all_edit_info_unique_position_with_coverage_df.apply(lambda row: row['contig'].replace('_{}'.format(row['barcode']), ''), axis=1)
        return all_edit_info_unique_position_with_coverage_df
    else:
        return all_edit_info_unique_position_with_coverage_df
        


def zero_edit_found(final_site_level_information_df, output_folder, sailor_list, bedgraphs_list, keep_intermediate_files, start_time, logging_folder):
    print("No edits found.")
    sites_columns = ['site_id','barcode','contig','position','ref','alt','strand','count','coverage','conversion','strand_conversion']
    sites_empty_df = pd.DataFrame(columns=sites_columns)
    sites_empty_df.to_csv('{}/final_filtered_site_info.tsv'.format(output_folder), sep='\t', index=False)

    Annotated_sites_columns = ['site_id','barcode','contig','position','ref','alt','strand','count','coverage','conversion','strand_conversion','feature_name','feature_type','feature_strand']
    annotated_sites_empty_df = pd.DataFrame(columns=Annotated_sites_columns)
    annotated_sites_empty_df.to_csv('{}/final_filtered_site_info_annotated.tsv'.format(output_folder), sep='\t', index=False)

    empty_df = pd.DataFrame()
    if len(sailor_list) > 0:
        for conversion in sailor_list:
            conversion_search = conversion[0] + '>' + conversion[1]
            empty_df.to_csv('{}/sailor_style_sites_{}.bed'.format(
                output_folder, 
                conversion_search.replace(">", "-")), 
                header=False, index=False, sep='\t')

    if len(bedgraphs_list) > 0:
        bedgraph_folder = '{}/bedgraphs'.format(output_folder)
        make_folder(bedgraph_folder)
        for conversion in bedgraphs_list:
            conversion_search = conversion[0] + '>' + conversion[1]
            empty_df.to_csv('{}/{}_{}.bedgraph'.format(bedgraph_folder, output_folder.split('/')[-1], conversion), sep='\t', index=False, header=False)
            
    current, peak = tracemalloc.get_traced_memory()
    
    with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
        f.write(f'sites\t{len(final_site_level_information_df)}\n') 
        f.write(f'peak_memory_mb\t{peak/1e6}\n') 
        f.write(f'time_elapsed_seconds\t{time.time()-start_time:.2f}s\n') 

    print(f"Current memory usage {current/1e6}MB; Peak: {peak/1e6}MB")
    print(f'Time elapsed: {time.time()-start_time:.2f}s')

    if not keep_intermediate_files:
        pretty_print("Deleting intermediate files...", style="-")
        delete_intermediate_files(output_folder)

    pretty_print("Done!", style="+")
    return 'Done'


def delete_intermediate_files(output_folder):
    to_delete = ['coverage', 'edit_info', 'split_bams', 'combined_all_cells_split_by_suffix',
                 'combined_source_cells_split_by_suffix',
                 'matrix_outputs',
                 'all_edit_info.tsv', 
                 'concat_command.sh', 'depth_commands_source_cells.sh', 'depth_commands_source_cells.txt', 'combined.bed', 'merge_command.sh',
                 'final_edit_info_no_coverage.tsv', 'final_edit_info_no_coverage_sorted.tsv',
                 'depths_source_cells.txt', 'depth_modified.tsv', 'final_edit_info.tsv', 'final_filtered_edit_info.tsv',
                 'combined_all_cells.bed', 'depth_commands_all_cells.sh', 'depth_commands_all_cells.txt', 'depths_all_cells.txt', 'combined_source_cells.bed'
                ]
    for object in to_delete:
        object_path = '{}/{}'.format(output_folder, object)

        if os.path.exists(object_path):
            if os.path.isfile(object_path):
                os.remove(object_path)
            else:
                shutil.rmtree(object_path)
