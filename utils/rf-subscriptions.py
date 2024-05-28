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
Support creating, deleting, and listening for subscriptions

Classes:
    HandleRequest

Functions:
    determine_bmc_type(object) -> string
    determine_scheme(object) -> string
    event_delete(object) -> int
    event_subscribe(object, string, string, bool) -> int
    list_subscriptions(object) -> object
    main() -> int
    make_redfish_call(object, string, string, object, bool) -> string
    start_redfish_event_server(object)

Misc Variables:
    event
    httpd
    http_thread
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
import requests
import urllib3

VERSION = "0.0.1"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
standard_out = logging.StreamHandler(sys.stdout)
standard_out.setLevel(logging.INFO)
logger.addHandler(standard_out)
standard_err = logging.StreamHandler(sys.stderr)
standard_err.setLevel(logging.ERROR)
logger.addHandler(standard_err)

VERBOSE1 = logging.INFO - 1
VERBOSE2 = logging.INFO - 2
logging.addLevelName(VERBOSE1, "VERBOSE1")
logging.addLevelName(VERBOSE2, "VERBOSE2")

CRAY_BMC = "Cray"
GIGABYTE_BMC = "Gigabyte"
HPE_BMC = "HPE"
INTEL_BMC = "Intel"
OPEN_BMC = "OpenBmc" # Foxconn Paradise
UNKNOWN_BMC = "Unknown"

event = threading.Event()


class HandleRequest(BaseHTTPRequestHandler):
    """Simple HTTP server to receive streaming telemetry."""

    def do_POST(self):
        """Handler for POSTs from Redfish endpoint."""
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len)
        logger.info(post_body)
        global event
        event.set()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()


