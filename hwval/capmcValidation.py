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
import requests
import sys

from datetime import datetime, timedelta

from debug import dbgPrint, setDbgLevel, dbgLow, dbgMed
from auth import getAuthenticationToken
from health import printExtraHealth, printNotHealthy, printOK

auth_token = getAuthenticationToken()

def getNid(xname):
    dbgPrint(dbgMed, "getNid")

    getHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            }

    URL = "https://api-gw-service-nmn.local/apis/smd/hsm/v1/State/Components/" + xname

    dbgPrint(dbgMed, "POST: %s %s" % (URL, getHeaders))

    r = requests.get(url = URL, headers = getHeaders)

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 300:
        return 1

    comp = json.loads(r.text)

    return comp['NID']


capMin = 0
capMax = 0

def get_power_cap_capabilities(xname):
    dbgPrint(dbgMed, "get_power_cap_capabilities")
    global capMin
    global capMax

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_power_cap_capabilities")
        printExtraHealth(xname, "Could not get nid")
        return 1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'nids': [nid],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_power_cap_capabilities"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_power_cap_capabilities")
        printExtraHealth(label, msg)
        return 1

    capInfo = json.loads(r.text)

    group = capInfo['groups'][0]

    if group['controls']:
        control = None
        for tmp in group['controls']:
            if tmp['name'].startswith('Node'):
                control = tmp
                break
        if control != None:
            capMax = control['max']
            capMin = control['min']

    supply = group['supply']

    if capMax == 0:
        if supply == 0:
            printNotHealthy("get_power_cap_capabilities")
            printExtraHealth("min", capMin)
            printExtraHealth("max", capMax)
            printExtraHealth("supply", supply)
            return 1
        else:
            capMax = supply

    printOK("get_power_cap_capabilities")

    return 0

def get_power_cap(xname):
    dbgPrint(dbgMed, "get_power_cap")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_power_cap")
        printExtraHealth(xname, "Could not get nid")
        return 1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'nids': [nid],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_power_cap"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_power_cap")
        printExtraHealth(label, msg)
        return 1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("get_power_cap")
        printExtraHealth(xname, capInfo['nids'][0]['err_msg'])
        return 1

    val = capInfo['nids'][0]['controls'][0]['val']

    if val is not None and val <= 0:
        printNotHealthy("get_power_cap")
        printExtraHealth("value", val)
        return 1

    printOK("get_power_cap")

    return 0

def extract_power_cap_val(capInfo):
    for x in capInfo['nids'][0]['controls']:
        if x["name"] == "node":
            return x['val']
    return None

def set_power_cap(xname):
    dbgPrint(dbgMed, "set_power_cap")

    if capMax == 0:
        printNotHealthy("set_power_cap")
        printExtraHealth("Invalid max cap value", capMax)
        return 1

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, "Could not get nid")
        return 1

    # Get and save original value
    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'nids': [nid],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_power_cap"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("set_power_cap")
        printExtraHealth(label, msg)
        return 1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, "Node not in the Ready state")
        return 1

    origVal = extract_power_cap_val(capInfo)

    if origVal is not None and origVal <= 0:
        printNotHealthy("set_power_cap")
        printExtraHealth("value", origVal)
        return 1

    # Verify in range
    if origVal is not None and (origVal < capMin or origVal > capMax):
        printNotHealthy("set_power_cap")
        printExtraHealth("value", origVal)
        return 1

    # Set to (max - 10)
    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    capVal = capMax - 10

    payload = {
            'nids': [{'controls': [{'name': 'node', 'val': capVal}], 'nid': nid}],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/set_power_cap"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("set_power_cap")
        printExtraHealth(label, msg)
        return 1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, capInfo['nids'][0]['err_msg'])
        return 1

    # Get

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'nids': [nid],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_power_cap"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("set_power_cap")
        printExtraHealth(label, msg)
        return 1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, "Node not in the Ready state")
        return 1

    setVal = extract_power_cap_val(capInfo)

    if setVal is not None and setVal <= 0:
        printNotHealthy("set_power_cap")
        printExtraHealth("value", setVal)
        return 1

    # Verify avg of min/max
    if setVal != capVal:
        printNotHealthy("set_power_cap")
        printExtraHealth("set value", setVal)
        printExtraHealth("expected value", capVal)
        return 1

    # Set original value

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    if origVal is None:
        capVal = 0
    else:
        capVal = origVal

    payload = {
            'nids': [{'controls': [{'name': 'node', 'val': capVal}], 'nid': nid}],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/set_power_cap"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("set_power_cap")
        printExtraHealth(label, msg)
        return 1

    printOK("set_power_cap")

    return 0

def get_node_energy(xname):
    dbgPrint(dbgMed, "get_node_energy")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_node_energy")
        printExtraHealth(xname, "Could not get nid")
        return 1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    etime = datetime.today()
    stime = etime - timedelta(hours=1)

    payload = {
            'nids': [nid],
            'start_time': stime.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': etime.strftime('%Y-%m-%d %H:%M:%S'),
            }


    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_node_energy"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_node_energy")
        printExtraHealth(label, msg)
        return 1

    energyInfo = json.loads(r.text)
    err = energyInfo['e']

    if err > 0:
        printNotHealthy("get_node_energy")
        printExtraHealth(xname, "No data in time window")
        return 1

    energy = energyInfo['nodes'][0]['energy']

    if energy <= 0:
        printNotHealthy("get_node_energy")
        printExtraHealth("energy", energy)
        return 1

    printOK("get_node_energy")

    return 0

