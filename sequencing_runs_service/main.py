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
        raise HTTPException(status_code=404, detail="Instrument not found")

    runs = crud.get_sequencing_runs_by_instrument_id(db, instrument_id)
    for run in runs:
        run.instrument_id = run.instrument.instrument_id

    return runs
