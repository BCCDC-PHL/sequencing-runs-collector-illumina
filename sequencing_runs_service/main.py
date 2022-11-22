import logging
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


@app.get("/instruments/{instrument_id}", response_model=schemas.InstrumentResponse)
async def get_instrument_by_id(instrument_id: str, db: Session = Depends(get_db)):
    """
    """
    instrument = crud.get_instrument_by_id(db, instrument_id)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found")

    return instrument


@app.get("/instruments/{instrument_id}/runs", response_model=list[schemas.SequencingRunResponse])
async def get_runs_by_instrument_id(instrument_id: str, db: Session = Depends(get_db)):
    """
    """
    instrument = crud.get_instrument_by_id(db, instrument_id)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found: " + instrument_id)

    runs = crud.get_sequencing_runs_by_instrument_id(db, instrument_id)
    for run in runs:
        run.instrument_id = run.instrument.instrument_id

    return runs


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


@app.get("/runs/{run_id}/samples", response_model=list[schemas.SampleResponse])
async def get_samples_by_run_id(run_id: str, db: Session = Depends(get_db)):
    """
    """
    run = crud.get_sequencing_run_by_id(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Sequencing run not found: " + run_id)

    samples = crud.get_samples_by_run_id(db, run_id)

    for sample in samples:
        if sample.project is not None:
            sample.project_id = sample.project.project_id

    return samples


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
