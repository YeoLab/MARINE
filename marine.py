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
import os


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src/'))

from utils import make_folder, pretty_print, make_depth_command_script_single_cell, \
concatenate_files, get_edits_with_coverage_df, zero_edit_found, delete_intermediate_files, \
pivot_edits_to_sparse, print_marine_logo, convert_sites_to_sailor, convert_conversions_argument, \
generate_bedgraphs, check_folder_is_empty_warn_if_not, print_all_cells_coverage_warning, remove_file_if_exists

from core import run_edit_identifier, run_bam_reconfiguration, run_edit_finding, \
gather_edit_information_across_subcontigs, run_coverage_calculator, generate_site_level_information, \
generate_depths

from annotate import annotate_sites, get_strand_specific_conversion 


def get_unique_barcodes(bam_path):
    """Extract unique cell barcodes from a BAM file using samtools and awk.

    Args:
        bam_path: Path to the BAM file to extract CB tags from.

    Returns:
        list: Sorted list of unique barcode strings found in the BAM file.

    Raises:
        RuntimeError: When the samtools/awk command returns a non-zero exit code.
    """
    # Use samtools to extract CB tags and get unique barcodes
    command = (
        f"samtools view {bam_path} | "  # View the BAM file
        f"awk '{{for (i=12; i<=NF; i++) if ($i ~ /^CB:Z:/) print substr($i, 6)}}' | "  # Extract CB tags
        f"sort | uniq"  # Sort and get unique barcodes
    )
    print(f"\t\t\t\tCommand:\n\t\t\t\t{command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Error extracting barcodes: {result.stderr.strip()}")
    
    # Split the output into a list of barcodes
    barcodes = result.stdout.strip().split("\n") if result.stdout.strip() else []
    return barcodes


def get_unique_barcodes_for_reads_in_bamfile(args):
    """Worker function for Pool.map; unpacks a 7-tuple and returns unique barcodes for a BAM/chromosome.

    Args:
        args: 7-tuple of (chrom, prefix, suffix, bam_filepath, unique_positions,
            output_folder, output_suffix).

    Returns:
        list: Sorted list of unique barcode strings found in bam_filepath.
    """
    chrom, prefix, suffix, bam_filepath, unique_positions, output_folder, output_suffix = args
    
    print(f"\t\tProcessing BAM for ({prefix}, {suffix}) on chromosome {chrom}")
    unique_barcodes = get_unique_barcodes(bam_filepath)
    print(f"\t\t\t{prefix}_{suffix}: Unique positions: {len(unique_positions)}, Unique barcodes: {len(unique_barcodes)}")
    
    return unique_barcodes


def get_suffix_pairs_from_bam_filepath(bam_filepaths):
    """
    Retrieve, given bam filepaths 9_A-1.bam, 9_G-1.bam, etc., a list of tuples representing prefix and suffix for each 
    bam, and a dictionary mapping each tuple to the corresponding file, e.g.:
        * [(9, A-1), (9, G-1)], {'9_A-1': 'path/t/9_A-1.bam', '9_G-1': 'path/to/9_G-1.bam'}

    Args:
        bam_filepaths (list): List of BAM filepaths to extract suffix pairs.
    """
    suffix_pairs = []
    suffix_pair_to_bam_filepath = {}

    for bam in bam_filepaths:
        contig_prefix = os.path.basename(bam).split("_")[0]
        barcode_suffix = os.path.basename(bam).split("_")[1].split(".")[0]
        
        suffix_pairs.append((contig_prefix, barcode_suffix))
        suffix_pair_to_bam_filepath[f'{contig_prefix}_{barcode_suffix}'] = bam
        
    return suffix_pairs, suffix_pair_to_bam_filepath


