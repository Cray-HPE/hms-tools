#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import sys
import argparse
import getpass

from os import path

from debug import *
from k8s import *

"""
Triage modules
"""
from dependencies import *
from riverTriage import *
from mountainTriage import *

triageModules = [
        validateHmsDependencies,
        triageRiverDiscovery,
        triageMountainDiscovery
        ]

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

    if args.version is True:
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

    idx = 0
    while idx < len(triageModules):
        dbgPrint(dbgMed, "Calling: %d %s" % (idx, triageModules[idx].__name__))
        triageModules[idx]()
        idx = idx + 1

    print("Done")

    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)
