# ledflash, pause, instrument, roundrobin work

# Lightweight threading library for the micropython board.
# Author: Peter Hinch
# V1.03 Implements gc
# Copyright Peter Hinch 2016 Released under the MIT license

import pyb, micropython, gc
micropython.alloc_emergency_exception_buf(100)

# TIMER ACCESS

TIMERPERIOD = 0x7fffffff                        # 35.79 minutes 2148 secs
MAXTIME     = TIMERPERIOD//2                    # 1073 seconds maximum timeout
MAXSECS     = MAXTIME//1000000

class TimerException(Exception) : pass

def microsWhen(timediff):                       # Expected value of counter in a given no. of uS
    if timediff >= MAXTIME:
        raise TimerException()
    return (pyb.micros() + timediff) & TIMERPERIOD

def microsSince(oldtime):                       # No of uS since timer held this value
    return (pyb.micros() - oldtime) & TIMERPERIOD

def after(trigtime):                            # If current time is after the specified value return
    res = ((pyb.micros() - trigtime) & TIMERPERIOD) # the no. of uS after. Otherwise return zero
    if res >= MAXTIME:
        res = 0
    return res

def microsUntil(tim):                           # uS from now until a specified time (used in Delay class)
    return ((tim - pyb.micros()) & TIMERPERIOD)

def seconds(S):                                 # Utility functions to convert to integer microseconds
    return int(1000000*S)

def millisecs(mS):
    return int(1000*mS)

# WAITFOR CLASS
# This is a base class. User threads should use classes derived from this.

class Waitfor(object):
    def __init__(self):
        self.uS = 0                             # Current value of timeout in uS
        self.timeout = microsWhen(0)            # End value of microsecond counter when TO has elapsed
        self.forever = False                    # "infinite" time delay flag
        self.irq = None                         # Interrupt vector no
        self.pollfunc = None                    # Function to be called if we're polling
        self.pollfunc_args = ()                 # Arguments for the above
        self.customcallback = None              # Optional custom interrupt handler
        self.interruptcount = 0                 # Set by handler, tested by triggered()
        self.roundrobin = False                 # If true reschedule ASAP

    def triggered(self):                        # Polled by scheduler. Returns a priority tuple or None if not ready
        if self.irq:                            # Waiting on an interrupt
            self.irq.disable()                  # Potential concurrency issue here (????)
            numints = self.interruptcount       # Number of missed interrupts
            if numints:                         # Waiting on an interrupt and it's occurred
                self.interruptcount = 0         # Clear down the counter
            self.irq.enable()
            if numints:
                return (numints, 0, 0)
        if self.pollfunc:                       # Optional function for the scheduler to poll
            res = self.pollfunc(*self.pollfunc_args) # something other than an interrupt
            if res is not None:
                return (0, res, 0)
        if not self.forever:                    # Check for timeout
            if self.roundrobin:
                return (0,0,0)                  # Priority value of round robin thread
            res = after(self.timeout)           # uS after, or zero if not yet timed out in which case we return None
            if res:                             # Note: can never return (0,0,0) here!
                return (0, 0, res)              # Nonzero means it's timed out
        return None                             # Not ready for execution

    def _ussetdelay(self, uS=None):             # Reset the timer by default to its last value
        if uS:                                  # If a value was passed, update it
            self.uS = uS
        self.timeout = microsWhen(self.uS)      # Target timer value
        return self

    def setdelay(self, secs=None):              # Method used by derived classes to alter timer values
        if secs is None:                        # Set to infinity
            self.forever = True
            return self
        else:                                   # Update saved delay and calculate a new end time
            if secs <= 0 or secs > MAXSECS:
                raise ValueError('Invalid time delay')
            self.forever = False
            return self._ussetdelay(seconds(secs))

    def __call__(self):                         # Convenience function allows user to yield an updated
        if self.uS:                             # waitfor object
            return self._ussetdelay()
        return self

    def intcallback(self, irqno):               # Runs in interrupt's context.
        if self.customcallback:
            self.customcallback(irqno)
        self.interruptcount += 1                # Increments count to enable trigger to operate

class Roundrobin(Waitfor):                      # Compatibility only. A thread yielding a Roundrobin
    def __init__(self):                         # will be rescheduled as soon as priority threads have been serviced
        super().__init__()
        self.roundrobin = True

# Intended for device drivers
class Timeout(Waitfor):
    def __init__(self, tim):
        super().__init__()
        self.setdelay(tim)

# yield from wait
def wait(secs):
    if secs <=0 :
        raise TimerException()
    count, tstart = divmod(secs, MAXSECS)
    overshoot = 0
    if tstart > 0:
        res = yield Timeout(tstart)
        overshoot = res[2]
    while count:
        res = yield Timeout(MAXSECS)
        overshoot += res[2]
        count -= 1
    return (0, 0, overshoot)

