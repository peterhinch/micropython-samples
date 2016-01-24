# Program to test/demonstrate consistency of results from getcal()
from array import array
from ds3231_pb import DS3231

# This takes 12.5 hours to run: to sve you the trouble here are results from one sample of Pyboard.

# Mean and standard deviation of RTC correction factors based on ten runs over different periods.
# Conclusion: for the best possible accuracy, run for 20 minutes. However a ten minute run gave
# a result within 2ppm (one minute/yr).
# >>> test()
# t =  5 -174 -175 -175 -172 -175 -175 -172 -174 -175 -172  avg -173.8 sd   1.3
# t = 10 -175 -175 -175 -175 -173 -175 -176 -175 -174 -175  avg -174.8 sd   0.7
# t = 20 -175 -175 -175 -175 -174 -175 -175 -175 -175 -174  avg -174.8 sd   0.4
# t = 40 -175 -175 -175 -174 -174 -175 -174 -174 -175 -174  avg -174.4 sd   0.5

def test():
    NSAMPLES = 10
    a = DS3231()
    for t in (5, 10, 20, 40):
        values = array('f', (0 for z in range(NSAMPLES)))
        print('t = {:2d}'.format(t), end = '')
        for x in range(NSAMPLES):
            cal = a.getcal(t)
            values[x] = cal
            print('{:5d}'.format(cal), end = '')
        avg = sum(values)/NSAMPLES
        sd2 = sum([(v -avg)**2 for v in values])/NSAMPLES
        sd = sd2 ** 0.5
        print('  avg {:5.1f} sd {:5.1f}'.format(avg, sd))
