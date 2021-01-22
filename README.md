# CASM Hardware Management Services tools

The repository contains a collection of tools and utilities to assist the
Hardware Management Services team in managing a Shasta system. The Hardware
Management Services are responsible for monitoring and maintaining a running
Shasta system.

## Repository information
### autotriage
This tool assists the Hardware Management Services team by using kubernetes and
requests modules for python to communicate with the system to determine HMS
health status. This tool is designed to identify known issues and areas to dig
in deeper. It is not designed to point out the exact error that is causing the
current problem. There is some guidance provided that will be enhanced as more
is learned.

### hwval
This tool assists the Hardware Management Services team by using kubernetes and
requests modules for python to communicate with the system to determine hardware
compatibility with the HMS services. This tool is designed as a high level
thumbs up/thumbs down utility. Deep dive into why a certain aspect of the tool
reports an error is not done. Extra information is provided where possible when
a failure occurs. Not all hardware supports all features and may fail a portion
of the validation.

### Push utility

```
Usage: push_tools_to_host -H <hostname>
```

Everything in the autotriage directory is rsync'd to the target host into
/tmp/hms-tools. As new directories are added to the repo they should be
added to the push_tools_to_host script.

```
~/dev/hms-tools > ./push_tools_to_host.sh -H surly2-ncn-w001
Password:
sending incremental file list
created directory /tmp/hms-tools
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