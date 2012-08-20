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

from soc.modules.gsoc.models.connection import GSoCConnection
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
    self.assertTemplateUsed(response, 'v2/modules/gsoc/connection/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def assertConnectionShowTemplatesUsed(self, response):
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 
        'v2/modules/gsoc/connection/show_connection.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def testConnectionCreate(self):
    # Test GET call.
    self.data.createOrgAdmin(self.org)
    url = '/gsoc/connect/' + self.org.key().name()
    response = self.get(url)
    self.assertConnectionTemplatesUsed(response)

    # Create the user that will receive the connection.
    other_data = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_data.createOtherUser('to_be_admin@example.com')
    other_data.createOrgAdmin(self.org)
    other_data.notificationSettings(new_invites=True)
    
    # Test POST to OrgConnectionPage.
    expected = {
        'parent' : other_data.user,
        'profile' : other_data.profile,
        'organization' : self.org,
        'org_mentor' : True,
        'org_org_admin' : True
    }
    data = {
        'users' : other_data.profile.email,
        'role' : '2',
        'message' : 'Test message',
        'organization' : self.org
    }
    response = self.post(url, data)
    self.assertEmailSent(bcc=other_data.profile.email, n=1)
    connection = GSoCConnection.all().ancestor(other_data.user).get()
    self.assertPropertiesEqual(expected, connection)

    # Test POST to UserConnectionPage.
    del expected['org_mentor']
    del expected['org_org_admin']
    expected['user_mentor'] = True
    expected['org_org_admin'] = True

    data = {
        'user' : other_data.user,
        'profile' : other_data.profile,
        'organization' : self.org
    }
    response = self.post(url, data)
    self.assertEmailSent(bcc=other_data.profile.email, n=1)
    connection = GSoCConnection.all().ancestor(other_data.user).get()
    self.assertIsNotNone(connection)
    
  def testConnectionRespond(self):
    # Create the users needed for viewing a connection.
    other_data = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_data.createOtherUser('other_user@example.com')
    other_data.createOrgAdmin(self.org)

    # TODO(dcrodman): Currently trying to make this work; url is in the proper
    # format with the correct args but keeps returning 404s.
    pass

    # Create the connection to be viewed.
    properties = {
        'parent' : other_data.user,
        'profile' : other_data.profile,
        'organization' : self.org,
        'org_mentor' : True,
    }
    connection = seeder_logic.seed(GSoCConnection, properties)

    # Test GET. 
    url = 'gsoc/connection/%s/%s' % (
        other_data.profile.key().name(), unicode(connection.key().id()))
    response = self.get(url)
    self.assertConnectionShowTemplatesUsed(response)
    