# This sample has an edit at the very end of the read. But we want to make sure it is not included if dist from end filter
# is active.

mypython=$1

$mypython $MARINE/marine.py \
--bam_filepath \
$MARINE/tests/singlecell_tests/bams/10_C-1_orig.bam \
--annotation_bedfile_path \
$MARINE/annotations/cellranger-GRCh38-3.0.0.annotation.genes.bed \
--output_folder \
$MARINE/tests/singlecell_tests/edge_case_filter_dist_test \
--min_base_quality \
15 \
--cores \
4 \
--min_dist_from_end 2 \
--barcode_tag "CB" \
--strandedness 2 --num_per_sublist 1 \
--contigs 10 --interval_length 40000000 --keep_intermediate_files