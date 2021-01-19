#!/usr/bin/python3

import json
import requests

from datetime import datetime, timedelta

from debug import *
from auth import *
from health import *

auth_token = getAuthenticationToken()

def getNid(xname):
    dbgPrint(dbgMed, "getNid")

    getHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            }

    URL = "https://api-gw-service-nmn.local/apis/smd/hsm/v1/State/Components/" + xname

    r = requests.get(url = URL, headers = getHeaders)

    dbgPrint(dbgMed, r.text)

    if r.status_code >= 300:
        return -1

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
        return -1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'nids': [nid],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_power_cap_capabilities"

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

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
            return -1
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
        return -1

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'nids': [nid],
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_power_cap"

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("get_power_cap")
        printExtraHealth(xname, capInfo['nids'][0]['err_msg'])
        return -1

    val = capInfo['nids'][0]['controls'][0]['val']

    if val is not None and val <= 0:
        printNotHealthy("get_power_cap")
        printExtraHealth("value", val)
        return -1

    printOK("get_power_cap")

    return 0

def extract_power_cap_val(capInfo):
    for x in capInfo['nids'][0]['controls']:
        if x["name"] == "node":
            return x['val']
    return None

def set_power_cap(xname):
    dbgPrint(dbgMed, "set_power_cap")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, "Could not get nid")
        return -1

    if capMax == 0:
        printNotHealthy("set_power_cap")
        printExtraHealth("Invalid max cap value", capMax)
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, "Node not in the Ready state")
        return -1

    origVal = extract_power_cap_val(capInfo)

    if origVal is not None and origVal <= 0:
        printNotHealthy("set_power_cap")
        printExtraHealth("value", origVal)
        return -1

    # Verify in range
    if origVal is not None and (origVal < capMin or origVal > capMax):
        printNotHealthy("set_power_cap")
        printExtraHealth("value", origVal)
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, capInfo['nids'][0]['err_msg'])
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    capInfo = json.loads(r.text)

    err = capInfo['e']

    if err != 0:
        printNotHealthy("set_power_cap")
        printExtraHealth(xname, "Node not in the Ready state")
        return -1

    setVal = extract_power_cap_val(capInfo)

    if setVal is not None and setVal <= 0:
        printNotHealthy("set_power_cap")
        printExtraHealth("value", setVal)
        return -1

    # Verify avg of min/max
    if setVal != capVal:
        printNotHealthy("set_power_cap")
        printExtraHealth("set value", setVal)
        printExtraHealth("expected value", capVal)
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    printOK("set_power_cap")

    return 0

def get_node_energy(xname):
    dbgPrint(dbgMed, "get_node_energy")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_node_energy")
        printExtraHealth(xname, "Could not get nid")
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    energyInfo = json.loads(r.text)
    err = energyInfo['e']

    if err > 0:
        printNotHealthy("get_node_energy")
        printExtraHealth(xname, "No data in time window")
        return -1

    energy = energyInfo['nodes'][0]['energy']

    if energy <= 0:
        printNotHealthy("get_node_energy")
        printExtraHealth("energy", energy)
        return -1

    printOK("get_node_energy")

    return 0

def get_node_energy_stats(xname):
    dbgPrint(dbgMed, "get_node_energy_stats")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(xname, "Could not get nid")
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    energyInfo = json.loads(r.text)
    err = energyInfo['e']

    if err > 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(xname, "No data in time window")
        return -1

    energy = energyInfo['energy_total']

    if energy <= 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth("energy_total", energy)
        return -1

    printOK("get_node_energy_stats")
    return 0

def get_node_energy_counter(xname):
    dbgPrint(dbgMed, "get_node_energy_counter")

    nid = getNid(xname)

    if nid < 0:
        printNotHealthy("get_node_energy_stats")
        printExtraHealth(xname, "Could not get nid")
        return -1

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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    energyInfo = json.loads(r.text)
    err = energyInfo['e']

    if err > 0:
        printNotHealthy("get_node_energy_counter")
        printExtraHealth(xname, "No data in time window")
        return -1

    energy = energyInfo['nodes'][0]['energy_ctr']

    if energy <= 0:
        printNotHealthy("get_node_energy_counter")
        printExtraHealth("energy_ctr", energy)
        return -1

    printOK("get_node_energy_counter")
    return 0

def get_system_power(xname):
    dbgPrint(dbgMed, "get_system_power")

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'window-len': 300,
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_system_power"

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = "system"
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_system_power")
        printExtraHealth(label, msg)
        return -1

    powerInfo = json.loads(r.text)
    err = powerInfo['e']

    if err > 0:
        printNotHealthy("get_system_power")
        printExtraHealth("system", "No data in time window")
        return -1

    avgPower = powerInfo['avg']

    if avgPower <= 0:
        printNotHealthy("get_system_power")
        printExtraHealth("Avg Power", avgPower)
        return -1

    printOK("get_system_power")
    return 0

def get_system_power_details(xname):
    dbgPrint(dbgMed, "get_system_power_details")

    postHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            }

    payload = {
            'window-len': 300,
            }

    URL = "https://api-gw-service-nmn.local/apis/capmc/capmc/v1/get_system_power_details"

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

    label = ""
    msg = ""

    if r.status_code >= 500:
        label = "CAPMC"
        msg = "Internal CAPMC Error"
    elif r.status_code >= 400:
        label = "system"
        msg = "Bad Request"
    elif r.status_code >= 300:
        label = "CAPMC"
        msg = "URI redirection"

    if r.status_code >= 300:
        printNotHealthy("get_system_power_details")
        printExtraHealth(label, msg)
        return -1

    powerInfo = json.loads(r.text)
    err = powerInfo['e']

    if err > 0:
        printNotHealthy("get_system_power_details")
        printExtraHealth("system", "No data in time window")
        return -1

    avgPower = powerInfo['cabinets'][0]['avg']

    if avgPower <= 0:
        printNotHealthy("get_system_power_details")
        printExtraHealth("Avg Power", avgPower)
        return -1

    printOK("get_system_power_details")
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

    r = requests.post(url = URL, headers = postHeaders, data = json.dumps(payload))

    dbgPrint(dbgMed, r.text)

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
        return -1

    status = json.loads(r.text)
    err = status['e']

    if err < 0:
        printNotHealthy("get_xname_status")
        printExtraHealth(xname, "Could not talk to BMC, undefined")
        return -1

    printOK("get_xname_status")

    return 0

validations = [
        get_power_cap_capabilities,
        get_power_cap,
        set_power_cap,
        get_node_energy,
        get_node_energy_stats,
        get_node_energy_counter,
        get_system_power,
        get_system_power_details,
        get_xname_status
        ]

def capmcValidation(xname):
    dbgPrint(dbgMed, "capmcValidation")

    idx = 0
    while idx < len(validations):
        dbgPrint(dbgMed, "Calling: %d %s" % (idx, validations[idx].__name__))
        validations[idx](xname)
        idx = idx + 1

    return 0

if __name__ == "__main__":
    setDbgLevel(dbgLow)
    exit(capmcValidation())

