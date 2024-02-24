from setuptools import setup, find_packages

import sequencing_runs_collector

setup(
    name='sequencing-runs-collector',
    version=sequencing_runs_collector.__version__,
    description='',
    author='Dan Fornika',
    author_email='dan.fornika@bccdc.ca',
    url='https://github.com/BCCDC-PHL/sequencing-runs-collector',
    packages=find_packages(exclude=('tests', 'tests.*')),
    python_requires='>=3.10,<3.12',
    install_requires=[
        "jsonschema",
        "xmltodict==0.13.0",
        "interop==1.3.1",
        "pyfastx==2.0.2",
        "pytz==2023.3",
        "pytest==7.3.0",
        "requests==2.31.0",
    ],
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=[
        
    ],
    entry_points = {
        'console_scripts': [
            "sequencing-runs-collector = sequencing_runs_collector.__main__:main",
            "collect-single-run = sequencing_runs_collector.collect_single_run:main",
        ],
    }
)
