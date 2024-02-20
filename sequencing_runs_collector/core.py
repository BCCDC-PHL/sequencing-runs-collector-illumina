import json
import logging
import os
import re
import requests

from typing import Iterable, Optional


import sequencing_runs_collector.illumina as illumina
import sequencing_runs_collector.nanopore as nanopore
import sequencing_runs_collector.parsers.samplesheet as samplesheet


def get_instrument_info_by_sequencing_run_id(sequencing_run_id):
    """
    """
    instrument = {}
    if re.match(illumina.MISEQ_RUN_ID_REGEX, sequencing_run_id):
        instrument['instrument_type'] = "ILLUMINA"
        instrument['instrument_model'] = "MISEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(illumina.NEXTSEQ_RUN_ID_REGEX, sequencing_run_id):
        instrument['instrument_type'] = "ILLUMINA"
        instrument['instrument_model'] = "NEXTSEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(nanopore.GRIDION_RUN_ID_REGEX, sequencing_run_id):
        instrument['instrument_type'] = "NANOPORE"
        instrument['instrument_model'] = "GRIDION"
    elif re.match(nanopore.PROMETHION_RUN_ID_REGEX, sequencing_run_id):
        instrument['instrument_type'] = "NANOPORE"
        instrument['instrument_model'] = "PROMETHION"
    else:
        instrument['instrument_type'] = "UNKNOWN"
        instrument['instrument_model'] = "UNKNOWN"

    return instrument


def run_id_to_date(run_id):
    """
    Generate an ISO8601-formatted date from the run ID.

    :param run_id: Sequencing run ID
    :type run_id: str
    :return: ISO8601-formatted date
    :rtype: str
    """
    run_date = None
    run_id_date_component = run_id.split('_')[0]
    if len(run_id_date_component) == 6:
        six_digit_date = run_id.split('_')[0]
        two_digit_year = six_digit_date[0:2]
        four_digit_year = "20" + two_digit_year
        two_digit_month = six_digit_date[2:4]
        two_digit_day = six_digit_date[4:6]
        run_date = '-'.join([four_digit_year, two_digit_month, two_digit_day])
    elif len(run_id_date_component) == 8:
        eight_digit_date = run_id.split('_')[0]
        four_digit_year = eight_digit_date[0:4]
        two_digit_month = eight_digit_date[4:6]
        two_digit_day = eight_digit_date[6:8]
        run_date = '-'.join([four_digit_year, two_digit_month, two_digit_day])

    return run_date


def find_runs(config: dict[str, object]) -> Iterable[Optional[dict[str, object]]]:
    """
    Find all sequencing runs under all of the `run_parent_dirs` from the config.
    Runs are found by matching sub-directory names against the following regexes: `"\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"` (MiSeq) and `"\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"` (NextSeq)

    :param config: Application config.
    :type config: dict[str, object]
    :return: Dictionary of sequencin run info, indexed by sequencing run ID.
    :rtype: Iterable[dict[str, object]]
    """
    run = {}
    run_parent_dirs = config.get('run_parent_dirs', None)
    if run_parent_dirs is not None:
        for run_parent_dir in run_parent_dirs:
            if run_parent_dir is not None and os.path.exists(run_parent_dir):
                subdirs = os.scandir(run_parent_dir)
                for subdir in subdirs:
                    run = {}
                    instrument_type = None
                    instrument_model = None
                    run_id = subdir.name
                    if re.match(illumina.MISEQ_RUN_ID_REGEX, run_id):
                        instrument_type = "ILLUMINA"
                        instrument_model = "MISEQ"
                    elif re.match(illumina.NEXTSEQ_RUN_ID_REGEX, run_id):
                        instrument_type = "ILLUMINA"
                        instrument_model = "NEXTSEQ"
                    elif re.match(nanopore.GRIDION_RUN_ID_REGEX, run_id):
                        instrument_type = "NANOPORE"
                        instrument_model = "GRIDION"
                    elif re.match(nanopore.PROMETHION_RUN_ID_REGEX, run_id):
                        instrument_type = "NANOPORE"
                        instrument_model = "PROMETHION"
                    else:
                        logging.info(json.dumps({'event_type': 'sequencing_run_skipped', 'directory': subdir.path}))
                        yield None
                    if subdir.is_dir() and instrument_model != None and os.path.exists(os.path.join(subdir.path, "upload_complete.json")):
                        logging.debug(json.dumps({"event_type": "sequencing_run_found", "sequencing_run_id": run_id}))
                        run = {
                            "run_id": run_id,
                            "instrument_type": instrument_type,
                            "instrument_model": instrument_model,
                            "run_dir": subdir.path,
                        }

                        yield run


