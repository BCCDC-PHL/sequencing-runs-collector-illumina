#!/usr/bin/env python

import argparse
import datetime
import json
import logging
import os
import time

import sequencing_runs_collector.config
import sequencing_runs_collector.core as core

DEFAULT_SCAN_INTERVAL_SECONDS = 3600.0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    parser.add_argument('--log-level')
    parser.add_argument('--dry-run', action='store_true')
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

    quit_when_safe = False
    scan_interval = DEFAULT_SCAN_INTERVAL_SECONDS

    while(True):
        try:
            if args.config:
                try:
                    config = sequencing_runs_collector.config.load_config(args.config, dry_run=args.dry_run)
                    logging.info(json.dumps({"event_type": "config_loaded", "config_file": os.path.abspath(args.config)}))
                except json.decoder.JSONDecodeError as e:
                    # If we fail to load the config file, we continue on with the
                    # last valid config that was loaded.
                    logging.error(json.dumps({"event_type": "load_config_failed", "config_file": os.path.abspath(args.config)}))

            scan_start_timestamp = datetime.datetime.now()
            for run in core.scan(config):
                if run is not None:
                    try:
                        config = sequencing_runs_collector.config.load_config(args.config, dry_run=args.dry_run)
                        logging.info(json.dumps({"event_type": "config_loaded", "config_file": os.path.abspath(args.config)}))
                    except json.decoder.JSONDecodeError as e:
                        logging.error(json.dumps({"event_type": "load_config_failed", "config_file": os.path.abspath(args.config)}))
                    if run['instrument_type'] == 'ILLUMINA':
                        run_to_submit = core.collect_illumina_run(config, run)
                        # TODO: further validation before submitting
                        if run_to_submit is not None:
                            if 'submit' not in config or config['submit']:
                                core.submit_illumina_run(config, run_to_submit)
                            if 'write_to_file' in config and 'output_directory' in config:
                                if os.path.exists(str(config['output_directory'])) and config['write_to_file']:
                                    output_file_path = os.path.join(str(config['output_directory']), str(run['run_id']) + '.json')
                                    with open(output_file_path, 'w') as f:
                                        json.dump(run_to_submit, f, indent=2)
                                        logging.info(json.dumps({'event_type': 'run_data_written_to_file', 'run_id': run['run_id'], 'output_file_path': os.path.abspath(output_file_path)}))
                        else:
                            logging.debug(json.dumps({'event_type': 'skipped_submitting_run', 'run': run}))
                    elif run['instrument_type'] == 'NANOPORE':
                        run_to_submit = core.collect_nanopore_run(config, run)
                        if 'submit' not in config or config['submit']:
                            core.submit_nanopore_run(config, run_to_submit)
                        if 'write_to_file' in config and 'output_directory' in config:
                            if os.path.exists(str(config['output_directory'])) and config['write_to_file']:
                                output_file_path = os.path.join(str(config['output_directory']), str(run['run_id']) + '.json')
                                with open(output_file_path, 'w') as f:
                                    json.dump(run_to_submit, f, indent=2)
                                    logging.info(json.dumps({'event_type': 'run_data_written_to_file', 'run_id': run['run_id'], 'output_file_path': os.path.abspath(output_file_path)}))
                if quit_when_safe:
                    exit(0)
            scan_complete_timestamp = datetime.datetime.now()
            scan_duration_delta = scan_complete_timestamp - scan_start_timestamp
            scan_duration_seconds = scan_duration_delta.total_seconds()
            logging.info(json.dumps({"event_type": "scan_complete", "scan_duration_seconds": scan_duration_seconds}))

            if quit_when_safe:
                exit(0)

            if "scan_interval_seconds" in config:
                try:
                    scan_interval = float(str(config['scan_interval_seconds']))
                except ValueError as e:
                    scan_interval = DEFAULT_SCAN_INTERVAL_SECONDS
            time.sleep(scan_interval)
        except KeyboardInterrupt as e:
            logging.info(json.dumps({"event_type": "quit_when_safe_enabled"}))
            quit_when_safe = True


if __name__ == '__main__':
    main()
