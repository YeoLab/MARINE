import pysam
import os
from glob import glob
import sys
from sys import getsizeof
import time
import numpy as np
import pandas as pd
import polars as pl
from collections import defaultdict
import multiprocessing
from tqdm import tqdm
from multiprocessing import get_context

from read_process import incorporate_replaced_pos_info,incorporate_insertions_and_deletions,\
get_positions_from_md_tag,reverse_complement,get_edit_information,get_edit_information_wrapper,\
has_edits,get_total_coverage_for_contig_at_position,\
print_read_info, get_read_information, get_hamming_distance, remove_softclipped_bases,find

from utils import get_contig_lengths_dict, get_intervals, index_bam, write_rows_to_info_file, write_header_to_edit_info, \
write_read_to_bam_file, remove_file_if_exists, make_folder, concat_and_write_bams_wrapper, make_edit_finding_jobs, pretty_print, get_contigs_that_need_bams_written, split_bed_file, \
get_coverage_wrapper, write_reads_to_file, sort_bam, rm_bam, suffixes, get_broken_up_contigs, run_command, \
make_depth_command_script_single_cell, concatenate_files, generate_and_run_bash_merge, read_barcode_whitelist_file

import os, psutil


def generate_depths(output_folder, bam_filepaths, original_bam_filepath, paired_end=False, barcode_tag=None, cores=1):
    
    coverage_start_time = time.perf_counter()

    all_depth_commands = []

    combine_edit_sites_command = (
        "echo 'concatenating bed file...';"
        "for file in {}/edit_info/*edit_info.tsv; do "
        "awk 'NR > 1 {{print $2, $4-1, $4}}' OFS='\t' \"$file\"; "
        "done | sort -k1,1 -k2,2n -u > {}/combined_source_cells.bed;"
    ).format(output_folder, output_folder)

    if not os.path.exists(f'{output_folder}/combined_source_cells.bed'):
        run_command(combine_edit_sites_command)
    
    all_depth_commands.append(combine_edit_sites_command)

    output_suffix = 'source_cells'
    
    if barcode_tag:
        coverage_subfolder = '{}/coverage'.format(output_folder)
        make_folder(coverage_subfolder)

        # Single cell mode
        split_bed_file(
            f"{output_folder}/combined_{output_suffix}.bed",
            f"{output_folder}/combined_{output_suffix}_split_by_suffix",
            bam_filepaths,
            output_suffix=output_suffix
        )
        
        make_depth_command_script_single_cell(paired_end, bam_filepaths, output_folder,
                                  all_depth_commands=all_depth_commands, output_suffix='source_cells', run=True, processes=cores, barcode_tag=barcode_tag)
        
    else:
        if paired_end:
            paired_end_flag = '-s '
        else:
            paired_end_flag = ''
            
        # Bulk mode, we will not split the bed and simply use samtools depth on the combined.bed
        samtools_depth_command = f"samtools depth {paired_end_flag}-a -b {output_folder}/combined_source_cells.bed {original_bam_filepath} > {output_folder}/depths_source_cells.txt"
        run_command(samtools_depth_command)
        

    print("Concatenating edit info files...")
    concatenate_files(output_folder, "edit_info/*edit_info.tsv",
                      "{}/final_edit_info_no_coverage.tsv".format(output_folder),
                     run=True)

    print("Append the depth columns to the concatenated final_edit_info file...")

    header_columns = ['barcode', 'contig', 'position', 'ref', 'alt',
                      'read_id', 'strand', 'coverage']


    generate_and_run_bash_merge(output_folder,
                                '{}/final_edit_info_no_coverage.tsv'.format(output_folder),
                            '{}/depths_source_cells.txt'.format(output_folder), 
                            '{}/final_edit_info.tsv'.format(output_folder), 
                                header_columns, barcode_tag=barcode_tag)
    
    coverage_total_time = time.perf_counter() - coverage_start_time
    
    total_seconds_for_contig_df = pd.DataFrame({'coverage_total_time': [coverage_total_time]})
    return coverage_total_time, total_seconds_for_contig_df


