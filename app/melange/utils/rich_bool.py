# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module with RichBool class."""


class RichBool(object):
  """Class that extends capabilities of traditional bool type.

  Except for the boolean value (usually referred to as the boolean part),
  this class may also contain an arbitrary extra object (usually referred to
  as the extra part).

  Instances of this class behave as if they were normal bool objects when it
  comes to comparison with other objects. The semantics should be as similar
  to bool type as possible. The only exception is that the extra part can be
  accessed at any time of the object's lifetime.

  Typical usage of this class is a return value of a function for which
  regular bool type is not sufficient enough. Specifically, a function may
  want to inform the caller why its result is either True or False. It is
  a good fit for the extra part which may transport a message or some sort
  of constant.

  The contract on how the extra part is used depends entirely on the function
  and its callers.
  """

  def __init__(self, value, extra=None):
    """Initializes a new instance of RichBool class with the required
    boolean part and optional extra part.

    Args:
      value: boolean part of the object. It must be an instance of bool type
          which is True or False.
      extra: extra part of the object. It can be arbitrary value of any type.
    """
    if not isinstance(value, bool):
      raise TypeError(
          'Passed value must be a bool. %s found instead.' % type(value))

    self._value = value
    self._extra = extra

  @property
  def value(self):
    """Returns boolean part of the object.

    Returns:
      boolean part of the object.
    """
    return self._value

  @property
  def extra(self):
    """Returns extra part of the object.

    Returns:
      extra part of the object.
    """
    return self._extra

  def __cmp__(self, other):
    """Compares the object with the other specified object.

    The comparison logic is based purely on the boolean part of this object.
    Only that value is compared with the other object passed as the argument.
    Extra part is omitted and not involved at any point of the process.

    In other words, when two different RichBool objects are compared,
    the evaluation reduces to comparison of their boolean parts. Specifically,
    if those parts are equal, then the objects are considered equal even if
    their extra parts are different.

    Args:
      other: object to be compared with self object.

    Returns:
      a negative integer if self < other, zero if self == other, a positive
      integer if self > other.
    """
    if not isinstance(other, RichBool):
      return cmp(self.value, other)
    else:
      return self.value.__cmp__(other.value)

  def __hash__(self):
    """Computes value of hash function for the object.

    As with comparison, the value is based purely on the boolean part of
    this object. Therefore, the returned value is actually a hash function
    of that part.

    Extra part is omitted. In particular, two different objects with
    the same boolean value and different extra values return the same
    hash value as well.

    Returns:
      hash value of self object.
    """
    return self.value.__hash__()

  def __nonzero__(self):
    """Tests whether the object is non zero.

    The test is based entirely on the boolean part of this object. Therefore,
    the object evaluates to the same value as the boolean part.

    Returns:
      True if boolean part of self object evaluates to True, False if
      boolean part evaluates to False.
    """
    return self.value.__nonzero__()


TRUE = RichBool(True)
FALSE = RichBool(False)