def scan(config):
    """
    Scanning involves looking for all existing runs...

    :param config: Application config.
    :type config: dict[str, object]
    :return: None
    :rtype: NoneType
    """
    logging.info(json.dumps({"event_type": "scan_start"}))

    logging.debug(json.dumps({"event_type": "find_runs_start"}))
    num_runs_found = 0
    for run in find_runs(config):
        if run is not None:
            yield run

    logging.info(json.dumps({"event_type": "find_and_store_runs_complete", "num_runs_found": num_runs_found}))


def collect_illumina_run(config, run):
    """
    
    """

    run_dir = run['run_dir']
    run_id = os.path.basename(run_dir.rstrip('/'))
    flowcell_id = run_id.split('_')[-1]
    instrument = get_instrument_info_by_sequencing_run_id(run_id)
    
    sequencing_run = {
        'sequencing_run_id': run_id,
        'flowcell_id': flowcell_id,
    }

    if instrument['instrument_type'] == "ILLUMINA":
        sequencing_run['type'] = "illumina_sequencing_run"
    else:
        exit("Incorrect sequencing run type. This parser only supports illumina runs.")

    run_date = run_id_to_date(run_id)
    sequencing_run['run_date'] = run_date
    sequencing_run['instrument_id'] = instrument.get('instrument_id')

    
    interop_summary = illumina.get_illumina_interop_summary(run_dir)
    sequencing_run.update(interop_summary)
    runinfo = illumina.get_runinfo(run_dir)
    sequencing_run.update(runinfo)

    demultiplexing_output_dirs = illumina.find_demultiplexing_output_dirs(run_dir, instrument['instrument_model'])

    sequencing_run['demultiplexings'] = []
    for demultiplexing_output_dir in demultiplexing_output_dirs:
        demultiplexing = {
            'demultiplexing_id': None,
            'samplesheet_path': None,
            'sequenced_libraries': [],
        }
        demultiplexing_id = illumina.get_demultiplexing_id(run_id, demultiplexing_output_dir, instrument['instrument_model'])
        demultiplexing['demultiplexing_id'] = demultiplexing_id
        samplesheet_path = illumina.find_samplesheet(demultiplexing_output_dir, instrument['instrument_model'])
        demultiplexing['samplesheet_path'] = samplesheet_path
        
        if samplesheet_path is not None:
            parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_path, instrument['instrument_type'], instrument['instrument_model'])

            sequenced_libraries = illumina.get_sequenced_libraries_from_samplesheet(parsed_samplesheet, instrument['instrument_model'], demultiplexing_output_dir, config['project_id_translation'])
            demultiplexing['sequenced_libraries'] = sequenced_libraries

        sequencing_run['demultiplexings'].append(demultiplexing)

    return sequencing_run


def submit_illumina_run(config, run):
    """
    """
    base_url = config.get('api_root', None)
    api_token = config.get('api_token', None)
    response = None
    run_id = run.get('id', None)
    if base_url is not None and api_token is not None:
        base_url = base_url.rstrip('/')
        headers = {
            'Authorization': "Bearer " + api_token,
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json',
        }
        url = '/'.join([base_url, 'sequencing-runs', 'illumina'])
        try:
            request_body = {
                'data': run,
                'links': {},
            }
            if config['dry_run']:
                print(json.dumps(request_body, indent=2))
            else:
                response = requests.post(url, headers=headers, json=request_body)
        except requests.exceptions.ConnectionError as e:
            logging.error(json.dumps({'event_type': 'run_submission_failed', 'sequencing_run_id': run_id, 'error_message': str(e)}))
    if response is not None:
        if response.ok:
            logging.info(json.dumps({'event_type': 'run_submission_succeeded', 'sequencing_run_id': run_id, 'status_code': response.status_code, 'reason': response.reason}))
        else:
            logging.error(json.dumps({'event_type': 'run_submission_failed', 'sequencing_run_id': run_id, 'status_code': response.status_code, 'reason': response.reason}))


def submit_nanopore_run(config, run):
    """
    """
    base_url = config.get('api_root', None)
    api_token = config.get('api_token', None)
    response = None
    run_id = run.get('id', None)
    if base_url is not None and api_token is not None:
        base_url = base_url.rstrip('/')
        headers = {
            'Authorization': "Bearer " + api_token,
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json',
        }
        url = '/'.join([base_url, 'sequencing-runs', 'nanopore'])
        try:
            request_body = {
                'data': run,
                'links': {},
            }
            if config['dry_run']:
                print(json.dumps(request_body, indent=2))
            else:
                response = requests.post(url, headers=headers, json=request_body)
        except requests.exceptions.ConnectionError as e:
            logging.error(json.dumps({'event_type': 'run_submission_failed', 'sequencing_run_id': run_id, 'error_message': str(e)}))
    if response is not None:
        if response.ok:
            logging.info(json.dumps({'event_type': 'run_submission_succeeded', 'sequencing_run_id': run_id, 'status_code': response.status_code, 'reason': response.reason}))
        else:
            logging.error(json.dumps({'event_type': 'run_submission_failed', 'sequencing_run_id': run_id, 'status_code': response.status_code, 'reason': response.reason}))

