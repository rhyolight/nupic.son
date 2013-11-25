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
from melange.models import contact as contact_model
from melange.models import survey as survey_model

from summerofcode.models import organization as soc_org_model
from summerofcode.templates import tabs

from tests import org_utils
from tests import profile_utils
from tests import test_utils


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = u'Test Org Name'
TEST_BLOG = 'http://www.test.blog.com/'
TEST_DESCRIPTION = u'Test Organization Description'
TEST_FACEBOOK = u'http://www.test.facebook.com/'
TEST_FEED_URL = u'http://www.test.feed.com/'
TEST_GOOGLE_PLUS = u'http://www.test.google.plus.com/'
TEST_IDEAS_PAGE = 'http://www.test.ideas.com/'
TEST_IRC_CHANNEL = 'irc://irc.freenode.net/test'
TEST_LOGO_URL = u'http://www.test.logo.url.com/'
TEST_MAILING_LIST = 'mailinglist@example.com'
TEST_TWITTER = u'http://www.test.twitter.com/'
TEST_WEB_PAGE = u'http://www.web.page.com/'


def _getOrgPreferencesEditUrl(org):
  """Returns URL to Edit Organization Preferences page.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Edit Organization Preferences page.
  """
  return '/gsoc/org/preferences/edit/%s' % org.key.id()


def _getOrgProfileCreateUrl(program):
  """Returns URL to Create Organization Profile page.

  Args:
    program: Program entity.

  Returns:
    A string containing the URL to Create Organization Profile page.
  """
  return '/gsoc/org/profile/create/%s' % program.key().name()


def _getOrgProfileEditUrl(org):
  """Returns URL to Edit Organization Profile page.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Edit Organization Profile page.
  """
  return '/gsoc/org/profile/edit/%s' % org.key.id()


def _getOrgApplicationSubmitUrl(org):
  """Returns URL to Submit Organization Application page.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Submit Organization Application page.
  """
  return '/gsoc/org/application/submit/%s' % org.key.id()


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


class OrgProfileCreatePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgProfileCreatePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createProfile()
    response = self.get(_getOrgProfileCreateUrl(self.program))
    self.assertResponseOK(response)

  def testOrgProfileCreated(self):
    """Tests that organization entity is created properly."""
    self.profile_helper.createProfile()

    backup_admin = profile_utils.seedGSoCProfile(self.program)

    postdata = {
        'org_id': TEST_ORG_ID,
        'name': TEST_ORG_NAME,
        'blog': TEST_BLOG,
        'description': TEST_DESCRIPTION,
        'facebook': TEST_FACEBOOK,
        'feed_url': TEST_FEED_URL,
        'google_plus': TEST_GOOGLE_PLUS,
        'logo_url': TEST_LOGO_URL,
        'ideas_page': TEST_IDEAS_PAGE,
        'irc_channel': TEST_IRC_CHANNEL,
        'backup_admin': backup_admin.link_id,
        'mailing_list': TEST_MAILING_LIST,
        'twitter': TEST_TWITTER,
        'web_page': TEST_WEB_PAGE,
        }
    response = self.post(
        _getOrgProfileCreateUrl(self.program), postdata=postdata)

    # check that organization entity has been created
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertIsNotNone(org)
    self.assertEqual(org.contact.blog, TEST_BLOG)
    self.assertEqual(org.contact.facebook, TEST_FACEBOOK)
    self.assertEqual(org.contact.feed_url, TEST_FEED_URL)
    self.assertEqual(org.contact.google_plus, TEST_GOOGLE_PLUS)
    self.assertEqual(org.contact.irc_channel, TEST_IRC_CHANNEL)
    self.assertEqual(org.contact.mailing_list, TEST_MAILING_LIST)
    self.assertEqual(org.contact.twitter, TEST_TWITTER)
    self.assertEqual(org.contact.web_page, TEST_WEB_PAGE)
    self.assertEqual(org.description, TEST_DESCRIPTION)
    self.assertEqual(org.ideas_page, TEST_IDEAS_PAGE)
    self.assertEqual(org.logo_url, TEST_LOGO_URL)
    self.assertEqual(org.name, TEST_ORG_NAME)
    self.assertEqual(org.org_id, TEST_ORG_ID)

    # check that the client is redirected to update page
    self.assertResponseRedirect(response, url=_getOrgApplicationSubmitUrl(org))

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


