python \
/tscc/projects/ps-yeolab3/ekofman/sailor2/marine.py \
--bam_filepath \
/tscc/projects/ps-yeolab3/ekofman/sailor2/tests/singlecell_tests/bams/9_3000526_only_5_cells.bam \
--annotation_bedfile_path \
/tscc/projects/ps-yeolab3/ekofman/sailor2/annotations/hg38_gencode.v35.annotation.genes.bed \
--output_folder \
/tscc/projects/ps-yeolab3/ekofman/sailor2/tests/singlecell_tests/only_5_cells_test \
--min_dist_from_end \
0 \
--min_base_quality \
0 \
--cores \
16 \
--barcode_tag "CB" \
--contigs "9" \
--verbose \
--num_intervals_per_contig 16