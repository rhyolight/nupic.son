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

from melange.models import cached_list as cached_list_model
from melange.utils import lists

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project as project_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


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


class TestSimpleColumn(unittest.TestCase):
  """Unit tests for SimpleColumn class."""

  def testGetListData(self):
    """Tests getListData method."""
    class TestModel(db.Model):
      name = db.StringProperty()
      value = db.IntegerProperty()

    test_entity = TestModel(name='test_name', value=1)

    name_column = lists.SimpleColumn('name', 'Name')
    value_column = lists.SimpleColumn('value', 'Value')

    self.assertEqual(test_entity.name, name_column.getValue(test_entity))
    self.assertEqual(test_entity.value, value_column.getValue(test_entity))


class TestGSoCProjectsColumns(unittest.TestCase):
  """Unit tests for implementations of Column class for GSoCProjects."""

  def setUp(self):
    self.program = seeder_logic.seed(program_model.GSoCProgram)
    self.organization = seeder_logic.seed(org_model.GSoCOrganization,
        {'scope': self.program, 'program': self.program})
    self.student = seeder_logic.seed(
        profile_model.GSoCProfile, {'key_name': 'student'})

    # seed a project for above organization, program and student
    project_properties = {
        'parent': self.student,
        'scope': self.program,
        'org': self.organization
    }

    self.project = seeder_logic.seed(
        project_model.GSoCProject, project_properties)

  def testKeyColumn(self):
    """Tests KeyColumn class."""
    key_column = lists.KeyColumn('key', 'Key')
    expected_value = '%s/%s' % (
        self.project.parent_key().name(), self.project.key().id())
    self.assertEqual(expected_value, key_column.getValue(self.project))

  def testStudentColumn(self):
    """Tests StudentColumn class."""
    student_column = lists.StudentColumn('student', 'Student')
    expected_value = self.student.key().name()
    self.assertEqual(expected_value, student_column.getValue(self.project))

  def testOrganizationColumn(self):
    """Tests OrganizationColumn class."""
    org_column = lists.OraganizationColumn('organization', 'Organization')
    expected_value = self.organization.name
    self.assertEqual(expected_value, org_column.getValue(self.project))


class TestDatastoreReaderForDB(unittest.TestCase):
  """Unit tests for DatastoreReaderForDB class."""

  def testGetListData(self):    
    """Tests getGetListData method."""
    class TestDBModel(db.Model):
      name = db.StringProperty()
      value = db.IntegerProperty()

    for i in range(10):
      TestDBModel(name='name %s' % i, value=i, key_name='id %s' % i).put()

    name = lists.SimpleColumn('name', 'Name')
    value = lists.SimpleColumn('value', 'Value')

    list_reader = lists.DatastoreReaderForDB('test_list')

    test_list = lists.List('test_list', 0, TestDBModel, [name, value],
                           list_reader)

    # A stub for getList function in lists module.
    def dummyGetList(list_id):
      return test_list

    lists.getList = dummyGetList

    query = TestDBModel.all()
    start = str(TestDBModel.get_by_key_name('id 3').key())

    item_list, next_key = list_reader.getListData(query, start, 5)

    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(3, 8)]
    expected_next_key = str(TestDBModel.get_by_key_name('id 8').key())

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)


class TestDatastoreReaderForNDB(unittest.TestCase):
  """Unit tests for DatastoreReaderForDB class."""

  def testGetListData(self):
    """Tests getGetListData method."""
    class TestNDBModel(ndb.Model):
      name = ndb.StringProperty()
      value = ndb.IntegerProperty()

    for i in range(10):
      TestNDBModel(name='name %s' % i, value=i, id='id %s' % i).put()

    name = lists.SimpleColumn('name', 'Name')
    value = lists.SimpleColumn('value', 'Value')

    list_reader = lists.DatastoreReaderForNDB('test_list')

    test_list = lists.List('test_list', 0, TestNDBModel, [name, value],
                           list_reader)

    # A stub for getList function in lists module.
    def dummyGetList(list_id):
      return test_list

    lists.getList = dummyGetList

    query = TestNDBModel.query()
    start = str(ndb.Key(TestNDBModel, 'id 3').to_old_key())

    item_list, next_key = list_reader.getListData(query, start, 5)

    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(3, 8)]
    expected_next_key = str(ndb.Key(TestNDBModel, 'id 8').to_old_key())

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)


class TestCacheReader(unittest.TestCase):
  """Unit tests for CacheReader class"""
  # TODO:(Aruna)complete this class
  pass
