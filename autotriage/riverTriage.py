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

queryAndResponse = [
        {"", ""}
        ]

""" {configmap name, string to search for} """
configMaps = [
        {"cray-bss-ipxe-conf", "bss_ipxe.conf"},
        {"cray-capmc-configuration", "config.toml"},
        {"cray-reds-maas-bridge-config", "reds-maas-bridge-datra.json"},
        {"reds-client-urls", "REDS_X86_64"},
        {"reds-init-configmap", "GATEWAY_IP"},
        {"reds-mapping-json", "cray_reds_mapping.json"},
        {"smd-nid-map-json", "node_nid_map.json"}
        ]


def checkForFile(dir, file):
    dbgPrint(dbgMed, "checkForFile " + dir + "/" + file)
    fullPath = dir + "/" + file
    if path.exists(fullPath) == False:
        printNotHealthy(file)
        printExtraHealth("File status", "missing")
        return
    if path.isfile(fullPath) == False:
        printNotHealthy(file)
        printExtraHealth("File status", "not a file")
        return
    if path.getsize(fullPath) == 0:
        printNotHealthy(file)
        printExtraHealth("File status", "empty")
        return
    printOK(file)


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

    for n in nList:
        URL = "https://api-gw-service-nmn.local/apis/smd/hsm/v1/State/Components/" + n
        r = requests.get(url = URL, headers = {"Authorization": "Bearer %s" % auth_token})
        if r.status_code != 200:
            printNotHealthy(n)
            printExtraHealth("Component", "Missing from HSM")

        if getDbgLevel() > dbgMed:
            print("========================================================")
            print(r.url)
            print(r.status_code)
            print(r.text)
            print(r.headers)


def checkIFNames():
    dbgPrint(dbgMed, "checkIFNames")
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
        printExtraHealth("Format", "doesn't match string#/#/#")
    else:
        printOK("REDS mapping ifNames")


def checkConsoleLog():
    dbgPrint(dbgMed, "checkConsoleLog")
    """ does it exist? is it > 0 size? are there errors? """


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

    r = requests.post(url = URL, data = DATA)
    result = json.loads(r.text)

    dbgPrint(dbgMed, result['access_token'])
    return result['access_token']


def triageRiverDiscovery():
    dbgPrint(dbgMed, "triageRiverDiscovery")

    checkForFile(maasBridgeDir, maasBridgeFile)
    checkForFile(mappingJsonDir, mappingJsonFile)

    auth_token = getAuthenticationToken()

    mNodes = getRiverManagementNodes()

    if len(mNodes) == 0:
        printNotHealthy("NCN nodes")
        printExtraHealth("nodes", "missing from bridge file")
    else:
        checkForNodeDiscovery(mNodes, auth_token)

    cNodes = getRiverComputeNodes()

    if len(cNodes) == 0:
        printNotHealthy("Compute nodes")
        printExtraHealth("nodes", "missing from mapping file")
    else:
        checkForNodeDiscovery(cNodes, auth_token)

    checkIFNames()

    checkConsoleLog()
