import datetime
import logging
import os
import unittest

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

import alembic
import alembic.config

import sequencing_runs_service.models as models
import sequencing_runs_service.schemas as schemas
import sequencing_runs_service.crud as crud

class TestCrudInstrument(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                            datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)

        connection_uri = "sqlite:///:memory:"

        project_root_path = os.path.join(os.path.dirname(__file__), '..')
        alembic_dir_path = os.path.join(project_root_path, 'alembic')
        alembic_config_file_path = os.path.join(project_root_path, "alembic.ini")
        alembic_cfg = alembic.config.Config(file_=alembic_config_file_path)
        alembic_cfg.set_main_option('script_location', alembic_dir_path)
        alembic_cfg.set_main_option('sqlalchemy.url', connection_uri)
        alembic.command.upgrade(alembic_cfg, 'head')
        
        self.engine = create_engine(connection_uri)
        self.session = Session(self.engine)
        models.Base.metadata.create_all(self.engine)


    def tearDown(self):
        models.Base.metadata.drop_all(self.engine)


    def test_create_instrument(self):

        instrument = schemas.InstrumentCreate(
            instrument_id = "M00123",
            instrument_type = "miseq",
            manufacturer_name = "illumina",
        )

        created_instrument = crud.create_instrument(self.session, instrument)

        self.assertIsNotNone(created_instrument)
        self.assertEqual(created_instrument.id, 1)

