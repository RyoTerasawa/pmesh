from ._window import ResampleWindow as _ResampleWindow

import numpy
from numpy.lib.stride_tricks import as_strided

def _mkarr(var, shape, dtype):
    var = numpy.asarray(var, dtype=dtype)
    if numpy.isscalar(shape):
        shape = (int(shape),)

    if len(var.shape) == 0:
        return as_strided(var, shape=shape, strides=[0] * len(shape))
    else:
        r = numpy.empty(shape, dtype)
        r[...] = var
        return r

class Affine(object):
    """ Defines an affine Transformation, used by ResampleWindow.

        Parameters
        ----------
            translate : array_like, in integer mesh units.
            period : array_like in integer mesh units.
            scale : factor that multiples on position to obtain mesh units.

    """
    def __init__(self, ndim, scale=None, translate=None, period=None):
        if scale is None:
            scale = 1.0
        if translate is None:
            translate = 0
        if period is None:
            period = 0

        scale = _mkarr(scale, ndim, 'f8' )
        period = _mkarr(period, ndim, 'intp')
        translate = _mkarr(translate, ndim, 'f8')

        self.scale = scale
        self.translate = translate
        self.period = period
        self.ndim = ndim

    def shift(self, amount):
        """ Returns a new Affine where the translate is shifted by amount.
            Amount is in integer mesh units, as translate. """

        return Affine(self.ndim, self.scale, self.translate + amount, self.period)

class ResampleWindow(_ResampleWindow):
    def __init__(self, kind, support=-1):
        _ResampleWindow.__init__(self, kind, support)

    def resize(self, support):
        """ Change the support of the window, returning a new window. """
        return ResampleWindow(self.kind, support)

    def paint(self, real, pos, mass=None, hsml=None, diffdir=None, transform=None):
        """
            paint to a field.

            Parameters
            ----------
            real : array_like
                original values are preserved.

            pos : array_like

            mass : array_like or None
                None for 1

            hsml: array_like or None
                None for 1

            diffdir: int or None
                direction for differentiation kernel.
                0, 1, 2,... or None

            transform: Affine
                The Affine transformation from position to grid units.

        """
        if transform is None:
            transform = Affine(real.ndim)

        assert isinstance(transform, Affine)

        order = numpy.zeros(real.ndim, dtype=int)
        if diffdir is not None:
            order[diffdir] = 1

        pos = numpy.asfarray(pos)
        if mass is None:
            mass = numpy.array(1.0, 'f8')
        else:
            mass = numpy.asfarray(mass)

        if hsml is None:
            hsml = numpy.array(1.0, 'f8')
        else:
            hsml = numpy.asfarray(hsml)

        mass = _mkarr(mass, len(pos), mass.dtype)
        hsml = _mkarr(hsml, len(pos), hsml.dtype)

        # workaround https://github.com/cython/cython/issues/1605

        if not pos.flags.writeable:
            pos = pos.copy()
        if not mass.flags.writeable:
            mass = mass.copy()
        if not hsml.flags.writeable:
            hsml = hsml.copy()

        _ResampleWindow.paint(self, real, pos, hsml, mass, order, transform.scale, transform.translate, transform.period)

    def readout(self, real, pos, out=None, hsml=None, diffdir=None, transform=None):
        """
            readout from a field.

            Parameters
            ----------
            real : array_like

            pos : array_like

            out : array_like

            mass : array_like or None
                None for 1

            diffdir: int or None
                direction for differentiation kernel.
                0, 1, 2,... or None

            transform: Affine
                The Affine transformation from position to grid units.

        """
        if transform is None:
            transform = Affine(real.ndim)

        assert isinstance(transform, Affine)

        order = numpy.zeros(real.ndim, dtype=int)
        if diffdir is not None:
            order[diffdir] = 1

        pos = numpy.asfarray(pos)
        if out is None:
            out = numpy.zeros(pos.shape[:-1], dtype='f8')

        if hsml is None:
            hsml = numpy.array(1.0, 'f8')
        else:
            hsml = numpy.asfarray(hsml)
        hsml = _mkarr(hsml, len(pos), hsml.dtype)

        # workaround https://github.com/cython/cython/issues/1605

        if not pos.flags.writeable:
            pos = pos.copy()

        _ResampleWindow.readout(self, real, pos, hsml, out, order, transform.scale, transform.translate, transform.period)

        return out

def FindResampler(window):
    if window in windows:
        window = windows[window]
    if not isinstance(window, ResampleWindow):
        raise TypeError("argument is not a ResampleWindow name or a ResampleWindow object")
    return window

windows = dict(
    NEAREST = ResampleWindow(kind="nearest"),
    LINEAR = ResampleWindow(kind="linear"),
    NNB = ResampleWindow(kind="tunednnb"),
    CIC = ResampleWindow(kind="tunedcic"),
    TSC = ResampleWindow(kind="tunedtsc"),
    QUADRATIC = ResampleWindow(kind="quadratic"),
    CUBIC = ResampleWindow(kind="cubic"),
    LANCZOS2 = ResampleWindow(kind="lanczos2"),
    LANCZOS3 = ResampleWindow(kind="lanczos3"),
    LANCZOS4 = ResampleWindow(kind="lanczos4"),
    LANCZOS5 = ResampleWindow(kind="lanczos5"),
    LANCZOS6 = ResampleWindow(kind="lanczos6"),
    ACG2 = ResampleWindow(kind="acg2"),
    ACG3 = ResampleWindow(kind="acg3"),
    ACG4 = ResampleWindow(kind="acg4"),
    ACG5 = ResampleWindow(kind="acg5"),
    ACG6 = ResampleWindow(kind="acg6"),
    DB6 = ResampleWindow(kind="db6"),
    DB12 = ResampleWindow(kind="db12"),
    DB20 = ResampleWindow(kind="db20"),
    SYM6 = ResampleWindow(kind="sym6"),
    SYM12 = ResampleWindow(kind="sym12"),
    SYM20 = ResampleWindow(kind="sym20"),
)
for m, p in list(windows.items()):
    windows[m.lower()] = p
    globals()[m] = p

# compatible.
methods = windows
del m, p
