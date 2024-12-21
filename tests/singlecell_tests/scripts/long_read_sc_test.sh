mypython=$1

$mypython $MARINE/marine.py \
--bam_filepath \
$MARINE/examples/data/LR_single_cell.md.subset.filtered.sorted.bam \
--annotation_bedfile_path \
$MARINE/annotations/cellranger-mm10-3.0.0.annotation.genes.bed \
--output_folder \
$MARINE/tests/singlecell_tests/long_read_sc_test \
--min_dist_from_end \
0 \
--min_base_quality \
0 \
--cores \
16 \
--barcode_whitelist_file $MARINE/examples/data/sc_lr_barcodes.tsv \
--strandedness 2 \
--barcode_tag "IB" \
--contigs "6" \
--num_intervals_per_contig 4 \
--keep_intermediate_files