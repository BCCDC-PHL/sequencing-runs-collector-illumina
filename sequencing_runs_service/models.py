from sqlalchemy import Boolean, Column, ForeignKey, Integer, Float, String, Date
from sqlalchemy.orm import relationship

from .database import Base


class Instrument(Base):
    __tablename__ = "instrument"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True, unique=True)
    instrument_type = Column(String)
    manufacturer_name = Column(String)

    sequencing_runs = relationship("SequencingRun", back_populates="instrument")


class SequencingRun(Base):
    __tablename__ = "sequencing_run"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True, unique=True)
    instrument_id = Column(Integer, ForeignKey("instrument.id"))
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

    instrument = relationship("Instrument", back_populates="sequencing_runs")
    samples = relationship("Sample", back_populates="run")


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, index=True, unique=True)

    samples = relationship("Sample", back_populates="project")


class Sample(Base):
    __tablename__ = "sample"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True)
    run_id = Column(Integer, ForeignKey("sequencing_run.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    num_reads = Column(Integer)
    num_bases = Column(Integer)
    percent_bases_greater_or_equal_to_q30 = Column(Float)

    run = relationship("SequencingRun", back_populates="samples")
    project = relationship("Project", back_populates="samples")
    fastq_files = relationship("FastqFile", back_populates="sample")


class FastqFile(Base):
    __tablename__ = 'fastq_file'

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("sample.id"))
    read_type = Column(String)
    filename = Column(String)
    md5_checksum = Column(String)
    size_bytes = Column(Integer)
    total_reads = Column(Integer)
    total_bases = Column(Integer)
    mean_read_length = Column(Float)
    max_read_length = Column(Integer)
    min_read_length = Column(Integer)
    num_bases_greater_or_equal_to_q30 = Column(Integer)

    sample = relationship("Sample", back_populates="fastq_files")
