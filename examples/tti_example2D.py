import numpy as np

from containers import IGrid, IShot
from TTI_codegen import TTI_cg

dimensions = (150, 150)
model = IGrid()
model.shape = dimensions
origin = (0., 0.)
spacing = (20.0, 20.0)
dtype = np.float32
t_order = 2
spc_order = 2
# True velocity
true_vp = np.ones(dimensions) + 1.0
true_vp[:, int(dimensions[1] / 3):int(2*dimensions[1]/3)] = 3.0
true_vp[:, int(2*dimensions[1] / 3):int(dimensions[1])] = 4.0

model.create_model(origin, spacing, true_vp, 0.1*(true_vp - 2),
                   0.08 * (true_vp - 2), np.pi/5*np.ones(dimensions),
                   0*np.ones(dimensions))

# Define seismic data.
data = IShot()
src = IShot()
f0 = .010
dt = model.get_critical_dt()
t0 = 0.0
tn = 2000.0
nt = int(1+(tn-t0)/dt)
h = model.get_spacing()
# data.reinterpolate(dt)
# Set up the source as Ricker wavelet for f0


def source(t, f0):
    r = (np.pi * f0 * (t - 1./f0))
    return (1-2.*r**2)*np.exp(-r**2)

# Source geometry
time_series = np.zeros((nt, 2))

time_series[:, 0] = source(np.linspace(t0, tn, nt), f0)
time_series[:, 1] = source(np.linspace(t0 + 50, tn, nt), f0)

location = np.zeros((2, 3))
location[0, 0] = origin[0] + dimensions[0] * spacing[0] * 0.3
location[0, 1] = origin[1] + dimensions[1] * spacing[1] * 0.3
location[0, 2] = origin[1] + 2 * spacing[1]
location[1, 0] = origin[0] + dimensions[0] * spacing[0] * 0.6
location[1, 1] = origin[1] + dimensions[1] * spacing[1] * 0.6
location[1, 2] = origin[1] + 2 * spacing[1]

src.set_receiver_pos(location)
src.set_shape(nt, 1)
src.set_traces(time_series)

# Receiver geometry
receiver_coords = np.zeros((101, 3))
receiver_coords[:, 0] = np.linspace(50, 950, num=101)
receiver_coords[:, 1] = origin[1] + dimensions[1] * spacing[1] * 0.5
receiver_coords[:, 2] = location[0, 1]
data.set_receiver_pos(receiver_coords)
data.set_shape(nt, 101)


TTI = TTI_cg(model, data, None, t_order=2, s_order=spc_order, nbpml=10)
(rec, u, v) = TTI.Forward()

# recw = open('RecTTI', 'w')
# recw.write(rec.data)
# recw.close()
