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

"""ndb model classes for seeder testing."""

from google.appengine.ext import ndb

from melange.appengine import db as db_util


class NdbDummyModel(ndb.Model):
  """A ndb dummy model class for seeder testing."""
  boolean = ndb.BooleanProperty(required=True)
  name = ndb.StringProperty(required=True)
  link = ndb.StringProperty(required=True, validator=db_util.link_validator)
  email = ndb.StringProperty(required=True, validator=db_util.email_validator)
  numbers = ndb.IntegerProperty(repeated=True)


class NdbKeyProperty(ndb.Model):
  """A ndb model class with KeyProperty for seeder testing."""
  name = ndb.StringProperty(required=True)
  key = ndb.KeyProperty(required=True)
