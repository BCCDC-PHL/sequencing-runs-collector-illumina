import json
import logging
import os
import xmltodict


def parse_runinfo_miseq_v1(runinfo_path):
    """
    Parse the RunInfo.xml file for a MiSeq run.

    :param runinfo_path: Path to the RunInfo.xml file
    :type runinfo_path: str
    :return: Run information
    :rtype: dict[str, object]
    """
    runinfo = {}
    doc = None
    with open(runinfo_path) as f:
        doc = xmltodict.parse(f.read(), process_namespaces=True)

    if doc is not None:
        run_datetime_str = doc["RunInfo"]["Run"]["Date"]
        reads = []
        runinfo_reads = doc["RunInfo"]["Run"]["Reads"]["Read"]
        # When the runinfo file has only one read, it is a dict, not a list
        if isinstance(runinfo_reads, dict):
            runinfo_reads = [runinfo_reads]
        for read in runinfo_reads:
            r = {}
            try:
                r['number'] = int(read['@Number'])
            except (ValueError, TypeError) as e:
                logging.error(json.dumps({'event_type': 'invalid_runinfo', 'runinfo_path': runinfo_path, 'read': read}))
            try:
                r['num_cycles'] = int(read['@NumCycles'])
            except (ValueError, TypeError) as e:
                logging.error(json.dumps({'event_type': 'invalid_runinfo', 'runinfo_path': runinfo_path, 'read': read}))
            
            if '@IsIndexedRead' in read and read['@IsIndexedRead'] == 'Y':
                r['is_indexed_read'] = True
            elif '@IsIndexedRead' in read and read['@IsIndexedRead'] == 'N':
                r['is_indexed_read'] = False

            reads.append(r)
        runinfo['reads'] = reads

    return runinfo


def parse_runinfo_nextseq_v1(runinfo_path):
    """
    Parse the RunInfo.xml file for a NextSeq run.

    :param runinfo_path: Path to the RunInfo.xml file
    :type runinfo_path: str
    :return: Run information
    :rtype: dict[str, object]
    """
    runinfo = {}
    doc = None
    with open(runinfo_path) as f:
        try:
            doc = xmltodict.parse(f.read(), process_namespaces=True)
        except Exception as e:
            logging.error(json.dumps({'event_type': 'invalid_runinfo', 'runinfo_path': runinfo_path, 'error': str(e)}))

    if doc is not None:
        run_datetime_str = doc["RunInfo"]["Run"]["Date"]
        reads = []
        runinfo_reads = doc["RunInfo"]["Run"]["Reads"]["Read"]
        # When the runinfo file has only one read, it is a dict, not a list
        if isinstance(runinfo_reads, dict):
            runinfo_reads = [runinfo_reads]
        for read in runinfo_reads:
            r = {}
            try:
                r['number'] = int(read.get('@Number', None))
            except (ValueError, TypeError) as e:
                logging.error(json.dumps({'event_type': 'invalid_runinfo', 'runinfo_path': runinfo_path, 'read': read}))
            try:
                r['num_cycles'] = int(read.get('@NumCycles', None))
            except (ValueError, TypeError) as e:
                logging.error(json.dumps({'event_type': 'invalid_runinfo', 'runinfo_path': runinfo_path, 'read': read}))
            if '@IsIndexedRead' in read and read['@IsIndexedRead'] == 'Y':
                r['is_indexed_read'] = True
            elif '@IsIndexedRead' in read and read['@IsIndexedRead'] == 'N':
                r['is_indexed_read'] = False

            reads.append(r)

        runinfo['reads'] = reads

    return runinfo
