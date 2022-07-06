#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2020-2022] Hewlett Packard Enterprise Development LP
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
import requests

from os import path
from base64 import b64decode
from re import search

from debug import *
from health import *
from k8s import *

maasBridgeFile = "cray_reds_maas_bridge.json"
maasBridgeDir = "/etc/ansible/hosts/host_files/ncn-w001/cray_reds"
mappingJsonFile = "mapping.json"
mappingJsonDir = "/etc/ansible/hosts/host_files/ncn-w001/cray_reds"
logDir = "/var/log/cray"

configMaps = [
        {
            "map": "cray-reds-maas-bridge-config",
            "fields": [ "reds-maas-bridge-data.json" ],
        }, {
            "map": "reds-client-urls",
            "fields": [ "REDS_X86_64_INITRD_URL", "REDS_X86_64_KERNEL_URL" ],
        }, {
            "map" :"reds-init-configmap",
            "fields": [ "GATEWAY_IP" ],
        }, {
            "map": "reds-mapping-json",
            "fields": [ "cray_reds_mapping.json" ],
        }, {
            "map": "smd-nid-map-json",
            "fields": [ "node_nid_map.json" ],
        }
        ]


def checkConfigMaps():
    dbgPrint(dbgMed, "checkConfigMaps ")
    for map in configMaps:
        cMap = getK8sClient().read_namespaced_config_map(map["map"], "services")

        badMap = False
        for f in map["fields"]:
            if (cMap.data.get(f) is None or
                    cMap.data[f] == ""):
                badMap = True
                badField = f

        if badMap == True:
            printNotHealthy(map["map"])
            printExtraHealth("Data field", "Missing required field: " + badField)
        else:
            printOK(map["map"])


def checkForFile(dir, file):
    dbgPrint(dbgMed, "checkForFile " + dir + "/" + file)
    fullPath = dir + "/" + file
    msg = ""
    if path.exists(fullPath) == False:
        msg = "missing"
    elif path.isfile(fullPath) == False:
        msg = "not a file"
    elif path.getsize(fullPath) == 0:
        msg = "empty"

    if msg != "":
        printNotHealthy(file)
        printExtraHealth("File status", msg)
        return 1

    printOK(file)
    return 0


def getRiverManagementNodes():
    dbgPrint(dbgMed, "getRiverManagementNodes")
    retList = []
    with open(maasBridgeDir + "/" + maasBridgeFile) as json_file:
        data = json.load(json_file)
        for e in data:
            retList.append(e['ID'])
    if getDbgLevel() > dbgMed:
        print(retList)
    return retList


def getRiverComputeNodes():
    dbgPrint(dbgMed, "getRiverComputeNodes")
    retList = []
    with open(mappingJsonDir + "/" + mappingJsonFile) as json_file:
        data = json.load(json_file)
        for s in data['switches']:
            for p in s['ports']:
                retList.append(p['peerID'])
    if getDbgLevel() > dbgMed:
        print(retList)
    return retList


def checkForNodeDiscovery(nList, auth_token):
    dbgPrint(dbgMed, "checkForNodeDiscovery")
    if getDbgLevel() > dbgLow:
        for n in nList:
            print(n)

    getHeaders = {
            "Authorization": "Bearer %s" % auth_token,
            'cache-control': "no-cache",
            }

    for n in nList:
        URL = "https://api-gw-service-nmn.local/apis/smd/hsm/v2/State/Components/" + n
        r = requests.get(url = URL, headers = getHeaders)
        if r.status_code >= 500:
            printNotHealthy(n)
            printExtraHealth("HSM", "Can't talk to HSM")
        elif r.status_code >= 400:
            printNotHealthy(n)
            printExtraHealth("Component", "Missing from HSM")
        elif r.status_code >= 300:
            printNotHealthy(n)
            printExtraHealth("HSM", "URI redirection")

        if getDbgLevel() > dbgMed:
            print("========================================================")
            print(r.url)
            print(r.status_code)
            print(r.text)
            print(r.headers)


def checkIfNames():
    dbgPrint(dbgMed, "checkIfNames")
    """ load configmap for reds-mapping-json and validate that all the ifNames
    don't have a space in them, or regex Str#/#/#+ """
    cMap = getK8sClient().read_namespaced_config_map("reds-mapping-json",
            "services", pretty=False)
    data = cMap.data
    map = data['cray_reds_mapping.json']
    decode = json.loads(map)
    switches = decode['switches']
    notHealthy = False
    for s in switches:
        for p in s['ports']:
            m = search('^[a-zA-Z]+\d\/\d+\/\d+$', p['ifName'])
            if m is None:
                notHealthy = True

    if notHealthy is True:
        printNotHealthy("REDS mapping ifNames")
        printExtraHealth("Format", "Doesn't match string#/#/#")
    else:
        printOK("REDS mapping ifNames")


