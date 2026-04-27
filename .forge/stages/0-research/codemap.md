# Codemap: MARINE
Generated: 2026-04-24 23:50 UTC
Files indexed: 9 | Estimated tokens: ~2,095

## File Tree
  ./
    marine.py - 9 fn: get_unique_barcodes, get_unique_barcodes_for_reads_in_bamfile, get_suffix_pairs_from_bam_filepath, +6
    marine2.py - 7 fn: edit_finder, bam_processing, coverage_processing, +4
  src/
    __init__.py - 20 lines
    annotate.py - 3 fn: make_bedtool_from_final_sites, get_strand_specific_conversion, annotate_sites
    core.py - 17 fn: generate_depths, bam_processing, edit_finder, +14
    read_process.py - 13 fn: reverse_complement, incorporate_insertions_and_deletions, get_hamming_distance, +10
    utils.py - 53 fn: print_marine_logo, generate_permutations_list_for_CB, generate_bedgraphs, +50
  tests/
    integration_tests_auto_check.py - 2 fn: get_all_edited_positions_and_barcodes_adatas, get_all_positions_and_barcodes_in_adatas
    unittests.py - 1 class(es): TestReadProcessFunctions

## Key Files
### marine.py
**Purpose**: no docstring
**Imports**: argparse, collections, glob, multiprocessing, os, pandas as pd, polars as pl, psutil, pysam, shutil, subprocess, sys, time, tqdm, tracemalloc, +6 more
**Classes**: none
**Functions**: `get_unique_barcodes(bam_path)`; `get_unique_barcodes_for_reads_in_bamfile(args)`; `get_suffix_pairs_from_bam_filepath(bam_filepaths)`; `prepare_combinations_for_split(df, bam_filepaths, output_folder, output_suffix, processes=4)`; `process_combination_for_split(args)`; `filter_sites_using_tabulation_bed(df, tabulation_bed)`; `generate_and_split_bed_files_for_all_positions(output_folder, bam_filepaths, tabulation_bed=None, processes=4, output_suffix="all_cells")`; `run(bam_filepath, annotation_bedfile_path, output_folder, contigs=[], strandedness=True, barcode_tag="CB", paired_end=False, barcode_whitelist_file=None, verbose=False, coverage_only=False, filtering_only=False, annotation_only=False, bedgraphs_list=[], sailor_list=[], min_base_quality = 15, min_read_quality = 0, min_dist_from_end = 10, max_edits_per_read = None, cores = 64, number_of_expected_bams=4, 
        keep_intermediate_files=False,
        num_per_sublist=6,
        skip_coverage=False, interval_length=2000000,
        all_cells_coverage=False, tabulation_bed=None
       )`; +1 more

### marine2.py
**Purpose**: no docstring
**Imports**: argparse, multiprocessing, os, pandas as pd, polars as pl, psutil, pysam, scipy.special, sys, time, tqdm, read_process, utils, core, annotate
**Classes**: none
**Functions**: `edit_finder(bam_filepath, output_folder, reverse_stranded, barcode_tag="CB", barcode_whitelist=None, contigs=[], num_intervals_per_contig=16, 
                verbose=False, cores=64)`; `bam_processing(overall_label_to_list_of_contents, output_folder, barcode_tag, cores, number_of_expected_bams,
                   verbose)`; `coverage_processing(output_folder, barcode_tag='CB', paired_end=False, verbose=False, cores=1, number_of_expected_bams=4)`; `print_marine_logo()`; `calculate_sailor_score(sailor_row)`; `get_sailor_sites(final_site_level_information_df, conversion="C>T")`; `run(bam_filepath, annotation_bedfile_path, output_folder, contigs=[], num_intervals_per_contig=16, reverse_stranded=True, barcode_tag="CB", paired_end=False, barcode_whitelist_file=None, verbose=False, coverage_only=False, filtering_only=False, annotation_only=False, sailor=False, min_base_quality = 15, min_dist_from_end = 10, cores = 64, number_of_expected_bams=4)`

### src/__init__.py
**Purpose**: no docstring
**Exports**: get_contig_lengths_dict, incorporate_replaced_pos_info, incorporate_insertions_and_deletions, get_positions_from_md_tag, reverse_complement, get_edit_information, get_edit_information_wrapper, get_read_information, get_intervals, pretty_print
**Imports**: .read_process, .utils, logging
**Classes**: none
**Functions**: none

### src/annotate.py
**Purpose**: no docstring
**Imports**: pybedtools, pandas as pd, os, sys
**Classes**: none
**Functions**: `make_bedtool_from_final_sites(df)`; `get_strand_specific_conversion(r, strandedness)`; `annotate_sites(sites_df, annotation_bedfile_path)`

