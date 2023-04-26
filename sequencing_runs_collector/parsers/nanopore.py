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
                final_summary[field] = str(datetime.datetime.fromisoformat(final_summary[field]))
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


def collect_acquisition_runs_from_run_report(run_report):
    """
    """
    acquisitions = []
    if 'acquisitions' in run_report:
        for acquisition in run_report['acquisitions']:
            a = {
                'acquisition_run_id': None,
                'timestamp_acquisition_started': None,
                'timestamp_acquisition_ended': None,
                'num_reads_total': None,
                'num_reads_passed_filter': None,
                'percent_reads_passed_filter': None,
                'num_reads_skipped': None,
                'num_bases_passed_filter': None,
                'basecalling_config_filename': None,
            }
            # TODO: separate out some of this into separate try/except
            # Currently, it 'short-circuits' if any field fails to parse
            try:
                a['acquisition_run_id'] = acquisition['acquisition_run_info']['run_id']
                a['num_reads_total'] = int(acquisition['acquisition_run_info']['yield_summary']['read_count'])
                a['num_reads_passed_filter'] = int(acquisition['acquisition_run_info']['yield_summary']['basecalled_pass_read_count'])
                a['num_reads_skipped'] = int(acquisition['acquisition_run_info']['yield_summary']['basecalled_skipped_read_count'])
                if a['num_reads_total'] > 0:
                    a['percent_reads_passed_filter'] = a['num_reads_passed_filter'] / a['num_reads_total'] * 100
                else:
                    a['percent_reads_passed_filter'] = 0.0
                num_bases_passed = int(acquisition['acquisition_run_info']['yield_summary']['basecalled_pass_bases'])
                num_bases_failed = int(acquisition['acquisition_run_info']['yield_summary']['basecalled_fail_bases'])
                num_bases_total = num_bases_passed + num_bases_failed
                a['num_bases_total'] = num_bases_total
                a['num_bases_passed_filter'] = num_bases_passed
                if num_bases_total > 0:
                    a['percent_bases_passed_filter'] = a['num_bases_passed_filter'] / a['num_bases_total'] * 100
                else:
                    a['percent_bases_passed_filter'] = 0.0

                # TODO: Clean up this timestamp parsing logic. This is a bit messy/flaky
                start_time = acquisition['acquisition_run_info']['start_time']
                if start_time and start_time.endswith('Z'):
                    start_time_nanoseconds = start_time.split('.', 1)[1].rstrip('Z')
                    start_time_microseconds = start_time_nanoseconds[0:6]
                    start_time = start_time.split('.')[0] + '.' + start_time_microseconds + '+00:00'
                    try:
                        a['timestamp_acquisition_started'] = datetime.datetime.fromisoformat(start_time)
                    except ValueError as e:
                        pass
                end_time = acquisition['acquisition_run_info']['end_time']
                if end_time and end_time.endswith('Z'):
                    end_time_nanoseconds = end_time.split('.', 1)[1].rstrip('Z')
                    end_time_microseconds = end_time_nanoseconds[0:6]
                    end_time = start_time.split('.')[0] +  '.' + end_time_microseconds + '+00:00'
                    try:
                        a['timestamp_acquisition_ended'] = datetime.datetime.fromisoformat(end_time)
                    except ValueError as e:
                        pass
                a['startup_state'] = acquisition['acquisition_run_info']['startup_state']
                a['state'] = acquisition['acquisition_run_info']['state']
                a['finishing_state'] = acquisition['acquisition_run_info']['finishing_state']
                a['stop_reason'] = acquisition['acquisition_run_info']['stop_reason']
                a['basecalling_config_filename'] = acquisition['acquisition_run_info']['config_summary']['basecalling_config_filename']
                a['purpose'] = acquisition['acquisition_run_info']['config_summary']['purpose']
                a['events_to_base_ratio'] = float(acquisition['acquisition_run_info']['config_summary']['events_to_base_ratio'])
                a['sample_rate'] = int(acquisition['acquisition_run_info']['config_summary']['sample_rate'])
                a['channel_count'] = int(acquisition['acquisition_run_info']['config_summary']['channel_count'])
            except KeyError as e:
                pass
            except ValueError as e:
                pass

            acquisitions.append(a)
            
    return acquisitions
