'''clangTooling header files.'''

import pathlib


def include_dir() -> pathlib.Path:
    '''Location of header files.'''
    return pathlib.Path(__file__).parent
