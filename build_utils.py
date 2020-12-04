'''Utility functions for cloning and building clangTooling.'''

import pathlib
import subprocess
from tempfile import TemporaryDirectory
from fnmatch import filter as fnfilter
from shutil import copytree, copyfileobj, rmtree
from os import cpu_count, walk, chmod
from os.path import isdir, join
import logging
from time import time
import platform

from clangTooling import get_lib_ext


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

def _do_build(git_url, tmpdir):
    # either clone or update
    clone_cmd = ['git', 'clone', '--depth', '1', '--single-branch', git_url, tmpdir]
    try:
        _run_cmd(clone_cmd, 'Failed to get git repo')
    except ValueError:
        update_cmd = ['git', 'pull']
        _run_cmd(update_cmd, 'Failed to get or update git repo', cwd=tmpdir)

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


def do_build(git_url='https://github.com/llvm/llvm-project.git', win_plat=None, use_tmp=False):
    '''Build clangTooling from source.'''

    if win_plat is not None:
        if win_plat not in {'win32', 'win_amd64'}:
            raise ValueError(f'Unknown windows platform {str(win_plat)}')
        if use_tmp:
            with TemporaryDirectory() as tmpdir:
                _do_build(git_url, tmpdir)
        else:
            tmpdir = pathlib.Path(f'./build{win_plat}')
            tmpdir.mkdir(exist_ok=True, parents=True)
            tmpdir = str(tmpdir)
            _do_build(git_url, tmpdir)
    else:
        if use_tmp:
            with TemporaryDirectory() as tmpdir:
                _do_build(git_url, tmpdir)
        else:
            tmpdir = pathlib.Path(f'./build_clang')
            tmpdir.mkdir(exist_ok=True, parents=True)
            tmpdir = str(tmpdir)     
            _do_build(git_url, tmpdir)
