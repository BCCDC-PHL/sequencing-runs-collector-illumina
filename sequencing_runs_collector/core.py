import os
import re

import sequencing_runs_collector.illumina as illumina
import sequencing_runs_collector.samplesheet as samplesheet


def get_instrument_info_by_sequencing_run_id(sequencing_run_id):
    """
    """
    miseq_run_id_regex = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
    nextseq_run_id_regex = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"
    gridion_run_id_regex = "\d{8}_\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}"
    promethion_run_id_regex = "\d{8}_\d{4}_P2S_[0-9]{5}-\d{1}_[A-Z0-9]+_[a-z0-9]{8}"

    instrument = {}
    if re.match(miseq_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "ILLUMINA"
        instrument['instrument_model'] = "MISEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(nextseq_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "ILLUMINA"
        instrument['instrument_model'] = "NEXTSEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(gridion_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "NANOPORE"
        instrument['instrument_model'] = "GRIDION"
    elif re.match(promethion_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "NANOPORE"
        instrument['instrument_model'] = "PROMETHION"
    else:
        instrument['instrument_type'] = "UNKNOWN"
        instrument['instrument_model'] = "UNKNOWN"

    return instrument


def run_id_to_date(run_id):
    """
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


def scan(config):
    yield None


def load_illumina_run(config, run):
    """
    """

    run_dir = run['run_dir']
    run_id = os.path.basename(run_dir.rstrip('/'))

    instrument = get_instrument_info_by_sequencing_run_id(run_id)
    
    sequencing_run = {
        'id': run_id,
        'attributes': {},
        'links':[],
    }

    if instrument['instrument_type'] == "ILLUMINA":
        sequencing_run['type'] = "illumina_sequencing_run"
    else:
        exit("Incorrect sequencing run type. This parser only supports illumina runs.")

    run_date = run_id_to_date(run_id)
    sequencing_run['attributes']['run_date'] = run_date
    sequencing_run['attributes']['instrument_id'] = instrument.get('instrument_id')

    
    interop_summary = illumina.get_illumina_interop_summary(run_dir)
    sequencing_run['attributes'].update(interop_summary)

    demultiplexing_output_dirs = illumina.find_demultiplexing_output_dirs(run_dir, instrument['instrument_model'])

    sequencing_run['attributes']['demultiplexings'] = []
    for demultiplexing_output_dir in demultiplexing_output_dirs:
        demultiplexing = {
            'id': None,
            'samplesheet_path': None,
            'sequenced_libraries': [],
        }
        demultiplexing_id = illumina.get_demultiplexing_id(run_id, demultiplexing_output_dir, instrument['instrument_model'])
        demultiplexing['id'] = demultiplexing_id
        samplesheet_path = illumina.find_samplesheet(demultiplexing_output_dir, instrument['instrument_model'])
        demultiplexing['samplesheet_path'] = samplesheet_path
        
        if samplesheet_path is not None:
            parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_path, instrument['instrument_type'], instrument['instrument_model'])

            sequenced_libraries = illumina.get_sequenced_libraries_from_samplesheet(parsed_samplesheet, instrument['instrument_model'], demultiplexing_output_dir, config['project_id_translation'])
            demultiplexing['sequenced_libraries'] = sequenced_libraries

        sequencing_run['attributes']['demultiplexings'].append(demultiplexing)


def load_nanopore_run(config, run):
    """
    """
    pass
