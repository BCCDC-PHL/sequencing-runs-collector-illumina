from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import event
from sqlalchemy.orm import registry, relationship

from sequencing_runs.domain import model

mapper_registry = registry()
metadata = mapper_registry.metadata

illumina_instruments = Table(
    "instrument_illumina",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instrument_id", String, unique=True),
    Column("type", String),
    Column("model", String),
    Column("status", String),
    Column("timestamp_status_updated", DateTime),
)

illumina_instruments_view = Table(
    "instrument_illumina_view",
    metadata,
    Column("instrument_id", String),
    Column("type", String),
    Column("model", String),
    Column("status", String),
    Column("timestamp_status_updated", DateTime),
)

nanopore_instruments = Table(
    "instrument_nanopore",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("instrument_id", String, unique=True),
    Column("type", String),
    Column("model", String),
    Column("status", String),
    Column("timestamp_status_updated", DateTime),
)

nanopore_instruments_view = Table(
    "instrument_nanopore_view",
    metadata,
    Column("instrument_id", String),
    Column("type", String),
    Column("model", String),
    Column("status", String),
    Column("timestamp_status_updated", DateTime),
)

illumina_sequencing_runs = Table(
    "sequencing_run_illumina",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sequencing_run_id", String, unique=True),
    Column("instrument_id", ForeignKey("instrument_illumina.id")),
    Column("flowcell_id", String),
    Column("run_date", Date),
    Column("cluster_count", Integer),
    Column("cluster_count_passed_filter", Integer),
    Column("error_rate", Float),
    Column("first_cycle_intensity", Float),
    Column("percent_aligned", Float),
    Column("q30_percent", Float),
    Column("projected_yield_gigabases", Float),
    Column("num_reads", Integer),
    Column("num_reads_passed_filter", Integer),
    Column("percent_reads_passed_filter", Float),
    Column("yield_gigabases", Float),
)

illumina_sequencing_run_demultiplexings = Table(
    "sequencing_run_illumina_demultiplexing",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sequencing_run_id", ForeignKey("sequencing_run_illumina.id")),
    Column("demultiplexing_num", Integer),
)

nanopore_sequencing_runs = Table(
    "sequencing_run_nanopore",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sequencing_run_id", String, unique=True),
    Column("instrument_id", ForeignKey("instrument_illumina.id")),
    Column("flowcell_id", String),
    Column("flowcell_product_code", String),
    Column("run_date", Date),
    Column("protocol_id", String),
    Column("protocol_run_id", String),
    Column("acquisition_run_id", String),
    Column("timestamp_acquisition_started", DateTime),
    Column("timestamp_acquisition_stopped", DateTime),
    Column("timestamp_processing_stopped",DateTime),
    Column("num_reads_total", Integer),
    Column("num_reads_passed_filter", Integer),
    Column("yield_gigabases", Float),
)


def start_mappers():
    """
    Start the mappers that map between our domain model classes and the database tables.
    """
    illumina_instruments_mapper = mapper_registry.map_imperatively(
        model.IlluminaInstrument, illumina_instruments,
    )

    nanopore_instruments_mapper = mapper_registry.map_imperatively(
        model.NanoporeInstrument, nanopore_instruments,
    )

    illumina_sequencing_runs_mapper = mapper_registry.map_imperatively(
        model.IlluminaSequencingRun, illumina_sequencing_runs,
    )

    illumina_sequencing_run_demultiplexings_mapper = mapper_registry.map_imperatively(
        model.IlluminaSequencingRunDemultiplexing, illumina_sequencing_run_demultiplexings,
    )

    nanopore_sequencing_runs_mapper = mapper_registry.map_imperatively(
        model.NanoporeSequencingRun, nanopore_sequencing_runs,
    )
    
