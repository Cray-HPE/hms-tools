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

import json

from utils.debug import dbgPrint, dbgMed
from utils.health import printOK
from utils.health import printInfo, printExtraInfo
from utils.health import printError, printExtraError
from utils.redfish import makeRedfishCall, validateField, FIELD, TYPE

fwInvFields = [
    ["@odata.id", str],
    ["Id", str],
    ["Version", str],
    ["Name", str],
]

def checkRedfishFirmwareInventoryComp(bmcName, fwURI):
    fname = "checkRedfishFirmwareInventoryComp"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + fwURI
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if payload:
        mResponse = json.loads(payload)

        for check in fwInvFields:
            badResults += validateField(fname, fwURI, check[FIELD], mResponse,
                                    check[TYPE])
    else:
        printError(fname)
        printExtraError(label, msg)
        badResults += 1

    return badResults

def checkRedfishFirmwareInventory(bmcName, fwURI):
    fname = "checkRedfishFirmwareInventory"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + fwURI
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if payload:
        response = json.loads(payload)

        badResults += validateField(fname, fwURI, "Members", response, list)
        if "Members" in response:
            for member in response["Members"]:
                badResults += checkRedfishFirmwareInventoryComp(bmcName,
                    member["@odata.id"])
    else:
        printError(fname)
        printExtraError(label, msg)
        badResults += 1

    return badResults

actionFields = [
    ["@Redfish.ActionInfo", str],
    ["target", str],
]

def checkRedfishUpdateService(bmcName):
    fname = "checkRedfishUpdateService"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + "/redfish/v1/UpdateService"
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError(fname)
        printExtraError(label, msg)
        return 1

    response = json.loads(payload)

    # Check Actions structure
    aField = response["Actions"]["#UpdateService.SimpleUpdate"]
    for e in actionFields:
        badResults += validateField(fname, "/redfish/v1/UpdateService",
                                e[FIELD], aField, e[TYPE])

    badResults += checkRedfishFirmwareInventory(bmcName,
                           response["FirmwareInventory"]["@odata.id"])

    if badResults == 0:
        printOK(fname)

    return badResults