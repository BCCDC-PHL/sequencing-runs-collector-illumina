import logging

from sqlalchemy import select, delete, and_
from sqlalchemy.orm import Session

from sequencing_runs_db.models import *

###### Instruments
def get_instruments_illumina(db: Session):
    """
    """
    db_instruments = db.query(InstrumentIllumina).all()

    return db_instruments


def get_instruments_nanopore(db: Session):
    """
    """
    db_instruments = db.query(InstrumentNanopore).all()

    return db_instruments


def get_instrument_illumina_by_id(db: Session, instrument_id: str):
    """
    """
    db_instrument = db.query(InstrumentIllumina).filter(
        InstrumentIllumina.instrument_id == instrument_id
    ).one_or_none()
    
    return db_instrument


def create_instrument_illumina(db: Session, instrument, commit=True):
    """
    """
    db_instrument = None
    existing_instrument = db.query(InstrumentIllumina).filter(
        InstrumentIllumina.instrument_id == instrument['instrument_id']
    ).one_or_none()

    if existing_instrument is None:
        db_instrument = InstrumentIllumina(**instrument)
        db.add(db_instrument)
        if commit:
            db.commit()
            db.refresh(db_instrument)
    else:
        db_instrument = existing_instrument
    
    return db_instrument


def create_instrument_nanopore(db: Session, instrument, commit=True):
    """
    """
    db_instrument = None

    existing_instrument = db.query(InstrumentNanopore).filter(
        InstrumentNanopore.instrument_id == instrument['instrument_id']
    ).one_or_none()
    
    if existing_instrument is None:
        db_instrument = InstrumentNanopore(**instrument)
        db.add(db_instrument)
        if commit:
            db.commit()
            db.refresh(db_instrument)
    
    return db_instrument


###### Sequencing Runs
def get_sequencing_runs_illumina(db: Session):
    """
    """
    db_sequencing_runs = db.query(SequencingRunIllumina).all()

    return db_sequencing_runs


def get_sequencing_runs_illumina_by_instrument_id(db: Session, instrument_id: str, skip: int = 0, limit: int = 100):
    """
    """
    db_sequencing_runs = None

    instrument = get_instrument_illumina_by_id(db, instrument_id)
    
    if instrument is not None:
        sequencing_runs = db.query(SequencingRunIllumina).filter(
            SequencingRunIllumina.instrument_id == instrument.id
        ).offset(skip).limit(limit).all()

    return db_sequencing_runs


def get_sequencing_run_illumina_by_id(db: Session, run_id: str):
    """
    """
    db_sequencing_run = db.query(SequencingRunIllumina).filter(
        SequencingRunIllumina.sequencing_run_id == run_id
    ).one_or_none()

    return db_sequencing_run


def create_sequencing_run_illumina(db: Session, sequencing_run, commit=True):
    """
    """
    db_sequencing_run = None

    existing_instrument = db.query(InstrumentIllumina).filter(
        InstrumentIllumina.instrument_id == sequencing_run['instrument_id']
    ).one_or_none()

    if existing_instrument is not None:
        db_sequencing_run = SequencingRunIllumina(
            instrument_id = existing_instrument.id,
            sequencing_run_id = sequencing_run['sequencing_run_id'],
            run_date = sequencing_run['run_date'],
            cluster_count = sequencing_run['cluster_count'],
            cluster_count_passed_filter = sequencing_run['cluster_count_passed_filter'],
            error_rate = sequencing_run['error_rate'],
            q30_percent = sequencing_run['q30_percent'],
            projected_yield_gigabases = sequencing_run['projected_yield_gigabases'],
            num_reads = sequencing_run['num_reads'],
            num_reads_passed_filter = sequencing_run['num_reads_passed_filter'],
            yield_gigabases = sequencing_run['yield_gigabases'],
        )
        db.add(db_sequencing_run)
        if commit:
            db.commit()
            db.refresh(db_sequencing_run)

    return db_sequencing_run


def create_sequencing_run_nanopore(db: Session, sequencing_run, commit=True):
    """
    """
    db_sequencing_run = None

    existing_instrument = db.query(InstrumentNanopore).filter(
        InstrumentNanopore.instrument_id == sequencing_run['instrument_id']
    ).one_or_none()

    if existing_instrument is not None:
        existing_sequencing_run = db.query(SequencingRunNanopore).filter(
            SequencingRunNanopore.sequencing_run_id == sequencing_run['sequencing_run_id']
        ).one_or_none()
        if existing_sequencing_run is None:
            sequencing_run['instrument_id'] = existing_instrument.id
            db_sequencing_run_nanopore_fields = [
                'sequencing_run_id',
                'instrument_id',
                'flowcell_id',
                'flowcell_product_code',
                'run_date',
                'protocol_id',
                'protocol_run_id',
                'acquisition_run_id',
                'timestamp_acquisition_started',
                'timestamp_acquisition_stopped',
                'timestamp_processing_stopped',
                'num_reads_total',
                'num_reads_passed_filter',
                'yield_gigabases',
            ]

            filtered_sequencing_run = {
                k: sequencing_run.get(k, None) for k in db_sequencing_run_nanopore_fields
            }
            db_sequencing_run = SequencingRunNanopore(**filtered_sequencing_run)
            db.add(db_sequencing_run)
            if commit:
                db.commit()
                db.refresh(db_sequencing_run)

    return db_sequencing_run



