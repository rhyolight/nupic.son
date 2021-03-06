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

"""Tests for user profile related views."""

import unittest

from google.appengine.ext import ndb

from datetime import date
from datetime import timedelta

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from soc.modules.gci.models import profile as profile_model

from tests import profile_utils
from tests import test_utils


class ProfileViewTest(test_utils.GCIDjangoTestCase):
  """Tests user profile views."""

  def setUp(self):
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

    self.birth_date = str(date.today() - timedelta(365 * 15))

    props = {}
    # we do not want to seed the data in the datastore, we just
    # want to get the properties generated for seeding. The post
    # test will actually do the entity creation, so we reuse the
    # seed_properties method from the seeder to get the most common
    # values for Profile and StudentInfo
    props.update(seeder_logic.seed_properties(profile_model.GCIProfile))
    props.update(seeder_logic.seed_properties(profile_model.GCIStudentInfo))

    props.update({
        'student_info': None,
        'status': 'active',
        'is_org_admin': False,
        'is_mentor': False,
        'org_admin_for': [],
        'mentor_for': [],
        'scope': self.gci,
        'birth_date': self.birth_date,
        'res_country': 'Netherlands',
        'ship_country': 'Netherlands',
    })

    self.default_props = props

    # we have other tests that verify the age_check system
    self.client.cookies['age_check'] = self.birth_date

  def _updateDefaultProps(self, user):
    """Updates default_props variable with more personal data stored in
    the specified user object.
    """
    self.default_props.update({
        'link_id': user.user_id,
        'user': user,
        'parent': user,
        'email': user.account.email()
        })

  def assertProfileTemplatesUsed(self, response):
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/profile/base.html')
    self.assertTemplateUsed(response, 'modules/gci/_form.html')

  @unittest.skip('This profile view is deprecated.')
  def testCreateProfilePage(self):
    self.timeline_helper.studentSignup()
    url = '/gci/profile/student/' + self.gci.key().name()
    self.client.cookies['age_check'] = '1'
    response = self.get(url)
    self.assertProfileTemplatesUsed(response)

  @unittest.skip('This profile view is deprecated.')
  def testCreateMentorProfilePage(self):
    self.timeline_helper.orgsAnnounced()
    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.get(url)
    self.assertProfileTemplatesUsed(response)

  @unittest.skip('This profile view is deprecated.')
  def testRedirectWithStudentProfilePage(self):
    self.timeline_helper.studentSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.get(url)
    redirect_url = '/gci/profile/' + self.gci.key().name()
    self.assertResponseRedirect(response, redirect_url)

  @unittest.skip('This profile view is deprecated.')
  def testRedirectWithMentorProfilePage(self):
    self.timeline_helper.studentSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.get(url)
    response_url = '/gci/profile/' + self.gci.key().name()
    self.assertResponseRedirect(response, response_url)

  @unittest.skip('This profile view is deprecated.')
  def testForbiddenWithStudentProfilePage(self):
    self.timeline_helper.studentSignup()
    self.profile_helper.createStudent()
    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)
    url = '/gci/profile/org_admin/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

  @unittest.skip('This profile view is deprecated.')
  def testRegistrationTimeline(self):
    # no registration should be available just after the program is started
    self.timeline_helper.kickoff()

    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = '/gci/profile/org_admin/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    # only org admins should be able to register in org sign up period
    self.timeline_helper.orgSignup()

    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = '/gci/profile/org_admin/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseOK(response)

    # only org admins and mentors should be able to register after the orgs
    # are announced
    self.timeline_helper.orgsAnnounced()

    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = '/gci/profile/mentor/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseOK(response)

    url = '/gci/profile/org_admin/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseOK(response)

  @unittest.skip('This profile view is deprecated.')
  def testForbiddenWithMentorProfilePage(self):
    self.timeline_helper.studentSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    url = '/gci/profile/student/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseForbidden(response)

  @unittest.skip('This profile view is deprecated.')
  def testEditProfilePage(self):
    self.timeline_helper.studentSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    url = '/gci/profile/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseOK(response)

    self.assertNotContains(
        response,
        '<input id="agreed_to_tos" type="checkbox" name="agreed_to_tos">')

  #TODO(daniel): this test should work, when we disable edition of profiles
  # after the project is over
  #def testEditProfilePageInactive(self):
  #  self.timeline_helper.offSeason()
  #
  #  user = profile_utils.seedNDBUser()
  #  profile_utils.loginNDB(user)
  #  profile_utils.seedNDBProfile(self.program.key(), user=user)
  #
  #  url = '/gci/profile/' + self.gci.key().name()
  #  response = self.get(url)
  #  self.assertResponseForbidden(response)

  @unittest.skip('This profile view is deprecated.')
  def testCreateUser(self):
    self.timeline_helper.studentSignup()

    self.default_props.update({
        'link_id': 'test',
        })

    response = self.post(self.student_url, self.default_props)
    self.assertResponseRedirect(response, self.validated_url)

    self.assertEqual(1, profile_model.GCIProfile.all().count())
    student = profile_model.GCIProfile.all().get()

    self.assertEqual(self.birth_date, str(student.birth_date))
    self.assertSameEntity(self.gci, student.program)

  @unittest.skip('This profile view is deprecated.')
  def testCreateUserNoLinkId(self):
    self.timeline_helper.studentSignup()

    del self.default_props['link_id']

    response = self.post(self.student_url, self.default_props)
    self.assertResponseOK(response)
    self.assertIn('link_id', response.context['error'])

  @unittest.skip('This profile view is deprecated.')
  def testCreateProfile(self):
    self.timeline_helper.studentSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    self._updateDefaultProps(user)
    postdata = self.default_props

    response = self.post(self.student_url, postdata)
    self.assertResponseRedirect(response, self.validated_url)

    # hacky
    profile = profile_model.GCIProfile.all().get()
    profile.delete()

    postdata.update({
        'email': 'somerandominvalid@emailid',
        })

    response = self.post(self.student_url, postdata)

    # yes! this is the protocol for form posts. We get an OK response
    # with the response containing the form's GET request page whenever
    # the form has an error and could not be posted. This is the architecture
    # chosen in order to save the form error state's while rendering the
    # error fields.
    self.assertResponseOK(response)

    error_dict = response.context['error']
    self.assertIn('email', error_dict)
