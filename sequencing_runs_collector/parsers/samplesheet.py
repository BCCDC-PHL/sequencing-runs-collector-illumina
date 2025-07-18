import csv
import glob
import json
import logging
import os
import re


from pathlib import Path
from typing import Optional

import jsonschema

import sequencing_runs_collector.util as util


def _parse_header_section_miseq_v1(samplesheet_path: str):
    header_lines = []
    header = {}
    header['instrument_type'] = 'MiSeq'

    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Header]'):
                continue
            if line.strip().startswith('[Reads]'):
                break
            else:
                header_lines.append(line.strip().rstrip(','))

    for line in header_lines:
        header_key = line.split(',')[0].lower().replace(" ", "_")

        if len(line.split(',')) > 1:
            header_value = line.split(',')[1]
        else:
            header_value = ""

        if header_key != "":
            header[header_key] = header_value
              
    return header


def _parse_reads_section_miseq_v1(samplesheet_path: str):
    """
    """
    reads_lines = []
    reads = []
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Reads]'):
                break
        for line in f:
            if line.strip().startswith('[Settings]'):
                break
            reads_lines.append(line.strip().rstrip(','))

    for line in reads_lines:
        if line != "":
            read_len = int(line.split(',')[0])
            reads.append(read_len)

    return reads

def _parse_reads_section_miseq_v2(samplesheet_path: str):
    """
    """
    reads_lines = []
    reads = []
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Reads]'):
                break
        for line in f:
            if line.strip().startswith('[Settings]'):
                break
            reads_lines.append(line.strip().rstrip(','))

    for line in reads_lines:
        if line != "":
            read_len = int(line)
            reads.append(read_len)

    return reads


def _parse_settings_section_miseq_v1(samplesheet_path: str):
    """
    """
    settings_lines = []
    settings = {}
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Settings]'):
                break
        for line in f:
            if line.strip().startswith('[Data]'):
                break
            settings_lines.append(line.strip().rstrip(','))

    for line in settings_lines:
        settings_key = line.split(',')[0].lower().replace(" ", "_")

        if len(line.split(',')) > 1:
            settings_value = line.split(',')[1]
        else:
            settings_value = ""

        if settings_key != "":
            settings[settings_key] = settings_value
              
    return settings


def _parse_data_section_miseq_v1(samplesheet_path):
    """
    """
    data = []
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if not line.strip().startswith('[Data]'):
                continue
            else:
                break
          
        data_header = [x.lower() for x in next(f).strip().split(',')]
      
        for line in f:
            if not all([x == '' for x in line.strip().split(',')]):
                data_line = {}
                for idx, data_element in enumerate(line.strip().split(',')):
                    try:
                        data_line[data_header[idx]] = data_element
                    except IndexError as e:
                        pass
                data.append(data_line)

    return data


def _determine_samplesheet_version(samplesheet_path: str, instrument_type: str):
    """
    """
    samplesheet_version = None
    if instrument_type == 'miseq':
        samplesheet_version = 1
    elif instrument_type == 'nextseq':
        samplesheet_version = 1

    return samplesheet_version


def _parse_samplesheet_miseq_v1(samplesheet_path: str):
    """
    """
    samplesheet = {}
    samplesheet['header'] = _parse_header_section_miseq_v1(samplesheet_path)
    samplesheet['reads'] = _parse_reads_section_miseq_v1(samplesheet_path)
    samplesheet['settings'] = _parse_settings_section_miseq_v1(samplesheet_path)
    samplesheet['data'] = _parse_data_section_miseq_v1(samplesheet_path)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "resources", "samplesheet_miseq_v1.schema.json")
    schema = None
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=samplesheet, schema=schema)
    except jsonschema.ValidationError as e:
        logging.error({"event_type": "samplesheet_validation_failed", "samplesheet_path": samplesheet_path, "schema_path": schema_path})

    return samplesheet


