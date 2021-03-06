#!/usr/bin/python3

# MIT License
#
# (C) Copyright [2020] Hewlett Packard Enterprise Development LP
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

from subprocess import Popen, PIPE

from debug import *
from health import *
from k8s import *

services = [
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
        "cray-meds",
        "cray-hms-hmcollector",
        "cray-hms-pmdbd",
        "cray-hms-rts"
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
        idx = 0
        if p.status.conditions is not None:
            while idx < len(p.status.conditions):
                cond = p.status.conditions[idx]
                if cond.type == "Ready":
                    if (cond.status == "True" or
                        (cond.status == "False" and
                         cond.reason == "PodCompleted")):
                        printOK(p.metadata.name)
                    else:
                        printNotHealthy(p.metadata.name)
                        if getDbgLevel() >= dbgLow:
                            if p.status.init_container_statuses is not None:
                                for c in p.status.init_container_statuses:
                                    if c.state.waiting is not None:
                                        printExtraHealth(c.name, c.state.waiting.reason)
                            for c in p.status.container_statuses:
                                if c.ready is False:
                                    if (c.state.terminated is not None and
                                        c.state.terminated.reason != "Completed"):
                                        printExtraHealth(c.name, "is not ready")
                                    if c.state.waiting is not None:
                                        printExtraHealth(c.name, c.state.waiting.reason)
                idx = idx + 1
        else:
            printNotHealthy(p.metadata.name)
            printExtraHealth("container", p.status.reason)


if __name__ == "__main__":
    setDbgLevel(dbgLow)
    exit(validateHmsDependencies())

