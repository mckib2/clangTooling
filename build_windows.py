'''Do local builds of Windows x86 and x64.'''

import argparse

from build_utils import do_build


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', choices=['win32', 'win_amd64'], help='Target windows platform.', required=True)
    args = parser.parse_args()
    do_build(win_plat=args.p)
