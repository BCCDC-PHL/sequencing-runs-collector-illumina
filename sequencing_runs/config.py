import os

def get_database_uri():
    path = os.environ.get("SEQUENCING_RUNS_DB_PATH", "sequencing_runs.db")
    return f"sqlite:///{path}"
