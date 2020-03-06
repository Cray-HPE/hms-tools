from debug import *

def printOK(msg):
    r""" printOK(msg) - Prints the message with an OK """
    dbgPrint(dbgLow, "\033[1;32;40m%-30s\tOK\033[0m" % msg)

def printNotHealthy(msg):
    r""" printNotHealthy(msg) - Prints the message with a Not Healthy """
    print("\033[1;31;40m%-30s\tNot Healthy\033[0m" % msg)

def printExtraHealth(label, msg):
    r""" printExtraHealth(label, msg) - Prints a lable and then the message """
    dbgPrint(dbgLow, "\033[1;31;40m%30s\t%s\033[0m" % (label, msg))
