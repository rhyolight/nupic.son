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

"""This module contains the Summer Of Code-specific organization model."""

from google.appengine.ext import ndb

from melange.appengine import db
from melange.models import organization as org_model


class SOCOrganization(org_model.Organization):
  """Model that represents a Summer Of Code-specific organization."""
  # TODO(daniel): add all SoC specific fields, like slots, etc.

  #: URL to a page with a list of project ideas for the organization.
  ideas_page = ndb.StringProperty(
      indexed=False, validator=db.link_validator)

  #: Number of slots that have been allocated to this organization by
  #: program administrators.
  slot_allocation = ndb.IntegerProperty()

  #: Number of slots that have been requested by organization administrators
  #: based on how many proposals the organization is really willing to accept.
  slot_request_min = ndb.IntegerProperty()

  #: Number of slots that would have been desired by the organization,
  #: if the total number of slots was unlimited.
  slot_request_max = ndb.IntegerProperty()
