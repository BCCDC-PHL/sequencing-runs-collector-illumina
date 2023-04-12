from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sequencing_runs import views
from sequencing_runs.domain import model
from sequencing_runs.adapters import orm
from sequencing_runs.adapters.repository import SqlAlchemyIlluminaInstrumentRepository
from sequencing_runs.service_layer import services, unit_of_work

app = Flask(__name__)


orm.start_mappers()


@app.route("/instruments", methods=["GET"])
def get_instruments():
    illumina_instruments = views.illumina_instruments(unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork())
    nanopore_instruments = views.illumina_instruments(unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork())
    app.logger.debug('Called: views.illumina_instruments()')
    response = []
    for instrument in illumina_instruments:
        instrument_dict = instrument.to_dict()
        response.append(instrument.to_dict())

    for instrument in nanopore_instruments:
        instrument_dict = instrument.to_dict()
        response.append(instrument.to_dict())

    return jsonify(response)


@app.route("/instruments", methods=["POST"])
def add_instrument():
    pass
    
