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

import sys
import requests
import re
import json
from requests.auth import HTTPBasicAuth
import urllib3
import pprint

from debug import dbgPrint, setDbgLevel, dbgLow, dbgMed, dbgMed, dbgHigh
from health import printExtraHealth, printNotHealthy, printOK

rfUser = None
rfPass = None

def makeRedfishCall(action, targPath, reqData=None):
    dbgPrint(dbgMed, "makeRedfishCall %s: %s %s" % (action, targPath, reqData))

    # Until certificates are being used to talk to Redfish endpoints the basic
    # auth method will be used. To do so, SSL verification needs to be turned
    # off  which results in a InsecureRequestWarning. The following line
    # disables only the IsnsecureRequestWarning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    else:
        return None, "Redfish Operation", "Bad Request"

    dbgPrint(dbgMed, "makeRedfishCall %s complete" % action)
    dbgPrint(dbgHigh, "makeRedfishCall %s Response: %s" % (action, r.text))

    ret = r.text
    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "Redfish"
        msg = "Internal Redfish Error"
        ret = None
    elif r.status_code >= 400:
        label = targPath
        msg = "Bad Request"
        ret = None
    elif r.status_code >= 300:
        label = "Redfish"
        msg = "URI redirection"
        ret = None

    return ret, label, msg

