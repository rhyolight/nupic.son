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

"""Unit tests for organization homepage views."""

from tests import org_utils
from tests import test_utils


TEST_ORG_ID = 'test_org'

def _getOrgHomeUrl(org):
  """Returns URL to Organization Homepage.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Edit Organization Preferences page.
  """
  return '/gsoc/org2/home/%s' % org.key.id()


class OrgHomePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgHomePage class."""

  def setUp(self):
    """See unittest.UnitTest.setUp for specification."""
    self.init()
    self.org = org_utils.seedSOCOrganization(TEST_ORG_ID, self.program.key())

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getOrgHomeUrl(self.org))
    self.assertResponseOK(response)
