import os
from setuptools import setup
import ConfigParser


def load_metadata(ini_file):
    config = ConfigParser.ConfigParser()
    read_files = config.read(ini_file)
    if len(read_files) == 0:
        raise Exception("Failed to read %s" % ini_file)
    meta = {}
    for item in config.options("meta"):
        meta[item] = config.get("meta", item)
    return meta

METADATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gentle_django_mongo/METADATA')
META = load_metadata(METADATA_PATH)


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return ""

setup(
    name=META["name"],
    version=META["version"],
    author="Sebastian Phelps",
    author_email="sebastian.phelps@gmail.com",
    description=META["description"],
    keywords="gentle_django_mongo mongo django model",
    packages=['gentle_django_mongo'],
    include_package_data=True,
    package_data={'gentle_django_mongo': ['METADATA', ]},
    long_description=read('README.md'),
    requires=[
        'django (>=1.4.1)',
        'pymongo (>=2.7.1)'
    ],
    install_requires=[
        'django>=1.4.1',
        'pymongo>=2.7.1'
    ]
)
