import numpy as np
import typing
from collections import namedtuple

Sample = namedtuple('Sample', 'ts, x, y')


class Filter:
    def __init__(self):
        self.timeWindow = 50
        self.distT      = 25
        self._Tfast     = .5
        self._Tslow     = 300
        self.TresetTime = 100       # 100 ms to exponentially go from Tfast to Tslow

        self._x         = np.nan
        self._y         = np.nan
        self._t         = 0.
        self._tLastStep = -np.inf
        self._interval  = None
        self._buffer: typing.List[Sample] = []
        self._Tacc      = None      # acceleration of exponential reset curve

        self._recalculateResetAcc()

    def _recalculateResetAcc(self):
        self._Tacc = 2*(self.Tslow-self.Tfast)/(100*100)

    @property
    def Tfast(self):
        return self._Tfast
    @Tfast.setter
    def Tfast(self, value):
        if value>=self._Tslow:
            raise RuntimeError('Tfast should be smaller than Tslow')
        self._Tfast = value
        self._recalculateResetAcc()
        
    @property
    def Tslow(self):
        return self._Tslow
    @Tslow.setter
    def Tslow(self, value):
        if self._Tfast>=value:
            raise RuntimeError('Tslow should be larger than Tfast')
        self._Tslow = value
        self._recalculateResetAcc()

    def add_sample(self, ts, x, y):
        # ts: timestamp in ms
        #  x: horizontal x position
        #  y: horizontal y position

        if np.isnan(self._x) and np.isnan(self._y) and self._t == 0:
            self._x = x
            self._y = y
            self._t = self.Tslow

        # if nan input, just return last value
        # TODO: optionally, if obj last value is too old (look at
        # latest sample in buffer compared to incoming timestamp),
        # stop showing data
        if np.isnan(x) or np.isnan(y):
            return self._x, self._y
            
        # add incoming data to buffer
        self._buffer.append(Sample(ts, x, y))

        # run through available data and divide up into time windows
        dt = np.array([ts-s.ts for s in self._buffer])
        # throw out data older than we're interested in
        remove = dt > 2*self.timeWindow
        self._buffer = [s for s,r in zip(self._buffer,remove) if not r]
        dt = dt[np.logical_not(remove)]

        # split up buffer into two time windows
        qdt = dt>self.timeWindow
        xs  = np.array([s.x for s in self._buffer])
        ys  = np.array([s.y for s in self._buffer])
        avgXB = xs[qdt].mean()
        avgYB = ys[qdt].mean()
        avgXA = xs[np.logical_not(qdt)].mean()
        avgYA = ys[np.logical_not(qdt)].mean()

        # if we swap to Tfast, we exponentially return to Tslow. We do
        # so over a hardcoded period of 100 ms. Compute current T
        # here
        if ts-self._tLastStep<=self.TresetTime:
            self._t = min(self.Tfast+.5*self._Tacc*(ts-self._tLastStep)**2, self.Tslow)
        else:
            self._t = self.Tslow
        # check for fast movement, reset T to Tfast if there is
        if not np.isnan(avgXA) and not np.isnan(avgXB):
            dist = np.hypot(avgXB-avgXA,avgYB-avgYA)
            if dist > self.distT:
                self._t          = self.Tfast
                self._tLastStep  = ts
        
        # if we don't know the sampling interval yet, determine it
        # from the data
        # check if we have enough data to start the filter. We do that by checking if we just threw out a sample because its too old, that means the buffer is fully filled.
        # (actually its ready one sample earlier, but thats hard to detect)
        validFilter = np.any(remove)
        if validFilter and self._interval is None and len(self._buffer)>1:
            self._interval  = -np.diff(dt).mean()

        # smooth based on new incoming sample
        if self._interval is not None:
            alpha = self._t / self._interval
            self._x = (x + alpha * self._x) / (1. + alpha)
            self._y = (y + alpha * self._y) / (1. + alpha)
        else:
            # return average of data we have seen so far, best we can
            # do until we have seen enough data to really go at it
            self._x = np.nanmean(xs)
            self._y = np.nanmean(ys)
        
        return self._x, self._y