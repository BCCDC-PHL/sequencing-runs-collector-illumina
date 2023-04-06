import datetime
import json


def parse_final_summary(final_summary_path):
    """
    """
    int_fields = [
        'fast5_files_in_final_dest',
        'fast5_files_in_fallback',
        'fastq_files_in_final_dest',
        'fastq_files_in_fallback',
    ]
    bool_fields = [
        'basecalling_enabled',
    ]
    datetime_fields = [
        'started',
        'acquisition_stopped',
        'processing_stopped',
    ]
    final_summary = {}
    with open(final_summary_path, 'r') as f:
        for line in f:
            k, v = line.strip().split('=', 1)
            final_summary[k] = v
        for field in int_fields:
            try:
                final_summary[field] = int(final_summary[field])
            except ValueError as e:
                final_summary[field] = None
            except KeyError as e:
                final_summary[field] = None

        for field in bool_fields:
            try:
                final_summary[field] = bool(final_summary[field])
            except ValueError as e:
                final_summary[field] = None
            except KeyError as e:
                final_summary[field] = None

        for field in datetime_fields:
            try:
                final_summary[field] = datetime.datetime.fromisoformat(final_summary[field])
            except ValueError as e:
                final_summary[field] = None
            except KeyError as e:
                final_summary[field] = None

        # Adjust a few field names to better match our db schema
        field_translation = {
            'instrument': 'instrument_id',
            'started': 'timestamp_acquisition_started',
            'acquisition_stopped': 'timestamp_acquisition_stopped',
            'processing_stopped': 'timestamp_processing_stopped',
            'protocol': 'protocol_id',
            'flow_cell_id': 'flowcell_id',
            
        }

        for original_field, translated_field in field_translation.items():
            final_summary[translated_field] = final_summary[original_field]
            final_summary.pop(original_field)

    return final_summary


def parse_sequencing_run_report(report_path):
    """
    """
    parsed_report = {}
    
    with open(report_path, 'r') as f:
        full_report = json.load(f)
        parsed_report = full_report

    return parsed_report
    

def collect_run_yield_from_run_report(parsed_report):
    """
    """
    run_yield = {
        'num_reads_total': None,
        'num_reads_passed_filter': None,
        'yield_bases': None,
        'yield_gigabases': None,
    }

    if 'acquisitions' in parsed_report:
        acquisitions = parsed_report['acquisitions']
        for acquisition in acquisitions:
            try:
                acquisition_reads = int(acquisition['acquisition_run_info']['yield_summary']['read_count'])
                if run_yield['num_reads_total'] == None:
                    run_yield['num_reads_total'] = acquisition_reads
                else:
                    run_yield['num_reads_total'] += acquisition_reads
                acquisition_reads_passed = int(acquisition['acquisition_run_info']['yield_summary']['basecalled_pass_read_count'])
                if run_yield['num_reads_passed_filter'] == None:
                    run_yield['num_reads_passed_filter'] = acquisition_reads_passed
                else:
                    run_yield['num_reads_passed_filter'] += acquisition_reads_passed
                acquisition_bases = int(acquisition['acquisition_run_info']['yield_summary']['basecalled_pass_bases'])
                if run_yield['yield_bases'] == None:
                    run_yield['yield_bases'] = acquisition_bases
                else:
                    run_yield['yield_bases'] += acquisition_bases
            except KeyError as e:
                pass

        if run_yield['yield_bases'] != None:
            run_yield['yield_gigabases'] = run_yield['yield_bases'] / 1000000000
    return run_yield
