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

"""Module containing list utilities."""

# These imports are needed for the toListItemDict function, to avoid 
# 'KindError' by func(entity) if func access a db.ReferenceProperty of the 
# entity.
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.timeline import GSoCTimeline

from google.appengine.ext import ndb
from google.appengine.ext import db

from soc.mapreduce import cache_list_items

from melange.logic import cached_list

import pickle


FINAL_BATCH = 'done'


class List(object):
  """Represents a list."""

  def __init__(self, list_id, index, model_class, columns, datastore_reader,
               cache_reader=None, operations_func=None):
    """Initialize a list object.

    Args:
      list_id: A unique id for the list.
      index: Index of the list in the page it is displayed.
      model_class: Model class of the entities used to create list items.
      columns: A list of Column objects describing columns in the list.
      datastore_reader: A ListReader to read data from the datastore.
      cache_reader: A ListReader to read list data from the cache.
      operations_func: A function that will return operations supported by the
        jqgrid list row. This function should take one argument, representing
        the relevant list item.
    """
    self._list_id = list_id
    self._index = index
    self.model_class = model_class
    self.columns = columns
    self._cache_reader = cache_reader
    self._datastore_reader = datastore_reader

    if operations_func:
      self._getOperations = operations_func
    else:
      self._getOperations = _getDefaultOperations

  def getListData(self, query, start=None, limit=50):
    """Get 'data' section of the json object expected by jqgrid.

    Spectification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Args:
      query: Query that can be used to fetch items for this list. Entities
        related to all the list items in this list, satisfy filters in this
        query.
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Returns: A dict containing the list data.
    """
    if self._cache_reader:
      items, next_item = self._cache_reader.getListData(query, start, limit)
      if not items:
        # A cache miss. Fetch data using the datastore reader.
        items, next_item = self._datastore_reader.getListData(
                                                      query, start, limit)
    else:
      items, next_item = self._datastore_reader.getListData(query, start, limit)

    data = [{'columns':item, 'operations': self._getOperations(item)}
               for item in items[0:limit]]

    if not start:
      start = ''

    return {'data': {start: data}, 'next': next_item}


class ListDataReader(object):
  """Base class for list data readers."""
  def __init__(self, list_id):
    """Initializes a ListDataReader.

    Args:
      list_id: The id of the list this reader reads data for.
    """
    self._list_id = list_id

  def getListData(self, query, start, limit):
    """Get list items for a list.

    Implementing subclasses must override this method.

    Args:
      query: Query that will be used to fetch datastore entities relevant to the
        list.
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Returns:
      A Tuple whose first element is a list of list items and whose second
      element is the index of the first list item of the next batch. None if
      the list items cannot be read.
    """
    raise NotImplementedError


class CacheReader(ListDataReader):
  """List reader for reding list data from cache."""
  def __init__(self, list_id):
    super(CacheReader, self).__init__(list_id)

  def getListData(self, query, start=None, limit=50):
    """See ListDataReader.getListData for specification."""
    data_id = getDataId(query)

    if cached_list.isCachedListExists(data_id):
      if cached_list.isListValid(data_id):
        return (cached_list.getCachedItems(data_id), FINAL_BATCH)
      else:
        self._start_caching(data_id, query)

        # return None because cache is not hit
        return None, None

    else:
      self._start_caching(data_id, query)

      # return None because cache is not hit
      return None, None

  def _start_caching(self, data_id, query):
    if cached_list.isCachedListExists(data_id) and \
           cached_list.isProcessRunning(data_id):
      return
    # Create an empty cache list, if a cache list with this data id does not
    # exist
    cached_list.cacheItems(data_id, [])

    entity_kind = '%s.%s' % \
        (query._model_class.__module__, query._model_class.__name__)
    query_pickle = pickle.dumps(query)

    cache_list_pipline = cache_list_items.CacheListsPipeline(
         self._list_id, entity_kind, query_pickle)

    cache_list_pipline.start()

    # Set the process id regarding this cache list
    cached_list.cacheProcessStarted(data_id, cache_list_pipline.pipeline_id)


class DatastoreReaderForDB(ListDataReader):
  """List reader for reading list data from datastore using db queries."""
  def __init__(self, list_id):
    super(DatastoreReaderForDB, self).__init__(list_id)

  def getListData(self, query, start=None, limit=50):
    """See ListDataReader.getListData for specification."""
    if start:
      query.filter('__key__ >=', db.Key(start))

    entities = query.fetch(limit + 1)

    if len(entities) == limit + 1:
      next_key = str(entities[-1].key())
    else:
      next_key = FINAL_BATCH

    col_funcs = [(c.name, c.getValue) for c in getList(self._list_id).columns]
    items = [toListItemDict(entity, col_funcs) for entity in entities]
    return (items[:limit], next_key)


