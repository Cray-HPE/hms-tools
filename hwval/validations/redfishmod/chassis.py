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
from utils.health import printOK
from utils.health import printInfo, printExtraInfo
from utils.health import printError, printExtraError
from utils.redfish import makeRedfishCall, validateField, FIELD, TYPE

chassisURIs = [
    ["AssetTag", str],
    ["SerialNumber", str],
    ["Power", dict],
    ["PartNumber", str],
    ["Manufacturer", str],
    ["Model", str]
]

def checkRedfishChassis(bmcName):
    dbgPrint(dbgMed, "checkRedfishChassis")
    badResults = 0

    path = "https://" + bmcName + "/redfish/v1/Chassis"
    dbgPrint(dbgMed, "checkRedfishChassis checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("checkRedfishChassis")
        printExtraError(label, msg)
        return 1

    response = json.loads(payload)

    if "Members" not in response:
        printError("checkRedfishChassis")
        printExtraError(path + " .Members", "missing")
        return 1

    for member in response["Members"]:
        path = "https://" + bmcName + member["@odata.id"]
        dbgPrint(dbgMed, "checkRedfishChassis checking " + path)
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError("checkRedfishChassis")
            printExtraError(label, msg)
            badResults += 1
            continue

        mResponse = json.loads(payload)

        if ("ChassisType" in mResponse and
            (mResponse["ChassisType"] == "Enclosure" or
             mResponse["ChassisType"] == "RackMount")):
            for check in chassisURIs:
                badResults += validateField("checkRedfishChassis", path,
                                        check[FIELD], mResponse, check[TYPE])
        else:
            printInfo("checkRedfishChassis")
            printExtraInfo("Skipping "+member["@odata.id"],
                                "URI is for a " + mResponse["ChassisType"])

    if badResults == 0:
        printOK("checkRedfishChassis")

    return badResults