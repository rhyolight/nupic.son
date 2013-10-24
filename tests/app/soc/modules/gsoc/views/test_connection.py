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

"""Tests for connection views."""
from nose.plugins import skip
from google.appengine.ext import db

from melange.models import connection
from soc.modules.gsoc.views import connection as connection_view

from tests import profile_utils
from tests import program_utils
from tests import test_utils

# connection.OrgConnectionPage url pattern - %s should be org key name.
ORG_CONNECTION_PAGE_URL = '/gsoc/connect/%s'
# connection.UserConnectionPage url pattern - first %s is org key, second is
# for the parent User link id.
USER_CONNECTION_PAGE_URL = '/gsoc/connect/%s/%s'
# connection.ShowConnectionForOrgMemberPage url pattern. first is org key,
# second is profile parent User link id, third is connection numberic id.
ORG_SHOW_CONNECTION_PAGE_URL = '/gsoc/connection/%s/%s/%s'
# See comment for ORG_SHOW_CONNECTION_PAGE_URL.
USER_SHOW_CONNECTION_PAGE_URL = '/gsoc/connection/user/%s/%s/%s'
# connection.SubmitConnectionMessagePost url pattern. Order is sponosr,
# program, user link id, connection id.
CONNECTION_MESSAGE_URL = '/gsoc/connection_message/%s/%s/%s'

class OrgConnectionPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgConnectionPage."""

  def setUp(self):
    self.init()
    self.connection_url = None

  def _connectionPageURL(self):
    if not self.connection_url:
      self.connection_url = ORG_CONNECTION_PAGE_URL % self.org.key().name()
    return self.connection_url

  def testNormalUserForbiddenAccess(self):
    """Test that normal users cannot access thus view."""
    self.profile_helper.createUser()
    response = self.get(self._connectionPageURL())
    self.assertResponseForbidden(response)

  def testStudentForbiddenAccess(self):
    """Test that students cannot access this view."""
    self.profile_helper.createStudent()
    response = self.get(self._connectionPageURL())
    self.assertResponseForbidden(response)

  def testOtherOrgAdminForbiddenAccess(self):
    """Test that an org admin for another organization cannot access this view.
    """
    other_org = self.createOrg()
    url = self._connectionPageURL()
    self.profile_helper.deleteProfile()
    self.profile_helper.createOrgAdmin(other_org)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testOrgConnectionTemplatesUsed(self):
    """Test than an org admin for the organization can access this view."""
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self._connectionPageURL())
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/connection/base.html')

  def testInvalidLinkIdFailure(self):
    """Test that if an org admin provides an invalid link id or one that is
    not associated with any user then a ValidationError exception is thrown
    and connection(s) are not created.
    """
    self.profile_helper.createOrgAdmin(self.org)
    post_data = {
        'org_role' : connection.MENTOR_ROLE,
        'users' : 'doesnotexist'
        }
    response = self.post(self._connectionPageURL(), post_data)
    expected = connection_view.DEF_NONEXISTANT_LINK_ID % 'doesnotexist'
    self.assertTrue(expected in response.content)

    post_data['users'] = 'th1s $hould f4il'
    response = self.post(self._connectionPageURL(), post_data)
    expected = connection_view.DEF_INVALID_LINK_ID % 'th1s $hould f4il'
    self.assertTrue(expected in response.content)

  def testInitiateConnection(self):
    """Tests that given valid input, a connection is successfully established.
    """
    self.profile_helper.createOrgAdmin(self.org)
    profile_helper = profile_utils.GSoCProfileHelper(self.gsoc, dev_test=False)
    other_profile = profile_helper.createProfile()

    post_data = {
        'users' : other_profile.link_id,
        'org_role' : connection.MENTOR_ROLE,
        }
    self.post(self._connectionPageURL(), post_data)

    query = connection.Connection.all().ancestor(other_profile)
    connection_entity = query.get()
    self.assertIsNotNone(connection_entity)
    self.assertEquals(connection.MENTOR_ROLE, connection_entity.org_role)
    self.assertEquals(connection.NO_ROLE, connection_entity.user_role)
    self.assertEquals(self.org.key(), connection_entity.organization.key())

  def testInitiateAnonymousConnection(self):
    """Tests that given a valid email address that is not affiliated with any
    existing profile will cause an AnonymousConnection to be created and will
    receive an email with the url.
    """
    self.profile_helper.createOrgAdmin(self.org)
    post_data = {
      'users' : 'test@somethingelese.com',
      'org_role' : connection.MENTOR_ROLE,
      }
    response = self.post(self._connectionPageURL(), post_data)

    query = connection.AnonymousConnection.all().ancestor(self.org)
    connection_entity = query.get()
    self.assertIsNotNone(connection_entity)
    self.assertEquals(connection.MENTOR_ROLE, connection_entity.org_role)
    self.assertEquals(self.org.key(), connection_entity.parent().key())
    self.assertEquals('test@somethingelese.com', connection_entity.email)

  def testGuarnateedOneOrgAdmin(self):
    """Test that the root org admin cannot establish a connection with him or
    her self in order to prevent the org from becoming leader-less.
    """
    self.profile_helper.createOrgAdmin(self.org)
    post_data = {
      'users' : self.profile_helper.profile.link_id,
      'org_role' : connection.MENTOR_ROLE
      }
    response = self.post(self._connectionPageURL(), post_data)

    profile = db.get(self.profile_helper.profile.key())
    self.assertResponseBadRequest(response)
    self.assertTrue(profile.is_org_admin)
    self.assertIn(self.org.key(), profile.org_admin_for)


class OrgConnectionPageEmailsTest(OrgConnectionPageTest):

  def testConnectionNotificationEmailsSent(self):
    """Test that an email is sent to a user when an org admin initiates
    a connection.
    """
    self.profile_helper.createOrgAdmin(self.org)
    profile_helper = profile_utils.GSoCProfileHelper(self.gsoc, dev_test=False)
    other_profile = profile_helper.createProfile()

    post_data = {
        'org_role' : connection.MENTOR_ROLE,
        'users' : other_profile.link_id
        }
    self.post(self._connectionPageURL(), post_data)
    self.assertEmailSent(to=other_profile.email)

  def testAnonymousConnectionNotificationEmailsSent(self):
    """Tests that an email is sent to an unregistered email address when
    an org admin initiates a new connection.
    """
    self.profile_helper.createOrgAdmin(self.org)
    post_data = {
        'org_role' : connection.MENTOR_ROLE,
        'users' : 'test@something.com'
        }
    self.post(self._connectionPageURL(), post_data)
    self.assertEmailSent(bcc='test@something.com')

class UserConnectionPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for UserConnectionPage."""

  def setUp(self):
    self.init()
    self.connection_url = None

  def _connectionPageURL(self):
    if not self.connection_url:
      self.connection_url = USER_CONNECTION_PAGE_URL % (
          self.org.key().name(), self.profile_helper.profile.parent().link_id)
    return self.connection_url

  def testStudentForbiddenAccess(self):
    """Test that a student cannot access this view."""
    self.profile_helper.createStudent()
    response = self.get(self._connectionPageURL())
    self.assertResponseForbidden(response)

  def testTemplatesUsed(self):
    """Test that one with a mentor profile can access this page."""
    self.profile_helper.createProfile()
    response = self.get(self._connectionPageURL())
    self.assertGSoCTemplatesUsed(response)
    self.assertResponseCode(response, 200)
    self.assertTemplateUsed(response, 'modules/gsoc/connection/base.html')

  def testInitiateConnection(self):
    """Test that a connection is generated for a user."""
    self.profile_helper.createProfile()
    self.post(self._connectionPageURL())

    query = connection.Connection.all().ancestor(self.profile_helper.profile)
    connection_entity = query.get()
    self.assertNotEqual(None, connection_entity)
    self.assertEquals(connection.ROLE, connection_entity.user_role)
    self.assertEquals(connection.NO_ROLE, connection_entity.org_role)
    self.assertEquals(self.org.key(), connection_entity.organization.key())

  def testConnectionNotificationEmailsSent(self):
    """Test that an email is sent to all org admins when a user initiates
    a connection.
    """
    self.profile_helper.createProfile()
    helper = profile_utils.GSoCProfileHelper(self.gsoc, dev_test=False)
    helper.createOrgAdmin(self.org)
    helper.profile.notify_new_requests = True
    helper.profile.put()

    self.post(self._connectionPageURL())
    self.assertEmailSent(to=helper.profile.email)


