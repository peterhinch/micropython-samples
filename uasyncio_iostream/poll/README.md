Context: uasyncio StreamReader and StreamWriter objects hang indefinitely under fault conditions.

Under fault conditions uasyncio expects to receive POLLERR or POLLHUP conditions from the poll instance. In my testing this never occurs.

Testing was of client connections. Socket type was SOCK_STREAM. Two fault conditions were tested:  
 1. Server outage.
 2. Socket closed by another coroutine.

Testing was performed with a server running under the Unix build. Clients were tested on:
 1. Unix build (on same machine as server).
 2. ESP8266.
 3. ESP32.

Results were as follows. Numbers represent the event no. received from the poll instance. "No trigger" means that the poll instance produced no response after the fault. On all platforms where the client was reading, a server outage produced a POLLIN (1) response. On all but ESP32 this repeated indefinitely causing the client endlessly to read empty bytes objects.

Numbers are base 10. Mode refers to the client mode. Expected refers to uasyncio.

| Mode  | Platform | Outage  | Closure    | Expected |
|:-----:|:--------:|:-------:|:----------:|:--------:|
| Read  | Unix     | 1       | 32         | 9 or 17  |
| Read  | ESP8266  | 1       | No trigger | 9 or 17  |
| Read  | ESP32    | 1 (once)| No trigger | 9 or 17  |
| Write | Unix     | OSError | 32         | 12 or 20 |
| Write | ESP8266  | OSError | No trigger | 12 or 20 |
| Write | ESP832   | OSError | No trigger | 12 or 20 |

1 == POLLIN  
4 == POLLOUT  
9 == (POLLIN & POLLERR)  
17 == (POLLIN & POLLHUP)  
12 == (POLLOUT & POLLERR)  
20 == (POLLOUT & POLLHUP)  
32 == I have no idea.

Test scripts may be found here:  
[Server - can run in read or write mode](https://github.com/peterhinch/micropython-samples/blob/master/uasyncio_iostream/poll/server.py)  
[Read client](https://github.com/peterhinch/micropython-samples/blob/master/uasyncio_iostream/poll/client_r.py)  
[Write client](https://github.com/peterhinch/micropython-samples/blob/master/uasyncio_iostream/poll/client_w.py)
