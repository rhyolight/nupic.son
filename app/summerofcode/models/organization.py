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


DEFAULT_MAX_SCORE = 5

class SOCOrganization(org_model.Organization):
  """Model that represents a Summer Of Code-specific organization."""
  # TODO(daniel): add all SoC specific fields, like slots, etc.

  #: URL to a page with a list of project ideas for the organization.
  ideas_page = ndb.StringProperty(
      indexed=False, validator=db.link_validator)

  #: Proposal template that would have been desired by the organization.
  contrib_template = ndb.TextProperty()

  #: Number of slots that have been allocated to this organization by
  #: program administrators.
  slot_allocation = ndb.IntegerProperty(default=0)

  #: Number of slots that have been requested by organization administrators
  #: based on how many proposals the organization is really willing to accept.
  slot_request_min = ndb.IntegerProperty(default=0)

  #: Number of slots that would have been desired by the organization,
  #: if the total number of slots was unlimited.
  slot_request_max = ndb.IntegerProperty(default=0)

  #: Maximal number of points that can be given to a proposal by mentors.
  max_score = ndb.IntegerProperty(default=5)

  #: Boolean property telling what mentors should be displayed to organization
  #: administrators when they assign mentors to proposals. If the property is
  #: set to False, only mentors who are willing to take up the project will
  #: be presented. If the property is set to True, all mentors will be listed.
  list_all_mentors = ndb.BooleanProperty(default=False)

  #: Boolean property telling whether submitting scores for proposals
  #: is currently enabled for mentors of this organization or not.
  scoring_enabled = ndb.BooleanProperty(default=True, indexed=False)
