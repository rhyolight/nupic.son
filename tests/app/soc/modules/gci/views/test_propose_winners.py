# Copyright 2014 the Melange authors.
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

"""Tests for propose winners related views."""

from google.appengine.ext import ndb

from tests import profile_utils
from tests import test_utils


def _getProposeWinnersPageUrl(org_key):
  """Returns URL to Propose Winners page for the specified organization.

  Args:
    org_key: Organization key.

  Returns:
    The URL to Propose Winners page.
  """
  return '/gci/propose_winners/%s' % org_key.name()


class ProposeWinnersPageTest(test_utils.GCIDjangoTestCase):
  """Unit tests for ProposeWinnersPage."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that the page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    self.timeline_helper.allWorkReviewed()
    response = self.get(_getProposeWinnersPageUrl(self.org.key()))
    self.assertResponseOK(response)
