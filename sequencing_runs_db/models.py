from sqlalchemy import Boolean, Column, ForeignKey, Integer, Float, String, Date
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class InstrumentIllumina(Base):
    __tablename__ = "instrument_illumina"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, unique=True)
    instrument_type = Column(String)
    manufacturer_name = Column(String)
    status = Column(String)
    current_sequencing_run = Column(String)

    sequencing_runs = relationship("SequencingRunIllumina", back_populates="instrument")


class InstrumentNanopore(Base):
    __tablename__ = "instrument_nanopore"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, unique=True)
    instrument_type = Column(String)
    manufacturer_name = Column(String)
    status = Column(String)
    current_sequencing_run = Column(String)

    sequencing_runs = relationship("SequencingRunNanopore", back_populates="instrument")


class SequencingRunIllumina(Base):
    __tablename__ = "sequencing_run_illumina"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True, unique=True)
    instrument_id = Column(Integer, ForeignKey("instrument_illumina.id"))
    run_date = Column(Date)
    cluster_count = Column(Integer)
    cluster_count_passed_filter = Column(Integer)
    error_rate = Column(Float)
    first_cycle_intensity = Column(Float)
    percent_aligned = Column(Float)
    percent_bases_greater_or_equal_to_q30 = Column(Float)
    projected_yield_gigabases = Column(Float)
    num_reads = Column(Integer)
    num_reads_passed_filter = Column(Integer)
    yield_gigabases = Column(Float)

    instrument = relationship("InstrumentIllumina", back_populates="sequencing_runs")
    libraries = relationship("SequencedLibraryIllumina", back_populates="sequencing_run")


class SequencingRunNanopore(Base):
    __tablename__ = "sequencing_run_nanopore"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True, unique=True)
    instrument_id = Column(Integer, ForeignKey("instrument_nanopore.id"))
    run_date = Column(Date)
    num_reads = Column(Integer)
    num_reads_passed_filter = Column(Integer)
    yield_gigabases = Column(Float)

    instrument = relationship("InstrumentNanopore", back_populates="sequencing_runs")
    libraries = relationship("SequencedLibraryNanopore", back_populates="sequencing_run")


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, index=True, unique=True)

    sequenced_illumina_libraries = relationship("SequencedLibraryIllumina", back_populates="project")
    sequenced_nanopore_libraries = relationship("SequencedLibraryNanopore", back_populates="project")


class SequencedLibraryIllumina(Base):
    __tablename__ = "sequenced_library_illumina"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(String, index=True)
    sequencing_run_id = Column(Integer, ForeignKey("sequencing_run_illumina.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    samplesheet_project_id = Column(String)
    num_reads = Column(Integer)
    num_bases = Column(Integer)
    q30_rate = Column(Float)

    sequencing_run = relationship("SequencingRunIllumina", back_populates="samples")
    project = relationship("Project", back_populates="samples")
    fastq_files = relationship("FastqFile", back_populates="sample")


class SequencedLibraryNanopore(Base):
    __tablename__ = "sequenced_library_nanopore"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(String, index=True)
    sequencing_run_id = Column(Integer, ForeignKey("sequencing_run_nanopore.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    num_reads = Column(Integer)
    num_bases = Column(Integer)
    read_n50 = Column(Float)

    sequencing_run = relationship("SequencingRunIllumina", back_populates="samples")
    project = relationship("Project", back_populates="samples")
    fastq_files = relationship("FastqFile", back_populates="sample")


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