def _parse_samplesheet_miseq_v2(samplesheet_path: str):
    """
    """
    samplesheet = {}
    samplesheet['header'] = _parse_header_section_miseq_v1(samplesheet_path)
    samplesheet['reads'] = _parse_reads_section_miseq_v2(samplesheet_path)
    samplesheet['settings'] = _parse_settings_section_miseq_v2(samplesheet_path)
    samplesheet['data'] = _parse_data_section_miseq_v1(samplesheet_path)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "resources", "samplesheet_miseq_v1.schema.json")
    schema = None
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=samplesheet, schema=schema)
    except jsonschema.ValidationError as e:
        logging.error({"event_type": "samplesheet_validation_failed", "samplesheet_path": samplesheet_path, "schema_path": schema_path})

    return samplesheet


def _parse_header_section_nextseq_v1(samplesheet_path):
    """
    """
    header_lines = []
    header = {}
    header['instrument_type'] = 'NextSeq2000'

    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Header]'):
                continue
            if line.strip().startswith('[Reads]') or line.strip().rstrip(',') == "":
                break
            else:
                header_lines.append(line.strip().rstrip(','))

    for line in header_lines:
        header_key = util.camel_to_snake(line.split(',')[0])

        if len(line.split(',')) > 1:
            header_value = line.split(',')[1]
        else:
            header_value = ""

        if header_key != "":
            header[header_key] = header_value
              
    return header


def _parse_reads_section_nextseq_v1(samplesheet_path):
    """
    """
    reads_lines = []
    reads = {}
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Reads]'):
                break
        for line in f:
            if line.strip().startswith('[Sequencing_Settings]') or line.strip().rstrip(',') == "":
                break
            reads_lines.append(line.strip().rstrip(','))

    for line in reads_lines:
        reads_key = util.camel_to_snake(line.split(',')[0])
        if len(line.split(',')) > 1:
            reads_value = int(line.split(',')[1])
        else:
            reads_value = ""

        if reads_key != "":
            reads[reads_key] = reads_value

    return reads


def _parse_sequencing_settings_section_nextseq_v1(samplesheet_path):
    """
    """
    sequencing_settings_lines = []
    sequencing_settings = {}
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Sequencing_Settings]'):
                break
        for line in f:
            if line.strip().startswith('[BCLConvert_Settings]') or line.strip().rstrip(',') == "":
                break
            sequencing_settings_lines.append(line.strip().rstrip(','))

    for line in sequencing_settings_lines:
        sequencing_settings_key = util.camel_to_snake(line.split(',')[0])

        if len(line.split(',')) > 1:
            sequencing_settings_value = line.split(',')[1]
        else:
            sequencing_settings_value = ""

        if sequencing_settings_key != "":
            sequencing_settings[sequencing_settings_key] = sequencing_settings_value
              
    return sequencing_settings


def _parse_bclconvert_settings_section_nextseq_v1(samplesheet_path):
    """
    """
    bclconvert_settings_lines = []
    bclconvert_settings = {}
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[BCLConvert_Settings]'):
                break
        for line in f:
            if line.strip().startswith('[BCLConvert_Data]') or line.strip().rstrip(',') == "":
                break
            bclconvert_settings_lines.append(line.strip().rstrip(','))

    for line in bclconvert_settings_lines:
        bclconvert_settings_key = util.camel_to_snake(line.split(',')[0])

    if len(line.split(',')) > 1:
        bclconvert_settings_value = line.split(',')[1]
    else:
        bclconvert_settings_value = ""

    if bclconvert_settings_key != "":
        bclconvert_settings[bclconvert_settings_key] = bclconvert_settings_value
              
    return bclconvert_settings


def _parse_bclconvert_data_section_nextseq_v1(samplesheet_path):
    """
    """
    bclconvert_data_lines = []
    bclconvert_data = []
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[BCLConvert_Data]'):
                break
        for line in f:
            if line.strip().startswith('[Cloud_Settings]') or line.strip().rstrip(',') == "":
                break
            bclconvert_data_lines.append(line.strip().rstrip(','))

    bclconvert_data_keys = [util.camel_to_snake(x) for x in bclconvert_data_lines[0].split(',')]
    for line in bclconvert_data_lines[1:]:
        d = {}
        values = line.split(',')
        for idx, key in enumerate(bclconvert_data_keys):
            d[key] = values[idx]
        bclconvert_data.append(d)

    return bclconvert_data


