from marshmallow_jsonapi.flask import Schema,Relationship
from marshmallow_jsonapi import fields

class InstrumentSchema(Schema):
    class Meta:
        type_ = "instrument"
        self_url = "/instrument/{id}"
        self_url_kwargs = {"id": "<id>"}
        self_url_many = "/instruments/"

    id = fields.Str(dump_only=True)
    type = fields.Str()
    model = fields.Str()
    status = fields.Str()

    
