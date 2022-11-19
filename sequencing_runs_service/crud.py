import logging

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
    instrument = db.query(models.Instrument) \
                   .filter(models.Instrument.instrument_id == instrument_id) \
                   .first()
    
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
def get_sequencing_runs(db: Session):
    """
    """
    sequencing_runs = db.query(models.SequencingRun).all()

    return sequencing_runs


def get_sequencing_runs_by_instrument_id(db: Session, instrument_id: str, skip: int = 0, limit: int = 100):
    """
    """
    instrument = get_instrument_by_id(db, instrument_id)
    sequencing_runs = db.query(models.SequencingRun) \
                        .filter(models.SequencingRun.instrument_id == instrument.id) \
                        .offset(skip).limit(limit).all()

    return sequencing_runs


def get_sequencing_run_by_id(db: Session, run_id: str):
    """
    """
    sequencing_run = db.query(models.SequencingRun) \
                       .filter(models.SequencingRun.run_id == run_id) \
                       .first()

    return sequencing_run


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


###### Projects
def get_projects(db: Session):
    """
    """
    projects = db.query(models.Project).all()

    return projects


def get_project_by_id(db: Session, project_id):
    """
    """
    project = db.query(models.Project) \
                .filter(models.Project.project_id == project_id) \
                .first()

    return project


def create_project(db: Session, project: schemas.ProjectCreate):
    """
    """
    db_project = models.Project(
        project_id = project.project_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


###### Samples
def get_samples_by_run_id(db: Session, run_id: str, skip: int = 0, limit: int = 100):
    """
    """
    run = db.query(models.SequencingRun) \
                .filter(models.SequencingRun.run_id == run_id) \
                .first()
    samples = db.query(models.Sample) \
                .filter(models.Sample.run_id == run.id) \
                .offset(skip).limit(limit).all()

    return samples


def get_samples_by_project_id(db: Session, project_id: str, skip: int = 0, limit: int = 100):
    """
    """
    samples = db.query(models.Sample) \
                .filter(models.Project.project_id == project_id) \
                .offset(skip).limit(limit).all()
    logging.info(samples)

    return samples


def create_samples(db: Session, samples: list[schemas.SampleCreate], sequencing_run: schemas.SequencingRun):
    """
    """
    db_samples = []
    for sample in samples:
        db_sample = models.Sample(
            run_id = sequencing_run.id,
            sample_id = sample.sample_id,
            project_id = sample.project_id,
        )
        db.add(db_sample)

    db.commit()
