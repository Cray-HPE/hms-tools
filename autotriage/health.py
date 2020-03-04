from debug import *

def printOK(msg):
    r""" printOK(msg) - Prints the message with an OK """
    dbgPrint(dbgLow, "%-30s\tOK" % msg)

def printNotHealthy(msg):
    r""" printNotHealthy(msg) - Prints the message with a Not Healthy """
    print("%-30s\tNot Healthy" % msg)

def printExtraHealth(label, msg):
    r""" printExtraHealth(label, msg) - Prints a lable and then the message """
    dbgPrint(dbgLow, "%30s\t%s" % (label, msg))
