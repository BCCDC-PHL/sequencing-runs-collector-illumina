#!/usr/bin/env python3

import argparse
import os
import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import sequencing_runs_service.crud as crud
import sequencing_runs_service.schemas as schemas
import sequencing_runs_service.models as models


def create_db_session(db_url):
    """
    """
    engine = create_engine(
        db_url, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = SessionLocal()

    return session


def run_id_to_date(run_id):
    """
    """
    six_digit_date = run_id.split('_')[0]
    two_digit_year = six_digit_date[0:2]
    four_digit_year = "20" + two_digit_year
    two_digit_month = six_digit_date[2:4]
    two_digit_day = six_digit_date[4:6]

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
    if run.run_id not in existing_run_ids:
        crud.create_sequencing_run(db, run)
    

def main(args):
    db_url = "sqlite:///" + args.db
    db = create_db_session(db_url)

    run_id = os.path.basename(args.run_dir)
    instrument_id = run_id.split('_')[1]
    instrument_type = "nextseq"
    instrument_manufacturer_name = "illumina"
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
    )

    load_sequencing_run(db, sequencing_run)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db')
    parser.add_argument('run_dir')
    args = parser.parse_args()
    main(args)
