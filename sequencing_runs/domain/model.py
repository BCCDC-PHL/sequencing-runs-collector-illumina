import abc
import datetime
import json

from typing import Optional
from typing import Protocol


class JsonSerializable(Protocol):
    def to_json(self, indent):
        pass


class Entity(abc.ABC):
    pass


class IlluminaInstrument(Entity):
    """
    Represents a sequencing instrument. Instruments come in two types:
    "ILLUMINA" and "NANOPORE". There are multiple models for each of
    those types.
    """

    def __init__(
        self,
        instrument_id: str,
        type: str,
        model: str,
        status="UNKNOWN"
    ):
        self.instrument_id = instrument_id
        self.type = type
        self.model = model
        self.status = status

    def update_status(self, status: str):
        self.status = status

    def __repr__(self):
        return f"<IlluminaInstrument {self.instrument_id}>"

    def __eq__(self, other):
        if not isinstance(other, IlluminaInstrument):
            return False
        return other.instrument_id == self.instrument_id

    def __hash__(self):
        return hash(self.instrument_id)

    def to_dict(self):
        instrument_dict = {
            'instrument_id': self.instrument_id,
            'model': self.model,
            'type': self.type,
            'status': self.status,
            'timestamp_status_updated': self.timestamp_status_updated,
        }
        return instrument_dict

    def to_json(self, indent):
        instrument_dict = self.to_dict()
        if 'timestamp_status_updated' in instrument_dict:
            instrument_dict['timestamp_status_updated'] = str(instrument_dict['timestamp_status_updated'])
        json_entity = json.dumps(instrument_dict, indent=indent)

        return json_entity


class NanoporeInstrument(Entity):
    """
    """

    def __init__(
        self,
        instrument_id: str,
        type: str,
        model: str,
        status="UNKNOWN",
        **kwargs,
    ):
        self.instrument_id = instrument_id
        self.type = type
        self.model = model
        self.status = status

    def update_status(self, status: str):
        self.status = status

    def __repr__(self):
        return f"<NanoporeInstrument {self.instrument_id}>"

    def __eq__(self, other):
        if not isinstance(other, NanoporeInstrument):
            return False
        return other.instrument_id == self.instrument_id

    def __hash__(self):
        return hash(self.instrument_id)

    def to_dict(self):
        instrument_dict = {
            'instrument_id': self.instrument_id,
            'model': self.model,
            'type': self.type,
            'status': self.status,
            'timestamp_status_updated': self.timestamp_status_updated,
        }
        return instrument_dict

    def to_json(self, indent):
        json_entity = json.dumps(self.__dict__, indent=indent)

        return json_entity


class IlluminaSequencingRunDemultiplexing(Entity):
    """
    """

    def __init__(
            self,
            sequencing_run_id: str,
            demultiplexing_id: int,
    ):
        self.sequencing_run_id = sequencing_run_id
        self.demultiplexing_id = demultiplexing_id

    def __repr__(self):
        return f"<IlluminaSequencingRunDemultiplexing {self.sequencing_run_id}:{self.demultiplexing_id}>"


class IlluminaSequencingRun(Entity):
    """
    """

    def __init__(
            self,
            sequencing_run_id: str,
            instrument_id: str,
            flowcell_id: Optional[str]=None,
            run_date: Optional[datetime.date]=None,
            cluster_count: Optional[int]=None,
            cluster_count_passed_filter: Optional[int]=None,
            error_rate: Optional[float]=None,
            first_cycle_intensity: Optional[float]=None,
            percent_aligned: Optional[float]=None,
            q30_percent: Optional[float]=None,
            projected_yield_gigabases: Optional[float]=None,
            num_reads: Optional[int]=None,
            num_reads_passed_filter: Optional[int]=None,
            yield_gigabases: Optional[float]=None,
            demultiplexings: Optional[list[IlluminaSequencingRunDemultiplexing]]=None,
            **kwargs,
    ):
        percent_reads_passed_filter = 0.0
        if num_reads_passed_filter and num_reads and num_reads > 0:
            percent_reads_passed_filter = num_reads_passed_filter / num_reads * 100
        percent_clusters_passed_filter = 0.0
        if cluster_count and cluster_count_passed_filter and cluster_count > 0:
            percent_clusters_passed_filter = cluster_count_passed_filter / cluster_count * 100
        self.sequencing_run_id = sequencing_run_id
        self.instrument_id = instrument_id
        self.flowcell_id = flowcell_id
        if run_date is None:
            self.run_date = self._run_date_from_run_id(sequencing_run_id)
        else:
            self.run_date = run_date
        self.cluster_count = cluster_count
        self.cluster_count_passed_filter = cluster_count_passed_filter
        self.percent_clusters_passed_filter = percent_clusters_passed_filter
        self.error_rate = error_rate
        self.first_cycle_intensity = first_cycle_intensity
        self.percent_aligned = percent_aligned
        self.q30_percent = q30_percent
        self.projected_yield_gigabases = projected_yield_gigabases
        self.num_reads = num_reads
        self.num_reads_passed_filter = num_reads_passed_filter
        self.percent_reads_passed_filter = percent_reads_passed_filter
        self.yield_gigabases = yield_gigabases
        self.demultiplexings = demultiplexings

    def __repr__(self):
        return f"<IlluminaSequencingRun {self.sequencing_run_id}>"

    def __eq__(self, other):
        if not isinstance(other, IlluminaSequencingRun):
            return False
        return other.sequencing_run_id == self.sequencing_run_id

    def to_json(self, indent):
        json_entity = json.dumps(self.__dict__, indent=indent)

        return json_entity

    def _run_date_from_run_id(self, run_id):
        run_date = None
        run_id_date_component = run_id.split('_')[0]
        if len(run_id_date_component) == 6:
            six_digit_date = run_id.split('_')[0]
            two_digit_year = six_digit_date[0:2]
            four_digit_year = "20" + two_digit_year
            two_digit_month = six_digit_date[2:4]
            two_digit_day = six_digit_date[4:6]
            run_date = datetime.date(int(four_digit_year), int(two_digit_month), int(two_digit_day))

        return run_date




