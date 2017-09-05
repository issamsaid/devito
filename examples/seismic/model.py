import numpy as np
import os

from devito import DenseData, ConstantData
from devito.logger import error


__all__ = ['Model', 'demo_model']


def demo_model(preset, **kwargs):
    """
    Utility function to create preset :class:`Model` objects for
    demonstration and testing purposes. The particular presets are ::

    * 'layer2D': Simple two-layer model with velocities 1.5 km/s
                 and 2.5 km/s in the top and bottom layer respectively.
    * 'marmousi2D': Loads the 2D Marmousi data set from the given
                    filepath. Requires the ``opesci/data`` repository
                    to be available on your machine.
    """
    if preset.lower() in ['constant']:
        # A constant single-layer model in a 2D or 3D domain
        # with velocity 1.5km/s.
        shape = kwargs.pop('shape', (101, 101))
        spacing = kwargs.pop('spacing', tuple([10. for _ in shape]))
        origin = kwargs.pop('origin', tuple([0. for _ in shape]))
        nbpml = kwargs.pop('nbpml', 10)
        vp = kwargs.pop('vp', 1.5)

        return Model(vp=vp, origin=origin, shape=shape,
                     spacing=spacing, nbpml=nbpml, **kwargs)

    elif preset.lower() in ['layers', 'twolayer', '2layer']:
        # A two-layer model in a 2D or 3D domain with two different
        # velocities split across the height dimension:
        # By default, the top part of the domain has 1.5 km/s,
        # and the bottom part of the domain has 2.5 km/s.
        shape = kwargs.pop('shape', (101, 101))
        spacing = kwargs.pop('spacing', tuple([10. for _ in shape]))
        origin = kwargs.pop('origin', tuple([0. for _ in shape]))
        nbpml = kwargs.pop('nbpml', 10)
        ratio = kwargs.pop('ratio', 2)
        vp_top = kwargs.pop('vp_top', 1.5)
        vp_bottom = kwargs.pop('vp_bottom', 2.5)

        # Define a velocity profile in km/s
        v = np.empty(shape, dtype=np.float32)
        v[:] = vp_top  # Top velocity (background)
        v[..., int(shape[-1] / ratio):] = vp_bottom  # Bottom velocity

        return Model(vp=v, origin=origin, shape=shape,
                     spacing=spacing, nbpml=nbpml, **kwargs)

    elif preset.lower() in ['circle']:
        # A simple circle in a 2D domain with a background velocity.
        # By default, the circle velocity is 2.5 km/s,
        # and the background veloity is 3.0 km/s.
        shape = kwargs.pop('shape', (101, 101))
        spacing = kwargs.pop('spacing', tuple([10. for _ in shape]))
        origin = kwargs.pop('origin', tuple([0. for _ in shape]))
        nbpml = kwargs.pop('nbpml', 10)
        vp = kwargs.pop('vp', 3.0)
        vp_background = kwargs.pop('vp_background', 2.5)
        r = kwargs.pop('r', 15)

        # Only a 2D preset is available currently
        assert(len(shape) == 2)

        v = np.empty(shape, dtype=np.float32)
        v[:] = vp_background

        a, b = shape[0] / 2, shape[1] / 2
        y, x = np.ogrid[-a:shape[0]-a, -b:shape[1]-b]
        v[x*x + y*y <= r*r] = vp

        return Model(vp=v, origin=origin, shape=shape,
                     spacing=spacing, nbpml=nbpml)

    elif preset.lower() in ['marmousi', 'marmousi2d']:
        shape = (1601, 401)
        spacing = (7.5, 7.5)
        origin = (0., 0.)

        # Read 2D Marmousi model from opesc/data repo
        data_path = kwargs.get('data_path', None)
        if data_path is None:
            error("Path to opesci/data not found! Please specify with "
                  "'data_path=<path/to/opesci/data>'")
            raise ValueError("Path to model data unspecified")
        path = os.path.join(data_path, 'Simple2D/vp_marmousi_bi')
        v = np.fromfile(path, dtype='float32', sep="")
        v = v.reshape(shape)

        # Cut the model to make it slightly cheaper
        v = v[301:-300, :]

        return Model(vp=v, origin=origin, shape=v.shape,
                     spacing=spacing, nbpml=20)

    else:
        error('Unknown model preset name %s' % preset)


def damp_boundary(damp, nbpml, spacing):
    """Initialise damping field with an absorbing PML layer.

    :param damp: Array data defining the damping field
    :param nbpml: Number of points in the damping layer
    :param spacing: Grid spacing coefficent
    """
    dampcoeff = 1.5 * np.log(1.0 / 0.001) / (40.)
    ndim = len(damp.shape)
    for i in range(nbpml):
        pos = np.abs((nbpml - i + 1) / float(nbpml))
        val = dampcoeff * (pos - np.sin(2*np.pi*pos)/(2*np.pi))
        if ndim == 2:
            damp[i, :] += val/spacing[0]
            damp[-(i + 1), :] += val/spacing[0]
            damp[:, i] += val/spacing[1]
            damp[:, -(i + 1)] += val/spacing[1]
        else:
            damp[i, :, :] += val/spacing[0]
            damp[-(i + 1), :, :] += val/spacing[0]
            damp[:, i, :] += val/spacing[1]
            damp[:, -(i + 1), :] += val/spacing[1]
            damp[:, :, i] += val/spacing[2]
            damp[:, :, -(i + 1)] += val/spacing[2]