def prepare_combinations_for_split(df, bam_filepaths, output_folder, output_suffix, processes=4):
    """
    Prepares the chromosome-suffix combinations for multiprocessing.
    For each position in a given barcode, we want to look at the coverage at that
    position for that chromosome in reads across all other barcodes. 
    
    Args:
        df (pd.DataFrame): Filtered DataFrame containing edit data.
        bam_filepaths (list): List of processed BAM files to incorporate
        output_folder (str): Path to the output folder for split BED files.
        output_suffix (str): Suffix for output files.
        processes (int): Number of processes for multiprocessing.

    Returns:
        list: List of tuples for processing.
    """

    # Extract prefix and suffix from BAM filenames
    suffix_pairs, suffix_pair_to_bam_filepath = get_suffix_pairs_from_bam_filepath(bam_filepaths)
    print(f"suffix_pairs is {suffix_pairs}")
    
    # Prepare arguments for multiprocessing
    barcode_finding_tasks = []
    overall_barcodes_list = set()
    overall_positions_list = set()

    # For each unique chromosomes in the dataset... i.e. 9. 
    for chrom in  df['contig'].unique():
        print(f"\tChecking {chrom}...")

        chrom = str(chrom)
        df['contig'] = df['contig'].astype(str)
        df_for_chrom = df[df['contig'] == chrom]
        # Get the positions only found in that chromosome and add them to our overall position list
        unique_positions = df_for_chrom.position.unique()
        overall_positions_list.update([f'{chrom}:{p}' for p in unique_positions])

        chrom_filtered_suffix_pairs = [(prefix, suffix) for prefix, suffix in suffix_pairs if prefix == chrom]
        for prefix, suffix in chrom_filtered_suffix_pairs:
            # For all the bam files belonging to this chromosome, e.g. 9_A-1, or 9_G-1:
            bam_filepath = suffix_pair_to_bam_filepath.get(f'{prefix}_{suffix}')
            barcode_finding_tasks.append([chrom, prefix, suffix, bam_filepath, unique_positions, output_folder, output_suffix])

    # Get unique barcodes contained in each bam, using a multiprocessing pool for maximal core usage efficiency
    print(f"Starting multiprocessing to figure out unique barcodes per bam, with {processes} processes...")
    with Pool(processes) as pool:
        list_of_unique_barcodes_per_bam = pool.map(get_unique_barcodes_for_reads_in_bamfile, barcode_finding_tasks)

    # Make new task list for next step
    new_tasks = []
    # Aggregate results -- change tasks list to have unique barcodes rather than bam filepath
    for unique_barcodes, task in zip(list_of_unique_barcodes_per_bam, barcode_finding_tasks):        
        overall_barcodes_list = overall_barcodes_list.union(set(unique_barcodes))  
        # Originally the 4th elementin the task tuple was the bam filepath, but now that we have all the information 
        # we need from it in the form of unique barcodes, we can simply use the list of unique barcodes here instead.
        task[3] = unique_barcodes
        new_tasks.append(task)

    print(f"\nFound {len(overall_barcodes_list)} unique barcodes and {len(overall_positions_list)} unique positions.\n")
    return new_tasks, sorted(overall_barcodes_list), sorted(overall_positions_list)


def process_combination_for_split(args):
    """Worker function for Pool.map; unpacks a 7-tuple and writes split BED files for one combination.

    Args:
        args: 7-tuple of (chrom, prefix, suffix, unique_barcodes, unique_positions,
            output_folder, output_suffix).
    """
    chrom, prefix, suffix, unique_barcodes, unique_positions, output_folder, output_suffix = args
    # Output file path
    output_file = os.path.join(output_folder, f"combined_{output_suffix}_{prefix}_{suffix}.bed")

    # Write combinations directly to the file
    with open(output_file, "w") as f:
        for position in unique_positions:
            for barcode in unique_barcodes:
                contig = f"{chrom}_{barcode}"  # Construct contig using chromosome and barcode
                f.write(f"{contig}\t{int(position)-1}\t{int(position)}\n")

    print(f"\t\t\t>>> Processed {chrom}, {prefix}_{suffix} -> {output_file}")
    

