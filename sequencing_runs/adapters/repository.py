import abc
from typing import Optional
from typing import Protocol

from sequencing_runs.domain import model

class Repository(Protocol):
    def add(self, instrument: model.Entity):
        """
        """

    def get(self, id: str) -> Optional[model.Entity]:
        """
        """

    def list(self) -> list[model.Entity]:
        """
        """


class IlluminaInstrumentRepository(Repository):
    """
    """
    def add(self, instrument: model.IlluminaInstrument):
        raise NotImplementedError


    def get(self, id: str) -> Optional[model.IlluminaInstrument]:
        raise NotImplementedError

    def list(self) -> list[model.IlluminaInstrument]:
        raise NotImplementedError


class NanoporeInstrumentRepository(Repository):
    """
    """
    def add(self, instrument: model.NanoporeInstrument):
        raise NotImplementedError

    def get(self, id: str) -> Optional[model.NanoporeInstrument]:
        raise NotImplementedError

    def list(self) -> list[model.NanoporeInstrument]:
        raise NotImplementedError


class SqlAlchemyRepository(Repository):
    """
    """
    def __init__(self, session):
        self.session = session

    def add(self, entity: model.Entity):
        raise NotImplementedError

    def get(self, id: str) -> Optional[model.Entity]:
        raise NotImplementedError

    def list(self):
        raise NotImplementedError


class SqlAlchemyIlluminaInstrumentRepository(Repository):
    """
    """
    def __init__(self, session):
        self.session = session


    def add(self, instrument: model.IlluminaInstrument):
        """
        """
        existing_instrument = self.get(instrument.instrument_id)
        if existing_instrument is None:
            self.session.add(instrument)


    def get(self, instrument_id: str) -> Optional[model.IlluminaInstrument]:
        """
        """
        instrument = self.session.query(model.IlluminaInstrument).filter_by(
            instrument_id=instrument_id
        ).one_or_none()

        return instrument


    def list(self) -> list[model.IlluminaInstrument]:
        """
        """
        instruments = self.session.query(model.IlluminaInstrument).all()

        return instruments


class SqlAlchemyNanoporeInstrumentRepository(Repository):
    """
    """
    def __init__(self, session):
        self.session = session


    def add(self, instrument: model.NanoporeInstrument):
        """
        """
        existing_instrument = self.get(instrument.instrument_id)
        if existing_instrument is None:
            self.session.add(instrument)


    def get(self, instrument_id: str) -> Optional[model.NanoporeInstrument]:
        """
        """
        instrument = self.session.query(model.NanoporeInstrument).filter_by(
            instrument_id=instrument_id
        ).one_or_none()

        return instrument


    def list(self) -> list[model.NanoporeInstrument]:
        """
        """
        instruments = self.session.query(model.NanoporeInstrument).all()

        return instruments


class SqlAlchemyIlluminaSequencingRunRepository(Repository):
    """
    """
    def __init__(self, session):
        self.session = session


    def add(self, sequencing_run: model.IlluminaSequencingRun):
        """
        """
        existing_sequencing_run = self.get(sequencing_run.sequencing_run_id)
        if existing_sequencing_run is None:
            self.session.add(sequencing_run)


    def get(self, sequencing_run_id: str) -> Optional[model.IlluminaSequencingRun]:
        """
        """
        sequencing_run = self.session.query(model.IlluminaSequencingRun).filter_by(
            sequencing_run_id=sequencing_run_id
        ).one_or_none()

        return sequencing_run


    def list(self) -> list[model.IlluminaSequencingRun]:
        """
        """
        sequencing_runs = self.session.query(model.IlluminaSequencingRun).all()

        return sequencing_runs


class SqlAlchemyNanoporeSequencingRunRepository(Repository):
    """
    """
    def __init__(self, session):
        self.session = session


    def add(self, sequencing_run: model.NanoporeSequencingRun):
        """
        """
        existing_sequencing_run = self.get(sequencing_run.sequencing_run_id)
        if existing_sequencing_run is None:
            self.session.add(sequencing_run)


    def get(self, sequencing_run_id: str) -> Optional[model.NanoporeSequencingRun]:
        """
        """
        sequencing_run = self.session.query(model.NanoporeSequencingRun).filter_by(
            sequencing_run_id=sequencing_run_id
        ).one_or_none()

        return sequencing_run


    def list(self) -> list[model.NanoporeSequencingRun]:
        """
        """
        sequencing_runs = self.session.query(model.NanoporeSequencingRun).all()

        return sequencing_runs
