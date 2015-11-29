import pyb, mutex

mutex = mutex.Mutex()

def update(t):                  # Interrupt handler may not be able to acquire the lock
    global var1, var2           # if main loop has it
    if mutex.test():            # critical section start
        var1 += 1
        pyb.udelay(200)
        var2 += 1
        mutex.release()         # critical section end

def main():
    global var1, var2
    var1, var2 = 0, 0
    t2 = pyb.Timer(2, freq = 995, callback = update)
    t4 = pyb.Timer(4, freq = 1000, callback = update)
    for x in range(1000000):
        with mutex:             # critical section start
            a = var1
            pyb.udelay(200)
            b = var2
            result = a == b     # critical section end
        if not result:
            print('Fail after {} iterations'.format(x))
            break
        pyb.delay(1)
        if x % 1000 == 0:
            print(x)
    t2.deinit()
    t4.deinit()
    print(var1, var2)
