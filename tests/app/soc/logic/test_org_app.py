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

"""Tests for organization application logic."""

import unittest

from soc.logic import org_app as org_app_logic
from soc.models import org_app_survey as org_app_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import survey_utils


class GetOrgAdminsTest(unittest.TestCase):
  """Unit tests for getOrgAdmins function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed a program
    program = seeder_logic.seed(program_model.Program)

    # seed two users
    first_user = profile_utils.seedUser()
    other_user = profile_utils.seedUser()
    
    # seed two profiles
    profile_properties = {
        'parent': first_user,
        'link_id': first_user.key().name(),
        'program': program,
        'scope': program
        }
    self.first_profile = seeder_logic.seed(
        profile_model.Profile, properties=profile_properties)

    profile_properties = {
        'parent': other_user,
        'link_id': other_user.key().name(),
        'program': program,
        'scope': program
        }
    self.other_profile = seeder_logic.seed(
        profile_model.Profile, properties=profile_properties)

    # seed org application
    org_app_properties = {'program': program}
    org_app = seeder_logic.seed(
        org_app_model.OrgAppSurvey, properties=org_app_properties)

    survey_helper = survey_utils.SurveyHelper(program, False, org_app=org_app)
    self.org_app_record = survey_helper.createOrgAppRecord(
        'org_id', first_user, other_user)

  def testTwoAdminsReturned(self):
    """Tests that function returns two profiles of org admins."""
    org_admins = org_app_logic.getOrgAdmins(self.org_app_record)
    
    self.assertSetEqual(
        set([self.first_profile.key(), self.other_profile.key()]),
        set([org_admin.key() for org_admin in org_admins]))
