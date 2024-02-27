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
Turn power to a node On and Off, validating events are properly flowing and the
node makes it to the target states.

If node is Off, turns node On, checks state, turns node Off, checks state.
If node is On, turns node Off, checks state, turns node On, checks state.
Verifies at least 1 Redfish On event and 1 Redfish Off event.

Classes:
    handleRequest

Functions:
    determineScheme(object) -> string
    eventDelete(object) -> int
    eventSubscribe(object, string) -> int
    forceNodeOff(object, string)
    getFirstNodePath(object) -> string
    getPowerState(object, string) -> string
    main() -> int
    makeRedfishCall(object, string, string, object) -> string
    startRedfishEventServer(object)
    turnNodeOff(object, string)
    turnNodeOn(object, string)
    waitForState(object, string, string) -> string

Misc Variables:
    event
    httpd
    httpThread
"""

# pylint: disable=invalid-name
# pylint: disable=global-statement
# pylint: disable=global-variable-not-assigned
# pylint: disable=deprecated-method

from datetime import datetime

import os
import sys
import argparse
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
import time
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

event = threading.Event()

class handleRequest(BaseHTTPRequestHandler):
    """Simple HTTP server to receive streaming telemetry."""
    def do_POST(self):
        """Handler for POSTs from Redfish endpoint."""
        global event
        event.set()


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
                verify = False, timeout = 30)
    elif action == "POST":
        r = requests.post(url = targPath, auth = auth, headers = headers,
                data = reqData, verify = False, timeout = 30)
    elif action == "DELETE":
        r = requests.delete(url = targPath, auth = auth, verify = False, timeout = 30)
    else:
        return None

    json_body = r.text

    if not json_body:
        json_body = r.status_code

    if r.status_code >= 300:
        my_logger.error("Redfish call returned %d.", r.status_code)
        my_logger.error("Redfish %s for %s returned %d.", action, targPath, r.status_code)
        json_body = None

    return json_body


def getFirstNodePath(args):
    """
    Select the first available node to perform power operations on.

    Parameters:
        args (object): Command line arguments.

    Returns:
        path (string): URI of the first node found in Systems collection
    """
    my_logger.info("Finding node to use for test.")
    path = f"https://{args.bmc}/redfish/v1/Systems"
    rsp = makeRedfishCall(args, "GET", path)
    if not rsp:
        my_logger.warning("Redfish call to get Systems failed.")
        return None

    sysCollection = json.loads(rsp)

    nPath = None
    if "Members" in sysCollection and len(sysCollection['Members']) > 0:
        nPath = sysCollection['Members'][0]['@odata.id']

    return nPath

def turnNodeOff(args, nPath):
    """
    Send a graceful shutdown request to the target.

    Parameters:
        args (object): Command line arguments.
        nPath (string): Systems URI for target node.
    """
    my_logger.info("Turning node at %s Off.", nPath)
    path = f"https://{args.bmc}{nPath}"
    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.warning("Redfish call to get computer system information for %s failed.", nPath)
        return

    compSystem = json.loads(rsp)
    compSysReset = compSystem['Actions']['#ComputerSystem.Reset']

    aVals = None
    if "ResetType@Redfish.AllowableValues" in compSysReset:
        aVals = compSysReset['ResetType@Redfish.AllowableValues']
    elif "@Redfish.ActionInfo" in compSysReset:
        aiPath = compSysReset['@Redfish.ActionInfo']
        path = f"https://{args.bmc}{aiPath}"
        rsp = makeRedfishCall(args, "GET", path)

        if not rsp:
            my_logger.warning("Redfish call to get ActionInfo for %s failed.", aiPath)
            return

        resetActionInfo = json.loads(rsp)
        for param in resetActionInfo['Parameters']:
            if param['Name'] == "ResetType":
                aVals = param['AllowableValues']

    resetType = None
    for val in aVals:
        if val == "GracefulShutdown":
            resetType = "GracefulShutdown"

    if resetType is None:
        for val in aVals:
            if val == "Off":
                resetType = "Off"

    if resetType is None:
        my_logger.warning("Could not determine ResetType for power Off.")
        return

    reset = {
            'ResetType': resetType,
            }

    path = f"https://{args.bmc}{compSysReset['target']}"
    rsp = makeRedfishCall(args, "POST", path, json.dumps(reset))

    if not rsp:
        my_logger.warning("Redfish call to perform Off power action failed.")

def forceNodeOff(args, nPath):
    """
    Send a force Off request to the target.

    Parameters:
        args (object): Command line arguments.
        nPath (string): Systems URI for target node.
    """
    my_logger.info("Forcing node at %s Off.", nPath)
    path = f"https://{args.bmc}{nPath}"
    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.warning("Redfish call to get computer system information for %s failed.", nPath)
        return

    compSystem = json.loads(rsp)
    compSysReset = compSystem['Actions']['#ComputerSystem.Reset']

    reset = {
            'ResetType': 'ForceOff',
            }

    path = f"https://{args.bmc}{compSysReset['target']}"
    rsp = makeRedfishCall(args, "POST", path, json.dumps(reset))

    if not rsp:
        my_logger.warning("Redfish call to perform force Off power action failed.")


def turnNodeOn(args, nPath):
    """
    Send a power On request to the target.

    Parameters:
        args (object): Command line arguments.
        nPath (string): Systems URI for target node.
    """
    my_logger.info("Turning node at %s On.", nPath)
    path = f"https://{args.bmc}{nPath}"
    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.warning("Redfish call to get computer system information for %s failed.", nPath)
        return

    compSystem = json.loads(rsp)
    compSysReset = compSystem['Actions']['#ComputerSystem.Reset']

    reset = {
            'ResetType': 'On',
            }

    path = f"https://{args.bmc}{compSysReset['target']}"
    rsp = makeRedfishCall(args, "POST", path, json.dumps(reset))

    if not rsp:
        my_logger.warning("Redfish call to perform On power action failed.")


def getPowerState(args, nPath):
    """
    Query the power state of the target.

    Parameters:
        args (object): Command line arguments.
        nPath (string): Systems URI for target node.

    Returns:
        state (string): Power state of the node.
    """
    path = f"https://{args.bmc}{nPath}"
    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.warning("Redfish call to get computer system information for %s failed.", nPath)
        return None

    compSystem = json.loads(rsp)

    return compSystem['PowerState']


def waitForState(args, nPath, state):
    """
    Wait for target node to transition to expected state.

    Parameters:
        args (object): Command line arguments.
        nPath (string): Systems URI for target node.
        state (string): Power state of the node to wait for.

    Returns:
        state (string): Last power state queried from the node.
    """
    nstate = getPowerState(args, nPath)

    count = 0
    while (nstate != state and count < 30):
        time.sleep(10)
        nstate = getPowerState(args, nPath)
        count += 1

    return nstate

def startRedfishEventServer(args, scheme):
    """
    Start an HTTP server to receive streaming telemetry.

    Parameters:
        args (object): Command line arguments.
        scheme (string): Secure or unsecure http protocol.
    """
    my_logger.info("Starting %s Redfish event server.", scheme)
    my_logger.info("ip %s port %s", args.ip, args.port)
    httpd = HTTPServer((args.ip, int(args.port)), handleRequest)
    if scheme == "https":
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile="cert/tls.crt",
                keyfile="cert/tls.key", server_side=True)

    def serve_forever(httpd):
        with httpd:
            httpd.serve_forever()

    httpThread = threading.Thread(target=serve_forever, args=(httpd,))
    httpThread.daemon = True
    httpThread.start()


def eventSubscribe(args, scheme):
    """
    Sends a subscribe request to the Redfish endpoint.

    Parameters:
        args (object): Command line arguments.
        scheme (string): Secure or unsecure http protocol.

    Returns:
        result (int): 0 for success, 1 for failure
    """
    my_logger.info("Subscribing to Redfish events with %s.", scheme)
    eventTypes = ["StatusChange", "Alert", "ResourceUpdated", "ResourceAdded", "ResourceRemoved"]
    destination = f"{scheme}://{args.ip}:{args.port}/{args.bmc}"

    sub = {
        'Context': f"PowerTest-{args.bmc}-PowerTest",
        'Destination': destination,
        'Protocol': 'Redfish',
        'EventTypes': eventTypes,
    }

    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = makeRedfishCall(args, "POST", path, json.dumps(sub))

    if not rsp:
        my_logger.warning("Redfish call to create subscription failed.")
        return 1

    return 0


def eventDelete(args):
    """
    Finds and deletes the subscription that this test created.

    Parameters:
        args (object): Command line arguments.

    Returns:
        result (int): 0 for success, 1 for failure
    """
    my_logger.info("Deleting subscriptions created by this test.")
    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.warning("Redfish call to list subscriptions failed.")
        return 1

    subCollection = json.loads(rsp)

    count = 0
    for subEntry in subCollection['Members']:
        entry = subEntry['@odata.id']
        path = f"https://{args.bmc}{entry}"

        rsp = makeRedfishCall(args, "GET", path)

        if not rsp:
            my_logger.warning("Redfish call to get subscription entry %s failed.", entry)
            return 1

        sub = json.loads(rsp)

        if (sub['Context'] == f"PowerTest-{args.bmc}-PowerTest" and
                sub['Destination'] == f"http://{args.ip}:{args.port}/{args.bmc}"):
            count += 1

            rsp = makeRedfishCall(args, "DELETE", path)

            if not rsp:
                my_logger.warning("Redfish call to delete subscription entry %s failed.", entry)
                return 1

    return 0


def determineScheme(args):
    """
    Check if we are talking to an iLO device. If we are, we need to use https
    instead of http for the server.

    Parameters:
        args (object): Command line arguments.

    Returns:
        scheme (string): Secure or unsecure http protocol.
    """
    my_logger.info("Determining which http scheme to use.")
    path = f"https://{args.bmc}/redfish/v1/Registries/iLO"

    rsp = makeRedfishCall(args, "GET", path)

    if rsp:
        return "https"

    path = f"https://{args.bmc}/redfish/v1/Registries/OpenBMC"

    rsp = makeRedfishCall(args, "GET", path)

    if rsp:
        return "https"

    return "http"

def main(argslist=None):
    """Main program"""
    parser = argparse.ArgumentParser(description='Echo server.')
    parser.add_argument('-i', '--ip', help='IP address to listen on.')
    parser.add_argument('-r', '--port', help='Port to listen on.')
    parser.add_argument('-b', '--bmc', help='BMC name or IP.')
    parser.add_argument('-u', '--user', help='Redfish user name.')
    parser.add_argument('-p', '--passwd', help='Redfish password.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbosity of tool in stdout')
    parser.add_argument('-V', '--version', action="store_true",
            help='Print the script version information and exit.')
    parser.add_argument('-l', '--logdir', default='./logs',
            help='Directory for log files')
    args = parser.parse_args(argslist)

    # set logging file
    standard_out.setLevel(logging.INFO - args.verbose if args.verbose < 3 else logging.DEBUG)

    logpath = args.logdir

    if not os.path.isdir(logpath):
        os.makedirs(logpath)

    fmt = logging.Formatter('%(levelname)s - %(message)s')
    file_handler = logging.FileHandler(datetime.strftime(datetime.now(),
        os.path.join(logpath, "PoweControlTest_%m_%d_%Y_%H%M%S.txt")))
    file_handler.setLevel(min(logging.INFO if not args.verbose else
        logging.DEBUG, standard_out.level))
    file_handler.setFormatter(fmt)
    my_logger.addHandler(file_handler)

    if args.version is True:
        my_logger.info("%s: %s", __file__, VERSION)
        return 0

    scheme = determineScheme(args)

    rsp = eventSubscribe(args, scheme)
    if rsp != 0:
        my_logger.error("FAIL: Could not subscribe to Redfish event notifications.")
        return 1

    startRedfishEventServer(args, scheme)

    nPath = getFirstNodePath(args)
    if nPath is None:
        my_logger.error("FAIL: No node found, cannot perform power actions.")
        return 1

    my_logger.info("Using node %s.", nPath)

    state = getPowerState(args, nPath)
    ret = 0
    if state is None:
        my_logger.error("FAIL: Could not query power state of target node %s.", nPath)
        ret = 1

    failures = 0
    if state == "On" and ret == 0:
        my_logger.info("Starting with node in the On state.")
        turnNodeOff(args, nPath)
        notOff = True
        if event.wait(timeout=300):
            state = waitForState(args, nPath, "Off")
            if state == "Off":
                my_logger.info("PASS: Node properly turned Off.")
                notOff = False
            else:
                failures += 1
                my_logger.error("FAIL: Node sent Redfish event but is not Off.")
        if notOff:
            my_logger.info("INFO: Node failed to turn Off in the alloted time,"
                " attempting force Off.")
            forceNodeOff(args, nPath)
            if event.wait(timeout=60):
                state = waitForState(args, nPath, "Off")
                if state == "Off":
                    my_logger.info("PASS: Node was forced Off.")
                else:
                    failures += 1
                    ret = 1
                    my_logger.error("FAIL: Node sent Redfish event but is not Off.")
            else:
                failures += 1
                state = getPowerState(args, nPath)
                if state == "Off":
                    my_logger.error("FAIL: Node turned Off but did not send a Redfish event.")
                else:
                    my_logger.error("FAIL: Node failed to be forced Off in the alloted time.")
                    ret = 1

        if ret == 0:
            time.sleep(15)
            turnNodeOn(args, nPath)
            if event.wait(timeout=60):
                state = waitForState(args, nPath, "On")
                if state == "On":
                    my_logger.info("PASS: Node properly turned On.")
                else:
                    failures += 1
                    ret = 1
                    my_logger.error("FAIL: Node sent Redfish event but is not On.")
            else:
                failures += 1
                ret = 1
                state = getPowerState(args, nPath)
                if state == "On":
                    my_logger.error("FAIL: Node turned On but did not send a Redfish event.")
                else:
                    my_logger.error("FAIL: Node failed to turn On in the alloted time.")

    if state == "Off" and ret == 0:
        my_logger.info("Starting with node in the Off state.")
        turnNodeOn(args, nPath)
        if event.wait(timeout=60):
            state = waitForState(args, nPath, "On")
            if state == "On":
                my_logger.info("PASS: Node properly turned On.")
            else:
                failures += 1
                ret = 1
                my_logger.error("FAIL: Node sent Redfish event but is not On.")
        else:
            failures += 1
            state = getPowerState(args, nPath)
            if state == "On":
                my_logger.error("FAIL: Node turned On but did not send a Redfish event.")
            else:
                my_logger.error("FAIL: Node failed to turn On in the alloted time.")
                ret = 1

        if ret == 0:
            time.sleep(30)
            my_logger.info("INFO: Attempting force Off.")
            forceNodeOff(args, nPath)
            if event.wait(timeout=60):
                state = waitForState(args, nPath, "Off")
                if state == "Off":
                    my_logger.info("PASS: Node was forced Off.")
                else:
                    failures += 1
                    ret = 1
                    my_logger.error("FAIL: Node sent Redfish event but is not Off.")
            else:
                failures += 1
                ret = 1
                state = getPowerState(args, nPath)
                if state == "Off":
                    my_logger.error("FAIL: Node turned Off but did not send a Redfish event.")
                else:
                    my_logger.error("FAIL: Node failed to be forced Off in the alloted time.")

    rsp = eventDelete(args)
    if rsp != 0:
        my_logger.error("Failed to delete Redfish event notification subscription.")
        ret = 1

    if ret == 0:
        my_logger.info("SUCCESS: All tests passed.")
    elif failures > 0:
        my_logger.error("FAILED: There %s %d test failure%s.",
                ("was" if failures == 1 else "were"), failures,
                    ("s" if failures > 1 else ""))

    return ret


if __name__ == "__main__":
    result = main()
    sys.exit(result)