def get_node_energy_stats(xname):
    dbgPrint(dbgMed, "get_node_energy_stats")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(xname, "Could not get nid")
        return 1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    etime = datetime.today()
    stime = etime - timedelta(hours=1)

    payload = {
            'nids': [nid],
            'start_time': stime.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': etime.strftime('%Y-%m-%d %H:%M:%S'),
            }


    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_node_energy_stats"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(label, msg)
        return 1

    energyInfo = json.loads(r.text)
    err = energyInfo['e']

    if err > 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(xname, "No data in time window")
        return 1

    energy = energyInfo['energy_total']

    if energy <= 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth("energy_total", energy)
        return 1

    printOK("get_node_energy_stats")
    return 0

def get_node_energy_counter(xname):
    dbgPrint(dbgMed, "get_node_energy_counter")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(xname, "Could not get nid")
        return 1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    etime = datetime.today()
    stime = etime - timedelta(hours=1)

    payload = {
            'nids': [nid],
            'start_time': stime.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': etime.strftime('%Y-%m-%d %H:%M:%S'),
            }


    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_node_energy_counter"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_node_energy_counter")
        printExtraHealth(label, msg)
        return 1

    energyInfo = json.loads(r.text)
    err = energyInfo['e']

    if err > 0:
        printNotHealthy("get_node_energy_counter")
        printExtraHealth(xname, "No data in time window")
        return 1

    energy = energyInfo['nodes'][0]['energy_ctr']

    if energy <= 0:
        printNotHealthy("get_node_energy_counter")
        printExtraHealth("energy_ctr", energy)
        return 1

    printOK("get_node_energy_counter")
    return 0

def get_xname_status(xname):
    dbgPrint(dbgMed, "get_xname_status")

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'xnames': [xname],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_xname_status"

    dbgPrint(dbgMed, "POST: %s %s %s" % (URL, postHeaders, payload))

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, "Response: %s" % r.text)

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = xname
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_xname_status")
        printExtraHealth(label, msg)
        return 1

    status = json.loads(r.text)
    err = status['e']

    if err < 0:
        printNotHealthy("get_xname_status")
        printExtraHealth(xname, "Could not talk to BMC, undefined")
        return 1

    printOK("get_xname_status")

    return 0

validations = [
        get_power_cap_capabilities,
        get_power_cap,
        set_power_cap,
        get_node_energy,
        get_node_energy_stats,
        get_node_energy_counter,
        get_xname_status
        ]

def capmcValidation(xname, tests=None, list=False):
    dbgPrint(dbgMed, "capmcValidation")

    if list:
        return validations

    failures = 0
    if tests:
        for t in tests:
            for test in validations:
                if t == test.__name__:
                    dbgPrint(dbgMed, "Calling: capmcValidation:%s" % test.__name__)
                    ret = test(xname)
                    failures = failures + ret
    else:
        for test in validations:
            dbgPrint(dbgMed, "Calling: capmcValidation:%s" % test.__name__)
            ret = test(xname)
            failures = failures + ret

    return failures

if __name__ == "__main__":
    setDbgLevel(dbgLow)
    dbgPrint(dbgLow, "Calling: capmcValidation(%s, %s, %s)" % (sys.argv[1],
        sys.argv[2], sys.argv[3]))
    exit(capmcValidation(sys.argv[1], sys.argv[2], sys.argv[3]))

