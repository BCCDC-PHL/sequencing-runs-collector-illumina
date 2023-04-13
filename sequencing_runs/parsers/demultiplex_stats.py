import csv

def parse_demultiplex_stats(demultiplex_stats_path):
    field_translation = {
        'SampleID': 'library_id',
        'Index': 'index',
        '# Reads': 'num_reads',
        '# Perfect Index Reads': 'num_perfect_index_reads',
        '# One Mismatch Index Reads': 'num_one_mismatch_index_reads',
        '# of >= Q30 Bases (PF)': 'num_bases_above_q30',
        'Mean Quality Score (PF)': 'mean_quality_score',
    }
    int_fields = [
        'num_reads',
        'num_perfect_index_reads',
        'num_one_mismatch_index_reads',
        'num_bases_above_q30',
    ]
    float_fields = [
        'mean_quality_score',
    ]
    demultiplex_stats = []
    with open(demultiplex_stats_path, 'r') as f:
        reader = csv.DictReader(f, dialect='unix')
        for row in reader:
            demultiplex_stats_record = {
                'num_reads': None,
                'num_perfect_index_reads': None,
                'num_one_mismatch_index_reads': None,
                'num_bases_above_q30': None,
                'mean_quality_score': None,
            }
            for k, v in field_translation.items():
                demultiplex_stats_record[v] = row[k]
            for field in int_fields:
                try:
                    demultiplex_stats_record[field] = int(demultiplex_stats_record[field])
                except ValueError as e:
                    demultiplex_stats_record[field] = None
            for field in float_fields:
                try:
                    demultiplex_stats_record[field] = float(demultiplex_stats_record[field])
                except ValueError as e:
                    demultiplex_stats_record[field] = None

            demultiplex_stats.append(demultiplex_stats_record)

    return demultiplex_stats
