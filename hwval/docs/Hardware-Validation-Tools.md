1.  [CASMHMS](index.html)
2.  [CASMHMS Home](CASMHMS-Home_119901124.html)
3.  [Design Documents](Design-Documents_127906417.html)

# <span id="title-text"> CASMHMS : Hardware Validation Tools </span>

Created by <span class="author"> Michael Jendrysik</span>, last modified
on Jan 19, 2021

<table class="wrapped confluenceTable">
<tbody>
<tr class="odd">
<th class="confluenceTh">Developers</th>
<td class="confluenceTd"><div class="content-wrapper">
<p><a href="https://connect.us.cray.com/confluence/display/~mjendrysik" class="confluence-userlink user-mention">Michael Jendrysik</a>, <a href="https://connect.us.cray.com/confluence/display/~phalseth" class="confluence-userlink user-mention">Pete Halseth</a>, <a href="https://connect.us.cray.com/confluence/display/~schooler" class="confluence-userlink user-mention">Mitchell Schooler</a>, <a href="https://connect.us.cray.com/confluence/display/~nowicki" class="confluence-userlink user-mention">James Nowicki</a></p>
</div></td>
</tr>
<tr class="even">
<th class="confluenceTh">Tester</th>
<td class="confluenceTd"><div class="content-wrapper">
<p><a href="https://connect.us.cray.com/confluence/display/~mjendrysik" class="confluence-userlink user-mention">Michael Jendrysik</a>, <a href="https://connect.us.cray.com/confluence/display/~phalseth" class="confluence-userlink user-mention">Pete Halseth</a>, <a href="https://connect.us.cray.com/confluence/display/~schooler" class="confluence-userlink user-mention">Mitchell Schooler</a>, <a href="https://connect.us.cray.com/confluence/display/~nowicki" class="confluence-userlink user-mention">James Nowicki</a></p>
</div></td>
</tr>
<tr class="odd">
<th class="confluenceTh">Publications</th>
<td class="confluenceTd"></td>
</tr>
<tr class="even">
<th class="confluenceTh">Product</th>
<td class="confluenceTd"><em>Shasta</em></td>
</tr>
<tr class="odd">
<th class="confluenceTh">Target release</th>
<td class="confluenceTd"><div class="content-wrapper">
<p><span class="status-macro aui-lozenge">2021-02-26</span></p>
</div></td>
</tr>
<tr class="even">
<th class="confluenceTh">Epic</th>
<td class="confluenceTd"><br />
</td>
</tr>
<tr class="odd">
<th class="confluenceTh">Date</th>
<td class="confluenceTd"><em>2020-01-11</em></td>
</tr>
<tr class="even">
<th class="confluenceTh">Document status</th>
<td class="confluenceTd"><div class="content-wrapper">
<span class="status-macro aui-lozenge">DRAFT</span>
</div></td>
</tr>
</tbody>
</table>

# <span class="nh-number">1. </span>Abstract

Over the course of the lifetime of a project new hardware and new
firmware is always available. Before this hardware or firmware can be
used effectively in the Shasta system, some validation must be done on
it. Currently that validation is done by hand resulting in slow
validation efforts, inconsistent coverage, and an uneasiness that
something was missed. Some tooling does exist to assist in hardware
validation but it is not used for any number of reasons, new tooling is
being written to assist certain aspects of validation, and yet other
tools exist but may not be in the proper form to use for validation.
This document will be an attempt to identify all tooling that exists, is
being worked on, and what is missing and then to collect all the tools
into a coherent story to enhance and speed up hardware and firmware
validation.

# <span class="nh-number">2. </span>Change History

  

<table class="wrapped confluenceTable">
<tbody>
<tr class="odd">
<td class="confluenceTd"><p><strong>Date</strong></p></td>
<td class="confluenceTd"><p><strong>Version</strong></p></td>
<td class="confluenceTd"><p><strong>Change Description</strong></p></td>
</tr>
<tr class="even">
<td class="confluenceTd"><p><em>2020-01-11</em></p></td>
<td class="confluenceTd"><p><em>0.1</em></p></td>
<td class="confluenceTd"><p>Initial version</p></td>
</tr>
</tbody>
</table>

**Table of Contents**

