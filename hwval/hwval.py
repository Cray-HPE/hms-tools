#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2020-2021] Hewlett Packard Enterprise Development LP
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
import json
import requests

from os import path

import hostlist

from debug import dbgPrint, dbgMed, dbgHigh, setDbgLevel
from auth import getAuthenticationToken

auth_token = getAuthenticationToken()

"""
HW Validation modules
"""
from capmcValidation import capmcValidation

hwValidationModule = [
        capmcValidation
        ]

def nidsToXnames(nidlist):
    dbgPrint(dbgMed, "nidsToXnames")

    getHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            }

    queryparams = {}
    queryparams['nid'] = []
    for n in nidlist.split(','):
        queryparams['nid'].append(int(n))

    URL = "https://api-gw-service-nmn.local/apis/smd/hsm/v1/State/Components"

    dbgPrint(dbgMed, "POST: %s %s" % (URL, queryparams))
    dbgPrint(dbgHigh, "POST: %s" % getHeaders)

    r = requests.get(url = URL, headers = getHeaders, params = queryparams)

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 300:
        return 1

    components = json.loads(r.text)
    xnames = None
    for comp in components['Components']:
        if xnames is None:
            xnames = comp['ID']
        else:
            xnames = xnames + ',' + comp['ID']

    return xnames

def main():
    parser = argparse.ArgumentParser(description='Automatic hardware validation tool.')
    parser.add_argument('-l', '--list', 
            help='List modules and tests that are available. all: show all '
               'modules and tests, top: show top level modules, <module>: show '
               'tests for the module')
    parser.add_argument('-x', '--xnames',
            help='Xnames to do hardware validation on. Valid options are a '
               'single xname, comma separated xnames, or hostlist style xnames')
    parser.add_argument('-n', '--nids',
            help='Nids to do hardware validation on. Valid options are a '
               'single nid, comma separated nids, or hostlist style nids: '
               '[1-10]')
    parser.add_argument('-t', '--tests',
            help='List of tests to execute in the form '
                '<module>:<test>[,<module>:<test>[,...]]')
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

    if args.verbose:
        setDbgLevel(args.verbose)

    if args.list:
        if args.list == "all" or args.list == "top":
            for pkg in hwValidationModule:
                print("%s" % pkg.__name__)
                if args.list == "all":
                    tests = pkg(None, None, True)
                    for t in tests:
                        print("     %s" % t.__name__)
        else:
            for pkg in hwValidationModule:
                if pkg.__name__ == args.list:
                    print("%s" % pkg.__name__)
                    tests = pkg(None, None, True)
                    for t in tests:
                        print("     %s" % t.__name__)

        return 0

    if args.xnames is None and args.nids is None:
        parser.print_usage()
        print("%s: error: missing argument" % path.basename(__file__))
        return 1

    if args.nids is not None:
        nids = hostlist.expand(args.nids)
        xnames = nidsToXnames(nids)

    if args.xnames is not None:
        if xnames is not None:
            args.xnames = args.xnames + ',' + xnames
        xnames = hostlist.expand(args.xnames)

    dbgPrint(dbgMed, "Nodes to validate: %s" % xnames)

    # Convert into a list and remove duplicates
    xnames = xnames.split(',')
    xnames_set = set(xnames)
    xnames = (list(xnames_set))

    tests = {}
    if args.tests:
        pairs = args.tests.split(',')
        for p in pairs:
            kv = p.split(':')
            if kv[0] not in tests:
                tests[kv[0]] = []
            tests[kv[0]].append(kv[1])

    dbgPrint(dbgMed, "Tests to execute: %s" % tests)

    failures = 0

    for xname in xnames:
        if tests:
            for m in tests.keys():
                for module in hwValidationModule:
                    if m == module.__name__:
                        print("\033[1;36m%s(%s):\033[0m" % (module.__name__, xname))
                        ret = module(xname, tests[m])
                        failures = failures + ret
        else:
            for module in hwValidationModule:
                print("\033[1;36m%s(%s):\033[0m" % (module.__name__, xname))
                ret = module(xname)
                failures = failures + ret

    if failures == 0:
        print("All validations PASSED")
    else:
        print("%d Validations FAILED" % failures)

    print("Done")

    return 0

if __name__ == "__main__":
    ret = main()
    exit(ret)
