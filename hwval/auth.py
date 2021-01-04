import json
import requests

from base64 import b64decode

from k8s import *

def getAuthenticationToken():
    dbgPrint(dbgMed, "getAuthenticationToken")

    URL = "https://api-gw-service-nmn.local/keycloak/realms/shasta/protocol/openid-connect/token"

    kSecret = getK8sClient().read_namespaced_secret("admin-client-auth", "default")
    secret = b64decode(kSecret.data['client-secret']).decode("utf-8")
    dbgPrint(dbgHigh, "\tSecret: " + secret)

    DATA = {
            "grant_type": "client_credentials",
            "client_id": "admin-client",
            "client_secret": secret
            }

    try:
        r = requests.post(url = URL, data = DATA)
    except OSError:
        return ""

    result = json.loads(r.text)

    dbgPrint(dbgHigh, result['access_token'])
    return result['access_token']


