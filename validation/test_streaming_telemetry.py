#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2022-2023] Hewlett Packard Enterprise Development LP
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
Subscribe to and validate that streaming telemetry is working.

On Olympus class hardware, the controllers are capable of sending telemetry
information to a requested destination. This test will attempt to setup
streaming telemetry and wait for streaming telemetry to be received.

Classes:
    handleRequest

Functions:
    eventDelete(object) -> int
    eventSubscribe(object) -> int
    main() -> int
    makeRedfishCall(object, string, string, object) -> string
    startRedfishEventServer(object)

Misc Variables:
    event
    httpThread
"""

# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=global-statement
# pylint: disable=missing-docstring
# pylint: disable=broad-except
# pylint: disable=too-many-nested-blocks
# pylint: disable=too-many-locals
# pylint: disable=too-many-boolean-expressions
# pylint: disable=too-many-statements
# pylint: disable=too-many-return-statements
# pylint: disable=too-many-branches
# pylint: disable=global-variable-not-assigned

from datetime import datetime

import os
import sys
import argparse
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
        r = requests.delete(url = targPath, auth = auth, verify = False,
                timeout = 30)
    else:
        return None, "Redfish Operation", "Bad Request"

    json_body = r.text

    if not json_body:
        json_body = r.status_code

    if r.status_code >= 300:
        my_logger.error("Redfish call returned %d", r.status_code)
        json_body = None

    return json_body


def startRedfishEventServer(args):
    """
    Start an HTTP server to receive streaming telemetry.

    Parameters:
        args (object): Command line arguments.
    """
    my_logger.info("Starting Redfish event server.")
    httpd = HTTPServer(('', int(args.port)), handleRequest)

    def serve_forever(httpd):
        with httpd:
            httpd.serve_forever()

    httpThread = threading.Thread(target=serve_forever, args=(httpd,))
    httpThread.daemon = True
    httpThread.start()


def eventSubscribe(args):
    """
    Sends a subscribe request to the Redfish endpoint.

    Parameters:
        args (object): Command line arguments.

    Returns:
        success/failure (int): 0 for success, 1 for failure
    """
    my_logger.info("Subscribing to CrayTelemetry event")
    registryPrefixes = ["CrayTelemetry"]
    eventTypes = ["StatusChange"]
    destination = f"http://{args.ip}:{args.port}"

    sub = {
        'Context': f"TelemetryTest-{args.bmc}-TelemetryTest",
        'Destination': destination,
        'Protocol': 'Redfish',
        'RegistryPrefixes': registryPrefixes,
        'EventTypes': eventTypes,
    }

    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = makeRedfishCall(args, "POST", path, json.dumps(sub))

    if not rsp:
        my_logger.error("Redfish call to create subscription failed.")
        return 1

    return 0


def eventDelete(args):
    """
    Finds and deletes the subscription that this test created.

    Parameters:
        args (object): Command line arguments.

    Returns:
        success/failure (int): 0 for success, 1 for failure
    """
    my_logger.info("Deleting subscriptions created by this test.")
    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        my_logger.error("Redfish call to list subscriptions failed.")
        return 1

    subCollection = json.loads(rsp)

    count = 0
    for subEntry in subCollection['Members']:
        entry = subEntry['@odata.id']
        path = f"https://{args.bmc}{entry}"

        rsp = makeRedfishCall(args, "GET", path)

        if not rsp:
            my_logger.error("Redfish call to get subscription entry %s failed.", entry)
            return 1

        sub = json.loads(rsp)

        if (sub['Context'] == "TelemetryTest-{args.bmc}-TelemetryTest" and
                sub['Destination'] == f"http://{args.ip}:{args.port}"):
            count += 1

            rsp = makeRedfishCall(args, "DELETE", path)

            if not rsp:
                my_logger.error("Redfish call to delete subscription entry %s failed.", entry)
                return 1

    return 0


def main(argslist=None):
    """Main program"""
    parser = argparse.ArgumentParser(description='Streaming telemetry test')
    parser.add_argument('-i', '--ip', help='IP address to listen on')
    parser.add_argument('-r', '--port', help='Port to listen on')
    parser.add_argument('-b', '--bmc', help='BMC name or IP')
    parser.add_argument('-u', '--user', help='Redfish user name')
    parser.add_argument('-p', '--passwd', help='Redfish password')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbosity of tool in stdout')
    parser.add_argument('-V', '--version', action="store_true",
            help='Print the script version information and exit')
    parser.add_argument('-l', '--logdir', default='./logs',
            help='Directory for log files')
    args = parser.parse_args(argslist)

    # set logging file
    standard_out.setLevel(logging.INFO - args.verbose if args.verbose < 3 else logging.DEBUG)

    logpath = args.logdir

    if not os.path.isdir(logpath):
        os.makedirs(logpath)

    fmt = logging.Formatter('%(levelname)s - %(message)s')
    file_handler = logging.FileHandler(datetime.strftime(datetime.now(), os.path.join(logpath, "StreaingTelemetryTest_%m_%d_%Y_%H%M%S.txt")))
    file_handler.setLevel(min(logging.INFO if not args.verbose else logging.DEBUG, standard_out.level))
    file_handler.setFormatter(fmt)
    my_logger.addHandler(file_handler)

    if args.version is True:
        my_logger.info("%s: %s", __file__, VERSION)
        return 0

    rsp = eventSubscribe(args)
    if rsp != 0:
        my_logger.error("Failed to subscribe to streaming telemetry events.")
        return 1

    startRedfishEventServer(args)

    ret = 1
    my_logger.info("Waiting for streaming telemetry.")
    if event.wait(timeout=30):
        my_logger.info("PASS: Telemetry streaming is successful.")
        ret = 0
    else:
        my_logger.error("FAIL: Did not receive streaming telemetry in the alloted time.")

    rsp = eventDelete(args)
    if rsp != 0:
        my_logger.error("Failed to delete streaming telemetry subscription.")
        ret = 1

    return ret


if __name__ == "__main__":
    result = main()
    sys.exit(result)
