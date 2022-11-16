from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from .database import Base


class Instrument(Base):
    __tablename__ = "instrument"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, index=True)
    instrument_type = Column(String)
    manufacturer_name = Column(String)

    sequencing_runs = relationship("SequencingRun", back_populates="instrument")


class SequencingRun(Base):
    __tablename__ = "sequencing_run"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True)
    instrument_id = Column(Integer, ForeignKey("instrument.id"))
    run_date = Column(Date)

    instrument = relationship("Instrument", back_populates="sequencing_runs")