def bam_processing(bam_filepath, overall_label_to_list_of_contents, output_folder, barcode_tag='CB', cores=1, number_of_expected_bams=4,
                   verbose=False):
    # Only used for single-cell and/or long read reconfiguration of bams to optimize coverage calculation
    split_bams_folder = '{}/split_bams'.format(output_folder)
    make_folder(split_bams_folder)
    contigs_to_generate_bams_for = get_contigs_that_need_bams_written(list(overall_label_to_list_of_contents.keys()),
                                                                      split_bams_folder, 
                                                                      barcode_tag=barcode_tag,
                                                                    number_of_expected_bams=number_of_expected_bams
                                                                     )
    if verbose:
        pretty_print("Will split and reconfigure the following contigs: {}".format(",".join(contigs_to_generate_bams_for)))
    
    
    # BAM Generation
    total_bam_generation_time, total_seconds_for_bams = run_bam_reconfiguration(
        split_bams_folder, 
        bam_filepath, 
        overall_label_to_list_of_contents, 
        contigs_to_generate_bams_for, 
        barcode_tag=barcode_tag, 
        cores=cores,
        number_of_expected_bams=number_of_expected_bams,
        verbose=verbose)
    
    total_seconds_for_bams_df = pd.DataFrame.from_dict(total_seconds_for_bams, orient='index')
    total_seconds_for_bams_df.columns = ['seconds']
    total_seconds_for_bams_df['contigs'] = total_seconds_for_bams_df.index
    total_seconds_for_bams_df.index = range(len(total_seconds_for_bams_df))
    
    return total_bam_generation_time, total_seconds_for_bams_df
    

def edit_finder(bam_filepath, output_folder, strandedness, barcode_tag="CB", barcode_whitelist=None, contigs=[],
                verbose=False, cores=64, min_read_quality=0, min_base_quality=0, dist_from_end=0, interval_length=2000000):
    
    pretty_print("Each contig is being split into subsets of length...".format(interval_length))
    
    overall_label_to_list_of_contents, results, overall_time, overall_total_reads, \
    total_seconds_for_reads, counts_summary_df = run_edit_identifier(
        bam_filepath, 
        output_folder, 
        strandedness=strandedness,
        barcode_tag=barcode_tag,
        barcode_whitelist=barcode_whitelist,
        contigs=contigs,
        verbose=verbose,
        cores=cores,
        min_read_quality=min_read_quality,
        min_base_quality=min_base_quality,
        dist_from_end=dist_from_end,
        interval_length=interval_length
    )
    
    #print(overall_label_to_list_of_contents.keys())
    #print(overall_label_to_list_of_contents.get(list(overall_label_to_list_of_contents.keys())[0]))
    
    pretty_print(
        [
            "Reads processed:\t{}".format(overall_total_reads), 
            "Time to process reads in min:\t{}".format(round(overall_time/60, 5)),
            "Read Summary:\n{}".format(counts_summary_df)
        ],
        style="-"
    )
    
    
    total_seconds_for_reads_df = pd.DataFrame.from_dict(total_seconds_for_reads, orient='index')
    total_seconds_for_reads_df.columns = ['seconds']
    total_seconds_for_reads_df['reads'] = total_seconds_for_reads_df.index
    total_seconds_for_reads_df.index = range(len(total_seconds_for_reads_df))
    
    
    return overall_label_to_list_of_contents, results, total_seconds_for_reads_df, overall_total_reads, counts_summary_df
    
