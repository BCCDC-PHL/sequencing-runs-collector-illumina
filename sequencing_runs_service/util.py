import datetime
import hashlib
import re

# https://stackoverflow.com/a/1176023
def camel_to_snake(name):
    """
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


# https://stackoverflow.com/a/1960546
def row2dict(row):
    """
    """
    d = {}
    for column in row.__table__.columns:
        d[column.name] = getattr(row, column.name)

    return d

def md5(file_path):
    """
    Calculate MD5 checksum of a file.

    :param file_path: Path to the file.
    :type file_path: str
    :return: MD5 checksum
    :rtype: str
    """
    with open(file_path, 'rb') as f:
        file_contents = f.read()
        md5 = hashlib.md5(file_contents).hexdigest()

    return md5
