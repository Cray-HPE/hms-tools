#!/usr/bin/python3

import sys
import argparse
import getpass

from debug import *
from dependencies import *
from riverTriage import *
from mountainTriage import *
from k8s import *


def main():
    parser = argparse.ArgumentParser(description='Automatic triaging tool.')
    parser.add_argument('-H', '--host',
            help='Target host to execute triage on.')
    parser.add_argument('--xnames',
            help='xnames to do a focused triage on.')
    parser.add_argument('-v', '--verbose', action="count", default=0,
            help='Increase output verbosity.')
    args = parser.parse_args()

    if args.verbose is not None:
        setDbgLevel(args.verbose)

    # if args.host is not None:
    #     un = input('Enter username to connect to ' + args.host + ': ')
    #     try:
    #         pw = getpass.getpass()
    #     except Exception as error:
    #         print('ERROR', error)
    #     dbgPrint(dbgHigh, un + ' : ' + pw)

    if args.host is None:
        args.host = "localhost"

    validateHmsDependencies(args.host)
    triageRiverDiscovery()
    triageMountainDiscovery()

    print("Done")

    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)
