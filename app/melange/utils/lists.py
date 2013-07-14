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

from soc.mapreduce import cache_list_items

from melange.logic import cached_list

import pickle


class List(object):
  """Represents a list."""

  def __init__(self, list_id, index, columns, operations_func=None, cached=False):
    """Initialize a list object.

    Args:
      list_id: A unique id for the list.
      index: Index of the list in the page it is displayed.
      columns: A list of Column objects describing columns in the list.  
      operations_func: A function that will return operations supported by the
        jqgrid list row. This function should take one argument, representing
        the relevant list item.
      cached: A boolean indicating whether this list should be cached using a
        CachedList entity.  
    """
    self._list_id = list_id
    self._index = index
    self._columns = columns

    if operations_func:
      self._getOperations = operations_func
    else:
      self._getOperations = _getDefaultOperations

    self._cached = cached

  def _getItems(self, query, start, limit):
    """Get list items in this list.

    If the list can be cached but not cached a mapreduce will be started to
    cache list items, and live data will be sent to the current request.  

    Args:
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Retutns:
      A list of dicts each representing an item in the list.  
    """
    # Check whether the list is cached in a CachedList entity.
    # TODO:(Aruna) Take into consideration whether the list data is valid as
    # well.
    if self._cached and cached_list.isCachedListExists(getDataId(query)):
      return cached_list.getCachedItems(getDataId(query), start, limit + 1)
    elif self._cached:
      # The list can be cached but cached list is not found.
      entity_kind = '%s.%s' % \
        (query._model_class.__module__, query._model_class.__name__)
      query_pickle = pickle.dumps(query)

      cache_list_pipline = cache_list_items.CacheListsPipeline(
           self._list_id, entity_kind, query_pickle)

      cache_list_pipline.start()

      # TODO: fetch live data for this request
    else:
      # TODO: fetch live data
      pass

  def _getNext(self, items, start, limit):
    """Get the index of the first elemnet of the next batch.

    When jqgrid asks for batches of list items it will use start (key of the
    first item)  and limit (number of items in the batch) parameters to define
    a batch. This method is used to get the key of the first element of the
    next batch.

    Args:
      items: A list of items retrieved from the datastore for this batch.
      start: key of the first element of this batch.
      limit: No of items requested from the datastore for this batch.

    Returns:
      The key of the next element if current batch is not the last batch  
    """
    if len(items) < limit:
      return 'done'
    else:
      if self.isInCache():
        return start + limit - 1
      else:
        return str(items[-1].key())


  def getListData(self, query, start, limit):
    """Get 'data' section of the json object expected by jqgrid.

    Spectification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Args:
      query: Query that can be used to fetch items for this. Entities related
        to all the list items in this list, satisfy filters in this query.
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Returns: A dict containing the list data.
    """
    items = self._getItems(query, start, limit + 1)
    data = [{'columns':item, 'operations': self._getOperations(item)}
               for item in items[0:limit]]

    next_item = self._getNext(items, start, limit + 1)

    if not start:
      start = ''

    return {'data': {start: data}, 'next': next_item}


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
  """Represents a column in a list.

  Args:
    col_id: A unique identifier of this column.
    name: The header of the column that is shown to the user.
    col_func: A function to be called when rendering this column for a single
      entity. This function should take an entity as an argument.
    width: The width of the column.
    resizable: Whether the width of the column should be resizable by the
      end user.
    hidden: Whether the column should be hidden by default.
    searchhidden: Whether this column should be searchable when hidden. 
  """
  def __init__(self, col_id, name, col_func, width=None, resizable=True,
               hidden=False, searchhidden=True, options=None):
    self.col_id = col_id;
    self.name = name;
    self.width = width
    self.resizable = resizable
    self.hidden = hidden
    self.searchhidden = hidden
    self.options = options

    if not (callable(col_func)):
      raise TypeError('%s is not a callable function.' % str(col_func))
    else:
      self.col_func = col_func


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
key = Column('key', 'Key', (lambda entity: '%s/%s' % (
             entity.parent_key().name(), entity.key().id())), hidden=True)
student = Column('student', 'Student', lambda entity: entity.parent().name)
title = Column('title', 'Title', lambda entity: entity.title)

GSOC_PROJECTS_LIST = List(GSOC_PROJECTS_LIST_ID, 0, [key, student], cached=True)


LISTS = {
  GSOC_PROJECTS_LIST_ID: GSOC_PROJECTS_LIST
}
