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

eventServiceURIs_1_3 = [
    ["RegistryPrefixes", list],
    ["ResourceTypes", list],
    ["Subscriptions", dict]
]

eventServiceURIs_pre_1_3 = [
    ["EventTypesForSubscription", list],
    ["Subscriptions", dict]
]

def checkRedfishEventService(bmcName):
    dbgPrint(dbgMed, "checkRedfishEventService")
    badResults = 0

    path = "https://" + bmcName + "/redfish/v1/EventService"
    dbgPrint(dbgMed, "checkRedfishEventService checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("checkRedfishEventService")
        printExtraError(label, msg)
        return 1

    response = json.loads(payload)

    checkURIs = []
    if response["@odata.type"] < "#EventService.v1_3_0.EventService":
        checkURIs = eventServiceURIs_pre_1_3
    else:
        checkURIs = eventServiceURIs_1_3

    for check in checkURIs:
        badResults += validateField("checkRedfishEventService",
                            "/redfish/v1/EventService", check[FIELD],
                            response, check[TYPE])

    if badResults == 0:
        printOK("checkRedfishEventService")

    return badResults