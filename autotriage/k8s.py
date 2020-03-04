from kubernetes import client, config

from debug import *


config.load_kube_config()
k8sClient = client.CoreV1Api()


def getK8sClient():
    dbgPrint(dbgMed, "initK8s")
    return k8sClient
