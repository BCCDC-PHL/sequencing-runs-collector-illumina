#!/usr/bin/env python

import argparse
import datetime
import glob
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
    args = parser.parse_args()

    config = {}

    try:
        log_level = getattr(logging, args.log_level.upper())
    except AttributeError as e:
        log_level = logging.INFO

    logging.basicConfig(
        format='{"timestamp": "%(asctime)s.%(msecs)03d", "level": "%(levelname)s", "module": "%(module)s", "function_name": "%(funcName)s", "line_num": %(lineno)d, "message": %(message)s}',
        datefmt='%Y-%m-%dT%H:%M:%S',
        encoding='utf-8',
        level=log_level,
    )
    logging.debug(json.dumps({"event_type": "debug_logging_enabled"}))

    quit_when_safe = False
    scan_interval = DEFAULT_SCAN_INTERVAL_SECONDS

    while(True):
        if quit_when_safe:
            exit(0)
        try:
            if args.config:
                try:
                    config = sequencing_runs_collector.config.load_config(args.config)
                    logging.info(json.dumps({
                        "event_type": "config_loaded",
                        "config_file": os.path.abspath(args.config)
                    }))
                except json.decoder.JSONDecodeError as e:
                    # If we fail to load the config file, we continue on with the
                    # last valid config that was loaded.
                    logging.error(json.dumps({
                        "event_type": "load_config_failed",
                        "config_file": os.path.abspath(args.config)
                    }))

            scan_start_timestamp = datetime.datetime.now()
            existing_run_output_ids = []
            existing_run_output_dirs_glob = os.path.join(str(config['output_directory']), '*', '*')
            existing_run_output_dirs = glob.glob(existing_run_output_dirs_glob)
            for existing_run_output_dir in existing_run_output_dirs:
                existing_run_output_ids.append(os.path.basename(existing_run_output_dir))

            for run in core.scan(config):
                if run is not None:
                    try:
                        config = sequencing_runs_collector.config.load_config(args.config)
                        logging.info(json.dumps({
                            "event_type": "config_loaded",
                            "config_file": os.path.abspath(args.config)
                        }))
                    except json.decoder.JSONDecodeError as e:
                        logging.error(json.dumps({
                            "event_type": "load_config_failed",
                            "config_file": os.path.abspath(args.config)
                        }))

                    
                    if run['run_id'] in existing_run_output_ids:
                        logging.debug(json.dumps({'event_type': 'skipped_existing_run', 'run': run}))
                        continue
                    if run['instrument_type'] == 'ILLUMINA':
                        timestamp_collect_run_start = datetime.datetime.now()
                        logging.info(json.dumps({
                            'event_type': 'collect_run_start',
                            'run_id': run['run_id'],
                            'run_dir': run['run_dir']
                        }))
                        collected_run = core.collect_illumina_run(config, run)
                        timestamp_collect_run_complete = datetime.datetime.now()
                        logging.info(json.dumps({
                            'event_type': 'collect_run_complete',
                            'run_id': run['run_id'],
                            'collect_run_duration_seconds': (timestamp_collect_run_complete - timestamp_collect_run_start).total_seconds()
                        }))
                        if collected_run is None:
                            logging.error(json.dumps({
                                'event_type': 'collect_run_returned_none',
                                'sequencing_run_id': run['run_id'],
                            }))
                            continue
                        
                        run_output_dir = os.path.join(str(config['output_directory']), 'illumina', str(run['run_id']))
                        os.makedirs(run_output_dir)
                        core.write_collected_illumina_run(collected_run, run_output_dir)
                        logging.info(json.dumps({
                            'event_type': 'run_data_written',
                            'run_id': run['run_id'],
                            'output_dir': os.path.abspath(run_output_dir)
                        }))

                    elif run['instrument_type'] == 'NANOPORE':
                        collected_run = core.collect_nanopore_run(config, run)
                        if collected_run is None:
                            logging.error(json.dumps({
                                'event_type': 'collect_run_returned_none',
                                'sequencing_run_id': run['run_id'],
                            }))
                            continue

                        run_output_dir = os.path.join(str(config['output_directory']), 'nanopore', str(run['run_id']))
                        os.makedirs(run_output_dir)
                        core.write_collected_nanopore_run(collected_run, run_output_dir)
                        logging.info(json.dumps({
                            'event_type': 'run_data_written',
                            'run_id': run['run_id'],
                            'output_dir': os.path.abspath(run_output_dir)
                        }))
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