class ShowConnectionForOrgMemberPageTest(test_utils.GSoCDjangoTestCase):

  def setUp(self):
    self.init()
    self.connection_url = None

    self.profile_helper.createOrgAdmin(self.org)

    self.other_data = profile_utils.GSoCProfileHelper(
        self.gsoc, dev_test=False)
    self.other_data.createProfile()
    self.other_data.createConnection(self.org)
    self.other_data.connection.user_role = connection.ROLE
    self.other_data.connection.put()

  def _connectionPageURL(self):
    if not self.connection_url:
      self.connection_url = ORG_SHOW_CONNECTION_PAGE_URL % (
          self.org.key().name(), self.other_data.profile.parent().link_id,
          self.other_data.connection.key().id())
    return self.connection_url

  def testNormalUserForbiddenAccess(self):
    """Test that a normal user cannot access this view."""
    url = self._connectionPageURL()
    self.profile_helper.deleteProfile()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testOtherOrgAdminForbiddenAccess(self):
    """Test that an org admin for another org is forbidden access."""
    url = self._connectionPageURL()
    self.profile_helper.createOrgAdmin(self.createOrg())
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testRequestingUserForbiddenAccess(self):
    """Test that this page is not accessible to the user with whom the
    connection is being established.
    """
    self.profile_helper.deleteProfile()
    self.profile_helper.profile = self.other_data.profile
    response = self.get(self._connectionPageURL())
    self.assertResponseForbidden(response)

  def testTemplatesUsed(self):
    """Test that an org admin for this org can access the view."""
    response = self.get(self._connectionPageURL())
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'modules/gsoc/connection/show_connection.html')

  def testAssignUserMentorRole(self):
    """Test that a user will be assigned a mentor role, either from having no
    role previously or from an org admin role.
    """
    post_data = {'role_response' : connection.MENTOR_ROLE}
    self.post(self._connectionPageURL(), post_data)

    profile = db.get(self.other_data.profile.key())
    connection_entity = db.get(self.other_data.connection.key())
    self.assertEqual(connection.MENTOR_ROLE, connection_entity.org_role)
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.org.key(), profile.mentor_for)

    query = connection.ConnectionMessage.all().ancestor(connection_entity)
    expected = connection_view.USER_ASSIGNED_MENTOR % profile.name()
    self.assertIn(expected, query.get().content)
    self.assertEmailSent(to=self.other_data.profile.email)

  def testAssignUserOrgAdminRole(self):
    """Test that a user will be assigned an org admin role."""
    post_data = {'role_response' : connection.ORG_ADMIN_ROLE}
    self.post(self._connectionPageURL(), post_data)

    profile = db.get(self.other_data.profile.key())
    connection_entity = db.get(self.other_data.connection.key())
    self.assertEqual(connection.ORG_ADMIN_ROLE, connection_entity.org_role)
    self.assertTrue(profile.is_mentor)
    self.assertTrue(profile.is_org_admin)
    self.assertIn(self.org.key(), profile.mentor_for)
    self.assertIn(self.org.key(), profile.org_admin_for)

    query = connection.ConnectionMessage.all().ancestor(connection_entity)
    expected = connection_view.USER_ASSIGNED_ORG_ADMIN % profile.name()
    self.assertIn(expected, query.get().content)

  def testAssignNoRole(self):
    """Test that a user can be lowered from a mentor org admin role."""
    self.other_data.createOrgAdmin(self.org)
    self.other_data.profile.put()

    post_data = {'role_response' : connection.NO_ROLE}
    self.post(self._connectionPageURL(), post_data)

    profile = db.get(self.other_data.profile.key())
    connection_entity = db.get(self.other_data.connection.key())
    self.assertEqual(connection.NO_ROLE, connection_entity.org_role)
    self.assertFalse(profile.is_mentor)
    self.assertFalse(profile.is_org_admin)
    self.assertNotIn(self.org.key(), profile.mentor_for)
    self.assertNotIn(self.org.key(), profile.org_admin_for)

    query = connection.ConnectionMessage.all().ancestor(connection_entity)
    expected = connection_view.USER_ASSIGNED_NO_ROLE % profile.name()
    self.assertIn(expected, query.get().content)


