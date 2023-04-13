import json
import xmltodict

def parse_generate_fastq_run_statistics(generate_fastq_run_statistics_path):
    generate_fastq_run_statistics = {}
    doc = None
    with open(generate_fastq_run_statistics_path) as f:
        doc = xmltodict.parse(f.read(), process_namespaces=True)

    if doc is not None:
        generate_fastq_run_statistics['run_stats'] = {
            'num_clusters_raw': None,
            'num_clusters_passed_filter': None,
            'num_unindexed_clusters': None,
            'num_unindexed_clusters_passed_filter': None,
        }
        generate_fastq_run_statistics['sample_stats'] = []
        if 'StatisticsGenerateFASTQ' in doc and 'RunStats' in doc['StatisticsGenerateFASTQ']:
            if 'NumberOfClustersRaw' in doc['StatisticsGenerateFASTQ']['RunStats']:
                try:
                    generate_fastq_run_statistics['run_stats']['num_clusters_raw'] = int(doc['StatisticsGenerateFASTQ']['RunStats']['NumberOfClustersRaw'])
                except ValueError as e:
                    pass
            if 'NumberOfClustersPF' in doc['StatisticsGenerateFASTQ']['RunStats']:
                try:
                    generate_fastq_run_statistics['run_stats']['num_clusters_passed_filter'] = int(doc['StatisticsGenerateFASTQ']['RunStats']['NumberOfClustersPF'])
                except ValueError as e:
                    pass
            if 'NumberOfUnindexedClusters' in doc['StatisticsGenerateFASTQ']['RunStats']:
                try:
                    generate_fastq_run_statistics['run_stats']['num_unindexed_clusters'] = int(doc['StatisticsGenerateFASTQ']['RunStats']['NumberOfUnindexedClusters'])
                except ValueError as e:
                    pass
            if 'NumberOfUnindexedClustersPF' in doc['StatisticsGenerateFASTQ']['RunStats']:
                try:
                    generate_fastq_run_statistics['run_stats']['num_unindexed_clusters_passed_filter'] = int(doc['StatisticsGenerateFASTQ']['RunStats']['NumberOfUnindexedClustersPF'])
                except ValueError as e:
                    pass

        if 'StatisticsGenerateFASTQ' in doc and 'OverallSamples' in doc['StatisticsGenerateFASTQ']:
            if 'SummarizedSampleStatistics' in doc['StatisticsGenerateFASTQ']['OverallSamples']:
                for sample_stats_record in doc['StatisticsGenerateFASTQ']['OverallSamples']['SummarizedSampleStatistics']:
                    sample_stats = {
                        'sample_name': None,
                        'sample_id': None,
                        'num_clusters_raw': None,
                        'num_clusters_passed_filter': None,
                    }
                    if 'SampleName' in sample_stats_record:
                        sample_stats['sample_name'] = sample_stats_record['SampleName']
                    if 'SampleID' in sample_stats_record:
                        sample_stats['sample_id'] = sample_stats_record['SampleID']
                    if 'NumberOfClustersRaw' in sample_stats_record:
                        try:
                            sample_stats['num_clusters_raw'] = int(sample_stats_record['NumberOfClustersRaw'])
                        except ValueError as e:
                            pass
                    if 'NumberOfClustersPF' in sample_stats_record:
                        try:
                            sample_stats['num_clusters_passed_filter'] = int(sample_stats_record['NumberOfClustersPF'])
                        except ValueError as e:
                            pass
                    generate_fastq_run_statistics['sample_stats'].append(sample_stats)

    return generate_fastq_run_statistics