def run_edit_identifier(bampath, output_folder, strandedness, barcode_tag="CB", barcode_whitelist=None, contigs=[], verbose=False, cores=64, min_read_quality=0, min_base_quality=0, dist_from_end=0, interval_length=2000000):

    # Make subfolder in which to information about edits
    edit_info_subfolder = '{}/edit_info'.format(output_folder)
    make_folder(edit_info_subfolder)
    
    edit_finding_jobs = make_edit_finding_jobs(bampath, output_folder, strandedness, barcode_tag, barcode_whitelist, contigs, verbose, min_read_quality, min_base_quality, dist_from_end, interval_length=interval_length)
    pretty_print("{} total jobs".format(len(edit_finding_jobs)))
    
    # Performance statistics
    overall_total_reads = 0
    total_seconds_for_reads = {0: 1}
    
    # Result containers
    overall_label_to_list_of_contents = defaultdict(lambda:{})
    results = []
    
    start_time = time.perf_counter()

    all_counts_summary_dfs = []
    overall_count_summary_dict = defaultdict(lambda:0)
    #multiprocessing.set_start_method('spawn')
    with get_context("spawn").Pool(processes=cores, maxtasksperchild=4) as p:
        max_ = len(edit_finding_jobs)
        with tqdm(total=max_) as pbar:
            for _ in p.imap_unordered(find_edits_and_split_bams_wrapper, edit_finding_jobs):
                # values returned within array _ are:
                # ~~~~  contig, label, barcode_to_concatted_reads_pl, total_reads, counts_df, time_df, total_time
                # So the line overall_label_to_list_of_contents[_[0]][_[1]] =  _[2]
                # is equivalent to overall_label_to_list_of_contents[contig][label] = barcode_to_concatted_reads_pl
                pbar.update()

                if barcode_tag: 
                    # Only keep this information for single cell requirements
                    overall_label_to_list_of_contents[_[0]][_[1]] =  _[2]
                total_reads = _[3]
                counts_summary_df = _[4]
                all_counts_summary_dfs.append(counts_summary_df)

                total_time = time.perf_counter() - start_time

                overall_total_reads += total_reads

                total_seconds_for_reads[overall_total_reads] = total_time

    overall_time = time.perf_counter() - start_time 
    
    if len(all_counts_summary_dfs) == 0:
        return overall_label_to_list_of_contents, results, overall_time, overall_total_reads, total_seconds_for_reads, pd.DataFrame()

    all_counts_summary_dfs_combined = pd.concat(all_counts_summary_dfs, axis=1)
    #print(all_counts_summary_dfs_combined.index, all_counts_summary_dfs_combined.columns)
    
    overall_count_summary_df = pd.DataFrame.from_dict(all_counts_summary_dfs_combined).sum(axis=1)
    #print(overall_count_summary_df)

    return overall_label_to_list_of_contents, results, overall_time, overall_total_reads, total_seconds_for_reads, overall_count_summary_df



def run_bam_reconfiguration(split_bams_folder, bampath, overall_label_to_list_of_contents, contigs_to_generate_bams_for, barcode_tag='CB', cores=1, number_of_expected_bams=4, verbose=False):
    start_time = time.perf_counter()

    with pysam.AlignmentFile(bampath, "rb") as samfile:
        # Get the bam header, which will be used for each of the split bams too
        header_string = str(samfile.header)

    # num_processes = np.max([len(contigs_to_generate_bams_for), 32])
    num_processes = cores
    
    total_seconds_for_bams = {0: 1}
    total_bams = 0
    with get_context("spawn").Pool(processes=num_processes, maxtasksperchild=4) as p:
        max_ = len(contigs_to_generate_bams_for)
        with tqdm(total=max_) as pbar:
            for _ in p.imap_unordered(concat_and_write_bams_wrapper, [[i[0], i[1], header_string, split_bams_folder, 
                                                                       barcode_tag, number_of_expected_bams, verbose] for i in overall_label_to_list_of_contents.items() if i[0] in contigs_to_generate_bams_for]):
                pbar.update()
                
                total_bams += 1
                total_time = time.perf_counter() - start_time
                total_seconds_for_bams[total_bams] = total_time

    total_bam_generation_time = time.perf_counter() - start_time
    return total_bam_generation_time, total_seconds_for_bams


