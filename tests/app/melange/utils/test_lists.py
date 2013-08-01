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

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project as project_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


NDB_TEST_LIST_ID = 'test_list_ndb'
DB_TEST_LIST_ID = 'test_list_db'


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


class TestDBModel(db.Model):
  """Used to create db entities for tests."""
  name = db.StringProperty()
  value = db.IntegerProperty()


class TestNDBModel(ndb.Model):
  """Used to create ndb entities for tests."""
  name = ndb.StringProperty()
  value = ndb.IntegerProperty()


class TestDatastoreReaderForDB(unittest.TestCase):
  """Unit tests for DatastoreReaderForDB class."""
  def setUp(self):
    for i in range(10):
      TestDBModel(name='name %s' % i, value=i, key_name='id %s' % i).put()

    name = lists.SimpleColumn('name', 'Name')
    value = lists.SimpleColumn('value', 'Value')

    self.list_reader = lists.DatastoreReaderForDB()

    test_list = lists.List(DB_TEST_LIST_ID, 0, TestDBModel, [name, value],
                           self.list_reader)

    # Register the above list in the lists module
    lists.LISTS[DB_TEST_LIST_ID] = test_list

  def testGetListDataWithStartAndLimit(self):
    """Tests getGetListData method with parameters start and limit specified."""

    query = TestDBModel.all()
    start = str(TestDBModel.get_by_key_name('id 3').key())

    item_list, next_key = self.list_reader.getListData(
        DB_TEST_LIST_ID, query, start, 5)

    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(3, 8)]
    expected_next_key = str(TestDBModel.get_by_key_name('id 8').key())

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)

  def testGetListDataWithStart(self):
    """Tests getGetListData with parameter start specified but not limit."""
    query = TestDBModel.all()
    start = str(TestDBModel.get_by_key_name('id 3').key())

    item_list, next_key = self.list_reader.getListData(
        DB_TEST_LIST_ID, query, start=start)

    # All the items after specified id should be returned. Returned next key
    # should indicate final batch.
    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(3, 10)]
    expected_next_key = lists.FINAL_BATCH

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)

  def testGetListDataWithLimit(self):
    """Tests getGetListData with parameter limit specified but not start."""
    query = TestDBModel.all()

    item_list, next_key = self.list_reader.getListData(
        DB_TEST_LIST_ID, query, limit=5)

    # First five entities should be returned.
    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(0, 5)]
    expected_next_key = str(TestDBModel.get_by_key_name('id 5').key())

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)

  def testGetListDataWithoutStartOrLimit(self):
    """Tests getGetListData with parameter start or limit not specified."""
    query = TestDBModel.all()

    item_list, next_key = self.list_reader.getListData(
        DB_TEST_LIST_ID, query)

    # All the items in the list should be returned. Returned next key should
    # indicate final batch.
    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(0, 10)]
    expected_next_key = lists.FINAL_BATCH

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)


class TestDatastoreReaderForNDB(unittest.TestCase):
  """Unit tests for DatastoreReaderForDB class."""
  def setUp(self):
    for i in range(10):
      TestNDBModel(name='name %s' % i, value=i, id='id %s' % i).put()

    name = lists.SimpleColumn('name', 'Name')
    value = lists.SimpleColumn('value', 'Value')

    self.list_reader = lists.DatastoreReaderForNDB()

    test_list = lists.List(NDB_TEST_LIST_ID, 0, TestNDBModel, [name, value],
                           self.list_reader)

    lists.LISTS[NDB_TEST_LIST_ID] = test_list

  def testGetListDataWWithStartAndLimit(self):
    """Tests getGetListData method."""
    query = TestNDBModel.query()
    start = str(ndb.Key(TestNDBModel, 'id 3').to_old_key())

    item_list, next_key = self.list_reader.getListData(
        NDB_TEST_LIST_ID, query, start, 5)

    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(3, 8)]
    expected_next_key = str(ndb.Key(TestNDBModel, 'id 8').to_old_key())

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)

  def testGetListDataWithStart(self):
    """Tests getGetListData with parameter start specified but not limit."""
    query = TestNDBModel.query()
    start = str(ndb.Key(TestNDBModel, 'id 3').to_old_key())

    item_list, next_key = self.list_reader.getListData(
        NDB_TEST_LIST_ID, query, start=start)

    # All the items after specified id should be returned. Returned next key
    # should indicate final batch.
    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(3, 10)]
    expected_next_key = lists.FINAL_BATCH

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)

  def testGetListDataWithLimit(self):
    """Tests getGetListData with parameter limit specified but not start."""
    query = TestNDBModel.query()

    item_list, next_key = self.list_reader.getListData(
        NDB_TEST_LIST_ID, query, limit=5)

    # First five entities should be returned.
    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(0, 5)]
    expected_next_key = str(ndb.Key(TestNDBModel, 'id 5').to_old_key())

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)

  def testGetListDataWithoutStartOrLimit(self):
    """Tests getGetListData with parameter start or limit not specified."""
    query = TestNDBModel.query()

    item_list, next_key = self.list_reader.getListData(
        NDB_TEST_LIST_ID, query)

    # All the items in the list should be returned. Returned next key should
    # indicate final batch.
    expected_list = [{'Name': 'name %s' % i, 'Value': i} for i in range(0, 10)]
    expected_next_key = lists.FINAL_BATCH

    self.assertListEqual(item_list, expected_list)
    self.assertEqual(next_key, expected_next_key)


class TestCacheReader(unittest.TestCase):
  """Unit tests for CacheReader class"""
  # TODO:(Aruna)complete this class
  pass
