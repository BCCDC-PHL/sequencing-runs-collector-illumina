#!/usr/bin/env python3

import argparse
import datetime
import glob
import json
import os
import re

import pytz

from sequencing_runs.parsers import interop
from sequencing_runs.parsers import nanopore
from sequencing_runs.domain import model
from sequencing_runs.adapters import orm
from sequencing_runs.service_layer import services, unit_of_work


DEFAULT_LOCAL_TIMEZONE = "America/Vancouver"

def load_config(config_path):
    """
    """
    config = {}
    with open(config_path, 'r') as f:
        config = json.load(f)

    return config


def get_instrument_info_by_sequencing_run_id(sequencing_run_id):
    """
    """
    miseq_run_id_regex = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
    nextseq_run_id_regex = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"
    gridion_run_id_regex = "\d{8}_\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}"
    promethion_run_id_regex = "\d{8}_\d{4}_P2S_[0-9]{5}-\d{1}_[A-Z0-9]+_[a-z0-9]{8}"

    instrument = {}
    if re.match(miseq_run_id_regex, sequencing_run_id):
        instrument['type'] = "ILLUMINA"
        instrument['model'] = "MISEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(nextseq_run_id_regex, sequencing_run_id):
        instrument['type'] = "ILLUMINA"
        instrument['model'] = "NEXTSEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(gridion_run_id_regex, sequencing_run_id):
        instrument['type'] = "NANOPORE"
        instrument['model'] = "GRIDION"
    elif re.match(promethion_run_id_regex, sequencing_run_id):
        instrument['type'] = "NANOPORE"
        instrument['model'] = "PROMETHION"

    return instrument


def get_nanopore_instrument_id(sequencing_run_dir_path):
    """
    """
    instrument_id = None
    final_summary_files = glob.glob(os.path.join(args.run_dir, 'final_summary_*.txt'))
    final_summary_file = None
    if len(final_summary_files) > 0:
        # There *should* be only one of these files.
        # If there are more than one, we arbitrarily take the first
        final_summary_file = final_summary_files[0]
        if os.path.exists(final_summary_file):
            final_summary = nanopore.parse_final_summary(final_summary_file)
            instrument_id = final_summary['instrument_id']

    return instrument_id


def collect_illumina_sequencing_run_info(run_dir):
    """
    """
    run_info = {}
    run_id = os.path.basename(run_dir.rstrip('/'))
    run_id_split = run_id.split('_')
    run_info['sequencing_run_id'] = run_id
    run_info['instrument_id'] = run_id_split[1]
    run_info['flowcell_id'] = run_id_split[-1]
    interop_summary = interop.summary_nonindex(run_dir)
    run_info.update(interop_summary)

    return run_info


