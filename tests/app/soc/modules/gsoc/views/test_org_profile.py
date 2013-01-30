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


"""Tests for GSoC Organization profile related views.
"""


import os

from google.appengine.ext import db

from soc.modules.gsoc.models import organization
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import survey_utils
from tests import test_utils


TEST_ORG_POST_DATA = {
    'name': 'New Test Org',
    'home_page': 'http://newtestorg.example.com',
    'description': 'We are the best of the test orgs',
    'tags': 'Test, org, language',
    'short_name': 'NTO',
    'email': 'nto@newtestorg.example.com',
    'contact_street': 'Test org street',
    'contact_city': 'Test org city',
    'contact_country': 'Belgium',
    'contact_postalcode': 111111,
    'phone': 1111111111,
    'max_score': 5,
    }


class OrgProfilePageTest(test_utils.GSoCDjangoTestCase):
  """Tests the view for organization profile page.
  """

  def setUp(self):
    self.init()
    self.survey_helper = survey_utils.SurveyHelper(self.gsoc, self.dev_test,
                                                   self.org_app)

  def createOrgAppRecord(self):
    """Creates the org application record entity.
    """
    backup_admin = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    backup_admin.createOtherUser('backupadmin@example.com')
    backup_admin_profile = backup_admin.createOrgAdmin(self.org)
    backup_admin.notificationSettings()

    return self.survey_helper.createOrgAppRecord(
        'test_org', self.data.user, backup_admin_profile.parent())

  def assertOrgProfilePageTemplatesUsed(self, response):
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/org_profile/base.html')

  def testOrgProfileCreateOffSeason(self):
    """Tests that it is Ok to create an org profile during off season.
    """
    self.timeline.offSeason()
    self.data.createOrgAdmin(self.org)
    record = self.createOrgAppRecord()

    url = '/gsoc/profile/organization/%s?org_id=%s' % (
        self.gsoc.key().name(), record.org_id)
    response = self.get(url)
    self.assertResponseOK(response)

  def testOrgProfileEditOffSeason(self):
    """Tests that it is Ok to edit an org profile during off season.
    """
    self.timeline.offSeason()
    self.data.createOrgAdmin(self.org)

    url = '/gsoc/profile/organization/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseOK(response)

  def testNonUserLoginRedirect(self):
    """Tests that a user who is not logged in is redirected to its login page.
    """
    current_logged_in_account = os.environ.get('USER_EMAIL', None)
    try:
      os.environ['USER_EMAIL'] = ''
      url = '/gsoc/profile/organization/' + self.gsoc.key().name()
      response = self.get(url)
      self.assertResponseRedirect(response)

      expected_redirect_base = 'https://www.google.com/accounts/Login?'\
          +'continue=http%3A//some.testing.host.tld'
      expected_redirect_address = expected_redirect_base + url
      actual_redirect_address = response.get('location', None)
      self.assertEqual(expected_redirect_address, actual_redirect_address)

      url = '/gsoc/profile/organization/' + self.org.key().name()
      response = self.get(url)
      self.assertResponseRedirect(response)
      expected_redirect_address = expected_redirect_base + url
      actual_redirect_address = response.get('location', None)
      self.assertEqual(expected_redirect_address, actual_redirect_address)
    finally:
      if current_logged_in_account is None:
        del os.environ['USER_EMAIL']
      else:
        os.environ['USER_EMAIL'] = current_logged_in_account

  def testOrgAdminCanCreateOrgProfile(self):
    """Tests if the org admin for the org can create org profile.
    """
    self.data.createProfile()
    record = self.createOrgAppRecord()

    base_url = '/gsoc/profile/organization/'
    suffix = '%s?org_id=%s' % (self.gsoc.key().name(), record.org_id)
    url = base_url + suffix

    response = self.get(url)
    self.assertOrgProfilePageTemplatesUsed(response)
    self.assertResponseOK(response)

    org_key_name = '%s/%s' % (self.gsoc.key().name(), record.org_id)
    org = organization.GSoCOrganization.get_by_key_name(org_key_name)

    self.assertEqual(org, None)

    postdata = TEST_ORG_POST_DATA
    response = self.post(url, postdata)
    self.assertResponseRedirect(
        response, base_url + '%s/%s?validated' % (
            self.gsoc.key().name(), record.org_id))

    org = organization.GSoCOrganization.get_by_key_name(org_key_name)
    self.assertEqual(org.link_id, record.org_id)

    # Make sure that the new org/veteran value is copied from the organization
    # application
    self.assertEqual(org.new_org, record.new_org)

  def testBackupAdminCanCreateOrgProfile(self):
    """Tests if the backup admin for the org can create org profile.
    """
    self.data.createProfile()
    record = self.createOrgAppRecord()

    # Swap main admin and backupadmin
    record.backup_admin, record.main_admin = (
        record.main_admin, record.backup_admin)
    record.put()

    base_url = '/gsoc/profile/organization/'
    suffix = '%s?org_id=%s' % (self.gsoc.key().name(), record.org_id)
    url = base_url + suffix

    response = self.get(url)
    self.assertOrgProfilePageTemplatesUsed(response)
    self.assertResponseOK(response)

    org_key_name = '%s/%s' % (self.gsoc.key().name(), record.org_id)
    org = organization.GSoCOrganization.get_by_key_name(org_key_name)

    self.assertEqual(org, None)

    postdata = TEST_ORG_POST_DATA
    response = self.post(url, postdata)
    self.assertResponseRedirect(
        response, base_url + '%s/%s?validated' % (
            self.gsoc.key().name(), record.org_id))

    org = organization.GSoCOrganization.get_by_key_name(org_key_name)
    self.assertEqual(org.link_id, record.org_id)

    # Make sure that the new org/veteran value is copied from the organization
    # application
    self.assertEqual(org.new_org, record.new_org)

  def testNoProfileUserCantEditOrgProfile(self):
    """Tests that a user without a profile can not edit an org profile.
    """
    self.timeline.kickoff()
    url = '/gsoc/profile/organization/' + self.org.key().name()
    self.data.createUser()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testOrgAdminForOrgCanEditOrgProfile(self):
    """Tests that only the assigned org admin for an organization can edit the
    org profile.
    """
    self.timeline.orgSignup()
    #make the current user to be a mentor for self.org and test for 403.
    self.data.createMentor(self.org)
    url = '/gsoc/profile/organization/' + self.org.key().name()
    self.timeline.orgSignup()
    response = self.get(url)
    self.assertResponseForbidden(response)

    from soc.modules.gsoc.models.organization import GSoCOrganization
    other_organization = seeder_logic.seed(GSoCOrganization)
    self.data.createOrgAdmin(other_organization)
    url = '/gsoc/profile/organization/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    #make the current logged in user to be admin for self.org.
    self.data.createOrgAdmin(self.org)
    self.gsoc.allocations_visible = False
    self.gsoc.put()

    url = '/gsoc/profile/organization/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertOrgProfilePageTemplatesUsed(response)

    context = response.context
    self.assertEqual(context['page_name'], 'Organization profile')
    self.assertTrue('org_home_page_link' in context)
    self.assertTrue('page_name' in context)
    self.assertFalse('slot_transfer_page_link' in context)

    self.gsoc.allocations_visible = True
    self.gsoc.put()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertOrgProfilePageTemplatesUsed(response)
    self.assertTrue('slot_transfer_page_link' in response.context)

    self.timeline.studentsAnnounced()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertOrgProfilePageTemplatesUsed(response)
    self.assertFalse('slot_transfer_page_link' in response.context)

  def test404IsReturnedWhenOrgDoesNotExists(self):
    """Tests that when an org admin tries to access the profile page for an
    org which does not exists a 404 is shown.
    """
    self.data.createOrgAdmin(self.org)
    suffix = '%s/%s/%s' % (self.sponsor.link_id, self.gsoc.link_id, 
                           'non_existing_link_id')
    url = '/gsoc/profile/organization/' + suffix
    import httplib
    response = self.get(url)
    self.assertResponseCode(response, httplib.NOT_FOUND)

  def testAnOrgAdminCanUpdateOrgProfile(self):
    """Tests if an org admin can update the profile for its organization.
    """
    self.timeline.orgSignup()
    self.data.createOrgAdmin(self.org)

    orig_new_org = self.org.new_org

    url = '/gsoc/profile/organization/' + self.org.key().name()
    postdata = seeder_logic.seed_properties(organization.GSoCOrganization)
    updates = {
        'email': 'temp@gmail.com', 'irc_channel': 'irc://i.f.net/gsoc',
        'pub_mailing_list': 'https://l.s.net',
        'tags': 'foo, bar', 'gsoc_org_page_home': 'http://www.xyz.com',
        'contact_postalcode': '247667', 'contact_country': 'India',
        'dev_mailing_list': 'http://d.com', 'home': postdata['home'].key(),
        'max_score': 5, 'new_org': not orig_new_org, # swap orig new org value
        }
    postdata.update(updates)
    self.assertNotEqual(updates['email'], self.org.email)
    response = self.post(url, postdata)
    self.assertResponseRedirect(response)

    expected_redirect_url = 'http://testserver' + url + '?validated'
    actual_redirect_url = response.get('location', None)
    self.assertEqual(expected_redirect_url, actual_redirect_url)

    updated_org = db.get(self.org.key())
    self.assertEqual(updates['email'], updated_org.email)

    # Make sure that the orig new_org value is retained.
    self.assertEqual(updated_org.new_org, orig_new_org)
