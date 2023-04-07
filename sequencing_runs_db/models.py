from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy import  DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class InstrumentIllumina(Base):
    __tablename__ = "instrument_illumina"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    instrument_id = Column(String, unique=True)
    instrument_type = Column(String)
    instrument_model = Column(String)
    status = Column(String)
    timestamp_status_updated = Column(DateTime)
    
    sequencing_runs = relationship("SequencingRunIllumina", back_populates="instrument")


class InstrumentNanopore(Base):
    __tablename__ = "instrument_nanopore"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    instrument_id = Column(String, unique=True)
    instrument_type = Column(String)
    instrument_model = Column(String)
    status = Column(String)
    timestamp_status_updated = Column(String)

    sequencing_runs = relationship("SequencingRunNanopore", back_populates="instrument")


class SequencingRunIllumina(Base):
    __tablename__ = "sequencing_run_illumina"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sequencing_run_id = Column(String, index=True, unique=True)
    instrument_id = Column(Integer, ForeignKey("instrument_illumina.id"))
    flowcell_id = Column(String)
    run_date = Column(Date)
    cluster_count = Column(Integer)
    cluster_count_passed_filter = Column(Integer)
    error_rate = Column(Float)
    first_cycle_intensity = Column(Float)
    percent_aligned = Column(Float)
    q30_percent = Column(Float)
    projected_yield_gigabases = Column(Float)
    num_reads = Column(Integer)
    num_reads_passed_filter = Column(Integer)
    percent_reads_passed_filter = Column(Float)
    yield_gigabases = Column(Float)

    instrument = relationship("InstrumentIllumina", back_populates="sequencing_runs")
    libraries = relationship("SequencedLibraryIllumina", back_populates="sequencing_run")


class SequencingRunNanopore(Base):
    __tablename__ = "sequencing_run_nanopore"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sequencing_run_id = Column(String, index=True, unique=True)
    instrument_id = Column(Integer, ForeignKey("instrument_nanopore.id"))
    flowcell_id = Column(String)
    flowcell_product_code = Column(String)
    run_date = Column(Date)
    protocol_id = Column(String)
    protocol_run_id = Column(String)
    acquisition_run_id = Column(String)
    timestamp_acquisition_started = Column(DateTime)
    timestamp_acquisition_stopped = Column(DateTime)
    timestamp_processing_stopped = Column(DateTime)
    num_reads_total = Column(Integer)
    num_reads_passed_filter = Column(Integer)
    yield_gigabases = Column(Float)

    instrument = relationship("InstrumentNanopore", back_populates="sequencing_runs")
    libraries = relationship("SequencedLibraryNanopore", back_populates="sequencing_run")
    acquisition_runs = relationship("AcquisitionRunNanopore", back_populates="sequencing_run")


class AcquisitionRunNanopore(Base):
    __tablename__ = "acquisition_run_nanopore"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sequencing_run_id = Column(Integer, ForeignKey("sequencing_run_nanopore.id"))
    acquisition_run_id = Column(String, index=True, unique=True)
    num_reads_total = Column(Integer)
    num_reads_passed_filter = Column(Integer)
    num_reads_skipped = Column(Integer)
    percent_reads_passed_filter = Column(Float)
    num_bases_total = Column(Integer)
    num_bases_passed_filter = Column(Integer)
    percent_bases_passed_filter = Column(Float)
    timestamp_acquisition_started = Column(DateTime)
    timestamp_acquisition_stopped = Column(DateTime)
    startup_state = Column(String)
    state = Column(String)
    finishing_state = Column(String)
    stop_reason = Column(String)
    purpose = Column(String)
    basecalling_config_filename = Column(String)

    sequencing_run = relationship("SequencingRunNanopore", back_populates="acquisition_runs")


class AcquisitionSnapshotNanopore(Base):
    __tablename__ = "acquisition_snapshot_nanopore"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    acquisition_run_id = Column(Integer, ForeignKey("acquisition_run_nanopore.id"))
    acquisition_elapsed_seconds = Column(Integer)
    num_reads_total = Column(Integer)
    fraction_basecalled = Column(Float)
    fraction_skipped = Column(Float)
    num_reads_passed_filter = Column(Integer)
    num_reads_skipped = Column(Integer)
    num_bases_total = Column(Integer)
    num_bases_passed_filter = Column(Integer)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(String, index=True, unique=True)

    sequenced_illumina_libraries = relationship("SequencedLibraryIllumina", back_populates="project")
    sequenced_nanopore_libraries = relationship("SequencedLibraryNanopore", back_populates="project")
    aliases = relationship("ProjectAlias", back_populates="project")


class ProjectAlias(Base):
    __tablename__ = "project_alias"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    alias = Column(String)

    project = relationship("Project", back_populates="aliases")


class SequencedLibraryIllumina(Base):
    __tablename__ = "sequenced_library_illumina"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    library_id = Column(String, index=True)
    sequencing_run_id = Column(Integer, ForeignKey("sequencing_run_illumina.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    samplesheet_project_id = Column(String)
    num_reads = Column(Integer)
    num_bases = Column(Integer)
    q30_rate = Column(Float)

    sequencing_run = relationship("SequencingRunIllumina", back_populates="libraries")
    project = relationship("Project", back_populates="sequenced_illumina_libraries")


class SequencedLibraryNanopore(Base):
    __tablename__ = "sequenced_library_nanopore"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(String, index=True)
    sequencing_run_id = Column(Integer, ForeignKey("sequencing_run_nanopore.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    num_reads = Column(Integer)
    num_bases = Column(Integer)
    read_n50 = Column(Float)

    sequencing_run = relationship("SequencingRunNanopore", back_populates="libraries")
    project = relationship("Project", back_populates="sequenced_nanopore_libraries")


class FastqFile(Base):
    __tablename__ = 'fastq_file'

    id = Column(Integer, primary_key=True, index=True)
    read_type = Column(String)
    filename = Column(String)
    md5_checksum = Column(String)
    size_bytes = Column(Integer)
    num_reads = Column(Integer)
    num_bases = Column(Integer)
    mean_read_length = Column(Float)
    max_read_length = Column(Integer)
    min_read_length = Column(Integer)
    q30_rate = Column(Float)
