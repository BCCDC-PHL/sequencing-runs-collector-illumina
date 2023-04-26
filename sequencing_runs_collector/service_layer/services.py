
import sequencing_runs.domain.model as model
import sequencing_runs.views as views

from sequencing_runs.adapters.repository import IlluminaInstrumentRepository
from sequencing_runs.adapters.repository import NanoporeInstrumentRepository

from sequencing_runs.service_layer.unit_of_work import UnitOfWork


def get_illumina_instruments(uow: UnitOfWork) -> list[model.IlluminaInstrument]:
    """
    """
    instruments = []
    with uow:
        for instrument in uow.repo.list():
            instruments.append(instrument) 
    
    return instruments


def update_instrument_status(instrument_id: str, status: str, uow: UnitOfWork):
    """
    """
    with uow:
        instrument = uow.repo.get(instrument_id)
        if instrument is not None:
            instrument.status = status
        uow.commit()

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
