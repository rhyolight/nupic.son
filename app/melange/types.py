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

"""Definitions of Melange types."""

from melange.models import organization as ndb_organization
from melange.models import profile as ndb_profile
from melange.models import user

from soc.models import organization
from soc.models import profile
from soc.models import program
from soc.models import timeline


class Models(object):
  """Class that encapsulates methods that return appropriate model classes.

  Attributes:
    org_model: class that represents organization model.
    profile_model: class that represents profile model.
    program_model: class that represents program model.
    student_data_model: class that represents student data model.
    timeline_model: class that represents timeline model.
    user_model: class that represents user model.
  """

  def __init__(
      self, ndb_org_model=None, ndb_profile_model=None, org_model=None,
      profile_model=None, program_model=None, program_messages_model=None,
      student_data_model=None, timeline_model=None):
    """Initializes new instance of Models class.

    Args:
      org_model: class that represents organization model.
      profile_model: class that represents profile model.
      program_model: class that represents program model.
      program_messages_model: class that represents program messages model.
      student_data_model: class that represents student data model.
      timeline_model: class that represents timeline model.
    """
    # TODO(daniel): remove when not necessary
    self.ndb_org_model = ndb_org_model
    self.ndb_profile_model = ndb_profile_model
    self.org_model = org_model
    self.profile_model = profile_model
    self.program_model = program_model
    self.program_messages_model = program_messages_model
    self.student_data_model = student_data_model
    self.timeline_model = timeline_model
    self.user_model = user.User

MELANGE_MODELS = Models(
    ndb_org_model=ndb_organization.Organization,
    ndb_profile_model=ndb_profile.Profile,
    org_model=organization.Organization,
    profile_model=profile.Profile,
    program_model=program.Program,
    program_messages_model=program.ProgramMessages,
    student_data_model=ndb_profile.StudentData,
    timeline_model=timeline.Timeline)
