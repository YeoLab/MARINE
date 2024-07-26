import pandas as pd
import sys

test_name_to_expectations = {
    "unstranded_pair_test": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "Citrine.dna",
            "position": 435,
            "count": 22,
            "coverage": 22,
            "num_rows": 1,
            "strand_conversion": "C>T",
            "strand": "+"
        }]
    },
    "pair_test": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "18",
            "position": 49491556,
            "count": 2,
            "coverage": 2,
            "num_rows": 1,
            "strand_conversion": "C>T",
            "strand": "-",
            "feature_name": "RPL17-C18orf32,RPL17",
            "feature_strand": "-,-"
        },
        {
            "contig": "18",
            "position": 49567494,
            "count": 2,
            "coverage": 2,
            "num_rows": 1,
            "strand_conversion": "C>T",
            "strand": "+",
            "feature_name": "LIPG",
            "feature_strand": "+"
        }]
    },
    
    "F1R2_pair_test": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "chr17",
            "position": 43044352,
            "count": 1,
            "coverage": 1,
            "conversion": "G>A",
            "num_rows": 1,
            "conversion": "G>A",
            "strand_conversion": "C>T",
            "strand": "-",
            "feature_name": "BRCA1",
            "feature_strand": "-"
        }]
    },

    "F1R2_pair_test-single_end_mode": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "chr17",
            "position": 43044352,
            "count": 1,
            "coverage": 2,
            "conversion": "G>A",
            "num_rows": 1,
            "conversion": "G>A",
            "strand_conversion": "C>T",
            "strand": "-",
            "feature_name": "BRCA1",
            "feature_strand": "-"
        }]
    },

     "F2R1_end_second_in_pair_test": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "chr17",
            "position": 43001716,
            "count": 1,
            "coverage": 1,
            "conversion": "G>A",
            "strand_conversion": "G>A",
            "strand": "+",
            "feature_name": "RPL27"
        }]
    },
    "same_pos_dif_reads_test": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "chr17",
            "position": 83199872,
            "count": 9,
            "coverage": 9,
            "conversion": "C>G",
            "strand_conversion": "C>G",
            "strand": "+",
            "feature_name": "AC139099.2"
        }]
    },
    "tax1bp3_chr17_3665556_read_test": {
        "folder": "strandedness_tests",
        "expectations": [{
            "contig": "chr17",
            "position": 3665556,
            "num_rows": 1,
            "count": 1,
            "coverage": 1,
            "conversion": "G>A",
            "strand_conversion": "G>A",
            "strand": "+",
            #"feature_name": "AC139099.2"
        }]
    },

        "only_5_cells_test": {
        "folder": "singlecell_tests",
        "expectations": [{
            "contig": "9",
            "barcode": 	"GGGACCTTCGAGCCAC-1",
            "position": 3000524,
            "num_rows": 1,
            "count": 1,
            "coverage": 12,
            "conversion": "C>A",
            "strand_conversion": "G>T",
            "strand": "-"
        },
        {
            "contig": "9",
            "barcode": 	"GGGACCTTCGAGCCAC-1",
            "position": 3000525,
            "num_rows": 1,
            "count": 1,
            "coverage": 12,
            "conversion": "C>T",
            "strand_conversion": "G>A",
            "strand": "-"
        },
        {
            "contig": "9",
            "barcode": 	"GATCCCTCAGTAACGG-1",
            "position": 3000525,
            "num_rows": 1,
            "count": 1,
            "coverage": 4,
            "conversion": "C>G",
            "strand_conversion": "G>C",
            "strand": "-"
        }]
    },
    "long_read_sc_test": {
        "folder": "singlecell_tests",
        "expectations": [{
            "contig": "6",
            "barcode": 	"ENSMUST00000203816-AACGTGTTGGAGAGGG-16-G",
            "position": 115807969,
            "num_rows": 1,
            "count": 1,
            "coverage": 1,
            "conversion": "A>C",
            "strand_conversion": "T>G",
            "strand": "-",
            "feature_name": "Rpl32"
        },
        {
            "contig": "6",
            "barcode": 	"ENSMUST00000081840-AAGTCGTACCAGGCTC-40-C",
            "position": 115805653,
            "num_rows": 1,
            "count": 1,
            "coverage": 1,
            "conversion": "G>A",
            "strand_conversion": "C>T",
            "strand": "-",
            "feature_name": "Rpl32"
        },
        {
            "contig": "6",
            "barcode": 	"ENSMUST00000081840-AACGTGTTGGAGAGGG-40-G",
            "position": 115807015,
            "num_rows": 1,
            "count": 1,
            "coverage": 8,
            "conversion": "C>T",
            "strand_conversion": "G>A",
            "strand": "-",
            "feature_name": "Rpl32"
        }]
    }

}

failures = 0
for test_name, info in test_name_to_expectations.items():
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nChecking results for {}".format(test_name))
    
    expectations_list = info.get("expectations")
    for expectations in expectations_list:
        print("\tExpecting: {}".format(expectations))
    
              
        folder = info.get("folder")
        
        contig = expectations.get("contig")
        barcode = expectations.get("barcode", None)
        
        position = expectations.get("position")
        
        final_filtered_site_info_annotated = "{}/{}/final_filtered_site_info_annotated.tsv".format(folder, test_name)
        final_filtered_site_info_annotated_df = pd.read_csv(final_filtered_site_info_annotated, sep='\t', index_col=0)
    
        row_of_interest = final_filtered_site_info_annotated_df[
            (final_filtered_site_info_annotated_df['position'] == position) &\
            (final_filtered_site_info_annotated_df['contig'].astype(str) == contig)
        ]
    
    
        if barcode:
            row_of_interest = row_of_interest[row_of_interest.barcode == barcode]
    
        failure = False
        try:
            assert(len(row_of_interest) == expectations.get("num_rows", 1))
        except Exception as e:
            print("Num rows expected: {}, was {}".format(expectations.get("num_rows", 1), len(row_of_interest)))
            failure = True
            
        for attribute in list(expectations.keys()):
            if attribute in ['count', 'coverage', 'conversion', 'strand', 'feature_name']:
                attribute_expectation = expectations.get(attribute)
                try:
                    assert(row_of_interest[attribute].iloc[0] == attribute_expectation)
                except Exception as e:
                    print("Exception: {} was {}".format(attribute, row_of_interest[attribute].iloc[0]))
                    failure = True
        if not failure:
            print("\n\t >>> {} passed! <<<\n".format(test_name))
        else:
            print("\n\t ~~~ {} FAILED! ~~~\n".format(test_name))
            failures += 1

print("There were {} failures".format(failures))
if failures > 0:
    sys.exit(1)
else:
    sys.exit(0)