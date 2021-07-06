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

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
import datetime
from random import randrange

from utils.debug import dbgPrint, dbgMed
from utils.health import printError, printExtraError
from utils.health import printOK
from utils.health import printInfo, printExtraInfo
from utils.redfish import makeRedfishCall
from utils.redfish import isGigabyte, isHPERiver, isHPEMountain

def getIPAddress():
    ipv4Str = os.popen('ip -o -f inet addr show vlan004 2>/dev/null').read()
    if not ipv4Str:
        return ""
    return ipv4Str.split()[3].split("/")[0]

event = threading.Event()
  
class handleRequest(BaseHTTPRequestHandler):
    def do_POST(self):
        global event
        event.set()
  
httpd = None
httpThread = None
  
def startRedfishEventServer():
    dbgPrint(dbgMed, "startRedfishEventServer")
    global httpd
    global httpThread
  
    ipAddr = getIPAddress()
    if not ipAddr:
        printError("eventRedfishEventServer")
        printExtraError("vlan004", "could not determine IP addr")
        return 1

    httpd = HTTPServer((ipAddr, 443), handleRequest)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile="cert/tls.crt",
                                    keyfile="cert/tls.key", server_side=True)
 
    def serve_forever(httpd):
        with httpd:
            httpd.serve_forever()
 
    httpThread = threading.Thread(target=serve_forever, args=(httpd,))
    httpThread.setDaemon(True)
    httpThread.start()
    return 0
  
def eventSubscribe(bmcName):
    dbgPrint(dbgMed, "eventSubscribe")

    ipAddr = getIPAddress()
    if not ipAddr:
        printError("eventSubscribe")
        printExtraError("vlan004", "could not determine IP addr")
        return 1

    path = "https://" + bmcName + "/redfish/v1/EventService"
    dbgPrint(dbgMed, "checkRedfishEventService checking " + path)
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("checkRedfishEventService")
        printExtraError(label, msg)
        return 1

    response = json.loads(payload)

    sub = {
        'Context': "RFSubTest-%s-RFSubTest" % bmcName,
        'Destination': "https://%s/receiver" % ipAddr,
        'Protocol': 'Redfish',
    }

    if response["@odata.type"] < "#EventService.v1_3_0.EventService":
        eventTypes = ["StatusChange"]
        sub['EventTypes'] = eventTypes

    path = "https://%s/redfish/v1/EventService/Subscriptions" % bmcName

    payload, label, msg = makeRedfishCall("POST", path, json.dumps(sub))

    if not payload:
        printError("eventSubscribe")
        printExtraError(label, msg)
        return 1

    printOK("eventSubscribe")

    return 0

def eventTest(bmcName):
    dbgPrint(dbgMed, "eventTest")
    global event

    hostPath = "https://" + bmcName
    path = hostPath + "/redfish/v1/Chassis"
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("telemetryPoll")
        printExtraError(label, msg)
        return 1

    chassisList = json.loads(payload)
    chassis = chassisList['Members'][0]

    testEvent = {}
    path = hostPath + "/redfish/v1/EventService/Actions/EventService.SubmitTestEvent"

    if isGigabyte(chassis['@odata.id']):
        evID = randrange(10000,99999)
        testEvent = {
            "EventTimestamp":       "2020-05-26T23:04:09+02:00",
            "EventId":              evID,
            "OriginOfCondition":    "/redfish/v1/Chassis/Self",
            "MessageId":            "PropertyValueNotInList",
            "MessageArgs":          ["Lit","IndicatorLED"],
            "Severity":             "Warning"
        }
    elif isHPERiver(chassis['@odata.id']):
        testEvent = {
            'EventID':           'Test Event',
            'Severity':          'OK',
            'EventType':         'StatusChange',
            'OriginOfCondition': 'Test',
            'EventTimestamp':    str(datetime.datetime.now()),
            'MessageArgs':       [],
            'Message':           'This is a test event',
            'MessageId':         'TestMsg.v0'
        }
    elif isHPEMountain(chassis['@odata.id']):
        printInfo("eventValidate")
        printExtraInfo("Test Event","Not supported")
        return 1

    if httpd is None:
        startRedfishEventServer()

    payload, label, msg = makeRedfishCall("POST", path, json.dumps(testEvent))

    if not payload:
        printError("eventValidate")
        printExtraError(label, msg)
        return 1

    if event.wait(timeout=30):
        printOK("eventValidate")
        return 0
    else:
        printError("eventValidate")
        printExtraError("event", "timed out waiting for Redfish test event")
        return 1

def eventDelete(bmcName):
    dbgPrint(dbgMed, "eventDelete")

    ipAddr = getIPAddress()
    if not ipAddr:
        printError("eventDelete")
        printExtraError("vlan004", "could not determine IP addr")
        return 1

    path = "https://%s/redfish/v1/EventService/Subscriptions" % bmcName

    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("eventDelete")
        printExtraError(label, msg)
        return 1

    subCollection = json.loads(payload)

    count = 0
    for subEntry in subCollection['Members']:
        path = "https://%s%s" % (bmcName, subEntry['@odata.id'])

        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError("eventDelete")
            printExtraError(label, msg)
            return 1

        sub = json.loads(payload)

        if (sub['Context'] == "RFSubTest-%s-RFSubTest" % bmcName and
            sub['Destination'] == "https://%s/receiver" % ipAddr):
            count += 1

            payload, label, msg = makeRedfishCall("DELETE", path)

            if not payload:
                printError("eventDelete")
                printExtraError(label, msg)
                return 1

    dbgPrint(dbgMed, "%d subscriptions deleted for %s" % (count, bmcName))

    printOK("eventDelete")

    return 0
