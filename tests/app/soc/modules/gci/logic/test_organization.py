# Copyright 2011 the Melange authors.
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

"""Tests for GCI logic for organizations."""

from google.appengine.api import memcache
from google.appengine.ext import ndb

from soc.modules.gci.logic import organization as org_logic
from soc.modules.gci.models import task as task_model

from tests import task_utils
from tests import profile_utils
from tests.program_utils import GCIProgramHelper
from tests.test_utils import SoCTestCase


class OrganizationTest(SoCTestCase):
  """Tests the logic for GCIOrganization.
  """

  def setUp(self):
    self.init()
    self.gci_program_helper = GCIProgramHelper()
    self.program = self.gci_program_helper.createProgram()

  def testGetRemainingTaskQuota(self):
    """Tests if the remaining task quota that can be published by a given
    organization is correctly returned.
    """
    gci_program_helper = GCIProgramHelper()
    org = gci_program_helper.createOrg()
    org.task_quota_limit = 5
    org.put()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[ndb.Key.from_old_key(org.key())])
    student = profile_utils.seedNDBStudent(self.program)

    # valid tasks.
    for _ in xrange(3):
      task_utils.seedTask(
          self.program, org, [mentor.key.to_old_key()],
          student=student.key.to_old_key(), status=task_model.CLOSED)
    # invalid tasks.
      task_utils.seedTask(
          self.program, org, [mentor.key.to_old_key()],
          student=student.key.to_old_key(), status='Unpublished')
    expected_quota = org.task_quota_limit - 3
    actual_quota = org_logic.getRemainingTaskQuota(org)

    self.assertEqual(expected_quota, actual_quota)

  def testParticipating(self):
    """Tests if a list of all the organizations participating in a given gci
    program is returned.
    """
    test_org_count = 2
    expected = []
    actual = org_logic.participating(self.program)
    self.assertEqual(expected, actual)
    org1 = self.gci_program_helper.createOrg()
    org2 = self.gci_program_helper.createNewOrg()
    # We need to clear the cache with the key given below as the first call to
    # the function being tested sets an empty cache with the same key.
    key = '%s_participating_orgs_for_%s' % (
        test_org_count, self.program.key().name())
    memcache.delete(key)
    expected = set([org1.key(), org2.key()])
    actual = org_logic.participating(
        self.gci_program_helper.program, org_count=test_org_count)
    actual = set([org.key() for org in actual])
    self.assertEqual(expected, set(actual))
