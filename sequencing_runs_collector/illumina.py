import glob
import json
import hashlib
import os
import re

import pyfastx

import sequencing_runs_collector.parsers.interop as interop
import sequencing_runs_collector.parsers.runinfo as runinfo


MISEQ_RUN_ID_REGEX = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
NEXTSEQ_RUN_ID_REGEX = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"

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
                    if re.match("\d+_\d", os.path.basename(timestamp_dir)):
                        demultiplexing_output_dirs.append(timestamp_dir)
        else:
            # The 'old' MiSeq output directory is always 'Data/Intensities/BaseCalls'
            basecalls_dir = os.path.join(run_dir, 'Data', 'Intensities', 'BaseCalls')
            demultiplexing_output_dirs.append(basecalls_dir)

    return demultiplexing_output_dirs


def get_demultiplexing_id(run_id, demultiplexing_output_dir, instrument_model):
    """
    Get the demultiplexing ID for a run.

    :param run_id: Run ID
    :type run_id: str
    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :return: Demultiplexing ID
    :rtype: str
    """
    demultiplexing_id = None
    if instrument_model == 'NEXTSEQ':
        demultiplexing_output_dir_basename = os.path.basename(demultiplexing_output_dir)
        demultiplexing_id = demultiplexing_output_dir_basename
    elif instrument_model == 'MISEQ':
        demultiplexing_output_dir_basename = os.path.basename(demultiplexing_output_dir)
        if demultiplexing_output_dir_basename == 'BaseCalls':
            demultiplexing_id = "1"
        else:
            demultiplexing_parent_dir_basename = os.path.basename(os.path.abspath(os.path.join(demultiplexing_output_dir, os.pardir)))
            demultiplexing_parent_dir_basename_split = demultiplexing_parent_dir_basename.split('_')
            if len(demultiplexing_parent_dir_basename_split) > 1:
                demultiplexing_num = demultiplexing_parent_dir_basename_split[-1]
                demultiplexing_id = str(demultiplexing_num)

    return demultiplexing_id


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


def get_fastq_stats(fastq_path):
    """
    Get statistics for a FASTQ file.

    :param fastq_path: Path to FASTQ file
    :type fastq_path: str
    :return: FASTQ statistics keys: [num_reads, num_bases]
    :rtype: dict[str, object]
    """
    try:
        fq = pyfastx.Fastq(fastq_path, build_index=False)
    except RuntimeError as e:
        return {
            'num_reads': None,
            'num_bases': None,
        }

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
        
    stats = {
        'num_reads': num_reads,
        'num_bases': num_bases,
        'q30_percent': q30_percent,
        'q30_percent_last_25_bases': q30_percent_last_25_bases,
        'md5': file_hash.hexdigest(),
        'file_size_mb': file_size_mb,
    }

    return stats


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


