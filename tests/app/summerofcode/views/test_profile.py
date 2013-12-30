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

"""Unit tests for user profile related views."""

import datetime

from google.appengine.ext import ndb

from melange.models import profile as profile_model
from melange.models import user as user_model

from summerofcode.views import profile as profile_view

from tests import profile_utils
from tests import test_utils


TEST_BIRTH_DATE = datetime.date(1993, 01, 01)
TEST_BLOG = 'http://www.test.blog.com/'
TEST_EMAIL = 'test@example.com'
TEST_FIRST_NAME = 'Test First'
TEST_GENDER = profile_view._GENDER_FEMALE_ID
TEST_LAST_NAME = 'Test Last'
TEST_PHONE = '1234567890'
TEST_PHOTO_URL = u'http://www.test.photo.url.com/'
TEST_PROGRAM_KNOWLEDGE = u'Test program knowledge'
TEST_PUBLIC_NAME = 'Test Public Name'
TEST_RESIDENTIAL_STREET = 'Test Street'
TEST_RESIDENTIAL_CITY = 'Test City'
TEST_RESIDENTIAL_PROVINCE = 'CA'
TEST_RESIDENTIAL_POSTAL_CODE = '90000'
TEST_RESIDENTIAL_COUNTRY = 'United States'
TEST_TEE_SIZE = profile_view._TEE_SIZE_M_ID
TEST_TEE_STYLE = profile_view._TEE_STYLE_FEMALE_ID
TEST_USER_ID = 'test_user_id'
TEST_WEB_PAGE = u'http://www.web.page.com/'


def _getProfileRegisterAsOrgMemberUrl(program_key):
  """Returns URL to Register As Organization Member page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Register As Organization Member page.
  """
  return '/gsoc/profile/register/org_member/%s' % program_key.name()


def _getEditProfileUrl(program_key):
  """Returns URL to Edit Profile page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Edit Profile page.
  """
  return '/gsoc/profile/edit/%s' % program_key.name()


class ProfileOrgMemberCreatePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileOrgMemberCreatePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getProfileRegisterAsOrgMemberUrl(self.program.key()))
    self.assertResponseOK(response)

  def testOrgMemberProfileCreated(self):
    """Tests that profile entity is created correctly."""
    postdata = {
        'user_id': TEST_USER_ID,
        'public_name': TEST_PUBLIC_NAME,
        'web_page': TEST_WEB_PAGE,
        'blog': TEST_BLOG,
        'photo_url': TEST_PHOTO_URL,
        'first_name': TEST_FIRST_NAME,
        'last_name': TEST_LAST_NAME,
        'email': TEST_EMAIL,
        'phone': TEST_PHONE,
        'residential_street': TEST_RESIDENTIAL_STREET,
        'residential_city': TEST_RESIDENTIAL_CITY,
        'residential_province': TEST_RESIDENTIAL_PROVINCE,
        'residential_country': TEST_RESIDENTIAL_COUNTRY,
        'residential_postal_code': TEST_RESIDENTIAL_POSTAL_CODE,
        'birth_date': TEST_BIRTH_DATE.strftime('%Y-%m-%d'),
        'tee_style': TEST_TEE_STYLE,
        'tee_size': TEST_TEE_SIZE,
        'gender': TEST_GENDER,
        'program_knowledge': TEST_PROGRAM_KNOWLEDGE,
        }
    response = self.post(
        _getProfileRegisterAsOrgMemberUrl(self.program.key()),
        postdata=postdata)
    self.assertResponseRedirect(
        response, url=_getEditProfileUrl(self.program.key()))

    # check that user entity has been created
    user_key = ndb.Key(user_model.User._get_kind(), TEST_USER_ID)
    user = user_key.get()
    self.assertIsNotNone(user)

    # check that profile entity has been created
    profile_key = ndb.Key(
        user_model.User._get_kind(), TEST_USER_ID,
        profile_model.Profile._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_USER_ID))
    profile = profile_key.get()
    self.assertIsNotNone(profile)


class ProfileEditPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileEditPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.profile = profile_utils.seedNDBProfile(self.program.key())
    profile_utils.loginNDB(self.profile.key.parent().get())

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getEditProfileUrl(self.program.key()))
    self.assertResponseOK(response)

  def testProfileUpdated(self):
    """Tests that profile is updated properly."""
    postdata = {
        'public_name': TEST_PUBLIC_NAME,
        'web_page': TEST_WEB_PAGE,
        'blog': TEST_BLOG,
        'photo_url': TEST_PHOTO_URL,
        'first_name': TEST_FIRST_NAME,
        'last_name': TEST_LAST_NAME,
        'email': TEST_EMAIL,
        'phone': TEST_PHONE,
        'residential_street': TEST_RESIDENTIAL_STREET,
        'residential_city': TEST_RESIDENTIAL_CITY,
        'residential_province': TEST_RESIDENTIAL_PROVINCE,
        'residential_country': TEST_RESIDENTIAL_COUNTRY,
        'residential_postal_code': TEST_RESIDENTIAL_POSTAL_CODE,
        'birth_date': TEST_BIRTH_DATE.strftime('%Y-%m-%d'),
        'tee_style': TEST_TEE_STYLE,
        'tee_size': TEST_TEE_SIZE,
        'gender': TEST_GENDER,
        'program_knowledge': TEST_PROGRAM_KNOWLEDGE,
        }
    response = self.post(
        _getEditProfileUrl(self.program.key()), postdata=postdata)
    self.assertResponseRedirect(
        response, url=_getEditProfileUrl(self.program.key()))

    # check profile properties
    profile = self.profile.key.get()
    # TODO(daniel): handle public_name
    #self.assertEqual(profile.public_name, TEST_PUBLIC_NAME)
    self.assertEqual(profile.contact.web_page, TEST_WEB_PAGE)
    self.assertEqual(profile.contact.blog, TEST_BLOG)
    self.assertEqual(profile.contact.email, TEST_EMAIL)
    self.assertEqual(profile.first_name, TEST_FIRST_NAME)
    self.assertEqual(profile.last_name, TEST_LAST_NAME)
    self.assertEqual(profile.contact.phone, TEST_PHONE)
    self.assertEqual(
        profile.residential_address.street, TEST_RESIDENTIAL_STREET)
    self.assertEqual(
        profile.residential_address.city, TEST_RESIDENTIAL_CITY)
    self.assertEqual(
        profile.residential_address.province, TEST_RESIDENTIAL_PROVINCE)
    self.assertEqual(
        profile.residential_address.country, TEST_RESIDENTIAL_COUNTRY)
    self.assertEqual(
        profile.residential_address.postal_code, TEST_RESIDENTIAL_POSTAL_CODE)
    self.assertEqual(profile.birth_date, TEST_BIRTH_DATE)
    #: TODO(daniel): handle program_knowledge
    #self.assertEqual(profile.program_knowledge, TEST_PROGRAM_KNOWLEDGE)
    self.assertEqual(profile.tee_style, profile_model.TeeStyle.FEMALE)
    self.assertEqual(profile.tee_size, profile_model.TeeSize.M)
