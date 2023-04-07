from setuptools import setup, find_packages

import sequencing_runs_db

setup(
    name='sequencing-runs-db',
    version=sequencing_runs_db.__version__,
    description='',
    author='Dan Fornika',
    author_email='dan.fornika@bccdc.ca',
    url='https://github.com/BCCDC-PHL/sequencing-runs-db',
    packages=find_packages(exclude=('tests', 'tests.*')),
    python_requires='>=3.10,<3.11',
    install_requires=[
        "sqlalchemy==1.4.44",
        "alembic==1.8.1",
        "xmltodict==0.13.0",
        "jsonschema==4.17.3",
        "interop==1.2.3",
        "pyfastx==1.0.1",
        "pytz==2023.3",
    ],
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=[],
    entry_points = {
        'console_scripts': [],
    }
)
