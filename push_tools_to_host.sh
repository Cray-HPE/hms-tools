#!/bin/bash

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

rsync -avzh autotriage root@${host}:/tmp/hms-triage-tools

