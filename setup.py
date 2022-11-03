import os
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="hpe_warranty_lookup",
    version="0.2.2",
    author="Paul Scherrer Institute",
    author_email="science-it@psi.ch",
    description=("Simple script to check HPE warranty status"),
    license="GPLv3",
    keywords="",
#    url="https://github.com/paulscherrerinstitute/data_api_python",
    packages=["hpe_warranty_lookup", ],
#    long_description=read('README.md'),
    entry_points={
        'console_scripts': [
            'hpe-warranty-lookup=hpe_warranty_lookup.hpe_warranty_lookup:main',
        ]
    },
    install_requires=[
        'requests',
        'bs4'
    ]

)