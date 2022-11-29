import json
import interop

summary_field_translation = {
    'ReadNumber': 'read_number',
    'IsIndex': 'is_index',
    'Cluster Count': 'cluster_count',
    'Cluster Count Pf': 'cluster_count_passed_filter',
    'Error Rate': 'error_rate',
    'First Cycle Intensity': 'first_cycle_intensity',
    '% Aligned': 'percent_aligned',
    '% >= Q30': 'percent_bases_greater_or_equal_to_q30',
    '% Occupied': 'percent_occupied',
    'Projected Yield G': 'projected_yield',
    'Reads': 'num_reads',
    'Reads Pf': 'num_reads_passed_filter',
    'Yield G': 'yield_gigabases',
}

summary_int_fields = set([
    'cluster_count',
    'cluster_count_passed_filter',
    'num_reads',
    'num_reads_passed_filter',
])

index_summary_field_translation = {
    'Lane': 'lane',
    'Tile': 'tile',
    'Barcode': 'barcode',
    'Cluster Count': 'cluster_count',
    'Fraction Mapped': 'fraction_mapped',
    'Id': 'barcode_id',
    'Index1': 'index_1',
    'Index2': 'index_2',
    'Project Name': 'project_name',
    'Sample Id': 'sample_id',
    'SampleID': 'sample_id',
    '% Demux': 'percent_demux',
}

index_summary_int_fields = set([
    'cluster_count',
    'barcode_id',
    'lane',
    'tile',
])

def summary_nonindex(run_dir_path):
    """
    :param run_dir_path: Path to the top-level run directory
    :type run_dir_path: str
    :return:
    :rtype: dict[str, object]
    """
    summary_nonindex_ndarray = interop.summary(run_dir_path, 'NonIndex')

    original_field_names = summary_nonindex_ndarray.dtype.names
    summary_dict = {}

    for s in summary_nonindex_ndarray.tolist():
        summary_dict_original_field_names = dict(zip(original_field_names, s))
        summary_dict_translated_field_names = {}
        for original_field_name in original_field_names:
            if original_field_name in summary_field_translation:
                translated_field_name = summary_field_translation[original_field_name]
                value = summary_dict_original_field_names[original_field_name]
                if translated_field_name in summary_int_fields:
                    summary_dict_translated_field_names[translated_field_name] = int(value)
                else:
                    summary_dict_translated_field_names[translated_field_name] = value
        summary_dict = summary_dict_translated_field_names

    return summary_dict


def summary_read(run_dir_path):
    """
    :param run_dir_path: Path to the top-level run directory
    :type run_dir_path: str
    :return:
    :rtype: dict[str, object]
    """
    summary_read_ndarray = interop.summary(run_dir_path, 'Read')

    original_field_names = summary_read_ndarray.dtype.names
    summary_dicts = []

    for s in summary_read_ndarray.tolist():
        summary_dict_original_field_names = dict(zip(original_field_names, s))
        summary_dict_translated_field_names = {}
        for original_field_name in original_field_names:
            if original_field_name in summary_field_translation:
                translated_field_name = summary_field_translation[original_field_name]
                value = summary_dict_original_field_names[original_field_name]
                if translated_field_name in summary_int_fields:
                    summary_dict_translated_field_names[translated_field_name] = int(value)
                else:
                    summary_dict_translated_field_names[translated_field_name] = value
        # For some reason the 'IsIndex' field has value 89 if true, 78 if false
        if summary_dict_translated_field_names['is_index'] == 89:
            summary_dict_translated_field_names['is_index'] = True
        elif summary_dict_translated_field_names['is_index'] == 78:
            summary_dict_translated_field_names['is_index'] = False
        summary_dicts.append(summary_dict_translated_field_names)

    return summary_dicts


def index_summary_barcode(run_dir_path):
    """
    """
    index_summary_barcode_ndarray = interop.index_summary(run_dir_path, 'Barcode')
    original_field_names = index_summary_barcode_ndarray.dtype.names
    summary_dicts = []

    for s in index_summary_barcode_ndarray.tolist():
        summary_dict_original_field_names = dict(zip(original_field_names, s))
        summary_dict_translated_field_names = {}
        for original_field_name in original_field_names:
            if original_field_name in index_summary_field_translation:
                translated_field_name = index_summary_field_translation[original_field_name]
                value = summary_dict_original_field_names[original_field_name]
                if translated_field_name in index_summary_int_fields:
                    summary_dict_translated_field_names[translated_field_name] = int(value)
                else:
                    summary_dict_translated_field_names[translated_field_name] = value

        summary_dicts.append(summary_dict_translated_field_names)

    print(json.dumps(summary_dicts[0:3], indent=2))
    exit()

    return summary_dicts


def indexing(run_dir_path):
    """
    """
    indexing_ndarray = interop.indexing(run_dir_path)
    original_field_names = indexing_ndarray.dtype.names
    summary_dicts = []
    print(indexing_ndarray.dtype.names)
    print(indexing_ndarray[0])
    for s in indexing_ndarray.tolist():
        summary_dict_original_field_names = dict(zip(original_field_names, s))
        summary_dict_translated_field_names = {}
        for original_field_name in original_field_names:
            if original_field_name in index_summary_field_translation:
                translated_field_name = index_summary_field_translation[original_field_name]
                value = summary_dict_original_field_names[original_field_name]
                if translated_field_name in index_summary_int_fields:
                    summary_dict_translated_field_names[translated_field_name] = int(value)
                else:
                    summary_dict_translated_field_names[translated_field_name] = value

        summary_dicts.append(summary_dict_translated_field_names)

    print(json.dumps(summary_dicts[-1], indent=2))
    print(len(summary_dicts))
    exit()
    return summary_dicts
