# Tests for uasyncio iostream read/write changes

These tests perform concurrent input and output and use timers to
emulate read/write hardware.  
iotest1.py Device can perform unbuffered writes only.  
iotest2.py Device performs buffered writes and unbuffered reads.  
iotest4.py Run test(False) for unbuffered writes and buffered reads.  
iotest5.py Unbuffered read and write.  

Obsolete test:  
iotest3.py Demonstrated workround for failing concurrent I/O using separate
input and output objects.  

Other tests:  
iotest.py Measure timing of I/O scheduling with a scope.  
auart.py Run a loopback test on a physical UART.  
auart_hd.py Simulate a pair of devices running a half-duplex protocol over a
pair of UARTs.
