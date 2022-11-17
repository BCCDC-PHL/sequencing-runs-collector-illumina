from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    """
    """
    root = {
        "links": [
            {
                "href": "/instruments",
                "rel": "instruments",
            },
            {
                "href": "/runs",
                "rel": "runs",
            },
        ]
    }

    return root

@app.get("/instruments", response_model=list[schemas.InstrumentResponse])
async def get_instruments(db: Session = Depends(get_db)):
    """
    """
    instruments = crud.get_instruments(db)

    return instruments


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
        sample.project_id = sample.project.project_id

    return samples
