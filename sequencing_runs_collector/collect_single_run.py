#!/usr/bin/env python

import argparse
import datetime
import json
import logging
import os
import re
import time

import sequencing_runs_collector.config
import sequencing_runs_collector.core as core
import sequencing_runs_collector.illumina as illumina
import sequencing_runs_collector.nanopore as nanopore

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    parser.add_argument('--log-level')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--run-dir')
    
    args = parser.parse_args()

    config = {}

    try:
        log_level = getattr(logging, args.log_level.upper())
    except AttributeError as e:
        log_level = logging.INFO

    logging.basicConfig(
        format='{"timestamp": "%(asctime)s.%(msecs)03d", "level": "%(levelname)s", "module", "%(module)s", "function_name": "%(funcName)s", "line_num", %(lineno)d, "message": %(message)s}',
        datefmt='%Y-%m-%dT%H:%M:%S',
        encoding='utf-8',
        level=log_level,
    )
    logging.debug(json.dumps({"event_type": "debug_logging_enabled"}))

    if args.config:
        try:
            config = sequencing_runs_collector.config.load_config(args.config, dry_run=args.dry_run)
            logging.info(json.dumps({"event_type": "config_loaded", "config_file": os.path.abspath(args.config)}))
        except json.decoder.JSONDecodeError as e:
            # If we fail to load the config file, we continue on with the
            # last valid config that was loaded.
            logging.error(json.dumps({"event_type": "load_config_failed", "config_file": os.path.abspath(args.config)}))
            exit(-1)
            
    run = {}
    instrument_type = None
    instrument_model = None
    run_id = os.path.basename(args.run_dir.rstrip('/'))
    if re.match(illumina.MISEQ_RUN_ID_REGEX, run_id):
        instrument_type = "ILLUMINA"
        instrument_model = "MISEQ"
    elif re.match(illumina.NEXTSEQ_RUN_ID_REGEX, run_id):
        instrument_type = "ILLUMINA"
        instrument_model = "NEXTSEQ"
    elif re.match(nanopore.GRIDION_RUN_ID_REGEX, run_id):
        instrument_type = "NANOPORE"
        instrument_model = "GRIDION"
    elif re.match(nanopore.PROMETHION_RUN_ID_REGEX, run_id):
        instrument_type = "NANOPORE"
        instrument_model = "PROMETHION"
    else:
        logging.info(json.dumps({'event_type': 'failed_to_determine_run_type', 'directory': os.path.abspath(args.run_dir)}))
        exit(-1)
    if os.path.exists(args.run_dir) and instrument_model != None and os.path.exists(os.path.join(args.run_dir, "upload_complete.json")):
        logging.debug(json.dumps({"event_type": "sequencing_run_found", "sequencing_run_id": run_id}))

        run = {
            "run_id": run_id,
            "instrument_type": instrument_type,
            "instrument_model": instrument_model,
            "run_dir": os.path.abspath(args.run_dir),
        }

        if run['instrument_type'] == 'ILLUMINA':
            run_to_submit = core.collect_illumina_run(config, run)
            # TODO: further validation before submitting
            if run_to_submit is not None:
                if 'submit' not in config or config['submit']:
                    core.submit_illumina_run(config, run_to_submit)
                else:
                    if 'write_to_file' in config and 'output_directory' in config:
                        if os.path.exists(str(config['output_directory'])) and config['write_to_file']:
                            output_file_path = os.path.join(str(config['output_directory']), run['run_id'] + '.json')
                            with open(output_file_path, 'w') as f:
                                json.dump(run_to_submit, f, indent=2)
                                logging.info(json.dumps({'event_type': 'run_data_written_to_file', 'run_id': run['run_id'], 'output_file_path': os.path.abspath(output_file_path)}))
            else:
                logging.debug(json.dumps({'event_type': 'skipped_submitting_run', 'run': run}))
        elif run['instrument_type'] == 'NANOPORE':
            run_to_submit = core.collect_nanopore_run(config, run)
            if 'submit' not in config or config['submit']:
                core.submit_nanopore_run(config, run_to_submit)
            else:
                if 'write_to_file' in config and 'output_directory' in config:
                    if os.path.exists(str(config['output_directory'])) and config['write_to_file']:
                        output_file_path = os.path.join(str(config['output_directory']), run['run_id'] + '.json')
                        with open(output_file_path, 'w') as f:
                            json.dump(run_to_submit, f, indent=2)
                            logging.info(json.dumps({'event_type': 'run_data_written_to_file', 'run_id': run['run_id'], 'output_file_path': os.path.abspath(output_file_path)}))
                

if __name__ == '__main__':
    main()
