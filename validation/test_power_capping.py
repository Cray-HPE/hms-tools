#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2022-2024] Hewlett Packard Enterprise Development LP
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

"""
Check to make sure the power capping for the node can be set and stays set.

Functions:
    determinePowerCapType(object, string) -> int, string
    disablePowerCapping(object, int, string) -> boolean
    enablePowerCapping(object, int, string) -> boolean
    getChassisPath(object) -> string
    getCurrentPowerCap(object, int, string) -> object
    main() -> int
    makeRedfishCall(object, string, string, object) -> string
    setPowerCap(object, int, string, object) -> int

Misc Variables:
    CONTROLS - Olympus style power capping controls
    POWERCTL - Standard power capping controls
    POWERSVC - HPE Apollo 6500 style power capping controls
"""

#pylint: disable=C0103
#pylint: disable=W0603,W0621
#pylint: disable=R0201,R0911,R0912,R0914,R0915

from datetime import datetime

import os
import sys
import argparse
import logging
import json
import requests
import urllib3

VERSION="1.1.0"

my_logger = logging.getLogger()
my_logger.setLevel(logging.DEBUG)
standard_out = logging.StreamHandler(sys.stdout)
standard_out.setLevel(logging.INFO)
my_logger.addHandler(standard_out)
standard_err = logging.StreamHandler(sys.stderr)
standard_err.setLevel(logging.ERROR)
my_logger.addHandler(standard_err)

VERBOSE1 = logging.INFO - 1
VERBOSE2 = logging.INFO - 2
logging.addLevelName(VERBOSE1, "VERBOSE1")
logging.addLevelName(VERBOSE2, "VERBOSE2")

def makeRedfishCall(args, action, targPath, reqData=None):
    """
    Hub to communicating with a Redfish endpoint. Returns a json payload of a
    Redfish response.

    Parameters:
        args (object): Command line arguments.
        action (string): GET, POST, or DELETE
        targPath (string): Redfish URL for HTTP request.
        reqData (object): Payload to send to Redfish endpoint on a POST.

    Returns:
        json_body (string): JSON payload response from Redfish HTTP request
    """

    # Until certificates are being used to talk to Redfish endpoints the basic
    # auth method will be used. To do so, SSL verification needs to be turned
    # off  which results in a InsecureRequestWarning. The following line
    # disables only the IsnsecureRequestWarning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    auth = requests.auth.HTTPBasicAuth(args.user, args.passwd)

    headers = {
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
    }

    if action == "GET":
        r = requests.get(url = targPath, auth = auth, headers = headers,
                verify = False, timeout=30)
    elif action == "POST":
        r = requests.post(url = targPath, auth = auth, headers = headers,
                data = reqData, verify = False, timeout=30)
    elif action == "DELETE":
        r = requests.delete(url = targPath, auth = auth, verify = False, timeout=30)
    elif action == "PATCH":
        # Olympus nodes don't need the etag for the PATCH
        if ".Deep" not in targPath:
            rsp = requests.get(url = targPath, auth = auth, headers = headers,
                    verify = False, timeout=30)

            if rsp.status_code >= 300:
                my_logger.warning("Redfish call to get power structure failed for %s.", targPath)
                return None

            power = json.loads(rsp.text)
            headers['If-Match'] = power['@odata.etag']

        r = requests.patch(url = targPath, auth = auth, headers = headers,
                data = reqData, verify = False, timeout=30)
    else:
        return None

    json_body = r.text

    if not json_body:
        json_body = r.status_code

    if r.status_code >= 300:
        my_logger.warning("Redfish call returned %d.", r.status_code)
        if "LicenseKeyRequired" in r.text:
            my_logger.error("FAIL: License key required for power capping.")
        json_body = None

    return json_body


def getChassisPath(args):
    """
    Select the first available node from the Chassis to perform power capping on.

    Parameters:
        args (object): Command line arguments.

    Returns:
        path (string): URI of a chassis member to perform power capping on.
    """
    my_logger.info("Finding node to use for test.")
    path = f"https://{args.bmc}/redfish/v1/Chassis"
    rsp = makeRedfishCall(args, "GET", path)
    if not rsp:
        my_logger.warning("Redfish call to get Chassis failed.")
        return None

    chassisCollection = json.loads(rsp)

    if "Members" in chassisCollection and len(chassisCollection['Members']) > 0:
        for member in chassisCollection['Members']:
            if ("Mezz" not in member['@odata.id'] and
                    "Enclosure" not in member['@odata.id']):
                path = member['@odata.id']
                my_logger.info("Using node %s.", path)
                return path

    return None

CONTROLS = 0
POWERCTL = 1
POWERSVC = 2

