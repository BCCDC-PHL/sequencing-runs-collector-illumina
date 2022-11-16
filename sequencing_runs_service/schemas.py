import datetime

from typing import List, Union

from pydantic import BaseModel


###### Instruments
class InstrumentBase(BaseModel):
    instrument_id: str
    instrument_type: str
    manufacturer_name: str

    class Config:
        orm_mode = True


class Instrument(InstrumentBase):
    id: int


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentResponse(InstrumentBase):
    pass
    

###### Sequencing Runs
class SequencingRunBase(BaseModel):
    run_id: str
    run_date: datetime.date

    class Config:
        orm_mode = True


class SequencingRun(SequencingRunBase):
    id: int


class SequencingRunCreate(SequencingRunBase):
    pass


class SequencingRunResponse(SequencingRunBase):
    instrument_id: str
    pass
