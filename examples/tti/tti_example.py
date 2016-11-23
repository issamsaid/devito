import numpy as np

from examples.containers import IGrid, IShot
from examples.tti.TTI_codegen import TTI_cg


def source(t, f0):
    agauss = 0.5*f0
    tcut = 1.5/agauss
    s = (t-tcut)*agauss
    return np.exp(-2*s**2)*np.cos(2*np.pi*s)


def setup(dimensions=(50, 50, 50), spacing=(20.0, 20.0, 20.0), tn=250.0,
          time_order=2, space_order=2, nbpml=10):

    origin = (0., 0., 0.)

    # True velocity
    true_vp = np.ones(dimensions) + 1.0
    true_vp[:, :, int(dimensions[0] / 3):int(2*dimensions[0]/3)] = 3.0
    true_vp[:, :, int(2*dimensions[0] / 3):int(dimensions[0])] = 4.0

    model = IGrid(origin, spacing,
                  true_vp,
                  .4*np.ones(dimensions),
                  -.1*np.ones(dimensions),
                  -np.pi/7*np.ones(dimensions),
                  np.pi/5*np.ones(dimensions))

    # Define seismic data.
    data = IShot()

    f0 = .010
    dt = model.get_critical_dt()
    t0 = 0.0
    nt = int(1+(tn-t0)/dt)
    # Set up the source as Ricker wavelet for f0

    time_series = source(np.linspace(t0, tn, nt), f0)
    location = (origin[0] + dimensions[0] * spacing[0] * 0.5,
                origin[1] + dimensions[1] * spacing[1] * 0.5,
                origin[1] + 2 * spacing[1])
    data.set_source(time_series, dt, location)
    receiver_coords = np.zeros((101, 3))
    receiver_coords[:, 0] = np.linspace(50,
                                        origin[0] +
                                        (dimensions[0] - 2) * spacing[0],
                                        num=101)
    receiver_coords[:, 1] = origin[1] + dimensions[1] * spacing[1] * 0.5
    receiver_coords[:, 2] = location[2]
    data.set_receiver_pos(receiver_coords)
    data.set_shape(nt, 101)

    TTI = TTI_cg(model, data, None, t_order=time_order, s_order=space_order, nbpml=nbpml)
    return TTI


def run(dimensions=(50, 50, 50), spacing=(20.0, 20.0, 20.0), tn=250.0,
        time_order=2, space_order=2, nbpml=10, dse='advanced',
        auto_tuning=False, compiler=None, cache_blocking=None):
    if auto_tuning:
        cache_blocking = None

    TTI = setup(dimensions, spacing, tn, time_order, space_order, nbpml)

    rec, u, v, gflopss, oi, timings = TTI.Forward(dse=dse,
                                                  auto_tuning=auto_tuning,
                                                  cache_blocking=cache_blocking,
                                                  compiler=compiler)

    return gflopss, oi, timings, [rec, u, v]


if __name__ == "__main__":
    run(auto_tuning=True)
