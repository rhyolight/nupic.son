# Copyright 2009 the Melange authors.
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

"""This module contains the GCI specific Organization Model.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.modules.gci.models import profile

import soc.models.organization


class GCIOrganization(soc.models.organization.Organization):
  """GCI Organization model extends the basic Organization model.
  """

  #: Property that stores the amount of tasks the organization can publish.
  task_quota_limit = db.IntegerProperty(required=True, default=0)

  #: Optional notification mailing list
  notification_mailing_list = db.EmailProperty(required=False,
    verbose_name=ugettext('Notification mailing list'))
  notification_mailing_list.help_text = ugettext(
    'If entered all GCI Task notifications for this organization will be sent '
    'to this address, in addition to those users who subscribed to the '
    'individual task.')
  notification_mailing_list.group = ugettext('4. Organization Preferences')

  #: List of keys of the student profiles that are nominated to be
  #: the grand prize winners by the organization
  proposed_winners = db.ListProperty(db.Key)

  #: Backup nomination for the grand prize winner by the organization
  backup_winner = db.ReferenceProperty(reference_class=profile.GCIProfile,
      required=False, collection_name='backup_winner_for')
