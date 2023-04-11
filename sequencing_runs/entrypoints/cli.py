#!/usr/bin/env python3

import argparse
import glob
import json
import os
import re

from sequencing_runs.parsers import interop
from sequencing_runs.parsers import nanopore
from sequencing_runs.domain import model
from sequencing_runs.adapters import orm
from sequencing_runs.service_layer import services, unit_of_work

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


def collect_nanopore_sequencing_run_info(run_dir):
    """
    """
    run_info = {}
    run_id = os.path.basename(run_dir.rstrip('/'))
    run_id_split = run_id.split('_')
    run_info['sequencing_run_id'] = run_id
    run_info['instrument_id'] = get_nanopore_instrument_id(run_dir)

    sequencing_run_report_files = glob.glob(os.path.join(run_dir, 'report_*.json'))
    final_summary_file = None
    if len(sequencing_run_report_files) > 0:
        # There *should* be only one of these files.
        # If there are more than one, we arbitrarily take the first
        sequencing_run_report_file = sequencing_run_report_files[0]
        if os.path.exists(sequencing_run_report_file):
            sequencing_run_report = nanopore.parse_sequencing_run_report(sequencing_run_report_file)
            flowcell_product_code = sequencing_run_report['protocol_run_info']['flow_cell']['product_code']
            run_info['flowcell_product_code'] = flowcell_product_code
            run_yield = nanopore.collect_run_yield_from_run_report(sequencing_run_report)
            run_info.update(run_yield)
    

    return run_info


def load_run(args):
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
        sequencing_run_info = collect_nanopore_sequencing_run_info(args.run_dir)
        sequencing_run = model.NanoporeSequencingRun(**sequencing_run_info)
        services.add_nanopore_sequencing_run(
            sequencing_run,
            uow=load_sequencing_run_uow,
        )
    
    
    
    

def main(args):
    config = load_config(args.config)

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