def convertXnameToBMCName(xname):
    bmcName = None

    m = re.search( # contains nC name OR is sC name OR is cC name
            'x[0-9]+c[0-7]s[0-9]+b0|x[0-9]+c[0-7]r[0-9]+b0$|x[0-9]+c[0-7]b0$',
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

def checkAvgConsumedWatts(power):
    dbgPrint(dbgMed, "checkAvgConsumedWatts")
    if ('PowerMetrics' in power['PowerControl'][0] and
        ('Name' in power['PowerControl'][0] or 'Name' in power) and
        ('PhysicalContext' in power['PowerControl'][0] or
         'Hpe' in power['Oem'])):
        if 'AverageConsumedWatts' in power['PowerControl'][0]['PowerMetrics']:
            return 0
    dbgPrint(dbgMed, power)
    return 1

def checkVoltages(power):
    dbgPrint(dbgMed, "checkVoltages")
    dbgPrint(dbgHigh, power)
    for voltage in power['Voltages']:
        if ('ReadingVolts' not in voltage or
            'Name' not in voltage or
            'PhysicalContext' not in voltage):
                if 'Name' in voltage:
                    if voltage['Name']:
                        dbgPrint(dbgMed, voltage)
                        return 1
    return 0

def checkLineVoltages(power):
    dbgPrint(dbgMed, "checkLineVoltages")
    dbgPrint(dbgHigh, power)
    for psu in power['PowerSupplies']:
        if ('LineInputVoltage' not in psu or
            'Name' not in psu):
                if 'Name' in psu:
                    if psu['Name']:
                        dbgPrint(dbgMed, psu)
                        return 1
    return 0

def checkFans(thermal):
    dbgPrint(dbgMed, "checkFans")
    dbgPrint(dbgHigh, thermal)
    for fan in thermal['Fans']:
        if ('Reading' not in fan or
            'Name' not in fan or
            ('PhysicalContext' not in fan and
            'Hpe' not in fan['Oem'])):
                dbgPrint(dbgMed, fan)
                return 1
    return 0

def checkTemps(thermal):
    dbgPrint(dbgMed, "checkTemps")
    dbgPrint(dbgHigh, thermal)
    for temp in thermal['Temperatures']:
        if ('ReadingCelsius' not in temp or
            'Name' not in temp or
            'PhysicalContext' not in temp):
            if 'Status' in temp:
                if temp['Status']['State'] != "Absent":
                    dbgPrint(dbgMed, temp)
                    return 1
    return 0

def eventSubscribe(bmcName):
    return 1

def eventTest(bmcName):
    return 1

def eventDelete(bmcName):
    return 1

def telemetryPoll(bmcName):
    dbgPrint(dbgMed, "telemetryPoll")
    hostPath = "https://" + bmcName

    path = hostPath + "/redfish/v1/Chassis"
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printNotHealthy("telemetryPoll")
        printExtraHealth(label, msg)
        return 1

    chassisList = json.loads(payload)

    badResults = 0

    for chassis in chassisList['Members']:
        chassisPath = hostPath + chassis['@odata.id']

        path = chassisPath + "/Power"
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printNotHealthy("telemetryPoll power")
            printExtraHealth(label, msg)
            return 1

        Power = json.loads(payload)

        path = chassisPath + "/Thermal"
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printNotHealthy("telemetryPoll thermal")
            printExtraHealth(label, msg)
            return 1

        Thermal = json.loads(payload)

        # Gigabyte
        #   /Power
        #       .PowerControl.PowerMetrics.AverageConsumedWatts
        #       .Voltages[].ReadingVolts
        #   /Thermal
        #       .Fans[].Reading
        #       .Temperatures[].ReadingCelsius
        if isGigabyte(chassis['@odata.id']):
            ret = checkAvgConsumedWatts(Power)
            if ret != 0:
                printNotHealthy("telemetryPoll power")
                printExtraHealth(bmcName, "AverageConsumedWatts missing")
                badResults += 1

            ret = checkVoltages(Power)
            if ret != 0:
                printNotHealthy("telemetryPoll power")
                printExtraHealth(bmcName, "Voltages missing")
                badResults += 1

            ret = checkFans(Thermal)
            if ret != 0:
                printNotHealthy("telemetryPoll thermal")
                printExtraHealth(bmcName, "Fans missing")
                badResults += 1

            ret = checkTemps(Thermal)
            if ret != 0:
                printNotHealthy("telemetryPoll thermal")
                printExtraHealth(bmcName, "Temperatures missing")
                badResults += 1

        # HPE - Mountain (we don't poll, but check what we can)
        #   /Power
        #       .Voltages[].ReadingVolts
        #   /Thermal
        #       .Temperatures[].ReadingCelsius
        if isHPEMountain(chassis['@odata.id']):
            ret = checkVoltages(Power)
            if ret != 0:
                printNotHealthy("telemetryPoll power")
                printExtraHealth(bmcName, "Voltages missing")
                badResults += 1

            ret = checkTemps(Thermal)
            if ret != 0:
                printNotHealthy("telemetryPoll thermal")
                printExtraHealth(bmcName, "Temperatures missing")
                badResults += 1

        # HPE - River
        #   /Power
        #       .PowerControl.PowerMetrics.AverageConsumedWatts
        #       .PowerSupplies[].LineInputVoltage
        #   /Thermal
        #       .Fans[].Reading
        #       .Temperatures[].ReadingCelsius
        if isHPERiver(chassis['@odata.id']):
            ret = checkAvgConsumedWatts(Power)
            if ret != 0:
                printNotHealthy("telemetryPoll power")
                printExtraHealth(bmcName, "AverageConsumedWatts missing")
                badResults += 1

            ret = checkLineVoltages(Power)
            if ret != 0:
                printNotHealthy("telemetryPoll power")
                printExtraHealth(bmcName, "Voltages missing")
                badResults += 1

            ret = checkFans(Thermal)
            if ret != 0:
                printNotHealthy("telemetryPoll thermal")
                printExtraHealth(bmcName, "Fans missing")
                badResults += 1

            ret = checkTemps(Thermal)
            if ret != 0:
                printNotHealthy("telemetryPoll thermal")
                printExtraHealth(bmcName, "Temperatures missing")
                badResults += 1



    if badResults == 0:
        printOK("telemetryPoll")

    return badResults

validations = [
    eventSubscribe,
    eventTest,
    eventDelete,
    telemetryPoll
        ]

def redfishValidation(xname, tests=None, list=False, args=None):
    dbgPrint(dbgMed, "redfishValidation")

    if list:
        return validations

    if not args:
        printNotHealthy("redfishValidation")
        printExtraHealth(xname, "Missing arguments")
        return 1

    if not args.user or not args.passwd:
        printNotHealthy("redfishValidation")
        printExtraHealth(xname, "Missing credentials")
        return 1

    bmcName = convertXnameToBMCName(xname)

    if not bmcName:
        printNotHealthy("redfishValidation")
        printExtraHealth(xname, "Could not determine BMC name")
        return 1

    global rfUser
    global rfPass
    rfUser = args.user
    rfPass = args.passwd

    failures = 0
    if tests:
        for t in tests:
            for test in validations:
                if t == test.__name__:
                    dbgPrint(dbgMed, "Calling: redfishValidation:%s" % test.__name__)
                    ret = test(bmcName)
                    failures = failures + ret
    else:
        for test in validations:
            dbgPrint(dbgMed, "Calling: redfishValidation:%s" % test.__name__)
            ret = test(bmcName)
            failures = failures + ret

    return failures

if __name__ == "__main__":
    setDbgLevel(dbgLow)
    dbgPrint(dbgLow, "Calling: redfishValidation(%s, %s, %s)" % (sys.argv[1],
        sys.argv[2], sys.argv[3]))
    exit(redfishValidation(sys.argv[1], sys.argv[2], sys.argv[3]))

