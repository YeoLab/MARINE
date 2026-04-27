import unittest
import os
import sys

directory_path = os.path.abspath(os.path.join('../src/'))
if directory_path not in sys.path:
    sys.path.append(directory_path)

from utils import get_contig_lengths_dict, get_intervals
from read_process import incorporate_replaced_pos_info,incorporate_insertions_and_deletions,\
get_positions_from_md_tag,reverse_complement,remove_softclipped_bases


class TestReadProcessFunctions(unittest.TestCase): 
    def test_reverse_complement(self):
        # Test reverse complement function
        print("Testing reverse_complement")
        test_seq = 'ACTGAC'
        expected_seq = 'GTCAGT'
        self.assertEqual(reverse_complement(test_seq), expected_seq)
    
    def test_incorporate_replaced_pos_info_insertions(self):
        # Test incorporating insertions (1 is insertion)
        print("Testing incorporate_replaced_pos_info_insertions...")
        
        test_aligned_seq = \
        'GATGCTTATATAGGGAACAAAATGGTCCCTACACCATTTTTTTTTTCTGGAGTGCATAATGGATACATTTGATGACTTTTACCCTCTTATCTAAATCTAAA'
        fixed_test_aligned_seq = \
        'GATGCTTATATAGGGAACAAAATGGTCCCTACACCATTTTTTTTTCTGGAGTGCATAATGGATACATTTGATGACTTTTACCCTCTTATCTAAATCTAAA'
        test_cigar_tuples = [(0, 44), (1, 1), (0, 56)]
        self.assertEqual(incorporate_insertions_and_deletions(test_aligned_seq, test_cigar_tuples),
                         fixed_test_aligned_seq)
        
    def test_incorporate_replaced_pos_info_deletions(self):
        # Test incorporating deletions (2 is deletion, 4 is soft-clipping)
        print("Testing incorporate_replaced_pos_info_deletions...")
        
        test_aligned_seq = \
        'TCTTTGATAGAGCCACCAAGATGCTTATATAGGGAACAAATGGTCCCTACACCATTTTTTTTCCTGGAGTGCCCCATGTACTCTGCGTTGATACCACTGCT'
        fixed_test_aligned_seq =\
        'TCTTTGATAGAGCCACCAAGATGCTTATATAGGGAAC*AAATGGTCCCTACACCATTTTTTTTCCTGGAGTGC'
        test_cigar_tuples = [(0, 37), (2, 1), (0, 35), (4, 29)]
        self.assertEqual(incorporate_insertions_and_deletions(test_aligned_seq, test_cigar_tuples),
                         fixed_test_aligned_seq)

    def test_get_positions_from_md_tag(self):
        print("Testing get_positions_from_md_tag...")
        md_tags_and_expectations = {
            '11T63': [11, 75]
        }
        
        for md_tag, expected in md_tags_and_expectations.items():
            print('\tTesting {}...'.format(md_tag))
            positions = get_positions_from_md_tag(md_tag)
            self.assertEqual(expected, positions)
            
    def test_incorporate_replaced_pos_info(self):
        print("Testing incorporate_replaced_pos_info...")
        indicated_sequence, bases_at_pos = incorporate_replaced_pos_info('ACTAGACA', [0, 3, 6])
        self.assertEqual('ActAgaCa', indicated_sequence)
        self.assertEqual(['A', 'A', 'C'], bases_at_pos)
        
    def test_remove_softclipped_bases(self):
        test_cigar_tuples = [(4, 2), (0, 7)]
        test_aligned_sequence = '123456789'
        clipped, cropped_tuples = remove_softclipped_bases(test_cigar_tuples, test_aligned_sequence)
        assert(clipped == '3456789')
        assert(cropped_tuples == [(0,7)])

        test_cigar_tuples = [(0, 2), (4, 7)]
        test_aligned_sequence = '123456789'
        clipped, cropped_tuples = remove_softclipped_bases(test_cigar_tuples, test_aligned_sequence)
        assert(clipped == '12')
        assert(cropped_tuples == [(0,2)])


class TestUtilsFunctions(unittest.TestCase):
    def test_get_intervals_partial_last_window(self):
        # H5 regression: contig length 100, interval 30 -> last interval ends at 100
        intervals = get_intervals('chr1', {'chr1': 100}, 30)
        self.assertEqual(intervals[-1][1], 100,
                         "Last interval end must equal contig_length, not interval boundary")
        self.assertEqual(intervals, [[0, 30], [30, 60], [60, 90], [90, 100]])

    def test_get_intervals_exact_division(self):
        # H5 edge case: contig length 60, interval 30 -> exactly two clean windows
        intervals = get_intervals('chr1', {'chr1': 60}, 30)
        self.assertEqual(intervals, [[0, 30], [30, 60]])

    def test_get_intervals_short_contig(self):
        # H5 edge case: contig length 100 with interval_length larger than contig
        intervals = get_intervals('chr1', {'chr1': 100}, 2000000)
        self.assertEqual(intervals, [[0, 100]])

    def test_get_coverage_wrapper_no_header_kwarg(self):
        # C4 regression: .format() call must not pass header=False
        import inspect
        from utils import get_coverage_wrapper
        source = inspect.getsource(get_coverage_wrapper)
        # The bug was: '{}/coverage/{}.tsv'.format(output_folder, contig, header=False)
        # The fix is:  '{}/coverage/{}.tsv'.format(output_folder, contig)
        self.assertNotIn('header=False', source,
                         ".format() must not receive header keyword argument")
        self.assertIn(".format(output_folder, contig)", source,
                      "Filename must be built with two positional .format() args")

    def test_marine_run_starts_time_at_top(self):
        # C2 regression: start_time = time.time() must appear before any zero_edit_found call inside run()
        import inspect
        import sys as _sys
        _sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE')
        import marine
        source = inspect.getsource(marine.run)
        # start_time assignment must precede first zero_edit_found reference
        idx_start = source.find('start_time = time.time()')
        idx_zero = source.find('zero_edit_found')
        self.assertGreaterEqual(idx_start, 0,
                                "run() must define start_time via time.time()")
        self.assertGreaterEqual(idx_zero, 0,
                                "run() must reference zero_edit_found")
        self.assertLess(idx_start, idx_zero,
                        "start_time must be defined before first zero_edit_found call")

    def test_marine_pool_uses_processes_param(self):
        # C3 regression: Pool must use the function's `processes` parameter, not undefined `cores`
        import inspect
        import sys as _sys
        _sys.path.insert(0, '/tscc/projects/ps-yeolab3/bay001/codebase/MARINE')
        import marine
        source = inspect.getsource(marine.generate_and_split_bed_files_for_all_positions)
        self.assertNotIn('Pool(processes=cores)', source,
                         "Pool must not reference undefined `cores`")
        self.assertIn('Pool(processes)', source,
                      "Pool must use the `processes` function parameter")


class TestPublicAPIPreserved(unittest.TestCase):
    def test_generate_empty_matrix_file_removed(self):
        # Task-12 static source regression: confirms the no-op placeholder was deleted
        import utils
        self.assertFalse(
            hasattr(utils, 'generate_empty_matrix_file'),
            "generate_empty_matrix_file was a dead no-op (body: pass, no callers) "
            "and must not be re-introduced"
        )


unittest.main()