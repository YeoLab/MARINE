#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

mypython=$1

echo "Python is $mypython"


# MARINE environment variable must be set from main marine directory:
#     export MARINE=$(pwd)

echo "Running bulk tests..."

tests_folder="strandedness_tests/"

echo "Bulk tests scripts"
ls -lh $MARINE/tests/$tests_folder/scripts/

for t in "no_edits_edge_case_test" "F1R2_pair_test-single_end_mode_sailor" "F1R2_pair_test-single_end_mode" "F1R2_pair_test" "F2R1_end_second_in_pair_test" "same_pos_dif_reads_test" "tax1bp3_chr17_3665556_read_test" "pair_test" "unstranded_pair_test"
do
    echo $t
    echo "Removing old files..."
    rm $MARINE/tests/$tests_folder$t/* -r || true

    echo "Running tests..."
    bash $MARINE/tests/$tests_folder/scripts/$t.sh $mypython
   
done


echo "Running single-cell tests..."


tests_folder="singlecell_tests/"

echo "SC tests scripts"
ls -lh $MARINE/tests/$tests_folder/scripts/


for t in "only_5_cells_test" "only_5_cells_bulk_mode_test" "only_5_cells_all_cells_coverage_test" "only_4_cells_all_cells_coverage_test" "only_5_cells_all_cells_coverage_no_tabulation_test" "long_read_sc_test" "edge_case_test" "edge_case_dist_filter_test"

do
    echo $t
    echo "Removing old files..."
    rm $MARINE/tests/$tests_folder$t/* -r || true

    echo "Running tests..."
    bash $MARINE/tests/$tests_folder/scripts/$t.sh $mypython
   
done


echo "Checking results..."
$mypython $MARINE/tests/integration_tests_auto_check.py tests

exitcode=$?

echo "Exit code: $exitcode"
exit $exitcode
