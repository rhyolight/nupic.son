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

"""Tests for the organization applications process."""

import json
import os

from soc.models import org_app_survey

from tests import profile_utils
from tests import test_utils
from tests import timeline_utils

ORG_APP_SCHEMA = ([
    ["frm-t1359271954246-item", "frm-t1359347613687-item",
     "frm-t1359347873346-item", "frm-t1359347876071-item"],
    {
        "frm-t1359271954246-item": {
            "field_type": "input_text",
            "required": True,
            "label": "Text field sample question?",
            },
        "frm-t1359347613687-item": {
            "field_type": "textarea",
            "required": False,
            "label": "Paragraph field sample question?",
            },
        "frm-t1359347873346-item": {
            "field_type": "checkbox",
            "required": True,
            "other": False,
            "values": [{
                "value": "Ckbx 1",
                "checked": False,
                },
            {
                "value": "Ckbx 2",
                "checked": False,
                },
            {
                "value": "Ckbx 3",
                "checked": False,
                },
            {
                "value": "Ckbx 4",
                "checked": False,
                }],
            "label": "Checkbox field sample question?",
            },
        "frm-t1359347876071-item": {
            "field_type": "radio",
            "required": False,
            "other": True,
            "values": [{
                "value": "Radio1",
                "checked": False,
                },
            {
                "value": "Radio2",
                "checked": False,
                },
            {
                "value": "Radio3",
                "checked": False,
                },
            {
                "value": "Radio4",
                "checked": False
                }],
            "label": "Radio field sample question?",
            }
         }
    ])


class OrgAppTest(test_utils.GSoCDjangoTestCase):
  """Tests for organization applications to be submitted by organizations.
  """

  def setUp(self):
    self.init()

  def assertOrgAppCreateOrEditTemplatesUsed(self, response):
    """Asserts that all the templates from the org app create were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/org_app/edit.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def getOrgAppCreatePostData(self):
    """Returns the post data dictionary for creating or editing org app."""
    time_fmt = '%Y-%m-%d %H:%M:%S'
    return {
        'title': 'GSoC Org App',
        'short_name': 'GSoCOA',
        'content': 'Organization application for GSoC',
        'survey_start': timeline_utils.past().strftime(time_fmt),
        'survey_end': timeline_utils.future().strftime(time_fmt),
        'schema': json.dumps(ORG_APP_SCHEMA),
        }

  def testOrgAppCreateOrEditByProgramAdmin(self):
    """Tests that program admin can create an organization application.
    """
    # Make sure we do not have an org app for this test.
    self.org_app.delete()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    url = '/gsoc/org/application/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertOrgAppCreateOrEditTemplatesUsed(response)

    org_app_key_name = 'gsoc_program/%s/orgapp' % (self.gsoc.key().name(),)
    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)

    self.assertIsNone(org_app)

    response = self.post(url, self.getOrgAppCreatePostData())
    print response.content
    self.assertResponseRedirect(response, url + '?validated')

    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)
    self.assertNotEqual(org_app, None)

  def testOrgAppCreateOrEditByNonUser(self):
    """Tests that a non-user cannot create an organization application.
    """
    # Make sure we do not have an org app for this test.
    self.org_app.delete()

    current_logged_in_account = os.environ.get('USER_EMAIL', None)
    try:
      os.environ['USER_EMAIL'] = ''
      url = '/gsoc/org/application/edit/' + self.gsoc.key().name()
      response = self.get(url)
      self.assertResponseRedirect(response)
      expected_redirect_address = ('https://www.google.com/accounts/Login?'
          + 'continue=http%3A//some.testing.host.tld' + url)
      actual_redirect_address = response.get('location', None)
      self.assertEqual(expected_redirect_address, actual_redirect_address)

      response = self.post(url, self.getOrgAppCreatePostData())
      actual_redirect_address = response.get('location', None)
      self.assertEqual(expected_redirect_address, actual_redirect_address)
    finally:
      if current_logged_in_account is None:
        del os.environ['USER_EMAIL']
      else:
        os.environ['USER_EMAIL'] = current_logged_in_account

  def testOrgAppCreateOrEditByUserNoRole(self):
    """Tests that a user with no role cannot create an organization application.
    """
    # Make sure we do not have an org app for this test.
    self.org_app.delete()

    url = '/gsoc/org/application/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    org_app_key_name = 'gsoc_program/%s/orgapp' % (self.gsoc.key().name(),)
    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)

    self.assertIsNone(org_app)

    response = self.post(url, self.getOrgAppCreatePostData())
    self.assertResponseForbidden(response)

    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)
    self.assertIsNone(org_app)

  def testOrgAppCreateOrEditByOrgAdmin(self):
    """Tests that an org admin cannot create an organization application.
    """
    # Make sure we do not have an org app for this test.
    self.org_app.delete()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[self.org.key])

    url = '/gsoc/org/application/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    org_app_key_name = 'gsoc_program/%s/orgapp' % (self.gsoc.key().name(),)
    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)

    self.assertIsNone(org_app)

    response = self.post(url, self.getOrgAppCreatePostData())
    self.assertResponseForbidden(response)

    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)
    self.assertIsNone(org_app)

  def testOrgAppCreateOrEditByMentor(self):
    """Tests that a mentor cannot create an organization application.
    """
    # Make sure we do not have an org app for this test.
    self.org_app.delete()

    self.profile_helper.createMentor(self.org)
    url = '/gsoc/org/application/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    org_app_key_name = 'gsoc_program/%s/orgapp' % (self.gsoc.key().name(),)
    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)

    self.assertIsNone(org_app)

    response = self.post(url, self.getOrgAppCreatePostData())
    self.assertResponseForbidden(response)

    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)
    self.assertIsNone(org_app)

  def testOrgAppCreateOrEditByStudent(self):
    """Tests that a student cannot create an organization application.
    """
    # Make sure we do not have an org app for this test.
    self.org_app.delete()

    self.profile_helper.createStudent()
    url = '/gsoc/org/application/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    org_app_key_name = 'gsoc_program/%s/orgapp' % (self.gsoc.key().name(),)
    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)

    self.assertIsNone(org_app)

    response = self.post(url, self.getOrgAppCreatePostData())
    self.assertResponseForbidden(response)

    org_app = org_app_survey.OrgAppSurvey.get_by_key_name(org_app_key_name)
    self.assertIsNone(org_app)
