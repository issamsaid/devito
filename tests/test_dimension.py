import devito
import pytest
from conftest import skipif_yask
from devito.dimension import FixedDimension
from devito import DenseData, y


@skipif_yask
@pytest.mark.xfail
def test_incorrect_usage():
    m = DenseData(name="m", shape=(10, 10))
    devito.x = FixedDimension(name='x', size=10, spacing=devito.x.spacing)
    assert(devito.x in m.indices)


@skipif_yask
def test_correct_usage():
    myx = FixedDimension(name='x', size=10, spacing=devito.x.spacing)
    m = DenseData(name="m", dimensions=(myx, y))
    assert(myx in m.indices)