def filter_sites_using_tabulation_bed(df, tabulation_bed):
    """Filter edit positions to those overlapping a tabulation BED file.

    Args:
        df: DataFrame of final sites with 'contig' and 'position' columns.
        tabulation_bed: File path to BED file containing all sites where coverage
            calculation is desired.

    Returns:
        tuple: (tabulation_bed_df, tabulation_edits_df, unique_tabulation_bed_sites)
            where tabulation_bed_df is all sites in the BED file,
            tabulation_edits_df is BED sites that have at least one edit,
            and unique_tabulation_bed_sites is a deduplicated array of contig_position strings.
    """
    df['contig_position'] = df['contig'].astype(str) + '_' + df['position'].astype(str)
    
    tabulation_bed_df = pd.read_csv(tabulation_bed, sep='\t', names=['chrom', 'start', 'end'])
    tabulation_bed_df['contig'] = tabulation_bed_df['chrom']
    tabulation_bed_df['position'] = tabulation_bed_df['start'] # This should be the value matching edit sites
    tabulation_bed_df['contig_position'] = tabulation_bed_df['chrom'].astype(str) + '_' + tabulation_bed_df['position'].astype(str)

    unique_tabulation_bed_sites = tabulation_bed_df.contig_position.unique()
    print(f"\t{len(unique_tabulation_bed_sites)} unique positions in {tabulation_bed}...")
    print(f"\tExample rows:\n{tabulation_bed_df.head()}\n")

    positions_with_edits = set(df['contig_position'])
    positions_to_keep = positions_with_edits.intersection(unique_tabulation_bed_sites)
    
    print(f"\t{len(positions_to_keep)} out of {len(unique_tabulation_bed_sites)} specified positions were found to have edits.")

    tabulation_edits_df = df[df['contig_position'].isin(positions_to_keep)]
    
    return tabulation_bed_df, tabulation_edits_df, unique_tabulation_bed_sites


def generate_and_split_bed_files_for_all_positions(output_folder, bam_filepaths, tabulation_bed=None, processes=4, output_suffix="all_cells"):
    """Generate combined BED files for all edit sites and split them into suffix-specific files.

    Args:
        output_folder: Path to the output folder containing final_filtered_site_info.tsv.
        bam_filepaths: List of BAM filepaths used to extract suffix pairs.
        tabulation_bed: Optional BED file path to filter sites before splitting. Default None.
        processes: Number of multiprocessing workers. Default 4.
        output_suffix: Suffix used in output directory and file naming. Default "all_cells".
    """
    input_file = f"{output_folder}/final_filtered_site_info.tsv"
    df = pd.read_csv(input_file, sep="\t")
    print(f"\n{len(df)} positions in {input_file}...")
    print(f"Example rows in {input_file}:\n{df.head(5)}")

    
    pretty_print('Splitting bedfile locations to enable efficient coverage calculation at all positions...',
                 style='.')
    
    # Prepare combinations for multiprocessing
    split_bed_folder = f"{output_folder}/combined_{output_suffix}_split_by_suffix"
    os.makedirs(split_bed_folder, exist_ok=True)

    # Cleanup existing .bed files in the output folder
    existing_bed_files = glob(os.path.join(split_bed_folder, "*.bed"))
    if existing_bed_files:
        print(f"Found {len(existing_bed_files)} existing .bed files. Removing...")
        for file in existing_bed_files:
            remove_file_if_exists(file)
    print("Existing .bed files removed. Starting fresh.")

    # Filter by tabulation bed-specified positions
    if tabulation_bed:
        # Pivot dataframe of edits only at specified tabulation sites
        print("Pivoting tabulation-based edits dataframe into sparse h5ad files...")
        coverage_calc_sites_bed_df, edits_to_make_pivot_df, unique_tabulation_bed_sites = filter_sites_using_tabulation_bed(df, tabulation_bed)
    else:
        # Pivot dataframe of edits at all edit sites
        print("Pivoting all edits dataframe into sparse h5ad files...")
        edits_to_make_pivot_df = df
        coverage_calc_sites_bed_df = df

    print('edits_to_make_pivot_df', len(edits_to_make_pivot_df))
    
    # Calculate coverage in all cells only at the positions specified in tabulation bed
    combinations, overall_barcodes_list, overall_positions_list = prepare_combinations_for_split(
        coverage_calc_sites_bed_df, 
        bam_filepaths, 
        split_bed_folder, 
        output_suffix,
        processes=processes
    )

    print("Pivoting edits dataframe into sparse h5ad files...")
    pivot_edits_to_sparse(edits_to_make_pivot_df, output_folder, overall_barcodes_list, overall_positions_list)

    if tabulation_bed:
        try:
            assert sorted([i.replace('_', ':') for i in unique_tabulation_bed_sites]) == overall_positions_list
        except AssertionError as e:
            print(f"AssertionError: Overall positions derived for coverage calculation is not equal to tabulation sites: {e}.\n {len(unique_tabulation_bed_sites)} in tabulation bed, {len(overall_positions_list)} derived positions")
            raise  # Properly re-raise the exception
            
    # Run the processing with multiprocessing
    with Pool(processes) as pool:
        pool.map(process_combination_for_split, combinations)

    print(f"\nAll split BED files generated in {output_folder}/combined_{output_suffix}_split_by_suffix\n")
        
    
