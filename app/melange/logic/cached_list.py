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

"""Contains logic concerning cached lists."""

from google.appengine.ext import ndb

from melange.models import cached_list as cached_list_model


def cacheItems(list_id, items):
  """Save a given list of dictionaries in a cached list.
  
  If a list does not exists with the given list_id creates a new CachedList. 
  This function should always be run in a transaction.

  Args:
    list_id: A string containing the unique id of the CachedList entity.
    items: The list of dicts each representing an item in the list.
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()
  if not cached_list:
    cached_list = cached_list_model.CachedList(id=list_id)
  cached_list.list_data.extend(items)
  cached_list.put()


def getCachedItems(list_id, start, limit):
  """Retrieve stored items from a cached list.

  Args:
    list_id: The unique id of the CachedList entity
    start: The starting index of the items returned
    limit: Number of items returned. If the number of items in the list, after
      given starting index is less than specified here, only that number of
      items will be returned

  Returns:
    A list of dicts each representing an item in the cached list
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with id %s does not exist' % list_id)

  return cached_list.list_data[start:(start+limit)]


def isCachedListExists(list_id):
  """Check whether a cached list with a list_id exists

  Args:
    list_id: Id of the list.

  Returns:
    True if a list with the given list_id exists, False otherwise.  
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)

  if list_key.get():
    return True
  else:
    return False