class Model(object):
    """The physical model used in seismic inversion processes.

    :param origin: Origin of the model in m as a tuple in (x,y,z) order
    :param spacing: Grid size in m as a Tuple in (x,y,z) order
    :param shape: Number of grid points size in (x,y,z) order
    :param vp: Velocity in km/s
    :param nbpml: The number of PML layers for boundary damping
    :param rho: Density in kg/cm^3 (rho=1 for water)
    :param epsilon: Thomsen epsilon parameter (0<epsilon<1)
    :param delta: Thomsen delta parameter (0<delta<1), delta<epsilon
    :param theta: Tilt angle in radian
    :param phi: Asymuth angle in radian

    The :class:`Model` provides two symbolic data objects for the
    creation of seismic wave propagation operators:

    :param m: The square slowness of the wave
    :param damp: The damping field for absorbing boundarycondition
    """
    def __init__(self, origin, spacing, shape, vp, nbpml=20, dtype=np.float32,
                 epsilon=None, delta=None, theta=None, phi=None):
        self.origin = origin
        self.spacing = spacing
        self.shape = shape
        self.nbpml = int(nbpml)
        self.dtype = dtype

        # Ensure same dimensions on all inpute parameters
        assert(len(origin) == len(spacing))
        assert(len(origin) == len(shape))

        # Create square slowness of the wave as symbol `m`
        if isinstance(vp, np.ndarray):
            self.m = DenseData(name="m", shape=self.shape_domain, dtype=self.dtype)
        else:
            self.m = ConstantData(name="m", value=1/vp**2, dtype=self.dtype)

        # Set model velocity, which will also set `m`
        self.vp = vp

        # Create dampening field as symbol `damp`
        self.damp = DenseData(name="damp", shape=self.shape_domain,
                              dtype=self.dtype)
        damp_boundary(self.damp.data, self.nbpml, spacing=self.get_spacing())

        # Additional parameter fields for TTI operators
        self.scale = 1.

        if epsilon is not None:
            if isinstance(epsilon, np.ndarray):
                self.epsilon = DenseData(name="epsilon", shape=self.shape_domain,
                                         dtype=self.dtype)
                self.epsilon.data[:] = self.pad(1 + 2 * epsilon)
                # Maximum velocity is scale*max(vp) if epsilon > 0
                if np.max(self.epsilon.data) > 0:
                    self.scale = np.sqrt(np.max(self.epsilon.data))
            else:
                self.epsilon = 1 + 2 * epsilon
                self.scale = epsilon
        else:
            self.epsilon = 1

        if delta is not None:
            if isinstance(delta, np.ndarray):
                self.delta = DenseData(name="delta", shape=self.shape_domain,
                                       dtype=self.dtype)
                self.delta.data[:] = self.pad(np.sqrt(1 + 2 * delta))
            else:
                self.delta = delta
        else:
            self.delta = 1

        if theta is not None:
            if isinstance(theta, np.ndarray):
                self.theta = DenseData(name="theta", shape=self.shape_domain,
                                       dtype=self.dtype)
                self.theta.data[:] = self.pad(theta)
            else:
                self.theta = theta
        else:
            self.theta = 0

        if phi is not None:
            if isinstance(phi, np.ndarray):
                self.phi = DenseData(name="phi", shape=self.shape_domain,
                                     dtype=self.dtype)
                self.phi.data[:] = self.pad(phi)
            else:
                self.phi = phi
        else:
            self.phi = 0

    @property
    def dim(self):
        """
        Spatial dimension of the model domain
        """
        return len(self.shape)

    @property
    def shape_domain(self):
        """Computational shape of the model domain, with PML layers"""
        return tuple(d + 2*self.nbpml for d in self.shape)

    @property
    def domain_size(self):
        """
        Physical size of the domain as determined by shape and spacing
        """
        return tuple((d-1) * s for d, s in zip(self.shape, self.spacing))

    @property
    def critical_dt(self):
        """Critical computational time step value from the CFL condition."""
        # For a fixed time order this number goes down as the space order increases.
        #
        # The CFL condtion is then given by
        # dt <= coeff * h / (max(velocity))
        coeff = 0.38 if len(self.shape) == 3 else 0.42
        return coeff * np.min(self.spacing) / (self.scale*np.max(self.vp))

    @property
    def vp(self):
        """:class:`numpy.ndarray` holding the model velocity in km/s.

        .. note::

        Updating the velocity field also updates the square slowness
        ``self.m``. However, only ``self.m`` should be used in seismic
        operators, since it is of type :class:`DenseData`.
        """
        return self._vp

    @vp.setter
    def vp(self, vp):
        """Set a new velocity model and update square slowness

        :param vp : new velocity in km/s
        """
        self._vp = vp

        # Update the square slowness according to new value
        if isinstance(vp, np.ndarray):
            self.m.data[:] = self.pad(1 / (self.vp * self.vp))
        else:
            self.m.data = 1 / vp**2

    def get_spacing(self):
        """Return the grid size"""
        return self.spacing

    def pad(self, data):
        """Padding function PNL layers in every direction for for the
        absorbing boundary conditions.

        :param data : Data array to be padded"""
        pad_list = [(self.nbpml, self.nbpml) for _ in self.shape]
        return np.pad(data, pad_list, 'edge')
