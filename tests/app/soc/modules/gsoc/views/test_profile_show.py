#!/usr/bin/env python2.5
#
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


"""Tests for GSoC read only profile page related views.
"""

__authors__ = [
  '"Praveen Kumar" <praveen97uma@gmail.com>',
  ]

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase

class ProfileShowPageTest(GSoCDjangoTestCase):
  """Tests the view for read only profile show page.
  """

  def setUp(self):
    self.init()

  def assertProfileShowTemplateUsed(self, response):
    """Asserts that correct templates were used to render the view.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/profile_show/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_loggedin_msg.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_readonly_template.html')

  def testUserWithoutAProfileCanNotAccessItsProfile(self):
    """Tests that a user which has no profile can not access its profile.
    """
    self.data.createUser()
    url = '/gsoc/profile/show/' + self.gsoc.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testAUserNotLoggedInIsRedirectedToLoginPage(self):
    """Tests that a user who is not logged in and trying to access its profile
    is redirected to a login page.
    """
    import os
    current_logged_in_account = os.environ.get('USER_EMAIL', None)
    try:
      os.environ['USER_EMAIL'] = ''
      url = '/gsoc/profile/show/' + self.gsoc.key().name()
      response = self.client.get(url)
      expected_redirect_url = 'https://www.google.com/accounts/Login?'+\
          'continue=http%3A//Foo%3A8080'+url
      actual_redirect_url = response.get('location', None)
      self.assertResponseRedirect(response)
      self.assertEqual(expected_redirect_url, actual_redirect_url)
    finally:
      if current_logged_in_account is None:
        del os.environ['USER_EMAIL']
      else:
        os.environ['USER_EMAIL'] = current_logged_in_account

  def testAStudentWithAProfileCanAccessItsProfilePage(self):
    """Tests that a logged in student with a profile can access its profile page.
    """
    self.data.createStudent()
    url = '/gsoc/profile/show/' + self.gsoc.key().name()
    response = self.client.get(url)
    self.assertResponseOK(response)
    self.assertProfileShowTemplateUsed(response)

    context = response.context
    self.assertTrue('page_name' in context)
    self.assertTrue('program_name' in context)
    self.assertTrue('form_top_msg' in context)
    self.assertTrue('profile' in context)
    self.assertTrue('css_prefix' in context)
    self.assertFalse('submit_tax_link' in context)
    self.assertFalse('submit_enrollment_link' in context)
    
    expected_page_name = '%s Profile - %s' % (self.data.program.short_name, 
                                              self.data.profile.name())
    actual_page_name = context['page_name']
    self.assertEqual(expected_page_name, actual_page_name)
    
    expected_program_name = self.data.program.name
    actual_program_name = context['program_name']
    self.assertEqual(expected_program_name, actual_program_name)


class ProfileAdminPageTest(GSoCDjangoTestCase):
  """Tests the view related to readonly profile page.
  """

  def setUp(self):
    self.init()

  def assertProfileShowPageTemplatesUsed(self, response):
    """Asserts that correct templates were used to render the view.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/profile_show/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_loggedin_msg.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_readonly_template.html')

  def testAUserNotLoggedInIsRedirectedToLoginPage(self):
    """Tests that a user who is not logged in and trying to access its profile
    is redirected to a login page.
    """
    profile_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('notloggedinuser@example.com')
    profile_helper.createProfile()
    import os
    current_logged_in_account = os.environ.get('USER_EMAIL', None)
    try:
      os.environ['USER_EMAIL'] = ''
      url = '/gsoc/profile/admin/' + profile_helper.profile.key().name()
      response = self.client.get(url)
      self.assertResponseRedirect(response)
      expected_redirect_url = 'https://www.google.com/accounts/Login?'+\
          'continue=http%3A//Foo%3A8080'+url
      actual_redirect_url = response.get('location', None)
      self.assertEqual(expected_redirect_url, actual_redirect_url)
    finally:
      if current_logged_in_account is None:
        del os.environ['USER_EMAIL']
      else:
        os.environ['USER_EMAIL'] = current_logged_in_account
        
  def testANormalUserCanNotAccessItsAdminProfileUrl(self):
    """Tests that a normal user can not access the its admin profile url.
    """
    self.data.createStudent()
    url = '/gsoc/profile/admin/'+self.data.profile.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createInactiveProfile()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createMentor(self.org)
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createOrgAdmin(self.org)
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createInactiveProfile()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
  def testOnlyAHostCanAccessTheAdminProfilePage(self):
    """Tests that only the host is allowed to access its profile page.
    """
    profile_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('host@example.com')
    profile_helper.createProfile()
    profile_helper.createHost()
    url = '/gsoc/profile/admin/' + profile_helper.profile.key().name()

    self.data.createStudent()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createInactiveStudent()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createInactiveProfile()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createMentor(self.org)
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    
    self.data.createOrgAdmin(self.org)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.data.createProfile()
    self.data.createHost()
    url = '/gsoc/profile/admin/' + self.data.profile.key().name()
    response = self.client.get(url)
    self.assertResponseOK(response)
    self.assertProfileShowPageTemplatesUsed(response)

    context = response.context
    self.assertTrue('page_name' in context)
    self.assertTrue('program_name' in context)
    self.assertTrue('form_top_msg' in context)
    self.assertTrue('profile' in context)
    self.assertTrue('css_prefix' in context)
    self.assertTrue('submit_tax_link' in context)
    self.assertTrue('submit_enrollment_link' in context)
    
    expected_page_name = '%s Profile - %s' % (self.data.program.short_name, 
                                              self.data.profile.name())
    actual_page_name = context['page_name']
    self.assertEqual(expected_page_name, actual_page_name)
    
    expected_program_name = self.data.program.name
    actual_program_name = context['program_name']
    self.assertEqual(expected_program_name, actual_program_name)

