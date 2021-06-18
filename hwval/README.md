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
is off and you will only see **Info**, **Warning**, and **Not Healthy**
messages. that can be changed using one or more -v options. When executed as an
individual module, the verbosity is set to Low (a single -v) and cannot be
changed on the command line. This level of verbosity will show all **OK**,
**Info**, **Warning**, and **Not Healthy**, and additional information for
each of the non-**OK** items.

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
  -i IPS, --ips IPS     IPs to do hardware validation on. Valid options are a
                        single IP, comma separated IPs, or hostlist style IPs:
                        10.1.100.[1-36]
  -t TESTS, --tests TESTS
                        List of tests to execute in the form
                        <module>:<test>[,<module>:<test>[,...]]
  -v, --verbose         Increase output verbosity.
  -V, --version         Print the script version information and exit.
  -u USER, --user USER  Username for Redfish validation. All XNAMES and IPs must
                        have the same username for their BMC.
  -p PASSWD, --passwd PASSWD
                        Password for Redfish validation. All XNAMES and IPs must
                        have the same password for their BMC.
```

Example output for a mountain node.

```
ncn-m001:/tmp/hms-tools/hwval # ./hwval.py -x x1000c7s5b0n0 -u root -p $PASSWD
-v capmcValidation(x1000c7s5b0n0):
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

# Modules

## CAPMC

Utilizes the CAPMC API to perform certain operations to validate the hardware
can be controlled and monitored by CAPMC.

### Additional Requirements

* Working k8s Shasta stack
  * Hardware State Manager
  * Vault

### Validations

* get_power_cap_capabilities
  * Makes a CAPMC call that will query the HSM to get the power capping
  capabilities of the target XNAME.
  * Checks:
    * First Node control has a valid Max set
    * First Node control has a valid Supply set

* get_power_cap
  * Makes a CAPMC call that will query the hardware for the currently set power
  cap limit
  * Checks:
    * /redfish/v1/Chassis/{systemID}/Power .PowerControl.PowerLimit.LimitInWatts
    has a valid setting

* set_power_cap
  * Makes several CAPMC calls to get the current power cap setting, set the
  power cap to a reduced value, query the setting to validate it is set, return
  the power cap setting to the original value.

* get_node_energy (DEPRECATED)
  * Makes a CAPMC call that queries the PMDB for node energy telemetry to check
  for valid telemetry

* get_node_energy_stats (DEPRECATED)
  * Makes a CAPMC call that queries the PMDB for node energy statistics to check
  for valid telemetry

* get_node_energy_counter (DEPRECATED)
  * Makes a CAPMC call that queries the PMDB for node energy counter telemetry
  to check for valid telemetry

* get_xname_status
  * Makes a CAPMC call that will query the hardware for the current power
  status.

## Redfish

Utilizes direct calls to Redfish to validate certain URIs and fields within
those URIs are available for the HMS software stack to manage the hardware with.

### Additional requirements

* Credentials for the Redfish endpoints
* All Redfish endpoint credentials used as targets for the command need to be
the same.

### Validations

* checkRedfishURIs
  * Makes Redfish calls to specific high level URIs checking fields for valid
  types and values
  * URIs and fields:
    * /redfish/v1
      * .Chassis
      * .EventService
      * .Managers
      * .Systems
      * .UpdateService
    * /redfish/v1/Chassis
      * .Members
    * /redfish/v1/Systems
      * .Members
    * /redfish/v1/Managers
      * .Members
    * /redfish/v1/UpdateService
      * .Actions
      * .FirmwareInvenntory
    * /redfish/v1/EventService
      * .Subscriptions

* checkRedfishChassis
  * Makes Redfish calls to Chassis URIs checking fields for valid types and
  values.
  * URIs and fields:
    * /redfish/v1/Chassis/{systemID}
      * .SerialNumber
      * .Power
      * .PartNumber
      * .Manufacturer
      * .Model

* checkRedfishManagers
  * Makes Redfish calls to Managers URIs checking fields for valid types and
  values.
  * URIs and fields:
    * /redfish/v1/Chassis/{systemID}
      * .Name
      * .Actions
      * .ManagerType
      * .NetworkProtocol

* checkRedfishEventService
  * Makes Redfish calls to the EventService URI checking fields for valid types
  and values.
  * URIs and fields:
    * /redfish/v1/EventService
      * EventService definition pre-1.3
        * .EventTypesForSubscription
        * .Subscriptions
      * EventService definition 1.3 and later
        * .RegistryPrefixes
        * .ResourceTypes
        * .Subscriptions

* checkRedfishSystems
  * Makes Redfish calls to the Systems URIs checking fields for valid types and
  values.
  * URIs and fields:
    * /redfish/v1/Systems/{systemID}
      * .Actions
      * .Bios
      * .BiosVersion
      * .EthernetInterfaces
      * .Manufacturer
      * .Memory
      * .MemorySummary
      * .Model
      * .PartNumber
      * .PowerState
      * .Processors
      * .SerialNumber
      * .SKU
      * .Status
    * /redfish/v1/Systems/{systemID}/Memory
      * .Members
      * .Members@odata.count
    * /redfish/v1/Systems/{systemID}/Memory/{dimmID}
      * .CapacityMiB
      * .Id
      * .MemroyDeviceType
      * .Manufacturer
      * .PartNumber
      * .SerialNumber
      * .OperatingSpeedMhz
    * /redfish/V1/Systems/{systemID}/Processors
      * .Members
      * .Members@odata.count
    * /redfish/V1/Systems/{systemID}/Processors/{cpuID}
      * .Manufacturer
      * .Model
      * .SerialNumber
      * .TotalCores
      * .TotalThreads
      * .MaxSpeedMHz

* checkRedfishUpdateService
  * Makes Redfish calls to the UpdateService URIs checking for valid types and
  values.
  * URIs and fields:
    * /redfish/v1/UpdateService
      * .Actions.#UpdateService.SimpleUpdate.@Redfish.ActionInfo
      * .Actions.#UpdateService.SimpleUpdate.target
    * /redfish/v1/UpdateService/FirmwareInventory/{fwID}
      * .@odata.id
      * .Id
      * .Version
      * .Name

* telemetryPoll
  * Makes Redfish calls to validate telemetry queries contain the expected data
  fields. Not all hardware supports all possible checks.
  * Checks:
    * /redfish/v1/Chassis/Power
      * .PowerControl.PowerMetrics.AverageConsumedWatts
      * .Voltages[].ReadingVolts
      * .PowerSupplies[].LineInputVoltage
    * /redfish/v1/Chassis/Thermal
      * .Fans[].Reading
      * .Temperatures[].ReadingCelsius
