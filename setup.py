from setuptools import setup, find_packages

import sequencing_runs_service

setup(
    name='sequencing-runs-service',
    version=sequencing_runs_service.__version__,
    description='',
    author='Dan Fornika',
    author_email='dan.fornika@bccdc.ca',
    url='https://github.com/BCCDC-PHL/sequencing-runs-service',
    packages=find_packages(exclude=('tests', 'tests.*')),
    python_requires='>=3.10',
        install_requires=[
        "sqlalchemy==1.4.44",
        "alembic==1.8.1",
        "jsonschema==4.17.0",
        "fastapi==0.87.0",
        "uvicorn",
    ],
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=[],
    entry_points = {
        'console_scripts': [],
    }
)