-   [1. Abstract](#HardwareValidationTools-Abstract)
-   [2. Change History](#HardwareValidationTools-ChangeHistory)
-   [3. Introduction](#HardwareValidationTools-Introduction)
    -   [3.1.
        Problem/Motivation](#HardwareValidationTools-Problem/Motivation)
    -   [3.2. Assumptions](#HardwareValidationTools-Assumptions)
    -   [3.3. Proposed
        Solution](#HardwareValidationTools-ProposedSolution)
    -   [3.4. Rationale](#HardwareValidationTools-Rationale)
    -   [3.5. Requirements](#HardwareValidationTools-Requirements)
-   [4. Description](#HardwareValidationTools-Description)
    -   [4.1. Detail](#HardwareValidationTools-Detail)
    -   [4.2. Interfaces](#HardwareValidationTools-Interfaces)
    -   [4.3. Use Cases](#HardwareValidationTools-UseCases)
    -   [4.4. Requirements
        Response](#HardwareValidationTools-RequirementsResponse)
    -   [4.5. Changes](#HardwareValidationTools-Changes)
    -   [4.6. Dependencies](#HardwareValidationTools-Dependencies)
    -   [4.7.
        Portability/Compatibility](#HardwareValidationTools-Portability/Compatibility)
    -   [4.8.
        Performance/Scalability](#HardwareValidationTools-Performance/Scalability)
    -   [4.9. RAS/Robustness](#HardwareValidationTools-RAS/Robustness)
    -   [4.10.
        Programmability](#HardwareValidationTools-Programmability)
    -   [4.11. Productivity](#HardwareValidationTools-Productivity)
    -   [4.12.
        Configurability](#HardwareValidationTools-Configurability)
    -   [4.13. Security](#HardwareValidationTools-Security)
    -   [4.14.
        Build/Install/Packaging](#HardwareValidationTools-Build/Install/Packaging)
    -   [4.15.
        Support/Maintainability](#HardwareValidationTools-Support/Maintainability)
    -   [4.16. Risks](#HardwareValidationTools-Risks)
    -   [4.17. Other Issues](#HardwareValidationTools-OtherIssues)
-   [5. Documentation](#HardwareValidationTools-Documentation)
-   [6. Stakeholders](#HardwareValidationTools-Stakeholders)
-   [7. Minutes](#HardwareValidationTools-Minutes)
-   [8. Appendix](#HardwareValidationTools-Appendix)
    -   [8.1. List of New
        Acronyms](#HardwareValidationTools-ListofNewAcronyms)
    -   [8.2. References](#HardwareValidationTools-References)

 

# <span class="nh-number">3. </span><u>Introduction</u>

## <span class="nh-number">3.1. </span>Problem/Motivation

The HMS development team is tasked with some validation of new hardware
and firmware that is made available. These validation efforts need to be
done to make sure the HMS services are able to properly discover and
manage the hardware. If HMS is unable to manage the hardware then the
system will be unusable for other CSM services and most importantly
customers be unable to run jobs. Validation efforts take valuable time
away from development and bug fixing of the Shasta HMS software stack.

## <span class="nh-number">3.2. </span>Assumptions

-   Validation of single nodes/switches
-   Validation of groups of nodes/switches
-   Minimal validation of hardware outside of the Shasta software stack
-   Full validation of hardware integrated with the Shasta software
    stack
-   Possible productization or open-sourcing of the validation tools

## <span class="nh-number">3.3. </span>Proposed Solution

Identifying existing tools, writing new tools, combining tools where
appropriate, and generating a validation document.

Expand the hwval.py tool that was writing for CAPMC validation. Improve
the infrastructure to allow listing and selecting of individual tests.
Add new validation modules where appropriate. Tie in existing tools
where it makes sense.

Update or write a new rfvalepidator tool. Currently this tool compares
Redfish output to previous runs on the same hardware. Enhance the tool
to validate the Redfish on new hardware to verify discovery can complete
as expected. If enhancing this tool is not possible, writing a new tool
that does not require any docker or k8s software will be written.

Document procedures to enable groups outside of HMS to be able to do
some validation of hardware and firmware before it is delivered.

## <span class="nh-number">3.4. </span>Rationale

There are currently no dedicated tools or procedures to follow. The
alternative to developing the tools and procedures is to continue to do
validation without guidance and by hand.

## <span class="nh-number">3.5. </span>Requirements

1.  Redfish validation able to run outside of the Shasta k8s environment
2.  No institutional knowledge needed to execute the tools
3.  Simple output for increased comprehension
4.  Listing of all validation routines on a tool-by-tool basis
5.  Ability to select individual validation routines and groups of
    routines
6.  One driver for all tools
7.  Individual tools executable as stand-alone entities
8.  IP address, xname, or NID as valid targets
9.  Multi-target capable
10. Capable of being executed using automation

# <span class="nh-number">4. </span><u>Description</u>

## <span class="nh-number">4.1. </span>Detail

**hwval - Hardware Validation Tool**

Validations are broken up into individual python modules and the module
entry point is added to a master table. Each module file also includes a
table of individual validations that can be executed as a group or
individually. Simplified k8s authentication on a per module basis.
Available validations can be listed and filtered based on the module.
Individual tests can be selected by supplying the module name along with
the test name in the form &lt;module&gt;:&lt;test&gt;.

-   Requires full Shasta stack

Targeted validations:

-   **CAPMC**
    -   get\_power\_cap\_capabilities
    -   get\_power\_cap - requires the target node to be in the Ready
        state
    -   set\_power\_cap - requires the target node to be in the Ready
        state
    -   get\_node\_energy - database query - indicates telemetry is
        flowing from Mountain nodes, polling is working for River nodes
    -   get\_node\_energy\_stats - database query - indicates telemetry
        is flowing from Mountain nodes, polling is working for River
        nodes
    -   get\_node\_energy\_counter - database query - indicates
        telemetry is flowing from Mountain nodes, polling is working for
        River nodes
    -   *get\_system\_power* - remove, cabinet/rack level power queries
        do not prove target hardware is working correctly
    -   *get\_system\_power\_details* - remove, cabinet/rack level power
        queries do not prove target hardware is working correctly
    -   get\_xname\_status
    -   xname\_on
    -   xname\_off
    -   get\_xname\_power\_cap\_capabilities - CAPMC enhancement needed
    -   get\_xname\_power\_cap - CAPMC enhancement needed
    -   set\_xname\_power\_cap - CAPMC enhancement needed
    -   get\_xname\_energy - CAPMC enhancement needed
    -   get\_xname\_energy\_stats - CAPMC enhancement needed
    -   get\_xname\_energy\_counter - CAPMC enhancement needed
-   **SCSD**
    -   Credential setting
    -   Certs creation - does this talk to Redfish?
    -   Certs deletion - does this talk to Redfish?
    -   Certs fetch - does this talk to Redfish?
    -   Certs setting

Accepts single xname, a list of xnames, or a hostlist as the target(s)
of the validation.

**rfepvalidator - Redfish Endpoint Validation Tool**

Compare responses from Redfish endpoint to a static description of what
the State Manager needs to fully discover a component.

-   Rosetta Switch Controllers
-   River NCN BMCs
-   River Compute Node BMCs
-   Mountain Chassis Controllers
-   Mountain Node Controllers**  
    **
-   Redfish event subscriptions - enhancement for HMCOLLECTOR
    validation, Mountain and River
-   Redfish telemetry subscriptions - enhancement for HMCOLLECTOR
    validation, Mountain only
-   Power and Temperature telemetry polling - enhancement for
    HMCOLLECTOR validation, River only

**switchval - Ethernet Switch Validation Tool**

-   TBD - Need input from
    <a href="https://connect.us.cray.com/confluence/display/~spresser" class="confluence-userlink user-mention">Steven Presser</a>

**CT Tests**

-   Continuous Test framework
-   Requires full Shasta stack
-   Executed manually one at a time from a CLI
-   Multiple deployment methods
    -   Docker container executing remote tests
    -   Deployed to NCNs via RPM
-   Smoke tests
    -   Services installed and running
    -   Bash scripts
    -   Check k8s pod status
    -   Checks HTTP status of API endpoints
-   Functional tests
    -   Tavern API tests
        -   Validates the API spec
        -   Validates correct responses
        -   Validates response contents
-   Validations:
    -   HSM  
        -   HSM Discovery/Inventory
        -   HSM FRU tracking
        -   Add list of HSM db fields we want covered - Enhancement to
            the HMS CT tests
    -   FAS
        -   Flash dry-run

**Hardware validation document**

-   Step by step instructions to execute
    -   Redfish Validation
    -   CT Tests
    -   Hardware Validation
    -   Ethernet Switch Validation
    -   Firmware upgrade/downgrade

## <span class="nh-number">4.2. </span>Interfaces

**hwval.py CLI**

    usage: hwval.py [-h] [-l LIST] [-x XNAMEs] [-t TESTS] [-v] [-V]

    Automatic hardware validation tool.

    optional arguments:
      -h, --help            show this help message and exit
      -l LIST, --list LIST  List modules and tests that are available. all: show
                            all modules and tests, top: show top level modules,
                            <module>: show tests for the module
      -x XNAMES, --xname XNAMES
                            Xnames to do hardware validation on. Xnames can be a
                            list: xname[,xname[,...]] or a hostlist: x1000c[0-7]s[0-7]b[0-1]n[0-1]
      -t TESTS, --tests TESTS
                            List of tests to execute in the form
                            <module>:<test>[,<module>:<test>[,...]]
      -v, --verbose         Increase output verbosity.
      -V, --version         Print the script version information and exit.

**rfepvalidator.py CLI**

See
<a href="https://stash.us.cray.com/projects/HMS/repos/hms-rfepvalidator/browse" class="external-link">Redfish Endpoint Validation Tool</a>
in Stash

**switchval.py CLI**

TBD

**CT Tests CLI**

See [HMS CT
Testing](https://connect.us.cray.com/confluence/display/CASMHMS/HMS+CT+Testing)

## <span class="nh-number">4.3. </span>Use Cases

1.  Existing hardware has new firmware available
    1.  Mountain controllers
        1.  cC
        2.  nC
    2.  River Nodes
        1.  BMC
    3.  Rosetta Switch controllers
        1.  sC
    4.  TOR Ethernet switch
2.  New TOR Ethernet switch
    1.  New vendor
    2.  New model
3.  New River NCN/UAN server
    1.  New vendor
    2.  New model
4.  New River Compute server
    1.  New vendor
    2.  New model
5.  New Mountain Compute blade
    1.  New vendor
    2.  New model
    3.  New CPUs
    4.  New GPUs

## <span class="nh-number">4.4. </span>Requirements Response

1.  Redfish validation able to run outside of the Shasta k8s environment
2.  No institutional knowledge needed to execute the tools
3.  Simple output for increased comprehension
4.  Listing of all validation routines on a tool-by-tool basis
5.  Ability to select individual validation routines and groups of
    routines
6.  One driver for all tools
7.  Individual tools executable as stand-alone entities
8.  IP address, xname, or NID as valid targets
9.  Multi-target capable
10. Capable of being executed using automation

## <span class="nh-number">4.5. </span>Changes

-   CAPMC
    -   Remove need for nodes to be in the Ready state for power cap
        calls
    -   Add new APIs for xname equivalents to power cap calls and energy
        queries
-   rfepvalidator
    -   Define minimum static description of a Redfish endpoint that
        would allow full discovery/inventory
    -   Add subscription and telemetry checks
-   hwval
    -   Remove unneeded power queries
    -   Add new validation modules

## <span class="nh-number">4.6. </span>Dependencies

-   python 2.7
-   docker/containerd
    -   rfepvalidator
-   Kubernetes
    -   hwval
    -   CT Tests

## <span class="nh-number">4.7. </span>Portability/Compatibility

-   v1 service APIs

## <span class="nh-number">4.8. </span>Performance/Scalability

N/A

## <span class="nh-number">4.9. </span>RAS/Robustness

N/A

## <span class="nh-number">4.10. </span>Programmability

N/A

## <span class="nh-number">4.11. </span>Productivity

Improves productivity of development when new hardware or firmware is
released.

## <span class="nh-number">4.12. </span>Configurability

N/A

## <span class="nh-number">4.13. </span>Security

-   hwval acquires an API token directly from k8s without additional
    authorization beyond the root login

## <span class="nh-number">4.14. </span>Build/Install/Packaging

-   *hwval*
    -   Available directly as a check-out from stash
    -   Install-able via an RPM
-   rfepvalidator
    -   Available directly as a check-out from stash and local/docker
        build
-   switchval
    -   Available directly as a check-out from stash
    -   Install-able via an RPM
-   CT Tests
    -   Available through CT pipeline docker container
    -   Install-able via an RPM

## <span class="nh-number">4.15. </span>Support/Maintainability

These tools are intended only for internal usage. Modular pieces enable
removal and addition of new validation efforts easily. Standard python
use allows for a flexible development environment.

## <span class="nh-number">4.16. </span>Risks

There are no risks with the development of the code. Without the new
validation tools, the risks include delays in future feature work,
support, and bug fixing.

## <span class="nh-number">4.17. </span>Other Issues

-   Currently only intended for HMS use

# <span class="nh-number">5. </span><u>Documentation</u>

-   A new document will be created that will cover the steps required to
    validation new hardware/firmware for HMS services

# <span class="nh-number">6. </span>Stakeholders

-   HMS Team

# <span class="nh-number">7. </span><u>Minutes</u>

-   <u>TBD</u>

# <span class="nh-number">8. </span>Appendix

## <span class="nh-number">8.1. </span>List of New Acronyms

-   BMC -
-   CAPMC - Cray Advanced Platform Monitor and Control
-   cC - Mountain Chassis Controller
-   CSM -
-   FAS - Firmware Action Service
-   FRU - Field Replaceable Unit
-   HMS - Hardware Management Services
-   HSM - Hardware State Manager
-   nC - Mountain Node Controller
-   NCN - Non-Compute Node
-   sC - Rosetta Switch Controller
-   UAN - User Access Node

## <span class="nh-number">8.2. </span>References

<span id="Department_Number"> </span>

<span id="Department_Number"></span>

Document generated by Confluence on Jan 14, 2022 07:17

[Atlassian](http://www.atlassian.com/)
