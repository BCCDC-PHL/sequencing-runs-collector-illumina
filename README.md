# sequencing-runs-collector

A database for storing info about sequencing runs.

# Installation
Depending on the deployment environment, it may make sense to create a conda or virtualenv. If doing so, ensure that the python version is >=3.10,<3.11.

```
conda create -n sequencing-runs-collector python=3.10
conda activate sequencing-runs-collector
```

From the top-level of this repo, use pip to install the app module.

```
pip install .
```

If setting up a development environment, install the app module in 'editable' mode:

```
pip install -e .
```

## Config

A [config template](config-template.json) is provided in the repo. The config file should look like this:

```json
{
    "run_parent_dirs": [
        "/path/to/runs",
        "/path/to/more/runs"
    ],
    "local_timezone": "America/Vancouver",
    "project_id_translation_file": "project_id_translation.csv",
    "scan_interval_seconds": 10,
    "api_root": "http://localhost:8080/",
    "api_token": "supersecret",
    "submit": false,
    "write_to_file": true,
    "output_directory": "test_output"
}
```

An optional `project_id_translation_file` can be provided to translate from the project IDs in SampleSheet files to the project IDs to store in the database. If one is provided, it should be a two-column .csv file with the headers:

`samplesheet_project_id`
`sequencing_runs_service_project_id`

For example:

```csv
samplesheet_project_id,sequencing_runs_service_project_id
28,antibiotic_resistance
35,outbreak_investigation
48,emerging_pathogens
35,assay_development
```

