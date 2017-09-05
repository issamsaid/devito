from sympy import Number, Symbol
from devito.arguments import DimensionArgProvider

__all__ = ['Dimension', 'x', 'y', 'z', 't', 'p', 'd', 'time']


class Dimension(Symbol, DimensionArgProvider):

    """Index object that represents a problem dimension and thus
    defines a potential iteration space.

    :param size: Optional, size of the array dimension.
    :param reverse: Traverse dimension in reverse order (default False)
    :param buffered: Optional, boolean flag indicating whether to
                     buffer variables when iterating this dimension.
    """

    is_Buffered = False
    is_Lowered = False

    def __new__(cls, name, **kwargs):
        newobj = Symbol.__new__(cls, name)
        newobj.size = kwargs.get('size', None)
        newobj.reverse = kwargs.get('reverse', False)
        newobj.spacing = kwargs.get('spacing', Symbol('h_%s' % name))
        return newobj

    def __str__(self):
        return self.name

    @property
    def symbolic_size(self):
        """The symbolic size of this dimension."""
        try:
            return Number(self.size)
        except TypeError:
            return self.rtargs[0].as_symbol


class BufferedDimension(Dimension):

    is_Buffered = True

    """
    Dimension symbol that implies modulo buffered iteration.

    :param parent: Parent dimension over which to loop in modulo fashion.
    """

    def __new__(cls, name, parent, **kwargs):
        newobj = Symbol.__new__(cls, name)
        assert isinstance(parent, Dimension)
        newobj.parent = parent
        newobj.modulo = kwargs.get('modulo', 2)
        return newobj

    @property
    def size(self):
        return self.parent.size

    @property
    def reverse(self):
        return self.parent.reverse

    @property
    def spacing(self):
        return self.parent.spacing


class LoweredDimension(Dimension):

    is_Lowered = True

    """
    Dimension symbol representing modulo iteration created when resolving a
    :class:`BufferedDimension`.

    :param buffered: BufferedDimension from which this Dimension originated.
    :param offset: Offset value used in the modulo iteration.
    """

    def __new__(cls, name, buffered, offset, **kwargs):
        newobj = Symbol.__new__(cls, name)
        assert isinstance(buffered, BufferedDimension)
        newobj.buffered = buffered
        newobj.offset = offset
        return newobj

    @property
    def origin(self):
        return self.buffered + self.offset

    @property
    def size(self):
        return self.buffered.size

    @property
    def reverse(self):
        return self.buffered.reverse


# Default dimensions for time
time = Dimension('time', spacing=Symbol('s'))
t = BufferedDimension('t', parent=time)

# Default dimensions for space
x = Dimension('x', spacing=Symbol('h_x'))
y = Dimension('y', spacing=Symbol('h_y'))
z = Dimension('z', spacing=Symbol('h_z'))

d = Dimension('d')
p = Dimension('p')
