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

"""Unit tests for organization application view."""

from google.appengine.ext import ndb

from melange.models import organization as melange_org_model
from summerofcode.models import organization as soc_org_model

from tests import test_utils


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = u'Test Org Name'

def _getOrgAppTakeUrl(program):
  """Returns URL to Organization Application Take page.

  Args:
    program: Program entity.

  Returns:
    A string containing the URL to Organization Application Take page.
  """
  return '/gsoc/org/application/take/%s' % program.key().name()


class OrgAppTakePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgAppTakePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createProfile()
    response = self.get(_getOrgAppTakeUrl(self.program))
    self.assertResponseOK(response)

  def testOrganizationAndApplicationCreated(self):
    """Tests that org entity as well as application are created properly."""
    self.profile_helper.createProfile()

    postdata = {
        'org_id': TEST_ORG_ID,
        'name': TEST_ORG_NAME,
        }
    self.post(_getOrgAppTakeUrl(self.program), postdata=postdata)

    # check that organization entity has been created
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertIsNotNone(org)

    # check that survey response is created and persisted
    app_response = melange_org_model.ApplicationResponse.query(
        ancestor=org.key).get()
    self.assertIsNotNone(app_response)
