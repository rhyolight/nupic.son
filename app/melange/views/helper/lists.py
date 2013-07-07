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

"""Contains helpers for lists."""

from melange.logic import cached_list


# TODO: Complete this list
CACHED_ENTITY_TYPES = ['GSoCOrganization', 'GSoCProjects', 'GCITasks']


class List(object):
  """Represents a list."""

  def __init__(self, item_type, filter_value, idx, operations_func=None):
    """Initialize a list object.

    Args:
      item_type: Type of items cached in the list.
      filter_value: The value of the property used to filter items for this 
        from all the entities of the kind, item_type.
      idx: Index of the list in the page it is displayed
      operations_func: A function that will return operations supported by the
        jqgrid list row. This function should take one argument, representing
        the relevant list item.
    """
    self._list_id = getListId(item_type, filter_value)
    self._idx = idx
    if operations_func:
      self._getOperations = operations_func
    else:
      self._getOperations = _getDefaultOperations

  def _getItems(self, start, limit):
    return cached_list.getCachedItems(self._list_id, start, limit + 1)

  def _getNext(self, items, start, limit):
    if len(items) < limit:
      return "done"
    else:
      return start + limit - 1

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
    data = [{"columns":item, "operations": self._getOperations(item)}
               for item in items[0:limit]]

    next_item = self._getNext(items, start, limit + 1)

    if not start:
      start = 0

    return {"data": {start: data}, "next": next_item}


def _getDefaultOperations(item):
  # TODO(Aruna): Complete this method
  return {}


def getListId(item_type, filter_value):
  if item_type not in CACHED_ENTITY_TYPES:
    raise TypeError("%s is not an item type cached in cached lists" % item_type)
  return("%s %s" % (item_type, filter_value))
