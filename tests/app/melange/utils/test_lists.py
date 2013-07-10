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

"""Tests for functions in the lists module."""

import unittest

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.utils import lists


class TestToListItemDict(unittest.TestCase):
  """Unit tests for toListItemDict function."""

  def testToListItemDict(self):
    """Tests whether correct is dict is returned for a db model."""
    class Book(db.Model):
      item_freq = db.StringProperty()
      freq = db.IntegerProperty()
      details = db.TextProperty()
      released = db.BooleanProperty()
      owner = db.ReferenceProperty()

    class Author(db.Model):
      name = db.StringProperty()

    entity = Book()
    entity.item_freq = '5'
    entity.freq = 4
    entity.details = 'Test Entity'
    entity.released = True
    entity.owner = Author(name='Foo Bar').put()
    entity.put()

    columns = {
        'details': lambda ent: ent.details,
        'freq': lambda ent: '%s - %s' % (ent.item_freq, ent.freq),
        'released': lambda ent: "Yes" if ent.released else "No",
        'author': lambda ent: ent.owner.name
    }

    list_item_dict = lists.toListItemDict(entity, columns)

    expected_dict = {'details': 'Test Entity', 'freq': '5 - 4',
                     'released': 'Yes', 'author': 'Foo Bar'}

    self.assertEqual(list_item_dict, expected_dict)
