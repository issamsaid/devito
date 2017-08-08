from sympy import Number, Symbol
from devito.arguments import DimensionArgProvider, FixedDimensionArgProvider

__all__ = ['Dimension', 'x', 'y', 'z', 't', 'p', 'd', 'time']


class FixedDimension(Symbol, FixedDimensionArgProvider):

    is_Fixed = True
    is_Buffered = False
    is_Lowered = False

    """Index object that represents a problem dimension fixed in size 

    :param size: Optional, size of the array dimension.
    :param reverse: Traverse dimension in reverse order (default False)
    :param buffered: Optional, boolean flag indicating whether to
                     buffer variables when iterating this dimension.
    """

    def __new__(cls, name, **kwargs):
        newobj = Symbol.__new__(cls, name)
        newobj.size = kwargs.get('size', None)
        newobj.reverse = kwargs.get('reverse', False)
        return newobj

    def __str__(self):
        return self.name

    @property
    def symbolic_size(self):
        """The symbolic size of this dimension."""
        return Number(self.ccode)

    
class OpenDimension(Symbol, DimensionArgProvider):

    is_Fixed = False
    is_Buffered = False
    is_Lowered = False

    """Index object that represents a problem dimension and thus
    defines a potential iteration space.

    :param size: Optional, size of the array dimension.
    :param reverse: Traverse dimension in reverse order (default False)
    :param buffered: Optional, boolean flag indicating whether to
                     buffer variables when iterating this dimension.
    """

    def __new__(cls, name, **kwargs):
        newobj = Symbol.__new__(cls, name)
        newobj.reverse = kwargs.get('reverse', False)
        return newobj
    
    def __str__(self):
        return self.name

    @property
    def symbolic_size(self):
        """The symbolic size of this dimension."""
        start, end = self.rtargs
        return Symbol(end.name) - Symbol(start.name)

    @property
    def size(self):
        _, end = self.rtargs
        return Symbol(end.name)


class Dimension(OpenDimension):

    @property
    def size(self):
        return super(Dimension, self).size
    
    @size.setter
    def size(self, size):
        if size is None:
            print("Type set to open")
            self.size = None
            self.__class__ = OpenDimension
        else:
            print("Type set to fixed")
            self.__class__ = FixedDimension
            self.size = size


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
time = Dimension('time')
t = BufferedDimension('t', parent=time)

# Default dimensions for space
x = Dimension('x')
y = Dimension('y')
z = Dimension('z')

d = Dimension('d')
p = Dimension('p')
