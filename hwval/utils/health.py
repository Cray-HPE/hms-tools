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

from utils.debug import dbgPrint, dbgLow

def printOK(msg):
    r""" printOK(msg) - Prints the message with an OK """
    dbgPrint(dbgLow, "\033[1;32m%-50s\tOK\033[0m" % msg)

def printWarning(msg):
    r""" printWarning(msg) - Prints the message with a Warning"""
    print("\033[1;33m%-50s\tWarning\033[0m" % msg)

def printExtraWarning(label, msg):
    r""" printExtraWarning(label, msg) - Prints a label and then the message """
    dbgPrint(dbgLow, "\033[1;33m%50s\t%s\033[0m" % (label, msg))

def printError(msg):
    r""" printNotHealthy(msg) - Prints the message with a Error"""
    print("\033[1;31m%-50s\tError\033[0m" % msg)

def printExtraError(label, msg):
    r""" printExtraHealth(label, msg) - Prints a label and then the message """
    dbgPrint(dbgLow, "\033[1;31m%50s\t%s\033[0m" % (label, msg))

def printInfo(msg):
    r""" printInfo(msg) - Prints the message with a Info"""
    print("\033[1;35m%-50s\tInfo\033[0m" % msg)

def printExtraInfo(label, msg):
    r""" printExtraInfo(label, msg) - Prints a label and then the message """
    dbgPrint(dbgLow, "\033[1;35m%50s\t%s\033[0m" % (label, msg))
