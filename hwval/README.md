# Hardware Validation Tool

This tool assists the Hardware Management Services team by using kubernetes and
requests modules for python to communicate with the system to determine hardware
compatibility with the HMS services. This tool is designed as a high level
thumbs up/thumbs down utility. Deep dive into why a certain aspect of the tool
reports an error is not done. Extra information is provided where possible when
a failure occurs. Not all hardware supports all features and may fail a portion
of the validation.

Each validation module can be executed on it's own, or it can be called from the
main driver program hwval.py. When executed from the driver program, verbosity
is off and you will only see **Not Healthy** messages. that can be changed using
one or more -v options. When executed as an individual module, the verbosity is
set to Low (a single -v) and cannot be changed on the command line. This level
of verbosity will show all **OK**, **Not Healthy**, and additional error
information for each of the **Not Healthy** items.

New validation modules can be written and added to the hardwareValidation table
in the hwval.py script. The hardwareValidation entries get executed in the order
they appear in the list.

## Requirements
* Executes on an NCN
* Requires being logged in as root

## Usage
```
ncn-m001:~ # cd /tmp/hms-tools
ncn-m001:/tmp/hms-tools/hwval # ./hwval.py --h
usage: hwval.py [-h] [-l LIST] [-x XNAMES] [-n NIDS] [-t TESTS] [-v] [-V]
                [-u USER] [-p PASSWD]

Automatic hardware validation tool.

optional arguments:
  -h, --help            show this help message and exit
  -l LIST, --list LIST  List modules and tests that are available. all: show
                        all modules and tests, top: show top level modules,
                        <module>: show tests for the module
  -x XNAMES, --xnames XNAMES
                        Xnames to do hardware validation on. Valid options are
                        a single xname, comma separated xnames, or hostlist
                        style xnames
  -n NIDS, --nids NIDS  Nids to do hardware validation on. Valid options are a
                        single nid, comma separated nids, or hostlist style
                        nids: [1-10]
  -t TESTS, --tests TESTS
                        List of tests to execute in the form
                        <module>:<test>[,<module>:<test>[,...]]
  -v, --verbose         Increase output verbosity.
  -V, --version         Print the script version information and exit.
  -u USER, --user USER  Username for Redfish validation. All --xnames must
                        have the same username for their BMC.
  -p PASSWD, --passwd PASSWD
                        Password for Redfish validation. All --xnames must
                        have the same password for their BMC.
```

Example output for a mountain node.

```
ncn-m001:/tmp/hms-tools/hwval # ./hwval.py -x x1000c7s5b0n0 -u root -p $PASSWD -v
capmcValidation(x1000c7s5b0n0):
get_power_cap_capabilities              	OK
get_power_cap                           	OK
set_power_cap                           	OK
get_node_energy                         	Not Healthy
                           x1000c7s5b0n0	No data in time window
get_node_energy_stats                   	Not Healthy
                           x1000c7s5b0n0	No data in time window
get_node_energy_counter                 	Not Healthy
                           x1000c7s5b0n0	No data in time window
get_xname_status                        	OK
redfishValidation(x1000c7s5b0n0):
telemetryPoll                           	OK
6 Validations FAILED
Done
```
