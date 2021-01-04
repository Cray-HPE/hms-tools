#!/usr/bin/python3

import sys
import argparse

from os import path

from debug import *

"""
HW Validation modules
"""
from capmcValidation import *

hwValidationModule = [
        capmcValidation
        ]


def main():
    parser = argparse.ArgumentParser(description='Automatic hardware validation tool.')
    parser.add_argument('-X', '--xname',
            help='Xname to do hardware validation on.')
    parser.add_argument('-v', '--verbose', action="count", default=0,
            help='Increase output verbosity.')
    parser.add_argument('-V', '--version', action="store_true",
            help='Print the script version information and exit.')
    args = parser.parse_args()

    if args.version is True:
        script_dir = path.dirname(__file__)
        filename = ".version"
        with open(script_dir + "/" + filename, "r") as ver:
            print("%s: %s" % (__file__, ver.read()))
        return 0

    if args.verbose is not None:
        setDbgLevel(args.verbose)

    if args.xname is None:
        print("Invalid argument.")
        return 1

    idx = 0
    while idx < len(hwValidationModule):
        dbgPrint(dbgMed, "Calling: %d %s" % (idx, hwValidationModule[idx].__name__))
        hwValidationModule[idx](args.xname)
        idx = idx + 1

    print("Done")

    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)