def delete_sequencing_run_illumina(db: Session, run_id: str, commit=True):
    """
    Delete all database records for a sequencing run.

    :param db: Database session
    :type db: sqlalchemy.orm.Session
    :param run_id: Sequencing Run ID
    :type run_id: str
    :return: All deleted records for sample.
    :rtype: list[SequencingRunIllumina]
    """
    db_sequencing_run = db.query(SequencingRunIllumina).filter(
        SequencingRunIllumina.sequencing_run_id == run_id
    ).one_or_none()

    if db_sequencing_run is not None:
        db.delete(db_sequencing_run)
        if commit:
            db.commit()

    return db_sequencing_run


###### Projects
def get_projects(db: Session):
    """
    """
    projects = db.query(Project).all()

    return projects


def get_project_by_id(db: Session, project_id):
    """
    """
    project = db.query(Project).filter(
        Project.project_id == project_id
    ).one_or_none()

    return project


def create_project(db: Session, project, commit=True):
    """
    """
    db_project = None
    existing_project = db.query(Project).filter(
        Project.project_id == project['project_id']
    ).one_or_none()

    if existing_project is None:
        db_project = Project(
            project_id = project.project_id,
        )
        db.add(db_project)

        if commit:
            db.commit()
            db.refresh(db_project)

    return db_project


###### Libraries
def get_libraries_by_sequencing_run_illumina_id(db: Session, run_id: str, skip: int = 0, limit: int = 100):
    """
    """
    db_libraries = None

    existing_sequencing_run = db.query(SequencingRunIllumina).filter(
        SequencingRunIllumina.run_id == run_id
    ).one_or_none()
    
    if existing_sequencing_run is not None:
        db_libraries = db.query(SequencedLibraryIllumina).filter(
            SequencedLibraryIllumina.sequencing_run_id == existing_sequencing_run.id
        ).offset(skip).limit(limit).all()

    return db_libraries


def get_illumina_libraries_by_project_id(db: Session, project_id: str, skip: int = 0, limit: int = 100):
    """
    """
    db_libraries = db.query(SequencedLibraryIllumina).filter(
        Project.project_id == project_id
    ).offset(skip).limit(limit).all()

    return db_libraries


def create_libraries_illumina(db: Session, libraries: list[dict], sequencing_run: dict, commit=True):
    """
    Create a set of sequenced illumina library records in the database.

    :param db: Database session.
    :type db: sqlalchemy.orm.Session
    :param samples:
    :type samples: list[schemas.SampleCreate]
    :param sequencing_run:
    :type sequencing_run: schemas.SequencingRun
    :return: None
    :rtype: NoneType
    """
    db_libraries = []
    existing_instrument = db.query(InstrumentIllumina).filter(
        InstrumentIllumina.instrument_id == sequencing_run['instrument_id']
    ).one_or_none()

    existing_sequencing_run = db.query(SequencingRunIllumina).filter(
        SequencingRunIllumina.sequencing_run_id == sequencing_run['sequencing_run_id']
    ).one_or_none()

    if existing_instrument is not None and existing_sequencing_run is not None:
        for library in libraries:
            existing_project = db.query(Project).filter(
                Project.project_id == library['library_id']
            ).one_or_none()

            db_library = SequencedLibraryIllumina(
                library_id = library['library_id'],
                sequencing_run_id = existing_sequencing_run.id,
                samplesheet_project_id = library['samplesheet_project_id'],
                num_reads = library['num_reads'],
                num_bases = library['num_bases'],
                q30_rate = library['q30_rate'],
            )
            if existing_project is not None:
                db_library.project_id = existing_project.id
            else:
                db_library.project_id = None

            db.add(db_library)
            db_libraries.append(db_library)

    if commit:
        db.commit()

    return db_libraries


###### Fastq Files
def create_fastq_file(db: Session, fastq_file, commit=True):
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
    db_fastq_file = FastqFile(
        read_type = fastq_file['read_type'],
        filename = fastq_file['filename'],
        md5_checksum = fastq_file['md5_checksum'],
        size_bytes = fastq_file['size_bytes'],
        total_reads = fastq_file['total_reads'],
        total_bases = fastq_file['total_bases'],
        mean_read_length = fastq_file['mean_read_length'],
        max_read_length = fastq_file['max_read_length'],
        min_read_length = fastq_file['min_read_length'],
        q30_rate = fastq_file['q30_rate'],
    )
    db.add(db_fastq_file)
    if commit:
        db.commit()
        db.refresh(db_fastq_file)

    return db_fastq_file
