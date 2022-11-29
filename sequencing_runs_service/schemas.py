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
    instrument_id: str


class InstrumentResponse(InstrumentBase):
    id: str
    type: str
    links: dict[str, str]


class InstrumentSingleResponse(BaseModel):
    links: dict[str, str]
    data: InstrumentResponse


class InstrumentCollectionResponse(BaseModel):
    links: dict[str, str]
    data: list[InstrumentResponse]


###### Sequencing Runs
class SequencingRunBase(BaseModel):
    run_date: datetime.date
    cluster_count: int|None
    cluster_count_passed_filter: int|None
    error_rate: float|None
    percent_bases_greater_or_equal_to_q30: float|None

    class Config:
        orm_mode = True


class SequencingRun(SequencingRunBase):
    id: int


class SequencingRunCreate(SequencingRunBase):
    instrument: Instrument


class SequencingRunResponse(SequencingRunBase):
    id: str
    type: str
    links: dict[str, str]


class SequencingRunSingleResponse(BaseModel):
    links: dict[str, str]
    data: SequencingRunResponse


class SequencingRunCollectionResponse(BaseModel):
    links: dict[str, str]
    data: list[SequencingRunResponse]


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
