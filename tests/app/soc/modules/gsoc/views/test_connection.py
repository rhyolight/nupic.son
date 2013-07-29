# Copyright 2012 the Melange authors.
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

"""Tests for the connection view.
"""

from google.appengine.ext import db

from melange.models import connection

from melange.models.connection import Connection
from melange.models.connection_message import ConnectionMessage
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase
from tests.test_utils import MailTestCase

class ConnectionTest(GSoCDjangoTestCase, MailTestCase):
  """ Tests connection page.
  """

  def setUp(self):
    super(ConnectionTest, self).setUp()
    self.init()

  def assertConnectionTemplatesUsed(self, response):
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/connection/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def assertConnectionShowTemplatesUsed(self, response):
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/connection/show_connection.html')
    self.assertTemplateUsed(response, 'modules/gsoc/base.html')

  def testConnectionCreate(self):
    # Test GET call.
    self.profile_helper.createOrgAdmin(self.org)
    url = '/gsoc/connect/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertConnectionTemplatesUsed(response)

    # Create the user that will receive the connection.
    other_data = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_data.createOtherUser('to_be_admin@example.com')
    other_data.notificationSettings(new_invites=True)

    # Test POST to OrgConnectionPage.
    expected = {
        'parent' : other_data.user,
        'organization' : self.org,
        'role' : connection.ORG_ADMIN_ROLE,
        'org_state' : connection.STATE_ACCEPTED,
        }
    data = {
        'users' : other_data.profile.email,
        'role_choice' : connection.ORG_ADMIN_ROLE,
        'message' : 'Test message',
        'organization' : self.org
        }
    response = self.post(url, data)
    new_connection = Connection.all().ancestor(other_data.user).get()
    self.assertPropertiesEqual(expected, new_connection)
    self.assertEmailSent(bcc=other_data.profile.email, n=1)

    # Test POST to UserConnectionPage.
    expected['user_state'] = connection.STATE_ACCEPTED
    expected['org_state'] = connection.STATE_ACCEPTED

    data = {
        'user' : other_data.user,
        'organization' : self.org
        }
    response = self.post(url, data)
    self.assertEmailSent(bcc=other_data.profile.email, n=1)
    new_connection = Connection.all().ancestor(other_data.user).get()
    self.assertIsNotNone(new_connection)

  def testConnectionUserAction(self):
    self.profile_helper.createProfile()

    # Create the connection to be viewed.
    properties = {
        'parent' : self.profile_helper.user,
        'profile' : self.profile_helper.profile,
        'organization' : self.org,
        'org_state' : connection.STATE_ACCEPTED,
        'role' : connection.ORG_ADMIN_ROLE
        }
    new_connection = seeder_logic.seed(Connection, properties)

    # Test GET.
    url = '/gsoc/connection/%s/%s' % (
        self.profile_helper.profile.key().name(),
        long(new_connection.key().id()))
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertConnectionShowTemplatesUsed(response)

    # Test the various User responses to an org admin invite.
    data = {'responses' : 'reject_org_admin'}
    response = self.post(url, data)
    self.assertResponseRedirect(response)
    new_connection = Connection.all().get()
    self.assertEqual(new_connection.user_state, connection.STATE_REJECTED)
    profile = GSoCProfile.all().get()
    self.assertNotIn(self.org.key(), profile.mentor_for)
    self.assertNotIn(self.org.key(), profile.org_admin_for)
    msg = ConnectionMessage.all().ancestor(new_connection).get()
    self.assertNotEqual(None, msg)
    msg.delete()

    data['responses'] = 'accept_org_admin'
    response = self.post(url, data)
    self.assertResponseRedirect(response)
    new_connection = Connection.all().get()
    self.assertEqual(new_connection.user_state, connection.STATE_ACCEPTED)
    profile = GSoCProfile.all().get()
    self.assertIn(self.org.key(), profile.mentor_for)
    self.assertIn(self.org.key(), profile.org_admin_for)
    self.assertEmailSent(to=profile.email)
    msg = ConnectionMessage.all().ancestor(new_connection).get()
    self.assertNotEqual(None, msg)

  def testConnectionOrgAction(self):
    self.profile_helper.createOrgAdmin(self.org)

    other_data = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_data.createProfile()

    # Create the connection.
    properties = {
        'parent' : other_data.user,
        'profile' : other_data.profile,
        'organization' : self.org,
        'user_state' : connection.STATE_ACCEPTED,
        'role' : connection.MENTOR_ROLE
        }
    new_connection = seeder_logic.seed(Connection, properties)

    # Test GET.
    url = '/gsoc/connection/%s/%s' % (
        other_data.profile.key().name(),
        long(new_connection.key().id()))
    response = self.get(url)
    self.assertConnectionShowTemplatesUsed(response)
    self.assertResponseOK(response)

    # Test the various Org responses.
    data = {'responses' : 'reject_mentor'}
    response = self.post(url, data)
    self.assertResponseRedirect(response)
    new_connection = Connection.all().get()
    self.assertEqual(new_connection.org_state, connection.STATE_REJECTED)
    profile = GSoCProfile.all().filter(
        'link_id =', other_data.profile.link_id).get()
    self.assertNotIn(self.org.key(), profile.mentor_for)
    msg = ConnectionMessage.all().ancestor(new_connection).get()
    self.assertNotEqual(None, msg)
    msg.delete()

    data['responses'] = 'accept_mentor'
    response = self.post(url, data)
    self.assertResponseRedirect(response)
    new_connection = Connection.all().get()
    self.assertEqual(new_connection.org_state, connection.STATE_ACCEPTED)
    profile = GSoCProfile.all().filter(
        'link_id =', other_data.profile.link_id).get()
    self.assertIn(self.org.key(), profile.mentor_for)
    self.assertEmailSent(to=profile.email)
    msg = ConnectionMessage.all().ancestor(new_connection).get()
    self.assertNotEqual(None, msg)
