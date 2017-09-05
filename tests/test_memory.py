from devito import DenseData
import pytest
import numpy as np


@pytest.mark.parametrize('shape', [(20, 20), (20, 20, 20), (20, 20, 20, 20)])
def test_first_touch(shape):
    m = DenseData(name='m', shape=shape, first_touch=True)
    assert(np.allclose(m.data, 0))
    m2 = DenseData(name='m2', shape=shape, first_touch=False)
    assert(np.allclose(m2.data, 0))
    assert(np.array_equal(m.data, m2.data))
