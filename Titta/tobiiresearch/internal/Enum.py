'''
Created on 10 aug. 2016
'''

import sys


def _enum__str__(self):
    return repr(self._value_string)


def _enum__eq__(self, other):
    return self.value == other.value


def _enum__ne__(self, other):
    return not self.__eq__(other)


def _enum_get_value(self):
    return self._value


class _enum_value(object):
    __str__ = _enum__str__
    __eq__ = _enum__eq__
    __ne__ = _enum__ne__
    __get_value = _enum_get_value
    value = property(__get_value)

    def __init__(self, value, value_string):
        self._value = value
        self._value_string = value_string


def __enum__init__(self, value):
    for value_string in self.__class__.__dict__:
        cur_value = self.__class__.__dict__[value_string]
        if isinstance(cur_value, _enum_value) and cur_value.value == value:
            self._value = value
            self._value_string = value_string
            break
    else:
        raise ValueError("Invalid enum value {0}.".format(value))


def _enum(class_object):
    class_object.__init__ = __enum__init__
    class_object.__str__ = _enum__str__
    class_object.__eq__ = _enum__eq__
    class_object.__ne__ = _enum__ne__
    class_object.__get_value = _enum_get_value
    class_object.value = property(class_object.__get_value)
    for value_string in class_object.__dict__:
        value = class_object.__dict__[value_string]

        if sys.version_info[0] == 3:
            inst = int
        else:
            inst = (int, long)  # noqa: F821
        if isinstance(value, inst):
            setattr(class_object, value_string, _enum_value(value, value_string))

    return class_object