def collect_nanopore_sequencing_run_info(config, run_dir):
    """
    """
    run_info = {}
        
    local_timezone = DEFAULT_LOCAL_TIMEZONE
    if 'local_timezone' in config:
        local_timezone = pytz.timezone(config['local_timezone'])

    run_id = os.path.basename(run_dir.rstrip('/'))
    run_id_split = run_id.split('_')
    run_info['sequencing_run_id'] = run_id
    run_info['instrument_id'] = get_nanopore_instrument_id(run_dir)

    sequencing_run_report_files = glob.glob(os.path.join(args.run_dir, 'report_*.json'))
    sequencing_run_report_file = None
    if len(sequencing_run_report_files) > 0:
        # There *should* be only one of these files.
        # If there are more than one, we arbitrarily take the first
        sequencing_run_report_file = sequencing_run_report_files[0]
        if os.path.exists(sequencing_run_report_file):
            sequencing_run_report = nanopore.parse_sequencing_run_report(sequencing_run_report_file)
            instrument_id = sequencing_run_report['host']['serial']
            run_info['instrument_id'] = instrument_id
            protocol_id = sequencing_run_report['protocol_run_info']['protocol_id']
            run_info['protocol_id'] = protocol_id
            protocol_run_id = sequencing_run_report['protocol_run_info']['run_id']
            run_info['protocol_run_id'] = protocol_run_id
            protocol_run_start_time = sequencing_run_report['protocol_run_info']['start_time']
            # TODO: Move this timestamp parsing logic into the run report parser?
            if protocol_run_start_time and protocol_run_start_time.endswith('Z'):
                start_time_nanoseconds = protocol_run_start_time.split('.', 1)[1].rstrip('Z')
                start_time_microseconds = start_time_nanoseconds[0:6]
                start_time = protocol_run_start_time.split('.')[0] + '.' + start_time_microseconds + '+00:00'
                try:
                    run_info['timestamp_protocol_run_started'] = datetime.datetime.fromisoformat(start_time)
                except ValueError as e:
                    pass
            protocol_run_end_time = sequencing_run_report['protocol_run_info']['end_time']
            if protocol_run_end_time and protocol_run_end_time.endswith('Z'):
                end_time_nanoseconds = protocol_run_end_time.split('.', 1)[1].rstrip('Z')
                end_time_microseconds = end_time_nanoseconds[0:6]
                end_time = protocol_run_end_time.split('.')[0] + '.' + end_time_microseconds + '+00:00'
                try:
                    run_info['timestamp_protocol_run_ended'] = datetime.datetime.fromisoformat(end_time)
                except ValueError as e:
                    pass
            flowcell_id = sequencing_run_report['protocol_run_info']['flow_cell']['flow_cell_id']
            run_info['flowcell_id'] = flowcell_id
            flowcell_product_code = sequencing_run_report['protocol_run_info']['flow_cell']['product_code']
            run_info['flowcell_product_code'] = flowcell_product_code
            run_yield = nanopore.collect_run_yield_from_run_report(sequencing_run_report)
            run_info.update(run_yield)
            run_info['acquisition_runs'] = []
            utc_datetime_keys = [
                'timestamp_protocol_run_started',
                'timestamp_protocol_run_ended',
            ]
            for k in utc_datetime_keys:
                run_info[k] = run_info[k].replace(tzinfo=pytz.utc).astimezone(local_timezone)
            acquisition_runs = nanopore.collect_acquisition_runs_from_run_report(sequencing_run_report)
            for acquisition_run in acquisition_runs:
                acquisition_run['sequencing_run_id'] = run_id
                utc_datetime_keys = [
                    'timestamp_acquisition_started',
                    'timestamp_acquisition_ended',
                ]
                for k in utc_datetime_keys:
                    acquisition_run[k] = acquisition_run[k].replace(tzinfo=pytz.utc).astimezone(local_timezone)
                    
                run_info['acquisition_runs'].append(acquisition_run)

    return run_info


def load_run(args):
    config = load_config(args.config)
    sequencing_run_id = os.path.basename(args.run_dir.rstrip('/'))
    instrument_info = get_instrument_info_by_sequencing_run_id(sequencing_run_id)
    
    if instrument_info['type'] == "ILLUMINA":
        load_instrument_uow = unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork()
        instrument = model.IlluminaInstrument(**instrument_info)
        services.add_illumina_instrument(
            instrument,
            uow=load_instrument_uow,
        )
    elif instrument_info['type'] == "NANOPORE":
        load_instrument_uow = unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork()
        # Instrument ID isn't available directly from sequencing run ID for
        # nanopore runs.
        instrument_id = get_nanopore_instrument_id(args.run_dir)
        instrument_info['instrument_id'] = instrument_id
        instrument = model.NanoporeInstrument(**instrument_info)
        services.add_nanopore_instrument(
            instrument,
            uow=load_instrument_uow,
        )

    if instrument_info['type'] == "ILLUMINA":
        load_sequencing_run_uow = unit_of_work.SqlAlchemyIlluminaSequencingRunUnitOfWork()
        sequencing_run_info = collect_illumina_sequencing_run_info(args.run_dir)
        sequencing_run = model.IlluminaSequencingRun(**sequencing_run_info)
        services.add_illumina_sequencing_run(
            sequencing_run,
            uow=load_sequencing_run_uow,
        )
    elif instrument_info['type'] == "NANOPORE":
        load_sequencing_run_uow = unit_of_work.SqlAlchemyNanoporeSequencingRunUnitOfWork()
        sequencing_run_info = collect_nanopore_sequencing_run_info(config, args.run_dir)
        if 'acquisition_runs' in sequencing_run_info:
            for idx, acquisition_run in enumerate(sequencing_run_info['acquisition_runs']):
                sequencing_run_info['acquisition_runs'][idx] = model.NanoporeAcquisitionRun(**sequencing_run_info['acquisition_runs'][idx])
        sequencing_run = model.NanoporeSequencingRun(**sequencing_run_info)
        services.add_nanopore_sequencing_run(
            sequencing_run,
            uow=load_sequencing_run_uow,
        )
    
    
    
    

def main(args):

    orm.start_mappers()

    if args.load_run:
        load_run(args)
    

    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(help='sub-command help')
    parser_load = sub_parsers.add_parser('load', help='')
    parser_load.add_argument('load_run', action='store_const', const=True)
    parser_load.add_argument('run_dir', help='A run directory')
    parser_load.add_argument('-c', '--config')
    args = parser.parse_args()
    main(args)