OTHER_TEST_BLOG = 'http://www.other.test.blog.com/'
OTHER_TEST_DESCRIPTION = u'Other Organization Description'
OTHER_TEST_FACEBOOK = u'http://www.other.test.facebook.com/'
OTHER_TEST_NAME = 'Other Org Name'
OTHER_TEST_FEED_URL = u'http://www.other.test.feed.com/'
OTHER_TEST_GOOGLE_PLUS = 'http://www.other.test.google.plus.com/'
OTHER_TEST_IDEAS_PAGE = 'http://www.other.ideas.page.com/'
OTHER_TEST_IRC_CHANNEL = 'irc://irc.freenode.net/other'
OTHER_TEST_LOGO_URL = 'http://www.other.test.logo.url.com/'
OTHER_TEST_MAILING_LIST = 'othermailinglist@example.com'
OTHER_TEST_TWITTER = u'http://www.other.test.twitter.com/'
OTHER_TEST_WEB_PAGE = u'http://www.other.web.page.com/'

class OrgProfileEditPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgProfileEditPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    contact = contact_model.Contact(mailing_list=TEST_MAILING_LIST)
    self.org = org_utils.seedSOCOrganization(
        TEST_ORG_ID, self.program.key(), name=TEST_ORG_NAME,
        ideas_page=TEST_IDEAS_PAGE, contact=contact)
    self.app_response = survey_model.SurveyResponse(parent=self.org.key)
    self.app_response.put()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createProfile()
    response = self.get(_getOrgProfileEditUrl(self.org))
    self.assertResponseOK(response)

  def testOrgProfileUpdated(self):
    """Tests that organization entity is updated correctly."""
    self.profile_helper.createProfile()

    # check that mutable properties are updated
    postdata = {
        'blog': OTHER_TEST_BLOG,
        'description': OTHER_TEST_DESCRIPTION,
        'facebook': OTHER_TEST_FACEBOOK,
        'feed_url': OTHER_TEST_FEED_URL,
        'google_plus': OTHER_TEST_GOOGLE_PLUS,
        'ideas_page': OTHER_TEST_IDEAS_PAGE,
        'irc_channel': OTHER_TEST_IRC_CHANNEL,
        'logo_url': OTHER_TEST_LOGO_URL,
        'mailing_list': OTHER_TEST_MAILING_LIST,
        'name': OTHER_TEST_NAME,
        'twitter': OTHER_TEST_TWITTER,
        'web_page': OTHER_TEST_WEB_PAGE,
        }
    response = self.post(_getOrgProfileEditUrl(self.org), postdata=postdata)
    self.assertResponseRedirect(response, url=_getOrgProfileEditUrl(self.org))

    # check that organization entity has been updated
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.contact.blog, OTHER_TEST_BLOG)
    self.assertEqual(org.contact.mailing_list, OTHER_TEST_MAILING_LIST)
    self.assertEqual(org.description, OTHER_TEST_DESCRIPTION)
    self.assertEqual(org.contact.facebook, OTHER_TEST_FACEBOOK)
    self.assertEqual(org.contact.google_plus, OTHER_TEST_GOOGLE_PLUS)
    self.assertEqual(org.ideas_page, OTHER_TEST_IDEAS_PAGE)
    self.assertEqual(org.contact.irc_channel, OTHER_TEST_IRC_CHANNEL)
    self.assertEqual(org.logo_url, OTHER_TEST_LOGO_URL)
    self.assertEqual(org.name, OTHER_TEST_NAME)
    self.assertEqual(org.contact.twitter, OTHER_TEST_TWITTER)
    self.assertEqual(org.contact.web_page, OTHER_TEST_WEB_PAGE)

    # check that organization ID is not updated even if it is in POST data
    postdata = {
        'blog': OTHER_TEST_BLOG,
        'description': OTHER_TEST_DESCRIPTION,
        'facebook': OTHER_TEST_FACEBOOK,
        'feed_url': OTHER_TEST_FEED_URL,
        'google_plus': OTHER_TEST_GOOGLE_PLUS,
        'ideas_page': OTHER_TEST_IDEAS_PAGE,
        'logo_url': OTHER_TEST_LOGO_URL,
        'org_id': 'other_org_id',
        'name': TEST_ORG_NAME,
        'twitter': OTHER_TEST_TWITTER,
        'web_page': OTHER_TEST_WEB_PAGE,
        }
    response = self.post(_getOrgProfileEditUrl(self.org), postdata=postdata)
    self.assertResponseRedirect(response, url=_getOrgProfileEditUrl(self.org))

    # check that organization entity has been updated
    org = ndb.Key(
        soc_org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.org_id, TEST_ORG_ID)

  def testOrgsTabs(self):
    """Tests that correct organization related tabs are present in context."""
    response = self.get(_getOrgProfileEditUrl(self.org))

    # check that tabs are present in context
    self.assertIn('tabs', response.context)

    # check that tab to "Edit Profile" page is the selected one
    self.assertEqual(response.context['tabs'].selected_tab_id,
        tabs.ORG_PROFILE_TAB_ID)


class OrgApplicationSubmitPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgApplicationSubmitPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.org = org_utils.seedSOCOrganization(TEST_ORG_ID, self.program.key())

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createProfile()
    response = self.get(_getOrgApplicationSubmitUrl(self.org))
    self.assertResponseOK(response)

  def testApplicationCreated(self):
    """Tests that organization application is created properly."""
    # TODO(daniel): submit actual responses in POST data
    response = self.post(_getOrgApplicationSubmitUrl(self.org))
    self.assertResponseRedirect(response)

    # check that application has been created
    application = survey_model.SurveyResponse.query(ancestor=self.org.key).get()
    self.assertIsNotNone(application)

  def testOrgsTabs(self):
    """Tests that correct organization related tabs are present in context."""
    response = self.get(_getOrgApplicationSubmitUrl(self.org))

    # check that tabs are present in context
    self.assertIn('tabs', response.context)

    # check that tab to "Edit Profile" page is the selected one
    self.assertEqual(response.context['tabs'].selected_tab_id,
        tabs.ORG_APP_RESPONSE_TAB_ID)


class OrgAppShowPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgAppShowPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.org = org_utils.seedSOCOrganization(
        TEST_ORG_ID, self.program.key(), name=TEST_ORG_NAME)
    self.app_response = survey_model.SurveyResponse(parent=self.org.key)
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


TEST_SLOT_REQUEST_MIN = 3
TEST_SLOT_REQUEST_MAX = 10

class OrgPreferencesEditPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgPreferencesEditPage class."""

  def setUp(self):
    """See unittest.TestCase.testUp for specification."""
    self.init()
    self.org = org_utils.seedSOCOrganization(
        TEST_ORG_ID, self.program.key(), name=TEST_ORG_NAME)

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getOrgPreferencesEditUrl(self.org))
    self.assertResponseOK(response)

  def testOrgPreferencesUpdated(self):
    """Tests that organization entity is updated correctly."""
    self.profile_helper.createProfile()

    postdata = {
        'slot_request_min': unicode(TEST_SLOT_REQUEST_MIN),
        'slot_request_max': unicode(TEST_SLOT_REQUEST_MAX)
        }
    response = self.post(_getOrgPreferencesEditUrl(self.org), postdata=postdata)
    self.assertResponseRedirect(
        response, url=_getOrgPreferencesEditUrl(self.org))

    org = self.org.key.get()
    self.assertEqual(org.slot_request_min, TEST_SLOT_REQUEST_MIN)
    self.assertEqual(org.slot_request_max, TEST_SLOT_REQUEST_MAX)