def _parse_cloud_settings_section_nextseq_v1(samplesheet_path):
    """
    """
    cloud_settings_lines = []
    cloud_settings = {}
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Cloud_Settings]'):
                break
        for line in f:
            if line.strip().startswith('[BCLConvert_Settings]') or line.strip().rstrip(',') == "":
                break
            cloud_settings_lines.append(line.strip().rstrip(','))

    for line in cloud_settings_lines:
        cloud_settings_key = util.camel_to_snake(line.split(',')[0])

        if len(line.split(',')) > 1:
            cloud_settings_value = line.split(',')[1]
        else:
            cloud_settings_value = ""

        if cloud_settings_key != "":
            cloud_settings[cloud_settings_key] = cloud_settings_value
              
    return cloud_settings


def _parse_cloud_data_section_nextseq_v1(samplesheet_path):
    cloud_data_lines = []
    cloud_data = []
    with open(samplesheet_path, 'r') as f:
        for line in f:
            if line.strip().startswith('[Cloud_Data]'):
                break
        for line in f:
            if line.strip().startswith('[Cloud_Settings]') or line.strip().rstrip(',') == "":
                break
            cloud_data_lines.append(line.strip().rstrip(','))

    if cloud_data_lines:
        cloud_data_keys = [util.camel_to_snake(x) for x in cloud_data_lines[0].split(',')]
        for line in cloud_data_lines[1:]:
            d = {}
            values = line.strip().split(',')
            if not all([x == '' for x in values]):
                for idx, key in enumerate(cloud_data_keys):
                    try:
                        d[key] = values[idx]
                    except IndexError as e:
                        d[key] = ""
                cloud_data.append(d)
  
    return cloud_data



def _parse_samplesheet_nextseq_v1(samplesheet_path):
    """
    """
    samplesheet = {}
    samplesheet['header'] = _parse_header_section_nextseq_v1(samplesheet_path)
    samplesheet['reads'] = _parse_reads_section_nextseq_v1(samplesheet_path)
    samplesheet['sequencing_settings'] = _parse_sequencing_settings_section_nextseq_v1(samplesheet_path)
    samplesheet['bclconvert_settings'] = _parse_bclconvert_settings_section_nextseq_v1(samplesheet_path)
    samplesheet['bclconvert_data'] = _parse_bclconvert_data_section_nextseq_v1(samplesheet_path)
    samplesheet['cloud_settings'] = _parse_cloud_settings_section_nextseq_v1(samplesheet_path)
    samplesheet['cloud_data'] = _parse_cloud_data_section_nextseq_v1(samplesheet_path)

    return samplesheet


def parse_samplesheet_miseq(samplesheet_path: str):
    """
    """
    samplesheet = []
    version = _determine_samplesheet_version(samplesheet_path, 'miseq')
    if version == 1:
        samplesheet = _parse_samplesheet_miseq_v1(samplesheet_path)

    return samplesheet


def parse_samplesheet_nextseq(samplesheet_path: str):
    """
    """
    samplesheet = None
    version = _determine_samplesheet_version(samplesheet_path, 'nextseq')
    if version == 1:
        samplesheet = _parse_samplesheet_nextseq_v1(samplesheet_path)

    return samplesheet


