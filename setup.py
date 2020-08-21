"""
Setup script for the FIRE package.
"""

import os
import subprocess
from setuptools import setup
from setuptools import find_packages

import fire


SHORT_DESCR = "FIRE - FIkspunktREgister"


def readme():
    """
    Return a properly formatted readme text that can be used as the long
    description for setuptools.setup.
    """
    try:
        with open("README.md") as f:
            readme = f.read()
        return readme
    except:
        return SHORT_DESCR


setup(
    name="fire",
    version=fire.__version__,
    description=SHORT_DESCR,
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Danish",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["test", "flame"]),
    keywords="levelling database geodesy",
    url="https://github.com/Kortforsyningen/fire",
    author="SDFE, Septima",
    author_email="grf@sdfe.dk",
    license="MIT",
    test_suite="pytest",
    tests_require=["pytest>=3.1"],
    install_requires=["cx_Oracle>=7.0", "sqlalchemy>=1.2.13", "click", "click_plugins"],
    python_requires=">=3.6",
    entry_points="""
        [console_scripts]
        fire=fire.cli.main:fire

        [fire.cli.fire_commands]
        info=fire.cli.info:info
        gama=fire.cli.gama:gama
        niv=fire.cli.niv:niv
        søg=fire.cli.søg:søg
    """,
)