def run_edit_finding(barcode_tag,
                     barcode_whitelist_file, 
                     contigs, 
                     num_per_sublist,
                     bam_filepath, 
                     output_folder, 
                     strandedness,
                     min_read_quality,
                     min_base_quality,
                     min_dist_from_end,
                     interval_length,
                     number_of_expected_bams,
                     cores,
                     logging_folder,
                     verbose=False
                    ):
    overall_total_reads_processed = 0
    if barcode_whitelist_file:
        barcode_whitelist = read_barcode_whitelist_file(barcode_whitelist_file)
    else:
        barcode_whitelist = None

    if len(contigs) == 0:
        # Take care of the case where no contigs are specified, so that all contigs available are processed
        broken_up_contigs = [[]]
    else:
        if barcode_tag:
            # For single cell sequencing we will only process this many contigs at a time
            broken_up_contigs = get_broken_up_contigs(contigs, num_per_sublist)
                
        else:
            # For bulk sequencing we will just process all contigs 
            broken_up_contigs = [contigs]

    print('Contig groups to be processed:', broken_up_contigs)
    
    overall_counts_summary_df = defaultdict(lambda:0)
    overall_total_reads_processed = 0
    for subcontig_list in broken_up_contigs:
            
        overall_label_to_list_of_contents, results, total_seconds_for_reads_df, total_reads_processed, counts_summary_df = edit_finder(
            bam_filepath, 
            output_folder, 
            strandedness,
            barcode_tag,
            barcode_whitelist,
            subcontig_list,
            verbose,
            cores=cores,
            min_read_quality=min_read_quality,
            min_base_quality=min_base_quality,
            dist_from_end=min_dist_from_end,
            interval_length=interval_length
        )

        for k,v in counts_summary_df.items():
            overall_counts_summary_df[k] += v
            
        overall_total_reads_processed += total_reads_processed
        
        #total_seconds_for_reads_df.to_csv("{}/edit_finder_timing.tsv".format(logging_folder), sep='\t')
        
        if barcode_tag:
            # Make a subfolder into which the split bams will be placed
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            pretty_print("Contigs processed\n\n\t{}".format(sorted(list(overall_label_to_list_of_contents.keys()))))
            pretty_print("Splitting and reconfiguring BAMs to optimize coverage calculations", style="~")
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            
            total_bam_generation_time, total_seconds_for_bams_df = bam_processing(bam_filepath, overall_label_to_list_of_contents, output_folder, barcode_tag=barcode_tag, cores=cores, number_of_expected_bams=number_of_expected_bams, verbose=verbose)
            #total_seconds_for_bams_df.to_csv("{}/bam_reconfiguration_timing.tsv".format(logging_folder), sep='\t')
            pretty_print("Total time to concat and write bams: {} minutes".format(round(total_bam_generation_time/60, 3)))

        print("Deleting overall_label_to_list_of_contents...")
        del overall_label_to_list_of_contents

    
    with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
        f.write(f'total_reads_processed\t{overall_total_reads_processed}\n') 
        for k, v in overall_counts_summary_df.items():
            f.write(f'{k}\t{v}\n') 

        f.write(f'edits per read (EPR)\t{overall_counts_summary_df.get("total_edits")/overall_total_reads_processed}\n')


def incorporate_barcode(read_as_string, contig, barcode):
    read_tab_separated = read_as_string.split('\t')
    contig_section = '{}_{}'.format(contig, barcode)
    read_tab_separated[2] = contig_section
    read_as_string = '\t'.join(read_tab_separated)
    return read_as_string


def write_bam_file(reads, bam_file_name, header_string):   
    # Write, sort and index bam immediately
    write_reads_to_file(reads, bam_file_name, header_string)
    try:
        # print("\tSorting {}...".format(bam_file_name))
        sorted_bam_file_name = sort_bam(bam_file_name)
        # print("\tIndexing {}...".format(sorted_bam_file_name))
        index_bam(sorted_bam_file_name)
        rm_bam(bam_file_name)
    except Exception as e:
        print("Failed at indexing {}, {}".format(bam_file_name, e))
        