class ShowConnectionForUserPageTest(test_utils.GSoCDjangoTestCase):

  def setUp(self):
    self.init()
    self.connection_url = None

    self.profile_helper.createProfile()
    self.profile_helper.createConnection(self.org)

  def _connectionPageURL(self):
    if not self.connection_url:
      self.connection_url = USER_SHOW_CONNECTION_PAGE_URL % (
          self.org.key().name(), self.profile_helper.user.link_id,
          self.profile_helper.connection.key().id())
    return self.connection_url

  def testNormalUserForbiddenAccess(self):
    """Test that a normal user cannot access this view."""
    url = self._connectionPageURL()
    self.profile_helper.deleteProfile()
    self.assertResponseForbidden(self.get(url))

  def testOrgAdminForbiddenAccess(self):
    """Test that an org admin for this org cannot access the view if they
    are not the user for whom the Connection was created.
    """
    other_helper = profile_utils.GSoCProfileHelper(self.gsoc, False)
    other_helper.createProfile()
    other_helper.createConnection(self.org)

    self.profile_helper.createOrgAdmin(self.org)
    connection_url = USER_SHOW_CONNECTION_PAGE_URL % (
          self.org.key().name(), other_helper.user.link_id,
          other_helper.connection.key().id())

    response = self.get(connection_url)
    self.assertResponseForbidden(response)

  def testIncludedOrgAdminAllowedAccess(self):
    """Test that if a user is an org admin but is the one with whom the org
    is connecting, they can view the page."""
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(self._connectionPageURL())
    self.assertResponseOK(response)

  def testTemplatesUsed(self):
    """Test that someone with a mentor profile can access this view."""
    response = self.get(self._connectionPageURL())
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'modules/gsoc/connection/show_connection.html')

  def testAcceptMentorRole(self):
    """Tests that a user is promoted when they accept a role as a mentor."""
    self.profile_helper.connection.org_role = connection.MENTOR_ROLE
    self.profile_helper.connection.put()

    post_data = {'role_response' : connection.ROLE}
    self.post(self._connectionPageURL(), post_data)

    connection_entity = db.get(self.profile_helper.connection.key())
    profile = db.get(self.profile_helper.profile.key())
    self.assertEqual(connection.ROLE, connection_entity.user_role)
    self.assertTrue(profile.is_mentor)
    self.assertIn(self.org.key(), profile.mentor_for)

    query = connection.ConnectionMessage.all().ancestor(connection_entity)
    expected = connection_view.USER_ASSIGNED_MENTOR % profile.name()
    self.assertIn(expected, query.get().content)

  def testAcceptOrgAdminRole(self):
    """Tests that a user is promoted when they accept a role as an org admin.
    """
    self.profile_helper.connection.org_role = connection.ORG_ADMIN_ROLE
    self.profile_helper.connection.put()

    post_data = {'role_response' : connection.ROLE}
    self.post(self._connectionPageURL(), post_data)

    connection_entity = db.get(self.profile_helper.connection.key())
    profile = db.get(self.profile_helper.profile.key())
    self.assertEqual(connection.ROLE, connection_entity.user_role)
    self.assertTrue(profile.is_mentor)
    self.assertTrue(profile.is_org_admin)
    self.assertIn(self.org.key(), profile.mentor_for)
    self.assertIn(self.org.key(), profile.org_admin_for)

    query = connection.ConnectionMessage.all().ancestor(connection_entity)
    expected = connection_view.USER_ASSIGNED_ORG_ADMIN % profile.name()
    self.assertIn(expected, query.get().content)

  def testRemoveRole(self):
    """Tests that a user is demoted from a mentor or org admin role if they
    select no role.
    """
    self.profile_helper.connection.org_role = connection.MENTOR_ROLE
    self.profile_helper.connection.put()
    self.profile_helper.createMentor(self.org)

    post_data = {'role_response' : connection.NO_ROLE}
    self.post(self._connectionPageURL(), post_data)

    connection_entity = db.get(self.profile_helper.connection.key())
    profile = db.get(self.profile_helper.profile.key())
    self.assertEqual(connection.NO_ROLE, connection_entity.user_role)
    self.assertFalse(profile.is_mentor)
    self.assertFalse(profile.is_org_admin)
    self.assertNotIn(self.org.key(), profile.mentor_for)
    self.assertNotIn(self.org.key(), profile.org_admin_for)

    query = connection.ConnectionMessage.all().ancestor(connection_entity)
    expected = connection_view.USER_ASSIGNED_NO_ROLE % profile.name()
    self.assertIn(expected, query.get().content)

