#!/usr/bin/env python
import argparse
from collections import defaultdict
from glob import glob
from multiprocessing import Pool
import multiprocessing
import os
import pandas as pd
import polars as pl
import psutil
import pysam
import shutil
import subprocess
import sys
from sys import getsizeof
import time
from tqdm import tqdm
import tracemalloc
from matplotlib import pyplot as plt
import math
import shlex

# checkpoint 

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src/'))

from read_process import incorporate_replaced_pos_info,incorporate_insertions_and_deletions,\
get_positions_from_md_tag,reverse_complement,get_edit_information,get_edit_information_wrapper,\
has_edits,get_total_coverage_for_contig_at_position,\
print_read_info, get_read_information, get_hamming_distance, \
remove_softclipped_bases,find

from utils import get_intervals, index_bam, write_rows_to_info_file, write_header_to_edit_info, \
write_read_to_bam_file, remove_file_if_exists, make_folder, concat_and_write_bams_wrapper, \
pretty_print, read_barcode_whitelist_file, get_contigs_that_need_bams_written, \
make_depth_command_script_single_cell, generate_and_run_bash_merge, get_sailor_sites, \
concatenate_files, run_command, get_edits_with_coverage_df, zero_edit_found, delete_intermediate_files

from core import run_edit_identifier, run_bam_reconfiguration, \
gather_edit_information_across_subcontigs, run_coverage_calculator, generate_site_level_information

