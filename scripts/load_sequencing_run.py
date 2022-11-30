#!/usr/bin/env python3

import argparse
import csv
import datetime
import glob
import json
import os
import re

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import sequencing_runs_service.crud as crud
import sequencing_runs_service.schemas as schemas
import sequencing_runs_service.models as models
import sequencing_runs_service.util as util
import sequencing_runs_service.parsers.samplesheet as samplesheet
import sequencing_runs_service.parsers.runinfo as runinfo
import sequencing_runs_service.parsers.primary_analysis_metrics as primary_analysis_metrics
import sequencing_runs_service.parsers.interop as interop
import sequencing_runs_service.parsers.fastq as fastq


def create_db_session(db_url):
    """
    """
    engine = create_engine(
        db_url, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = SessionLocal()

    return session


def parse_project_id_translation(project_id_translation_path):
    """
    """
    project_id_translation = {}
    with open(project_id_translation_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_id_translation[row['samplesheet_project_id']] = row['sequencing_runs_service_project_id']

    return project_id_translation


def determine_sample_id_key(samplesheet_sample_record):
    """
    It's not always consistent which field to use in the samplesheet for the sample_id.
    Sometimes 'sample_id', sometimes 'sample_name'.
    """

    sample_key_id = "sample_id"
    sample_name_in_record = 'sample_name' in samplesheet_sample_record
    if sample_name_in_record:
        sample_name_not_blank = samplesheet_sample_record['sample_name'] != ""
    else:
        sample_name_not_blank = False
    sample_id_matches_snumber = re.match("S\d+", samplesheet_sample_record['sample_id']) is not None
    conditions_to_use_sample_name = [
        sample_name_in_record,
        sample_name_not_blank,
        sample_id_matches_snumber,
    ]

    if all(conditions_to_use_sample_name):
        sample_key_id = "sample_name"

    return sample_key_id


def run_id_to_date(run_id):
    """
    """
    run_id_date_component = run_id.split('_')[0]
    if len(run_id_date_component) == 6:
        six_digit_date = run_id.split('_')[0]
        two_digit_year = six_digit_date[0:2]
        four_digit_year = "20" + two_digit_year
        two_digit_month = six_digit_date[2:4]
        two_digit_day = six_digit_date[4:6]
        run_date = datetime.date(int(four_digit_year), int(two_digit_month), int(two_digit_day))
    elif len(run_id_date_component) == 8:
        eight_digit_date = run_id.split('_')[0]
        four_digit_year = eight_digit_date[0:4]
        two_digit_month = eight_digit_date[4:6]
        two_digit_day = eight_digit_date[6:8]
        run_date = datetime.date(int(four_digit_year), int(two_digit_month), int(two_digit_day))

    return run_date


def load_instrument(db, instrument):
    """
    """
    existing_instruments = crud.get_instruments(db)
    existing_instrument_ids = set([instrument.instrument_id for instrument in existing_instruments])
    if instrument.instrument_id in existing_instrument_ids:
        instrument = crud.get_instrument_by_id(db, instrument.instrument_id)
    else:
        instrument = crud.create_instrument(db, instrument)

    return instrument


def load_sequencing_run(db, run):
    instrument_id = run.run_id.split('_')[1]
    existing_runs = crud.get_sequencing_runs_by_instrument_id(db, instrument_id)
    existing_run_ids = set([run.run_id for run in existing_runs])
    if run.run_id in existing_run_ids:
        sequencing_run = crud.get_sequencing_run_by_id(db, run.run_id)
    else:
        sequencing_run = crud.create_sequencing_run(db, run)

    return sequencing_run


def load_projects(db, parsed_samplesheet, samples_section_key, project_key, project_id_lookup):
    """
    """
    project_ids_on_run = set()
    db_project_id_by_project_id = {}
    if samples_section_key is not None and project_key is not None:
        for samplesheet_sample_record in parsed_samplesheet[samples_section_key]:
            if samplesheet_sample_record[project_key] != "":
                samplesheet_project_id = samplesheet_sample_record[project_key]
                if samplesheet_project_id in project_id_lookup:
                    project_id = project_id_lookup[samplesheet_project_id]
                else:
                    project_id = samplesheet_project_id
                project_ids_on_run.add(project_id)

        existing_projects = crud.get_projects(db)
        existing_project_ids = set([project.project_id for project in existing_projects])
        for project_id in project_ids_on_run:
            if project_id in existing_project_ids:
                project = crud.get_project_by_id(db, project_id)
            else:
                project = schemas.ProjectCreate(
                    project_id = project_id,
                )
                project = crud.create_project(db, project)

    return db_project_id_by_project_id


def load_samples(db, parsed_samplesheet, samples_section_key, project_key, sequencing_run, db_project_id_by_project_id):
    """
    """
    samples_to_create = []
    for samplesheet_sample_record in parsed_samplesheet[samples_section_key]:
        sample_id_key = determine_sample_id_key(samplesheet_sample_record)
        sample_id = samplesheet_sample_record[sample_id_key]
        project_id = samplesheet_sample_record[project_key]
        if project_id in db_project_id_by_project_id:
            db_project_id = db_project_id_by_project_id[project_id]
        else:
            db_project_id = None

        sample = schemas.SampleCreate(
            sample_id = sample_id,
            project_id = db_project_id,
        )
        samples_to_create.append(sample)

    crud.create_samples(db, samples_to_create, sequencing_run)


def load_fastq_stats(db, fastq_dir, run_id):
    """
    """
    skip = 0
    limit = 100
    current_samples_batch = crud.get_samples_by_run_id(db, run_id, skip, limit)
    while len(current_samples_batch) > 0:
        for sample in current_samples_batch:
            for read_type in ["R1", "R2"]:
                fastq_file_paths = glob.glob(os.path.join(fastq_dir, sample.sample_id + "_*_" + read_type + "_*.fastq*"))
                for fastq_path in fastq_file_paths:
                    filename = os.path.basename(fastq_path)
                    file_stats = os.stat(fastq_path)
                    size_bytes = file_stats.st_size
                    md5_checksum = util.md5(fastq_path)
                    fastq_stats = fastq.collect_fastq_stats(fastq_path)
                    # print(json.dumps(fastq_stats, indent=2))
                    fastq_file = schemas.FastqFileCreate(
                        sample_id = sample.id,
                        read_type = read_type,
                        filename = filename,
                        md5_checksum = md5_checksum,
                        size_bytes = size_bytes,
                        total_reads = fastq_stats['total_reads'],
                        total_bases = fastq_stats['total_bases'],
                        mean_read_length = fastq_stats['mean_read_length'],
                        max_read_length = fastq_stats['max_read_length'],
                        min_read_length = fastq_stats['min_read_length'],
                        num_bases_greater_or_equal_to_q30 = fastq_stats['num_bases_greater_or_equal_to_q30'],
                    )
                    crud.create_fastq_file(db, fastq_file, sample)

        skip += limit
        current_samples_batch = crud.get_samples_by_run_id(db, run_id, skip, limit)

    return None
            


def main(args):
    db_url = "sqlite:///" + args.db
    db = create_db_session(db_url)

    project_id_lookup = {}
    if args.project_id_translation_table:
        project_id_lookup = parse_project_id_translation(args.project_id_translation_table)

    miseq_run_id_regex = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
    nextseq_run_id_regex = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"

    run_id = os.path.basename(args.run_dir.rstrip('/'))

    if re.match(miseq_run_id_regex, run_id):
        instrument_type = "miseq"
        fastq_dir = os.path.join(args.run_dir, 'Data', 'Intensities', 'BaseCalls')
    elif re.match(nextseq_run_id_regex, run_id):
        instrument_type = "nextseq"
        # TODO: select the most recent Analysis dir
        fastq_dir = os.path.join(args.run_dir, 'Analysis', '1', 'Data', 'fastq')
    else:
        instrument_type = None

    if instrument_type == "miseq" or instrument_type == "nextseq":
        instrument_manufacturer_name = "illumina"
        instrument_id = run_id.split('_')[1]
        interop_summary = interop.summary_nonindex(os.path.join(args.run_dir))
    else:
        instrument_manufacturer_name = None
        instrument_id = None

    run_date = run_id_to_date(run_id)

    instrument = schemas.InstrumentCreate(
        instrument_id = instrument_id,
        instrument_type = instrument_type,
        manufacturer_name = instrument_manufacturer_name,
    )

    instrument = load_instrument(db, instrument)

    sequencing_run = schemas.SequencingRunCreate(
        instrument = instrument,
        run_id = run_id,
        run_date = run_date,
        cluster_count = interop_summary['cluster_count'],
        cluster_count_passed_filter = interop_summary['cluster_count_passed_filter'],
        error_rate = interop_summary['error_rate'],
        percent_bases_greater_or_equal_to_q30 = interop_summary['percent_bases_greater_or_equal_to_q30'],
    )

    sequencing_run = load_sequencing_run(db, sequencing_run)

    samplesheet_paths = samplesheet.find_samplesheets(args.run_dir, instrument_type)
    samplesheet_to_parse = samplesheet.choose_samplesheet_to_parse(samplesheet_paths, instrument_type)
    parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_to_parse, instrument_type)

    samples_section_key = None
    project_key = None
    if instrument_type == "nextseq":
        samples_section_key = "cloud_data"
        project_key = "project_name"
    elif instrument_type == "miseq":
        samples_section_key = "data"
        project_key = "sample_project"


    # First load all projects on run that aren't already in the db
    load_projects(db, parsed_samplesheet, samples_section_key, project_key, project_id_lookup)

    existing_projects = crud.get_projects(db)
    db_project_id_by_project_id = {project.project_id: int(project.id) for project in existing_projects}

    # Then, now that we can easily look up db project IDs, load the samples:
    load_samples(db, parsed_samplesheet, samples_section_key, project_key, sequencing_run, db_project_id_by_project_id)

    load_fastq_stats(db, fastq_dir, run_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db')
    parser.add_argument('--project-id-translation-table')
    parser.add_argument('run_dir')
    args = parser.parse_args()
    main(args)
