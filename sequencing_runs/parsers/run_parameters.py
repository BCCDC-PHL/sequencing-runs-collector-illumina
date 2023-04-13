import json
import xmltodict

def parse_run_parameters(run_parameters_path):
    """
    """
    selected_run_parameters = {
        'experiment_name': None,
    }
    doc = None
    with open(run_parameters_path) as f:
        doc = xmltodict.parse(f.read(), process_namespaces=True)

    if doc is not None and 'RunParameters' in doc:
        run_parameters = doc['RunParameters']
        experiment_name = run_parameters.get('ExperimentName', None)
        selected_run_parameters['experiment_name'] = experiment_name
        if 'Reads' in run_parameters:
            selected_run_parameters['reads'] = []
            for read in run_parameters['Reads']['RunInfoRead']:
                r = {
                    'number': None,
                    'num_cycles': None,
                    'is_indexed_read': None,
                }
                try:
                    r['number'] = int(read['@Number'])
                except ValueError as e:
                    pass
                try:
                    r['num_cycles'] = int(read['@NumCycles'])
                except ValueError as e:
                    pass
                if read['@IsIndexedRead'] == "Y":
                    r['is_indexed_read'] = True
                elif read['@IsIndexedRead'] == "N":
                    r['is_indexed_read'] = False
                selected_run_parameters['reads'].append(r)
        elif 'CompletedCycles' in run_parameters:
            completed_cycles = run_parameters['CompletedCycles']
            selected_run_parameters['completed_cycles'] = {}
            c = {
                'read_1': None,
                'index_1': None,
                'index_2': None,
                'read_2': None,
            }
            try:
                c['read_1'] = int(completed_cycles.get('Read1', None))
            except ValueError as e:
                pass
            try:
                c['index_1'] = int(completed_cycles.get('Index1', None))
            except ValueError as e:
                pass
            try:
                c['index_2'] = int(completed_cycles.get('Index2', None))
            except ValueError as e:
                pass
            try:
                c['read_2'] = int(completed_cycles.get('Read2', None))
            except ValueError as e:
                pass
            selected_run_parameters['completed_cycles'] = c

    return selected_run_parameters
                
        
