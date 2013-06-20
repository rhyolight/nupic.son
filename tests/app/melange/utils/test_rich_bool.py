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

"""Tests for functions of RichBoolean class."""

import unittest

from melange.utils import rich_bool

class InitTest(unittest.TestCase):
  """Unit tests for the constructor of RichBool class."""

  def testForBooleanType(self):
    """Tests that object is initialized correctly for values of bool type."""
    richBool = rich_bool.RichBool(True)
    self.assertEqual(richBool.value, True)

    richBool = rich_bool.RichBool(False)
    self.assertEqual(richBool.value, False)

  def testForNonBooleanType(self):
    """Tests that exception is raised for values of non bool type."""
    # test for object type
    with self.assertRaises(TypeError):
      richBool = rich_bool.RichBool(object())

    # test for list type
    with self.assertRaises(TypeError):
      richBool = rich_bool.RichBool([])

    # test for int type
    with self.assertRaises(TypeError):
      richBool = rich_bool.RichBool(1)

    # test for extra part of bool type
    with self.assertRaises(TypeError):
      richBool = rich_bool.RichBool(object(), extra=True)


class PropertyTest(unittest.TestCase):
  """Unit tests for value and extra properties."""

  def testValue(self):
    """Tests that value property returns a correct value."""
    richBool = rich_bool.RichBool(True)
    self.assertEqual(richBool.value, True)

    richBool = rich_bool.RichBool(True, extra=object())
    self.assertEqual(richBool.value, True)

    richBool = rich_bool.RichBool(True, extra=False)
    self.assertEqual(richBool.value, True)

    richBool = rich_bool.RichBool(False)
    self.assertEqual(richBool.value, False)

    richBool = rich_bool.RichBool(False, extra=object())
    self.assertEqual(richBool.value, False)

    richBool = rich_bool.RichBool(False, extra=True)
    self.assertEqual(richBool.value, False)

  def testExtra(self):
    """Tests that extra property returns a correct value."""
    richBool = rich_bool.RichBool(True)
    self.assertIsNone(richBool.extra)

    extra = object()
    richBool = rich_bool.RichBool(True, extra=extra)
    self.assertEqual(richBool.extra, extra)


class ComparisonTest(unittest.TestCase):
  """Unit tests for comparison operator."""

  def testCompareTwoRichBool(self):
    """Tests that two objects are compared based on their boolean value."""
    richBool1 = rich_bool.RichBool(True)
    richBool2 = rich_bool.RichBool(True)
    self.assertEqual(richBool1, richBool2)

    richBool1 = rich_bool.RichBool(True)
    richBool2 = rich_bool.RichBool(False)
    self.assertGreater(richBool1, richBool2)
    self.assertNotEqual(richBool1, richBool2)
    self.assertLess(richBool2, richBool1)

    richBool1 = rich_bool.RichBool(False)
    richBool2 = rich_bool.RichBool(True)
    self.assertGreater(richBool2, richBool1)
    self.assertNotEqual(richBool1, richBool2)
    self.assertLess(richBool1, richBool2)

  def testExtraPartOmitted(self):
    """Tests that comparison result does not depend on extra value."""
    richBool1 = rich_bool.RichBool(True, extra='extra one')
    richBool2 = rich_bool.RichBool(True, extra='extra two')
    self.assertEqual(richBool1, richBool2)

    richBool1 = rich_bool.RichBool(True, extra='extra one')
    richBool2 = rich_bool.RichBool(False, extra='extra one')
    self.assertNotEqual(richBool1, richBool2)

  def testCompareWithBool(self):
    """Tests that comparison with bool type works correctly."""
    richBool = rich_bool.RichBool(True)
    self.assertEqual(True, richBool)
    self.assertEqual(richBool, True)
    self.assertNotEqual(False, richBool)
    self.assertNotEqual(richBool, False)
    self.assertLess(False, richBool)
    self.assertGreater(richBool, False)

    richBool = rich_bool.RichBool(False)
    self.assertEqual(False, richBool)
    self.assertEqual(richBool, False)
    self.assertNotEqual(True, richBool)
    self.assertNotEqual(richBool, True)
    self.assertLess(richBool, True)
    self.assertGreater(True, richBool)

  def testEqualsContract(self):
    """Tests (simply) that equals is equivalence relation."""
    # check reflexivity
    richBool1 = rich_bool.RichBool(True)
    self.assertEqual(richBool1, richBool1)

    # check symmetry
    richBool2 = rich_bool.RichBool(True)
    self.assertEqual(richBool1, richBool2)
    self.assertEqual(richBool2, richBool1)

    # check transitivity
    richBool3 = rich_bool.RichBool(True)
    self.assertEqual(richBool1, richBool2)
    self.assertEqual(richBool2, richBool3)
    self.assertEqual(richBool1, richBool3)

  def testCompareWithOtherTypes(self):
    """Tests that comparison works correctly with a few other types."""
    richBool = rich_bool.RichBool(True)

    # because 1 == True
    self.assertEqual(1, richBool)

    # because True != object()
    self.assertNotEqual(richBool, object())

    # because True < []
    self.assertGreater([], richBool)

    # because 0 < True
    self.assertLess(0, True)

    richBool = rich_bool.RichBool(False)

    # because 1 > False
    self.assertGreater(1, richBool)

    # because False != object()
    self.assertNotEqual(richBool, object())

    # because False < []
    self.assertGreater([], richBool)

    # because 0 == False
    self.assertEqual(0, richBool)


class HashTest(unittest.TestCase):
  """Unit tests for hash function."""

  def testHash(self):
    """Tests that hash is computed like for bool type."""
    self.assertEqual(hash(True), hash(rich_bool.RichBool(True)))
    self.assertEqual(hash(False), hash(rich_bool.RichBool(False)))


class NonzeroTest(unittest.TestCase):
  """Unit tests for nonzero function."""

  def testNonZero(self):
    """Test that nonzero is computed like for bool type."""
    self.assertEqual(
        True.__nonzero__(), rich_bool.RichBool(True).__nonzero__())
    self.assertEqual(
        False.__nonzero__(), rich_bool.RichBool(False).__nonzero__())

  def testWithExtra(self):
    """Test that extra part does not change the behavior."""
    self.assertEqual(True.__nonzero__(),
        rich_bool.RichBool(True, extra=False).__nonzero__())
    self.assertEqual(False.__nonzero__(),
        rich_bool.RichBool(False, extra=True).__nonzero__())
