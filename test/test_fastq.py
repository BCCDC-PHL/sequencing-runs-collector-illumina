import os
import unittest

import sequencing_runs_service.parsers.fastq as fastq

class TestFastqStats(unittest.TestCase):

    def setUp(self):
        self.test_root_path = os.path.join(os.path.dirname(__file__))
        self.test_data_path = os.path.join(self.test_root_path, 'data')

    def test_collect_fastq_stats_S001_R1(self):
        fastq_path = os.path.join(self.test_data_path, 'fastq', 'S001_R1.fastq')
        fastq_stats = fastq.collect_fastq_stats(fastq_path)

        self.assertIsNotNone(fastq_stats)
        self.assertEqual(fastq_stats['total_reads'], 1)
        self.assertEqual(fastq_stats['total_bases'], 42)
        self.assertEqual(fastq_stats['num_bases_greater_or_equal_to_q30'], 28)
        self.assertEqual(fastq_stats['mean_read_length'], 42.0)
        self.assertEqual(fastq_stats['max_read_length'], 42)
        self.assertEqual(fastq_stats['min_read_length'], 42)

    def test_collect_fastq_stats_S001_R2(self):
        fastq_path = os.path.join(self.test_data_path, 'fastq', 'S001_R2.fastq')
        fastq_stats = fastq.collect_fastq_stats(fastq_path)

        self.assertIsNotNone(fastq_stats)
        self.assertEqual(fastq_stats['total_reads'], 1)
        self.assertEqual(fastq_stats['total_bases'], 42)
        self.assertEqual(fastq_stats['num_bases_greater_or_equal_to_q30'], 31)
        self.assertEqual(fastq_stats['mean_read_length'], 42.0)
        self.assertEqual(fastq_stats['max_read_length'], 42)
        self.assertEqual(fastq_stats['min_read_length'], 42)

    def test_collect_fastq_stats_S001_R1_gz(self):
        fastq_path = os.path.join(self.test_data_path, 'fastq', 'S001_R1.fastq.gz')
        fastq_stats = fastq.collect_fastq_stats(fastq_path)

        self.assertIsNotNone(fastq_stats)
        self.assertEqual(fastq_stats['total_reads'], 1)
        self.assertEqual(fastq_stats['total_bases'], 42)
        self.assertEqual(fastq_stats['num_bases_greater_or_equal_to_q30'], 28)
        self.assertEqual(fastq_stats['mean_read_length'], 42.0)
        self.assertEqual(fastq_stats['max_read_length'], 42)
        self.assertEqual(fastq_stats['min_read_length'], 42)

    def test_collect_fastq_stats_S001_R2_gz(self):
        fastq_path = os.path.join(self.test_data_path, 'fastq', 'S001_R2.fastq.gz')
        fastq_stats = fastq.collect_fastq_stats(fastq_path)

        self.assertIsNotNone(fastq_stats)
        self.assertEqual(fastq_stats['total_reads'], 1)
        self.assertEqual(fastq_stats['total_bases'], 42)
        self.assertEqual(fastq_stats['num_bases_greater_or_equal_to_q30'], 31)
        self.assertEqual(fastq_stats['mean_read_length'], 42.0)
        self.assertEqual(fastq_stats['max_read_length'], 42)
        self.assertEqual(fastq_stats['min_read_length'], 42)

    
