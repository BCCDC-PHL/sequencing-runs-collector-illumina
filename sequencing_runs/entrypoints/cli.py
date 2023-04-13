#!/usr/bin/env python3

import argparse
import datetime
import glob
import json
import os
import re

import pytz

from sequencing_runs.parsers import generate_fastq_run_statistics
from sequencing_runs.parsers import interop
from sequencing_runs.parsers import rta_configuration
from sequencing_runs.parsers import demultiplex_stats
from sequencing_runs.parsers import samplesheet
from sequencing_runs.parsers import nanopore
from sequencing_runs.domain import model
from sequencing_runs.adapters import orm
from sequencing_runs.service_layer import services, unit_of_work


DEFAULT_LOCAL_TIMEZONE = "America/Vancouver"
MISEQ_RUN_ID_REGEX = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
NEXTSEQ_RUN_ID_REGEX = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"
GRIDION_RUN_ID_REGEX = "\d{8}_\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}"
PROMETHION_RUN_ID_REGEX = "\d{8}_\d{4}_P2S_[0-9]{5}-\d{1}_[A-Z0-9]+_[a-z0-9]{8}"

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
    instrument = {}
    if re.match(MISEQ_RUN_ID_REGEX, sequencing_run_id):
        instrument['type'] = "ILLUMINA"
        instrument['model'] = "MISEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(NEXTSEQ_RUN_ID_REGEX, sequencing_run_id):
        instrument['type'] = "ILLUMINA"
        instrument['model'] = "NEXTSEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(GRIDION_RUN_ID_REGEX, sequencing_run_id):
        instrument['type'] = "NANOPORE"
        instrument['model'] = "GRIDION"
    elif re.match(PROMETHION_RUN_ID_REGEX, sequencing_run_id):
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


def miseq_run_dir_is_new_structure(run_dir):
    """
    Determine if a MiSeq run dir uses the 'new' directory structure
    or not. The new directorty structure supports multiple demultiplexing
    outputs, in directories named like 'Alignment_1', 'Alignment_2', etc.
    """
    is_new_structure = False
    includes_alignment_subdirs = False
    run_dir_contents = os.listdir(run_dir)
    for content in run_dir_contents:
        if content.startswith('Alignment_'):
            includes_alignment_subdirs = True

    if includes_alignment_subdirs:
        is_new_structure = True

    return is_new_structure


def find_illumina_samplesheet(run_dir, demultiplexing_id):
    """
    Depending on the instrument model and directory structure, we may
    find the SampleSheet for a given demultiplexing in different locations.
    """
    samplesheet_path = None
    run_id = os.path.basename(run_dir.rstrip('/'))
    if re.match(MISEQ_RUN_ID_REGEX, run_id):
        if miseq_run_dir_is_new_structure(run_dir):
            alignment_subdir = os.path.join(run_dir, 'Alignment_' + demultiplexing_id)
            alignment_subdir_timestamp_subdirs = os.listdir(alignment_subdir)
            if len(alignment_subdir_timestamp_subdirs) > 0:
                # Not sure if there are ever multiple timestamp subdirs per alignment subdir
                # We arbitrarily take the last one.
                alignment_subdir_timestamp_subdir = alignment_subdir_timestamp_subdirs[-1]
                samplesheet_path = os.path.join(alignment_subdir_timestamp_subdir, 'SampleSheetUsed.csv')
        else:
            
            rta_config_path = os.path.join(run_dir, 'Data', 'Intensities', 'RTAConfiguration.xml')
            if os.path.exists(rta_config_path):
                rta_config = rta_configuration.parse_rta_configuration(rta_config_path)
                if 'samplesheet_filename' in rta_config:
                    samplesheet_path = os.path.join(run_dir, rta_config['samplesheet_filename'])
            
    elif re.match(NEXTSEQ_RUN_ID_REGEX, run_id):
        analysis_dir = os.path.join(run_dir, 'Analysis')
        if os.path.exists(analysis_dir):
            analysis_subdirs = os.listdir(analysis_dir)
            for analysis_subdir in analysis_subdirs:
                data_subdir = os.path.join(analysis_dir, analysis_subdir, 'Data')
                if os.path.exists(data_subdir):
                    samplesheet_paths = glob.glob(os.path.join(data_subdir, 'SampleSheet*.csv'))
                    if len(samplesheet_paths) > 0:
                        # Not sure if there are ever multiple SampleSheet files here
                        # We arbitrarily take the first one.
                        samplesheet_path = samplesheet_paths[0]

    return samplesheet_path