def find_edits(bampath, contig, split_index, start, end, output_folder, barcode_tag="CB", strandedness=0, barcode_whitelist=None, verbose=False, min_read_quality=0, min_base_quality=0, dist_from_end=0):  
    edit_info_subfolder = '{}/edit_info'.format(output_folder)
        
    time_reporting = {}
    start_time = time.perf_counter()
    
    samfile = pysam.AlignmentFile(bampath, "rb")
    
    counts = defaultdict(lambda:defaultdict(lambda:0))
    counts[contig]['total_edits'] = 0
    counts[contig]['edited'] = 0
    
    total_reads = 0
    
    bam_handles_for_barcodes = {}
    read_lists_for_barcodes = defaultdict(lambda:[])
    
    reads_for_contig = samfile.fetch(contig, start, end, multiple_iterators=True)
        
    output_file = '{}/{}_{}_{}_{}_edit_info.tsv'.format(edit_info_subfolder, contig, split_index, start, end)
    output_bedfile = '{}/{}_{}_{}_{}_edit_positions.bed'.format(edit_info_subfolder, contig, split_index, start, end)

    remove_file_if_exists(output_file)
    
    with open(output_file, 'w') as f:        
        write_header_to_edit_info(f)

        for i, read in enumerate(reads_for_contig):
            total_reads += 1
            
            if total_reads % 1000 == 0:
                time_reporting[total_reads] = time.perf_counter() - start_time

            if barcode_tag is None:
                barcode = 'no_barcode'
            elif read.has_tag(barcode_tag):
                barcode = read.get_tag(barcode_tag)
            else:
                barcode = 'missing'
                
            if barcode_whitelist and barcode != 'no_barcode':
                if barcode_tag == "IB" and read.has_tag("CB"):
                    # Single-cell long reads
                    cell_barcode = read.get_tag("CB")
                else:
                    cell_barcode = barcode
                    
                if cell_barcode not in barcode_whitelist:
                    counts[contig]['Barcode Filtered'] += 1
                    continue
            
            try:
                error_code, list_of_rows, num_edits_of_each_type = get_read_information(read, contig, strandedness=strandedness, barcode_tag=barcode_tag, verbose=verbose, min_read_quality=min_read_quality, min_base_quality=min_base_quality, 
dist_from_end=dist_from_end)
            except Exception as e:
                print("Failed getting read info on\n{}, {}".format(read.to_string(), e))
                break
                
            if error_code:
                counts[contig][error_code] += 1
            else:
                counts[contig]['edited'] += 1
                counts[contig]['total_edits'] += len(list_of_rows)
                write_rows_to_info_file(list_of_rows, f)
            
            # Store each read using its string representation only if there was not an mapq_low error code while processing the read
            if error_code != 'mapq_low':
                read_as_string = read.to_string() 
                if barcode_tag:
                    read_as_string = incorporate_barcode(read_as_string, contig, barcode)
                
                read_lists_for_barcodes[barcode].append(read_as_string)

        

    barcode_to_concatted_reads = {}
    if barcode_tag:
        # Add all reads to dictionary for contig and barcode, in their string representation
        for barcode, read_list in read_lists_for_barcodes.items():        
            
            # Concatenate the string representations of all reads for each bam-contig combination
            all_reads_concatted = '\n'.join(read_list)
                
            # Save this concatenated block of text to dictionary
            barcode_to_concatted_reads[barcode] = all_reads_concatted

    else: 
        # For bulk samples, we are just going to directly write the filtered reads to a bam file
        # containing only the reads in which the edits for this chunk were found, for easy coverage
        # calculation later.
        
        split_bams_subfolder = '{}/split_bams'.format(output_folder)
        make_folder(split_bams_subfolder)
        
        for barcode, read_list in read_lists_for_barcodes.items(): 
            make_folder('{}/{}'.format(split_bams_subfolder, contig))
                        
            bam_file_name = '{}/{}/{}_{}_{}_{}.bam'.format(split_bams_subfolder, contig, contig, split_index, start, end)
            header_string = str(samfile.header)
            write_bam_file(read_list, bam_file_name, header_string)
            
        
    time_reporting[total_reads] = time.perf_counter() - start_time
    
    samfile.close()
    
    return barcode_to_concatted_reads, total_reads, counts, time_reporting
        

def find_edits_and_split_bams(bampath, contig, split_index, start, end, output_folder, strandedness=0, barcode_tag="CB", barcode_whitelist=None, verbose=False, min_read_quality=0, min_base_quality=0, dist_from_end=0):
    barcode_to_concatted_reads, total_reads, counts, time_reporting = find_edits(bampath, contig, split_index,
                                                                         start, end, output_folder, barcode_tag=barcode_tag,
                                                                                 strandedness=strandedness,
                                                                                 barcode_whitelist=barcode_whitelist, verbose=verbose,
                                                                                 min_read_quality=min_read_quality,
                                                                                 min_base_quality=min_base_quality,
                                                                                 dist_from_end=dist_from_end
                                                                                )    
    return barcode_to_concatted_reads, total_reads, counts, time_reporting
    
    
    
import random


