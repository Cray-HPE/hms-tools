#!/bin/bash
#
# MIT License
#
# (C) Copyright [2021] Hewlett Packard Enterprise Development LP
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

debug=0

function usage {
    name=$(basename $0)
    echo "Usage: ${name} [-h] -H <host> [-d]"
    echo
    echo "-h            This help"
    echo "-H <host>     Host to push tools to"
    echo "-d            Turn on 'set -x'"
    echo
}

while getopts "hH:d" opt; do
    case ${opt} in
        h) usage
            exit 0
            ;;
        H) host=${OPTARG}
            ;;
        d) set -x
            ;;
        :) echo "Invalid option: $OPTARG requires an argument" 1>&2
            exit 1
            ;;
        *) usage
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

if [ -z ${host} ]; then
    usage
    exit 1
fi

set -e

rsync -avzh autotriage root@${host}:/tmp/hms-tools
rsync -avzh hwval root@${host}:/tmp/hms-tools

