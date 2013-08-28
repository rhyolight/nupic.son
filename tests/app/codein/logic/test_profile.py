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

"""Tests for profile logic."""

import unittest

from codein.logic import profile as profile_logic

from soc.modules.gci.models import organization as org_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import task as task_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class CanResignAsMentorForOrgTest(unittest.TestCase):
  """Unit tests for canResignAsMentorForOrg function."""

  def setUp(self):
    # seed an organization
    self.org = seeder_logic.seed(org_model.GCIOrganization)

    # seed a mentor
    profile_properties = {
        'is_mentor': True,
        'mentor_for': [self.org.key()],
        }
    self.profile = seeder_logic.seed(
        profile_model.GCIProfile, properties=profile_properties)

    task_properties = {
        'org': self.org
        }
    self.task = seeder_logic.seed(
        task_model.GCITask, properties=task_properties)

  def testForNoTasksAssigned(self):
    """Tests for a mentor with no tasks assigned."""
    result = profile_logic.canResignAsMentorForOrg(
        self.profile, self.org.key())
    self.assertTrue(result)

  def testForClosedTask(self):
    """Tests for a mentor with a closed task assigned."""
    self.task.mentors = [self.profile.key()]
    self.task.status = 'Closed'
    self.task.put()

    result = profile_logic.canResignAsMentorForOrg(
        self.profile, self.org.key())
    self.assertTrue(result)

  def testForNonClosedTask(self):
    self.task.mentors = [self.profile.key()]
    statuses = [status for status in task_model.GCITask.status.choices 
        if status != 'Closed']
    for status in statuses:
      self.task.status = status
      self.task.put()

      result = profile_logic.canResignAsMentorForOrg(
          self.profile, self.org.key())
      self.assertFalse(result)
