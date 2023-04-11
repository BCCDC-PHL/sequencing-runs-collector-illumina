import pytest
from sequencing_runs.adapters.repository import Repository
from sequencing_runs.service_layer.unit_of_work import UnitOfWork
from sequencing_runs.service_layer import services

class TestDictRepository(Repository):
    """
    """
    __test__ = False

    def __init__(self, entities):
        self._entities = {entity.id: entity for entity in entities}

    def add(self, entity):
        self._entities[entity.id] = entity

    def get(self, id):
        return self._entities[id]

    def list(self):
        return list(self._entities.values())


class TestUnitOfWork(UnitOfWork):
    """
    """
    __test__ = False
    
    def __init__(self):
        self.repo = TestDictRepository({})
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_illumina_instrument():
    uow = TestUnitOfWork()
    instrument_id = "M00123"
    services.add_illumina_instrument(instrument_id, "ILLUMINA", "MISEQ", uow)
    assert uow.repo.get(instrument_id) is not None
    assert uow.committed


def test_add_nanopore_instrument():
    uow = TestUnitOfWork()
    instrument_id = "GXB4567"
    services.add_nanopore_instrument(instrument_id, "NANOPORE", "GRIDION", uow)
    assert uow.repo.get(instrument_id) is not None
    assert uow.committed


