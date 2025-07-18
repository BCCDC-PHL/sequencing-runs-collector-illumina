import csv
import datetime
import glob
import json
import hashlib
import logging
import multiprocessing
import os
import re

import pyfastx

from pathlib import Path
from typing import Optional

import sequencing_runs_collector.parsers.interop as interop
import sequencing_runs_collector.parsers.runinfo as runinfo
import sequencing_runs_collector.parsers.samplesheet as samplesheet_parser


MISEQ_RUN_ID_REGEX = "\\d{6}_M\\d{5}_\\d+_\\d{9}-[A-Z0-9]{5}"
NEXTSEQ_RUN_ID_REGEX = "\\d{6}_VH\\d{5}_\\d+_[A-Z0-9]{9}"

def get_illumina_interop_summary(run_dir):
    """
    Get the interop summary for an Illumina run.

    :param run_dir: Run directory
    :type run_dir: str
    :return: Interop summary
    :rtype: dict[str, object]
    """
    interop_summary = interop.summary_nonindex(os.path.join(run_dir))
    if interop_summary.get('num_reads', None) and interop_summary.get('num_reads_passed_filter', None):
        interop_summary['percent_reads_passed_filter'] = interop_summary['num_reads_passed_filter'] / interop_summary['num_reads'] * 100
    if interop_summary.get('cluster_count', None) and interop_summary.get('cluster_count_passed_filter', None):
        interop_summary['percent_clusters_passed_filter'] = interop_summary['cluster_count_passed_filter'] / interop_summary['cluster_count'] * 100

    summary_lane = interop.summary_lane(os.path.join(run_dir))
    interop_summary['cluster_density'] = None
    interop_summary['cluster_density_passed_filter'] = None
    if len(summary_lane) > 0:
        interop_summary['cluster_density'] = summary_lane[0].get('cluster_density', None)
        interop_summary['cluster_density_passed_filter'] = summary_lane[0].get('cluster_density_passed_filter', None)

    return interop_summary


def find_demultiplexing_output_dirs(run_dir, instrument_model):
    """
    """
    demultiplexing_output_dirs = []
    if instrument_model == 'NEXTSEQ':
        analysis_dirs = glob.glob(os.path.join(run_dir, 'Analysis', '*'))
        demultiplexing_output_dirs = analysis_dirs
    elif instrument_model == 'MISEQ':
        alignment_dirs = glob.glob(os.path.join(run_dir, 'Alignment_*'))
        # The 'new' MiSeq output directory structure outputs
        # to 'Alignment_1', 'Alignment_2', etc.
        if len(alignment_dirs) > 0:
            for alignment_dir in alignment_dirs:
                timestamp_dirs = glob.glob(os.path.join(alignment_dir, '*'))
                for timestamp_dir in timestamp_dirs:
                    if re.match("\\d+_\\d", os.path.basename(timestamp_dir)):
                        demultiplexing_output_dirs.append(timestamp_dir)
        else:
            # The 'old' MiSeq output directory is always 'Data/Intensities/BaseCalls'
            basecalls_dir = os.path.join(run_dir, 'Data', 'Intensities', 'BaseCalls')
            demultiplexing_output_dirs.append(basecalls_dir)

    return demultiplexing_output_dirs


def get_demultiplexing_num(run_id, demultiplexing_output_dir, instrument_model):
    """
    Get the demultiplexing ID for a run.

    :param run_id: Run ID
    :type run_id: str
    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :return: Demultiplexing Num
    :rtype: int
    """
    demultiplexing_num = None
    if instrument_model == 'NEXTSEQ':
        demultiplexing_output_dir_basename = os.path.basename(demultiplexing_output_dir)
        try:
            demultiplexing_num = int(demultiplexing_output_dir_basename)
        except ValueError as e:
            pass
    elif instrument_model == 'MISEQ':
        demultiplexing_output_dir_basename = os.path.basename(demultiplexing_output_dir)
        if demultiplexing_output_dir_basename == 'BaseCalls':
            demultiplexing_num = 1
        else:
            demultiplexing_parent_dir_basename = os.path.basename(os.path.abspath(os.path.join(demultiplexing_output_dir, os.pardir)))
            demultiplexing_parent_dir_basename_split = demultiplexing_parent_dir_basename.split('_')
            if len(demultiplexing_parent_dir_basename_split) > 1:
                demultiplexing_num_str = demultiplexing_parent_dir_basename_split[-1]
                try:
                    demultiplexing_num = int(demultiplexing_num_str)
                except ValueError as e:
                    pass

    return demultiplexing_num


