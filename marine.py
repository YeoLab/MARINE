import argparse
from multiprocessing import Pool
import multiprocessing
import numpy as np
import os
import pandas as pd
import polars as pl
import psutil
import pysam
import sys
from sys import getsizeof
import time
from tqdm import tqdm

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src'))

from read_process import incorporate_replaced_pos_info,incorporate_insertions_and_deletions,\
get_positions_from_md_tag,reverse_complement,get_edit_information,get_edit_information_wrapper,\
has_edits,get_total_coverage_for_contig_at_position,\
print_read_info, get_read_information, get_hamming_distance, \
remove_softclipped_bases,find

from utils import get_intervals, index_bam, write_rows_to_info_file, write_header_to_edit_info, \
write_read_to_bam_file, remove_file_if_exists, make_folder, concat_and_write_bams_wrapper, \
pretty_print, read_barcode_whitelist_file, get_contigs_that_need_bams_written

from core import run_edit_identifier, run_bam_reconfiguration, \
gather_edit_information_across_subcontigs, run_coverage_calculator, generate_site_level_information
        
    
def edit_finder(bam_filepath, output_folder, reverse_stranded, barcode_tag="CB", barcode_whitelist=None, contigs=[], num_intervals_per_contig=16, 
                verbose=False):
    
    pretty_print("Each contig is being split into {} subsets...".format(num_intervals_per_contig))
    
    overall_label_to_list_of_contents, results, overall_time, overall_total_reads, \
    total_seconds_for_reads = run_edit_identifier(
        bam_filepath, 
        output_folder, 
        reverse_stranded=reverse_stranded,
        barcode_tag=barcode_tag,
        barcode_whitelist=barcode_whitelist,
        contigs=contigs,
        num_intervals_per_contig=num_intervals_per_contig, 
        verbose=verbose
    )
    
    
    pretty_print(
        [
            "Reads processed:\t{}".format(overall_total_reads), 
            "Time to process reads in min:\t{}".format(round(overall_time/60, 5))
        ],
        style="-"
    )
    
    
    total_seconds_for_reads_df = pd.DataFrame.from_dict(total_seconds_for_reads, orient='index')
    total_seconds_for_reads_df.columns = ['seconds']
    total_seconds_for_reads_df['reads'] = total_seconds_for_reads_df.index
    total_seconds_for_reads_df.index = range(len(total_seconds_for_reads_df))
    
    
    return overall_label_to_list_of_contents, results, total_seconds_for_reads_df


def bam_processing(overall_label_to_list_of_contents, output_folder, barcode_tag='CB', cores=1):
    split_bams_folder = '{}/split_bams'.format(output_folder)
    make_folder(split_bams_folder)
    contigs_to_generate_bams_for = get_contigs_that_need_bams_written(overall_label_to_list_of_contents, split_bams_folder, barcode_tag=barcode_tag)
    pretty_print("Will split and reconfigure the following contigs: {}".format(",".join(contigs_to_generate_bams_for)))
    
    
    # BAM Generation
    total_bam_generation_time, total_seconds_for_bams = run_bam_reconfiguration(split_bams_folder, bam_filepath, overall_label_to_list_of_contents, contigs_to_generate_bams_for, barcode_tag=barcode_tag, cores=cores)
    
    total_seconds_for_bams_df = pd.DataFrame.from_dict(total_seconds_for_bams, orient='index')
    total_seconds_for_bams_df.columns = ['seconds']
    total_seconds_for_bams_df['contigs'] = total_seconds_for_bams_df.index
    total_seconds_for_bams_df.index = range(len(total_seconds_for_bams_df))
    
    return total_bam_generation_time, total_seconds_for_bams_df
    
    
    
