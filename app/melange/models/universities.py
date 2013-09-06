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

"""Models that represents predefined universities."""

from google.appengine.ext import ndb


class University(ndb.Model):
  """Model that represent a single university."""

  #: identifier of the university
  uid = ndb.StringProperty()

  #: Full name of the university.
  name = ndb.StringProperty()

  #: Country in which the university is located.
  country = ndb.StringProperty()


class UniversityCluster(ndb.Model):
  """Model that represent predefined universities for the program that is
  defined by its parent key.

  Parent:
    soc.models.program.Program
  """
  universities = ndb.StructuredProperty(University, repeated=True)
