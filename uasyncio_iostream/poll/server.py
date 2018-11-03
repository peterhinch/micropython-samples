# Minimal stream based socket seerver. To test client exception handling. Can
# only handle a single client but will cope with client failure and reconnect.
# Run under MicroPython Unix build.

import usocket as socket
import utime
addr = socket.getaddrinfo('0.0.0.0', 8123)[0][-1]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(addr)
s.listen(1)

def run(write=True):
    try:
        while True:
            print('Awaiting connection.')
            try:
                conn, addr = s.accept()
            except OSError as er:
                print('Connect fail:', er.args[0])
                conn.close()
                continue

            print('Got connection from', addr)
            try:
                while True:
                    if write:
                        conn.send(b'0123456789\n')  # OSError on fail
                        utime.sleep(1)
                    else:
                        line = conn.readline()
                        if line == b'':
                            print('Connection fail')
                            break
                        else:
                            print(line)
            except OSError:
                conn.close()
    finally:
        conn.close()
        s.close()

print('run() to send lines of 11 bytes on port 8123,')
print('run(False) to read lines')
