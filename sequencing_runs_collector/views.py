from typing import Optional

from sequencing_runs.domain import model
from sequencing_runs.service_layer import unit_of_work


def illumina_instruments(uow: unit_of_work.SqlAlchemyUnitOfWork):
    """
    """
    results = []
    with uow:
        results = uow.session.query(model.IlluminaInstrument).all()
        uow.session.expunge_all()

    return results


def illumina_instrument_by_id(instrument_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork) -> Optional[model.IlluminaInstrument]:
    """
    """
    result = None
    with uow:
        result = uow.session.query(model.IlluminaInstrument).filter_by(
            instrument_id=instrument_id
        ).one_or_none()
        uow.session.expunge_all()

    return result


def nanopore_instruments(uow: unit_of_work.SqlAlchemyUnitOfWork) -> list[model.NanoporeInstrument]:
    """
    """
    results = []
    with uow:
        results = uow.session.query(model.NanoporeInstrument).all()
        uow.session.expunge_all()

    return results


def nanopore_instrument_by_id(instrument_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork) -> Optional[model.NanoporeInstrument]:
    """
    """
    result = None
    with uow:
      result = uow.session.query(model.NanoporeInstrument).filter_by(
          instrument_id=instrument_id
      ).one_or_none()
      uow.session.expunge_all()

    return result


def illumina_sequencing_runs(uow: unit_of_work.SqlAlchemyUnitOfWork) -> list[model.IlluminaSequencingRun]:
    """
    """
    results = []
    with uow:
        results = uow.session.query(model.IlluminaSequencingRun).all()
        uow.session.expunge_all()

    return results


def nanopore_sequencing_runs(uow: unit_of_work.SqlAlchemyUnitOfWork) -> list[model.NanoporeSequencingRun]:
    """
    """
    results = []
    with uow:
        results = uow.session.query(model.NanoporeSequencingRun).all()
        uow.session.expunge_all()

    return results