### src/core.py
**Purpose**: no docstring
**Imports**: pysam, os, glob, sys, time, numpy as np, pandas as pd, polars as pl, collections, multiprocessing, tqdm, read_process, utils, os, psutil, random
**Classes**: none
**Functions**: `generate_depths(output_folder, bam_filepaths, original_bam_filepath, paired_end=False, barcode_tag=None, cores=1)`; `bam_processing(bam_filepath, overall_label_to_list_of_contents, output_folder, barcode_tag='CB', cores=1, number_of_expected_bams=4,
                   verbose=False)`; `edit_finder(bam_filepath, output_folder, strandedness, barcode_tag="CB", barcode_whitelist=None, contigs=[],
                verbose=False, cores=64, min_read_quality=0, min_base_quality=0, dist_from_end=0, interval_length=2000000)`; `run_edit_identifier(bampath, output_folder, strandedness, barcode_tag="CB", barcode_whitelist=None, contigs=[], verbose=False, cores=64, min_read_quality=0, min_base_quality=0, dist_from_end=0, interval_length=2000000)`; `run_bam_reconfiguration(split_bams_folder, bampath, overall_label_to_list_of_contents, contigs_to_generate_bams_for, barcode_tag='CB', cores=1, number_of_expected_bams=4, verbose=False)`; `run_edit_finding(barcode_tag,
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
                    )`; `incorporate_barcode(read_as_string, contig, barcode)`; `write_bam_file(reads, bam_file_name, header_string)`; +9 more

### src/read_process.py
**Purpose**: no docstring
**Imports**: pandas as pd, numpy as np, collections, scipy, copy
**Classes**: none
**Functions**: `reverse_complement(input_seq)`; `incorporate_insertions_and_deletions(aligned_sequence, cigar_tuples, insertions=True, deletions=True, junctions=True)`; `get_hamming_distance(str1, str2)`; `has_edits(read)`; `get_total_coverage_for_contig_at_position(r, coverage_dict)`; `print_read_info(read)`; `get_read_information(read, contig, barcode_tag='CB', verbose=False, strandedness=0, 
                         min_read_quality=0, min_base_quality=0, dist_from_end=0)`; `get_positions_from_md_tag(md_tag, verbose=False)`; +5 more

### src/utils.py
**Purpose**: no docstring
**Imports**: math, glob, os, pysam, polars as pl, pandas as pd, numpy as np, sys, subprocess, collections, itertools, scipy.special, shutil, multiprocessing, time, +5 more
**Classes**: none
**Functions**: `print_marine_logo()`; `generate_permutations_list_for_CB(n)`; `generate_bedgraphs(final_site_level_information_df, conversions_list, output_folder)`; `convert_sites_to_sailor(final_site_level_information_df, sailor_list, output_folder, skip_coverage)`; `split_bed_file(input_bed_file, output_folder, bam_filepaths, output_suffix='')`; `get_contigs_that_need_bams_written(expected_contigs, split_bams_folder, barcode_tag='CB', number_of_expected_bams=4)`; `get_broken_up_contigs(contigs, num_per_sublist)`; `pivot_edits_to_sparse(df, output_folder, overall_barcodes_list, overall_positions_list)`; +45 more

### tests/integration_tests_auto_check.py
**Purpose**: no docstring
**Imports**: pandas as pd, sys, os, glob, anndata as ad, scipy.sparse as sp, anndata
**Classes**: none
**Functions**: `get_all_edited_positions_and_barcodes_adatas(test_folder)`; `get_all_positions_and_barcodes_in_adatas(test_folder)`

### tests/unittests.py
**Purpose**: no docstring
**Imports**: unittest, os, sys, utils, read_process
**Class** `TestReadProcessFunctions(unittest.TestCase)`: test_reverse_complement, test_incorporate_replaced_pos_info_insertions, test_incorporate_replaced_pos_info_deletions, test_get_positions_from_md_tag, test_incorporate_replaced_pos_info, test_remove_softclipped_bases
**Functions**: none

## Dependency Graph
marine.py -> (none)
marine2.py -> (none)
src/__init__.py -> src/read_process.py, src/utils.py
src/annotate.py -> (none)
src/core.py -> (none)
src/read_process.py -> (none)
src/utils.py -> (none)
tests/integration_tests_auto_check.py -> (none)
tests/unittests.py -> (none)

## Statistics
Total files: 9
Total lines: 4,734
Languages: Python (9)
Estimated map tokens: ~2,095 (vs ~47,340 reading all files)
Compression ratio: 22x
