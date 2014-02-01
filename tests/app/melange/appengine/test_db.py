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

"""Tests for melange.appengine.db."""

import unittest

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.appengine import db as melange_db


class EmailValidatorTest(unittest.TestCase):
  """Unit tests for email_validator function.

  The class contains only very simple test cases to demonstrate that the
  tested function throws an exception on invalid input and returns normally
  otherwise.

  The reason is that email_validator function simply uses a thirdparty
  validator to do the actual job. It is assumed that it works correctly.
  """

  def testValidEmail(self):
    """Tests that the function returns normally on a valid email."""
    melange_db.email_validator(None, 'test@example.com')

  def testInvalidEmail(self):
    """Tests that the function returns ValueError on an invalid email."""
    with self.assertRaises(ValueError):
      melange_db.email_validator(None, 'invalid_email_address')


class LinkValidatorTest(unittest.TestCase):
  """Unit tests for link_validator function.

  The class contains only very simple test cases to demonstrate that the
  tested function throws an exception on invalid input and returns normally
  otherwise.

  The reason is that link_validator function simply uses a thirdparty
  validator to do the actual job. It is assumed that it works correctly.
  """

  def testValidLink(self):
    """Tests that the function returns normally on a valid URL."""
    melange_db.link_validator(None, 'http://www.melange.com')

  def testInvalidLink(self):
    """Tests that the function returns ValueError on an invalid URL."""
    with self.assertRaises(ValueError):
      melange_db.link_validator(None, 'invalid_url_address')


class TestToDict(unittest.TestCase):
  """Unit tests for toDict function."""

  def testForDBModel(self):
    """Tests whether a correct dict is returned for a db model."""
    class Books(db.Model):
      item_freq = db.StringProperty()
      freq = db.IntegerProperty()
      details = db.TextProperty()
      released = db.BooleanProperty()

    entity = Books()
    entity.item_freq = '5'
    entity.freq = 4
    entity.details = 'Test Entity'
    entity.released = True
    entity.put()

    expected_dict = {'freq': 4, 'item_freq': '5', 'details': 'Test Entity',
                     'released': True}
    self.assertEqual(melange_db.toDict(entity), expected_dict)

  def testForNDBModel(self):
    """Tests whether a correct dict is returned for a db model."""
    class Books(ndb.Model):
      item_freq = ndb.StringProperty()
      freq = ndb.IntegerProperty()
      details = ndb.TextProperty()
      released = ndb.BooleanProperty()

    entity = Books()
    entity.item_freq = '5'
    entity.freq = 4
    entity.details = 'Test Entity'
    entity.released = True
    entity.put()

    expected_dict = {'freq': 4, 'item_freq': '5', 'details': 'Test Entity',
                     'released': True}
    self.assertEqual(melange_db.toDict(entity), expected_dict)


class AddFilterToQueryTest(unittest.TestCase):
  """Unit tests for addFilterToQuery function."""

  class TestModel(db.Model):
    """Test model class."""
    foo = db.IntegerProperty()

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a few of TestModel entities
    self.key1 = AddFilterToQueryTest.TestModel(foo=1).put()
    self.key2 = AddFilterToQueryTest.TestModel(foo=2).put()
    self.key3 = AddFilterToQueryTest.TestModel(foo=2).put()
    self.key4 = AddFilterToQueryTest.TestModel(foo=3).put()

  def testForSequentialValues(self):
    """Tests that filter is applied correctly for sequential values."""
    # test for a list
    query = AddFilterToQueryTest.TestModel.all()
    melange_db.addFilterToQuery(
        query, AddFilterToQueryTest.TestModel.foo, [1, 2])
    self.assertSetEqual(
        set(entity.key() for entity in query.fetch(10)),
        set([self.key1, self.key2, self.key3]))

    # test for a tuple
    query = AddFilterToQueryTest.TestModel.all()
    melange_db.addFilterToQuery(
        query, AddFilterToQueryTest.TestModel.foo, (1, 2))
    self.assertSetEqual(
        set(entity.key() for entity in query.fetch(10)),
        set([self.key1, self.key2, self.key3]))

  def testForSequenceWithOneElement(self):
    """Tests that filter is applied correctly for a one element sequence."""
    query = AddFilterToQueryTest.TestModel.all()
    melange_db.addFilterToQuery(
        query, AddFilterToQueryTest.TestModel.foo, [2])
    self.assertSetEqual(
        set(entity.key() for entity in query.fetch(10)),
        set([self.key2, self.key3]))
