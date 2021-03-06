import numpy as np
from sympy import Eq

import pytest

from devito import Operator, Forward, Backward, TimeData, t


@pytest.fixture
def a(shape=(11, 11)):
    """Forward time data object, unrolled (save=True)"""
    return TimeData(name='a', shape=shape, time_order=1,
                    time_dim=6, save=True)


@pytest.fixture
def b(shape=(11, 11)):
    """Backward time data object, unrolled (save=True)"""
    return TimeData(name='b', shape=shape, time_order=1,
                    time_dim=6, save=True)


@pytest.fixture
def c(shape=(11, 11)):
    """Forward time data object, buffered (save=False)"""
    return TimeData(name='c', shape=shape, time_order=1,
                    save=False, time_axis=Forward)


@pytest.fixture
def d(shape=(11, 11)):
    """Forward time data object, unrolled (save=True), end order"""
    return TimeData(name='d', shape=shape, time_order=2,
                    time_dim=6, save=True)


def test_forward(a):
    a.data[0, :] = 1.
    Operator(Eq(a.forward, a + 1.))()
    for i in range(a.shape[0]):
        assert np.allclose(a.data[i, :], 1. + i, rtol=1.e-12)


def test_backward(b):
    b.data[-1, :] = 7.
    Operator(Eq(b.backward, b - 1.), time_axis=Backward)()
    for i in range(b.shape[0]):
        assert np.allclose(b.data[i, :], 2. + i, rtol=1.e-12)


def test_forward_unroll(a, c, nt=5):
    """Test forward time marching with a buffered and an unrolled t"""
    a.data[0, :] = 1.
    c.data[0, :] = 1.
    eqn_c = Eq(c.forward, c + 1.)
    eqn_a = Eq(a.forward, c.forward)
    Operator([eqn_c, eqn_a])(time=nt)
    for i in range(nt):
        assert np.allclose(a.data[i, :], 1. + i, rtol=1.e-12)


def test_forward_backward(a, b, nt=5):
    """Test a forward operator followed by a backward marching one"""
    a.data[0, :] = 1.
    b.data[0, :] = 1.
    eqn_a = Eq(a.forward, a + 1.)
    Operator(eqn_a, time_axis=Forward)(time=nt)

    eqn_b = Eq(b, a + 1.)
    Operator(eqn_b, time_axis=Backward)(time=nt)
    for i in range(nt):
        assert np.allclose(b.data[i, :], 2. + i, rtol=1.e-12)


def test_forward_backward_overlapping(a, b, nt=5):
    """
    Test a forward operator followed by a backward one, but with
    overlapping operator definitions.
    """
    a.data[0, :] = 1.
    b.data[0, :] = 1.
    op_fwd = Operator(Eq(a.forward, a + 1.), time_axis=Forward)
    op_bwd = Operator(Eq(b, a + 1.), time_axis=Backward)

    op_fwd(time=nt)
    op_bwd(time=nt)
    for i in range(nt):
        assert np.allclose(b.data[i, :], 2. + i, rtol=1.e-12)


def test_loop_bounds_forward(d):
    """Test the automatic bound detection for forward time loops"""
    d.data[:] = 1.
    eqn = Eq(d, 2. + d.dt2)
    Operator(eqn, dle=None, dse=None, subs={t.spacing: 1.}, time_axis=Forward)()
    assert np.allclose(d.data[0, :], 1., rtol=1.e-12)
    assert np.allclose(d.data[-1, :], 1., rtol=1.e-12)
    for i in range(1, d.data.shape[0]-1):
        assert np.allclose(d.data[i, :], 1. + i, rtol=1.e-12)


def test_loop_bounds_backward(d):
    """Test the automatic bound detection for backward time loops"""
    d.data[:] = 1.
    eqn = Eq(d, 2. + d.dt2)
    Operator(eqn, dle=None, dse=None, subs={t.spacing: 1.}, time_axis=Backward)()
    assert np.allclose(d.data[0, :], 1., rtol=1.e-12)
    assert np.allclose(d.data[-1, :], 1., rtol=1.e-12)
    for i in range(1, d.data.shape[0]-1):
        assert np.allclose(d.data[i, :], d.data.shape[0] - i, rtol=1.e-12)
