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

"""Module containing survey related models."""

from google.appengine.ext import ndb


class SurveyResponse(ndb.Expando):
  """Model that records response of a single taker to a particular survey.""" 

  #: The survey for which this entity is a record.
  survey = ndb.KeyProperty(kind='Survey')

  #: Date when this record was created.
  created_on = ndb.DateTimeProperty(auto_now_add=True)

  #: Date when this record was last modified, i.e. when at least one of
  #: the answers changed.
  modified_on = ndb.DateTimeProperty(auto_now=True)
