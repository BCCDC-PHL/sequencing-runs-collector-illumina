import re
from dataclasses import dataclass

class ValidationException(Exception):
  """A base class for all business rule validation exceptions"""

class ValueObject:
  """A base class for all value objects"""


  
  
@dataclass(frozen=True)
class SequencingRunID(ValueObject):
    value: str
    
    def __post_init__(self):
        valid_run_id_regexes = {
            'MiSeq': "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}",
            'NextSeq': "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}",
            'GridION': "\d{8}_\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}",
            'PromethiION': "\d{8}_\d{4}_P2S_[0-9]{5}-\d{1}_[A-Z0-9]+_[a-z0-9]{8}",
        }
        for sequencer_type, regex in valid_run_id_regexes.values():
            if not re.match(regex, self.value):
                raise ValidationException("Invalid " + sequencer_type + " Run ID: " + self.value)

@dataclass(frozen=True)
class MiSeqRunID(SequencingRunID):

    def __post__init__(self):
        miseq_run_id_regex = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
        if not re.match(miseq_run_id_regex, self.value):
            raise ValidationException("Invalid MiSeq Run ID: " + self.value)


@dataclass(frozen=True)
class NextSeqRunID(SequencingRunID):
    value: str

    def __post__init__(self):
        nextseq_run_id_regex = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"
        if not re.match(nextseq_run_id_regex, self.value):
            raise ValidationException("Invalid NextSeq Run ID: " + self.value)


@dataclass(frozen=True)
class GridIonRunID(SequencingRunID):
    value: str

    def __post__init__(self):
        gridion_run_id_regex = "\d{8}_\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}"
        if not re.match(gridion_run_id_regex, self.value):
            raise ValidationException("Invalid GridION Run ID: " + self.value)


@dataclass(frozen=True)
class PromethIonRunID(SequencingRunID):
    value: str

    def __post__init__(self):
        promethion_run_id_regex  = "\d{8}_\d{4}_P2S_[0-9]{5}-\d{1}_[A-Z0-9]+_[a-z0-9]{8}"
        if not re.match(promethion_run_id_regex, self.value):
            raise ValidationException("Invalid PromethION Run ID: " + self.value)

