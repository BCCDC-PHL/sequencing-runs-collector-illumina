import json
import logging
import math
import os

from fastapi import Depends, FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from sqlalchemy.orm import Session

from . import crud, models, schemas, util
from .database import SessionLocal, engine
from .config import init_debug_logger

# For use in early development.
# TODO: Update logging config for production deployment.
init_debug_logger()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

allowed_origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

log = logging.getLogger("logger")

def get_db():
    """
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_model=schemas.LinksOnlyResponse)
async def root():
    """
    """
    links = {
        "self": "/",
        "instruments": "/instruments",
        "runs": "/runs",
    }
    response_body = {
        "links": links
    }

    return response_body


@app.get("/instruments", response_model=schemas.InstrumentCollectionResponse)
async def get_instruments(db: Session = Depends(get_db)):
    """
    """
    instruments = crud.get_instruments(db)
    data = []
    for instrument in instruments:
        data_dict = util.row2dict(instrument)
        data_dict['type'] = "instrument"
        data_dict['id'] = instrument.instrument_id
        data_dict['links'] = {
            'self': os.path.join('/instruments', instrument.instrument_id),
            'runs': os.path.join('/instruments', instrument.instrument_id, 'runs'),
        }
        data.append(data_dict)

    links = {
        "self": "/instruments"
    }

    response_body = {
        "data": data,
        "links": links,
    }

    return response_body


@app.get("/instruments/{instrument_id}", response_model=schemas.InstrumentSingleResponse)
async def get_instrument_by_id(instrument_id: str, db: Session = Depends(get_db)):
    """
    """
    instrument = crud.get_instrument_by_id(db, instrument_id)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found")

    
    data_dict = util.row2dict(instrument)
    data_dict['type'] = 'instrument'
    data_dict['id'] = instrument.instrument_id
    data_dict['links'] = {
        'self': os.path.join('/instruments', instrument_id),
        'runs': os.path.join('/instruments', instrument_id, 'runs'),
    }

    links = {
        "self": os.path.join('/instruments', instrument_id),
    }

    response_body = {
        'data': data_dict,
        'links': links,
    }

    return response_body


@app.get("/instruments/{instrument_id}/runs", response_model=schemas.SequencingRunCollectionResponse)
async def get_runs_by_instrument_id(instrument_id: str, db: Session = Depends(get_db)):
    """
    """
    instrument = crud.get_instrument_by_id(db, instrument_id)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found: " + instrument_id)

    runs = crud.get_sequencing_runs_by_instrument_id(db, instrument_id)
    data = []
    for run in runs:
        data_dict = util.row2dict(run)
        data_dict['type'] = 'sequencing_run'
        data_dict['id'] = run.run_id
        data_dict['links'] = {
            'self': os.path.join('/runs', run.run_id),
            'samples': os.path.join('/runs', run.run_id, 'samples'),
        }
        data.append(data_dict)

    links = {
        "self": "/instruments/" + instrument_id + "/runs"
    }

    response_body = {
        "data": data,
        "links": links,
    }

    return response_body


@app.get("/runs", response_model=list[schemas.SequencingRunResponse])
async def get_sequencing_runs(db: Session = Depends(get_db)):
    """
    """
    runs = crud.get_sequencing_runs(db)
    for run in runs:
        run.instrument_id = run.instrument.instrument_id

    return runs


@app.get("/runs/{run_id}", response_model=schemas.SequencingRunResponse)
async def get_sequencing_run_by_run_id(run_id: str, db: Session = Depends(get_db)):
    run = crud.get_sequencing_run_by_id(db, run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="Sequencing run not found: " + run_id)

    return run


@app.get("/runs/{run_id}/samples", response_model=schemas.SampleCollectionResponse)
async def get_samples_by_run_id(run_id: str, page: int = 1, db: Session = Depends(get_db)):
    """
    """
    page_size = 96
    if page == 1:
        min_index = 0
    else:
        min_index = (page - 1) * page_size
    max_index = min_index + page_size
    run = crud.get_sequencing_run_by_id(db, run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="Sequencing run not found: " + run_id)

    all_samples_on_run = crud.get_samples_by_run_id(db, run_id)
    num_samples_on_run = len(all_samples_on_run)
    log.info("Run ID: " + run_id + " Num samples: " + str(num_samples_on_run))
    page_samples = all_samples_on_run[min_index:max_index]
    first_page = 1
    last_page = math.ceil(num_samples_on_run / page_size)
    if (page + 1) > last_page:
        next_page = None
    else:
        next_page = page + 1
    if (page - 1) < first_page:
        prev_page = None
    else:
        prev_page = page - 1
    

    data = []
    for sample in page_samples:
        data_dict = util.row2dict(sample)
        data_dict['type'] = 'sample'
        data_dict['id'] = sample.sample_id
        if sample.project is not None:
            data_dict['project_id'] = sample.project.project_id
        data_dict['links'] = {
            'self': os.path.join('/runs', run_id, 'samples', sample.sample_id)
        }
        data_dict['fastq_files'] = []
        fastq_files = crud.get_fastq_files_by_run_id_by_sample_id(db, run_id, sample.sample_id)
        for fastq_file in fastq_files:
            fastq_file_dict = util.row2dict(fastq_file)
            fastq_file_links = {
                'self': "",
            }
            fastq_file_dict['type'] = 'fastq_file'
            fastq_file_dict['id'] = fastq_file_dict['md5_checksum']
            fastq_file_dict['links'] = fastq_file_links
            data_dict['fastq_files'].append(fastq_file_dict)
        logging.info(json.dumps(data_dict))
        data.append(data_dict)

    if next_page is None:
        next_link = None
    else:
        next_link = os.path.join('/runs', run_id, 'samples' + '?' + 'page=' + str(next_page))

    if prev_page is None:
        prev_link = None
    else:
        prev_link = os.path.join('/runs', run_id, 'samples' + '?' + 'page=' + str(prev_page))

    links = {
        'self': os.path.join('/runs', run_id, 'samples' + '?' + 'page=' + str(page)),
        'first': os.path.join('/runs', run_id, 'samples' + '?' + 'page=1'),
        'last': os.path.join('/runs', run_id, 'samples' + '?' + 'page=' + str(last_page)),
        'next': next_link,
        'prev': prev_link,
    }

    response_body = {
        'data': data,
        'links': links,
    }    

    return response_body


@app.get("/projects", response_model=list[schemas.ProjectResponse])
async def get_projects(db: Session = Depends(get_db)):
    """
    """
    projects = crud.get_projects(db)

    return projects


@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
async def get_project_by_id(project_id: str, db: Session = Depends(get_db)):
    """
    """
    project = crud.get_project_by_id(db, project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found: " + project_id)

    return project


@app.get("/projects/{project_id}/samples", response_model=list[schemas.SampleResponse])
async def get_samples_by_project_id(project_id: str, db: Session = Depends(get_db)):
    """
    """
    project = crud.get_project_by_id(db, project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found: " + project_id)

    samples = crud.get_samples_by_project_id(db, project_id)

    for sample in samples:
        sample.project_id = sample.project.project_id

    return samples


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Sequencing Runs Service",
        version="0.1.0-alpha-0",
        description="Data on BCCDC-PHL sequencing runs",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