def make_redfish_call(args, action, targPath, reqData=None, suppress_logs=False):
    """
    Hub to communicating with a Redfish endpoint. Returns a json payload of a
    Redfish response.

    Parameters:
        args (object): Command line arguments.
        action (string): GET, POST, or DELETE
        targPath (string): Redfish URL for HTTP request.
        reqData (object): Payload to send to Redfish endpoint on a POST.
        suppress_logs (bool): If True this only logs errors when debug is enabled

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

    logger.debug(f"request: {action}, url: {targPath}, headers: {headers}, request_body: {reqData}")

    if action == "GET":
        r = requests.get(url=targPath, auth=auth, headers=headers,
                         verify=False, timeout=30)
    elif action == "POST":
        r = requests.post(url=targPath, auth=auth, headers=headers,
                          data=reqData, verify=False, timeout=30)
    elif action == "DELETE":
        r = requests.delete(url=targPath, auth=auth, verify=False, timeout=30)
    else:
        return None

    json_body = r.text

    if not json_body:
        json_body = r.status_code

    if r.status_code >= 300:
        # the error log should not be logged when suppress_logs=True and the log level is info
        if not (suppress_logs and logger.getEffectiveLevel() == logging.INFO):
            logger.error(f"Redfish {action} for {targPath} returned {r.status_code}.")
        json_body = None

    logger.debug(f"response: {action}, url: {targPath}, code: {r.status_code}, response_body: {json_body}")

    return json_body


def start_redfish_event_server(args, scheme):
    """
    Start an HTTP server to receive streaming telemetry.

    Parameters:
        args (object): Command line arguments.
        scheme (string): Secure or unsecure http protocol.
    """
    logger.debug("Starting %s Redfish event server.", scheme)
    logger.debug("ip %s port %s", args.ip, args.port)
    httpd = HTTPServer((args.ip, int(args.port)), HandleRequest)
    if scheme == "https":
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile="cert/tls.crt",
                                       keyfile="cert/tls.key", server_side=True)

    def serve_forever(httpd):
        with httpd:
            httpd.serve_forever()

    http_thread = threading.Thread(target=serve_forever, args=(httpd,))
    http_thread.daemon = True
    http_thread.start()
    logger.info(f"Started http server. scheme: {scheme}, ip: {args.ip}, port: {args.port}")
    http_thread.join()


def event_subscribe(args, scheme, bmc_type, is_telemetry_subscription):
    """
    Sends a subscribe request to the Redfish endpoint.

    Parameters:
        args (object): Command line arguments.
        scheme (string): Secure or unsecure http protocol.
        bmc_type (string): The bmc type (cray, gigabyte, hpe, intel, or openBmc)
        is_telemetry_subscription: true if the subscription should be for telemetry

    Returns:
        result (int): 0 for success, 1 for failure
    """
    logger.debug("Subscribing to Redfish events with %s.", scheme)

    event_types = ["Alert"]
    if bmc_type == CRAY_BMC:
        event_types = ["StatusChange", "Alert", "ResourceUpdated", "ResourceAdded", "ResourceRemoved"]

    destination = f"{scheme}://{args.ip}:{args.port}/{args.bmc}"
    context = f"{args.bmc}-sub-tool"

    sub = {
        'Context': context,
        'Destination': destination,
        'Protocol': 'Redfish',
        'EventTypes': event_types,
    }
    if is_telemetry_subscription:
        sub['RegistryPrefixes'] = ["CrayTelemetry"]

    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = make_redfish_call(args, "POST", path, json.dumps(sub))

    if not rsp:
        logger.warning("Redfish call to create subscription failed.")
        return 1

    logger.info(f"Created subscription. bmc: {bmc_type}, scheme: {scheme}, Context: {context}, Destination: {destination}, EventTypes: {event_types}")
    return 0


def list_subscriptions(args):
    """
    List all the subscriptions for a BMC

    Parameters:
        args (object): Command line arguments.

    Returns:
        result (int): 0 for success, 1 for failure
    """
    sub_list = []
    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = make_redfish_call(args, "GET", path)
    if not rsp:
        logger.warning(f"Redfish call to list subscriptions failed. {path}")
        return 1

    subscriptions = json.loads(rsp)
    for subscription in subscriptions['Members']:
        entry = subscription['@odata.id']
        path = f"https://{args.bmc}{entry}"

        rsp = make_redfish_call(args, "GET", path)

        if not rsp:
            logger.warning("Redfish call to get subscription entry %s failed.", entry)
            return 1

        sub = json.loads(rsp)
        sub_list.append(sub)

    # print results
    for sub in sub_list:
        logger.info(f'{sub.get("Context"):<20} {sub.get("Destination"):<40} {sub.get("EventTypes", "")} {sub.get("RegistryPrefixes", "")}')

    return 0


def event_delete(args):
    """
    Finds and deletes the subscription that this test created.

    Parameters:
        args (object): Command line arguments.

    Returns:
        result (int): 0 for success, 1 for failure
    """
    logger.debug("Deleting subscriptions created by this test.")
    path = f"https://{args.bmc}/redfish/v1/EventService/Subscriptions"

    rsp = make_redfish_call(args, "GET", path)

    if not rsp:
        logger.warning(f"Redfish call to list subscriptions failed. {path}")
        return 1

    subCollection = json.loads(rsp)

    count = 0
    for subEntry in subCollection['Members']:
        entry = subEntry['@odata.id']
        path = f"https://{args.bmc}{entry}"

        rsp = make_redfish_call(args, "GET", path)

        if not rsp:
            logger.warning("Redfish call to get subscription entry %s failed.", entry)
            return 1

        sub = json.loads(rsp)

        if sub['Context'] == f"{args.bmc}-sub-tool":
            count += 1

            rsp = make_redfish_call(args, "DELETE", path)

            if not rsp:
                logger.warning("Redfish call to delete subscription entry %s failed.", entry)
                return 1

            logger.info(f"Deleted url: {path}, context: {sub['Context']}")
    return 0


def determine_bmc_type(args):
    """
    Determine the BMC type by getting /redfish/v1/Chassis

    Parameters:
        args (object): Command line arguments.

    Returns:
        bmc_type (string): The bmc type (cray, gigabyte, hpe, intel, or openBmc)
    """
    cray_redfish_path = "/redfish/v1/Chassis/Enclosure"
    gigabyte_redfish_path = "/redfish/v1/Chassis/Self"
    hpe_redfish_path = "/redfish/v1/Chassis/1"
    intel_redfish_path = "/redfish/v1/Chassis/RackMount"
    open_bmc_redfish_path = "/redfish/v1/Chassis/BMC_0"

    path = f"https://{args.bmc}/redfish/v1/Chassis"
    rsp = make_redfish_call(args, "GET", path)
    if not rsp:
        return ""
    chassis = json.loads(rsp)

    for member in chassis['Members']:
        url = member["@odata.id"]
        if url == cray_redfish_path:
            logger.debug("Cray BMC")
            return CRAY_BMC
        elif url == gigabyte_redfish_path:
            logger.debug("Gigabyte BMC")
            return GIGABYTE_BMC
        elif url == hpe_redfish_path:
            logger.debug("HPE BMC")
            return HPE_BMC
        elif url == intel_redfish_path:
            logger.debug("Intel BMC")
            return INTEL_BMC
        elif url == open_bmc_redfish_path:
            logger.debug("OpenBmc BMC")
            return OPEN_BMC
    logger.debug(f"Unknown BMC Type. Redfish Chassis: {rsp}")
    return UNKNOWN_BMC


def determine_scheme(args):
    """
    Check if we are talking to an iLO device. If we are, we need to use https
    instead of http for the server.

    Parameters:
        args (object): Command line arguments.

    Returns:
        scheme (string): Secure or unsecure http protocol.
    """
    logger.debug("Determining which http scheme to use.")
    path = f"https://{args.bmc}/redfish/v1/Registries/iLO"

    rsp = make_redfish_call(args, "GET", path, suppress_logs=True)

    if rsp:
        return "https"

    path = f"https://{args.bmc}/redfish/v1/Registries/OpenBMC"

    rsp = make_redfish_call(args, "GET", path, suppress_logs=True)

    if rsp:
        return "https"

    return "http"


def main(argslist=None):
    """Main program"""
    parser = argparse.ArgumentParser(description='Echo server.')
    parser.add_argument("command", help="the command to run",
                        choices=["create", "delete", "list", "listen"],
                        nargs="?")
    parser.add_argument('-i', '--ip', help='IP address to listen on.')
    parser.add_argument('-r', '--port', help='Port to listen on.')
    parser.add_argument('-b', '--bmc', help='BMC name or IP.')
    parser.add_argument('-u', '--user', help='Redfish user name.')
    parser.add_argument('-p', '--passwd', help='Redfish password.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbosity of tool in stdout')
    parser.add_argument('-V', '--version', action="store_true",
                        help='Print the script version information and exit.')
    parser.add_argument('-l', '--logdir',
                        help='Directory for log files')
    parser.add_argument('-t', '--telemetry', action='store_true',
                        help='Create a telemetry subscription')
    args = parser.parse_args(argslist)

    if args.verbose:
        standard_out.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        standard_out.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)

    # set logging file
    fmt = logging.Formatter('%(levelname)s - %(message)s')
    if args.logdir:
        logpath = args.logdir

        if not os.path.isdir(logpath):
            os.makedirs(logpath)

        file_handler = logging.FileHandler(datetime.strftime(
            datetime.now(),
            os.path.join(logpath,
            "rf-subscriptions-%m-%d-%Y-%H%M%S.txt")))
        file_handler.setLevel(min(logging.INFO if not args.verbose else logging.DEBUG, standard_out.level))
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    if args.version is True:
        logger.info("%s: %s", __file__, VERSION)
        return 0

    if args.command == "listen":
        scheme = determine_scheme(args)
        start_redfish_event_server(args, scheme)
        return 0
    elif args.command == "create":
        bmc_type = determine_bmc_type(args)
        scheme = determine_scheme(args)
        rsp = event_subscribe(args, scheme, bmc_type, args.telemetry)
        if rsp != 0:
            logger.error("FAIL: Could not subscribe to Redfish event notifications.")
            return 1
        return 0
    elif args.command == "delete":
        rsp = event_delete(args)
        if rsp != 0:
            logger.error("Failed to delete Redfish event notification subscription.")
            return 1
        return 0
    elif args.command == "list":
        list_subscriptions(args)
        return 0
    else:
        if not args.version:
            parser.print_help()
        return 1


if __name__ == "__main__":
    result = main()
    sys.exit(result)
