import csv
import json
import logging
import os
import re

from typing import Iterable, Optional
from pathlib import Path

import sequencing_runs_collector.illumina as illumina
import sequencing_runs_collector.nanopore as nanopore
import sequencing_runs_collector.parsers.samplesheet as samplesheet


def get_instrument_info_by_sequencing_run_id(sequencing_run_id):
    """
    Get instrument info by sequencing run ID.

    :param sequencing_run_id: Sequencing run ID
    :type sequencing_run_id: str
    :return: Instrument info
    :rtype: dict[str, str]
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
    Runs are found by matching sub-directory names against the following regexes: `"\\d{6}_M\\d{5}_\\d+_\\d{9}-[A-Z0-9]{5}"` (MiSeq) and `"\\d{6}_VH\\d{5}_\\d+_[A-Z0-9]{9}"` (NextSeq)

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
    Collect data for an Illumina sequencing run.

    :param config: Application config.
    :type config: dict[str, object]
    :param run: Run directory. Keys: [run_id, run_dir]
    :type run: dict[str, object]
    :return: Sequencing run data. Keys: [sequencing_run_id, flowcell_id, run_date, instrument_id, reads, clusters, yield, demultiplexings]
    :rtype: dict[str, object]
    """

    run_dir = run['run_dir']
    run_id = os.path.basename(run_dir.rstrip('/'))
    flowcell_id = run_id.split('_')[-1]
    instrument = get_instrument_info_by_sequencing_run_id(run_id)
    
    sequencing_run = {
        'sequencing_run_id': run_id,
        'flowcell_id': flowcell_id,
    }

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
            'demultiplexing_num': None,
            'samplesheet_path': None,
            'fastq_dir_path': None,
            'timestamp_demultiplexing_started': None,
            'sequenced_libraries': [],
        }
        demultiplexing_num = illumina.get_demultiplexing_num(run_id, demultiplexing_output_dir, instrument['instrument_model'])
        demultiplexing['demultiplexing_num'] = demultiplexing_num
        demultiplexing_id = '-'.join([run_id, "DEMUX", str(demultiplexing_num)])
        demultiplexing['demultiplexing_id'] = demultiplexing_id
        demultiplexing_start_timestamp = illumina.get_demultiplexing_start_timestamp(run_id, Path(demultiplexing_output_dir), instrument['instrument_model'])
        demultiplexing['timestamp_demultiplexing_started'] = demultiplexing_start_timestamp
        samplesheet_path = illumina.find_samplesheet(demultiplexing_output_dir, instrument['instrument_model'])
        if samplesheet_path is not None:
            samplesheet_path_relative = os.path.relpath(samplesheet_path, run_dir)
        else:
            samplesheet_path_relative = None
        demultiplexing['samplesheet_path'] = samplesheet_path_relative
        fastq_dir = illumina.find_fastq_output_dir(demultiplexing_output_dir, instrument['instrument_model'])
        demultiplexing['fastq_dir_path'] = os.path.relpath(fastq_dir, run_dir)

        if samplesheet_path is not None:
            parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_path, instrument['instrument_type'], instrument['instrument_model'])
            if instrument['instrument_model'].upper() == "MISEQ":
                sequencing_run['experiment_name'] = parsed_samplesheet.get('header', {}).get('experiment_name', None)
            elif instrument['instrument_model'].upper() == "NEXTSEQ":
                sequencing_run['experiment_name'] = parsed_samplesheet.get('header', {}).get('run_name', None)

            collect_fastq_stats = config.get('collect_fastq_stats', False)
            num_fastq_stats_collection_processes = config.get('num_fastq_stats_collection_processes', 1)
            sequenced_libraries = illumina.get_sequenced_libraries_from_samplesheet(parsed_samplesheet, instrument['instrument_model'], demultiplexing_output_dir, config['project_id_translation'], collect_fastq_stats, num_fastq_stats_collection_processes)
            demultiplexing['sequenced_libraries'] = sequenced_libraries

        sequencing_run['demultiplexings'].append(demultiplexing)

    return sequencing_run


