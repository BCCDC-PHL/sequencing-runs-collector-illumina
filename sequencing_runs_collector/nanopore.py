import glob
import json
import os
import re

from pathlib import Path
from typing import Optional

GRIDION_RUN_ID_REGEX = "\\d{8}_\\d{4}_X[1-5]_[A-Z0-9]+_[a-z0-9]{8}"
PROMETHION_RUN_ID_REGEX = "\\d{8}_\\d{4}_P2S_[0-9]{5}-\\d{1}_[A-Z0-9]+_[a-z0-9]{8}"


def find_fastq_output_dir(run_dir: Path) -> Optional[Path]:
    """
    Find the FASTQ output directory for a demultiplexing output directory.
    :param run_dir: Run output directory
    :type run_dir: Path
    :return: Path to the FASTQ output directory, or None if not found.
    :rtype: Optional[Path]
    """
    
    fastq_dir = None
    fastq_pass_dir = Path(os.path.join(run_dir, 'fastq_pass'))
    if os.path.exists(fastq_pass_dir):
        fastq_dir = fastq_pass_dir

    return fastq_dir


def find_samplesheet(run_dir: Path, instrument_type: str) -> Optional[Path]:
    """
    """
    samplesheet_path = None
    samplesheet_paths_glob = os.path.join(run_dir, 'sample_sheet*.csv')
    samplesheet_paths = glob.glob(samplesheet_paths_glob)
    if len(samplesheet_paths) == 1:
        samplesheet_path = Path(samplesheet_paths[0])

    return samplesheet_path


def find_report_json(run_dir: Path, instrument_type: str) -> Optional[Path]:
    """
    """
    report_json_path = None
    report_json_paths_glob = os.path.join(run_dir, 'report_*.json')
    report_json_paths = glob.glob(report_json_paths_glob)
    if len(report_json_paths) == 1:
        report_json_path = Path(report_json_paths[0])

    return report_json_path


def parse_report_json(report_json_path: Path):
    """
    """
    report_json = None
    with open(report_json_path, 'r') as f:
        report_json = json.load(f)