# Block on an interrupt from a pin subject to optional timeout
class Pinblock(Waitfor):
    def __init__(self, pin, mode, pull, customcallback = None, timeout = None):
        super().__init__()
        self.customcallback = customcallback
        if timeout is None:
            self.forever = True
        else:
            self.setdelay(timeout)
        self.irq = pyb.ExtInt(pin, mode, pull, self.intcallback)

class Poller(Waitfor):
    def __init__(self, pollfunc, pollfunc_args = (), timeout = None):
        super().__init__()
        self.pollfunc   = pollfunc
        self.pollfunc_args = pollfunc_args
        if timeout is None:
            self.forever = True
        else:
            self.setdelay(timeout)

# SCHEDULER CLASS

class Sched(object):
    GCTIME = const(50000)
    DEAD = const(0)
    RUNNING = const(1)
    PAUSED = const(2)
    YIELDED = const(0)
    FUNC = const(1)
    PID = const(2)
    STATE = const(3)
    DUE = const(4)
    def __init__(self, gc_enable = True):
        self.lstThread = []                     # Entries contain [Waitfor object, function, pid, state]
        self.bStop = False
        self.last_gc = 0
        self.pid = 0
        self.gc_enable = gc_enable

    def __getitem__(self, pid):                 # Index by pid
        threads = [thread for thread in self.lstThread if thread[PID] == pid]
        if len(threads) == 1:
            return threads[0]
        elif len(threads) == 0:
            raise ValueError('Unknown thread ID {}'.format(pid))
        else:
            raise OSError('Scheduler fault: duplicate thread {}'.format(pid))

    def stop(self, pid=0):
        if pid == 0:
            self.bStop = True                   # Kill _runthreads method
            return
        self[pid][STATE] = DEAD

    def pause(self, pid):
        self[pid][STATE] = PAUSED

    def resume(self, pid):
        self[pid][STATE] = RUNNING

    def add_thread(self, func):                 # Thread list contains [Waitfor object, generator, pid, state]
        self.pid += 1                           # Run thread to first yield to acquire a Waitfor instance
        self.lstThread.append([func.send(None), func, self.pid, RUNNING, True]) # and put the resultant thread onto the threadlist
        return self.pid

    def _idle_thread(self):                     # Runs once then in roundrobin or when there's nothing else to do
        if self.gc_enable and (self.last_gc == 0 or microsSince(self.last_gc) > GCTIME):
            gc.collect()
            self.last_gc = pyb.micros()

    def triggered(self, thread):
        wf = thread[YIELDED]
        if wf is None:
            return (0, 0, 0)                    # Roundrobin
        if isinstance(wf, Waitfor):
            return wf.triggered()
        try:
            tim = float(wf)
        except ValueError:
            raise ValueError('Thread yielded an invalid object')
        waitfor = Timeout(tim)
        thread[YIELDED] = waitfor
        return waitfor.triggered()

    def _runthread(self, thread, priority):
        try:                                    # Run thread, send (interrupt count, poll func value, uS overdue)
            thread[YIELDED] = thread[FUNC].send(priority)  # Store object yielded by thread
        except StopIteration:                   # The thread has terminated:
            thread[STATE] = DEAD                # Flag thread for removal

    def _get_thread(self):
        p_run = None                        # priority tuple of thread to run
        thr_run = None                      # thread to run
        candidates = [t for t in self.lstThread if t[STATE] == RUNNING]
        for thread in candidates:
            priority = self.triggered(thread)
            if priority is not None:        # Ignore threads waiting on time or event
                if priority == (0,0,0):     # Roundrobin (RR)
                    if thr_run is None and thread[DUE]:
                        p_run = priority    # Assign one, don't care which
                        thr_run = thread
                else:
                    if p_run is None or priority > p_run:
                        p_run = priority
                        thr_run = thread
        return thr_run, p_run


    def _runthreads(self):
        while not self.bStop:
            thr_run, p_run = self._get_thread()
            if thr_run is None:                 # All RR's have run, anything else is waiting
                return
            self._runthread(thr_run, p_run)
            thr_run[DUE] = False                # Only care if RR

    def run(self):                              # Returns if the stop method is used or all threads terminate
        while not self.bStop:
            self.lstThread = [thread for thread in self.lstThread if thread[STATE] != DEAD] # Remove dead threads
            self._idle_thread()                 # Garbage collect
            if len(self.lstThread) == 0:
                return
            for thread in self.lstThread:
                thread[DUE] = True              # Applies only to roundrobin
            self._runthreads()                  # Returns when all RR threads have run once
