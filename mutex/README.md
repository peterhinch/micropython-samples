# A very simple mutex class.

Files mutex.py mutex_test.py

A mutex is an object enabling threads of execution to protect critical sections of code from reentrancy
or to temporarily protect critical data sets from being updated by other threads. The term "mutex"
derives from the notion of mutual exclusion. A mutex usually provides three methods:

lock() (POSIX pthread_mutex_lock): wait until the mutex is free, then lock it  
unlock() (POSIX pthread_mutex_unlock): Immediate return. unlock the mutex.  
test() (POSIX pthread_mutex_trylock): Immediate return. test if it is locked.  

In this implementation lock and unlock is controlled by a context manager.

In the context of MicroPython a mutex provides a mechanism where an interrupt service routine (ISR) can
test whether the main loop was using critical variables at the time the interrupt occurred, and if so
avoid modifying those variables. Typical use is as follows:

```python
import pyb, mutex
mutex = mutex.Mutex()
data_ready = False

def callback(): # Timer or interrupt callback
    global data_ready
    if mutex.test():
        data_ready = True
        # Update critical variables
        mutex.release()
    else:
        # defer any update
# Associate callback with device (pin or timer)

while True:
    # code
    if data_ready:
        with mutex:
            data_ready = False
            # Access critical variables
    # more code
```
Note that the ``with`` statement will execute immediately because no other process runs a ``with`` block
on the same mutex instance.

[Linux man page](http://linux.die.net/man/3/pthread_mutex_lock)

References describing mutex and semaphore objects  
[geeksforgeeks](http://www.geeksforgeeks.org/mutex-vs-semaphore/)  
[stackoverflow](http://stackoverflow.com/questions/62814/difference-between-binary-semaphore-and-mutex)  
[differencebetween](http://www.differencebetween.net/language/difference-between-mutex-and-semaphore/)
