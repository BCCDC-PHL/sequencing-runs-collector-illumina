
import sequencing_runs.domain.model as model

from sequencing_runs.adapters.repository import IlluminaInstrumentRepository
from sequencing_runs.adapters.repository import NanoporeInstrumentRepository

from sequencing_runs.service_layer.unit_of_work import UnitOfWork


def get_illumina_instruments(uow: UnitOfWork) -> list[model.IlluminaInstrument]:
    """
    """
    instruments = uow.repo.list()
    
    return instruments


def get_illumina_instrument_by_id(repo: IlluminaInstrumentRepository, instrument_id: str):
    """
    """
    instrument = repo.get(instrument_id)

    return instrument


def add_illumina_instrument(instrument: model.IlluminaInstrument, uow: UnitOfWork):
    """
    """
    with uow:
        uow.repo.add(instrument)
        uow.commit()


def add_nanopore_instrument(instrument: model.NanoporeInstrument, uow: UnitOfWork):
    """
    """
    with uow:
        uow.repo.add(instrument)
        uow.commit()


def add_illumina_sequencing_run(sequencing_run: model.IlluminaSequencingRun, uow: UnitOfWork):
    """
    """
    with uow:
        uow.repo.add(sequencing_run)
        uow.commit()


def add_nanopore_sequencing_run(sequencing_run: model.NanoporeSequencingRun, uow: UnitOfWork):
    """
    """
    with uow:
        uow.repo.add(sequencing_run)
        uow.commit()
