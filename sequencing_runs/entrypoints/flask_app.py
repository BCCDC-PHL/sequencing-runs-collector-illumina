from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sequencing_runs import views
from sequencing_runs.domain import model
from sequencing_runs.adapters import orm
from sequencing_runs.adapters.repository import SqlAlchemyInstrumentRepository
from sequencing_runs.service_layer import services, unit_of_work

app = Flask(__name__)


orm.start_mappers()


@app.route("/instruments", methods=["GET"])
def get_instruments():
    instruments = services.get_instruments(unit_of_work.SqlAlchemyUnitOfWork())
    app.logger.debug('Called: services.get_instruments()')
    response = []
    for instrument in instruments:
        response.append(instrument.__dict__)

    return response


@app.route("/instruments", methods=["POST"])
def add_instrument():
    pass
    
