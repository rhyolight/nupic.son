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

import datetime
import math
import sys
import unittest

from django.utils import dateformat
from django.utils import html

from soc.views.helper import lists


class ColumnTypeFactoryTest(unittest.TestCase):
  """Unit tests for ColumnTypeFactory class."""

  def testCreatePlainText(self):
    column_type = lists.ColumnTypeFactory.create(lists.PLAIN_TEXT)
    self.assertIsInstance(column_type, lists.PlainTextColumnType)

  def testCreateNumerical(self):
    column_type = lists.ColumnTypeFactory.create(lists.NUMERICAL)
    self.assertIsInstance(column_type, lists.NumericalColumnType)

  def testCreateHtml(self):
    column_type = lists.ColumnTypeFactory.create(lists.HTML)
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
    self.assertEqual(50, self.column_type.safe('  50  '))


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


class PlainTextColumnTypeTest(unittest.TestCase):
  """Unit tests for PlainTextColumnType class."""

  def setUp(self):
    self.column_type = lists.PlainTextColumnType()

  def _escaped(self, value):
    return html.conditional_escape(value)

  def testSafe(self):
    text = ''
    self.assertEqual(text, self.column_type.safe(text))

    text = 'some example text'
    self.assertEqual(text, self.column_type.safe(text))

    text = '<a href="www.example.com">Example</a>'
    self.assertEqual(self._escaped(text), self.column_type.safe(text))

    text = '<script>alert("hacked")</script>'
    self.assertEqual(self._escaped(text), self.column_type.safe(text))


class HtmlColumnTypeTest(unittest.TestCase):
  """Unit tests for HtmlTextColumnType class."""

  def setUp(self):
    self.column_type = lists.HtmlColumnType()

  def testSafe(self):
    text = ''
    self.assertEqual(text, self.column_type.safe(text))

    text = 'some example text'
    self.assertEqual(text, self.column_type.safe(text))

    text = '<a href="www.example.com">Example</a>'
    self.assertEqual(text, self.column_type.safe(text))

    text = '<script>alert("hacked")</script>'
    self.assertEqual(text, self.column_type.safe(text))


class DateColumnTypeTest(unittest.TestCase):
  """Unit tests for DateColumnType class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.column_type = lists.DateColumnType()

  def testSafe(self):
    """Unit tests for safe function."""
    date = ''
    self.assertEqual('N/A', self.column_type.safe(date))

    date = None
    self.assertEqual('N/A', self.column_type.safe(date))

    date = datetime.datetime.utcnow()
    self.assertEqual(
        dateformat.format(date, lists.DATETIME_FORMAT),
        self.column_type.safe(date))

    date = datetime.date.today()
    self.assertEqual(
        dateformat.format(date, lists.DATE_FORMAT),
        self.column_type.safe(date))
