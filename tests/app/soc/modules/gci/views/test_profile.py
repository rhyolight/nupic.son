#!/usr/bin/env python2.5
#
# Copyright 2010 the Melange authors.
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


"""Tests for user profile related views.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests.test_utils import GCIDjangoTestCase


class ProfileViewTest(GCIDjangoTestCase):
  """Tests user profile views.
  """

  def setUp(self):
    from soc.modules.gci.models.profile import GCIProfile
    from soc.modules.gci.models.profile import GCIStudentInfo

    self.init()

    program_suffix = self.gci.key().name()

    self.url = '/gci/profile/%(program_suffix)s' % {
        'program_suffix': program_suffix
        }
    
    self.validated_url = self.url + '?validated'

    self.student_url = '/gci/profile/%(role)s/%(program_suffix)s' % {
        'role': 'student',
        'program_suffix': program_suffix                                                            
        }

    props = {
        'student_info': None,
        'status': 'active',
        'is_org_admin': False,
        'is_mentor': False,
        'org_admin_for': [],
        'mentor_for': [],
        'scope': self.gci
        }
    props.update(seeder_logic.seed_properties(GCIProfile))
    props.update(seeder_logic.seed_properties(GCIStudentInfo))

    self.default_props = props

  def assertProfileTemplatesUsed(self, response):
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/profile/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/_form.html')

  def testCreateProfilePage(self):
    self.timeline.studentSignup()
    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertProfileTemplatesUsed(response)

  def testCreateMentorProfilePage(self):
    self.timeline.studentSignup()
    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertProfileTemplatesUsed(response)

  def testRedirectWithStudentProfilePage(self):
    self.timeline.studentSignup()
    self.data.createStudent()
    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.client.get(url)
    redirect_url = '/gci/profile/' + self.gci.key().name()
    self.assertResponseRedirect(response, redirect_url)

  def testRedirectWithMentorProfilePage(self):
    self.timeline.studentSignup()
    self.data.createMentor(self.org)
    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.client.get(url)
    response_url = '/gci/profile/' + self.gci.key().name()
    self.assertResponseRedirect(response, response_url)

  def testForbiddenWithStudentProfilePage(self):
    self.timeline.studentSignup()
    self.data.createStudent()
    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)
    url = '/gci/profile/org_admin/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testForbiddenWithMentorProfilePage(self):
    self.timeline.studentSignup()
    self.data.createMentor(self.org)
    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testEditProfilePage(self):
    self.timeline.studentSignup()
    self.data.createProfile()
    url = '/gci/profile/' + self.gci.key().name()
    response = self.client.get(url)
    self.assertResponseOK(response)

  #TODO(daniel): this test should work, when we disable edition of profiles
  # after the project is over
  #def testEditProfilePageInactive(self):
  #  self.timeline.offSeason()
  #  self.data.createProfile()
  #  url = '/gci/profile/' + self.gci.key().name()
  #  response = self.client.get(url)
  #  self.assertResponseForbidden(response)

  def testCreateUser(self):
    self.timeline.studentSignup()

    self.default_props.update({
        'link_id': 'test',
        })

    response = self.post(self.student_url, self.default_props)
    self.assertResponseRedirect(response, self.validated_url)

  def testCreateUserNoLinkId(self):
    self.timeline.studentSignup()

    self.default_props.update({
        })

    response = self.post(self.student_url, self.default_props)
    self.assertResponseOK(response)
    self.assertTrue('link_id' in response.context['error'])

  def testCreateProfile(self):
    from soc.modules.gci.models.profile import GCIProfile
    from soc.modules.gci.models.profile import GCIStudentInfo

    self.timeline.studentSignup()
    self.data.createUser()

    suffix = "%(program)s" % {
        'program': self.gci.key().name(),
        }

    role_suffix = "%(role)s/%(suffix)s" % {
        'role': 'student',
        'suffix': suffix,
        }

    url = '/gci/profile/' + suffix
    role_url = '/gci/profile/' + role_suffix


    # we do not want to seed the data in the datastore, we just
    # want to get the properties generated for seeding. The post
    # test will actually do the entity creation, so we reuse the
    # seed_properties method from the seeder to get the most common
    # values for Profile and StudentInfo
    postdata = seeder_logic.seed_properties(GCIProfile)
    props = seeder_logic.seed_properties(GCIStudentInfo)

    postdata.update(props)
    postdata.update({
        'link_id': self.data.user.link_id,
        'student_info': None,
        'user': self.data.user, 'parent': self.data.user,
        'scope': self.gci, 'status': 'active',
        'email': self.data.user.account.email(),
        'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False,
    })

    response = self.post(self.student_url, postdata)

    self.assertResponseRedirect(response, self.validated_url)

    # hacky
    profile = GCIProfile.all().get()
    profile.delete()

    postdata.update({
        'email': 'somerandominvalid@emailid',
        })

    response = self.post(role_url, postdata)

    # yes! this is the protocol for form posts. We get an OK response
    # with the response containing the form's GET request page whenever
    # the form has an error and could not be posted. This is the architecture
    # chosen in order to save the form error state's while rendering the
    # error fields.
    self.assertResponseOK(response)

    error_dict = response.context['error']
    self.assertTrue('email' in error_dict)
