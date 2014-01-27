# Copyright 2014 the Melange authors.
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

"""This module contains a model that stores education information."""

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop

from protorpc import messages

from melange.utils import countries


class Degree(messages.Enum):
  """Class that enumerates possible types of supported degrees."""
  #: The undergraduate degree.
  UNDERGRADUATE = 1

  #: The master's degree.
  MASTERS = 2

  #: Doctor of Philosophy degree.
  PHD = 3


class Education(ndb.Model):
  """Model that represents education of a student."""
  #: Unique identifier of the school.
  school_id = ndb.StringProperty(required=False)

  #: Country in which the school is located.
  school_country = ndb.StringProperty(
      required=False, choices=countries.COUNTRIES_AND_TERRITORIES)

  #: Expected graduation year.
  expected_graduation = ndb.IntegerProperty()

  #: Major of the student.
  major = ndb.StringProperty()

  #: Degree which is currently being pursued by the student.
  degree = msgprop.EnumProperty(Degree)

  #: Grade of the student. This number may not have a consistent meaning across
  #; jurisdictional boundaries (e.g. eighth grade in the United States may
  #: not correspond to eighth standard in another nation).
  grade = ndb.IntegerProperty()