def get_demultiplexing_start_timestamp(run_id:str, demultiplexing_output_dir: Path, instrument_model: str) -> Optional[str]:
    """
    Get a timestamp for when the demultiplexing was started.

    :param run_id: Run ID
    :type run_id: str
    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :return: Demultiplexing start timestamp
    :rtype: Optional[str]
    """
    demultiplexing_start_timestamp = None
    if instrument_model == 'NEXTSEQ':
        dmx_dragen_events_path = os.path.join(demultiplexing_output_dir, 'Data', 'dmx_dragen_events.csv')
        if os.path.exists(dmx_dragen_events_path):
            with open(dmx_dragen_events_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['label'] == 'DRAGEN START':
                        demultiplexing_start_timestamp = row['time']

    elif instrument_model == 'MISEQ':
        pass

    return demultiplexing_start_timestamp


def find_samplesheet(demultiplexing_output_dir, instrument_model):
    """
    Find the SampleSheet for a demultiplexing output directory.

    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :return: Path to the SampleSheet, or None if not found.
    :rtype: str|None
    """
    samplesheet_path = None
    if instrument_model == 'NEXTSEQ':
        samplesheets = glob.glob(os.path.join(demultiplexing_output_dir, 'Data', 'SampleSheet*.csv'))
        if len(samplesheets) > 0:
            # There should be only one SampleSheet here.
            # We arbitrarily take the first if there are multiple.
            samplesheet_path = samplesheets[0]
    elif instrument_model == 'MISEQ':
        if os.path.exists(os.path.join(demultiplexing_output_dir, 'Alignment')):
            expected_samplesheet_path = os.path.join(demultiplexing_output_dir, 'Alignment', 'SampleSheetUsed.csv')
            if os.path.exists(expected_samplesheet_path):
                samplesheet_path = expected_samplesheet_path
        else:
            expected_samplesheet_path = os.path.join(demultiplexing_output_dir, 'SampleSheetUsed.csv')
            if os.path.exists(expected_samplesheet_path):
                samplesheet_path = expected_samplesheet_path

    return samplesheet_path


def get_fastq_stats(fastq_path, library_id, read_type="R1"):
    """
    Get statistics for a FASTQ file.

    :param fastq_path: Path to FASTQ file
    :type fastq_path: str
    :param library_id: Library ID
    :type library_id: str
    :param read_number: Read number
    :type read_type: str
    :return: FASTQ statistics keys: [num_reads, num_bases]
    :rtype: dict[str, object]
    """
    try:
        fq = pyfastx.Fastq(fastq_path, build_index=False)
    except RuntimeError as e:
        fastq_stats_summary = {
            'library_id': library_id,
            'read_type': read_type,
            'stats': {
                'num_reads_' + read_type.lower(): None,
                'num_bases_' + read_type.lower(): None,
                'q30_percent_' + read_type.lower(): None,
                'q30_percent_last_25_bases_' + read_type.lower(): None,
                'fastq_md5_' + read_type.lower(): None,
                'fastq_file_size_mb' + read_type.lower(): None,
            }
        }
        return fastq_stats_summary

    num_reads = 0
    num_bases = 0
    num_bases_over_q30 = 0
    num_bases_over_q30_last_25 = 0
    for name, seq, qual in fq:
        for q in qual:
            phred_quality = ord(q) - 33
            if phred_quality >= 30:
                num_bases_over_q30 += 1
        for q in qual[-25:]:
            phred_quality = ord(q) - 33
            if phred_quality >= 30:
                num_bases_over_q30_last_25 += 1
            
        num_reads += 1
        num_bases += len(seq)

    file_size_bytes = os.path.getsize(fastq_path)
    try:
        file_size_mb = round(file_size_bytes / 1024 / 1024, 4)
    except (ZeroDivisionError, ValueError) as e:
        file_size_mb = None

    file_hash = hashlib.md5()
    with open(fastq_path, "rb") as f:
        while chunk := f.read(8192):
            file_hash.update(chunk)

    try:
        q30_percent = round(num_bases_over_q30 / num_bases * 100, 4)
    except (ZeroDivisionError, ValueError) as e:
        q30_percent = None
    try:
        q30_percent_last_25_bases = round(num_bases_over_q30_last_25 / (25 * num_reads) * 100, 4)
    except (ZeroDivisionError, ValueError) as e:
        q30_percent_last_25_bases = None

    fastq_stats = {
        'num_reads_' + read_type.lower(): num_reads,
        'num_bases_' + read_type.lower(): num_bases,
        'q30_percent_' + read_type.lower(): q30_percent,
        'q30_percent_last_25_bases_' + read_type.lower(): q30_percent_last_25_bases,
        'fastq_md5_' + read_type.lower(): file_hash.hexdigest(),
        'fastq_file_size_mb_' + read_type.lower(): file_size_mb,
    }
    fastq_stats_summary = {
        'library_id': library_id,
        'read_type': read_type,
        'fastq_stats': fastq_stats,
    }

    return fastq_stats_summary


def find_fastq_output_dir(demultiplexing_output_dir, instrument_model):
    """
    Find the FASTQ output directory for a demultiplexing output directory.
    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :return: Path to the FASTQ output directory, or None if not found.
    :rtype: str|None
    """
    
    fastq_dir = None
    if instrument_model == "NEXTSEQ":
        fastq_dir = os.path.join(demultiplexing_output_dir, 'Data', 'fastq')
    elif instrument_model == "MISEQ":
        if os.path.basename(demultiplexing_output_dir) == "BaseCalls":
            fastq_dir = demultiplexing_output_dir
        else:
            fastq_dir = os.path.join(demultiplexing_output_dir, "Fastq")

    return fastq_dir


def get_sequenced_libraries_from_samplesheet(samplesheet, instrument_model, demultiplexing_output_dir, project_id_translation, collect_fastq_stats=False, num_fastq_stats_processes=1):
    """
    Get the sequenced libraries from a samplesheet.
    TODO: Separate out the FASTQ statistics collection more cleanly.

    :param samplesheet: Samplesheet
    :type samplesheet: dict[str, object]
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param project_id_translation: Project ID translation
    :type project_id_translation: dict[str, str]
    :param collect_fastq_stats: Collect FASTQ statistics
    :type collect_fastq_stats: bool
    :param num_fastq_stats_processes: Number of FASTQ statistics processes
    :type num_fastq_stats_processes: int
    :return: Sequenced libraries. Each library is a dictionary with keys: ['library_id', 'project_id_samplesheet', 'project_id_translated',
                                                                           'index', 'index2', 'fastq_filename_r1', 'fastq_filaname_r2', ...]
    :rtype: list[dict[str, object]]
    """
    sequenced_libraries = samplesheet_parser.samplesheet_to_sequenced_libraries(samplesheet, instrument_model)

    fastq_dir = find_fastq_output_dir(demultiplexing_output_dir, instrument_model)

    libraries_by_library_id = {}
    for library in sequenced_libraries:
        library_id = library['library_id']
        # If we don't have a translation, just use the original project ID for the translated project ID.
        library['project_id_translated'] = project_id_translation.get(library['project_id_samplesheet'], library['project_id_samplesheet']) 
        libraries_by_library_id[library_id] = library

    if fastq_dir is not None and os.path.exists(fastq_dir):
        for library_id in libraries_by_library_id.keys():
            sample_number = None
            fastq_path_r1 = None
            fastq_filename_r1 = None
            fastq_path_r2 = None
            fastq_filename_r2 = None

            fastq_paths_r1 = glob.glob(os.path.join(fastq_dir, f"{library_id}_*_R1_*.fastq.gz"))
            if len(fastq_paths_r1) > 0:
                fastq_path_r1 = fastq_paths_r1[0]
                fastq_filename_r1 = os.path.basename(fastq_path_r1)
                sample_number_match = re.search(r'_S(\d+)_', fastq_filename_r1)
                if sample_number_match:
                    try:
                        sample_number = int(sample_number_match.group(1).replace('S', '').lstrip('0'))
                    except ValueError as e:
                        pass
                libraries_by_library_id[library_id]['fastq_filename_r1'] = fastq_filename_r1

            fastq_paths_r2 = glob.glob(os.path.join(fastq_dir, f"{library_id}_*_R2_*.fastq.gz"))
            if len(fastq_paths_r2) > 0:
                fastq_path_r2 = fastq_paths_r2[0]
                fastq_filename_r2 = os.path.basename(fastq_path_r2)
                libraries_by_library_id[library_id]['fastq_filename_r2'] = fastq_filename_r2
    
            libraries_by_library_id[library_id]['sample_number'] = sample_number

    # Collect fastq stats in parallel
    # TODO: This part should be factored out into a separate function.
    if collect_fastq_stats:
        pool = multiprocessing.Pool(processes=num_fastq_stats_processes)
        get_fastq_stats_inputs = []
        for library_id, library in libraries_by_library_id.items():
            if 'fastq_filename_r1' in library and library['fastq_filename_r1'] is not None:
                fastq_path_r1 = os.path.join(fastq_dir, library['fastq_filename_r1'])
                if os.path.exists(fastq_path_r1):
                    get_fastq_stats_input = {
                        'fastq_path': fastq_path_r1,
                        'library_id': library_id,
                        'read_type': "R1"
                    }
                    get_fastq_stats_inputs.append(get_fastq_stats_input)
            if 'fastq_filename_r2' in library and library['fastq_filename_r2'] is not None:
                fastq_path_r2 = os.path.join(fastq_dir, library['fastq_filename_r2'])
                if os.path.exists(fastq_path_r2):
                    get_fastq_stats_input = {
                        'fastq_path': fastq_path_r2,
                        'library_id': library_id,
                        'read_type': "R2"
                    }
                    get_fastq_stats_inputs.append(get_fastq_stats_input)

        timestamp_collect_fastq_stats_start = datetime.datetime.now()
        logging.info(json.dumps({
            'event_type': 'collect_fastq_stats_start',
            'fastq_dir': os.path.abspath(fastq_dir),
            'num_fastq_stats_inputs': len(get_fastq_stats_inputs)
        }))
        fastq_stats = pool.starmap(get_fastq_stats, [(input['fastq_path'], input['library_id'], input['read_type']) for input in get_fastq_stats_inputs])
        pool.close()
        pool.join()
        timestamp_collect_fastq_stats_complete = datetime.datetime.now()
        logging.info(json.dumps({
            'event_type': 'collect_fastq_stats_complete',
            'fastq_dir': os.path.abspath(fastq_dir),
            'fastq_files_stats_collected': len(fastq_stats),
            'collect_fastq_stats_duration_seconds': (timestamp_collect_fastq_stats_complete - timestamp_collect_fastq_stats_start).total_seconds()
        }))

        fastq_stats_by_library_id = {}
        for fastq_stat in fastq_stats:
            library_id = fastq_stat['library_id']
            read_type = fastq_stat['read_type']
            if library_id not in fastq_stats_by_library_id:
                fastq_stats_by_library_id[library_id] = {}
            fastq_stats_by_library_id[library_id].update(fastq_stat.get('fastq_stats', {}).copy())

        for library_id, fastq_stats in fastq_stats_by_library_id.items():
            required_keys = [
                'num_reads_r1',
                'num_reads_r2',
                'num_bases_r1',
                'num_bases_r2',
                'q30_percent_r1',
                'q30_percent_r2',
                'q30_percent_last_25_bases_r1',
                'q30_percent_last_25_bases_r2',
            ]
            all_keys_present = all(key in fastq_stats for key in required_keys)
            
            if all_keys_present:
                all_keys_have_values = all(fastq_stats[key] is not None for key in required_keys)
                if all_keys_have_values:
                    num_bases_total = fastq_stats['num_bases_r1'] + fastq_stats['num_bases_r2']
                    num_reads_total = fastq_stats['num_reads_r1'] + fastq_stats['num_reads_r2']
                    q30_percent_r1 = fastq_stats['q30_percent_r1']
                    q30_percent_r2 = fastq_stats['q30_percent_r2']
                    num_q30_bases_r1 = round(fastq_stats['num_bases_r1'] * q30_percent_r1 / 100)
                    num_q30_bases_r2 = round(fastq_stats['num_bases_r2'] * q30_percent_r2 / 100)
                    num_q30_bases_total = num_q30_bases_r1 + num_q30_bases_r2
                    q30_percent_total = round(num_q30_bases_total / num_bases_total * 100, 4)
                    q30_percent_last_25_bases_r1 = fastq_stats['q30_percent_last_25_bases_r1']
                    q30_percent_last_25_bases_r2 = fastq_stats['q30_percent_last_25_bases_r2']
                    num_bases_last_25_r1 = fastq_stats['num_reads_r1'] * 25
                    num_bases_last_25_r2 = fastq_stats['num_reads_r2'] * 25
                    num_bases_last_25_total = num_bases_last_25_r1 + num_bases_last_25_r2
                    num_q30_bases_last_25_r1 = round(num_bases_last_25_r1 * q30_percent_last_25_bases_r1 / 100)
                    num_q30_bases_last_25_r2 = round(num_bases_last_25_r2 * q30_percent_last_25_bases_r2 / 100)
                    num_q30_bases_last_25_total = num_q30_bases_last_25_r1 + num_q30_bases_last_25_r2
                    q30_percent_last_25_bases_total = round(num_q30_bases_last_25_total / num_bases_last_25_total * 100, 4)
                else:
                    num_reads_total = None
                    num_bases_total = None
                    q30_percent_total = None
                    q30_percent_last_25_bases_total = None
            else:
                num_reads_total = None
                num_bases_total = None
                q30_percent_total = None
                q30_percent_last_25_bases_total = None
            fastq_stats_by_library_id[library_id]['num_reads'] = num_reads_total
            fastq_stats_by_library_id[library_id]['num_bases'] = num_bases_total
            fastq_stats_by_library_id[library_id]['q30_percent'] = q30_percent_total
            fastq_stats_by_library_id[library_id]['q30_percent_last_25_bases'] = q30_percent_last_25_bases_total

        for library_id, library in libraries_by_library_id.items():
            if library_id in fastq_stats_by_library_id:
                library.update(fastq_stats_by_library_id[library_id])
                library.pop('num_reads_r1', None)
                library.pop('num_reads_r2', None)
                library.pop('num_bases_r1', None)
                library.pop('num_bases_r2', None)

    sequenced_libraries = list(libraries_by_library_id.values())
            
            
    return sequenced_libraries


def get_runinfo(run_dir):
    """
    Get run information from the RunInfo.xml file.

    :param run_dir: Run directory
    :type run_dir: str
    :return: Run information
    :rtype: dict[str, object]
    """
    run_info = {
        'num_cycles_r1': None,
        'num_cycles_r2': None,
    }
    run_id = os.path.basename(run_dir)
    runinfo_path = os.path.join(run_dir, 'RunInfo.xml')
    if re.match(MISEQ_RUN_ID_REGEX, run_id):
        parsed_runinfo = runinfo.parse_runinfo_miseq_v1(runinfo_path)
        if 'reads' in parsed_runinfo:
            for read in parsed_runinfo['reads']:
                if not read['is_indexed_read']:
                    if read['number'] == 1:
                        run_info['num_cycles_r1'] = read['num_cycles']
                    elif read['number'] == 4:
                        run_info['num_cycles_r2'] = read['num_cycles']
        
    elif re.match(NEXTSEQ_RUN_ID_REGEX, run_id):
        parsed_runinfo = runinfo.parse_runinfo_nextseq_v1(runinfo_path)
        if 'reads' in parsed_runinfo:
            for read in parsed_runinfo['reads']:
                if not read['is_indexed_read']:
                    if read['number'] == 1:
                        run_info['num_cycles_r1'] = read['num_cycles']
                    elif read['number'] == 4:
                        run_info['num_cycles_r2'] = read['num_cycles']

    return run_info
