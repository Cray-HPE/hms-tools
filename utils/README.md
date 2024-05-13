# Hardware Utility Toolset

These scripts assist in getting information from the Hardware.

## Redfish Subscriptions

The script `rf-subscriptions.py` supports creating a subscription and then
listening to events for that subscription.

This script has only been tested with liquid-cooled hardware. Some old air
cooled hardware won't work because the redfish implementation does not
allow the script to create a subscription. It is probably rejecting a
call back that includes a port number.

### Setup

Set the BMC hostname or IP. This is usually the xname.
```
BMC=<hostname or IP>
```
Set the password to the BMC.
```
read -s PASSWD
```
Get the IP address to use for the environment variable LISTENIP
```
ip addr show | egrep hmn0
```
```
LISTENIP=<IP address the BMC can POST to on the test server>
```

Optional: Setup certificates. Some redfish implementations require
that the callback use `https` instead of `http`. This script
has not been tested with `https` subscriptions. Using `https` likely
requires certificates. Certificates can be setup using:
[gen-certs.sh](../hwval/gen-certs.sh)

### Start the Subscription Listener

```
rf-subscriptions.py listen -i $LISTENIP -r 45910 -b $BMC -u root -p $PASSWD
```

### Create a Subscription

Create a subscription for normal events, such as power on and off events.
```
rf-subscriptions.py create -i $LISTENIP -r 45910 -b $BMC -u root -p $PASSWD
```

Create a subscription for telemetry information.
```
rf-subscriptions.py create -i $LISTENIP -r 45910 -b $BMC -u root -p $PASSWD -t
```

### List Subscriptions

```
rf-subscriptions.py list -b $BMC -u root -p $PASSWD
```

### Delete Subscriptions

This will delete any subscriptions that were created by the script `rf-subscriptions.py`
```
rf-subscriptions.py delete -b $BMC -u root -p $PASSWD
```
