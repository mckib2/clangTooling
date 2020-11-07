'''clangTooling header files.'''

import pathlib


def header_dir() -> pathlib.Path:
    '''Location of header files.'''
    return pathlib.Path(__file__).parent / 'headers/'


def llvm_includes() -> list:
    '''Include directories for LLVM.'''
    hdrs = header_dir()
    return [
        hdrs / 'llvm/include',
        hdrs / 'build/include',
    ]


def clang_includes() -> list:
    '''Include directories for clang.'''
    hdrs = header_dir()
    return [
        hdrs / 'clang/include',
        hdrs / 'build/tools/clang/include',
    ]