class SubmitConnectionMessagePostTest(test_utils.GSoCDjangoTestCase):

  def setUp(self):
    self.init()

  def testConnectionMessageCreatedForAdmin(self):
    """Test that given valid input, a new ConnectionMessage is generated
    with the org admin's desired message and a notification email is
    sent to the user.
    """
    self.profile_helper.createOrgAdmin(self.org)
    self.profile_helper.profile.notify_new_requests = True
    self.profile_helper.profile.put()

    other_helper = profile_utils.GSoCProfileHelper(self.gsoc, False)
    other_helper.createConnection(self.org)
    other_helper.profile.email = 'test@something.com'
    other_helper.profile.put()

    post_data = { 'content' : 'Test message' }
    url = CONNECTION_MESSAGE_URL % (
        self.gsoc.key().name(),
        other_helper.user.link_id,
        other_helper.connection.key().id()
        )
    response = self.post(url, post_data)
    self.assertResponseCode(response, 302)

    message = connection.ConnectionMessage.all().get()
    self.assertIsNotNone(message)
    self.assertEquals('Test message', message.content)
    self.assertEquals(self.profile_helper.profile.key().id(),
        message.author.key().id())
    self.assertEmailSent(to=other_helper.profile.email)

  def testConnectionMessageCreatedForUser(self):
    """Test that given valid input, a new ConnectionMessage is generated
    with the involved user's desired message and a notification email is
    sent to all org admins.
    """
    other_helper = profile_utils.GSoCProfileHelper(self.gsoc, False)
    other_helper.createOrgAdmin(self.org)
    self.profile_helper.createConnection(self.org)

    post_data = { 'content' : 'Test message' }
    url = CONNECTION_MESSAGE_URL % (
        self.gsoc.key().name(),
        self.profile_helper.user.link_id,
        self.profile_helper.connection.key().id()
        )
    response = self.post(url, post_data)
    self.assertResponseCode(response, 302)

    message = connection.ConnectionMessage.all().get()
    self.assertIsNotNone(message)
    self.assertEquals('Test message', message.content)
    self.assertEquals(self.profile_helper.profile.key().id(),
        message.author.key().id())
    self.assertEmailSent(to=other_helper.profile.email)
