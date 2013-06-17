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

"""Logic for model of connection message."""

from google.appengine.ext import db

from soc.models import connection_message as connection_message_model


class QueryBuilder(object):
  """Query builder class for connection_message_model.ConnectionMessage
  model.
  """

  def __init__(self):
    """Initializes a new instance of the class."""
    self._ancestors = []
    self._author = None
    self._keys_only = False
    self._order = None

  def addAncestor(self, ancestor):
    """Adds ancestor to the query.

    Args:
      ancestor: the specified ancestor entity

    Returns:
      self object
    """
    self._ancestors.append(ancestor)
    return self

  def setAuthor(self, author):
    """Sets author for the query.

    Args:
      author: profile_model.Profile entity

    Returns:
      self object
    """
    self._author = author
    return self

  def setKeysOnly(self, keys_only):
    """Sets whether the query is key only or not.

    Args:
      keys_only: If true, the query returns only keys
          instead of complete entities

    Returns:
      self object
    """
    self._keys_only = keys_only
    return self

  def setOrder(self, order):
    """Sets order of the query.

    Args:
      order: string name of the property on which to sort

    Returns:
      self object
    """
    self._order = order
    return self

  def build(self):
    """Builds a new query object based on the properties of the builder.

    Returns:
      a built db.Query obejct
    """
    query = db.Query(connection_message_model.ConnectionMessage,
        keys_only=self._keys_only)
    if self._author is not None:
      query.filter('author', self._author)

    for ancestor in self._ancestors:
      query.ancestor(ancestor)

    return query

  def clear(self):
    """Clears properties of the query."""
    self._ancestors = []
    self._author = None
    self._keys_only = False
    self._order = None
