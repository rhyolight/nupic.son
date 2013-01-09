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

import unittest

from soc.views.helper import lists


class ColumnTypeFactoryTest(unittest.TestCase):
  """Unit tests for ColumnTypeFactory class.
  """

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
