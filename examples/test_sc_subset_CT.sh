#! /bin/bash

$MARINE/marine.py --bam_filepath $MARINE/examples/data/single_cell_CT.md.subset.bam --output_folder $MARINE/examples/sc_subset_CT --barcode_whitelist_file $MARINE/examples/data/sc_barcodes.tsv.gz --barcode_tag "CB" --num_intervals_per_contig 16 --strandedness 2 --contigs "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,X,Y"