from annotate import annotate_sites, get_strand_specific_conversion 


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

    
def bam_processing(overall_label_to_list_of_contents, output_folder, barcode_tag='CB', cores=1, number_of_expected_bams=4,
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
    total_bam_generation_time, total_seconds_for_bams = run_bam_reconfiguration(split_bams_folder, bam_filepath, overall_label_to_list_of_contents, contigs_to_generate_bams_for, barcode_tag=barcode_tag, cores=cores, 
                                                                                number_of_expected_bams=number_of_expected_bams,
                                                                                verbose=verbose)
    
    total_seconds_for_bams_df = pd.DataFrame.from_dict(total_seconds_for_bams, orient='index')
    total_seconds_for_bams_df.columns = ['seconds']
    total_seconds_for_bams_df['contigs'] = total_seconds_for_bams_df.index
    total_seconds_for_bams_df.index = range(len(total_seconds_for_bams_df))
    
    return total_bam_generation_time, total_seconds_for_bams_df
    
    
def print_marine_logo():
    logo_lines = [
    "::::    ::::      :::     :::::::::  ::::::::::: ::::    ::: :::::::::: ",
    "+:+:+: :+:+:+   :+: :+:   :+:    :+:     :+:     :+:+:   :+: :+:        ",
    "+:+ +:+:+ +:+  +:+   +:+  +:+    +:+     +:+     :+:+:+  +:+ +:+        ",
    "+#+  +:+  +#+ +#++:++#++: +#++:++#:      +#+     +#+ +:+ +#+ +#++:++#   ",
    "+#+       +#+ +#+     +#+ +#+    +#+     +#+     +#+  +#+#+# +#+        ",
    "#+#       #+# #+#     #+# #+#    #+#     #+#     #+#   #+#+# #+#        ",
    "###       ### ###     ### ###    ### ########### ###    #### ########## "
    ]
    for l in logo_lines:
        pretty_print(l)
        
    pretty_print("Multi-core Algorithm for Rapid Identification of Nucleotide Edits", style="=")


def get_broken_up_contigs(contigs, num_per_sublist):
    broken_up_contigs = []
                
    i_options = range((math.ceil(len(contigs)/num_per_sublist)) + 1)
    
    for i in i_options:
        contig_sublist = []
        j_options = range(i*num_per_sublist, (i*num_per_sublist) + num_per_sublist)
        
        for j in j_options:
            if j < len(contigs):
                contig_sublist.append(contigs[j])

        if len(contig_sublist) > 0:
            broken_up_contigs.append(contig_sublist)
    return broken_up_contigs

def split_bed_file(input_bed_file, output_folder, bam_filepaths, output_suffix=''):
    """
    Split a BED file into multiple files based on suffixes in the first column.
    Each line is assigned to the appropriate file based on the suffix.

    e.g.:
    
    10_AAACGAAAGTCACACT-1   6143263         6143264
    10_AAACGAAAGTCACACT-1   11912575        11912576
    10_AAACGAAAGTCACACT-1   12209751        12209752
    10_AAACGAAAGTCACACT-1   13320235        13320236
    10_AAACGAAAGTCACACT-1   27036085        27036086

    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    single_cell_approach = len(bam_filepaths) > 0
    
    suffix_pairs = [
        (os.path.basename(bam).split("_")[0], 
         os.path.basename(bam).split("_")[1].split(".")[0]) for bam in bam_filepaths
    ]
        
    # Open file handles for each suffix
    file_handles = {}
    for prefix, suffix in suffix_pairs:
        output_file = os.path.join(output_folder, f"combined_{output_suffix}_{prefix}_{suffix}.bed")
        file_handles[prefix + suffix] = open(output_file, 'w')

    try:
        with open(input_bed_file, 'r') as infile:
            for line in infile:
                # Parse the first column to determine the suffix
                columns = line.split()
                
                chrom = columns[0]  # Assuming the first column is the chromosome
                for prefix, suffix in suffix_pairs:
                    if chrom.startswith(f"{prefix}_") and chrom.endswith(suffix):
                        file_handles[prefix + suffix].write(line)
                        break

    finally:
        # Close all file handles
        for handle in file_handles.values():
            handle.close()
            

def generate_depths(output_folder, bam_filepaths, paired_end=False, barcode_tag=None):
    
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
        samtools_depth_command = f"samtools depth {paired_end_flag}-a -b {output_folder}/combined_source_cells.bed {bam_filepath} > {output_folder}/depths_source_cells.txt"
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
        

def convert_sites_to_sailor(final_site_level_information_df, sailor_list, output_folder, skip_coverage):
    # Output SAILOR-formatted file for use in FLARE downstream
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # 1       629275  629276  0.966040688     2,30    +
    # 1       629309  629310  2.8306e-05      1,1043  +
    
    for conversion in sailor_list:
        conversion_search = conversion[0] + '>' + conversion[1]
        
        print("Generating SAILOR-style bed outputs for conversion {}...".format(conversion))
        
        sailor_sites,weird_sites = get_sailor_sites(final_site_level_information_df, conversion_search, skip_coverage=skip_coverage)
        sailor_sites = sailor_sites.drop_duplicates()
    
        print("{} final deduplicated {} SAILOR-formatted sites".format(len(sailor_sites), conversion_search))
        sailor_sites.to_csv('{}/sailor_style_sites_{}.bed'.format(
            output_folder, 
            conversion_search.replace(">", "-")), 
            header=False,
            index=False,       
            sep='\t')


def generate_bedgraphs(final_site_level_information_df, conversion_search, output_folder):
    bedgraph_folder = '{}/bedgraphs'.format(output_folder)
    make_folder(bedgraph_folder)
    
    pretty_print("Making bedgraphs for {} conversions...\n".format(bedgraphs_list))
    for conversion in bedgraphs_list:
        conversion_search = conversion[0] + '>' + conversion[1]
        sites_for_conversion = final_site_level_information_df[final_site_level_information_df.conversion == conversion_search]
        sites_for_conversion['edit_fraction'] = sites_for_conversion['count']/sites_for_conversion['coverage']
        sites_for_conversion['start'] = sites_for_conversion['position'] - 1
        sites_for_conversion_bedgraph_cols = sites_for_conversion[['contig', 'start', 'position', 'edit_fraction']]
    
        sites_for_conversion_bedgraph_cols.to_csv('{}/{}_{}.bedgraph'.format(bedgraph_folder, output_folder.split('/')[-1], conversion), sep='\t', index=False, header=False)


def prepare_combinations_for_split(df, bam_filepaths, output_folder, output_suffix):
    """
    Prepares the chromosome-suffix combinations for multiprocessing.
    For each edited position in a given barcode, we want to look at the coverage at that
    position for that chromosome across all the other barcodes. 
    
    Args:
        df (pd.DataFrame): Filtered DataFrame containing edit data.
        bam_filepaths (list): List of BAM filepaths to extract suffix pairs.
        output_folder (str): Path to the output folder for split BED files.
        output_suffix (str): Suffix for output files.

    Returns:
        list: List of tuples for processing.
    """
    # Extract prefix and suffix from BAM filenames
    suffix_pairs = [
        (os.path.basename(bam).split("_")[0], os.path.basename(bam).split("_")[1].split(".")[0])
        for bam in bam_filepaths
    ]
    print(f"suffix_pairs is {suffix_pairs}")
    
    # Unique chromosomes in the dataset
    unique_chromosomes = df['contig'].unique()

    # Prepare combinations of chromosomes and suffix pairs
    combinations = []
    for chrom in unique_chromosomes:
        print(f"\tChecking {chrom}...")

        chrom = str(chrom)
        df['contig'] = df['contig'].astype(str)
        df_for_chrom = df[df['contig'] == chrom]
        unique_positions = df_for_chrom.position.unique()
        
        for prefix, suffix in suffix_pairs:
            
            if prefix == chrom:
                print(f"\t\tGenerating for ({prefix},{suffix})")                
                df_for_prefix_suffix =  df_for_chrom[df_for_chrom['barcode'].str.endswith(suffix)]
                unique_barcodes = df_for_prefix_suffix.barcode.unique()
                
                combinations.append((chrom, prefix, suffix, unique_positions, unique_barcodes, output_folder, output_suffix))
    
                print(f"\t\t\t{prefix}_{suffix}: Unique positions: {len(unique_positions)}, Unique barcodes: {len(unique_barcodes)}")
            
    return combinations

def process_combination_for_split(args):
    """
    Processes a single combination of chromosome, prefix, suffix, positions, and barcodes 
    to write split BED files.

    Args:
        args (tuple): Contains chromosome, prefix, suffix, positions, barcodes, 
                      output folder, and output suffix.
    """
    chrom, prefix, suffix, unique_positions, unique_barcodes, output_folder, output_suffix = args

    # Output file path
    output_file = os.path.join(output_folder, f"combined_{output_suffix}_{prefix}_{suffix}.bed")

    # Write combinations directly to the file
    with open(output_file, "w") as f:
        for position in unique_positions:
            for barcode in unique_barcodes:
                contig = f"{chrom}_{barcode}"  # Construct contig using chromosome and barcode
                f.write(f"{contig}\t{position-1}\t{position}\n")

    print(f"\t\t\t>>> Processed {chrom}, {prefix}_{suffix} -> {output_file}")


def generate_and_split_bed_files_for_all_edits(output_folder, bam_filepaths, tabulation_bed=None, processes=4, output_suffix="all_cells"):
    """
    Generates combined BED files for all edit sites and splits them into suffix-specific files.

    Args:
        output_folder (str): Path to the output folder.
        bam_filepaths (list): List of BAM filepaths for suffix extraction.
        strand_conversion (str): Strand conversion type (e.g., 'A>G').
        processes (int): Number of multiprocessing workers.
        output_suffix (str): Suffix for output files.
    """
    input_file = f"{output_folder}/final_filtered_site_info.tsv"
    df = pd.read_csv(input_file, sep="\t")
    print(f"\n{len(df)} positions in {input_file}...")
    
    # Filter by tabulation bed-specified positions
    if tabulation_bed:
        df['contig_position'] = df['contig'].astype(str) + '_' + df['position'].astype(str)
        tabulation_bed_df = pd.read_csv(tabulation_bed, sep='\t', names=['chrom', 'start', 'end'])
        tabulation_bed_df['contig_position'] = tabulation_bed_df['chrom'].astype(str) + '_' + tabulation_bed_df['start'].astype(str)
        print(f"\t{len(tabulation_bed_df)} unique positions in {tabulation_bed}...")
        print(tabulation_bed_df.head())
        
        df = df[df['contig_position'].isin(set(tabulation_bed_df.contig_position))]
        print(f"\tRunning {len(df)} positions through all-cell coverage tabulation...")

    # Prepare combinations for multiprocessing
    split_bed_folder = f"{output_folder}/combined_{output_suffix}_split_by_suffix"
    os.makedirs(split_bed_folder, exist_ok=True)
    
    # Cleanup existing .bed files in the output folder
    existing_bed_files = glob(os.path.join(split_bed_folder, "*.bed"))
    if existing_bed_files:
        print(f"\t\tFound {len(existing_bed_files)} existing .bed files. Removing...")
        for file in existing_bed_files:
            os.remove(file)
    print("Existing .bed files removed. Starting fresh.")
    
    combinations = prepare_combinations_for_split(df, bam_filepaths, f"{output_folder}/combined_{output_suffix}_split_by_suffix", output_suffix)

    # Run the processing with multiprocessing
    with Pool(processes=processes) as pool:
        pool.map(process_combination_for_split, combinations)

    print(f"All split BED files generated in {output_folder}/combined_{output_suffix}_split_by_suffix")


    
def run(bam_filepath, annotation_bedfile_path, output_folder, contigs=[], strandedness=True, barcode_tag="CB", paired_end=False, barcode_whitelist_file=None, verbose=False, coverage_only=False, filtering_only=False, annotation_only=False, bedgraphs_list=[], sailor_list=[], min_base_quality = 15, min_read_quality = 0, min_dist_from_end = 10, max_edits_per_read = None, cores = 64, number_of_expected_bams=4, 
        keep_intermediate_files=False,
        num_per_sublist=6,
        skip_coverage=False, interval_length=2000000,
        all_cells_coverage=False, tabulation_bed=None
       ):
        
    # Check to make sure the folder is empty, otherwise prompt for overwriting
    if any(os.scandir(output_folder)):
        pretty_print("WARNING: {} is not empty".format(output_folder), style="^")
    
    logging_folder = "{}/metadata".format(output_folder)

    with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
        f.write('bam_filepath\t{}\n'.format(bam_filepath)) 
        f.write('annotation_bedfile_path\t{}\n'.format(annotation_bedfile_path))
        f.write('output_folder\t{}\n'.format(output_folder))  
        f.write('strandedness\t{}\n'.format(strandedness))  
        f.write('barcode_tag\t{}\n'.format(barcode_tag))  
        f.write('barcode_whitelist_file\t{}\n'.format(barcode_whitelist_file))  
        f.write('contigs\t{}\n'.format(contigs))  
        f.write('interval_length\t{}\n'.format(interval_length))  
        f.write('verbose\t{}\n'.format(verbose))
        f.write('cores\t{}\n'.format(cores))
        f.write('number_of_expected_bams\t{}\n'.format(number_of_expected_bams))
        f.write('paired_end\t{}\n'.format(paired_end))
        f.write('min_base_quality\t{}\n'.format(min_base_quality))
        f.write('min_read_quality\t{}\n'.format(min_read_quality))
        f.write('min_dist_from_end\t{}\n'.format(min_dist_from_end))
        f.write('skip_coverage\t{}\n'.format(skip_coverage))

    
    # Check if filtering step finished
    final_filtered_sites_path = '{}/final_filtered_site_info.tsv'.format(output_folder)
    final_path_already_exists = False
    final_annotated_path_already_exists = False

    if os.path.exists(final_filtered_sites_path):
        print("{} exists... skipping edit finding.".format(final_filtered_sites_path))
        final_path_already_exists = True

    # Edit finding
    if not (coverage_only or filtering_only) and not final_path_already_exists:
        overall_total_reads_processed = 0
        if barcode_whitelist_file:
            barcode_whitelist = read_barcode_whitelist_file(barcode_whitelist_file)
        else:
            barcode_whitelist = None

        # Edit identification
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        pretty_print("Identifying edits", style="~")
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

                
                total_bam_generation_time, total_seconds_for_bams_df = bam_processing(overall_label_to_list_of_contents, output_folder, barcode_tag=barcode_tag, cores=cores, number_of_expected_bams=number_of_expected_bams, verbose=verbose)
                #total_seconds_for_bams_df.to_csv("{}/bam_reconfiguration_timing.tsv".format(logging_folder), sep='\t')
                pretty_print("Total time to concat and write bams: {} minutes".format(round(total_bam_generation_time/60, 3)))

            print("Deleting overall_label_to_list_of_contents...")
            del overall_label_to_list_of_contents

        
        with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
            f.write(f'total_reads_processed\t{overall_total_reads_processed}\n') 
            for k, v in overall_counts_summary_df.items():
                f.write(f'{k}\t{v}\n') 
            total_edits = overall_counts_summary_df.get("total_edits", 0)
            if total_edits > 0:
                f.write(f'edits per read (EPR)\t{total_edits/overall_total_reads_processed}\n')
            else:
                f.write(f'edits per read (EPR)\t{0}\n')

    reconfigured_bam_filepaths = glob('{}/split_bams/*/*.bam'.format(output_folder))
        
    if not final_path_already_exists and not skip_coverage:
        # Coverage calculation
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        pretty_print("Calculating coverage at edited sites, minimum read quality is {}...".format(min_read_quality), style='~')
        
        # We want to run the samtools depth command for each of the reconfigured bam files
        print("Running samtools depth on {} subset bam paths...".format(len(reconfigured_bam_filepaths)))
        total_time, total_seconds_for_contig_df = generate_depths(output_folder, reconfigured_bam_filepaths, paired_end=paired_end, barcode_tag=barcode_tag)
                                              
        total_seconds_for_contig_df.to_csv("{}/coverage_calculation_timing.tsv".format(logging_folder), sep='\t')
         
        pretty_print("Total time to calculate coverage: {} minutes".format(round(total_time/60, 3)))
    
        all_edit_info_unique_position_with_coverage_df = get_edits_with_coverage_df(output_folder,
                                                                                    barcode_tag=barcode_tag)
        
        pretty_print("\tNumber of edits after filtering:\n\t{}".format(len(all_edit_info_unique_position_with_coverage_df)))
    
        all_edit_info_filtered_pl = pl.from_pandas(all_edit_info_unique_position_with_coverage_df)

        final_site_level_information_df = generate_site_level_information(all_edit_info_filtered_pl, skip_coverage=skip_coverage)
        pretty_print("\tNumber of unique edit sites:\n\t{}".format(len(final_site_level_information_df)))
        pretty_print("Writing sites...\n")
        
        # Edge case when no edits are found.
        if len(final_site_level_information_df) == 0:
            output_zero_edit_files = zero_edit_found(final_site_level_information_df, output_folder, sailor_list, bedgraphs_list, keep_intermediate_files, start_time, logging_folder)
            return 'Done!'
        
        final_site_level_information_df.write_csv('{}/final_filtered_site_info.tsv'.format(output_folder), 
                                                  separator='\t')
       
            
        pretty_print("Adding strand-specific conversion...\n")
        final_site_level_information_df = pd.read_csv('{}/final_filtered_site_info.tsv'.format(output_folder), 
                                                  sep='\t')
        final_site_level_information_df['strand_conversion'] = final_site_level_information_df.apply(get_strand_specific_conversion, args=(strandedness,), axis=1)
        final_site_level_information_df.to_csv('{}/final_filtered_site_info.tsv'.format(output_folder), 
                                                  sep='\t', index=False)
        final_path_already_exists = True

        
        if len(sailor_list) > 0:
            print("{} sites being converted to SAILOR format...".format(len(final_site_level_information_df)))
            convert_sites_to_sailor(final_site_level_information_df, sailor_list, output_folder, skip_coverage)
           
        if len(bedgraphs_list) > 0:
            # Make plot of edit distributions
            generate_bedgraphs(final_site_level_information_df, bedgraphs_list, output_folder)
                
    if not annotation_bedfile_path:
        print("annotation_bedfile_path argument not provided ...\
        not annotating with feature information and strand-specific conversions.")
        
    if final_path_already_exists:
        # Edge case when no edits are found.
        final_site_level_information_df = pd.read_csv('{}/final_filtered_site_info.tsv'.format(output_folder), 
                                                  sep='\t')
        if len(final_site_level_information_df) == 0:
            output_zero_edit_files = zero_edit_found(final_site_level_information_df, output_folder, sailor_list, bedgraphs_list, keep_intermediate_files, start_time, logging_folder)
            return 'Done!'

    # Annotation option
    if final_path_already_exists and annotation_bedfile_path:
        final_site_level_information_df = pd.read_csv('{}/final_filtered_site_info.tsv'.format(output_folder), 
                                                  sep='\t')
        final_site_level_information_annotated_df = annotate_sites(final_site_level_information_df,
                                                                   annotation_bedfile_path)
        final_site_level_information_annotated_df.to_csv('{}/final_filtered_site_info_annotated.tsv'.format(output_folder), 
                                                  sep='\t', index=False)
        final_annotated_path_already_exists = True

    # Make plot of edit distributions
    if final_path_already_exists:
        final_site_level_information_df = pd.read_csv('{}/final_filtered_site_info.tsv'.format(output_folder), 
                                                  sep='\t')
        
        plot_folder = '{}/plots'.format(output_folder)
        make_folder(plot_folder)
        
        final_site_level_information_df.groupby('strand_conversion').count()['count'].plot(kind='barh')
        plt.title("Edit Distribution for {}".format(output_folder.split("/")[-1]))
        plt.savefig("{}/conversion_distribution.png".format(plot_folder))
        
        
    # Check memory usage
    current, peak = tracemalloc.get_traced_memory()

    logging_folder = "{}/metadata".format(output_folder)
    with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
        f.write(f'sites\t{len(final_site_level_information_df)}\n') 
        f.write(f'peak_memory_mb\t{peak/1e6}\n') 
        f.write(f'time_elapsed_seconds\t{time.time()-start_time:.2f}s\n') 

    print(f"Current memory usage {current/1e6}MB; Peak: {peak/1e6}MB")
    print(f'Time elapsed: {time.time()-start_time:.2f}s')

    if final_path_already_exists and all_cells_coverage:
        output_suffix = "all_cells"
        print("Calculating coverage at all edit sites in all cells...")
    
        # Get the list of BAM file paths
        bam_filepaths = glob(f"{output_folder}/split_bams/*/*.bam")
    
        # Generate and split BED files using multiprocessing
        generate_and_split_bed_files_for_all_edits(output_folder,
                                                   bam_filepaths, 
                                                   tabulation_bed=tabulation_bed,
                                                   processes=cores, 
                                                   output_suffix=output_suffix)

        make_depth_command_script_single_cell(
            paired_end,
            reconfigured_bam_filepaths, 
            output_folder, 
            output_suffix=output_suffix,
            run=True,
            pivot=True,
            processes=cores,
            barcode_tag=barcode_tag
        )
        
    if not keep_intermediate_files:
        pretty_print("Deleting intermediate files...", style="-")
        delete_intermediate_files(output_folder)

    pretty_print("Done!", style="+")

def check_samtools():
    try:
        # Run 'samtools --version' to check if samtools is available
        subprocess.run(["samtools", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Samtools is available.")
    except subprocess.CalledProcessError:
        print("Samtools is installed but encountered an issue running.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Samtools is not installed or not found in PATH.")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run MARINE')
            
    parser.add_argument('--bam_filepath', type=str, default=None, help="Full path to MD-tagged and indexed .bam file")
    parser.add_argument('--annotation_bedfile_path', type=str, default=None, help="Full path to bed file with desired annotations in bed6 format (contig start end label1 label2 strand)")

    parser.add_argument('--output_folder', type=str, default=None, help="Directory in which all results will be generated, will be created if it does not exist")
    
    parser.add_argument('--barcode_whitelist_file', type=str, default=None, help="List of cell barcodes to use for single-cell analysis")
    
    parser.add_argument('--cores', type=int, default=multiprocessing.cpu_count(), help="Number of CPUs to use for analysis. Will default to using all cores available if not specified")
    
    parser.add_argument('--strandedness', type=int, choices=[0, 1, 2],
                        help='Possible values include: 0 (unstranded), 1 (stranded) and 2 (reversely stranded).')

    parser.add_argument('--coverage', dest='coverage_only', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--filtering', dest='filtering_only', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--annotation', dest='annotation_only', action='store_true', help=argparse.SUPPRESS)

    parser.add_argument('--barcode_tag', type=str, default=None, help='CB for typical 10X experiment. For long-read and single-cell long read analyses, manually add an IS tag for isoform or an IB tag for barcode+isoform information. Do not provide any arguments when processing bulk seqencing')
    
    parser.add_argument('--min_dist_from_end', type=int, default=0, help='Minimum distance from the end of a read an edit has to be in order to be counted'),

    parser.add_argument('--min_base_quality', type=int, default=0, help='Minimum base quality, default is 0')
    parser.add_argument('--contigs', type=str, default='all', help="Which contigs to process, in comma separated list (ie 1,2,3 or chr1,chr2,chr3, whichever matches your nomenclature)")
    parser.add_argument('--min_read_quality', type=int, default=0, help='Minimum read quality, default is 0... every aligner assigns mapq scores differently, so double-check the range of qualities in your sample before setting this filter')
    
    parser.add_argument('--sailor', type=str, nargs='?', const='CT', default=None, dest='sailor', help="Generate SAILOR-style outputs.")
    
    parser.add_argument('--bedgraphs', type=str, nargs='?', const='CT', default=None, help='Conversions for which to output a bedgraph for non-single cell runs, (e.g. CT,AI)')
    parser.add_argument('--verbose', dest='verbose', action='store_true')
    parser.add_argument('--keep_intermediate_files', dest='keep_intermediate_files', action='store_true', help="Keep intermediate files for debugging or to use --all_cells_coverage flag")
    parser.add_argument('--num_per_sublist', dest='num_per_sublist', type=int, default=6, help="For single-cell datasets, specifies 'chunking', ie how many contigs to process at once. This can be lowered to enable lower-memory runs, with the tradeoff of longer runtime")
    parser.add_argument('--paired_end', dest='paired_end', action='store_true', help='Assess coverage taking without double-counting paired end overlapping regions... slower but more accurate. Edits by default are only counted once for an entire pair, whether they show up on both ends or not.')
    parser.add_argument('--skip_coverage', dest='skip_coverage', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--all_cells_coverage', dest='all_cells_coverage', action='store_true', help='Requires --keep_intermediate_files flag to be set. Caution: this can take a long time if too many sites are used (think thousands of sites x thousands of cells... it gets big quickly), it is worth reducing the number of sites to tabulate through filtering beforehand, and using the additional argument --tabulation_bed to specify these sites.')
    parser.add_argument('--tabulation_bed', dest='tabulation_bed', type=str, default=None, help='Locations to run tabulation across all cells. The fist column should be contig, the second should match the position in the final_filtered_sites_info.tsv file.')

    parser.add_argument('--max_edits_per_read', type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument('--num_intervals_per_contig', type=int, default=200, help=argparse.SUPPRESS) # deprecated
    parser.add_argument('--interval_length', type=int, default=32000000, help='Length of intervals to split analysis into... you probably don\'t have to change this.')
    
    args = parser.parse_args()
    bam_filepath = args.bam_filepath
    annotation_bedfile_path = args.annotation_bedfile_path
    output_folder = args.output_folder
    barcode_whitelist_file = args.barcode_whitelist_file
    cores = args.cores
    strandedness = args.strandedness
    contigs = args.contigs
    annotation_bedfile_path = args.annotation_bedfile_path
    
    coverage_only = args.coverage_only
    filtering_only = args.filtering_only
    annotation_only= args.annotation_only

    bedgraphs = args.bedgraphs
    sailor = args.sailor
    verbose = args.verbose
    keep_intermediate_files = args.keep_intermediate_files
    paired_end = args.paired_end
    all_cells_coverage = args.all_cells_coverage
    tabulation_bed = args.tabulation_bed
    skip_coverage = args.skip_coverage

    barcode_tag = args.barcode_tag
    min_base_quality = args.min_base_quality
    min_read_quality = args.min_read_quality
    min_dist_from_end = args.min_dist_from_end
    max_edits_per_read = args.max_edits_per_read
    
    num_intervals_per_contig = args.num_intervals_per_contig
    interval_length = args.interval_length
    num_per_sublist = args.num_per_sublist


    # all_cells_coverage only applies for single cell case
    if not barcode_tag:
        if all_cells_coverage == True:
            all_cells_coverage = False

    if all_cells_coverage:
        print("\n\nWill tabulate coverage across all cells... WARNING this can be extremely resource-consuming if there are a lot of cells and a lot of sites. Consider first filtering sites and then using the --tabulation_bed argument to specify the specific locations you would like tabulated across all cells.\n\n")
        if tabulation_bed:
            if os.path.exists(tabulation_bed):
                print("\t...using sites in {}".format(tabulation_bed))
            else:
                print("{} does not exist! Exiting.".format(tabulation_bed))
                sys.exit(1)
                
    # Convert bedgraphs argument into list of conversions
    if not bedgraphs is None:
        if barcode_tag in ['CB', 'IB']:
            sys.stderr.write("Can only output bedgraphs for bulk sequencing runs of MARINE")
            sys.exit(1)
            
        bedgraphs_list = bedgraphs.upper().replace('I', 'G').split(',')
        for b in bedgraphs_list:
            assert(b in ['AC', 'AG', 'AT', 'CA', 'CG', 'CT', 'GA', 'GC', 'GT', 'TA', 'TC', 'TG'])
    else:
        bedgraphs_list = []

    if not sailor is None:
        if barcode_tag in ['CB', 'IB']:
            sys.stderr.write("Can only output sailor for bulk sequencing runs of MARINE")
            sys.exit(1)
            
        sailor_list = sailor.upper().replace('I', 'G').split(',')
        for s in sailor_list:
            assert(s in ['AC', 'AG', 'AT', 'CA', 'CG', 'CT', 'GA', 'GC', 'GT', 'TA', 'TC', 'TG'])
    else:
        sailor_list = []
        
    assert(strandedness in [0, 1, 2])

    if not os.path.exists(output_folder):
        pretty_print("{} (output folder) does not exist, making folder...".format(output_folder))
        os.mkdir(output_folder)

    
    # Get the exact command line used to run this script
    command_line = " ".join(shlex.quote(arg) for arg in sys.argv)
    print('command: {}'.format(command_line))
    # Define the path to your manifest file
    manifest_file = "manifest.txt"
    # Save the command to the manifest file
    logging_folder = "{}/metadata".format(output_folder)
    make_folder(logging_folder)
    with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
        f.write(f"command {command_line}\n")


    if cores is None:
        cores = 16
    pretty_print("Assuming {} cores available for multiprocessing. Set this to the number of available cores for optimal execution.".format(cores))
   
    
    assert(not(coverage_only and filtering_only))

    print_marine_logo()

    pretty_print(["Arguments:",
                  "\tBAM filepath:\t{}".format(bam_filepath), 
                  "\tAnnotation bedfile filepath:\t{}".format(annotation_bedfile_path),
                  "\tOutput folder:\t{}".format(output_folder),
                  "\tBarcode whitelist:\t{}".format(barcode_whitelist_file),
                  "\tStrandedness:\t{}".format(strandedness),
                  "\tBarcode Tag:\t{}".format(barcode_tag),
                  "\tPaired End:\t{}".format(paired_end),
                  "\tCoverage only:\t{}".format(coverage_only),
                  "\tFiltering only:\t{}".format(filtering_only),
                  "\tAnnotation only:\t{}".format(annotation_only),
                  "\tSailor outputs:\t{}".format(sailor_list),
                  "\tBedgraphs:\t{}".format(bedgraphs_list),
                  "\tMinimum base quality:\t{}".format(min_base_quality),
                  "\tMinimum read quality:\t{}".format(min_read_quality),
                  "\tMinimum distance from end:\t{}".format(min_dist_from_end),
                  "\tMaximum edits per read:\t{}".format(max_edits_per_read),
                  "\tContigs:\t{}".format(contigs),
                  "\tInterval length:\t{}".format(interval_length),
                  "\tCores:\t{}".format(cores),
                  "\tVerbose:\t{}".format(verbose),
                  "\tKeep intermediate files:\t{}".format(keep_intermediate_files),
                  "\tSkip coverage?:\t{}".format(skip_coverage),
                  "\tFor single-cell: \t{} contigs at at time\n".format(num_per_sublist),
                  "\tCalculate coverage in all barcodes?: \t{}\n".format(all_cells_coverage),
                  "\tTabulation bed for coverage calculation?: \t{}\n".format(tabulation_bed)
                 ])

    if not paired_end:
        # Check to see that samtools is available in the environment
        check_samtools()

    # Whether to only run for certain contigs 
    if contigs == 'all':
        contigs = []
    else:
        contigs = contigs.split(",")

    start_time = time.time()
    tracemalloc.start()
    
    run(bam_filepath, 
        annotation_bedfile_path,
        output_folder, 
        contigs=contigs,
        strandedness=strandedness,
        barcode_tag=barcode_tag,
        paired_end=paired_end,
        barcode_whitelist_file=barcode_whitelist_file,
        coverage_only=coverage_only,
        filtering_only=filtering_only,
        annotation_only=annotation_only,
        sailor_list=sailor_list,
        bedgraphs_list=bedgraphs_list,
        min_base_quality = min_base_quality, 
        min_read_quality = min_read_quality,
        min_dist_from_end = min_dist_from_end,
        max_edits_per_read = max_edits_per_read,
        cores = cores,
        verbose = verbose,
        skip_coverage=skip_coverage,
        keep_intermediate_files=keep_intermediate_files,
        num_per_sublist=num_per_sublist,
        interval_length=interval_length,
        all_cells_coverage=all_cells_coverage,
        tabulation_bed=tabulation_bed
       )
    
    
