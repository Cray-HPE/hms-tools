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

import json

from utils.debug import dbgPrint, dbgMed
from utils.health import printOK, printError, printExtraError
from utils.redfish import makeRedfishCall, validateField, FIELD, TYPE, URI

URIData = [
    # [ URI, [field1, expectedType1, [subField1, subExpectedType1]], ..., [fieldN, expectedN]]
    ["/redfish/v1/", ["Chassis", dict], ["EventService", dict],
        ["Managers", dict], ["Systems", dict], ["UpdateService", dict]],
    ["/redfish/v1/Chassis", ["Members", list]],
    ["/redfish/v1/Systems", ["Members", list]],
    ["/redfish/v1/Managers", ["Members", list]],
    ["/redfish/v1/UpdateService", ["Actions", dict],
        ["FirmwareInventory", dict]],
    ["/redfish/v1/EventService", ["Subscriptions", dict]],
]

def checkRedfishURIs(bmcName):
    dbgPrint(dbgMed, "checkRedfishURIs")
    hostPath = "https://" + bmcName

    badResults = 0

    for entry in URIData:
        path = hostPath + entry[URI]
        dbgPrint(dbgMed, "checkRedfishURIs checking " + path)
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError("checkRedfishURIs")
            printExtraError(label, msg)
            badResults += 1
            continue

        response = json.loads(payload)

        idx = 1
        while idx < len(entry):
            e = entry[idx]
            badResults += validateField("checkRedfishURIs", path, e[FIELD],
                                        response, e[TYPE])
            idx += 1
            
    if badResults == 0:
        printOK("checkRedfishURIs")

    return badResults