def find_edits_and_split_bams_wrapper(parameters):
    try:
        start_time = time.perf_counter()
        bampath, contig, split_index, start, end, output_folder, strandedness, barcode_tag, barcode_whitelist, verbose, min_read_quality, min_base_quality, dist_from_end = parameters
        label = '{}({}):{}-{}'.format(contig, split_index, start, end)
        
        barcode_to_concatted_reads, total_reads, counts, time_reporting = find_edits_and_split_bams(
            bampath, 
            contig, 
            split_index, 
            start, 
            end,                                                           
            output_folder, 
            strandedness,
            barcode_tag=barcode_tag,
            barcode_whitelist=barcode_whitelist,
            verbose=verbose,
            min_read_quality=min_read_quality,
            min_base_quality=min_base_quality,
            dist_from_end=dist_from_end
        )
        counts_df = pd.DataFrame.from_dict(counts)
        
        if verbose:
            #pass
            print("{}:{}, total reads: {}, counts_df: {}".format(contig, split_index, total_reads, counts_df))
        
        time_df = pd.DataFrame.from_dict(time_reporting, orient='index')
        
        # Add a random integer column for grouping
        bucket_label = int(split_index)#%BULK_SPLITS
        
        if verbose:
            pass
            #print("\t\tsplit_index is {}; Bucket label is {}".format(split_index, bucket_label))
            #print("Num barcodes/identifiers: {}".format(len(barcode_to_concatted_reads)))
        
        if len(barcode_to_concatted_reads) > 0:
            barcode_to_concatted_reads_pl = pl.from_dict(barcode_to_concatted_reads).transpose(include_header=True, header_name='barcode').rename({"column_0": "contents"})
            
            if verbose:
                print("\tLength after transpose: {}".format(len(barcode_to_concatted_reads_pl)))
                print("\tHeight after transpose: {}".format(barcode_to_concatted_reads_pl.height))
            
            barcode_to_concatted_reads_pl = barcode_to_concatted_reads_pl.with_columns(bucket = pl.lit([bucket_label for _ in range(barcode_to_concatted_reads_pl.height)]))
            
        else:
            # No transposes are allowed on empty dataframes
            barcode_to_concatted_reads_pl = pl.from_dict(barcode_to_concatted_reads)
            
        total_time = time.perf_counter() - start_time
        return contig, label, barcode_to_concatted_reads_pl, total_reads, counts_df, time_df, total_time
    except Exception as e:
        print('Contig {}: {}'.format(label, e))
        return 0, label, pd.DataFrame(), 0, pd.DataFrame(), pd.DataFrame(), 0
    
    
    
def run_coverage_calculator(edit_info_grouped_per_contig_combined, 
                            output_folder, 
                            barcode_tag='CB',
                            paired_end=False, 
                            verbose=False,
                            processes=16
                           ):
    coverage_counting_job_params = get_job_params_for_coverage_for_edits_in_contig(
        edit_info_grouped_per_contig_combined, 
        output_folder,
        barcode_tag=barcode_tag,
        paired_end=paired_end,
        verbose=verbose
    )
    
    start_time = time.perf_counter()

    total_seconds_for_contig = {0: 1}
    total_contigs = 0
    
    results = []
    # Spawn has to be used instead of the default fork when using the polars library
    with get_context("spawn").Pool(processes=processes) as p:
        max_ = len(coverage_counting_job_params)
        with tqdm(total=max_) as pbar:
            for _ in p.imap_unordered(get_coverage_wrapper, coverage_counting_job_params):
                pbar.update()

                #print(_.columns)
                results.append(_)

                total_contigs += 1
                total_time = time.perf_counter() - start_time
                total_seconds_for_contig[total_contigs] = total_time
                
    total_time = time.perf_counter() - start_time
    return results, total_time, total_seconds_for_contig


def get_job_params_for_coverage_for_edits_in_contig(edit_info_grouped_per_contig_combined, output_folder,
                                                    barcode_tag='CB', paired_end=False, verbose=False):
    job_params = []
    
    for contig, edit_info in edit_info_grouped_per_contig_combined.items():
                    
        job_params.append([edit_info, contig, output_folder, barcode_tag, paired_end, verbose])  
        
    return job_params

    
