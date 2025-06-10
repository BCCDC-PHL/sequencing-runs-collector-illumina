from setuptools import setup, find_packages

setup(
    name='sequencing-runs-collector',
    version="0.1.0",
    description='',
    author='Dan Fornika',
    author_email='dan.fornika@bccdc.ca',
    url='https://github.com/BCCDC-PHL/sequencing-runs-collector',
    packages=find_packages(exclude=('tests', 'tests.*')),
    python_requires='>=3.10,<3.14',
    install_requires=[
        "jsonschema",
        "xmltodict==0.14.2",
        "interop==1.5.0",
        "pyfastx==2.2.0",
        "pytz==2023.3"
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