def collect_illumina_sequenced_libraries(run_dir, demultiplexing_id):
    """
    """
    sequenced_libraries = []
    instrument_model = None
    run_id = os.path.basename(run_dir.rstrip('/'))
    if re.match(MISEQ_RUN_ID_REGEX, run_id):
        instrument_model = 'MISEQ'
    elif re.match(NEXTSEQ_RUN_ID_REGEX, run_id):
        instrument_model = 'NEXTSEQ'

    if instrument_model is not None:
        samplesheet_path = find_illumina_samplesheet(run_dir, demultiplexing_id)
        parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_path, instrument_model)
        sequenced_libraries = samplesheet.samplesheet_to_sequenced_libraries(parsed_samplesheet, instrument_model)
        sequenced_libraries_by_library_id = {sequenced_library['library_id']: sequenced_library for sequenced_library in sequenced_libraries}
        if instrument_model == 'MISEQ':
            if miseq_run_dir_is_new_structure(run_dir):
                # MiSeq run with new dir structure
                alignment_dir = os.path.join(run_dir, 'Alignment_', demultiplexing_id)
                alignment_timestamp_subdirs = os.listdir(alignment_dir)
                generate_fastq_run_stats = {}
                if len(alignment_timestamp_subdirs) > 0:
                    # Not sure if there are ever multiple subdirs here.
                    # Arbitrarily take the last one.
                    alignment_timestamp_subdir = alignment_timestamp_subdirs[-1]
                    generate_fastq_run_statistics_path = os.path.join(alignment_dir, alignment_timestamp_subdir, 'GenerateFASTQRunStatistics.xml')
                    if os.path.exists(generate_fastq_run_statistics_path):
                        generate_fastq_run_stats = generate_fastq_run_statistics.parse_generate_fastq_run_statistics(generate_fastq_run_statistics_path)
                if 'sample_stats' in generate_fastq_run_stats:
                    for sample_stats_record in generate_fastq_run_stats['sample_stats']:
                        library_id = None
                        if 'sample_name' in sample_stats_record and 'sample_id' in sample_stats_record:
                            if re.match("S\d+$", sample_stats_record['sample_id']):
                                library_id = sample_stats_record['sample_name']
                            else:
                                library_id = sample_stats_record['sample_id']
                        if library_id is not None and library_id in sequenced_libraries_by_library_id:
                            sequenced_libraries_by_library_id[library_id]['num_reads'] = sample_stats_record.get('num_clusters_passed_filter', None)
            else:
                # MiSeq run with old dir structure
                generate_fastq_run_stats = {}
                generate_fastq_run_statistics_path = os.path.join(run_dir, 'Data', 'Intensities', 'BaseCalls', 'Alignment', 'GenerateFASTQRunStatistics.xml')
                if os.path.exists(generate_fastq_run_statistics_path):
                    generate_fastq_run_stats = generate_fastq_run_statistics.parse_generate_fastq_run_statistics(generate_fastq_run_statistics_path)
                if 'sample_stats' in generate_fastq_run_stats:
                    for sample_stats_record in generate_fastq_run_stats['sample_stats']:
                        library_id = None
                        if 'sample_name' in sample_stats_record and 'sample_id' in sample_stats_record:
                            if re.match("S\d+$", sample_stats_record['sample_id']):
                                library_id = sample_stats_record['sample_name']
                            else:
                                library_id = sample_stats_record['sample_id']
                        if library_id is not None and library_id in sequenced_libraries_by_library_id:
                            sequenced_libraries_by_library_id[library_id]['num_reads'] = sample_stats_record.get('num_clusters_passed_filter', None)
        elif instrument_model == 'NEXTSEQ':
            analysis_dir = os.path.join(run_dir, 'Analysis', demultiplexing_id)
            if os.path.exists(analysis_dir):
                reports_dir = os.path.join(analysis_dir, 'Data', 'Reports')
                demultiplex_stats_path = os.path.join(reports_dir, 'Demultiplex_Stats.csv')
                library_demultiplex_stats = demultiplex_stats.parse_demultiplex_stats(demultiplex_stats_path)
                for library_demultiplex_stats_record in library_demultiplex_stats:
                    if 'library_id' in library_demultiplex_stats_record:
                        library_id = library_demultiplex_stats_record['library_id']
                        if library_id in sequenced_libraries_by_library_id:
                            sequenced_libraries_by_library_id[library_id]['num_reads'] = library_demultiplex_stats_record.get('num_reads', None)
                            
        sequenced_libraries = list(sequenced_libraries_by_library_id.values())

    return sequenced_libraries


