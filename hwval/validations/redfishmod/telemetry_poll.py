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

from utils.debug import dbgPrint, dbgMed, dbgHigh
from utils.health import printOK, printError, printExtraError
from utils.redfish import makeRedfishCall, isGigabyte, isHPEMountain, isHPERiver

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

def telemetryPoll(bmcName):
    dbgPrint(dbgMed, "telemetryPoll")
    hostPath = "https://" + bmcName

    path = hostPath + "/redfish/v1/Chassis"
    payload, label, msg = makeRedfishCall("GET", path)

    if not payload:
        printError("telemetryPoll")
        printExtraError(label, msg)
        return 1

    chassisList = json.loads(payload)

    badResults = 0

    for chassis in chassisList['Members']:
        chassisPath = hostPath + chassis['@odata.id']

        path = chassisPath + "/Power"
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError("telemetryPoll power")
            printExtraError(label, msg)
            return 1

        Power = json.loads(payload)

        path = chassisPath + "/Thermal"
        payload, label, msg = makeRedfishCall("GET", path)

        if not payload:
            printError("telemetryPoll thermal")
            printExtraError(label, msg)
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
                printError("telemetryPoll power")
                printExtraError(bmcName, "AverageConsumedWatts missing")
                badResults += 1

            ret = checkVoltages(Power)
            if ret != 0:
                printError("telemetryPoll power")
                printExtraError(bmcName, "Voltages missing")
                badResults += 1

            ret = checkFans(Thermal)
            if ret != 0:
                printError("telemetryPoll thermal")
                printExtraError(bmcName, "Fans missing")
                badResults += 1

            ret = checkTemps(Thermal)
            if ret != 0:
                printError("telemetryPoll thermal")
                printExtraError(bmcName, "Temperatures missing")
                badResults += 1

        # HPE - Mountain (we don't poll, but check what we can)
        #   /Power
        #       .Voltages[].ReadingVolts
        #   /Thermal
        #       .Temperatures[].ReadingCelsius
        if isHPEMountain(chassis['@odata.id']):
            ret = checkVoltages(Power)
            if ret != 0:
                printError("telemetryPoll power")
                printExtraError(bmcName, "Voltages missing")
                badResults += 1

            ret = checkTemps(Thermal)
            if ret != 0:
                printError("telemetryPoll thermal")
                printExtraError(bmcName, "Temperatures missing")
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
                printError("telemetryPoll power")
                printExtraError(bmcName, "AverageConsumedWatts missing")
                badResults += 1

            ret = checkLineVoltages(Power)
            if ret != 0:
                printError("telemetryPoll power")
                printExtraError(bmcName, "Voltages missing")
                badResults += 1

            ret = checkFans(Thermal)
            if ret != 0:
                printError("telemetryPoll thermal")
                printExtraError(bmcName, "Fans missing")
                badResults += 1

            ret = checkTemps(Thermal)
            if ret != 0:
                printError("telemetryPoll thermal")
                printExtraError(bmcName, "Temperatures missing")
                badResults += 1



    if badResults == 0:
        printOK("telemetryPoll")

    return badResults