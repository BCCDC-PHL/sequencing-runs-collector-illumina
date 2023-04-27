import glob
import json
import os
import re

import sequencing_runs_collector.parsers.interop as interop
import sequencing_runs_collector.parsers.runinfo as runinfo


MISEQ_RUN_ID_REGEX = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
NEXTSEQ_RUN_ID_REGEX = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"

def get_illumina_interop_summary(run_dir):
    """
    """
    interop_summary = interop.summary_nonindex(os.path.join(run_dir))
    if interop_summary.get('num_reads', None) and interop_summary.get('num_reads_passed_filter', None):
        interop_summary['percent_reads_passed_filter'] = interop_summary['num_reads_passed_filter'] / interop_summary['num_reads'] * 100
    if interop_summary.get('cluster_count', None) and interop_summary.get('cluster_count_passed_filter', None):
        interop_summary['percent_clusters_passed_filter'] = interop_summary['cluster_count_passed_filter'] / interop_summary['cluster_count'] * 100

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
    """
    demultiplexing_id = None
    if instrument_model == 'NEXTSEQ':
        demultiplexing_output_dir_basename = os.path.basename(demultiplexing_output_dir)
        demultiplexing_id = run_id + "-DMX" + demultiplexing_output_dir_basename
    elif instrument_model == 'MISEQ':
        demultiplexing_output_dir_basename = os.path.basename(demultiplexing_output_dir)
        if demultiplexing_output_dir_basename == 'BaseCalls':
            demultiplexing_id = run_id + "-DMX1"
        else:
            demultiplexing_parent_dir_basename = os.path.basename(os.path.abspath(os.path.join(demultiplexing_output_dir, os.pardir)))
            demultiplexing_parent_dir_basename_split = demultiplexing_parent_dir_basename.split('_')
            if len(demultiplexing_parent_dir_basename_split) > 1:
                demultiplexing_num = demultiplexing_parent_dir_basename_split[-1]
                demultiplexing_id = run_id + "-DMX" + demultiplexing_num

    return demultiplexing_id


def find_samplesheet(demultiplexing_output_dir, instrument_model):
    """
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


def get_sequenced_libraries_from_samplesheet(samplesheet, instrument_model, demultiplexing_output_dir, project_id_translation):
    """
    """
    sequenced_libraries = []
    samples_section_key = None
    project_key = None
    fastq_dir = None

    if instrument_model == "NEXTSEQ":
        samples_section_key = "cloud_data"
        project_key = "project_name"
        fastq_dir = os.path.join(demultiplexing_output_dir, 'Data', 'fastq')
    elif instrument_model == "MISEQ":
        samples_section_key = "data"
        project_key = "sample_project"
        if os.path.basename(demultiplexing_output_dir) == "BaseCalls":
            fastq_dir = demultiplexing_output_dir
        else:
            fastq_dir = os.path.join(demultiplexing_output_dir, "Fastq")

    libraries_by_library_id = {}
    for sample in samplesheet[samples_section_key]:
        library = {
        }
        
        if re.match("S\d+$", sample['sample_id']):
            library_id_key = "sample_name"
        else:
            library_id_key = "sample_id"

        library_id = sample[library_id_key]
        library['id'] = library_id
        library['samplesheet_project_id'] = sample.get(project_key, None)
        library['translated_project_id'] = project_id_translation.get(library['samplesheet_project_id'], None)
        libraries_by_library_id[library_id] = library

    index_section_key = None
    if instrument_model == "NEXTSEQ":
        index_section_key = "bclconvert_data"
    elif instrument_model == "MISEQ":
        index_section_key = "data"

    if index_section_key is not None:
        for sample in samplesheet[index_section_key]:
            if index_section_key == 'bclconvert_data':
                library_id = sample['sample_id']
                libraries_by_library_id[library_id]['index'] = sample['index']
                libraries_by_library_id[library_id]['index2'] = sample['index2']
            else:
                if re.match("S\d+$", sample['sample_id']):
                    library_id_key = "sample_name"
                else:
                    library_id_key = "sample_id"
                library_id = sample[library_id_key]
                libraries_by_library_id[library_id]['index'] = sample['index']
                libraries_by_library_id[library_id]['index2'] = sample['index2']

    if fastq_dir is not None and os.path.exists(fastq_dir):
        for library_id in libraries_by_library_id.keys():
            fastq_path_r1 = None
            fastq_path_r2 = None
            fastq_paths_r1 = glob.glob(os.path.join(fastq_dir, library_id + '_*_R1_*.fastq.gz'))
            if len(fastq_paths_r1) > 0:
                fastq_path_r1 = fastq_paths_r1[0]
                libraries_by_library_id[library_id]['fastq_path_r1'] = fastq_path_r1
            fastq_paths_r2 = glob.glob(os.path.join(fastq_dir, library_id + '_*_R2_*.fastq.gz'))
            if len(fastq_paths_r2) > 0:
                fastq_path_r2 = fastq_paths_r2[0]
                libraries_by_library_id[library_id]['fastq_path_r2'] = fastq_path_r2
                
    sequenced_libraries = list(libraries_by_library_id.values())

    return sequenced_libraries


def get_runinfo(run_dir):
    """
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
