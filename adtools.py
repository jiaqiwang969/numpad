import os
import sys
sys.path.append(os.path.realpath('..')) # for running unittest
import unittest
import numpy as np
import scipy.sparse as sp
from numpad.adarray import *
from numpad.adsolve import *

class interp:
    '''
    1D interpolation
    y = interp(x0, y0, type)  # type can be 'linear' (default) or 'cubic'.
    y(x)                      # interpolate at x
    y.derivative(x)           # derivative of interpolant
    '''
    def __init__(self, x0, y0, type='linear'):
        assert (base(x0)[1:] > base(x0)[:-1]).all()
        x0, y0 = array(x0), array(y0)
        self.x0 = x0.copy()
        if type == 'linear':
            self.y0 = y0[:,np.newaxis].copy()
        elif type == 'cubic':
            y0p = solve(self.cspline_resid, zeros(y0.size), (x0, y0),
                        verbose=False)
            self.y0 = transpose([y0, y0p])
        else:
            raise ValueError('interp: unknown type {0}'.format(type))

    def cspline_resid(self, yp, x, y):
        dx = (x[1:] - x[:-1])
        slope = (y[1:] - y[:-1]) / dx
        curv_L = (6 * slope - 4 * yp[:-1] - 2 * yp[1:]) / dx
        curv_R = (4 * yp[1:] + 2 * yp[:-1] - 6 * slope) / dx
        return hstack([curv_L[:1], curv_L[1:] - curv_R[:-1], -curv_R[-1:]])

    def find(self, x):
        'which interval to look at?'
        i = np.searchsorted(base(self.x0), base(x))
        np.maximum(i, 1, i)
        np.minimum(i, self.x0.size - 1, i)
        x0, x1 = self.x0[i - 1], self.x0[i]
        y0, y1 = self.y0[i - 1], self.y0[i]
        return x0, x1, y0, y1

    def __call__(self, x):
        shape = x.shape
        x = ravel(x)
        x0, x1, y0, y1 = self.find(x)

        x_x0 = (x - x0) / (x1 - x0)
        x_x1 = 1 - x_x0
        y = x_x0 * y1[:,0] + x_x1 * y0[:,0]
        if self.y0.shape[1] == 2:
            slope = (y1[:,0] - y0[:,0]) / (x1 - x0)
            y += (x_x0 - 2*x_x0**2 + x_x0**3) * (y0[:,1] - slope) * (x1 - x0) \
               + (x_x1 - 2*x_x1**2 + x_x1**3) * (y1[:,1] - slope) * (x0 - x1)
        return y.reshape(shape)

    def derivative(self, x):
        x0, x1, y0, y1 = self.find(x)

        yp = (y1[:,0] - y0[:,0]) / (x1 - x0)
        if self.y0.shape[1] == 2:
            x_x0 = (x - x0) / (x1 - x0)
            x_x1 = 1 - x_x0
            slope = (y1[:,0] - y0[:,0]) / (x1 - x0)
            yp += (1 - 4*x_x0 + 3*x_x0**2) * (y0[:,1] - slope) \
                + (1 - 4*x_x1 + 3*x_x1**2) * (y1[:,1] - slope)
        return yp


class SanityCheck(unittest.TestCase):
    def testMatch(self):
        N = 11
        x0 = random.rand(N); x0.sort()
        y0 = random.rand(N)
        for interp_type in ('linear', 'cubic'):
            y = interp(x0, y0, interp_type)
            x = x0.copy()
            self.assertAlmostEqual(abs(base(y(x) - y0)).max(), 0)

    def testLinear(self):
        N = 11
        x0 = arange(N)
        y0 = arange(N)
        y0[-1] = 0
        for interp_type in ('linear',):
            y = interp(x0, y0, interp_type)
            x = linspace(-1, N-2, 10000)
            self.assertAlmostEqual(abs(base(y(x) - x)).max(), 0)

    def testMatchDeriv(self):
        N = 11
        x0 = random.rand(N); x0.sort()
        y0 = random.rand(N)
        y = interp(x0, y0, 'cubic')
        x = x0.copy()

        yp0 = base(y.y0[:,1])
        yp1 = base(y.derivative(x))
        yp2 = np.diag(y(x).diff(x).todense())
        self.assertAlmostEqual(abs(yp1 - yp0).max(), 0)
        self.assertAlmostEqual(abs(yp2 - yp0).max(), 0)


if __name__ == '__main__':
    unittest.main()