def collect_nanopore_run(config, run):
    """
    """
    sequencing_run = {}
    sequencing_run_id = run['run_id']
    instrument_type = run['instrument_type']
    instrument_model = run['instrument_model']
    run_dir = run['run_dir']

    sequencing_run['sequencing_run_id'] = sequencing_run_id

    run_date = run_id_to_date(sequencing_run_id)
    sequencing_run['run_date'] = run_date

    samplesheet_path = nanopore.find_samplesheet(run_dir, instrument_model)
    if not samplesheet_path:
        logging.error(json.dumps({
            'event_type': 'failed_to_find_samplesheet',
            'sequencing_run_id': sequencing_run_id,
            'run_dir': run_dir,
        }))
        return sequencing_run
    
    parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_path, instrument_type, instrument_model)
    if not parsed_samplesheet:
        logging.error(json.dumps({
            'event_type': 'failed_to_parse_samplesheet',
            'sequencing_run_id': sequencing_run_id,
            'run_dir': run_dir,
        }))
        return sequencing_run

    sequencing_run['sequenced_libraries'] = []
    for samplesheet_row in parsed_samplesheet:
        sequenced_library = {
            'alias': samplesheet_row.get('alias', None),
            'library_id': samplesheet_row.get('library_id', None),
            'project_id': samplesheet_row.get('project_id', None),
            'barcode': samplesheet_row.get('barcode', None),
        }
        sequencing_run['sequenced_libraries'].append(sequenced_library)
    
    report_json_path = nanopore.find_report_json(run_dir, instrument_type)
    if not report_json_path:
        logging.error(json.dumps({
            'event_type': 'failed_to_find_report_json',
            'sequencing_run_id': sequencing_run_id,
            'run_dir': run_dir,
        }))
        return sequencing_run
        
    parsed_report_json = nanopore.parse_report_json(report_json_path)

    return sequencing_run


def write_collected_illumina_run(collected_run: dict, run_output_path: Path):
    """
    """
    sequencing_run_id = collected_run['sequencing_run_id']

    run_summary_output_fieldnames = [
        "sequencing_run_id",
        "flowcell_id",
        "run_date",
        "instrument_id",
        "experiment_name",
        "num_cycles_r1",
        "num_cycles_r2",
        "cluster_count",
        "cluster_count_passed_filter",
        "error_rate",
        "first_cycle_intensity",
        "percent_aligned",
        "q30_percent",
        "projected_yield_gigabases",
        "yield_gigabases",
        "num_reads",
        "num_reads_passed_filter",
        "percent_clusters_passed_filter",
        "cluster_density",
        "cluster_density_passed_filter",
    ]

    run_summary_output_path = os.path.join(run_output_path, f"{sequencing_run_id}_run_summary.csv")
    with open(run_summary_output_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=run_summary_output_fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
        writer.writeheader()
        writer.writerow(collected_run)

    run_demultiplexings_output_path = os.path.join(run_output_path, 'demultiplexings')
    os.makedirs(run_demultiplexings_output_path, exist_ok=True)

    demultiplexing_output_fieldnames = [
        "sequencing_run_id",
        "demultiplexing_id",
        "demultiplexing_num",
        "samplesheet_path",
        "fastq_dir_path",
        "timestamp_demultiplexing_started"
    ]
    sequenced_libraries_output_fieldnames = [
        "sequencing_run_id",
        "demultiplexing_id",
        "library_id",
        "project_id_samplesheet",
        "project_id_translated",
        "index",
        "index2",
        "fastq_filename_r1",
        "fastq_filename_r2",
        "sample_number",
        "q30_percent_r1",
        "q30_percent_last_25_bases_r1",
        "fastq_md5_r1",
        "fastq_file_size_mb_r1",
        "q30_percent_r2",
        "q30_percent_last_25_bases_r2",
        "fastq_md5_r2",
        "fastq_file_size_mb_r2",
        "num_reads",
        "num_bases",
        "q30_percent",
        "q30_percent_last_25_bases",
    ]
    for demultiplexing in collected_run['demultiplexings']:
        demultiplexing['sequencing_run_id'] = sequencing_run_id
        demultiplexing_id = demultiplexing['demultiplexing_id']
        demultiplexing_output_dir = os.path.join(
            run_demultiplexings_output_path,
            demultiplexing_id,
        )
        os.makedirs(demultiplexing_output_dir, exist_ok=True)
        demultiplexing_output_path = os.path.join(
            demultiplexing_output_dir,
            f"{demultiplexing_id}_demultiplexing.csv",
        )
        with open(demultiplexing_output_path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=demultiplexing_output_fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
            writer.writeheader()
            writer.writerow(demultiplexing)

        sequenced_libraries_output_path = os.path.join(
            demultiplexing_output_dir,
            f"{demultiplexing_id}_sequenced_libraries.csv"
        )
        with open(sequenced_libraries_output_path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=sequenced_libraries_output_fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
            writer.writeheader()
            for sequenced_library in demultiplexing['sequenced_libraries']:
                sequenced_library['sequencing_run_id'] = sequencing_run_id
                sequenced_library['demultiplexing_id'] = demultiplexing_id
                writer.writerow(sequenced_library)
        
            
        

    
def write_collected_nanopore_run(collected_run: dict, run_output_path: Path):
    """
    """
    
    sequencing_run_id = collected_run['sequencing_run_id']

    run_summary_output_fieldnames = [
        'sequencing_run_id',
        'flowcell_id',
        'flowcell_product_code',
        'run_date',
        'instrument_id',
        'protocol_id',
        'protocol_run_id',
        'flowcell_channel_count'
    ]
    

    run_summary_output_path = os.path.join(run_output_path, f"{sequencing_run_id}_run_summary.csv")
    print(json.dumps(collected_run, indent=2))
    with open(run_summary_output_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=run_summary_output_fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
        writer.writeheader()
        writer.writerow(collected_run)
