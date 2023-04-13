import xmltodict

def parse_rta_configuration(rta_config_path):
    rta_config = {}
    doc = None
    with open(rta_config_path) as f:
        doc = xmltodict.parse(f.read(), process_namespaces=True)

    if doc is not None:
        samplesheet_filename = doc["RTAConfiguration"]["SampleSheetFileName"]
        
        rta_config['samplesheet_filename'] = samplesheet_filename

    return rta_config
