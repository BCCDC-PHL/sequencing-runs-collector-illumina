import json
import os
import csv

def load_config(config_path: str, dry_run=False) -> dict[str, object]:
    with open(config_path, 'r') as f:
        config = json.load(f)

    config['dry_run'] = dry_run

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
