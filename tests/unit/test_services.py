import pytest
from sequencing_runs.adapters.repository import Repository
from sequencing_runs.domain import model
from sequencing_runs.service_layer.unit_of_work import UnitOfWork
from sequencing_runs.service_layer import services

class TestInstrumentRepository(Repository):
    """
    """
    __test__ = False

    def __init__(self, instruments):
        self._instruments = {instrument.instrument_id: instrument for instrument in instruments}

    def add(self, instrument):
        self._instruments[instrument.instrument_id] = instrument

    def get(self, instrument_id):
        return self._instruments[instrument_id]

    def list(self):
        return list(self._instruments.values())


class TestUnitOfWork(UnitOfWork):
    """
    """
    __test__ = False
    
    def __init__(self):
        self.repo = TestInstrumentRepository({})
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_illumina_instrument():
    uow = TestUnitOfWork()
    instrument_info = {
        'instrument_id': "M00123",
        'type': "ILLUMINA",
        'model': "MISEQ",
    }
    instrument = model.IlluminaInstrument(**instrument_info)
    services.add_illumina_instrument(instrument, uow)
    assert uow.repo.get(instrument.instrument_id) is not None
    assert uow.committed


def test_add_nanopore_instrument():
    uow = TestUnitOfWork()
    instrument_info = {
        'instrument_id': "GXB4567",
        'type': "NANOPORE",
        'model': "GRIDION",
    }
    instrument = model.NanoporeInstrument(**instrument_info)
    services.add_nanopore_instrument(instrument, uow)
    assert uow.repo.get(instrument.instrument_id) is not None
    assert uow.committed


