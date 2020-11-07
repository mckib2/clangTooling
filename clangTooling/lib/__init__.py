'''clangTooling static libraries.'''

import pathlib
import distutils.ccompiler


def get_lib_ext() -> str:
    '''Get the extension of a static library on this platform.'''
    # Windows requires nonempty static library name to get extension
    ext = distutils.ccompiler.new_compiler().library_filename('dummy', lib_type='static')
    return pathlib.Path(ext).suffix


def library_dir() -> pathlib.Path:
    '''Get directory where static libraries live.'''
    return pathlib.Path(__file__).parent


def _clean_prefix(name: str, prefix='lib') -> str:
    if len(name) > len(prefix) and name[:len(prefix)] == prefix:
        return name[len(prefix):]
    return name


def _clean_ext(name: pathlib.Path) -> str:
    return name.with_suffix('').name


def library_list() -> list:
    '''Return list of libraries included in this package.'''
    return [_clean_prefix(_clean_ext(l)) for l in library_dir().glob(f'*{get_lib_ext()}')]


def llvm_library_list() -> list:
    '''Return a list of included llvm libraries in linking order.'''

    # read in list of all LLVM libraries in correct order;
    # iterate through list keeping only entries that we have
    with open('llvm_lib_list.txt', 'r') as txt:
        theirs = txt.read().split()
    ours = set(library_list())
    return [lib for lib in theirs if lib in ours]


def clang_library_list() -> list:
    '''Return a list of included clang libraries in linking order.'''
    # We have to keep this list updated manually
    return [
        'clangTooling',
        'clangASTMatchers',
        'clangFormat',
        'clangFrontend',
        'clangDriver',
        'clangParse',
        'clangSerialization',
        'clangSema',
        'clangEdit',
        'clangAnalysis',
        'clangToolingCore',
        'clangAST',
        'clangRewrite',
        'clangLex',
        'clangBasic',
    ]
