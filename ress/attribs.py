""" Test attributes manipulation"""


class Thing():

    def __init__(self):
        self._my_prop = 'My prop. value'

    def my_method(self, value='Dummy value'):
        """First line of my_method's docstring

        Plenty of other stuff here ...
        """
        return value + ' of ' + str(self)

    @property
    def my_prop(self):
        """Attrib prop getter"""
        return self._my_prop

    @my_prop.setter
    def my_prop(self, value):
        """Attrib prop setter"""
        self._my_prop = value

thing = Thing()

for n in ('my_method', 'my_prop'):
    print(f"\nAttribute name: {n}")
    # TODO: Still need a valid test to distinguish property from method!

    # Assign target to variable
    if n == 'my_method': a = getattr(thing, n)
    elif n == 'my_prop': a = getattr(thing.__class__, n)

    print("Attribute:", a)
    print("Type:", type(a))

    print("Test callable:", callable(a))
    print("Test type classmethod:", type(a) is classmethod)
    print("Test type staticmethod:", type(a) is staticmethod)
    print("Test type property:", type(a) is property)

    print("Summary:", a.__doc__.splitlines()[0].strip())

    # Call, get or set
    if n == 'my_method':
        print("Return without arg:", a())
        print("Return with arg 'New value':", a('New value'))
        a_class = getattr(thing.__class__, n)
        print("Return from class access:", a_class(thing))
    elif n == 'my_prop':
        print("Get value:", a.fget(thing))
        a.fset(thing, 'New prop. value')
        print("Set 'New prop. value:", a.fget(thing))



# print("\nAttribute thing.run")
# a = getattr(thing, 'run')
# print("Callable: ", callable(a))
# print("\nAttribute thing.__class__.run")
# a = getattr(thing.__class__, 'run')
# print("Callable: ", callable(a))
#
# print("\nAttribute thing.prop")
# a = getattr(thing, 'prop')
# print("Callable: ", callable(a))
# print("\nAttribute thing.__class__.prop")
# getattr(thing.__class__, 'prop')
# print("Callable: ", callable(a))
#
# print("\nAttribute thing._prop")
# a = getattr(thing, '_prop')
# print("Callable: ", callable(a))
# #getattr(thing.__class__, '_prop')
# #callable(a)
