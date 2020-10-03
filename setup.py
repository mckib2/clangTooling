'''Rely on cmake to build clangTooling and dependencies.'''

from tempfile import TemporaryDirectory
import subprocess
import pathlib
from fnmatch import filter as fnfilter
from shutil import copytree, copyfileobj
from os import cpu_count
from os.path import isdir, join
import distutils.ccompiler
import logging
from time import time

from distutils.core import setup
from setuptools import find_packages


def _include_patterns(*patterns):
    def _ignore_patterns(path, names):
        keep = set(name for pattern in patterns for name in fnfilter(names, pattern))
        ignore = set(name for name in names if name not in keep and not isdir(join(path, name)))
        return ignore
    return _ignore_patterns


def _copy(src, dst):
    tstart = time()
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
    with TemporaryDirectory() as tmpdir:
        clone_cmd = ['git', 'clone', '--depth', '1', '--single-branch', git_url, tmpdir]
        _run_cmd(clone_cmd, 'Failed to get git repo')

        build_dir = pathlib.Path(tmpdir) / 'build'
        build_dir.mkdir(exist_ok=True, parents=True)
        cmake_cmd = ['cmake', '-DLLVM_ENABLE_PROJECTS=clang', '-GNinja', '../llvm']
        _run_cmd(cmake_cmd, 'Failed cmake configure', cwd=build_dir)

        ncpu = cpu_count()
        target = 'clangTooling'
        make_cmd = ['ninja', target, f'-j{ncpu if ncpu else 1}']
        _run_cmd(make_cmd, f'Failed to make target {target}', cwd=build_dir)

        lib_dir = pathlib.Path(__file__).parent / 'lib'
        include_dir = pathlib.Path(__file__).parent / 'include'
        lib_dir.mkdir(exist_ok=True, parents=True)
        include_dir.mkdir(exist_ok=True, parents=True)
        lib_ext = distutils.ccompiler.new_compiler().library_filename('', lib_type='static')
        lib_ext = pathlib.Path(lib_ext).suffix
        logging.info('Found static library extension: %s', lib_ext)
        tstart = time()
        for lib in (build_dir / 'lib').glob(f'*{lib_ext}'):
            _copy(lib, lib_dir / lib.name)
        logging.info('Took %g seconds to copy static libraries', (time() - tstart))
        tstart = time()
        copytree(
            tmpdir, include_dir, dirs_exist_ok=True,
            ignore=_include_patterns('*.h', '*.inc'), copy_function=_copy)
        logging.info('Took %g seconds to copy headers', (time() - tstart))


logging.basicConfig(level=logging.INFO)
if len(list((pathlib.Path(__file__).parent / 'lib').glob('*'))) == 1:
    logging.info('Building static libaries...')
    do_build()
else:
    logging.info('Static libraries appear to exist already')

setup(
    name='clangTooling',
    version='0.0.1',
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
)
