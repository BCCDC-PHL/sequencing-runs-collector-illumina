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
    run_id: str
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


###### Fastq Files
class FastqFileBase(BaseModel):
    read_type: str
    filename: str
    md5_checksum: str|None
    size_bytes: int|None
    total_reads: int|None
    total_bases: int|None
    mean_read_length: float|None
    max_read_length: int|None
    min_read_length: int|None
    num_bases_greater_or_equal_to_q30: int|None

    class Config:
        orm_mode = True


class FastqFile(FastqFileBase):
    id: int


class FastqFileCreate(FastqFileBase):
    pass


class FastqFileResponse(FastqFileBase):
    id: str
    type: str
    links: dict[str, str]

    
class FastqFileSingleResponse(BaseModel):
    links: dict[str, str]
    data: FastqFileResponse


class FastqFileCollectionResponse(BaseModel):
    links: dict[str, str]
    data: list[FastqFileResponse]


###### Samples
class SampleBase(BaseModel):
    project_id: str | None

    class Config:
        orm_mode = True


class Sample(SampleBase):
    id: int


class SampleCreate(SampleBase):
    sample_id: str


class SampleResponse(SampleBase):
    id: str
    type: str
    fastq_files: list[FastqFileResponse]
    links: dict[str, str]


class SampleCollectionResponse(BaseModel):
    links: dict[str, str]
    data: list[SampleResponse]
