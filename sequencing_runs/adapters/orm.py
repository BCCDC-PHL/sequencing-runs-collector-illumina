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
    Column("instrument_id", String, unique=True),
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
    Column("instrument_id", String, unique=True),
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
    Column("demultiplexing_id", Integer),
)

illumina_sequenced_libraries = Table(
    "sequenced_library_illumina",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sequencing_run_id", ForeignKey("sequencing_run_illumina.id")),
    Column("demultiplexing_id", ForeignKey("sequencing_run_illumina_demultiplexing.id")),
    Column("samplesheet_project_id", String),
    Column("num_reads", Integer),
    Column("num_bases", Integer),
    Column("q30_rate", Float),
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
    Column("timestamp_protocol_run_started", DateTime),
    Column("timestamp_protocol_run_ended", DateTime),
    Column("num_reads_total", Integer),
    Column("num_reads_passed_filter", Integer),
    Column("yield_gigabases", Float),
)

nanopore_acquisition_runs = Table(
    "acquisition_run_nanopore",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("acquisition_run_id", String, unique=True),
    Column("sequencing_run_id", ForeignKey("sequencing_run_nanopore.id")),
    Column("num_reads_total", Integer),
    Column("num_reads_passed_filter", Integer),
    Column("num_bases_passed_filter", Integer),
    Column("startup_state", String),
    Column("state", String),
    Column("finishing_state", String),
    Column("stop_reason", String),
    Column("purpose", String),
    Column("events_to_base_ratio", Float),
    Column("sample_rate", Integer),
    Column("channel_count", Integer),
)


def start_mappers():
    """
    Start the mappers that map between our domain model classes and the database tables.
    """
    illumina_instruments_mapper = mapper_registry.map_imperatively(
        model.IlluminaInstrument, illumina_instruments,
    )    

    illumina_sequencing_runs_mapper = mapper_registry.map_imperatively(
        model.IlluminaSequencingRun, illumina_sequencing_runs,
        properties={
            "demultiplexings": relationship(model.IlluminaSequencingRunDemultiplexing, backref="sequencing_run"),
        }
    )

    illumina_sequencing_run_demultiplexings_mapper = mapper_registry.map_imperatively(
        model.IlluminaSequencingRunDemultiplexing, illumina_sequencing_run_demultiplexings,
    )

    illumina_sequenced_libraries_mapper = mapper_registry.map_imperatively(
        model.IlluminaSequencedLibrary, illumina_sequenced_libraries,
    )

    nanopore_instruments_mapper = mapper_registry.map_imperatively(
        model.NanoporeInstrument, nanopore_instruments,
    )

    nanopore_sequencing_runs_mapper = mapper_registry.map_imperatively(
        model.NanoporeSequencingRun, nanopore_sequencing_runs,
        properties={
            "acquisition_runs": relationship(model.NanoporeAcquisitionRun, backref="sequencing_run"),
        }
    )

    nanopore_acquisition_runs_mapper = mapper_registry.map_imperatively(
        model.NanoporeAcquisitionRun, nanopore_acquisition_runs,
    )
    
