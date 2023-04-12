import datetime

from dataclasses import dataclass


class Event:
    pass

@dataclass
class InstrumentCreated(Event):
    timestamp: datetime.datetime
    instrument_id: str

@dataclass
class InstrumentStatusUpdated(Event):
    timestamp: datetime.datetime
    instrument_id: str
