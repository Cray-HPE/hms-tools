# Hardware Validation Toolset

These tests assist the Hardware Management Services team by validating certain
aspects of the Redfish implementation are working in a way that the HMS software
is able to make use of them. The tests are designed to be run against a BMC that
is not necessarily connected to a Shasta system.

## Usage
### Setup
BMC=<hostname or IP>
LISTENIP=<IP address the BMC can POST to on the test server>
read -s PASSWD

### Power Capping
Perform a sequence of calls that will enable power capping, query the current
power capping information, set the power cap to Max-100, validate the power cap
is properly set, reset the power cap to the previous setting, and disable power
capping.

```
python test_power_capping.py -b $BMC -u root -p $PASSWD
if [ $? == 1 ]; then
    echo "Power cap validation failed."
fi
```

### Power Control
Perform a sequence of calls that will turn a node Off, validate it has turned
Off, then turn the node back On, and validate the node turned On. If the node is
already Off, the node will be turned On, validate it has turned On, then it will
be turned Off, and validate that it is Off.

A node may not turn Off in 5 minutes due to slow shutdown of the OS when a
graceful shutdown is requested. In these cases, the test will send a force Off
to the BMC to make sure the node is indeed Off.

A Redfish event server is brought up to catch the power Off and power On Redfish
events. Errors will be indicated if a Redfish event is received but the node
does not make it to the target power state.

```
python test_power_control.py -i $LISTENIP -r 45910 -b $BMC -u root -p $PASSWD
if [ $? == 1 ]; then
    echo "Power control validation failed."
fi
```

### Streaming Telemetry
Olympus BMCs stream their telemetry even if the nodes they manage are not
booted. This test will create a Redfish event server to catch the streaming
telemetry and then subscribe to streaming telemetry events at the BMC. If no
telemetry is received in 30 seconds the test fails.

This test is expected to fail on all River management, application, and
compute servers.

```
python test_streaming_telemetry.py -i $LISTENIP -r 45910 -b $BMC -u root -p $PASSWD
if [ $? == 1 ]; then
    echo "Streaming telemetry validation failed."
fi
```