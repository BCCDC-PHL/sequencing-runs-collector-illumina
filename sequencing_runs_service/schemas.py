import datetime

from typing import List, Union

from pydantic import BaseModel


class LinksOnlyResponse(BaseModel):
    links: dict[str, str]


###### Instruments
class InstrumentBase(BaseModel):
    instrument_type: str
    manufacturer_name: str

    class Config:
        orm_mode = True


class Instrument(InstrumentBase):
    id: int


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentResponse(InstrumentBase):
    id: str
    links: dict[str, str]


class InstrumentCollectionResponse(BaseModel):
    links: dict[str, str]
    data: list[InstrumentResponse]


###### Sequencing Runs
class SequencingRunBase(BaseModel):
    run_id: str
    run_date: datetime.date

    class Config:
        orm_mode = True


class SequencingRun(SequencingRunBase):
    id: int


class SequencingRunCreate(SequencingRunBase):
    instrument: Instrument


class SequencingRunResponse(SequencingRunBase):
    instrument_id: str


###### Projects
class ProjectBase(BaseModel):
    project_id: str

    class Config:
        orm_mode = True


class Project(ProjectBase):
    id: int


class ProjectCreate(ProjectBase):
    pass

    
class ProjectResponse(ProjectBase):
    pass


###### Samples
class SampleBase(BaseModel):
    sample_id: str
    project_id: str | None

    class Config:
        orm_mode = True


class Sample(SampleBase):
    id: int


class SampleCreate(SampleBase):
    pass


class SampleResponse(SampleBase):
    pass
