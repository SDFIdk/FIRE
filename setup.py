"""
Setup script for the FIRE package.
"""

import os
import subprocess
from setuptools import setup
from setuptools import find_packages

import fireapi
import firecli


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
    version=fireapi.__version__,
    description=SHORT_DESCR,
    long_description=readme(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Utilities",
    ],
    packages=find_packages(),
    keywords="levelling database geodesy",
    url="https://github.com/Kortforsyningen/fire",
    author="Septima / SDFE",
    author_email="grf@sdfe.dk",
    license="MIT",
    test_suite="pytest",
    tests_require=["pytest>=3.1"],
    install_requires=[
        "cx_Oracle>=7.0",
        "sqlalchemy>=1.2.13",
        "click",
        "click_plugins",
    ],
    python_requires=">=3.6",
    py_modules=["fireapi", "firecli", "firegama", "firemark"],
    entry_points="""
        [console_scripts]
        fire=firecli.main:fire

        [firecli.fire_commands]
        info=firecli.info:info
        gama=firegama.cli:gama
        mark=firemark.cli:mark
    """,
)
