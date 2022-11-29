import csv
import json
import re


def parse_primary_analysis_metrics_nextseq_v1(primary_analysis_metrics_path):
    field_translation = {
        'Average %Q30': 'average_percent_q30',
        'Total Yield': 'total_yield_gigabases',
        'Total Reads PF': 'total_reads_passed_filter',
        '% Loading Concentration': 'percent_loading_concentration',
    }
    metrics = {}
    with open(primary_analysis_metrics_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(json.dumps(row, indent=2))
            for field in field_translation:
                if re.match(field, row['Metric']):
                    translated_field = field_translation[field]
                    metrics[translated_field] = float(row[' Value'].strip())

    return metrics
        
