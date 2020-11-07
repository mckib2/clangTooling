'''Rely on cmake to build clangTooling and dependencies.'''

from tempfile import TemporaryDirectory
import subprocess
import pathlib
from fnmatch import filter as fnfilter
from shutil import copytree, copyfileobj, rmtree, which as shutil_which
from os import cpu_count, walk, chmod
from os.path import isdir, join
import logging
from time import time
import platform
import sys

from distutils.core import setup
from setuptools import Extension, find_packages

from clangTooling import get_lib_ext
from clangTooling.lib import _clean_prefix, _clean_ext


# Windows requires nonempty static library name to get extension
LIB_EXT = get_lib_ext()
logging.info('Found static library extension: %s', LIB_EXT)


def _include_patterns(*patterns):
    def _ignore_patterns(path, names):
        keep = set(name for pattern in patterns for name in fnfilter(names, pattern))
        ignore = set(name for name in names if name not in keep and not isdir(join(path, name)))
        return ignore
    return _ignore_patterns


def _copy(src, dst):
    tstart = time()
    if not pathlib.Path(src).is_dir():
        pathlib.Path(src).parent.mkdir(exist_ok=True, parents=True)
        with open(src, 'rb') as src_fp, open(dst, 'wb') as dst_fp:
            copyfileobj(src_fp, dst_fp, length=32*1024*1024)
        logging.info('Copied %s -> %s in %g seconds', str(src), str(dst), (time() - tstart))


def _run_cmd(cmd, err_msg, cwd=None):
    try:
        logging.info('Running %s', str(cmd))
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as ex:
        print(ex)
        raise ValueError(err_msg)


def do_build(git_url='https://github.com/llvm/llvm-project.git'):
    '''Build clangTooling from source.'''

    # tmpdir = pathlib.Path('/tmp/clangTooling')
    # tmpdir.mkdir(exist_ok=True, parents=True)
    # from tempfile import NamedTemporaryFile
    # tmpdir = str(tmpdir)
    # with NamedTemporaryFile() as _dummy:
    with TemporaryDirectory() as tmpdir:
        clone_cmd = ['git', 'clone', '--depth', '1', '--single-branch', git_url, tmpdir]
        _run_cmd(clone_cmd, 'Failed to get git repo')

        build_dir = pathlib.Path(tmpdir) / 'build'
        build_dir.mkdir(exist_ok=True, parents=True)
        cmake_cmd = ['cmake', '-DLLVM_ENABLE_PROJECTS=clang',
                     '-DCMAKE_BUILD_TYPE=Release',
                     '-GNinja', '../llvm']
        _run_cmd(cmake_cmd, 'Failed cmake configure', cwd=build_dir)

        make_cmd = ['ninja', 'clangTooling', f'-j{cpu_count() if cpu_count() else 1}']
        _run_cmd(make_cmd, f'Failed to make target clangTooling', cwd=build_dir)

        # Silly Windows permission hacks for readonly tmp files
        if platform.system() == 'Windows':
            logging.info('Recursively changing file permissions for Windows')
            tstart = time()
            for root, dirs, files in walk(tmpdir):
                for folder in dirs:
                    chmod(join(root, folder), 0o777)
                for doc in files:
                    chmod(join(root, doc), 0o777)
            logging.info('Took %g seconds to recursively chmod', (time() - tstart))

        lib_dir = pathlib.Path(__file__).parent / 'clangTooling/lib'
        include_dir = pathlib.Path(__file__).parent / 'clangTooling/include'
        lib_dir.mkdir(exist_ok=True, parents=True)
        include_dir.mkdir(exist_ok=True, parents=True)
        tstart = time()
        for lib in (build_dir / 'lib').glob(f'*{LIB_EXT}'):
            _copy(lib, lib_dir / lib.name)
        logging.info('Took %g seconds to copy static libraries', (time() - tstart))
        tstart = time()
        hdr_dest_dir = include_dir / 'headers'
        if hdr_dest_dir.exists():
            rmtree(hdr_dest_dir)
        copytree(
            tmpdir, hdr_dest_dir,
            ignore=_include_patterns('*.h', '*.inc', '*.def'), copy_function=_copy)
        logging.info('Took %g seconds to copy headers', (time() - tstart))


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

    logging.info('Building static libaries...')
    do_build()
else:
    logging.info('Static libraries appear to exist already')


# Update list of link-ordered LLVM libraries if we
# have llvm-config available
if shutil_which('llvm-config') is not None:
    with open('llvm_lib_list.txt', 'w') as txt:
        LLVM_LIBS = subprocess.run(
            ['llvm-config', '--libs', '--link-static'],
            stdout=subprocess.PIPE,
            check=True).stdout.decode()
        LLVM_LIBS = [_clean_prefix(_clean_ext(pathlib.Path(l)), '-l')
                     for l in LLVM_LIBS.split()]
        txt.write('\n'.join(LLVM_LIBS))


setup(
    name='clangTooling',
    version='0.0.5',
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