def determinePowerCapType(args, path):
    """
    Check to see which type of power capping the target is using.
            Chassis/{id}/Control                Olympus (Deep PATCH)
            Chassis/{id}/Power .PowerControl    GB, HPE DL
            Chassis/{id}/Power .Oem.Hpe         HPE Apollo 6500

    Parameters:
        args (object): Command line arguments.
        path (string): Path to valid chassis entry.

    Returns:
        Type (int): Which power cap payload type to use.
        path (string): Power capping URI.
    """
    my_logger.info("Determining which power cap scheme and URI to use.")
    path = f"https://{args.bmc}{path}"

    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.warning("Redfish call to get chassis information for %s failed.", path)
        return None, None

    chassis = json.loads(rsp)

    if "Controls" in chassis:
        path = f"https://{args.bmc}{chassis['Controls']['@odata.id']}"
        rsp = makeRedfishCall(args, "GET", path)

        if not rsp:
            my_logger.warning("Redfish call to get chassis controls information for %s failed.",
                path)
            return None, None

        controlsCollection = json.loads(rsp)

        if "Members" in controlsCollection and len(controlsCollection['Members']) > 0:
            for member in controlsCollection['Members']:
                if "NodePowerLimit" in member['@odata.id']:
                    my_logger.info("Using Chassis Controls for power capping.")
                    return CONTROLS, member['@odata.id']

    path = f"https://{args.bmc}{chassis['Power']['@odata.id']}"

    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.info("Redfish call to get chassis power information for %s failed.", path)
        return None, None

    power = json.loads(rsp)

    if ("Oem" in power and
            "Hpe" in power['Oem'] and
            "Links" in power['Oem']['Hpe'] and
            "PowerLimit" in power['Oem']['Hpe']['Links']):
        path = power['Oem']['Hpe']['Links']['PowerLimit']['@odata.id']
        rsp = makeRedfishCall(args, "GET", path)

        if not rsp:
            my_logger.warning("Redfish call to get power limit information for %s failed.", path)
            return None, None

        powerLimit = json.loads(rsp)

        plActions = powerLimit['Actions']
        configLimit = plActions['#HpeServerAccPowerLimit.ConfigurePowerLimit']

        my_logger.info("Using HPE ServerAccPowerLimit for power capping.")
        return POWERSVC, configLimit['target']

    my_logger.info("Using Chassis Power PowerControl for power capping.")
    return POWERCTL, chassis['Power']['@odata.id']


def enablePowerCapping(args, pcType, pcURI):
    """
    Make the proper calls to enable power capping. Olympus node power capping
    is enabled in the same call the power cap settings are done.

    Parameters:
        args (object): Command line arguments.
        pcType (int): Payload type.
        pcURI (string): Chassis URI.

    Returns:
        enabled (bool): True if power capping was enabled.
    """
    if pcType == CONTROLS:
        my_logger.info("Olympus power capping will be enabled at power capping time.")
        return True

    if "Self" in pcURI:
        my_logger.info("Trying to enable Gigabyte power capping.")
        path = f"https://{args.bmc}/redfish/v1/Chassis/Self/Power/Actions/LimitTrigger"

        enablePC = {
                'PowerLimitTrigger': 'Activate',
                }

        rsp = makeRedfishCall(args, "POST", path, json.dumps(enablePC))

        if rsp is None:
            my_logger.warning("Failed to enable power capping for Gigabyte.")
            return False

        my_logger.info("Power capping for Gigabyte was enabled.")
        return True


    my_logger.info("Trying to enable HPE power capping.")
    enablePC = {}
    path = None
    if pcType == POWERCTL:
        sysID = pcURI.split('/')[-2] # pylint: disable=unused-variable

        path = f"https://{args.bmc}/redfish/v1/Systems/{sysID}/BIOS/settings"

        dynamicPC = {
                'DynamicPowerCapping': 'Enabled',
                }
        enablePC = {
                'Attributes': dynamicPC,
                }

    if pcType == POWERSVC:
        url = '/'.join(pcURI.split('/')[:-3]) # pylint: disable=unused-variable
        path = f"https://{args.bmc}{url}"

        enablePC = {
                'PowerRegulationEnabled': True,
                'PowerRegulatorMode': 'UserConfig',
                }

    rsp = makeRedfishCall(args, "PATCH", path, json.dumps(enablePC))

    if rsp is None:
        my_logger.warning("Failed to enable power capping for HPE.")
        return False

    my_logger.info("Power capping for HPE was enabled.")
    return True


