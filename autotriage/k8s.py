from kubernetes import client, config

from debug import *


config.load_kube_config()
k8sClient = client.CoreV1Api()


def getK8sClient():
    dbgPrint(dbgMed, "getK8sClient")
    return k8sClient
