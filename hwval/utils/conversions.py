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

from utils.debug import dbgPrint, dbgMed, dbgHigh
from utils.auth import getAuthenticationToken

def nidsToXnames(nidlist):
    dbgPrint(dbgMed, "nidsToXnames")

    auth_token = getAuthenticationToken()

    getHeaders = {
            'Authorization': 'Bearer %s' % auth_token,
            'cache-control': 'no-cache',
            }

    queryparams = {}
    queryparams['nid'] = []
    for n in nidlist.split(','):
        queryparams['nid'].append(int(n))

    URL = "https://api-gw-service-nmn.local/apis/smd/hsm/v1/State/Components"

    dbgPrint(dbgMed, "POST: %s %s" % (URL, queryparams))
    dbgPrint(dbgHigh, "POST: %s" % getHeaders)

    r = requests.get(url = URL, headers = getHeaders, params = queryparams)

    dbgPrint(dbgMed, "Response: %s" % r.text)

    if r.status_code >= 300:
        return 1

    components = json.loads(r.text)
    xnames = None
    for comp in components['Components']:
        if xnames is None:
            xnames = comp['ID']
        else:
            xnames = xnames + ',' + comp['ID']

    return xnames
