import json
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

def to_jsonapi(d: dict, id_key: str, type_str: str, skip_keys: list[str]=[]):
    """
    Simple function to convert standard dict to JSON:API formatting.
    """
    d_jsonapi = {
        'id': d.get(id_key, None),
        'type': type_str,
        'attributes': {},
    }
    for k, v in d.items():
        if k != id_key and k not in skip_keys:
            d_jsonapi['attributes'][k] = v

    return d_jsonapi
        

@app.route("/instruments", methods=["GET"], strict_slashes=False)
def handle_instruments():
    """
    """
    if request.method == 'GET':
        illumina_instruments = views.illumina_instruments(unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork())
        nanopore_instruments = views.nanopore_instruments(unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork())
        response = {'data': []}
        for instrument in illumina_instruments:
            instrument_dict = instrument.to_dict()
            instrument_dict_jsonapi = to_jsonapi(instrument_dict, 'instrument_id', 'instrument')
            response['data'].append(instrument_dict_jsonapi)

        for instrument in nanopore_instruments:
            instrument_dict = instrument.to_dict()
            instrument_dict_jsonapi = to_jsonapi(instrument_dict, 'instrument_id', 'instrument')
            response['data'].append(instrument_dict_jsonapi)

        return jsonify(response)


@app.route("/instruments/<instrument_id>", methods=["GET", "PATCH"], strict_slashes=False)
def handle_instrument_by_id(instrument_id):
    """
    """
    instrument_id = request.view_args['instrument_id']
    if request.method == "GET":
        illumina_instrument = views.illumina_instrument_by_id(instrument_id, unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork())
        nanopore_instrument = views.nanopore_instrument_by_id(instrument_id, unit_of_work.SqlAlchemyNanoporeInstrumentUnitOfWork())

        response = {'data': None}
        if illumina_instrument is not None:
            instrument_dict = illumina_instrument.to_dict()
            instrument_dict_jsonapi = to_jsonapi(instrument_dict, 'instrument_id', 'instrument')
            response['data'] = instrument_dict_jsonapi

        if nanopore_instrument is not None:
            instrument_dict = nanopore_instrument.to_dict()
            instrument_dict_jsonapi = to_jsonapi(instrument_dict, 'instrument_id', 'instrument')
            response['data'] = instrument_dict_jsonapi

        return jsonify(response)

    elif request.method == "PATCH":
        update_dict = request.get_json()['data']
        print(json.dumps(update_dict))
        if 'attributes' in update_dict:
            status = update_dict['attributes'].get('status')
            services.update_instrument_status(instrument_id, status, unit_of_work.SqlAlchemyIlluminaInstrumentUnitOfWork())
            return "Success\n", 200
        else:
            return "Update failed\n", 500




@app.route("/sequencing-runs", methods=["GET"], strict_slashes=False)
def handle_sequencing_runs():
    response = {'data': []}

    illumina_sequencing_runs = views.illumina_sequencing_runs(unit_of_work.SqlAlchemyIlluminaSequencingRunUnitOfWork())
    nanopore_sequencing_runs = views.nanopore_sequencing_runs(unit_of_work.SqlAlchemyNanoporeSequencingRunUnitOfWork())
    
    for sequencing_run in illumina_sequencing_runs:
        response['data'].append(sequencing_run.to_dict())

    for sequencing_run in nanopore_sequencing_runs:
        response['data'].append(sequencing_run.to_dict())

    return jsonify(response)
    
