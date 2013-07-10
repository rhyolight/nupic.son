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


# TODO: Complete this list
CACHED_ENTITY_TYPES = ['GSoCOrganization', 'GSoCProjects', 'GCITasks']


class List(object):
  """Represents a list."""

  def __init__(self, index, query, columns, operations_func=None, cached=False):
    """Initialize a list object.

    Args:
      index: Index of the list in the page it is displayed.
      query: Query that can be used to fetch items for this. Entities related
        to all the list items in this list, satisfy filters in this query.
      columns: A list of Column objects describing columns in the list.  
      operations_func: A function that will return operations supported by the
        jqgrid list row. This function should take one argument, representing
        the relevant list item.
      cached: A boolean indicating whether this list should be cached using a
        CachedList entity.  
    """
    self._index = index
    self._query = query
    self._columns = columns

    if operations_func:
      self._getOperations = operations_func
    else:
      self._getOperations = _getDefaultOperations

    self._cached = cached

  def _getItems(self, start, limit):
    """Get list items in this list.

    If the list can be cached but not cached a mapreduce will be started to
    cache list items, and live data will be sent to the current request.  

    Args:
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Retutns:
      A list of dicts each representing an item in the list.  
    """
    if self.isInCache():
      return cached_list.getCachedItems(self._list_id, start, limit + 1)
    elif self._cached:
      # The list can be cached but cached list is not found.
      entity_kind = '%s.%s' % \
        (self._query._model_class.__module__, self._query._model_class.__name__)
      column_defs = [{c.name:c.column_def} for c in self._columns]
      query_pickle = pickle.dumps(self._query)

      cache_list_pipline = cache_list_items.CacheListsPipeline(
           entity_kind, column_defs, query_pickle)

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

  def isInCache(self):
    """Check whether the list is cached in a CachedList entity."""
    # TODO:(Aruna) Take into consideration whether the list data is valid as
    # well.
    return self._cached and \
        cached_list.isCachedListExists(getListId(self._query))

  def getListData(self, start, limit):
    """Get 'data' section of the json object expected by jqgrid.

    Spectification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Args:
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Returns: A dict containing the list data.
    """
    items = self._getItems(start, limit + 1)
    data = [{'columns':item, 'operations': self._getOperations(item)}
               for item in items[0:limit]]

    next_item = self._getNext(items, start, limit + 1)

    if not start:
      start = ''

    return {'data': {start: data}, 'next': next_item}


def _getDefaultOperations(item):
  # TODO:(Aruna) Complete this method
  return {}


def getListId(query):
  """Get a unique id for cached list related to a query"""
  return (hash(pickle.dumps(query)))


class Column(object):
  """Represents a column in a list.
  
  Args:
    col_id: A unique identifier of this column.
    name: The header of the column that is shown to the user.
    func_string: The string with content of a code of a function to be called 
          when rendering this column for a single entity. This function should 
          take an entity as an argument.
    width: The width of the column.
    resizable: Whether the width of the column should be resizable by the
               end user.
    hidden: Whether the column should be hidden by default.
    searchhidden: Whether this column should be searchable when hidden. 
  """
  def __init__(self, col_id, name, func_string, width=None, resizable=True,
               hidden=False, searchhidden=True, options=None):
    self.col_id = col_id;
    self.name = name;
    self.width = width
    self.resizable = resizable
    self.hidden = hidden
    self.searchhidden = hidden
    self.options = options

    if not (callable(eval(func_string))):
      raise TypeError('String %s does not represent a callable function.')
    else:
      self.func_string = func_string


def toListItemDict(entity, column_def):
  """Create a list item from a datastore entity.

  Args:
    entity: The datastore entity regarding a list item.
    column_def: a dictionary that has column names of the list as keys, and
      lambda functions that create the value for that column for a list item as
      values. These functions should take one parameter, the entity relevant to
      one list item.

  Returns:
    A dictionary describing a list item.
  """
  output = {}
  for col, func in column_def.items():
    output[col] = func(entity)
  return output
