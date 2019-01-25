"""
Setup script for the fire-cli package.
"""

import os
import subprocess
from setuptools import setup

import firecli

SHORT_DESCR = 'Kommandolinjeinterface til fikspunktsregistret FIRE'

def readme():
    """
    Return a properly formatted readme text that can be used as the long
    description for setuptools.setup.
    """
    try:
        with open('README.md') as f:
            readme = f.read()
        return readme
    except:
        return SHORT_DESCR

setup(
    name='fire-cli',
    version=firecli.__version__,
    description=SHORT_DESCR,
    long_description=readme(),
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Science/Research',
      'License :: OSI Approved :: ISC License (ISCL)',
      'Topic :: Scientific/Engineering :: GIS',
      'Topic :: Utilities'
    ],
    packages=['firecli'],
    entry_points = '''
        [console_scripts]
        fire=firecli.main:fire

        [firecli.fire_commands]
        info=firecli.info:info
    ''',
    keywords='levelling database geodesy',
    url='https://github.com/Kortforsyningen/fire-cli',
    author='Kristian Evers',
    author_email='kreve@sdfe.dk',
    license='MIT',
    py_modules=['firecli'],
    install_requires=[
        'click',
        'click_plugins',
        'fireapi',
    ],
)