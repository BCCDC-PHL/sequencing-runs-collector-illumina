from sqlalchemy.orm import Session

from . import models, schemas

###### Instruments
def get_instruments(db: Session):
    """
    """
    instruments = db.query(models.Instrument).all()

    return instruments


def get_instrument_by_id(db: Session, instrument_id: str):
    """
    """
    instrument = db.query(models.Instrument).filter(models.Instrument.instrument_id == instrument_id).first()
    
    return instrument

def create_instrument(db: Session, instrument: schemas.InstrumentCreate):
    """
    """
    db_instrument = models.Instrument(**instrument.dict())
    db.add(db_instrument)
    db.commit()
    db.refresh(db_instrument)
    
    return db_instrument


###### Sequencing Runs
def get_sequencing_runs_by_instrument_id(db: Session, instrument_id: str, skip: int = 0, limit: int = 100):
    """
    """
    sequencing_runs = db.query(models.SequencingRun) \
                        .filter(models.Instrument.instrument_id == instrument_id) \
                        .offset(skip).limit(limit).all()

    return sequencing_runs


def get_sequencing_run_by_id(db: Session, run_id: str):
    """
    """
    sequencing_runs = db.query(models.SequencingRun) \
             .filter(models.SequencingRun.run_id == run_id) \
             .offset(skip).limit(limit).all()

    return sequencing_runs


def create_sequencing_run(db: Session, sequencing_run: schemas.SequencingRunCreate):
    """
    """
    db_sequencing_run = models.SequencingRun(
        instrument_id = sequencing_run.instrument.id,
        run_id = sequencing_run.run_id,
        run_date = sequencing_run.run_date,
    )
    db.add(db_sequencing_run)
    db.commit()
    db.refresh(db_sequencing_run)

    return db_sequencing_run