def run(bam_filepath, annotation_bedfile_path, output_folder, contigs=[], strandedness=True, barcode_tag="CB", paired_end=False, barcode_whitelist_file=None, verbose=False, coverage_only=False, filtering_only=False, annotation_only=False, bedgraphs_list=[], sailor_list=[], min_base_quality = 15, min_read_quality = 0, min_dist_from_end = 10, max_edits_per_read = None, cores = 64, number_of_expected_bams=4, 
        keep_intermediate_files=False,
        num_per_sublist=6,
        skip_coverage=False, interval_length=2000000,
        all_cells_coverage=False, tabulation_bed=None
       ):
    """Run the full MARINE RNA-editing detection pipeline from BAM to filtered edit sites.

    Orchestrates all pipeline stages: edit identification, BAM reconfiguration, coverage
    calculation, site-level annotation, BED/SAILOR/bedgraph output, and optional
    all-cells coverage pivot. Writes results to output_folder.

    Args:
        bam_filepath: Path to the input BAM file.
        annotation_bedfile_path: Path to the annotation BED file for strand information.
        output_folder: Directory where all output files will be written.
        contigs: List of contig names to process. Empty list processes all contigs.
        strandedness: Whether to apply strand-specific filtering. Default True.
        barcode_tag: SAM tag containing cell barcodes. Default "CB".
        paired_end: Whether reads are paired-end. Default False.
        barcode_whitelist_file: Path to barcode whitelist file. Default None.
        verbose: Enable verbose logging. Default False.
        coverage_only: Skip edit finding and only calculate coverage. Default False.
        filtering_only: Only apply filters to existing edit info. Default False.
        annotation_only: Only run annotation step. Default False.
        bedgraphs_list: List of strand conversions for bedgraph output. Default [].
        sailor_list: List of strand conversions for SAILOR output. Default [].
        min_base_quality: Minimum base quality score to consider an edit. Default 15.
        min_read_quality: Minimum read mapping quality. Default 0.
        min_dist_from_end: Minimum distance from read end to call an edit. Default 10.
        max_edits_per_read: Maximum allowed edits per read; None disables filter. Default None.
        cores: Number of CPU cores for multiprocessing. Default 64.
        number_of_expected_bams: Expected number of split BAMs per contig. Default 4.
        keep_intermediate_files: Retain intermediate files after completion. Default False.
        num_per_sublist: Number of contigs processed per sublist batch. Default 6.
        skip_coverage: Skip coverage calculation step. Default False.
        interval_length: Length of genomic intervals for parallelization. Default 2000000.
        all_cells_coverage: Calculate coverage across all cells. Default False.
        tabulation_bed: BED file specifying sites for tabulation coverage. Default None.
    """
    start_time = time.time()
    tracemalloc.start()

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

    # Edit identification
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    pretty_print("Identifying edits", style="~")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    if os.path.exists(final_filtered_sites_path):
        print("{} exists... skipping edit finding.".format(final_filtered_sites_path))
        final_path_already_exists = True
    else:
        if not (coverage_only or filtering_only):
            run_edit_finding(
                barcode_tag,
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
                verbose
            )
            
    reconfigured_bam_filepaths = glob('{}/split_bams/*/*.bam'.format(output_folder))
        
    if not final_path_already_exists and not skip_coverage:
        # Coverage calculation
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        pretty_print("Calculating coverage at edited sites, minimum read quality is {}...".format(min_read_quality), style='~')
        
        # We want to run the samtools depth command for each of the reconfigured bam files
        print("Running samtools depth on {} subset bam paths...".format(len(reconfigured_bam_filepaths)))
        total_time, total_seconds_for_contig_df = generate_depths(output_folder, 
                                                                  reconfigured_bam_filepaths,
                                                                  bam_filepath, # original bam_filepath for bulk case
                                                                  paired_end=paired_end, 
                                                                  barcode_tag=barcode_tag, 
                                                                  cores=cores)
                                              
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
        pretty_print("Annotating edits...", style="~")

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
        # Coverage across all cells
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        pretty_print("Generating sparse matrices for all positions across all cells...", style="~")
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        delete_intermediate_files(output_folder, contains='all_cells')
        
        output_suffix = "all_cells"
    
        # Get the list of BAM file paths
        bam_filepaths = glob(f"{output_folder}/split_bams/*/*.bam")
    
        # Generate and split BED files using multiprocessing
        generate_and_split_bed_files_for_all_positions(
            output_folder,
            bam_filepaths, 
            tabulation_bed=tabulation_bed,
            output_suffix=output_suffix,
            processes=cores
        )

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
    """Verify that samtools is installed and accessible on the system PATH.

    Exits the process with code 1 if samtools is missing or returns a non-zero
    exit code when invoked, so the caller does not need to handle a return value.

    Raises:
        SystemExit: When samtools is not found in PATH or returns a non-zero exit code.
    """
    try:
        # Run 'samtools --version' to check if samtools is available
        subprocess.run(["samtools", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    print_marine_logo()
    check_folder_is_empty_warn_if_not(output_folder)

    # all_cells_coverage only applies for single cell case
    if not barcode_tag:
        if all_cells_coverage == True:
            print("WARNING: --all_cells_coverage flag only applies for single cell case, ignoring...")
            all_cells_coverage = False

    print_all_cells_coverage_warning(all_cells_coverage, tabulation_bed)

    bedgraphs_list = convert_conversions_argument(bedgraphs, barcode_tag, file_type='bedgraph')
    sailor_list = convert_conversions_argument(sailor, barcode_tag, file_type='sailor')
    
    assert(strandedness in [0, 1, 2])

    if not os.path.exists(output_folder):
        pretty_print("{} (output folder) does not exist, making folder...".format(output_folder))
        os.mkdir(output_folder)

    # Get the exact command line used to run this script
    command_line = " ".join(shlex.quote(arg) for arg in sys.argv)
    print('\ncommand:\n\n{}\n'.format(command_line))
    # Define the path to your manifest file
    manifest_file = "manifest.txt"
    # Save the command to the manifest file
    logging_folder = "{}/metadata".format(output_folder)
    make_folder(logging_folder)
    with open('{}/manifest.txt'.format(logging_folder), 'a+') as f:
        f.write(f"command {command_line}\n")


    if cores is None:
        cores = 16
    pretty_print("\nAssuming {} cores available for multiprocessing. Set this to the number of available cores for optimal execution.\n".format(cores))
   
    
    assert(not(coverage_only and filtering_only))

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
    
    
