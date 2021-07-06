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

import requests
import re
from requests.auth import HTTPBasicAuth
import urllib3

from utils.debug import dbgPrint, setDbgLevel, dbgMed, dbgHigh
from utils.health import printWarning, printExtraWarning
from utils.health import printError, printExtraError
import config

def makeRedfishCall(action, targPath, reqData=None):
    dbgPrint(dbgMed, "makeRedfishCall %s: %s %s" % (action, targPath, reqData))

    # Until certificates are being used to talk to Redfish endpoints the basic
    # auth method will be used. To do so, SSL verification needs to be turned
    # off  which results in a InsecureRequestWarning. The following line
    # disables only the IsnsecureRequestWarning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    rfUser = config.rfUser
    rfPass = config.rfPass

    if action == "GET":
        getHeaders = {
                'cache-control': 'no-cache',
                }
        r = requests.get(url = targPath, headers = getHeaders,
                auth = HTTPBasicAuth(rfUser, rfPass), verify = False)
    elif action == "POST":
        postHeaders = {
                'cache-control': 'no-cache',
                'Content-Type': 'application/json',
                }
        r = requests.post(url = targPath, headers = postHeaders, data = reqData,
                auth = HTTPBasicAuth(rfUser, rfPass), verify = False)
    elif action == "DELETE":
        deleteHeaders = {
            'cache-control': 'no-cache',
            }
        r = requests.delete(url = targPath, headers = deleteHeaders,
                auth = HTTPBasicAuth(rfUser, rfPass), verify = False)
    else:
        return None, "Redfish Operation", "Bad Request"

    dbgPrint(dbgMed, "makeRedfishCall %s complete" % action)
    dbgPrint(dbgHigh, "makeRedfishCall %s Response: %s" % (action, r.text))

    ret = r.text
    if not ret:
        ret = r.status_code

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "Redfish"
        msg = "Internal Redfish Error"
        ret = None
    elif r.status_code >= 400:
        label = targPath
        msg = "Bad Request (%d)" % r.status_code
        ret = None
    elif r.status_code >= 300:
        label = "Redfish"
        msg = "URI redirection"
        ret = None

    return ret, label, msg

def convertXnameToBMCName(xname):
    # xname could be an IP address or other style of hostname
    bmcName = xname

    m = re.search( # contains nC name OR is sC name OR is cC name
            'x[0-9]+c[0-7]s[0-9]+b[0-9]+$|x[0-9]+c[0-7]r[0-9]+b[0-9]+$|x[0-9]+c[0-7]b[0-9]+$',
            xname)

    if m and m.group(0):
        bmcName = m.group(0)
    else:
        m = re.search( # is chassis name OR is router slot name
                'x[0-9]+c[0-7]$|x[0-9]+c[0-7]r[0-9]+$', xname)
        if m and m.group(0):
            bmcName = m.group(0) + "b0"

    return bmcName

def isGigabyte(path):
    m = re.search('/redfish/v1/Chassis/Self', path)
    if m and m.group(0):
        return True
    return False

def isHPERiver(path):
    m = re.search('/redfish/v1/Chassis/1', path)
    if m and m.group(0):
        return True
    return False

def isHPEMountain(path):
    m = re.search('/redfish/v1/Chassis/Node|/redfish/v1/Chassis/Enclosure', path)
    if m and m.group(0):
        return True
    return False

URI = 0
FIELD = 0
TYPE = 1

def validateField(name, path, field, data, dType):
    dbgPrint(dbgMed, "validateField: " + name + " " + field)
    if field in data:
        fType = type(data[field])
        if fType is not dType:
            printError(name)
            printExtraError(field,
                "Is a " + fType.__name__ + " not a " + dType.__name__)
            return 1
        if fType is dict or fType is str:
            if len(data[field]) == 0:
                printWarning(name)
                printExtraWarning(path + " ." + field, "Zero length or empty")
                return 1
        if fType is int:
            if data[field] == 0:
                printWarning(name)
                printExtraWarning(path + " ." + field, "Is zero")
                return 1
    else:
        printWarning(name)
        printExtraWarning(path + " ." + field, "Missing")
        return 1
    
    return 0