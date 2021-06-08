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

cpuURIs = [
    ["Manufacturer", str],
    ["Model", str],
    ["SerialNumber", str],
    ["TotalCores", int],
    ["TotalThreads", int],
    ["MaxSpeedMHz", int],
]

def checkRedfishSystemsProcessorsCPU(bmcName, cpuURI):
    fname = "checkRedfishSystemsProcessorsCPU"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + cpuURI
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if payload:
        mResponse = json.loads(payload)
        for check in cpuURIs:
            badResults += validateField(fname, cpuURI,
                                check[FIELD], mResponse, check[TYPE])
    else:
        printError(fname)
        printExtraError(label, msg)
        badResults += 1

    return badResults

processorURIs = [
    ["Members", list],
    ["Members@odata.count", int]
]

def checkRedfishSystemsProcessors(bmcName, procURI):
    fname = "checkRedfishSystemsProcessors"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + procURI
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if payload:
        mResponse = json.loads(payload)

        for check in memoryURIs:
            badResults += validateField(fname, procURI,
                                    check[FIELD], mResponse, check[TYPE])
            if check[FIELD] == "Members" and check[FIELD] in mResponse:
                for member in mResponse[check[FIELD]]:
                    badResults += checkRedfishSystemsProcessorsCPU(bmcName,
                        member["@odata.id"])
    else:
        printError(fname)
        printExtraError(label, msg)
        badResults += 1

    return badResults

dimmURIs = [
    ["CapacityMiB", int],
    ["Id", str],
    ["MemoryDeviceType", str],
    ["Manufacturer", str],
    ["PartNumber", str],
    ["SerialNumber", str],
    ["OperatingSpeedMhz", int],
]

def checkRedfishSystemsMemoryDimms(bmcName, dimmURI):
    fname = "checkRedfishSystemsMemoryDimms"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + dimmURI
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if payload:
        mResponse = json.loads(payload)

        if "Status" in mResponse:
            if mResponse["Status"]["State"] != "Absent":
                for check in dimmURIs:
                    badResults += validateField(fname, dimmURI,
                                        check[FIELD], mResponse, check[TYPE])
            else:
                printInfo(fname)
                printExtraInfo(dimmURI, "Not present")
    else:
        printError(fname)
        printExtraError(label, msg)
        badResults += 1

    return badResults

memoryURIs = [
    ["Members", list],
    ["Members@odata.count", int]
]

def checkRedfishSystemsMemory(bmcName, memURI):
    fname = "checkRedfishSystemsMemory"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + memURI
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if payload:
        mResponse = json.loads(payload)

        for check in memoryURIs:
            badResults += validateField(fname, memURI,
                                    check[FIELD], mResponse, check[TYPE])
            if check[FIELD] == "Members" and check[FIELD] in mResponse:
                for member in mResponse[check[FIELD]]:
                    badResults += checkRedfishSystemsMemoryDimms(bmcName,
                        member["@odata.id"])
    else:
        printError(fname)
        printExtraError(label, msg)
        badResults += 1

    return badResults

systemsURIs = [
    ["Actions", dict],
    ["Bios", dict],
    ["BiosVersion", str],
    ["EthernetInterfaces", dict],
    ["Manufacturer", str],
    ["Memory", dict],
    ["MemorySummary", dict],
    ["Model", str],
    ["PartNumber", str],
    ["PowerState", str],
    ["Processors", dict],
    ["SerialNumber", str],
    ["SKU", str],
    ["Status", dict],
]

def checkRedfishSystems(bmcName):
    fname = "checkRedfishSystems"
    dbgPrint(dbgMed, fname)
    badResults = 0

    path = "https://" + bmcName + "/redfish/v1/Systems"
    dbgPrint(dbgMed, fname + " checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError(fname)
        printExtraError(label, msg)
        return 1

    response = json.loads(payload)

    if "Members" not in response:
        printError(fname)
        printExtraError(path + " .Members", "missing")
        return 1

    for member in response["Members"]:
        path = "https://" + bmcName + member["@odata.id"]
        dbgPrint(dbgMed, fname + " checking " + path)
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError(fname)
            printExtraError(label, msg)
            badResults += 1
            continue

        mResponse = json.loads(payload)

        for check in systemsURIs:
            badResults += validateField(fname, member["@odata.id"],
                                    check[FIELD], mResponse, check[TYPE])
            if check[FIELD] == "Memory" and check[FIELD] in mResponse:
                badResults += checkRedfishSystemsMemory(bmcName,
                        mResponse[check[FIELD]]["@odata.id"])
            if check[FIELD] == "Processors" and check[FIELD] in mResponse:
                badResults += checkRedfishSystemsProcessors(bmcName,
                        mResponse[check[FIELD]]["@odata.id"])

    if badResults == 0:
        printOK(fname)

    return badResults