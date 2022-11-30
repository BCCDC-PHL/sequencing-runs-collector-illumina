import logging

from sqlalchemy import select, delete, and_
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
        cluster_count = sequencing_run.cluster_count,
        cluster_count_passed_filter = sequencing_run.cluster_count_passed_filter,
        error_rate = sequencing_run.error_rate,
        percent_bases_greater_or_equal_to_q30 = sequencing_run.percent_bases_greater_or_equal_to_q30,
    )
    db.add(db_sequencing_run)
    db.commit()
    db.refresh(db_sequencing_run)

    return db_sequencing_run


def delete_sequencing_run(db: Session, run_id: str):
    """
    Delete all database records for a sequencing run.

    :param db: Database session
    :type db: sqlalchemy.orm.Session
    :param run_id: Sequencing Run ID
    :type run_id: str
    :return: All deleted records for sample.
    :rtype: list[models.SequencingRun]
    """
    sequencing_run_record = db.query(Sample).where(Sample.sample_id == sample_id).one_or_none()

    if sequencing_run_record is not None:
        db.delete(sequencing_run_record)
        db.commit()

    return sequencing_run_record


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
    Create a set of sample records in the database.

    :param db: Database session.
    :type db: sqlalchemy.orm.Session
    :param samples:
    :type samples: list[schemas.SampleCreate]
    :param sequencing_run:
    :type sequencing_run: schemas.SequencingRun
    :return: None
    :rtype: NoneType
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


###### Fastq Files
def create_fastq_file(db: Session, fastq_file: schemas.FastqFileCreate, sample: schemas.Sample):
    """
    Create a fastq file record in the database.

    :param db: Database session.
    :type db: sqlalchemy.orm.Session
    :param fastq_file:
    :type fastq_file: schemas.FastqFileCreate
    :param sample:
    :type sample: schemas.Sample
    :return: created Fastq file record.
    :rtype: models.FastqFile
    """
    db_fastq_file = models.FastqFile(
        sample_id = sample.id,
        read_type = fastq_file.read_type,
        filename = fastq_file.filename,
        md5_checksum = fastq_file.md5_checksum,
        size_bytes = fastq_file.size_bytes,
        total_reads = fastq_file.total_reads,
        total_bases = fastq_file.total_bases,
        mean_read_length = fastq_file.mean_read_length,
        max_read_length = fastq_file.max_read_length,
        min_read_length = fastq_file.min_read_length,
        num_bases_greater_or_equal_to_q30 = fastq_file.num_bases_greater_or_equal_to_q30,
    )
    db.add(db_fastq_file)
    db.commit()
    db.refresh(db_fastq_file)

    return db_fastq_file


def get_fastq_files_by_run_id_by_sample_id(db: Session, run_id: str, sample_id: str):
    """
    """
    fastq_files = []
    run = db.query(models.SequencingRun) \
            .filter(models.SequencingRun.run_id == run_id) \
            .one_or_none()

    if run is not None:
        samples = db.query(models.Sample) \
                    .filter(models.Sample.run_id == run.id) \
                    .filter(models.Sample.sample_id == sample_id) \
                    .all()

        for sample in samples:
            fastq_files_for_sample = db.query(models.FastqFile) \
                                       .filter(models.FastqFile.sample_id == sample.id)
            fastq_files += fastq_files_for_sample


    return fastq_files
