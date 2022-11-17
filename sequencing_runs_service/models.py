from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
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

    run = relationship("SequencingRun", back_populates="samples")
    project = relationship("Project", back_populates="samples")


