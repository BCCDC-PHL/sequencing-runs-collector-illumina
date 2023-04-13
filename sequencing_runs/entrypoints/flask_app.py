from datetime import datetime, date
from flask import Flask, request, jsonify
from flask.json.provider import DefaultJSONProvider

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sequencing_runs import views
from sequencing_runs.domain import model
from sequencing_runs.adapters import orm
from sequencing_runs.adapters.repository import SqlAlchemyIlluminaInstrumentRepository
from sequencing_runs.service_layer import services, unit_of_work


class UpdatedJSONProvider(DefaultJSONProvider):
    """
    """
    def default(self, o):
        if isinstance(o, date) or isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


app = Flask(__name__)
app.json = UpdatedJSONProvider(app)

orm.start_mappers()


@app.route("/instruments", methods=["GET"])
def get_instruments():
    illumina_instruments = views.illumina_instruments(unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork())
    nanopore_instruments = views.nanopore_instruments(unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork())
    response = []
    for instrument in illumina_instruments:
        instrument_dict = instrument.to_dict()
        response.append(instrument.to_dict())

    for instrument in nanopore_instruments:
        instrument_dict = instrument.to_dict()
        response.append(instrument.to_dict())

    return jsonify(response)


@app.route("/sequencing-runs", methods=["GET"])
def add_sequencing_runs():
    response = []

    illumina_sequencing_runs = views.illumina_sequencing_runs(unit_of_work.SqlAlchemyIlluminaSequencingRunUnitOfWork())
    nanopore_sequencing_runs = views.nanopore_sequencing_runs(unit_of_work.SqlAlchemyNanoporeSequencingRunUnitOfWork())
    
    for sequencing_run in illumina_sequencing_runs:
        response.append(sequencing_run.to_dict())

    for sequencing_run in nanopore_sequencing_runs:
        response.append(sequencing_run.to_dict())

    return jsonify(response)
    
