#!/usr/bin/python2.5
#
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

"""Club (Model) query functions.
"""

__authors__ = [
    '"Sverre Rabbelier" <sverre@rabbelier.nl>',
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from soc.logic.models import group
from soc.logic.models import club_app as club_app_logic
from soc.logic.models import request as request_logic

import soc.models.club
import soc.models.group


class Logic(group.Logic):
  """Logic methods for the Club model.
  """

  def __init__(self, model=soc.models.club.Club,
               base_model=soc.models.group, scope_logic=None):
    """Defines the name, key_name and model for this entity.
    """

    super(Logic, self).__init__(model, base_model=base_model,
                                scope_logic=scope_logic)

  def _onCreate(self, entity):
    """Invites the group admin and backup admin.
    """

    # Find their application
    application = club_app_logic.logic.getFromFields(link_id=entity.link_id)

    if application:
      # only if there is an application send out the invites
      properties = {
          'scope': entity,
          'scope_path': entity.key().name(),
          'role': 'club_admin',
          'role_verbose' : 'Club Admin',
          'group_accepted': True,
          }

      for admin in [application.applicant, application.backup_admin]:
        properties['link_id'] = admin.link_id
        key_fields = request_logic.logic.getKeyFieldsFromDict(properties)
        request_logic.logic.updateOrCreateFromFields(properties, key_fields)

      # set the application to completed  
      fields = {'status' : 'completed'}
      club_app_logic.logic.updateModelProperties(application, fields)


logic = Logic()
