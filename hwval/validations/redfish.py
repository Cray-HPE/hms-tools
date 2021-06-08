#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2021] Hewlett Packard Enterprise Development LP
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

from utils.debug import dbgPrint, setDbgLevel, dbgLow, dbgMed
from utils.health import printWarning, printExtraWarning
from utils.health import printError, printExtraError
from utils.redfish import convertXnameToBMCName

from .redfishmod.uris import checkRedfishURIs
from .redfishmod.chassis import checkRedfishChassis
from .redfishmod.managers import checkRedfishManagers
from .redfishmod.event_service import checkRedfishEventService
from .redfishmod.telemetry_poll import telemetryPoll
from .redfishmod.systems import checkRedfishSystems
from .redfishmod.update_service import checkRedfishUpdateService

validations = [
    #eventSubscribe,
    #eventTest,
    #eventDelete,
    checkRedfishURIs,
    checkRedfishChassis,
    checkRedfishManagers,
    checkRedfishEventService,
    checkRedfishSystems,
    checkRedfishUpdateService,
    telemetryPoll
        ]

def redfish(xname, tests=None, list=False, args=None):
    dbgPrint(dbgMed, "redfish")

    if list:
        return validations

    if not args:
        printError("redfish")
        printExtraError(xname, "Missing arguments")
        return 1

    if not args.user or not args.passwd:
        printError("redfish")
        printExtraError(xname, "Missing credentials")
        return 1

    bmcName = convertXnameToBMCName(xname)

    if not bmcName:
        printWarning("redfish")
        printExtraWarning(xname, "Could not determine BMC name")

    failures = 0
    if tests:
        for t in tests:
            for test in validations:
                if t == test.__name__:
                    dbgPrint(dbgMed, "Calling: redfish:%s" % test.__name__)
                    ret = test(bmcName)
                    failures = failures + ret
    else:
        for test in validations:
            dbgPrint(dbgMed, "Calling: redfish:%s" % test.__name__)
            ret = test(bmcName)
            failures = failures + ret

    return failures

if __name__ == "__main__":
    setDbgLevel(dbgLow)
    dbgPrint(dbgLow, "Calling: redfish(%s, %s, %s)" % (sys.argv[1],
        sys.argv[2], sys.argv[3]))
    exit(redfish(sys.argv[1], sys.argv[2], sys.argv[3]))

