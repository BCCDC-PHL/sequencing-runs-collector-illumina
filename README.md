# sequencing-runs-db

A database for storing info about sequencing runs.

# Installation
Depending on the deployment environment, it may make sense to create a conda or virtualenv. If doing so, ensure that the python version is >=3.10,<3.11.

```
conda create -n sequencing-runs-db python=3.10
conda activate sequencing-runs-db
```

From the top-level of this repo, use pip to install the app module.

```
pip install .
```

If setting up a development environment, install the app module in 'editable' mode:

```
pip install -e .
```

## Database setup
Currently sqlite is the only supported database, and the database must be located at the top-level of the repo, and named `dev.db`. This setup is intended to support lightweight early development. Database support will be improved before production deployment.

To clear any existing database and re-generate from scratch:

```
rm sequencing_runs.db
rm alembic/versions/*.py
alembic revision --autogenerate -m 'init'
alembic upgrade head
```

## Loading data
A simple data loading script has been provided under the `scripts` directory. It can be used
to load a single sequencing run into the database as follows:

```
load_sequencing_run.py --db sequencing_runs.db /path/to/sequencing_run
```

An optional `project_id_translation` file can be provided to translate from the project IDs in SampleSheet files to the project IDs to store in the database. If one is provided, it should be a two-column .csv file with the headers:

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

Use the project ID translation file as follows:

```
load_sequencing_run.py --db dev.db \
  --project-id-translation-table /path/to/project_id_translation_table.csv \
  /path/to/sequencing_run
```