def gather_edit_information_across_subcontigs(output_folder, barcode_tag='CB', number_of_expected_bams=4):
    
    splits = [i.split("/")[-1].split('_edit')[0] for i in sorted(glob('{}/edit_info/*'.format(output_folder)))]

    all_edit_info_for_barcodes = []

    edit_info_grouped_per_contig = defaultdict(lambda:[])
    edit_info_grouped_per_contig_combined = defaultdict(lambda:[])

    num_splits = len(splits)
    # print("Grouping edit information outputs by contig...")
    if num_splits > 500:
        interval = 400
    else:
        interval = 10
    
    for i, split in enumerate(splits):
        if i%interval == 0:
            print("\tsplit {}, {}/{}...".format(split, i, num_splits))

        contig = split.split("_")[0]

        edit_info_file = '{}/edit_info/{}_edit_info.tsv'.format(output_folder, split)
        edit_info_df = pd.read_csv(edit_info_file, sep='\t')
        edit_info_df['contig'] = edit_info_df['contig'].astype(str)
        edit_info_df['position'] = edit_info_df['position'].astype(int)

        edit_info = pl.from_pandas(edit_info_df) 
        
        if barcode_tag in ['CB', 'IS', 'IB']:
            # For single-cell or long read data we have to split the edit infos for each contig additionally by cell barcode 
            # or isoform ID in order to make the coverage calculation efficient per cell and/or per isoform
            suffix_options = suffixes.get(barcode_tag)
            for suffix in suffix_options:
                edit_info_subset = edit_info.filter(pl.col("barcode").str.ends_with(suffix))
                edit_info_grouped_per_contig["{}_{}".format(contig, suffix)].append(edit_info_subset)

        else:
            # For bulk data we don't have to do any filtering, the edits calculated for each split interval
            # can be paired directly with the split bam for that interval
            edit_info_grouped_per_contig["{}".format(split)].append(edit_info)
            
        del edit_info_df

    print("Done grouping! Concatenating ...")
    for contig, list_of_edit_info_dfs in edit_info_grouped_per_contig.items():
        edit_info_grouped_per_contig_combined[contig] = pl.concat(list_of_edit_info_dfs)
    print("Done concatenating!")
        
    return edit_info_grouped_per_contig_combined






def add_site_id(all_edit_info):
    if len(all_edit_info) == 0:
        return all_edit_info

    return all_edit_info.with_columns(
        pl.concat_str(
            [
                pl.col("barcode"),
                pl.col("contig"),
                pl.col("position"),
                pl.col("ref"),
                pl.col("alt"),
                pl.col("strand")
            ],
            separator="_",
        ).alias("site_id"))



def get_count_and_coverage_per_site(all_edit_info, skip_coverage=False):
    num_edits_df = all_edit_info.group_by("site_id").count()

    if not skip_coverage:
        coverage_df = all_edit_info.group_by("site_id").agg(pl.col("coverage").max())
        return num_edits_df.join(coverage_df, on='site_id')
    else:
        return num_edits_df



def generate_site_level_information(all_edit_info, skip_coverage=False):
    number_of_edits = len(all_edit_info)
    
    all_edit_info = add_site_id(all_edit_info)
    
    if len(all_edit_info) == 0:
        print("DataFrame is empty. Returning an empty DataFrame.")
        return all_edit_info

    identifying_values = ["site_id", "barcode", "contig", "position", "ref", "alt", "strand"]

    unique_rows_df = all_edit_info.select(identifying_values).unique(subset=identifying_values, maintain_order=True)

    count_and_coverage_at_site_df = get_count_and_coverage_per_site(all_edit_info, skip_coverage=skip_coverage)
    final_site_information_df = unique_rows_df.join(count_and_coverage_at_site_df, on='site_id')

    final_site_information_df = final_site_information_df.with_columns(
        pl.concat_str(
            [
                pl.col("ref"),
                pl.col("alt")
            ],
            separator=">",
        ).alias("conversion"))

    if not skip_coverage:
        number_of_sites = len(all_edit_info.group_by("site_id").agg(pl.col("coverage").unique()))
        assert(len(final_site_information_df) == number_of_sites)
    

    return final_site_information_df