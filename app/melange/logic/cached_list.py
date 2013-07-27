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

from soc.mapreduce import cache_list_items


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
    cached_list = cached_list_model.CachedList(id=list_id, valid=False,
                                               cache_process_id=None)
  cached_list.list_data.extend(items)
  cached_list.put()


def getCachedItems(list_id, start=0, limit=None):
  """Retrieve stored items from a cached list.

  Args:
    list_id: The unique id of the CachedList entity.
    start: The starting index of the items returned.
    limit: Number of items to be returned. If the number of items in the list,
      after given starting index is less than specified here, only that number
      of items will be returned. If None, all the items after the starting index
      are returned.

  Returns:
    A list of dicts each representing an item in the cached list.
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with id %s does not exist' % list_id)

  if limit:
    return cached_list.list_data[start:(start + limit)]
  else:
    return cached_list.list_data[start:]


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


def isListValid(list_id):
  """Checks whether the cache is valid according to the datastore entities.

  Args:
    list_id: Id of the list.

  Raises:
    ValueError if a cached list does not exist for the given list id.  

  Returns:
    True if the data in the cache is updated with the datastore entities. False
    if not (if cache contains stale data).
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with id %s does not exist' % list_id)

  if cached_list.valid:
    # Cached list is set as valid. If no caching process is run this list is
    # considered as valid.
    cache_pipeline = cache_list_items.CacheListsPipeline.from_id(
                       cached_list.cache_process_id)
    if cache_pipeline:
      return cache_pipeline.has_finalized
    else:
      # Pipeline hase been cleaned.
      return True


def setInvalid(list_id):
  """Sets the list as invalid.
  
  This function should be called after updating one or more datastore entities
  relevant to a cached list.
  
  Args:
    list_id: Id used to identify a CachedList entity.
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with id %s does not exist' % list_id)

  cached_list.valid = False
  cached_list.put()


def isProcessRunning(list_id):
  """Checks whether a process collecting list data for this list is running."""
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with id %s does not exist' % list_id)

  cache_pipeline = cache_list_items.CacheListsPipeline.from_id(
                       cached_list.cache_process_id)
  return cache_pipeline and not cache_pipeline.has_finalized


def cacheProcessStarted(list_id, process_id):
  """Updates information about background processes regarding a cached list.

  This function should be called when a background process to cache items for
  a list is started.

  Args:
    list_id: Id used to identify a CachedList entity.
    process_id: Id of the background process that caches data.
  """
  list_key = ndb.Key(cached_list_model.CachedList, list_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with id %s does not exist' % list_id)

  cached_list.cache_process_id = process_id
  cached_list.valid = True
  cached_list.put()
