"""
Global "constants"
"""
dbgLow = 1
dbgMed = 2
dbgHigh = 3

"""
Do not access this directly, use getDbgLevel() to see current value.
"""
dbgLevel = 0

def getDbgLevel():
    r""" getDbgLevel() - returns the currently set debug level """
    global dbgLevel
    return dbgLevel

def setDbgLevel(lvl):
    global dbgLevel
    dbgLevel = lvl

def dbgPrint(lvl, msg):
    global dbgLevel
    if dbgLevel >= lvl:
        print(msg)