class IlluminaSequencedLibrary(Entity):
    """
    """
    def __init__(
            self,
            library_id: str,
            sequencing_run_id: str,
            demultiplexing_id: str,
            samplesheet_project_id: Optional[str]=None,
            num_reads: Optional[int]=None,
            num_bases: Optional[int]=None,
            q30_rate: Optional[float]=None,
    ):
        self.library_id = library_id
        self.sequencing_run_id = sequencing_run_id
        self.demultiplexing_id = demultiplexing_id
        self.samplesheet_project_id = samplesheet_project_id
        self.num_reads = num_reads
        self.num_bases = num_bases
        self.q30_rate = q30_rate


class NanoporeAcquisitionRun(Entity):
    """
    """
    def __init__(
            self,
            acquisition_run_id: str,
            sequencing_run_id: str,
            num_reads_total: Optional[int]=None,
            num_reads_passed_filter: Optional[int]=None,
            num_reads_skipped: Optional[int]=None,
            num_bases_total: Optional[int]=None,
            num_bases_passed_filter: Optional[int]=None,
            startup_state: Optional[str]=None,
            state: Optional[str]=None,
            finishing_state: Optional[str]=None,
            stop_reason: Optional[str]=None,
            purpose: Optional[str]=None,
            events_to_base_ratio: Optional[float]=None,
            sample_rate: Optional[int]=None,
            channel_count: Optional[int]=None,
            **kwargs,
    ):
        self.acquisition_run_id = acquisition_run_id
        self.sequencing_run_id = sequencing_run_id
        self.num_reads_total = num_reads_total
        self.num_reads_passed_filter = num_reads_passed_filter
        self.num_reads_skipped = num_reads_skipped
        self.num_bases_total = num_bases_total
        self.num_bases_passed_filter = num_bases_passed_filter
        self.startup_state = startup_state
        self.state = state
        self.finishing_state = finishing_state
        self.stop_reason = stop_reason
        self.purpose = purpose
        self.events_to_base_ratio = events_to_base_ratio
        self.sample_rate = sample_rate
        self.channel_count = channel_count


class NanoporeSequencingRun(Entity):
    """
    """
    def __init__(
            self,
            sequencing_run_id: str,
            instrument_id: str,
            flowcell_id: Optional[str]=None,
            flowcell_product_code: Optional[str]=None,
            run_date: Optional[datetime.date]=None,
            protocol_id: Optional[str]=None,
            protocol_run_id: Optional[str]=None,
            timestamp_protocol_run_started: Optional[datetime.datetime]=None,
            timestamp_protocol_run_ended: Optional[datetime.datetime]=None,
            num_reads_total: Optional[int]=None,
            num_reads_passed_filter: Optional[int]=None,
            yield_gigabases: Optional[float]=None,
            acquisition_runs: Optional[list[NanoporeAcquisitionRun]]=None,
            **kwargs,
    ):
        self.sequencing_run_id = sequencing_run_id
        self.instrument_id = instrument_id
        self.flowcell_id = flowcell_id
        self.flowcell_product_code = flowcell_product_code
        if run_date is None:
            self.run_date = self._run_date_from_run_id(sequencing_run_id)
        else:
            self.run_date = run_date
        self.protocol_id = protocol_id
        self.protocol_run_id = protocol_run_id
        self.timestamp_protocol_run_started = timestamp_protocol_run_started
        self.timestamp_protocol_run_ended = timestamp_protocol_run_ended
        self.num_reads_total = num_reads_total
        self.num_reads_passed_filter = num_reads_passed_filter
        self.yield_gigabases = yield_gigabases
        self.acquisition_runs = acquisition_runs

    def __repr__(self):
        return f"<NanoporeSequencingRun {self.sequencing_run_id}>"

    def __eq__(self, other):
        if not isinstance(other, NanoporeSequencingRun):
            return False
        return other.sequencing_run_id == self.sequencing_run_id

    def to_json(self, indent):
        json_entity = json.dumps(self.__dict__, indent=indent)

        return json_entity

    def _run_date_from_run_id(self, run_id):
        run_date = None
        run_id_date_component = run_id.split('_')[0]
        if len(run_id_date_component) == 8:
            six_digit_date = run_id.split('_')[0]
            four_digit_year = six_digit_date[0:4]
            two_digit_month = six_digit_date[4:6]
            two_digit_day = six_digit_date[6:8]
            run_date = datetime.date(int(four_digit_year), int(two_digit_month), int(two_digit_day))

        return run_date


        
