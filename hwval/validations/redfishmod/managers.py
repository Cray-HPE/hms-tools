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
from utils.health import printOK, printError, printExtraError
from utils.redfish import makeRedfishCall, validateField, FIELD, TYPE

managerURIs = [
    ["Name", str],
    ["Actions", dict],
    ["ManagerType", str],
    ["NetworkProtocol", dict]
]

def checkRedfishManagers(bmcName):
    dbgPrint(dbgMed, "checkRedfishManagers")
    badResults = 0

    path = "https://" + bmcName + "/redfish/v1/Managers"
    dbgPrint(dbgMed, "checkRedfishManagers checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("checkRedfishManagers")
        printExtraError(label, msg)
        return 1

    response = json.loads(payload)

    if "Members" not in response:
        printError("checkRedfishManagers")
        printExtraError(path + " .Members", "missing")
        return 1

    for member in response["Members"]:
        path = "https://" + bmcName + member["@odata.id"]
        dbgPrint(dbgMed, "checkRedfishManagers checking " + path)
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError("checkRedfishManagers")
            printExtraError(label, msg)
            badResults += 1
            continue

        mResponse = json.loads(payload)

        for check in managerURIs:
            badResults += validateField("checkRedfishManagers",
                                    member["@odata.id"], check[FIELD],
                                    mResponse, check[TYPE])

    if badResults == 0:
        printOK("checkRedfishManagers")

    return badResults