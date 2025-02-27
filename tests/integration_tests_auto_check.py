import pandas as pd
import sys
import os
from glob import glob
import anndata as ad
import scipy.sparse as sp
import anndata


test_name_to_expectations = {
    "no_edits_edge_case_test": {
        "folder": "strandedness_tests",
        "total_edit_sites": 0,
        "expectations": []
    },
    "edge_case_test": {
        "folder": "singlecell_tests",
        "total_edit_sites": 2,
        "expectations": [{
            "contig": "10",
            "barcode": 	"AAACGAATCATTCATC-1",
            "position": 132330481,
            "num_rows": 1,
            "count": 1,
            "coverage": 1,
            "conversion": "T>G",
            "strand_conversion": "A>C",
            "strand": "-",
            "feature_name": "STK32C",
            "feature_strand": "-"
        },
        {
            "contig": "10",
            "barcode": 	"AAACGAATCATTCATC-1",
            "position": 132330438,
            "num_rows": 1,
            "count": 1,
            "coverage": 1,
            "conversion": "T>C",
            "strand_conversion": "A>G",
            "strand": "-",
            "feature_name": "STK32C",
            "feature_strand": "-"
        }]
    },
    "edge_case_filter_dist_test": {
        "folder": "singlecell_tests",
        "total_edit_sites": 1,
        "expectations": [{
            "contig": "10",
            "barcode": 	"AAACGAATCATTCATC-1",
            "position": 132330438,
            "num_rows": 1,
            "count": 1,
            "coverage": 1,
            "conversion": "T>C",
            "strand_conversion": "A>G",
            "strand": "-",
            "feature_name": "STK32C",
            "feature_strand": "-"
        }]
    },
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
    
    "F1R2_pair_test-single_end_mode_sailor": {
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

print("Current directory: {}".format(os.getcwd()))

# Check out results of each test
failures = 0
for test_name, info in test_name_to_expectations.items():
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nChecking results for {}".format(test_name))

    failure = False

    folder = info.get("folder")
    final_filtered_site_info_annotated = "{}/{}/final_filtered_site_info_annotated.tsv".format(folder, test_name)
    final_filtered_site_info_annotated_df = pd.read_csv(final_filtered_site_info_annotated, sep='\t', index_col=0)

    if "total_edit_sites" in info:
        try:
            assert(len(final_filtered_site_info_annotated_df) == info.get("total_edit_sites"))
            print("\n   >>> Found {} edits total, as expected <<<\n".format(info.get("total_edit_sites")))
        except Exception as e:
            print("Exception:\n\tNum total rows in final_filtered_site_info_annotated.tsv expected: {}, was {}".format(info.get("total_edit_sites"), len(final_filtered_site_info_annotated_df)))
            failure = True 
            failures += 1
            continue 
            
    expectations_list = info.get("expectations")
    for expectations in expectations_list:
        failure = False
        print("\tExpecting: {}".format(expectations))
        
        contig = expectations.get("contig")
        barcode = expectations.get("barcode", None)
        
        position = expectations.get("position")
        
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



tests_dir = sys.argv[1]
print('tests dir is {}'.format(tests_dir))
# Single-cell vs bulk processing check for same single-cell dataset 
sc_5_cells_path = "singlecell_tests/only_5_cells_test/final_filtered_site_info.tsv"
bulk_5_cells_path = "singlecell_tests/only_5_cells_bulk_mode_test/final_filtered_site_info.tsv"

print("Current directory: {}".format(os.getcwd()))
print("\tMatching files: {}".format(glob('singlecell_tests/only_5*/*final_filtered_site_info.tsv')))

sc_5_cells = pd.read_csv(sc_5_cells_path, sep='\t').sort_values(['position', 'strand_conversion'])
bulk_5_cells = pd.read_csv(bulk_5_cells_path, sep='\t').sort_values(['position', 'strand_conversion'])

print("Checking that analyzing a single-cell dataset in 'bulk' mode (i.e. not specificying the 'CB' barcode) yields the exact same positions and base changes, but with counts and coverages aggregated rather than at a single-cell resolution")
grouped_sc = pd.DataFrame(sc_5_cells.groupby(['contig', 'position', 'strand_conversion']).agg({'count': sum, 'strand_conversion': 'unique'}))
grouped_sc.index.names = ['contig', 'position', 'c']
grouped_sc['strand_conversion'] = [i[0] for i in grouped_sc['strand_conversion']]
grouped_sc = grouped_sc.sort_values(['position', 'strand_conversion'])

grouped_sc_rows = []
for r in grouped_sc.iterrows():
    grouped_sc_rows.append(r[0])

bulk_rows = []
for r in bulk_5_cells.iterrows():
    r = r[1]
    bulk_rows.append((r['contig'], r['position'], r['strand_conversion']))

try:
    assert(grouped_sc_rows == bulk_rows)
    for bulk_item, grouped_sc_item in zip(bulk_rows, grouped_sc_rows):
        assert(bulk_item == grouped_sc_item)
    assert(len(grouped_sc_rows) == len(bulk_rows))
    print("\n\t >>> single-cell and bulk on same dataset comparison passed! <<<\n")
except Exception as e:
    print("Exception: {}".format(e))
    print("\n\t ~~~ single cell vs bulk modes on sc dataset equivalency test FAILED! ~~~\n")
    failures += 1


def get_all_edited_positions_and_barcodes_adatas(test_folder):
    overall_coverage_matrix = f"{test_folder}/final_matrix_outputs/comprehensive_coverage_matrix.h5ad"
    overall_ct_edits_matrix = f"{test_folder}/final_matrix_outputs/comprehensive_C_T_edits_matrix.h5ad"
    overall_ag_edits_matrix = f"{test_folder}/final_matrix_outputs/comprehensive_A_G_edits_matrix.h5ad"
    overall_gc_edits_matrix = f"{test_folder}/final_matrix_outputs/comprehensive_G_C_edits_matrix.h5ad"
    
    # Load the AnnData object
    coverage_adata = ad.read_h5ad(overall_coverage_matrix)
    ct_edits_adata = ad.read_h5ad(overall_ct_edits_matrix)
    ag_edits_adata = ad.read_h5ad(overall_ag_edits_matrix)
    gc_edits_adata = ad.read_h5ad(overall_gc_edits_matrix)
    
    return coverage_adata, ct_edits_adata, ag_edits_adata, gc_edits_adata


def get_all_positions_and_barcodes_in_adatas(test_folder):
    name_to_obs = {}
    name_to_pos = {}
    name_to_adata = {}

    coverage_and_edit_matrices = sorted(glob('{}/final_matrix_outputs/comprehensive_coverage_matrix.h5ad'.format(test_folder))) + sorted(glob('{}/final_matrix_outputs/*edits_matrix.h5ad'.format(test_folder)))
    print('coverage_and_edit_matrices in {}'.format(test_folder),
          len(coverage_and_edit_matrices))

    total_edits_sum = 0
    
    for f in coverage_and_edit_matrices:
        filename = f.split('/')[-1].split('.h5ad')[0]

        # Load the AnnData object
        adata = ad.read_h5ad(f)

        if 'edits' in filename:
            total_edits_sum += pd.DataFrame(adata.X.todense()).sum().sum()
            
        print(filename, '\n\t', adata)

        name_to_adata[filename] = adata
        name_to_obs[filename] = set(adata.obs.index.tolist())
        name_to_pos[filename] = set(adata.var.index.tolist())
    
    covered_pos = set()
    covered_obs = set()
    
    edited_pos = set()
    edited_obs = set()
    
    for k,v in name_to_obs.items():
        if 'coverage' in k:
            covered_obs = covered_obs.union(v)
        else:
            edited_obs = edited_obs.union(v)
            
    for k,v in name_to_pos.items():
        if 'coverage' in k:
            covered_pos = covered_pos.union(v)
        else:
            edited_pos = edited_pos.union(v)
            
    final_filtered_site_info = pd.read_csv(f'{test_folder}/final_filtered_site_info.tsv', sep='\t')
    final_filtered_site_info['CombinedPosition'] = \
final_filtered_site_info['contig'].astype(str) + ':' + final_filtered_site_info['position'].astype(str)

    
    return edited_pos, covered_pos, edited_obs, covered_obs, \
    final_filtered_site_info, name_to_pos, name_to_obs, name_to_adata, total_edits_sum

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#     Check that the coverage and edit matrices are correct
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
print("Checking that the position X barcode coverage and edit h5ad sparse matrices are correct and contain the same information as the flat tsv final sites.")


adata_outputs_to_check = {
    'only_5_cells_all_coverage_with_extra_tabulated_sites_adata_test': {
        'test_folder': 'singlecell_tests/only_5_cells_all_cells_coverage_test/',
        'positions_in_adata': 53,
        'barcodes_in_adata': 5,
        'total_edits_sum': 99
    },
    'only_5_cells_all_coverage_all_edited_sites_adata_test': {
        'test_folder': 'singlecell_tests/only_5_cells_all_cells_coverage_no_tabulation_test/',
        'positions_in_adata': 51,
        'barcodes_in_adata': 5,
        'total_edits_sum': 99
    },
    'only_4_cells_all_coverage_with_extra_tabulated_sites_adata_test': {
        'test_folder': 'singlecell_tests/only_4_cells_all_cells_coverage_test/',
        'positions_in_adata': 53,
        'barcodes_in_adata': 4,
        'total_edits_sum': 89
    }
}

for test_name, test_values_dict in adata_outputs_to_check.items():
    print(f"\n===================================================================================================\
    \nRunning adata checks for\
    {test_name}\n===================================================================================================\n")
    expected_var = adata_outputs_to_check.get(test_name).get('positions_in_adata')
    expected_obs = adata_outputs_to_check.get(test_name).get('barcodes_in_adata')
    expected_total_edits_sum = adata_outputs_to_check.get(test_name).get('total_edits_sum')
    test_folder = adata_outputs_to_check.get(test_name).get('test_folder')
    
    
    edited_pos, covered_pos, edited_obs, covered_obs, final_filtered_site_info,\
    name_to_pos, name_to_obs, name_to_adata, total_edits_sum = get_all_positions_and_barcodes_in_adatas(test_folder)
    
    
    print('Checking that all tabulation bed positions are found in the sparse matrices')
    try:
        assert(expected_var == len(edited_pos))
        print("\n\t >>> Passed!")
    except Exception as e:
        print(e)
        print(f'Exception: edited positions is {len(edited_pos)} instead of expected {expected_var}')
        failures += 1
        
    print('Checking that final_filtered_site_info.tsv set of barcodes is same as in sparse matrices')
    try:
        assert(expected_obs == len(edited_obs))
        print("\n\t >>> Passed!")
    except Exception as e:
        print(f"Exception: edited barcodes is {len(edited_obs)} instead of expected {expected_obs}')")
        print(e)
        failures += 1
    
    
    print('edited barcodes: {}'.format(len(edited_obs)))
    print('covered barcodes: {}'.format(len(covered_obs)))
    try:
        assert(edited_obs == covered_obs)
        print("\n\t >>> coverage matrix / edit matrix barcode comparison passed! <<<\n")
    
    except Exception as e:
        print("Exception: Edited barcodes are not same as covered barcodes")
        print(e)
        failures += 1

    print('Checking that the total sum of all edits in the adata object is as expected ({})'.format(
        final_filtered_site_info['count'].sum()
    ))
    try:
        assert(total_edits_sum == expected_total_edits_sum == final_filtered_site_info['count'].sum())
    except Exception as e:
        print(f"Exception: total edit sum {total_edits_sum} is not same as expected edit sum {expected_total_edits_sum}")
        print(e)
        failures += 1
        
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        
    print('edited positions: {}'.format(len(edited_pos)))
    print('covered positions: {}'.format(len(covered_pos)))
    try:
        assert(edited_pos == covered_pos)
        print("\n\t >>> coverage matrix / edit matrix position comparison passed! <<<\n")
    except Exception as e:
        print("Exception: Edited positions are not same as covered positions")
        print(e)
        failures += 1
    
    # Execute test
    print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
    
    coverage_adata, ct_edits_adata, ag_edits_adata, gc_edits_adata = get_all_edited_positions_and_barcodes_adatas(test_folder)
    
    print('gc_edits_adata: {}'.format(len(gc_edits_adata)))
    print('ag_edits_adata: {}'.format(len(ag_edits_adata)))
    print('ct_edits_adata: {}'.format(len(ct_edits_adata)))
    
    try:
        """
        print('ct_edits_adata', pd.DataFrame(ct_edits_adata.X.todense(),
                                             index=ct_edits_adata.obs.index, 
                                             columns=ct_edits_adata.var.index), '\n')
        
        print('ag_edits_adata', pd.DataFrame(ag_edits_adata.X.todense(),
                                             index=ag_edits_adata.obs.index, 
                                             columns=ag_edits_adata.var.index), '\n')
    
        print('gc_edits_adata', pd.DataFrame(gc_edits_adata.X.todense(),
                                             index=gc_edits_adata.obs.index, 
                                             columns=gc_edits_adata.var.index), '\n')
        
        print('coverage_adata', pd.DataFrame(coverage_adata.X.todense(),
                                             index=coverage_adata.obs.index, 
                                             columns=coverage_adata.var.index)[['9:3000508', '9:3000527', '9:3000528']], '\n')
        """  
        
        assert(ct_edits_adata['GGGACCTTCGAGCCAC-1','9:3000528'].X.todense() == 1)
        assert(coverage_adata['GGGACCTTCGAGCCAC-1','9:3000528'].X.todense() == 12)
        print("\t\t9:3000528 passed...")
    
        assert(ct_edits_adata['GATCCCTCAGTAACGG-1','9:3000508'].X.todense() == 1)
        assert(coverage_adata['GATCCCTCAGTAACGG-1','9:3000508'].X.todense() == 3)
        print("\t\t9:3000508 passed...")
    
        assert(ag_edits_adata['GGGACCTTCGAGCCAC-1','9:3000527'].X.todense() == 10)
        assert(coverage_adata['GGGACCTTCGAGCCAC-1','9:3000527'].X.todense() == 12)
        print("\t\t9:3000527 passed...")
        
        assert(gc_edits_adata['GATCCCTCAGTAACGG-1','9:3000525'].X.todense()== 1)
        assert(coverage_adata['GATCCCTCAGTAACGG-1','9:3000525'].X.todense() == 4)
        print("\t\t9:3000525 passed...")
    
        print("\n\t >>> coverage matrix and edit matrix values confirmation passed! <<<\n")
    
    except Exception as e:
        print('Error', e)
        print("Exception: Expected edit and coverage values not found in sparse matrices")
        failures += 1
        raise(e)
    

print("There were {} failures".format(failures))
if failures > 0:
    sys.exit(1)
else:
    sys.exit(0)
