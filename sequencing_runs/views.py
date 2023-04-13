from sqlalchemy import select

from sequencing_runs.domain import model
from sequencing_runs.service_layer import unit_of_work


def illumina_instruments(uow: unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork):
    results = []
    with uow:
        for result in uow.repo.list():
            results.append(result)
        uow.session.expunge_all()
    return results

def illumina_instrument_by_id(instrument_id: str, uow: unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork):
    result = None
    with uow:
        result = uow.repo.get(instrument_id)
        uow.session.expunge_all()
    return result


def nanopore_instruments(uow: unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork):
    results = []
    with uow:
        for result in uow.repo.list():
            results.append(result)
        uow.session.expunge_all()
    return results

def nanopore_instrument_by_id(instrument_id: str, uow: unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork):
    result = None
    with uow:
      result = uow.repo.get(instrument_id)
      uow.session.expunge_all()
    return result


def illumina_sequencing_runs(uow: unit_of_work.SqlAlchemyIlluminaSequencingRunUnitOfWork):
    results = []
    with uow:
        for result in uow.repo.list():
            print(result)
            results.append(result)
        uow.session.expunge_all()
    return results

def nanopore_sequencing_runs(uow: unit_of_work.SqlAlchemyNanoporeSequencingRunUnitOfWork):
    results = []
    with uow:
        for result in uow.repo.list():
            results.append(result)
        uow.session.expunge_all()
    return results

