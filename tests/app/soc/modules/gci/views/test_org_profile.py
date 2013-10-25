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


"""Tests for GCI Organization profile related views."""

from google.appengine.ext import db

from melange.models import connection as connection_model

from soc.modules.gci.models import organization as org_model

from tests import profile_utils
from tests import test_utils
from tests import survey_utils


TEST_IRC_CHANNEL = 'irc://example.com'
TEST_MAILING_LIST = 'http://example.com'


class OrgProfilePageTest(test_utils.GCIDjangoTestCase):
  """Tests the view for organization profile page.
  """

  def setUp(self):
    self.init()
    self.record = survey_utils.SurveyHelper(self.gci, self.dev_test,
                                            self.org_app)

  def assertOrgProfilePageTemplatesUsed(self, response):
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/org_profile/base.html')

  def testCreateOrgNoLinkid(self):
    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseBadRequest(response)

  def testCreateOrgWrongLinkId(self):
    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url + '?org_id=no_matching_proposal')
    self.assertResponseNotFound(response)

  def testCreateOrgRejectedApp(self):
    self.profile_helper.createUser()
    self.record.createOrgAppRecord(
        'rejected', self.profile_helper.user, self.profile_helper.user,
        override={'status': 'rejected'})

    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url + '?org_id=rejected')
    self.assertResponseForbidden(response)

  def testCreateOrgNoProfile(self):
    self.profile_helper.createUser()
    self.record.createOrgAppRecord(
        'new_org', self.profile_helper.user, self.profile_helper.user)

    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url + '?org_id=new_org')

    redirect_url = '/gci/profile/org_admin/%s?org_id=new_org' % (
        self.gci.key().name())
    self.assertResponseRedirect(response, url=redirect_url)

  def testCreateOrg(self):
    """Tests that only the assigned org admin for an organization can edit the
    org profile.
    """
    self.timeline_helper.orgSignup()
    self.profile_helper.createProfile()

    # create backup admin for the application
    backup_admin = profile_utils.seedGCIProfile(self.program)

    self.record.createOrgAppRecord(
        'new_org', self.profile_helper.user, backup_admin.parent())

    url = '/gci/profile/organization/' + self.gci.key().name()
    create_url = url + '?org_id=new_org'
    response = self.get(create_url)
    self.assertResponseOK(response)
    self.assertOrgProfilePageTemplatesUsed(response)

    postdata = {
        'home': self.createDocument().key(), 'program': self.program,
        'scope': self.program, 'irc_channel': TEST_IRC_CHANNEL,
        'pub_mailing_list': TEST_MAILING_LIST, 'backup_winner': None,
    }
    response, _ = self.modelPost(create_url, org_model.GCIOrganization,
                                 postdata)
    self.assertResponseRedirect(response, url + '/new_org?validated')

    # check that a organization is created
    key_name = '%s/%s' % (self.program.key().name(), 'new_org')
    organization = org_model.GCIOrganization.get_by_key_name(key_name)
    self.assertIsNotNone(organization)
    self.assertEqual(organization.irc_channel, TEST_IRC_CHANNEL)
    self.assertEqual(organization.pub_mailing_list, TEST_MAILING_LIST)

    # check that the profile is organization administrator
    profile = db.get(self.profile_helper.profile.key())
    self.assertEqual(1, len(profile.org_admin_for))
    self.assertSameEntity(self.gci, profile.program)

    # check that a connection is created for the main admin
    connection = connection_model.Connection.all().ancestor(
        profile.key()).filter('organization', organization).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertEqual(connection.user_role, connection_model.ROLE)

    # check that a connection is created for the backup admin
    connection = connection_model.Connection.all().ancestor(
        backup_admin.key()).filter('organization', organization).get()
    self.assertIsNotNone(connection)
    self.assertEqual(connection.org_role, connection_model.ORG_ADMIN_ROLE)
    self.assertEqual(connection.user_role, connection_model.ROLE)
