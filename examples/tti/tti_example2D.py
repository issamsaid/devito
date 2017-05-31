import numpy as np

from examples.tti import AnisotropicWaveSolver
from examples.seismic import Model, PointSource, Receiver

dimensions = (150, 150)
origin = (0., 0.)
spacing = (20.0, 20.0)
time_order = 2
space_order = 4
# True velocity
true_vp = np.ones(dimensions) + 1.0
true_vp[:, int(dimensions[1] / 3):int(2*dimensions[1]/3)] = 3.0
true_vp[:, int(2*dimensions[1] / 3):int(dimensions[1])] = 4.0

model = Model(origin, spacing, dimensions, true_vp,
              epsilon=0.1*(true_vp - 2),
              delta=0.08 * (true_vp - 2),
              theta=np.pi/5*np.ones(dimensions),
              phi=0.1*np.ones(dimensions))

# Define seismic data.
f0 = .010
dt = model.critical_dt
t0 = 0.0
tn = 2000.0
nt = int(1+(tn-t0)/dt)
h = model.get_spacing()
# Set up the source as Ricker wavelet for f0


def source(t, f0):
    r = (np.pi * f0 * (t - 1./f0))
    return (1-2.*r**2)*np.exp(-r**2)


# Source geometry
time_series = np.zeros((nt, 1))
time_series[:, 0] = source(np.linspace(t0, tn, nt), f0)

location = np.zeros((1, 2))
location[0, 0] = origin[0] + dimensions[0] * spacing[0] * 0.5
location[0, 1] = origin[1] + 2 * spacing[1]
src = PointSource(name='src', data=time_series, coordinates=location)

# Receiver geometry
receiver_coords = np.zeros((101, 2))
receiver_coords[:, 0] = np.linspace(0, origin[0] +
                                    dimensions[0] * spacing[0], num=101)
receiver_coords[:, 1] = location[0, 1]
rec = Receiver(name='rec', ntime=nt, coordinates=receiver_coords)

solver = AnisotropicWaveSolver(model, source=src, receiver=rec,
                               time_order=time_order,
                               space_order=space_order)
rec, u, v, summary = solver.forward()
