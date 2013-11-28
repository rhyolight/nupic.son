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

"""This module contains the Code In-specific organization model."""

from google.appengine.ext import ndb

from melange.appengine import db
from melange.models import organization as org_model


DEFAULT_MAX_SCORE = 5

class CIOrganization(org_model.Organization):
  """Model that represents a Summer Of Code-specific organization."""

  #: Number of tasks the organization can have published at the same time.
  task_quota_limit = ndb.IntegerProperty(required=True, default=0)

  #: Email address to which all notifications will be sent.
  email_for_notifications = ndb.StringProperty(validator=db.email_validator)

  #: Student profiles that are nominated for the grand prize
  #: winners by the organization.
  nominated_winners = ndb.KeyProperty(repeated=True)

  #: Backup nomination for the grand prize winner by the organization.
  nominated_backup_winner = ndb.KeyProperty()
