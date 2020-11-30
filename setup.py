'''Rely on cmake to build clangTooling and dependencies.'''

import subprocess
import pathlib
from shutil import which as shutil_which
import logging
import platform
import sys

from distutils.core import setup
from setuptools import Extension, find_packages

from clangTooling import get_lib_ext
from clangTooling.lib import _clean_prefix, _clean_ext

from build_utils import _include_patterns, _run_cmd, do_build

# Windows requires nonempty static library name to get extension
LIB_EXT = get_lib_ext()
logging.info('Found static library extension: %s', LIB_EXT)

logging.basicConfig(level=logging.INFO)
# We don't want to rebuild clangTooling if it's a source
# distribution or the files have already been generated
if ('sdist' not in sys.argv and
        not list((pathlib.Path(__file__).parent / 'clangTooling/lib').glob(f'*{LIB_EXT}'))):
    logging.info('Checking build dependencies...')
    # if which('cmake') is None:
    _run_cmd(['python', '-m', 'pip', 'install', 'cmake'],
             "Failed to install cmake")
    # if which('ninja') is None:
    _run_cmd(['python', '-m', 'pip', 'install', 'ninja'],
             "Failed to install ninja")

    if platform.system() != 'Windows':
        logging.info('Building static libaries...')
        do_build()
    else:
        raise ValueError('Windows static libraries must be manually built!')
else:
    logging.info('Static libraries appear to exist already')


# Update list of link-ordered LLVM libraries if we
# have llvm-config available
if shutil_which('llvm-config') is not None:
    with open('clangTooling/lib/llvm_lib_list.txt', 'w') as txt:
        LLVM_LIBS = subprocess.run(
            ['llvm-config', '--libs', '--link-static'],
            stdout=subprocess.PIPE,
            check=True).stdout.decode()
        LLVM_LIBS = [_clean_prefix(_clean_ext(pathlib.Path(l)), '-l')
                     for l in LLVM_LIBS.split()]
        txt.write('\n'.join(LLVM_LIBS))


setup(
    name='clangTooling',
    version='0.0.6',
    author='Nicholas McKibben',
    author_email='nicholas.bgp@gmail.com',
    url='https://github.com/mckib2/clangTooling',
    license='MIT',
    description='clangTooling static libraries',
    long_description=open('README.rst', encoding='utf-8').read(),
    packages=find_packages(),
    keywords='clang',
    install_requires=open('requirements.txt', encoding='utf-8').read().split(),
    python_requires='>=3.6',
    include_package_data=True,
    package_data={
        '': [f'*{LIB_EXT}', '*.h', '*.inc', '*.def', 'llvm_lib_list.txt'],
    },

    # Add a dummy extension to get separate wheels for each OS
    ext_modules=[
        Extension(
            '_dummy',
            sources=['empty.c'],
            include_dirs=[str(pathlib.Path('./'))],
            language='c',
        )
    ],
)
