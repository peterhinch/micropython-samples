# application.py

# Released under the MIT licence.
# Copyright (C) Peter Hinch 2018

# The App class emulates a user application intended to service a single
# client. In this case we have four instances of the application servicing
# clients with ID's 1-4.

import uasyncio as asyncio
loop = asyncio.get_event_loop(runq_len=32, waitq_len=32)
import ujson
import server

class App():
    def __init__(self, client_id):
        self.client_id = client_id
        self.data = [0, 0]  # Exchange a 2-list with remote
        loop = asyncio.get_event_loop()
        loop.create_task(self.start(loop))

    async def start(self, loop):
        print('Client {} Awaiting connection.'.format(self.client_id))
        conn = None
        while conn is None:
            await asyncio.sleep_ms(100)
            conn = server.client_conn(self.client_id)
        loop.create_task(self.reader(conn))
        loop.create_task(self.writer(conn))

    async def reader(self, conn):
        print('Started reader')
        while True:
            # Attempt to read data: server times out if none arrives in timeout
            # period closing the Connection. .readline() pauses until the
            # connection is re-established.
            line = await conn.readline()
            self.data = ujson.loads(line)
            # Receives [restart count, uptime in secs]
            print('Got', self.data, 'from remote', self.client_id)

    # Send [approx application uptime in secs, received client uptime]
    async def writer(self, conn):
        print('Started writer')
        count = 0
        while True:
            self.data[0] = count
            count += 1
            print('Sent', self.data, 'to remote', self.client_id)
            print()
            # .write() behaves as per .readline()
            await conn.write('{}\n'.format(ujson.dumps(self.data)))
            await asyncio.sleep(5)
        

clients = [App(n) for n in range(1, 5)]  # Accept 4 clients with ID's 1-4
try:
    loop.run_until_complete(server.run(timeout=1500))
except KeyboardInterrupt:
    print('Interrupted')
finally:
    print('Closing sockets')
    for s in server.socks:
        s.close()
