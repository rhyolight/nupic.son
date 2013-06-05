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

from tests import test_utils
from tests import survey_utils

from soc.modules.gci.models import organization


class OrgProfilePageTest(test_utils.GCIDjangoTestCase):
  """Tests the view for organization profile page.
  """

  def setUp(self):
    self.init()
    self.record = survey_utils.SurveyHelper(self.gci, self.dev_test,
                                            self.org_app)

  def assertOrgProfilePageTemplatesUsed(self, response):
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/org_profile/base.html')

  def testCreateOrgNoLinkid(self):
    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseBadRequest(response)

  def testCreateOrgWrongLinkId(self):
    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url + '?org_id=no_matching_proposal')
    self.assertResponseNotFound(response)

  def testCreateOrgRejectedApp(self):
    self.data.createUser()
    self.record.createOrgAppRecord('rejected', self.data.user, self.data.user,
                                   override={'status': 'rejected'})

    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url + '?org_id=rejected')
    self.assertResponseForbidden(response)

  def testCreateOrgNoProfile(self):
    self.data.createUser()
    self.record.createOrgAppRecord('new_org', self.data.user, self.data.user)

    url = '/gci/profile/organization/' + self.gci.key().name()
    response = self.get(url + '?org_id=new_org')

    self.assertResponseRedirect(response)

  def testCreateOrg(self):
    """Tests that only the assigned org admin for an organization can edit the
    org profile.
    """
    self.timeline.orgSignup()
    self.data.createProfile()
    self.record.createOrgAppRecord('new_org', self.data.user, self.data.user)

    url = '/gci/profile/organization/' + self.gci.key().name()
    create_url = url + '?org_id=new_org'
    response = self.get(create_url)
    self.assertResponseOK(response)
    self.assertOrgProfilePageTemplatesUsed(response)
    
    postdata = {
        'home': self.createDocument().key(), 'program': self.gci,
        'scope': self.gci, 'irc_channel': 'irc://example.com',
        'pub_mailing_list': 'http://example.com', 'backup_winner': None,
    }
    response, _ = self.modelPost(create_url, organization.GCIOrganization,
                                 postdata)
    self.assertResponseRedirect(response, url + '/new_org?validated')
    profile = db.get(self.data.profile.key())
    self.assertEqual(1, len(profile.org_admin_for))
