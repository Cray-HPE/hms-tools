# CASM Hardware Management Services tools

The repository contains a collection of tools and utilities to assist the
Hardware Management Services team in validating hardware that is to be included
in a Shasta system.

## Repository information
### validation
A set of tools to assist the Hardware Management Services team in validating
new hardware without the use of kubernetes or the Shasta software stack. These
tools communicate directly with the Redfish endpoint of the hardware that is
being validated.
### autotriage
DEPRECATED
This tool assists the Hardware Management Services team by using kubernetes and
requests modules for python to communicate with the system to determine HMS
health status. This tool is designed to identify known issues and areas to dig
in deeper. It is not designed to point out the exact error that is causing the
current problem. There is some guidance provided that will be enhanced as more
is learned.

### hwval
DEPRECATED
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
validation/
validation/test_power_capping.py
validation/test_power_control.py
validation/test_streaming_telemetry.py

sent 655 bytes  received 457 bytes  444.80 bytes/sec
total size is 44.04K  speedup is 39.60
```
