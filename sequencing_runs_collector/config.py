import json
import os
import csv

def load_config(config_path: str) -> dict[str, object]:
    with open(config_path, 'r') as f:
        config = json.load(f)

    config['project_id_translation'] = {}

    if 'project_id_translation_file' in config and os.path.exists(config['project_id_translation_file']):
        # TODO: Load the translation file
        pass
        

    return config