def parse_samplesheet_gridion(samplesheet_path: Path):
    """
    """
    samplesheet = []
    with open(samplesheet_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'alias' in row:
                alias_split = row['alias'].split('_', 1)
                if len(alias_split) == 2:
                    library_id, project_id = alias_split
                    row['library_id'] = library_id
                    row['project_id'] = project_id
            samplesheet.append(row)

    return samplesheet


def parse_samplesheet(samplesheet_path: str, instrument_type: str, instrument_model: str) -> Optional[dict[str, object]]:
    """
    :param samplesheet_path:
    :type samplesheet_path: str
    :param instrument_type: One of `ILLUMINA` or `NANOPORE`
    :type instrument_type: str
    :param instrument_model: One of `MISEQ`, `NEXTSEQ`, `GRIDION`, `PROMETHION`
    :type instrument_model: str
    """
    samplesheet = None
    if instrument_model == 'MISEQ':
        samplesheet = parse_samplesheet_miseq(samplesheet_path)
    elif instrument_model == 'NEXTSEQ':
        samplesheet = parse_samplesheet_nextseq(samplesheet_path)
    elif instrument_model == 'GRIDION':
        samplesheet = parse_samplesheet_gridion(samplesheet_path)

    return samplesheet


def samplesheet_to_sequenced_libraries(parsed_samplesheet, instrument_model):
    """
    """
    sequenced_libraries = []
    if instrument_model == 'MISEQ':
        if 'data' in parsed_samplesheet:
            for data_record in parsed_samplesheet['data']:
                sequenced_library = {
                    'library_id': None,
                    'project_id_samplesheet': None,
                    'index': None,
                    'index2': None,
                }
                # The library ID that we want is sometimes under 'sample_id' and sometimes under 'sample_name'
                # The instrument will automatically label samples using an ID like 'S1', 'S2', etc in the other field.
                #
                # If one of 'sample_id' or 'sample_name' is blank and the other isn't then we take the non-blank one
                #
                # Otherwise we take the 'sample_name'
                if 'sample_name' in data_record:
                    if re.match("S\\d+$", data_record['sample_id']) and not re.match("S\\d+$", data_record['sample_name']):
                        sequenced_library['library_id'] = data_record['sample_name']
                    elif re.match("S\\d+$", data_record['sample_name']) and not re.match("S\\d+$", data_record['sample_id']):
                        sequenced_library['library_id'] = data_record['sample_id']
                    elif data_record['sample_id'] == '' and data_record['sample_name'] != '':
                        sequenced_library['library_id'] = data_record['sample_name']
                    elif data_record['sample_name'] == '' and data_record['sample_id'] != '':
                        sequenced_library['library_id'] = data_record['sample_id']
                    else:
                        sequenced_library['library_id'] = data_record['sample_name']
                else:
                    sequenced_library['library_id'] = data_record['sample_id']
                sequenced_library['library_id'] = sequenced_library['library_id'].replace('_', '-')
                sequenced_library['project_id_samplesheet'] = data_record.get('sample_project', None)
                sequenced_library['index'] = data_record.get('index', None)
                sequenced_library['index2'] = data_record.get('index2', None)
                sequenced_libraries.append(sequenced_library)

    elif instrument_model == 'NEXTSEQ':
        sequenced_libraries_by_library_id = {}
        if 'bclconvert_data' in parsed_samplesheet:
            for bclconvert_record in parsed_samplesheet['bclconvert_data']:
                sequenced_library = {
                    'library_id': None,
                    'project_id_samplesheet': None,
                    'index': None,
                    'index2': None,
                }
                sequenced_library['library_id'] = bclconvert_record['sample_id']
                sequenced_library['index'] = bclconvert_record['index']
                sequenced_library['index2'] = bclconvert_record['index2']
                sequenced_libraries_by_library_id[sequenced_library['library_id']] = sequenced_library
        if 'cloud_data' in parsed_samplesheet:
            for cloud_data_record in parsed_samplesheet['cloud_data']:
                library_id = cloud_data_record.get('sample_id', None)
                samplesheet_project_id = cloud_data_record.get('project_name', None)
                if library_id in sequenced_libraries_by_library_id:
                    sequenced_libraries_by_library_id[library_id]['project_id_samplesheet'] = samplesheet_project_id

        for library_id, sequenced_library in sequenced_libraries_by_library_id.items():
            sequenced_libraries.append(sequenced_library)
                

    return sequenced_libraries
