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


def nanopore_instruments(uow: unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork):
    results = []
    with uow:
        for result in uow.repo.list():
            results.append(result)
        uow.session.expunge_all()
    return results

