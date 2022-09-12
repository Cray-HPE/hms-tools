#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2022] Hewlett Packard Enterprise Development LP
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
    httpd
    httpThread
"""

#pylint: disable=C0103
#pylint: disable=W0603,W0621
#pylint: disable=R0201

import argparse
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
import urllib3

VERSION="1.0.0"

event = threading.Event()

class handleRequest(BaseHTTPRequestHandler):
    """Simple HTTP server to receive streaming telemetry."""
    def do_POST(self):
        """Handler for POSTs from Redfish endpoint."""
        global event
        event.set()

httpd = None
httpThread = None

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
                verify = False)
    elif action == "POST":
        r = requests.post(url = targPath, auth = auth, headers = headers,
                data = reqData, verify = False)
    elif action == "DELETE":
        r = requests.delete(url = targPath, auth = auth, verify = False)
    else:
        return None, "Redfish Operation", "Bad Request"

    json_body = r.text

    if not json_body:
        json_body = r.status_code

    if r.status_code >= 300:
        print("Redfish call returned %d" % r.status_code)
        json_body = None

    return json_body


def startRedfishEventServer(args):
    """
    Start an HTTP server to receive streaming telemetry.

    Parameters:
        args (object): Command line arguments.
    """
    global httpd
    global httpThread

    print("Starting Redfish event server.")
    httpd = HTTPServer((args.ip, int(args.port)), handleRequest)
    #httpd.socket = ssl.wrap_socket(httpd.socket, certfile="cert/tls.crt",
    #                                keyfile="cert/tls.key", server_side=True)

    def serve_forever(httpd):
        with httpd:
            httpd.serve_forever()

    httpThread = threading.Thread(target=serve_forever, args=(httpd,))
    httpThread.setDaemon(True)
    httpThread.start()


def eventSubscribe(args):
    """
    Sends a subscribe request to the Redfish endpoint.

    Parameters:
        args (object): Command line arguments.

    Returns:
        success/failure (int): 0 for success, 1 for failure
    """
    print("Subscribing to CrayTelemetry event")
    registryPrefixes = ["CrayTelemetry"]
    eventTypes = ["StatusChange"]
    destination = "http://%s:%s" % (args.ip, args.port)

    sub = {
        'Context': "TelemetryTest-%s-TelemetryTest" % args.bmc,
        'Destination': destination,
        'Protocol': 'Redfish',
        'RegistryPrefixes': registryPrefixes,
        'EventTypes': eventTypes,
    }

    path = "https://%s/redfish/v1/EventService/Subscriptions" % args.bmc

    rsp = makeRedfishCall(args, "POST", path, json.dumps(sub))

    if not rsp:
        print("Redfish call to create subscription failed.")
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
    print("Deleting subscriptions created by this test.")
    path = "https://%s/redfish/v1/EventService/Subscriptions" % args.bmc

    rsp = makeRedfishCall(args, "GET", path)

    if not rsp:
        print("Redfish call to list subscriptions failed.")
        return 1

    subCollection = json.loads(rsp)

    count = 0
    for subEntry in subCollection['Members']:
        entry = subEntry['@odata.id']
        path = "https://%s%s" % (args.bmc, entry)

        rsp = makeRedfishCall(args, "GET", path)

        if not rsp:
            print("Redfish call to get subscription entry %s failed." % entry)
            return 1

        sub = json.loads(rsp)

        if (sub['Context'] == "TelemetryTest-%s-TelemetryTest" % args.bmc and
                sub['Destination'] == "http://%s:%s" % (args.ip, args.port)):
            count += 1

            rsp = makeRedfishCall(args, "DELETE", path)

            if not rsp:
                print("Redfish call to delete subscription entry %s failed." % entry)
                return 1

    return 0


def main():
    """Main program"""
    parser = argparse.ArgumentParser(description='Echo server.')
    parser.add_argument('-i', '--ip', help='IP address to listen on.')
    parser.add_argument('-r', '--port', help='Port to listen on.')
    parser.add_argument('-b', '--bmc', help='BMC name or IP.')
    parser.add_argument('-u', '--user', help='Redfish user name.')
    parser.add_argument('-p', '--passwd', help='Redfish password.')
    parser.add_argument('-V', '--version', action="store_true",
            help='Print the script version information and exit.')
    args = parser.parse_args()

    if args.version is True:
        print("%s: %s" % (__file__, VERSION))
        return 0

    rsp = eventSubscribe(args)
    if rsp != 0:
        print("Failed to subscribe to streaming telemetry events.")
        return 1

    if httpd is None:
        startRedfishEventServer(args)

    ret = 1
    print("Waiting for streaming telemetry.")
    if event.wait(timeout=30):
        print("PASS: Telemetry streaming is successful.")
        ret = 0
    else:
        print("FAIL: Did not receive streaming telemetry in the alloted time.")

    rsp = eventDelete(args)
    if rsp != 0:
        print("Failed to delete streaming telemetry subscription.")
        ret = 1

    return ret


if __name__ == "__main__":
    result = main()
    sys.exit(result)
