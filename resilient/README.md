# Resilient MicroPython WiFi code

This document is intended as a general design guide. A specific solution for
many IOT applications may be found [here](https://github.com/peterhinch/micropython-iot.git).

The following is based on experience with the ESP8266. It aims to show how
to design responsive bidirectional networking applications which are resilent:
they recover from WiFi and server outages and are capable of long term running
without crashing.

It is possible to write resilient code for ESP8266, but little existing code
takes account of the properties of wireless links and the limitations of the
hardware. On bare metal, in the absence of an OS, it is necessary to detect
outages and initiate recovery to ensure that consistent program state is
maintained and to avoid crashes and `LmacRxBlk` errors.

Radio links are inherently unreliable. They can be disrupted by sporadic RF
interference, especially near the limits of range. A mobile device such as a
robot can move slowly out of range and then back in again. The access point
(AP) can suffer an outage as can the application code at the other end of the
link. An application intended for long term running on a WiFi connected device
should be able to recover from such events. Brief outages are common. In a
house whose WiFi is reliable as experienced on normal devices, outages occur
at a rate of around 20 per day.

The brute-force approach of a hardware watchdog timer has merit for recovering
from crashes but the use of a hard reset implies the loss of program state. A
hardware or software watchdog does not remove the need to perform continuous
monitoring of connectivity. In the event of an outage code may continue to run
feeding the watchdog; when the outage ends the ESP8266 will reconnect but the
application will be in an arbitrary state. Further, sockets may be left open
leading to `LmacRxBlk` errors and crashes.

# 1. Abstract

Many applications keep sockets open for long periods during which connectivity
may temporarily be lost. The socket may raise an exception but this is not
guaranteed: in cases of WiFi outage, loss of connectivity cannot be determined
from the socket state.

Detecting an outage is vital to ensure sockets are closed and to enable code at
both endpoints to initiate recovery; also to avoid crashes caused by writing
to a socket whose counterpart is unavailable.

It seems that the only sure way to detect an outage is for each endpoint
regularly to send data, and for the receiving endpoint to implement a read
timeout.

Failure correctly to detect and recover from WiFi disruption is a major cause
of unreliability in ESP8266 applications.

A demo is provided of a system where multiple ESP8266 clients communicate with
a wired server with low latency full duplex links. This has run for extended
periods with mutiple clients without issue. The demo is intended to illustrate
the minimum requirements for a resilient system.

# 2. Hardware

There are numerous poor quality ESP8266 boards. There can also be issues caused
by inadequate power supplies. I have found the following to be bomb-proof:
 1. [Adafruit Feather Huzzah](https://www.adafruit.com/product/2821)
 2. [Adafruit Huzzah](https://www.adafruit.com/product/2471)
 3. [WeMos D1 Mini](https://wiki.wemos.cc/products:d1:d1_mini) My testing was
 on an earlier version with the metal cased ESP8266.

# 3. Introduction

I became aware of the issue when running the official umqtt clients on an
ESP8266. Despite being one room away from the AP the connection seldom stayed
up for more than an hour or two. This in a house where WiFi as percieved by
PC's and other devices is rock-solid. Subsequent tests using the code in this
repo have demonstrated that brief outages are frequent.

I developed a [resilient MQTT driver](https://github.com/peterhinch/micropython-mqtt.git)
which is capable of recovering from WiFi outages. This is rather complex, in
part because of the requirements of MQTT.

The demo code in this repo aims to establish the minimum requirements for a
resilient bidirectional link between an application on a wired server and a
client on an ESP8266. If a loss of connectivity occurs for any reason,
communication pauses for the duration, resuming when the link is restored.

# 4. Application design

The two problems which must be solved are detection of an outage and ensuring
that, when the outage ends, both endpoint applications can resume without loss
of program state.

While an ESP8266 can detect a local loss of WiFi connectivity detection of link
deterioration or of failure of the remote endpoint is more difficult.

To enable a WiFi device to cope with outages there are three approaches of
increasing sophistication.

 1. Brief connection: the device code runs an infinite loop. It periodically
 waits for WiFi availability, connects to the remote, does its job and
 disconnects. The hope is that WiFi failure during the brief period of
 connection is unlikely. Program state is maintained. Advantage: outage
 detection is avoided. Drawbacks: unlikely is not impossible. The device cannot
 respond quickly to data from the remote
 2. Hard reset: this implies detecting in code an outage of WiFi or of the
 remote and triggering a hard reset. This implies a loss of program state.
 3. Resilient connection. This is the approach discussed here, where an outage
 is detected. The code on each endpoint recovers when connectivity resumes.
 Program state after recovery is consistent.

In the first two options the remote endpoint loops: it waits for a connection,
acquires the data, then closes the connection.

## 4.1 Outage detection

At low level communication is via sockets linking two endpoints. In the case
under discussion the endpoints are on physically separate hardware, at least
one device being physically connected by WiFi. Each endpoint has a socket
instance with both sharing a port. If one endpoint closes its socket, the other
gets an exception which should be handled appropriately - especially by closing
its socket.

Based on experience with the ESP8266, WiFi failures seldom cause exceptions to
be thrown. Consider a nonblocking socket performing reads from a device. In an
outage the socket will behave in the same way as during periods when it waits
for data to arrive. During an outage, writes to a nonblocking socket will
proceed normally until the ESP8266 buffers fill, provoking the dreaded
`LmacRxBlk:1` messages.

The `isconnected()` method is inadequate for detecting outages as it is a
property of the interface rather than the link. If two WiFi devices are
communicating, one may lose `isconnected()` owing to local radio conditions. If
the other end tried to assess connectivity with `isconnected()` it would
incorrectly conclude that there was no problem. Further, the method is unable
to detect outages caused by program failure on the remote endpoint.

The only reliable way to detect loss of connectivity appears to be by means of
timeouts, in particuar on socket reads. To keep a link open a minimum interval
between data writes must be enforced. The endpoint performing the read times
the interval between successful reads: if this exceeds a threshold the link is
presumed to have died and a recovery process initiated.

This implies that WiFi applications which only send data cannot reliably deal
with outages: to create a resilient link both ends need to wait on a read while
checking for a timeout. A device whose network connection is via WiFi can
sometimes get early notification of an outage with `isconnected()` but this is
only an adjunct to the read timeout.

When a wireless device detects an outage it should ensure that the other end of
the link also detects it so that sockets may be closed and connectivity may be
restored when the WiFi recovers. This means that it avoid sending data for a
period greater than the timeout period.

A further requirement for ESP8266 is to limit the amount of data put into a
socket while the remote endpoint is down: excessive data quantities can provoke
`LmacRxBlk` errors. I have not quantified this, but in general if N packets are
sent in each timeout interval there will be a maximum pemissible size for a
packet. The timeout interval will therefore be constrained by the maximum
throughput required.

## 4.2 Timeout value

The demo uses timeouts measured in seconds, enabling prompt recovery from
outages. The assumption is that all devices share a local network. If the
server is on the internet longer timeouts will be required.

To preserve reliability the amount of data sent during the timeout period must
be controlled. If connectivity is lost immediately after a keepalive, the loss
will be undetected until the timeout has elapsed. Any data sent during that
period will be buffered by the ESP8266 vendor code. Too much will lead to
`LmacRxBlk` and probable crashes. What constitutes "excessive" is moot:
experimentation is required.

## 4.3 Recovery

The demo system employs the following procedure for recovering from outages.
The wirelessly connected client behaves as follows.

All coroutines accessing the interface are cancelled, and all open sockets are
closed: this is essential to avoid `LmacRxBlk:1` messages and crashes. The WiFi
connection is downed.

The client then periodically attempts to reconnect to WiFi. On success it
checks that local WiFi connectivity remains good for a period of double the
timeout. During this period no attempt is made to send or receive data. This
ensures that the remote device will also detect an outage and close its
sockets. The procedure also establishes confidence that the WiFi as seen by the
client is stable.

At the end of this period the client attempts to re-establish the connection,
repeating the recovery procedure on failure. The server responds to the loss of
connectivity by closing the connection and the sockets. It responds to the
reconnection as per a new connection.

# 5. Demo system

This demo is of a minimal system based on nonblocking sockets. It is responsive
in that each endpoint can respond immediately to a packet from its counterpart.
WiFi connected clients can run indefinitely near the limit of wireless range;
they automatically recover from outages of the WiFi and of the remote endpoint.

The application scenario is of multiple wirelessly connected clients, each
communicating with its own application object running on a wired server. 
Communication is asynchronous and full-duplex (i.e. communication is
bidirectional and can be initiated asynchronously by either end of the link).

A data packet is a '\n' terminated line of text. Blank lines are reserved for
keepalive packets. The demo application uses JSON to serialise and exchange
arbitrary Python objects.

The demo comprises the following files:  
 1. `server.py` A server for MicroPython Unix build on a wired network
 connection.
 2. `application.py` Server-side application demo.
 3. `client_w.py` A client for ESP8266.
 4. `client_id.py` Each client must have a unique ID provided by this file.
 Also holds server IP and port number.
 5. `primitives.py` A stripped down version of
 [asyn.py](https://github.com/peterhinch/micropython-async/blob/master/asyn.py)
 This is used by server and client. The aim is RAM saving on ESP8266.

## 5.1 The client

The principal purpose of the demo is to expose the client code. A more usable
version could be written where the boilerplate code was separated from the
application code, and I will do this. This version deliberately lays bare its
workings for study.

It is started by instantiating a `Client` object. The constructor assumes
that the ESP8266 will auto-connect to an existing network. It starts a `run()`
coroutine which executes an infinite loop, initially waiting for a WiFi
connection. It then launches `reader` and `writer` coroutines. The `writer`
coro periodically sends a JSON encoded list, and the remote endpoint does
likewise.

The client's `readline()` function times out after 1.5 seconds, issuing an
`OSError`. If this occurs, the `reader` coro terminates clearing the `.rok`
(reader OK) flag. This causes the `run()` to terminate the `writer`
(and `_keepalive`) coros. When all coros have died, `run()` downs the WiFi for
double the timeout period to ensure that the remote will detect and respond to
the outage. The loop then repeats, attempting again to establish a connection.

The `writer` coro has similar logic ensuring that if it encounters an error the
other coros will be terminated.

Both `reader` and `writer` start by instantiating a socket and connecting to
the appropriate port. The socket is set to nonblocking and the unique client ID
(retrieved from `client_id.py`) is sent to the server. This enables the server
to associate a connection with a specific client.

When `writer` has connected to the server it starts the `_keepalive` method:
this sends a blank line at a rate guaranteed to ensure that at least one will
be sent every timeout interval.

The server also sends a blank line priodically. This serves to reset the
timeout on the `readline()` method the client, preventing a timeout from
occuring. Thus outage detection is effectively transparent: client and server
applications can send data at any rate.

## 5.2 The application

In this demo the application is assumed to reside on the server machine. This
enables a substantial simplification with the timeout, keepalive and error
handling being devolved to the server.

In this demo upto 4 clients with ID's 1-4 are each served by an instance of
`App`. However they could equally be served by different application classes.
When an `App` is instantiated the `start()` coro runs which waits for the
server to establish a connection with the correct client. It retrieves the
connection, starts `reader` and `writer` coros, and quits.

The `reader` and `writer` coros need take no account of link status. They
communicate using server `readline()` and `write()` methods which will pause
for the duration of any outage.

## 5.3 The server

The application starts the server by launching the `server.run` coro. The
argument defines the read timeout value which should be the same as that on the
client. The value (in ms) determines the keepalive rate and the minimum
downtime of an outage.

The `server.run` coro runs forever awaiting incoming connections. When one
occurs a socket is created and a line containing the client ID is read. If the
client ID is not in the dictionary of clients (`Connection.connections`) a
`Connection` is instantiated for that client and placed in the dictionary. On
subsequent connections of that client, the `Connection` will be retrieved from
the dictionary. This is done by classmethod `Connection.go`, which assigns the
socket to that `Connection` instance.

The server provides `readline` and `write` methods. In the event of an outage
they will pause for the duration. Message transmission is not guaranteed: if an
outage occurs after tansmission has commenced, the message will be lost.

In testing through hundreds of outages, no instances of corrupted or partial
messages occurred. Presumably TCP/IP ensures this.