def disablePowerCapping(args, pcType, pcURI):
    """
    Make the proper calls to disable power capping.

    Parameters:
        args (object): Command line arguments.
        pcType (int): Payload type.
        pcURI (string): Chassis URI.

    Returns:
        disabled (bool): True if power capping was disabled.
    """
    if pcType == CONTROLS:
        my_logger.info("Trying to disable Olympus power capping.")
        members = []
        nodePowerLimit = {
                '@odata.id': pcURI,
                'ControlMode': 'Disabled',
                }

        members.append(nodePowerLimit)

        payload = {
                'Members': members
                }

        url = '/'.join(pcURI.split('/')[:-1]) # pylint: disable=unused-variable
        path = f"https://{args.bmc}{url}.Deep"

        rsp = makeRedfishCall(args, "PATCH", path, json.dumps(payload))

        if rsp is None:
            my_logger.warning("Failed to disable power capping for Olympus.")
            return False

        my_logger.info("Power capping for Olympus was disabled.")
        return True

    if "Self" in pcURI:
        my_logger.info("Trying to disable Gigabyte power capping.")
        path = f"https://{args.bmc}/redfish/v1/Chassis/Self/Power/Actions/LimitTrigger"

        disablePC = {
                'PowerLimitTrigger': 'Deactivate',
                }

        rsp = makeRedfishCall(args, "POST", path, json.dumps(disablePC))

        if rsp is None:
            my_logger.warning("Failed to disable power capping for Gigabyte.")
            return False

        my_logger.info("Power capping for Gigabyte was disabled.")
        return True


    my_logger.info("Trying to disable HPE power capping.")
    disablePC = {}
    path = None
    if pcType == POWERCTL:
        sysID = pcURI.split('/')[4] # pylint: disable=unused-variable
        path = f"https://{args.bmc}/redfish/v1/Systems/{sysID}/BIOS/settings"

        dynamicPC = {
                'DynamicPowerCapping': 'Disabled',
                }
        disablePC = {
                'Attributes': dynamicPC,
                }

    if pcType == POWERSVC:
        url = '/'.join(pcURI.split('/')[:-3]) # pylint: disable=unused-variable
        path = f"https://{args.bmc}{url}"

        disablePC = {
                'PowerRegulationEnabled': False,
                'PowerRegulatorMode': 'UserConfig',
                }

    rsp = makeRedfishCall(args, "PATCH", path, json.dumps(disablePC))

    if rsp is None:
        my_logger.warning("Failed to disable power capping for HPE.")
        return False

    my_logger.info("Power capping for HPE was disabled.")
    return True


def getCurrentPowerCap(args, pcType, pcURI): # pylint: disable=unused-argument
    """
    Query the Redfish to find the Min, Max, and current power cap settings.

    Parameters:
        args (object): Command line arguments.
        pcType (int): Payload type.
        pcURI (string): Power capping URI.

    Returns:
        pcSettings (object): Power cap min, max, and current value.
    """
    my_logger.info("Calling Redfish to get the current power cap settings.")
    path = f"https://{args.bmc}{pcURI}"

    rsp = makeRedfishCall(args, "GET", path)

    if rsp is None:
        my_logger.warning("Failed to get power capping information from Redfish.")
        return None

    rfPC = json.loads(rsp)

    pcSettings = {}
    if pcType == CONTROLS:
        pcSettings['min'] = rfPC['SettingRangeMin']
        pcSettings['max'] = rfPC['SettingRangeMax']
        pcSettings['current'] = rfPC['SetPoint']

    if pcType == POWERCTL:
        if "Oem" in rfPC['PowerControl'][0]:
            if "Vendor" in rfPC['PowerControl'][0]['Oem']:
                pcSettings['min'] = rfPC['PowerControl'][0]['Oem']['Vendor']['PowerLimit']['Min']
                pcSettings['max'] = rfPC['PowerControl'][0]['Oem']['Vendor']['PowerLimit']['Max']
                pcSettings['current'] = rfPC['PowerControl'][0]['PowerLimit']['LimitInWatts']
                return pcSettings

        pcSettings['min'] = rfPC['PowerControl'][0]['PowerMetrics']['MinConsumedWatts']
        pcSettings['max'] = rfPC['PowerControl'][0]['PowerCapacityWatts']
        pcSettings['current'] = rfPC['PowerControl'][0]['PowerLimit']['LimitInWatts']

    if pcType == POWERSVC:
        pcSettings['min'] = rfPC['PowerLimitRanges'][0]['MinimumPowerLimit']
        pcSettings['max'] = rfPC['PowerLimitRanges'][0]['MaximumPowerLimit']
        pcSettings['current'] = rfPC['PowerLimits'][0]['PowerLimitInWatts']

    return pcSettings


