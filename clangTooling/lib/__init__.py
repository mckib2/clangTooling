'''clangTooling static libraries.'''

import pathlib


def library_dir() -> pathlib.Path:
    '''Get directory where static libraries live.'''
    return pathlib.Path(__file__).parent