query = 0
response = 1
queryAndResponse = [
        {
            "failOnFind": True,
            "query": "NBP filesize is 0 Bytes",
            "response": "Unable to download ipxe.efi, possible cert or network issue",
        }, {
            "failOnFind": True,
            "query": "Server response timeout",
            "response": "PXE-E18: Server response timeout",
        }, {
            "failOnFind": True,
            "query": "(bootscript).*(Connection timed out)",
            "response": "Timed out trying to download the BSS bootscript",
        }, {
            "failOnFind": True,
            "query": "(bootscript).*(Permission denied)",
            "response": "Permissioned denied trying to download BSS bootscript",
        }, {
            "failOnFind": True,
            "query": "Shell>",
            "response": "Dropped into the EFI shell",
        }, {
            "failOnFind": False,
            "query": "Linux version",
            "response": "Did not boot a kernel",
        }, {
            "failOnFind": False,
            "query": "Starting REDS init",
            "response": "Did not start REDS init",
        }, {
            "failOnFind": False,
            "query": "End cray-tokens-reds-finished",
            "response": "Cannot retrieve its token, check networking, istio, and the token service",
        }, {
            "failOnFind": True,
            "query": "POST to .* failed",
            "response": "Cannot talk to REDS, is the pod running?",
        }, {
            "failOnFind": False,
            "query": "Unknown Failure",
            "response": "Failed to discover for unknown reasons, check REDS and HSM logs",
        }
        ]


def checkConsoleLog(nodeList):
    dbgPrint(dbgMed, "checkConsoleLog")
    """ does it exist? is it > 0 size? are there errors? """
    consolesGood = True
    for n in nodeList:
        msg = ""
        file = "console_" + n + ".log"
        fullPath = logDir + "/" + file

        if path.exists(fullPath) == False:
            msg = "Missing, is the name valid?"
        elif path.isfile(fullPath) == False:
            msg = "Not a file"
        elif path.getsize(fullPath) == 0:
            msg = "Empty, may not have powered on, check power status"

        if msg != "":
            printNotHealthy(file)
            printExtraHealth("File status", "Missing, is the name valid?")
            consolesGood = False
            continue

        with open(fullPath) as conP:
            line = conP.readline()
            errorFound = False
            foundMatch = False
            while line and errorFound == False and foundMatch == False:
                for qr in queryAndResponse:
                    m = search(qr["query"], line)
                    if m is not None:
                        if qr["failOnFind"] == True:
                            printNotHealthy(file)
                            printExtraHealth("Status", qr["response"])
                            errorFound = True
                            consolesGood = False
                            break
                        foundMatch = True
                        break
                line = conP.readline()

            if foundMatch == False and errorFound == False:
                printNotHealthy(file)
                printExtraHealth("Status", qr["response"])
                consolesGood = False



    if consolesGood == True:
        printOK("Console files for River compute nodes and UANs")
    else:
        printNotHealthy("Console files for River compute nodes and UANs")

    return 0



def getAuthenticationToken():
    dbgPrint(dbgMed, "getAuthenticationToken")

    URL = "https://api-gw-service-nmn.local/keycloak/realms/shasta/protocol/openid-connect/token"

    kSecret = getK8sClient().read_namespaced_secret("admin-client-auth", "default")
    secret = b64decode(kSecret.data['client-secret']).decode("utf-8")
    dbgPrint(dbgMed, "\tSecret: " + secret)

    DATA = {
            "grant_type": "client_credentials",
            "client_id": "admin-client",
            "client_secret": secret
            }

    try:
        r = requests.post(url = URL, data = DATA)
    except OSError:
        return ""

    result = json.loads(r.text)

    dbgPrint(dbgMed, result['access_token'])
    return result['access_token']


def triageRiverDiscovery():
    dbgPrint(dbgMed, "triageRiverDiscovery")

    checkConfigMaps()

    auth_token = getAuthenticationToken()
    if auth_token == "":
        printNotHealthy("Authorization token")
        printExtraHealth("Token", "Could not obtain, cannot check on the nodes")

    mbfErr = checkForFile(maasBridgeDir, maasBridgeFile)
    if mbfErr == 0 and auth_token != "":
        mNodes = getRiverManagementNodes()

        if len(mNodes) == 0:
            printNotHealthy("Non-compute nodes")
            printExtraHealth("Nodes", "Missing from bridge file")
        else:
            checkForNodeDiscovery(mNodes, auth_token)
    else:
        if mbfErr != 0:
            printNotHealthy("Non-compute nodes")
            printExtraHealth("File", "Missing bridge file")

        if auth_token == "":
            printNotHealthy("Non-compute nodes")
            printExtraHealth("Status", "Unable to check")

    mjfErr = checkForFile(mappingJsonDir, mappingJsonFile)
    if mjfErr == 0 and auth_token != "":
        cNodes = getRiverComputeNodes()

        if len(cNodes) == 0:
            printNotHealthy("Compute nodes")
            printExtraHealth("Nodes", "Missing from mapping file")
        else:
            checkForNodeDiscovery(cNodes, auth_token)

        checkConsoleLog(cNodes)
    else:
        if mbfErr != 0:
            printNotHealthy("Compute nodes")
            printExtraHealth("File", "Missing mapping file")

        if auth_token == "":
            printNotHealthy("Compute nodes")
            printExtraHealth("Status", "Unable to check")

    checkIfNames()


if __name__ == "__main__":
    setDbgLevel(dbgLow)
    exit(triageRiverDiscovery())

