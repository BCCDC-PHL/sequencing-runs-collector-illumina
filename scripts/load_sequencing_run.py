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

import sequencing_runs_db.crud as crud
import sequencing_runs_db.util as util
import sequencing_runs_db.parsers.samplesheet as samplesheet
import sequencing_runs_db.parsers.runinfo as runinfo
import sequencing_runs_db.parsers.primary_analysis_metrics as primary_analysis_metrics
import sequencing_runs_db.parsers.interop as interop
import sequencing_runs_db.parsers.nanopore as nanopore
import sequencing_runs_db.parsers.fastq as fastq


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
    run_date = None
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


def get_instrument_info_by_sequencing_run_id(sequencing_run_id):
    """
    """
    miseq_run_id_regex = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
    nextseq_run_id_regex = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"
    gridion_run_id_regex = "\d{8}_\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}"
    promethion_run_id_regex = "\d{8}_\d{4}_P2S_[0-9]{5}-\d{1}_[A-Z0-9]+_[a-z0-9]{8}"

    instrument = {}
    if re.match(miseq_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "ILLUMINA"
        instrument['instrument_model'] = "MISEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(nextseq_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "ILLUMINA"
        instrument['instrument_model'] = "NEXTSEQ"
        instrument['instrument_id'] = sequencing_run_id.split('_')[1]
    elif re.match(gridion_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "NANOPORE"
        instrument['instrument_model'] = "GRIDION"
    elif re.match(promethion_run_id_regex, sequencing_run_id):
        instrument['instrument_type'] = "NANOPORE"
        instrument['instrument_model'] = "PROMETHION"

    return instrument
    

def main(args):
    db_url = "sqlite:///" + args.db
    db = create_db_session(db_url)

    project_id_lookup = {}
    if args.project_id_translation_table:
        project_id_lookup = parse_project_id_translation(args.project_id_translation_table)

    sequencing_run_id = os.path.basename(args.run_dir.rstrip('/'))

    sequencing_run = {
        'sequencing_run_id': sequencing_run_id
    }
    run_date = run_id_to_date(sequencing_run_id)
    sequencing_run['run_date'] = run_date

    instrument = get_instrument_info_by_sequencing_run_id(sequencing_run_id)

    sequencing_run.update(instrument)

    if instrument['instrument_type'] == "ILLUMINA":
        interop_summary = interop.summary_nonindex(os.path.join(args.run_dir))
        sequencing_run.update(interop_summary)
    else:
        final_summary_files = glob.glob(os.path.join(args.run_dir, 'final_summary_*.txt'))
        final_summary_file = None
        if len(final_summary_files) > 0:
            # There *should* be only one of these files.
            # If there are more than one, we arbitrarily take the first
            final_summary_file = final_summary_files[0]
            if os.path.exists(final_summary_file):
                final_summary = nanopore.parse_final_summary(final_summary_file)
                instrument['instrument_id'] = final_summary['instrument_id']
                sequencing_run.update(final_summary)
                
        sequencing_run_report_files = glob.glob(os.path.join(args.run_dir, 'report_*.json'))
        final_summary_file = None
        if len(sequencing_run_report_files) > 0:
            # There *should* be only one of these files.
            # If there are more than one, we arbitrarily take the first
            sequencing_run_report_file = sequencing_run_report_files[0]
            if os.path.exists(sequencing_run_report_file):
                sequencing_run_report = nanopore.parse_sequencing_run_report(sequencing_run_report_file)
                run_yield = nanopore.collect_run_yield_from_run_report(sequencing_run_report)
                sequencing_run.update(run_yield)
        

    if instrument['instrument_type'] == 'ILLUMINA':
        created_instrument = crud.create_instrument_illumina(db, instrument)
    elif instrument['instrument_type'] == 'NANOPORE':
        created_instrument = crud.create_instrument_nanopore(db, instrument)


    if instrument['instrument_type'] == 'ILLUMINA':
        created_sequencing_run = crud.create_sequencing_run_illumina(db, sequencing_run, commit=False)
    elif instrument['instrument_type'] == 'NANOPORE':
        created_sequencing_run = crud.create_sequencing_run_nanopore(db, sequencing_run, commit=False)

    db.commit()
    exit()
    

    samplesheet_paths = samplesheet.find_samplesheets(args.run_dir, instrument['instrument_type'])
    samplesheet_to_parse = samplesheet.choose_samplesheet_to_parse(samplesheet_paths, instrument['instrument_type'])
    parsed_samplesheet = samplesheet.parse_samplesheet(samplesheet_to_parse, instrument['instrument_type'])

    samples_section_key = None
    project_key = None
    if instrument['instrument_type'] == "ILLUMINA":
        if instrument['instrument_model'] == "NEXTSEQ":
            samples_section_key = "cloud_data"
            project_key = "project_name"
        elif instrument['instrument_model'] == "MISEQ":
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
