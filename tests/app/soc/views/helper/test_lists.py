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


"""Tests for lists helper functions."""

import math
import sys
import unittest

from soc.views.helper import lists


class ColumnTypeFactoryTest(unittest.TestCase):
  """Unit tests for ColumnTypeFactory class."""

  def testCreatePlainText(self):
    column_type = lists.ColumnTypeFactory.create(lists.ColumnType.PLAIN_TEXT)
    self.assertIsInstance(column_type, lists.PlainTextColumnType)

  def testCreateNumerical(self):
    column_type = lists.ColumnTypeFactory.create(lists.ColumnType.NUMERICAL)
    self.assertIsInstance(column_type, lists.NumericalColumnType)

  def testCreateHtml(self):
    column_type = lists.ColumnTypeFactory.create(lists.ColumnType.HTML)
    self.assertIsInstance(column_type, lists.HtmlColumnType)

  def testCreateWithInvalidArgument(self):
    with self.assertRaises(ValueError):
      column_type = lists.ColumnTypeFactory.create(None)

    with self.assertRaises(ValueError):
      column_type = lists.ColumnTypeFactory.create('invalid_column_type')


class NumericalColumnTypeTest(unittest.TestCase):
  """Unit tests for NumericalColumnType class."""

  def setUp(self):
    self.column_type = lists.NumericalColumnType()

  def testSafeForInt(self):
    self.assertEqual(0, self.column_type.safe(0))
    self.assertEqual(1, self.column_type.safe(1))
    self.assertEqual(-1, self.column_type.safe(-1))
    self.assertEqual(42, self.column_type.safe(42))
    self.assertEqual(-42, self.column_type.safe(-42))
    self.assertEqual(sys.maxint, self.column_type.safe(sys.maxint))

  def testSafeForLong(self):
    self.assertEqual(0, self.column_type.safe(0L))
    self.assertEqual(1, self.column_type.safe(1L))
    self.assertEqual(-1, self.column_type.safe(-1L))
    self.assertEqual(42, self.column_type.safe(42L))
    self.assertEqual(-42, self.column_type.safe(-42L))
    self.assertEqual(10**30, self.column_type.safe(10**30))
    self.assertEqual(-10**30, self.column_type.safe(-10**30))

  def testSafeForFloat(self):
    self.assertEqual(0.0, self.column_type.safe(0.0))
    self.assertEqual(1.0, self.column_type.safe(1.0))
    self.assertEqual(-1.0, self.column_type.safe(-1.0))
    self.assertEqual(math.pi, self.column_type.safe(math.pi))
    self.assertEqual(-math.pi, self.column_type.safe(-math.pi))

  def testSafeForValidString(self):
    self.assertEqual('', self.column_type.safe(''))

    self.assertEqual(0, self.column_type.safe('0'))
    self.assertEqual(0, self.column_type.safe('0.0'))
    self.assertEqual(0, self.column_type.safe('-0.0'))
    self.assertEqual(0, self.column_type.safe('+0.0'))
    self.assertEqual(0, self.column_type.safe('.0'))

    self.assertEqual(1, self.column_type.safe('1'))
    self.assertEqual(1, self.column_type.safe('1.0'))
    self.assertEqual(1, self.column_type.safe('+1.0'))
    self.assertEqual(1, self.column_type.safe('1.000000'))

    self.assertEqual(1.1, self.column_type.safe('1.1'))
    self.assertEqual(3.14159265359, self.column_type.safe('3.14159265359'))
    self.assertEqual(-7.12345, self.column_type.safe('-00007.12345'))
    self.assertEqual(0.002, self.column_type.safe('2e-3'))

  def testSafeForInvalidString(self):
    with self.assertRaises(ValueError):
      self.column_type.safe('a')

    with self.assertRaises(ValueError):
      self.column_type.safe('1.0.0')

    with self.assertRaises(ValueError):
      self.column_type.safe('1L')

    with self.assertRaises(ValueError):
      self.column_type.safe('2e-3 a')

  def testSafeForInvalidType(self):
    with self.assertRaises(TypeError):
      self.column_type.safe(object())

    with self.assertRaises(TypeError):
      self.column_type.safe([1])
