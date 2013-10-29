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

"""This module contains the organization related models."""

from google.appengine.ext import ndb

from django.utils import translation


# TODO(daniel): complete this class
class Organization(ndb.Model):
  """Model that represents an organization."""

  #: Field storing identifier of the organization.
  org_id = ndb.StringProperty(
      required=True,
      verbose_name=translation.ugettext('Organization ID'))

  #: Field storing name of the organization.
  name = ndb.StringProperty(required=True,
      verbose_name=translation.ugettext('Name'))
  name.group = translation.ugettext("1. Public Info")

  #: Field storing a reference to the program in which 
  #: the organization participates.
  program = ndb.KeyProperty(required=True)