def setPowerCap(args, pcType, pcURI, pcSettings):
    """
    Set the power cap limit to the supplied value.

    Parameters:
        args (object): Command line arguments.
        pcType (int): Payload type.
        pcURI (string): Power capping URI.
        pcSettings (object): Power cap min, max, and current value.

    Returns:
        success (int): 0 for success, 1 for failure
    """
    value = pcSettings['value']
    my_logger.info("Setting the power cap of %s to %d.", pcURI, value)
    if value < pcSettings['min'] or value > pcSettings['max']:
        my_logger.warning("Power capping value out of range.")
        return 1

    path = f"https://{args.bmc}{pcURI}"
    payload = None
    operation = "PATCH"

    if pcType == CONTROLS:
        members = []
        nodePowerLimit = {
                '@odata.id': pcURI,
                'ControlMode': 'Automatic',
                'SetPoint': value,
                }

        members.append(nodePowerLimit)

        payload = {
                'Members': members
                }

        url = '/'.join(pcURI.split('/')[:-1]) # pylint: disable=unused-variable
        path = f"https://{args.bmc}{url}.Deep"

    if pcType == POWERSVC:
        operation = "POST"
        powerLimits = []

        limit = {
                'PowerLimitInWatts': value,
                'ZoneNumber': 0,
                }

        powerLimits.append(limit)

        payload = {
                'PowerLimits': powerLimits,
                }

    if pcType == POWERCTL:
        powerControl = []
        powerLimit = {
                'LimitInWatts': value,
                }

        control = {
                'PowerLimit': powerLimit
                }

        powerControl.append(control)

        payload = {
            'PowerControl': powerControl,
            }

    rsp = makeRedfishCall(args, operation, path, json.dumps(payload))

    if rsp is None:
        my_logger.warning("Redfish call to set power cap failed for %s.", path)
        return 1


    return 0


def main():
    """Main program"""
    parser = argparse.ArgumentParser(description='Power Cap Testing.')
    parser.add_argument('-b', '--bmc', help='BMC name or IP.')
    parser.add_argument('-u', '--user', help='Redfish user name.')
    parser.add_argument('-p', '--passwd', help='Redfish password.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbosity of tool in stdout')
    parser.add_argument('-V', '--version', action="store_true",
            help='Print the script version information and exit.')
    parser.add_argument('-l', '--logdir', default='./logs',
            help='Directory for log files')
    args = parser.parse_args()

    # set logging file
    standard_out.setLevel(logging.INFO - args.verbose if args.verbose < 3 else logging.DEBUG)

    logpath = args.logdir

    if not os.path.isdir(logpath):
        os.makedirs(logpath)

    fmt = logging.Formatter('%(levelname)s - %(message)s')
    file_handler = logging.FileHandler(datetime.strftime(datetime.now(),
        os.path.join(logpath, "PowerCapTest_%m_%d_%Y_%H%M%S.txt")))
    file_handler.setLevel(min(logging.INFO if not args.verbose else logging.DEBUG,
        standard_out.level))
    file_handler.setFormatter(fmt)
    my_logger.addHandler(file_handler)

    if args.version is True:
        my_logger.info("%s: %s", __file__, VERSION)
        return 0

    path = getChassisPath(args)

    if path is None:
        my_logger.error("FAIL: Unable to determine which chassis entry to use for power capping.")
        return 1

    pcType, pcURI = determinePowerCapType(args, path)

    if pcType is None:
        my_logger.error("FAIL: Unable to determine which type of power capping to use.")
        return 1

    enabled = enablePowerCapping(args, pcType, pcURI)

    if not enabled:
        my_logger.error("FAIL: Could not enable power capping.")
        return 1

    pcSettings = getCurrentPowerCap(args, pcType, pcURI)

    print(pcSettings)
    if pcSettings is None:
        my_logger.error("FAIL: Unable to determine current power cap settings.")
        return 1

    newSettings = pcSettings
    newSettings['value'] = pcSettings['max'] - 100
    ret = setPowerCap(args, pcType, pcURI, newSettings)

    if ret == 1:
        my_logger.error("FAIL: Could not set power cap.")
        return 1

    curSettings = getCurrentPowerCap(args, pcType, pcURI)

    if curSettings is None:
        my_logger.error("FAIL: Unable to determine new power cap settings.")
        return 1

    my_logger.info("\tMin: %d expected %d", curSettings['min'], pcSettings['min'])
    my_logger.info("\tMax: %d expected %d", curSettings['max'], pcSettings['max'])
    my_logger.info("\tCurrent: %d expected %d", curSettings['current'], newSettings['value'])

    if (curSettings['min'] != newSettings['min'] or
            curSettings['max'] != newSettings['max'] or
            curSettings['current'] != newSettings['value']):
        my_logger.error("FAIL: Currently set power cap settings does not match expected.")
        return 1

    my_logger.info("PASS: Power capping succeeded.")

    pcSettings['value'] = pcSettings['max']
    ret = setPowerCap(args, pcType, pcURI, pcSettings)

    if ret == 1:
        my_logger.error("FAIL: Could not reset power cap.")
        return 1

    disabled = disablePowerCapping(args, pcType, pcURI)

    if not disabled:
        my_logger.error("FAIL: Could not disable power capping.")
        return 1

    return 0


if __name__ == "__main__":
    result = main()
    sys.exit(result)