def get_sequenced_libraries_from_samplesheet(samplesheet, instrument_model, demultiplexing_output_dir, project_id_translation, collect_fastq_stats=False):
    """
    Get the sequenced libraries from a samplesheet.

    :param samplesheet: Samplesheet
    :type samplesheet: dict[str, object]
    :param instrument_model: Instrument model ("MISEQ" or "NEXTSEQ")
    :type instrument_model: str
    :param demultiplexing_output_dir: Demultiplexing output directory
    :type demultiplexing_output_dir: str
    :param project_id_translation: Project ID translation
    :type project_id_translation: dict[str, str]
    :return: Sequenced libraries. Each library is a dictionary with keys: ['library_id', 'project_id_samplesheet', 'project_id_translated',
                                                                           'index', 'index2', 'fastq_filename_r1', 'fastq_filaname_r2', ...]
    :rtype: list[dict[str, object]]
    """
    sequenced_libraries = []
    samples_section_key = None
    project_key = None
    fastq_dir = None

    if instrument_model == "NEXTSEQ":
        samples_section_key = "cloud_data"
        project_key = "project_name"

    elif instrument_model == "MISEQ":
        samples_section_key = "data"
        project_key = "sample_project"

    fastq_dir = find_fastq_output_dir(demultiplexing_output_dir, instrument_model)

    libraries_by_library_id = {}
    for sample in samplesheet[samples_section_key]:
        library = {}
        
        if (re.match("S\d+$", sample['sample_id']) or re.match("\d+$", sample['sample_id'])):
            if 'sample_name' in sample and not (re.match("S\d+$", sample['sample_name']) or re.match("\d+$", sample['sample_name'])):
                library_id_key = "sample_name"
            else:
                library_id_key = "sample_id"
        else:
            library_id_key = "sample_id"

        samplesheet_library_id = sample[library_id_key]
        cleaned_library_id = samplesheet_library_id.replace("_", "-")
        if os.path.exists(os.path.join(fastq_dir, samplesheet_library_id + '_S*_L*_R1_001.fastq.gz')):
            library_id = samplesheet_library_id
        else:
            library_id = cleaned_library_id
        library['library_id'] = library_id
        library['project_id_samplesheet'] = sample.get(project_key, None)
        # If we don't have a translation, just use the original project ID for the translated project ID.
        library['project_id_translated'] = project_id_translation.get(library['project_id_samplesheet'], library['project_id_samplesheet']) 
        libraries_by_library_id[library_id] = library

    index_section_key = None
    if instrument_model == "NEXTSEQ":
        index_section_key = "bclconvert_data"
    elif instrument_model == "MISEQ":
        index_section_key = "data"

    if index_section_key is not None:
        for sample in samplesheet[index_section_key]:
            if index_section_key == 'bclconvert_data':
                library_id = sample['sample_id'].replace("_", "-")
                try:
                    if 'index' in sample:
                        libraries_by_library_id[library_id]['index'] = sample['index']
                    if 'index2' in sample:
                        libraries_by_library_id[library_id]['index2'] = sample['index2']
                except KeyError as e:
                    libraries_by_library_id[library_id] = {
                        'id': library_id
                    }
                    if 'index' in sample:
                        libraries_by_library_id[library_id]['index'] = sample['index']
                    if 'index2' in sample:
                        libraries_by_library_id[library_id]['index2'] = sample['index2']
                    
            else:
                if (re.match("S\d+$", sample['sample_id']) or re.match("\d+$", sample['sample_id'])):
                    if 'sample_name' in sample and not (re.match("S\d+$", sample['sample_name']) or re.match("\d+$", sample['sample_name'])):
                        library_id_key = "sample_name"
                    else:
                        library_id_key = "sample_id"
                else:
                    library_id_key = "sample_id"
                library_id = sample[library_id_key].replace("_", "-")
                if 'index' in sample:                 
                    libraries_by_library_id[library_id]['index'] = sample['index']
                if 'index2' in sample:
                    libraries_by_library_id[library_id]['index2'] = sample['index2']

    if fastq_dir is not None and os.path.exists(fastq_dir):
        for library_id in libraries_by_library_id.keys():
            sample_number = None
            fastq_path_r1 = None
            fastq_filename_r1 = None
            fastq_path_r2 = None
            fastq_filename_r2 = None
            fastq_stats_r1 = {}
            fastq_stats_r2 = {}
            num_reads = None
            num_bases = None
            fastq_paths_r1 = glob.glob(os.path.join(fastq_dir, library_id + '_*_R1_*.fastq.gz'))
            if len(fastq_paths_r1) > 0:
                fastq_path_r1 = fastq_paths_r1[0]
                fastq_filename_r1 = os.path.basename(fastq_path_r1)
                sample_number_match = re.search(r'_S(\d+)_', fastq_filename_r1)
                if sample_number_match:
                    try:
                        sample_number = int(sample_number_match.group(1).replace('S', '').lstrip('0'))
                    except ValueError as e:
                        pass
                if collect_fastq_stats:
                    fastq_stats_r1 = get_fastq_stats(fastq_path_r1)
                else:
                    fastq_stats_r1 = {}
                if 'num_reads' in fastq_stats_r1 and fastq_stats_r1['num_reads'] is not None:
                    if num_reads is None:
                        num_reads = 0
                    num_reads += fastq_stats_r1['num_reads']
                if 'num_bases' in fastq_stats_r1 and fastq_stats_r1['num_bases'] is not None:
                    if num_bases is None:
                        num_bases = 0
                    num_bases += fastq_stats_r1['num_bases']
                libraries_by_library_id[library_id]['fastq_filename_r1'] = fastq_filename_r1
                libraries_by_library_id[library_id]['fastq_md5_r1'] = fastq_stats_r1.get('md5', None)
                libraries_by_library_id[library_id]['q30_percent_r1'] = fastq_stats_r1.get('q30_percent', None)
                libraries_by_library_id[library_id]['q30_percent_last_25_bases_r1'] = fastq_stats_r1.get('q30_percent_last_25_bases', None)
                libraries_by_library_id[library_id]['fastq_file_size_mb_r1'] = fastq_stats_r1.get('file_size_mb', None)

            fastq_paths_r2 = glob.glob(os.path.join(fastq_dir, library_id + '_*_R2_*.fastq.gz'))
            if len(fastq_paths_r2) > 0:
                fastq_path_r2 = fastq_paths_r2[0]
                fastq_filename_r2 = os.path.basename(fastq_path_r2)
                if collect_fastq_stats:
                    fastq_stats_r2 = get_fastq_stats(fastq_path_r2)
                else:
                    fastq_stats_r2 = {}
                if 'num_reads' in fastq_stats_r2 and fastq_stats_r2['num_reads'] is not None:
                    if num_reads is None:
                        num_reads = 0
                    num_reads += fastq_stats_r2['num_reads']
                if 'num_bases' in fastq_stats_r2 and fastq_stats_r2['num_bases'] is not None:
                    if num_bases is None:
                        num_bases = 0
                    num_bases += fastq_stats_r2['num_bases']
                libraries_by_library_id[library_id]['fastq_filename_r2'] = fastq_filename_r2
                libraries_by_library_id[library_id]['fastq_md5_r2'] = fastq_stats_r2.get('md5', None)
                libraries_by_library_id[library_id]['q30_percent_r2'] = fastq_stats_r2.get('q30_percent', None)
                libraries_by_library_id[library_id]['q30_percent_last_25_bases_r2'] = fastq_stats_r2.get('q30_percent_last_25_bases', None)
                libraries_by_library_id[library_id]['fastq_file_size_mb_r2'] = fastq_stats_r2.get('file_size_mb', None)

            required_keys = ['num_bases', 'q30_percent']
            q30_percent_overall = None
            if all([key in fastq_stats_r1 for key in required_keys] + [key in fastq_stats_r2 for key in required_keys]):
                q30_percent_overall = round((fastq_stats_r1['num_bases'] * fastq_stats_r1['q30_percent'] +
                                          fastq_stats_r2['num_bases'] * fastq_stats_r2['q30_percent']) /
                                         (fastq_stats_r1['num_bases'] + fastq_stats_r2['num_bases']), 4)

            required_keys = ['num_reads', 'q30_percent_last_25_bases']
            q30_percent_last_25_bases_overall = None
            if all([key in fastq_stats_r1 for key in required_keys] + [key in fastq_stats_r2 for key in required_keys]):
                num_bases_r1 = fastq_stats_r1['num_reads'] * 25
                num_q30_bases_in_last_25_bases_r1 = (fastq_stats_r1['q30_percent_last_25_bases'] / 100) * num_bases_r1
                num_bases_r2 = fastq_stats_r2['num_reads'] * 25
                num_q30_bases_in_last_25_bases_r2 = (fastq_stats_r2['q30_percent_last_25_bases'] / 100) * num_bases_r2
                num_q30_bases_in_last_25_bases_total = num_q30_bases_in_last_25_bases_r1 + num_q30_bases_in_last_25_bases_r2
                num_bases_total = num_bases_r1 + num_bases_r2
                try:
                    q30_percent_last_25_bases_overall = round((num_q30_bases_in_last_25_bases_total / num_bases_total * 100), 4)
                except (ZeroDivisionError, ValueError) as e:
                    pass
                
            libraries_by_library_id[library_id]['sample_number'] = sample_number
            libraries_by_library_id[library_id]['num_reads'] = num_reads
            libraries_by_library_id[library_id]['num_bases'] = num_bases
            libraries_by_library_id[library_id]['q30_percent'] = q30_percent_overall
            libraries_by_library_id[library_id]['q30_percent_last_25_bases'] = q30_percent_last_25_bases_overall
                
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
