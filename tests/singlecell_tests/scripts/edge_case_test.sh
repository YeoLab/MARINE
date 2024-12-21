# This sample has an edit at the very end of the read. It's a good test to ensure that we don't have off by one errors
# in computing the coverage. It was aligned to the craig venter genome, so the reference is slightly difference from
# hg38 -- if aligning with hg38, this read doesn't have mutations at these positions.

# Expected edit
# AAACGAATCATTCATC-1      10_AAACGAATCATTCATC-1   10_AAACGAATCATTCATC-1:132330481 132330481       T       G       A00621:106:HLFHGDSXX:3:1152:16830:27352 -

# Expected combined.bed file
# 10_AAACGAATCATTCATC-1	132330438	132330439
# 10_AAACGAATCATTCATC-1	132330481	132330482

# Read
# A00621:106:HLFHGDSXX:3:1152:16830:27352 16      10_AAACGAATCATTCATC-1   132330391       255     91M     *       0       0       GCAACACCCATGTCACTCCTCATTCTCTCCTTGCTCTGCCCGGGTGGCTGGCCTCCCCACGCTCCTGAGAAGGTACTGGTTGTGCTTTCAG     FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF    NH:i:1   HI:i:1  AS:i:89 nM:i:0  TX:Z:ENST00000456004,+406,91M   GX:Z:ENSG00000165752    GN:Z:STK32C     fx:Z:ENSG00000165752    RE:A:E  li:i:0  BC:Z:TTTCCACT  QT:Z:FFFFF:FF    CR:Z:AAACGAATCATTCATC   CY:Z:FFFFFFFFFFFFFFFF   CB:Z:AAACGAATCATTCATC-1 UR:Z:CGCTTAAAACCT       UY:Z:FFFFFFFFFFFF       UB:Z:CGCTTAAAACCT      xf:i:25  RG:Z:10X214_1_AB_1:0:1:HLFHGDSXX:3      NM:i:2  MD:Z:47T42T0

mypython=$1

$mypython $MARINE/marine.py \
--bam_filepath \
$MARINE/tests/singlecell_tests/bams/10_C-1_orig.bam \
--annotation_bedfile_path \
$MARINE/annotations/cellranger-GRCh38-3.0.0.annotation.genes.bed \
--output_folder \
$MARINE/tests/singlecell_tests/edge_case_test \
--min_base_quality \
15 \
--cores \
4 \
--barcode_tag "CB" \
--strandedness 2 --num_per_sublist 1 \
--contigs 10 --interval_length 40000000 --keep_intermediate_files