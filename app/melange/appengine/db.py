# Copyright 2008 the Melange authors.
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

"""App Engine datastore related functions and classes."""

from django.core import validators

from google.appengine.ext import db
from google.appengine.ext import ndb


def email_validator(property, value):
  """Validates whether the input value for the specified property
  is a valid email address.

  The function signature is required by NBD API. Property parameter is not
  actually used in this function.

  Args:
    property: validated model property
    value: value to validate

  Raises:
    ValueError: if the specified value is not a valid email address.
  """
  try:
    # use internal django's validator
    validators.validate_email(value)
  except Exception:
    raise ValueError('%s is not a valid email address.' % value)


_LINK_VALIDATOR = validators.URLValidator()
def link_validator(property, value):
  """Validates whether the input value for the specified property
  is a valid URL.

  The function signature is required by NBD API. Property parameter is not
  actually used in this function.

  Args:
    property: validated model property
    value: value to validate

  Raises:
    ValueError: if the specified value is not a valid URL.
  """
  try:
    # use internal django's validator
    _LINK_VALIDATOR(value)
  except Exception:
    raise ValueError('%s is not a valid URL.' % value)


def toDict(entity):
  """Returns a dict with all specified values of a datastore entity.

  This function can be dropped when entire transition to ndb API is complete.

  Args:
    entity: datastore entity to be put in a dictionary.

  Raises:
    TypeError: if the specified entity is not App Engine datastore entity.
  """
  if isinstance(entity, db.Model):
    return db.to_dict(entity)
  elif isinstance(entity, ndb.Model):
    return entity.to_dict()
  else:
    raise TypeError(
        '%s object is not a valid datastore entity' % type(entity))


def addFilterToQuery(query, prop, value):
  """Extends the specified query by adding a filter on the specified property
  with the specified value.

  Args:
    query: query object to extend.
    prop: property of the query model on which to add a filter.
    value: value to compare with the property value. May be a single object
      or a list/tuple.
  """
  if isinstance(value, list) or isinstance(value, tuple):
    query.filter('%s IN' % prop.name, value)
  else:
    query.filter(prop.name, value)
