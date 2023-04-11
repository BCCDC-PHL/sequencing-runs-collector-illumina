from setuptools import setup, find_packages

import sequencing_runs

setup(
    name='sequencing-runs-service',
    version=sequencing_runs.__version__,
    description='',
    author='Dan Fornika',
    author_email='dan.fornika@bccdc.ca',
    url='https://github.com/BCCDC-PHL/sequencing-runs-service',
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
        "flask==2.2.3",
        "flask-sqlalchemy==3.0.3",
        "marshmallow-jsonapi==0.24.0",
        # These are testing requirements, should be moved to
        # another section
        "pytest==7.3.0",
        "requests==2.28.2",
    ],
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=[
        
    ],
    entry_points = {
        'console_scripts': [],
    }
)
