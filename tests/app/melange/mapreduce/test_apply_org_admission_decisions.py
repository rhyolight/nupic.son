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

"""Tests for MapReduce job to apply organization acceptance/rejection."""

from mapreduce import test_support

from melange.models import organization as org_model

from summerofcode import types

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import test_utils

from soc.logic.helper import notifications
from soc.models import program as program_model
from soc.mapreduce.helper import control as mapreduce_control
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class TestApplyOrgAdmissionDecisions(
    test_utils.GSoCDjangoTestCase, test_utils.TaskQueueTestCase):
  """Unit tests for ApplyOrgAdmissionDecisions MapReduce job."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # seed a few organizations; some of them are pre-rejected, some are
    # pre-accepted and some organizations on which no decisions have been taken;
    # the last group should not occur in production but this will check that
    # "undecided" organizations are not processed by the mapper
    seeded_orgs = ([], [], [])
    statuses = (
        org_model.Status.PRE_ACCEPTED,
        org_model.Status.PRE_REJECTED,
        org_model.Status.APPLYING)
    for i in range(4 * len(statuses)):
      org = org_utils.seedOrganization(
          self.program.key(), org_id='org_id_%s' % i,
          status=statuses[i % len(statuses)])
      seeded_orgs[i % len(statuses)].append(org.key)

    self.admins = []
    for i in range(int(1.5 * len(seeded_orgs))):
      admin = profile_utils.seedNDBProfile(
          self.program.key(), admin_for=seeded_orgs[i % len(seeded_orgs)])
      self.admins.append(admin)

    self.program_messages = self.program.getProgramMessages()

    self.pre_accepted_orgs = seeded_orgs[0]
    self.pre_rejected_orgs = seeded_orgs[1]
    self.applying_orgs = seeded_orgs[2]

    # set parameters of the MapReduce job
    self.params = {
        'entity_kind': 'melange.models.organization.Organization',
        'program_key': str(self.program.key())
        }

  def testDecisionsAreApplied(self):
    """Tests that status of organizations is changed after the job."""
    mapreduce_control.start_map(
        'ApplyOrgAdmissionDecisions', params=self.params)
    test_support.execute_until_empty(self.get_task_queue_stub())

    # check that pre-rejected organizations are accepted now
    for org_key in self.pre_accepted_orgs:
      org = org_key.get()
      self.assertEqual(org.status, org_model.Status.ACCEPTED)

    # check that pre-rejected organizations are rejected now
    for org_key in self.pre_rejected_orgs:
      org = org_key.get()
      self.assertEqual(org.status, org_model.Status.REJECTED)

    # check that nothing has changed regarding applying organizations
    for org_key in self.applying_orgs:
      org = org_key.get()
      self.assertEqual(org.status, org_model.Status.APPLYING)

    for org_key in self.pre_accepted_orgs:
      org = org_key.get()
      subject = notifications.DEF_ACCEPTED_ORG % {
          'org': org.name,
          }
      self.assertEmailSent(cc=org.contact.email, subject=subject)

    for org_key in self.pre_rejected_orgs:
      org = org_key.get()
      subject = notifications.DEF_REJECTED_ORG % {
          'org': org.name,
          }
      self.assertEmailSent(cc=org.contact.email, subject=subject)

  def testOrgsForAnotherProgram(self):
    """Tests that status of organizations for another program is untouched."""
    # seed another program
    program = seeder_logic.seed(program_model.Program)

    # seed a few pre-accepted and pre-rejected organizations
    pre_accepted_orgs = []
    for i in range(2):
      org = org_utils.seedOrganization(
          program.key(), org_id='pre_accepted_org_id_%s' % i,
          status=org_model.Status.PRE_ACCEPTED)
      pre_accepted_orgs.append(org.key)

    pre_rejected_orgs = []
    for i in range(3):
      org = org_utils.seedOrganization(
          program.key(), org_id='pre_rejrected_org_id_%s' % i,
          status=org_model.Status.PRE_REJECTED)
      pre_rejected_orgs.append(org.key)

    mapreduce_control.start_map(
        'ApplyOrgAdmissionDecisions', params=self.params)
    test_support.execute_until_empty(self.get_task_queue_stub())

    # check that pre-accepted organizations are still pre-accepted
    for org_key in pre_accepted_orgs:
      org = org_key.get()
      self.assertEqual(org.status, org_model.Status.PRE_ACCEPTED)

    # check that pre-rejected organizations are still pre-rejected
    for org_key in pre_rejected_orgs:
      org = org_key.get()
      self.assertEqual(org.status, org_model.Status.PRE_REJECTED)
