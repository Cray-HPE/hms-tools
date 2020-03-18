# CASMHMS Triage tools

The repository contains a collection of tools and utilities to assist in
triaging a Shasta system.

## Repository information

```bash
git clone ssh://git@stash.us.cray.com:7999/hms/hms-triage-tools.git
```

```bash
hms-triage-tools/
|-- autotriage/
|   |-- debug.py
|   |-- dependencies.py
|   |-- execute_triage.py
|   |-- health.py
|   |-- k8s.py
|   |-- mountainTriage.py
|   |-- remote.py
|   |-- riverTriage.py
|
|-- push_tools_to_host.sh
```

## Push utility

```bash
Usage: push_tools_to_host -H <hostname>
```

Everything in the autotriage directory is rsync'd to the target host into
/tmp/hms-triage-tools. As new directories are added to the repo they should be
added to the push_tools_to_host script.

```bash
~/dev/hms-triage-tools > ./push_tools_to_host.sh -H surly2-ncn-w001
Password:
sending incremental file list
created directory /tmp/hms-triage-tools
autotriage/
autotriage/.riverTriage.py.swp
autotriage/debug.py
autotriage/dependencies.py
autotriage/execute_triage.py
autotriage/health.py
autotriage/mountainTriage.py
autotriage/remote.py
autotriage/riverTriage.py
autotriage/__pycache__/
autotriage/__pycache__/debug.cpython-36.pyc
autotriage/__pycache__/dependencies.cpython-36.pyc

sent 5.88K bytes  received 262 bytes  4.09K bytes/sec
total size is 22.07K  speedup is 3.60
```

## Autotriage utility

This tool uses the kubernetes and requests modules for python to communicate
with the system to determine health status. This tool is designed to identify
known issues and areas to dig in deeper. It is not designed to point out the
exact error that is causing the current problem. There is some guidance provided
that will be enahanced as we learn more about each error that we encounter.

Each triage module can be executed on it's own, or it can be called from the
main driver program execute_triage.py. When executed from the driver program,
verbosity is off and you will only see **Not Healthy** messages. That can be
changed using one or more -v options. When executed as an individual module,
the verbosity is set to Low (a single -v) and cannot be changed on the command
line.  This level of verbosity will show all **OK**, **Not Healthy**, and
additional error information for each of the **Not Healthy** items.

New triage modules can be written and added to the triageModules table in the
execute_triage.py script. The triageModules get executed in the order they
appear in the list.

```bash
mug-ncn-w001:~ $ /tmp/hms-triage-tools/autotriage/execute_triage.py -h
usage: execute_triage.py [-h] [-H HOST] [--xnames XNAMES] [-v]

Automatic triaging tool.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase output verbosity.
```

Example base output. sma-cstream is included for debug purposes. Mug is River
only so cray-meds is not running, which is OK. And cray-hms-rts is expected to
be initializing at this stage until SLS is populated with information it needs
to do its job. x3000c0s7b0 is ncn-w001 which is only available on the CAN right
now for Mug.

```bash
mug-ncn-w001:~ $ /tmp/hms-triage-tools/autotriage/execute_triage.py
sma-cstream-86c57d9c9d-95dpc    Not Healthy
cray-hms-rts-9478985c9-qm9xn    Not Healthy
cray-meds                       Not Healthy
x3000c0s7b0                     Not Healthy
Done
```

Providing a single -v gives a little more detail about the unhealthy components
and shows everything that is checked.

```bash
mug-ncn-w001:~ $ /tmp/hms-triage-tools/autotriage/execute_triage.py -v
sma-cstream-86c57d9c9d-95dpc    Not Healthy
                       cstream  ContainerCreating
cray-hms-rts-9478985c9-qm9xn    Not Healthy
                    istio-init  PodInitializing
                  cray-hms-rts  PodInitializing
            cray-hms-rts-redis  PodInitializing
                   istio-proxy  PodInitializing
cray-tokens-7d99dc7d9-wvs7b     OK
cray-vault-0                    OK
cray-sls-5f9dd666f9-tsx5g       OK
cray-smd-76d49f59cc-cmgkz       OK
cray-smd-init-tzg4p             OK
cray-smd-loader-gbkxz           OK
cray-ars-c6b568c94-2w52m        OK
cray-ars-c6b568c94-jsg5p        OK
cray-ars-c6b568c94-kcb22        OK
cray-ipxe-7d7bfdb89d-th6fq      OK
cray-reds-7fdd68897f-wm5b4      OK
cray-bss-9cf9c746-grp5l         OK
cray-meds                       Not Healthy
                       Service  Not running on the system
cray_reds_maas_bridge.json      OK
mapping.json                    OK
x3000c0s7b0                     Not Healthy
                     Component  Missing from HSM
REDS mapping ifNames            OK
Done
```

Providing more than one -v starts getting into debugging information for the
script itself.
