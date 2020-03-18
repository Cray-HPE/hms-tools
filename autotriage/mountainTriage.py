#!/usr/bin/python3

from debug import *
from health import *

def triageMountainDiscovery():
    dbgPrint(dbgMed, "triageMountainDiscovery")

if __name__ == "__main__":
    setDbgLevel(dbgLow)
    exit(triageMountainDiscovery())

