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

import datetime


def setCacheItems(data_id, items, valid_period=datetime.timedelta(1)):
  """Save a given list of dictionaries in a cached list.

  If a list does not exists with the given data_id, creates a new CachedList. 
  This function should always be run in a transaction.

  Args:
    data_id: A string containing the unique id of the cached list data.
    items: The list of dicts each representing an item in the list.
    valid_through: A datetime.timedelta value indicating the time period the
      cached data should be considered valid. Defaults to one day.
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  cached_list = list_key.get()
  if not cached_list:
    cached_list = cached_list_model.CachedList(id=data_id)
  cached_list.list_data = items
  cached_list.valid_through = datetime.datetime.now() + valid_period
  cached_list.is_processing = False
  cached_list.put()


def getCachedItems(data_id, start=0, limit=None):
  """Retrieve stored items from a cached list.

  Args:
    data_id: A string containing the unique id of the cached list data.
    start: The starting index of the items returned.
    limit: Number of items to be returned. If the number of items in the list,
      after given starting index is less than specified here, only that number
      of items will be returned. If None, all the items after the starting index
      are returned.

  Returns:
    A list of dicts each representing an item in the cached list.
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with data id %s does not exist' % data_id)

  if limit:
    return cached_list.list_data[start:(start + limit)]
  else:
    return cached_list.list_data[start:]


def isCachedListExists(data_id):
  """Check whether a cached list with a data_id exists

  Args:
    data_id: A string containing the unique id of the cached list data.

  Returns:
    True if a list with the given data_id exists, False otherwise.  
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  return bool(list_key.get())


def isValid(data_id):
  """Checks whether the cache is valid according to the datastore entities.

  This function checks whether the cached list is updated within the specified
  time period.

  Args:
    data_id: A string containing the unique id of the cached list data.

  Raises:
    ValueError: if a cached list does not exist for the given list id.  

  Returns:
    True if the data in the cache is updated with the datastore entities. False
    if not.
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with data id %s does not exist' % data_id)

  if cached_list.valid_through and \
         cached_list.valid_through > datetime.datetime.now():
    return True
  else:
    return False


def isProcessing(data_id):
  """Checks whether a process collecting list data for this list is running.
  
  Args:
    data_id: A string containing the unique id of the cached list data.

  Raises:
    ValueError: if a cached list does not exist for the given list id.  

  Returns:
    True if a caching process is running. False if not.
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with data id %s does not exist' % data_id)

  return cached_list.is_processing


def setProcessing(data_id):
  """Changes the list state to indicate a caching process is running.

  Args:
    data_id: A string containing the unique id of the cached list data.

  Raises:
    ValueError: if a cached list does not exist for the given list id.
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  cached_list = list_key.get()

  if not cached_list:
    raise ValueError('A cached list with data id %s does not exist' % data_id)

  cached_list.is_processing = True
  cached_list.put()


def createEmptyProcessingList(data_id):
  """Create a cached list with empty list data and in processing state.

  Args:
    data_id: A string containing the unique id of the cached list data.

  Raises:
    ValueError: if a cached list already exist for the given list id.
  """
  list_key = ndb.Key(cached_list_model.CachedList, data_id)
  cached_list = list_key.get()

  if cached_list:
    raise ValueError('A cached list with data id %s already exists' % data_id)

  cached_list = cached_list_model.CachedList(id=data_id)
  cached_list.list_data = []
  cached_list.is_processing = True
  cached_list.put()
