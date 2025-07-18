import json
import os
import csv

from pathlib import Path

def load_config(config_path: Path) -> dict[str, object]:
    """
    Load the app config from JSON file

    :param config_path: Path to config file
    :type config_path: Path
    :return: App config
    :rtype: dict
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    config['project_id_translation'] = {}

    if 'project_id_translation_file' in config and os.path.exists(config['project_id_translation_file']):
        with open(config['project_id_translation_file'], 'r') as f:
            reader = csv.DictReader(f, dialect='unix')
            for row in reader:
                samplesheet_project_id = row.get('samplesheet_project_id', None)
                translated_project_id = row.get('translated_project_id', None)
                if samplesheet_project_id is not None and translated_project_id is not None:
                    config['project_id_translation'][samplesheet_project_id] = translated_project_id

    return config
