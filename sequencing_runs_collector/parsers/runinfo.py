import json
import xmltodict


def parse_runinfo_nextseq_v1(runinfo_path):
    runinfo = {}
    doc = None
    with open(runinfo_path) as f:
        doc = xmltodict.parse(f.read(), process_namespaces=True)

    if doc is not None:
        run_datetime_str = doc["RunInfo"]["Run"]["Date"]
        reads = []
        for read in doc["RunInfo"]["Run"]["Reads"]["Read"]:
            r = {}
            r['number'] = int(read['@Number'])
            r['num_cycles'] = int(read['@NumCycles'])
            if read['@IsIndexedRead'] == 'Y':
                r['is_indexed'] = True
            else:
                r['is_indexed'] = False

            reads.append(r)
        runinfo['reads'] = reads

    return runinfo