class DatastoreReaderForNDB(ListDataReader):
  """List reader for reading list data from datastore using ndb queries."""
  def __init__(self, list_id):
    super(DatastoreReaderForNDB, self).__init__(list_id)

  def getListData(self, query, start=None, limit=50):
    """See ListDataReader.getListData for specification."""
    if start:
      model_class = getList(self._list_id).model_class
      query = query.filter(model_class.key >= ndb.Key(urlsafe=start))

    entities = query.fetch(limit + 1)

    if len(entities) == limit + 1:
      next_key = str(entities[-1].key.to_old_key())
    else:
      next_key = FINAL_BATCH

    col_funcs = [(c.name, c.getValue) for c in getList(self._list_id).columns]
    items = [toListItemDict(entity, col_funcs) for entity in entities]
    return (items[:limit], next_key)


def _getDefaultOperations(item):
  # TODO:(Aruna) Complete this method
  return {}


def getDataId(query):
  """Get a unique 'data id' for a cached list related to a query.

  This id is used to identify data in a list. Two lists with the same data
  should have the same 'data id'.

  Args:
    query: A query used to create a list.

  Returns:
    A string containing an id that is unique for the given query.  
  """
  # The query is pickled unpickled and pickled again, and hash is taken.
  # The reason for pickling twice is that the hash is different between the
  # original object's pickle string and the one's that is created by unpickling.
  # But it is the same for all objects created by pickling and upickling many
  # times after that.
  return str(hash(pickle.dumps(pickle.loads(pickle.dumps(query)))))


class Column(object):
  """Base class for a column in a list.

  Args:
    col_id: A unique identifier of this column.
    name: The header of the column that is shown to the user.
    width: The width of the column.
    resizable: Whether the width of the column should be resizable by the
      end user.
    hidden: Whether the column should be hidden by default.
    searchhidden: Whether this column should be searchable when hidden. 
  """
  def __init__(self, col_id, name, width=None, resizable=True, hidden=False,
               searchhidden=True, options=None):
    self.col_id = col_id
    self.name = name
    self.width = width
    self.resizable = resizable
    self.hidden = hidden
    self.searchhidden = hidden
    self.options = options

  def getValue(self):
    """This method is called when rendering the column for a single entity.

    This must be overridden by implementing subclasses.

    Args:
      entity: The entity from which data for this column is taken from.

    Returns:
      A rendered value for the column.
    """
    raise NotImplementedError


def toListItemDict(entity, column_def):
  """Create a list item from a datastore entity.

  Args:
    entity: The datastore entity regarding a list item.
    column_def: A list of tuples. Each has a column name of the list, and the
      lambda functions that create the value for that column for a list item.
      These functions should take one parameter, the entity relevant to one list
      item.

  Returns:
    A dictionary describing a list item.
  """
  output = {}
  for col, func in column_def:
    output[col] = func(entity)
  return output


def getList(list_id):
  """Get the list instance relevant to a list id.

  Args:
    list_id: Unique id of the list.

  Returns:
    A List object with the given id.
  """
  return LISTS[list_id]


# A list of list ids
GSOC_PROJECTS_LIST_ID = 'gsoc_projects'


# GSoCProjects list
from soc.modules.gsoc.models import project


class SimpleColumn(Column):
  """Column object to display a simple attribute.
  
  When simply a value of an attribute of the entity is needed to be displayed
  in a column this class is used. The column id must be the same as the
  relevant attribute name.
  """
  def getValue(self, entity):
    return getattr(entity, self.col_id)


class KeyColumn(Column):
  """Column object to represent the unique key of the project."""
  def getValue(self, entity):
    """See Column.getValue for specification"""
    return '%s/%s' % (entity.parent_key().name(), entity.key().id())


class StudentColumn(Column):
  """Column object to represent the student"""
  def getValue(self, entity):
    """See Column.getValue for specification"""
    return entity.parent_key().name()


class OraganizationColumn(Column):
  """Column object to represent the organization"""
  def getValue(self, entity):
    """See Column.getValue for specification"""
    return entity.org.name


key = KeyColumn('key', 'Key', hidden=True)
student = StudentColumn('student', 'Student')
title = SimpleColumn('title', 'Title')
org = OraganizationColumn('org', 'Organization')
status = SimpleColumn('status', 'Status')

cache_reader = CacheReader(GSOC_PROJECTS_LIST_ID)
datastore_reader = DatastoreReaderForDB(GSOC_PROJECTS_LIST_ID)

GSOC_PROJECTS_LIST = List(GSOC_PROJECTS_LIST_ID, 0, project.GSoCProject,
                          [title, org, status], datastore_reader,
                          cache_reader=cache_reader)


LISTS = {
  GSOC_PROJECTS_LIST_ID: GSOC_PROJECTS_LIST
}
