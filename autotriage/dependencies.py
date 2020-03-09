
from subprocess import Popen, PIPE

from debug import *
from health import *
from k8s import *

services = [
        "cray-hms-hmcollector",
        "cray-hms-pmdbd",
        "cray-hms-rts",
        "cray-tokens",
        "cray-vault",
        "cray-sls",
        "cray-smd",
        "cray-smd-init",
        "cray-smd-loader",
        "cray-ars",
        "cray-ipxe",
        "cray-reds",
        "cray-bss",
        "cray-meds"
        ]

def validateHmsDependencies():
    dbgPrint(dbgMed, "validateHmsDependencies")
    for svc in services:
        validateService(svc)


"""
getPodName(service name)

There are several ways that pods identify themselves and there is no standard as
to how it should be done. For each service name see if we can find the pods that
correspond to that name in the different fields that could be used. Once we
match a service name and receive pods from our k8s call, stop checking and
return our pod array.

Any new service that is added to the services list will need to be verified that
the pods can be located in one of the methods below.
"""
def getPodName(svc):
    dbgPrint(dbgMed, "getPodName " + svc)
    retArray = []

    if svc == "cray-vault":
        label = "app=vault"
    else:
        label = "app=" + svc
    dbgPrint(dbgMed, "Service: " + svc + " Label: " + label)
    pods = getK8sClient().list_pod_for_all_namespaces(label_selector=label, watch=False)
    if len(pods.items) > 0:
        for i in pods.items:
            retArray.append(i)
            dbgPrint(dbgHigh, "\t%s\t%s" % (i.metadata.namespace,
                                            i.metadata.name))

    if len(retArray) == 0:
        label = "app.kubernetes.io/name=" + svc
        dbgPrint(dbgMed, "Service: " + svc + " Label: " + label)
        pods = getK8sClient().list_pod_for_all_namespaces(label_selector=label, watch=False)
        if len(pods.items) > 0:
            for i in pods.items:
                retArray.append(i)
                dbgPrint(dbgHigh, "\t%s\t%s" %
                            (i.metadata.namespace, i.metadata.name))

    if len(retArray) == 0:
        label = "job-name=" + svc
        dbgPrint(dbgMed, "Service: " + svc + " Label: " + label)
        pods = getK8sClient().list_pod_for_all_namespaces(label_selector=label, watch=False)
        if len(pods.items) > 0:
            for i in pods.items:
                retArray.append(i)
                dbgPrint(dbgHigh, "\t%s\t%s" %
                            (i.metadata.namespace, i.metadata.name))

    return retArray


"""
validateService(service name)

Gets an array of pods based on the service name. Looks at the status information
to determine if the pod is healthy or not. With at least dbgLow set, a list of
the container statuses for the unhealthy pods is displayed along with the list
of pods that are OK.
"""
def validateService(svc):
    dbgPrint(dbgMed, "validateService " + svc)
    podArray = getPodName(svc)

    if len(podArray) == 0:
        printNotHealthy(svc)
        printExtraHealth("Service", "Not running on the system")

    for p in podArray:
        if p.status.phase in ["Running", "Succeeded"]:
            printOK(p.metadata.name)
        else:
            printNotHealthy(p.metadata.name)
            if getDbgLevel() >= dbgLow:
                if p.status.init_container_statuses is not None:
                    for c in p.status.init_container_statuses:
                        if c.state.waiting is not None:
                            printExtraHealth(c.name, c.state.waiting.reason)
                for c in p.status.container_statuses:
                    if c.state.waiting is not None:
                        printExtraHealth(c.name, c.state.waiting.reason)

