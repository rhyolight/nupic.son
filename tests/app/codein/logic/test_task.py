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

"""Tests for task logic."""

import unittest

from codein.logic import task as task_logic

from soc.modules.gci.models import organization as org_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import task as task_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


class QueryTasksForMentorTest(unittest.TestCase):
  """Unit tests for queryTasksForMentor function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed an organization
    self.org = seeder_logic.seed(org_model.GCIOrganization)

    # seed a mentor
    profile_properties = {
        'is_mentor': True,
        'mentor_for': [self.org.key()]
        }
    self.profile = seeder_logic.seed(
        profile_model.GCIProfile, profile_properties)

    # seed a few tasks for the seeded mentor
    task_properties = {
        'mentors': [self.profile.key()],
        'status': task_model.OPEN,
        'org': self.org,
        'student': None,
        }
    self.task1 = seeder_logic.seed(
        task_model.GCITask, properties=task_properties)
    self.task2 = seeder_logic.seed(
        task_model.GCITask, properties=task_properties)

  def testAllTasksFetched(self):
    """Tests that all tasks for the mentor are fetched."""
    query = task_logic.queryTasksForMentor(self.profile.key())
    self.assertEqual(query.count(), 2)

  def testTasksWithFilters(self):
    """Tests with applying a filters on properties."""
    # seed another organization
    other_org = seeder_logic.seed(org_model.GCIOrganization)

    # seed another task for that organization and the seeded mentor
    task_properties = {
        'mentors': [self.profile.key()],
        'status': task_model.CLAIMED,
        'org': other_org,
        'student': None,
        }
    other_task = seeder_logic.seed(
        task_model.GCITask, properties=task_properties)

    # check querying tasks for organization filter
    extra_filters = {task_model.GCITask.org: [self.org]}
    query = task_logic.queryTasksForMentor(
        self.profile.key(), extra_filters=extra_filters)
    self.assertSetEqual(
        set(entity.key() for entity in query),
        set([self.task1.key(), self.task2.key()]))

    # check querying tasks for status filter
    extra_filters = {
        task_model.GCITask.status: [task_model.CLAIMED, task_model.OPEN]
        }
    query = task_logic.queryTasksForMentor(
        self.profile.key(), extra_filters=extra_filters)
    self.assertSetEqual(
        set(entity.key() for entity in query),
        set([self.task1.key(), self.task2.key(), other_task.key()]))