def coverage_processing(output_folder, barcode_tag='CB', cores=1):
    edit_info_grouped_per_contig_combined = gather_edit_information_across_subcontigs(output_folder, barcode_tag=barcode_tag)
    results, total_time, total_seconds_for_contig = run_coverage_calculator(edit_info_grouped_per_contig_combined, output_folder, barcode_tag=barcode_tag, cores=cores)
    
    total_seconds_for_contig_df = pd.DataFrame.from_dict(total_seconds_for_contig, orient='index')
    total_seconds_for_contig_df.columns = ['seconds']
    total_seconds_for_contig_df['contig sections'] = total_seconds_for_contig_df.index
    total_seconds_for_contig_df.index = range(len(total_seconds_for_contig_df))
    
    return results, total_time, total_seconds_for_contig_df


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

    
def run(bam_filepath, output_folder, contigs=[], num_intervals_per_contig=1, reverse_stranded=True, barcode_tag="CB", barcode_whitelist_file=None, verbose=False):
    min_base_quality = 15
    min_dist_from_end = 5
    
    
    print_marine_logo()
    
    
    logging_folder = "{}/metadata/".format(output_folder)
    make_folder(logging_folder)
    
    
    if barcode_whitelist_file:
        barcode_whitelist = read_barcode_whitelist_file(barcode_whitelist_file)
    else:
        barcode_whitelist = None
        
    # Edit identification
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    pretty_print("Identifying edits", style="~")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    overall_label_to_list_of_contents, results, total_seconds_for_reads_df = edit_finder(
        bam_filepath, 
        output_folder, 
        reverse_stranded,
        barcode_tag,
        barcode_whitelist,
        contigs,
        num_intervals_per_contig,
        verbose
    )
    
    total_seconds_for_reads_df.to_csv("{}/edit_finder_timing.tsv".format(logging_folder), sep='\t')

    # Make a subfolder into which the split bams will be placed
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    pretty_print("Contigs processed:\n\n\t{}".format(sorted(list(overall_label_to_list_of_contents.keys()))))
    pretty_print("Splitting and reconfiguring BAMs to optimize coverage calculations", style="~")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    total_bam_generation_time, total_seconds_for_bams_df = bam_processing(overall_label_to_list_of_contents, output_folder, barcode_tag=barcode_tag, cores=num_intervals_per_contig)
    total_seconds_for_bams_df.to_csv("{}/bam_reconfiguration_timing.tsv".format(logging_folder), sep='\t')
    
    # Coverage calculation
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    pretty_print("Total time to concat and write bams: {} minutes".format(round(total_bam_generation_time/60, 3)))
    pretty_print("Calculating coverage at edited sites", style='~')
    
    results, total_time, total_seconds_for_contig_df = coverage_processing(output_folder, barcode_tag=barcode_tag, cores=num_intervals_per_contig)
    total_seconds_for_contig_df.to_csv("{}/coverage_calculation_timing.tsv".format(logging_folder), sep='\t')

        
    pretty_print("Total time to calculate coverage: {} minutes".format(round(total_time/60, 3)))
    all_edit_info_pd = pd.concat(results)
    all_edit_info_pd.to_csv('{}/all_edit_info.tsv'.format(output_folder), sep='\t')
    
    # Filtering and site-level information
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    pretty_print("Filtering and calculating site-level statistics", style="~")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    all_edit_info_pd['contig'] = all_edit_info_pd['contig'].astype(str)
    
    # Convert to polars for faster operations
    all_edit_info = pl.from_pandas(all_edit_info_pd)
    all_edit_info_filtered = all_edit_info.filter(
        (pl.col("base_quality") > min_base_quality) & (pl.col("dist_from_end") >= min_dist_from_end))
    final_site_level_information_df = generate_site_level_information(all_edit_info_filtered)
    

    pretty_print("\tNumber of edits before filtering:\n\t{}".format(len(all_edit_info)))
    pretty_print("\tNumber of edits after filtering:\n\t{}".format(len(all_edit_info_filtered)))
    pretty_print("\tNumber of unique edit sites:\n\t{}".format(len(final_site_level_information_df)))


    all_edit_info_filtered.write_csv('{}/filtered_edit_info.tsv'.format(output_folder), 
                                     separator='\t')
    final_site_level_information_df.write_csv('{}/site_info.tsv'.format(output_folder), 
                                              separator='\t')

    pretty_print("Done!", style="+")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run MARINE')
    
    bulk_default_ct = '/projects/ps-yeolab3/ekofman/sailor2/data/Hugo-A1Aligned.sortedByCoord.out.md.bam' # C > T Apobec1 rep1
    bulk_default_ai = '/projects/ps-yeolab4/ekofman/Hugo/RBFOX2_bams/Hugo-B5Aligned.sortedByCoord.out.bam' # A > I 8e rep1
    sc_subset_ct = '/projects/ps-yeolab3/ekofman/sailor2/data/groups_0_1_2_3_4_5_6_7_8_9_10_11_merged.bam' # C > T Apobec1 sc subset
    sc_whole_ct = '/projects/ps-yeolab5/ekofman/Sammi/MouseBrainEF1A_SingleCell_EPR_batch2/filtered_possorted_ms_hippo_stamp_bam/filtered_keep_xf25_possorted_genome_with_header.bam_MD.bam'
    
    output_names = {
        bulk_default_ct: 'bulk_CT',
        bulk_default_ai: 'bulk_AI',
        sc_subset_ct: 'sc_subset_CT',
        sc_whole_ct: 'sc_whole_CT'
    }
    
    barcode_tag_dict = {
        sc_subset_ct: "CB",
        sc_whole_ct: "CB",
        bulk_default_ct: None,
        bulk_default_ai: None
    }
    
    
    reverse_stranded_dict = {
        sc_subset_ct: False,
        sc_whole_ct: False,
        bulk_default_ct: True,
        bulk_default_ai: True
    }
    
    #default_bam_filepath = bulk_default_ct
    #default_bam_filepath = sc_whole_ct

    default_bam_filepath = bulk_default_ct
    
    default_output_folder = '/projects/ps-yeolab3/ekofman/sailor2/scripts/{}'.format(output_names.get(default_bam_filepath))
    
    barcode_tag = barcode_tag_dict.get(default_bam_filepath)

    if default_bam_filepath in [sc_whole_ct, sc_subset_ct]:
        barcode_whitelist_file = '/projects/ps-yeolab3/ekofman/Sammi/MouseBrainEF1A_SingleCell_EPR_batch2/cellranger/results/ms_hippo_stamp_EIF4A_batch2/outs/filtered_feature_bc_matrix/barcodes.tsv.gz'
    else:
        barcode_whitelist_file = None
    
    
    parser.add_argument('--bam_filepath', type=str, default=default_bam_filepath)
    
    
    parser.add_argument('--output_folder', type=str, default=default_output_folder)
    
    parser.add_argument('--barcode_whitelist_file', type=str, default=barcode_whitelist_file)
    
    parser.add_argument('--cores', type=int, default=multiprocessing.cpu_count())
    
    args = parser.parse_args()
    bam_filepath = args.bam_filepath
    output_folder = args.output_folder
    barcode_whitelist_file = args.barcode_whitelist_file
    cores = args.cores
    reverse_stranded = reverse_stranded_dict.get(default_bam_filepath)
    
    if cores is None:
        cores = 16
    pretty_print("Assuming {} cores available for multiprocessing".format(cores))
   
    
    pretty_print(["Arguments:",
                  "\tBAM filepath:\t{}".format(bam_filepath), 
                  "\tOutput folder:\t{}".format(output_folder),
                  "\tBarcode whitelist:\t{}".format(barcode_whitelist_file),
                  "\tReverse Stranded:\t{}".format(reverse_stranded),
                  "\tBarcode Tag:\t{}".format(barcode_tag)
                 ])
    
    run(bam_filepath, 
        output_folder, 
        #contigs=['1', '2', '3'],
        reverse_stranded=reverse_stranded,
        barcode_tag=barcode_tag,
        barcode_whitelist_file=barcode_whitelist_file,
        num_intervals_per_contig=cores
       )