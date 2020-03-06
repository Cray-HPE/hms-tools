#!/usr/bin/python3

import sys
import argparse
import getpass

from os import path

from debug import *
from dependencies import *
from riverTriage import *
from mountainTriage import *
from k8s import *


def main():
    parser = argparse.ArgumentParser(description='Automatic triaging tool.')
    """
    parser.add_argument('-H', '--host',
            help='Target host to execute triage on.')
    parser.add_argument('-X', '--xnames',
            help='xnames to do a focused triage on.')
    """
    parser.add_argument('-v', '--verbose', action="count", default=0,
            help='Increase output verbosity.')
    parser.add_argument('-V', '--version', action="store_true",
            help='Print the script version information and exit.')
    args = parser.parse_args()

    if args.version is not None:
        script_dir = path.dirname(__file__)
        filename = ".version"
        with open(script_dir + "/" + filename, "r") as ver:
            print("%s: %s" % (__file__, ver.read()))
        return 0

    if args.verbose is not None:
        setDbgLevel(args.verbose)

    # if args.host is not None:
    #     un = input('Enter username to connect to ' + args.host + ': ')
    #     try:
    #         pw = getpass.getpass()
    #     except Exception as error:
    #         print('ERROR', error)
    #     dbgPrint(dbgHigh, un + ' : ' + pw)
    #
    # if args.host is None:
    #     args.host = "localhost"

    validateHmsDependencies()
    triageRiverDiscovery()
    triageMountainDiscovery()

    print("Done")

    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)
