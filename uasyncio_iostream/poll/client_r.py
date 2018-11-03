# client_r.py Test poll object's response to two fault conditions under Unix and ESP8266
import usocket as socket
import uasyncio as asyncio
import uselect as select

server_addr = socket.getaddrinfo('192.168.0.35', 8123)[0][-1]
s = socket.socket()
s.connect(server_addr)  # Expect OSError if server down
poller = select.poll()
poller.register(s, select.POLLIN)
s.setblocking(False)

success = False
async def run():
    global success
    ok = True
    try:
        while ok:
            res = poller.ipoll(10)
            for sock, ev in res:
                if ev & select.POLLIN:
                    r = sock.readline()
                    print(ev, r)
                    # A server outage prints 1, b'' forever on ESP8266 or Unix.
                    # If killer closes socket on ESP8266 ev is always 1,
                    # on Unix get ev == 32
                    # Never see 9 or 17 (base 10) which are the error responses expected by uasyncio
                    # (POLLIN & POLLERR or POLLIN & POLLHUP)
                else:  # The only way I can make it work (on Unix) is to quit on 32
                    print('Terminating event:', ev)  # What is 32??
                    ok = False
                    break
            await asyncio.sleep(0)
    except OSError:
        print('Got OSError')  # Never happens
    success = True  # Detected socket closure or error by OSError or event

async def killer():
    await asyncio.sleep(5)
    print('closing socket')
    s.close()
    for n in range(3, -1, -1):
        print('Shutdown in {}s'.format(n))  # Leave time for response from run()
        await asyncio.sleep(1)
    if success:
        print('Success: detected error/socket closure.')
    else:
        print('Failed to detect error/socket closure.')

loop = asyncio.get_event_loop()
loop.create_task(run())
try:
    loop.run_until_complete(killer())
finally:
    s.close()
