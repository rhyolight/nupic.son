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

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.models import connection as connection_model
from melange.models import organization as melange_org_model
from summerofcode.models import organization as soc_org_model

from tests import org_utils
from tests import profile_utils
from tests import test_utils


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = u'Test Org Name'
TEST_IDEAS_PAGE = 'http://www.test.ideas.com/'
TEST_LOGO_URL = u'http://www.test.logo.url.com/'

def _getOrgAppTakeUrl(program):
  """Returns URL to Organization Application Take page.

  Args:
    program: Program entity.

  Returns:
    A string containing the URL to Organization Application Take page.
  """
  return '/gsoc/org/application/take/%s' % program.key().name()


def _getOrgAppUpdateUrl(org):
  """Returns URL to Organization Application Update page.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Organization Application Update page.
  """
  return '/gsoc/org/application/update/%s' % org.key.id()


def _getOrgAppShowUrl(org):
  """Returns URL to Organization Application Show page.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Organization Application Show page.
  """
  return '/gsoc/org/application/show2/%s' % org.key.id()


def _getPublicOrgListUrl(program):
  """Returns URL to Public Organization List page.

  Args:
    program: Program entity.

  Returns:
    A string containing the URL to Public Organization List page.
  """
  return '/gsoc/org/list/public/%s' % program.key().name()


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

    backup_admin = profile_utils.seedGSoCProfile(self.program)

    postdata = {
        'org_id': TEST_ORG_ID,
        'name': TEST_ORG_NAME,
        'logo_url': TEST_LOGO_URL,
        'ideas_page': TEST_IDEAS_PAGE,
        'backup_admin': backup_admin.link_id
        }
    response = self.post(_getOrgAppTakeUrl(self.program), postdata=postdata)

    # check that organization entity has been created
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertIsNotNone(org)
    self.assertEqual(org.ideas_page, TEST_IDEAS_PAGE)
    self.assertEqual(org.logo_url, TEST_LOGO_URL)

    # check that the client is redirected to update page
    self.assertResponseRedirect(response, url=_getOrgAppUpdateUrl(org))

    # check that survey response is created and persisted
    app_response = melange_org_model.ApplicationResponse.query(
        ancestor=org.key).get()
    self.assertIsNotNone(app_response)

    # check that a connection with the current user has been started
    profile = db.get(self.profile_helper.profile.key())
    self.assertIn(org.key.to_old_key(), profile.org_admin_for)
    connection = connection_model.Connection.all().ancestor(
        profile.key()).filter('organization', org.key.to_old_key()).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertEqual(connection.user_role, connection_model.ROLE)

    # check that a connection with backup admin has been started
    backup_admin = db.get(backup_admin.key())
    self.assertIn(org.key.to_old_key(), backup_admin.org_admin_for)
    connection = connection_model.Connection.all().ancestor(
        backup_admin.key()).filter('organization', org.key.to_old_key()).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertEqual(connection.user_role, connection_model.ROLE)


OTHER_TEST_NAME = 'Other Org Name'
OTHER_TEST_IDAES_PAGE = 'http://www.other.ideas.page.com/'
OTHER_TEST_LOGO_URL = 'http://www.other.test.logo.url.com/'

class OrgAppUpdatePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgAppUpdatePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.org = org_utils.seedSOCOrganization(
        TEST_ORG_ID, self.program.key(), name=TEST_ORG_NAME,
        ideas_page=TEST_IDEAS_PAGE)
    self.app_response = melange_org_model.ApplicationResponse(
        parent=self.org.key)
    self.app_response.put()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createProfile()
    response = self.get(_getOrgAppUpdateUrl(self.org))
    self.assertResponseOK(response)

  def testOrganizationUpdated(self):
    """Tests that org entity is updated correctly."""
    self.profile_helper.createProfile()

    # check that mutable properties are updated
    postdata = {
        'ideas_page': OTHER_TEST_IDAES_PAGE,
        'logo_url': OTHER_TEST_LOGO_URL,
        'name': OTHER_TEST_NAME,
        }
    response = self.post(_getOrgAppUpdateUrl(self.org), postdata=postdata)
    self.assertResponseRedirect(response, url=_getOrgAppUpdateUrl(self.org))

    # check that organization entity has been updated
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.ideas_page, OTHER_TEST_IDAES_PAGE)
    self.assertEqual(org.logo_url, OTHER_TEST_LOGO_URL)
    self.assertEqual(org.name, OTHER_TEST_NAME)

    # check that organization ID is not updated even if it is in POST data
    postdata = {
        'ideas_page': OTHER_TEST_IDAES_PAGE,
        'logo_url': OTHER_TEST_LOGO_URL,
        'org_id': 'other_org_id',
        'name': TEST_ORG_NAME
        }
    response = self.post(_getOrgAppUpdateUrl(self.org), postdata=postdata)
    self.assertResponseRedirect(response, url=_getOrgAppUpdateUrl(self.org))

    # check that organization entity has been updated
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.org_id, TEST_ORG_ID)


class OrgAppShowPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgAppShowPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.org = org_utils.seedSOCOrganization(
        TEST_ORG_ID, self.program.key(), name=TEST_ORG_NAME)
    self.app_response = melange_org_model.ApplicationResponse(
        parent=self.org.key)
    self.app_response.put()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createProfile()
    response = self.get(_getOrgAppShowUrl(self.org))
    self.assertResponseOK(response)

  def testPostMethodNotAllowed(self):
    """Tests that POST method is not permitted."""
    self.profile_helper.createProfile()
    response = self.post(_getOrgAppShowUrl(self.org))
    self.assertResponseMethodNotAllowed(response)


class PublicOrganizationListPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for PublicOrganizationListPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getPublicOrgListUrl(self.program))
    self.assertResponseOK(response)
