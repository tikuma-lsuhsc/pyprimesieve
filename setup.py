#!/usr/bin/env python

import os
import re
import sys
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

with open(os.path.join(os.path.dirname(__file__), 'pyprimesieve', 'pyprimesieve.cpp')) as f:
    VERSION = re.search(r'__version__.*"(\d.*?)"', f.read()).group(1)

# the following code for C extension failure copied from SQLAlchemy's setup.py
# ----
ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32':
    # 2.6's distutils.msvc9compiler can raise an IOError when failing to
    # find the compiler
    ext_errors += (IOError,)


class BuildFailed(Exception):

    def __init__(self):
        self.cause = sys.exc_info()[1]  # work around py 2/3 different syntax


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(sys.exc_info()[1]):  # works with both py 2/3
                raise BuildFailed()
            raise


def status_msgs(*msgs):
    print('*' * 75)
    for msg in msgs:
        print(msg)
    print('*' * 75)

# ----


PRIMESIEVE_DIR = 'primesieve/src'
PRIMESIEVE_FILES = ['EratBig.cpp', 'EratMedium.cpp', 'EratSmall.cpp', 'ParallelPrimeSieve.cpp', 'PreSieve.cpp',
                    'PrimeFinder.cpp', 'PrimeGenerator.cpp', 'PrimeSieve.cpp', 'SieveOfEratosthenes.cpp',
                    'WheelFactorization.cpp', 'popcount.cpp']
PRIMESIEVE = [os.path.join(PRIMESIEVE_DIR, filename) for filename in PRIMESIEVE_FILES]


def run_setup(openmp):
    if openmp:
        kwargs = {
            'extra_compile_args': ['-fopenmp'],
            'extra_link_args': ['-fopenmp']
        }
    else:
        kwargs = {}

    setup(
        name='pyprimesieve',
        version=VERSION,
        packages=[''],
        cmdclass={'build_ext': ve_build_ext},
        package_data={'': ['LICENSE']},
        ext_modules=[
            Extension('pyprimesieve', sources=['pyprimesieve/pyprimesieve.cpp'] + PRIMESIEVE,
                      include_dirs=[PRIMESIEVE_DIR], **kwargs),
        ],
    )

try:
    run_setup(True)

except BuildFailed as exc:
    status_msgs(
        exc.cause,
        "WARNING: pyprimesieve could not be compiled using OpenMP flags.",
        "Failure information, if any, is above.",
        "Retrying the build without OpenMP support now."
    )

    run_setup(False)

    status_msgs(
        "WARNING: pyprimesieve could not be compiled using OpenMP.",
        "Function `primes_sum` will not execute in parallel on machines with multiple cores.",
        "Non-parallel build succeeded."
    )
