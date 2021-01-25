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

from debug import dbgPrint, dbgLow

def printOK(msg):
    r""" printOK(msg) - Prints the message with an OK """
    dbgPrint(dbgLow, "\033[1;32m%-40s\tOK\033[0m" % msg)

def printNotHealthy(msg):
    r""" printNotHealthy(msg) - Prints the message with a Not Healthy """
    print("\033[1;31m%-40s\tNot Healthy\033[0m" % msg)

def printExtraHealth(label, msg):
    r""" printExtraHealth(label, msg) - Prints a lable and then the message """
    dbgPrint(dbgLow, "\033[1;31m%40s\t%s\033[0m" % (label, msg))