def collect_illumina_demultiplexings(run_dir):
    """
    """
    demultiplexings = []
    run_id = os.path.basename(run_dir.rstrip('/'))
    if re.match(MISEQ_RUN_ID_REGEX, run_id):
        if miseq_run_dir_is_new_structure(run_dir):
            # MiSeq run with new dir structure
            for alignment_dir in glob.glob(os.path.join(run_dir, 'Alignment_*')):
                alignment_dir_name = os.path.basename(alignment_dir)
                demultiplexing_id = alignment_dir_name.split('_')[1]
                samplesheet_path = find_illumina_samplesheet(run_dir, demultiplexing_id)
                demultiplexing = {
                    'sequencing_run_id': run_id,
                    'demultiplexing_id': demultiplexing_id,
                    'samplesheet_path': samplesheet_path,
                    'sequenced_libraries': [],
                }
                sequenced_libraries = collect_illumina_sequenced_libraries(run_dir, demultiplexing_id)
                for sequenced_library in sequenced_libraries:
                    demultiplexing['sequenced_libraries'].append(sequenced_library)
                demultiplexings.append(demultiplexing)
        else:
            # MiSeq run with old dir structure
            demultiplexing_id = "1"
            samplesheet_path = find_illumina_samplesheet(run_dir, demultiplexing_id)
            demultiplexing = {
                'sequencing_run_id': run_id,
                'demultiplexing_id': "1",
                'samplesheet_path': samplesheet_path,
                'sequenced_libraries': [],
            }
            sequenced_libraries = collect_illumina_sequenced_libraries(run_dir, demultiplexing_id)
            for sequenced_library in sequenced_libraries:
                demultiplexing['sequenced_libraries'].append(sequenced_library)
            demultiplexings.append(demultiplexing)
    elif re.match(NEXTSEQ_RUN_ID_REGEX, run_id):
        demultiplexing_ids = os.listdir(os.path.join(run_dir, 'Analysis'))
        for demultiplexing_id in demultiplexing_ids:
            samplesheet_path = find_illumina_samplesheet(run_dir, demultiplexing_id)
            demultiplexing = {
                'sequencing_run_id': run_id,
                'demultiplexing_id': demultiplexing_id,
                'samplesheet_path': samplesheet_path,
                'sequenced_libraries': [],
            }
            sequenced_libraries = collect_illumina_sequenced_libraries(run_dir, demultiplexing_id)
            for sequenced_library in sequenced_libraries:
                demultiplexing['sequenced_libraries'].append(sequenced_library)
            demultiplexings.append(demultiplexing)

    return demultiplexings


def collect_illumina_sequencing_run_info(run_dir):
    """
    """
    run_info = {
        'demultiplexings': []
    }
    run_id = os.path.basename(run_dir.rstrip('/'))
    run_id_split = run_id.split('_')
    run_info['sequencing_run_id'] = run_id
    run_info['instrument_id'] = run_id_split[1]
    run_info['flowcell_id'] = run_id_split[-1]
    interop_summary = interop.summary_nonindex(run_dir)
    run_info.update(interop_summary)
    demultiplexings = collect_illumina_demultiplexings(run_dir)
    run_info['demultiplexings'] = demultiplexings

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
        for demultiplexing_idx, demultiplexing in enumerate(sequencing_run_info['demultiplexings']):
            for sequenced_library_idx, sequenced_library in enumerate(sequencing_run_info['demultiplexings'][demultiplexing_idx]['sequenced_libraries']):
                sequenced_library['sequencing_run_id'] = sequencing_run_info['sequencing_run_id']
                sequenced_library['demultiplexing_id'] = demultiplexing['demultiplexing_id']
                sequencing_run_info['demultiplexings'][demultiplexing_idx]['sequenced_libraries'][sequenced_library_idx] = model.IlluminaSequencedLibrary(**sequenced_library)
            sequencing_run_info['demultiplexings'][demultiplexing_idx] = model.IlluminaSequencingRunDemultiplexing(**demultiplexing)
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
