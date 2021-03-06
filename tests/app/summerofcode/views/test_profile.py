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
import mock
import unittest

from google.appengine.ext import ndb

from django import forms as django_forms
from django.utils import html

from melange.models import address as address_model
from melange.models import education as education_model
from melange.models import profile as profile_model
from melange.models import user as user_model

from soc.logic import validate

from summerofcode.templates import tabs
from summerofcode.views import profile as profile_view

from tests import profile_utils
from tests import program_utils
from tests import test_utils
from tests import timeline_utils


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
TEST_RESIDENTIAL_STREET_EXTRA = 'Test Street Extra'
TEST_RESIDENTIAL_CITY = 'Test City'
TEST_RESIDENTIAL_PROVINCE = 'CA'
TEST_RESIDENTIAL_POSTAL_CODE = '90000'
TEST_RESIDENTIAL_COUNTRY = 'United States'
TEST_SHIPPING_NAME = 'Test Shipping Name'
TEST_SHIPPING_STREET = 'Test Shipping Street'
TEST_SHIPPING_STREET_EXTRA = 'Test Shipping Street Extra.'
TEST_SHIPPING_CITY = 'Test Shipping City'
TEST_SHIPPING_PROVINCE = 'DC'
TEST_SHIPPING_POSTAL_CODE = '20000'
TEST_SHIPPING_COUNTRY = 'United States'
TEST_TEE_SIZE = profile_view._TEE_SIZE_M_ID
TEST_TEE_STYLE = profile_view._TEE_STYLE_FEMALE_ID
TEST_USER_ID = 'test_user_id'
TEST_WEB_PAGE = u'http://www.web.page.com/'

TEST_SCHOOL_COUNTRY = 'United States'
TEST_SCHOOL_NAME = 'Melange University'
TEST_MAJOR = 'Computer Science'
TEST_DEGREE = profile_view._DEGREE_MASTERS_ID

OTHER_TEST_SHIPPING_NAME = 'Other Shipping Name'
OTHER_TEST_SHIPPING_STREET = 'Other Shipping Street'
OTHER_TEST_SHIPPING_STREET_EXTRA = 'Other Shipping Street Extra'
OTHER_TEST_SHIPPING_CITY = 'Other Shipping City'
OTHER_TEST_SHIPPING_PROVINCE = 'AL'
OTHER_TEST_SHIPPING_POSTAL_CODE = '35005'
OTHER_TEST_SHIPPING_COUNTRY = 'United States'


def _getProfileRegisterAsOrgMemberUrl(program_key):
  """Returns URL to Register As Organization Member page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Register As Organization Member page.
  """
  return '/gsoc/profile/register/org_member/%s' % program_key.name()


def _getProfileRegisterAsStudentUrl(program_key):
  """Returns URL to Register As Student page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Register As Student page.
  """
  return '/gsoc/profile/register/student/%s' % program_key.name()


def _getEditProfileUrl(program_key):
  """Returns URL to Edit Profile page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Edit Profile page.
  """
  return '/gsoc/profile/edit/%s' % program_key.name()


def _getShowProfileUrl(program_key):
  """Returns URL to Show Profile page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Show Profile page.
  """
  return '/gsoc/profile/show/%s' % program_key.name()


def _getAdminProfileUrl(profile_key):
  """Returns URL to Admin Profile page.

  Args:
    profile_key: Profile key.

  Returns:
    A string containing the URL to Admin Profile page.
  """
  return '/gsoc/profile/admin/%s' % profile_key.id()


class ProfileOrgMemberCreatePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileOrgMemberCreatePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getProfileRegisterAsOrgMemberUrl(self.program.key()))
    self.assertResponseOK(response)

  def testProfileCreatedWhenNoUserExists(self):
    """Tests that profile entity is created correctly."""
    # check that page loads properly
    response = self.get(_getProfileRegisterAsOrgMemberUrl(self.program.key()))
    self.assertResponseOK(response)

    # check that username is present in the form
    form = response.context['forms'][0]
    self.assertIn('user_id', form.fields)

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

  def testProfileCreatedWhenUserExists(self):
    """Tests that a profile is created for a person with user entity."""
    # seed user entity
    user = profile_utils.seedNDBUser(TEST_USER_ID)
    profile_utils.loginNDB(user)

    # check that page loads properly
    response = self.get(_getProfileRegisterAsOrgMemberUrl(self.program.key()))
    self.assertResponseOK(response)

    # check that username is not present in the form
    form = response.context['forms'][0]
    self.assertNotIn('username', form.fields)

    # check POST request
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
        _getProfileRegisterAsOrgMemberUrl(self.program.key()),
        postdata=postdata)
    self.assertResponseRedirect(
        response, url=_getEditProfileUrl(self.program.key()))

    # check that profile entity has been created for the existing user
    profile = profile_model.Profile.query(ancestor=user.key).get()
    self.assertIsNotNone(profile)
    self.assertEqual(
        profile.key.id(), '%s/%s' % (self.program.key().name(), user.key.id()))

  def testSanitization(self):
    """Tests that possible malicious content is sanitized properly."""
    self.timeline_helper.orgsAnnounced()

    xss_payload = '><img src=http://www.google.com/images/srpr/logo4w.png>'

    postdata = {
        'user_id': xss_payload,
        'public_name': xss_payload,
        'web_page': xss_payload,
        'blog': xss_payload,
        'photo_url': xss_payload,
        'first_name': xss_payload,
        'last_name': xss_payload,
        'email': xss_payload,
        'phone': xss_payload,
        'residential_street': xss_payload,
        'residential_city': xss_payload,
        'residential_province': xss_payload,
        'residential_country': xss_payload,
        'residential_postal_code': xss_payload,
        'birth_date': xss_payload,
        'tee_style': xss_payload,
        'tee_size': xss_payload,
        'gender': xss_payload,
        'program_knowledge': xss_payload,
        }

    response = self.post(
        _getProfileRegisterAsOrgMemberUrl(self.program.key()),
        postdata=postdata)
    self.assertNotIn(xss_payload, response.content)
    self.assertIn(html.escape(xss_payload), response.content)


class ProfileRegisterAsStudentPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileRegisterAsStudentPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    # student registration is now
    self.program.timeline.student_signup_start = timeline_utils.past()
    self.program.timeline.student_signup_end = timeline_utils.future()
    self.program.timeline.put()

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getProfileRegisterAsStudentUrl(self.program.key()))
    self.assertResponseOK(response)

  def testStudentProfileCreated(self):
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
        'residential_street_extra': TEST_RESIDENTIAL_STREET_EXTRA,
        'residential_city': TEST_RESIDENTIAL_CITY,
        'residential_province': TEST_RESIDENTIAL_PROVINCE,
        'residential_country': TEST_RESIDENTIAL_COUNTRY,
        'residential_postal_code': TEST_RESIDENTIAL_POSTAL_CODE,
        'birth_date': TEST_BIRTH_DATE.strftime('%Y-%m-%d'),
        'tee_style': TEST_TEE_STYLE,
        'tee_size': TEST_TEE_SIZE,
        'gender': TEST_GENDER,
        'program_knowledge': TEST_PROGRAM_KNOWLEDGE,
        'school_country': TEST_SCHOOL_COUNTRY,
        'school_name': TEST_SCHOOL_NAME,
        'major': TEST_MAJOR,
        'degree': TEST_DEGREE,
        }
    response = self.post(
        _getProfileRegisterAsStudentUrl(self.program.key()),
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

    # check that the created profile is a student
    self.assertIsNotNone(profile.student_data)
    self.assertTrue(profile.is_student)

    # check student data properties
    self.assertEqual(
        profile.student_data.education.school_country, TEST_SCHOOL_COUNTRY)
    self.assertEqual(
        profile.student_data.education.school_id, TEST_SCHOOL_NAME)
    self.assertEqual(profile.student_data.education.major, TEST_MAJOR)
    self.assertEqual(
        profile.student_data.education.degree, education_model.Degree.MASTERS)
    self.assertEqual(profile.student_data.number_of_proposals, 0)
    self.assertEqual(profile.student_data.number_of_projects, 0)
    self.assertEqual(profile.student_data.number_of_passed_evaluations, 0)
    self.assertEqual(profile.student_data.number_of_failed_evaluations, 0)
    self.assertListEqual(profile.student_data.project_for_orgs, [])
    self.assertIsNone(profile.student_data.tax_form)
    self.assertIsNone(profile.student_data.enrollment_form)


VALID_POSTDATA = {
    'public_name': TEST_PUBLIC_NAME,
    'web_page': TEST_WEB_PAGE,
    'blog': TEST_BLOG,
    'photo_url': TEST_PHOTO_URL,
    'first_name': TEST_FIRST_NAME,
    'last_name': TEST_LAST_NAME,
    'email': TEST_EMAIL,
    'phone': TEST_PHONE,
    'residential_street': TEST_RESIDENTIAL_STREET,
    'residential_street_extra': TEST_RESIDENTIAL_STREET_EXTRA,
    'residential_city': TEST_RESIDENTIAL_CITY,
    'residential_province': TEST_RESIDENTIAL_PROVINCE,
    'residential_country': TEST_RESIDENTIAL_COUNTRY,
    'residential_postal_code': TEST_RESIDENTIAL_POSTAL_CODE,
    'shipping_name': TEST_SHIPPING_NAME,
    'shipping_street': TEST_SHIPPING_STREET,
    'shipping_city': TEST_SHIPPING_CITY,
    'shipping_province': TEST_SHIPPING_PROVINCE,
    'shipping_country': TEST_SHIPPING_COUNTRY,
    'shipping_postal_code': TEST_SHIPPING_POSTAL_CODE,
    'is_shipping_address_different': True,
    'birth_date': TEST_BIRTH_DATE.strftime('%Y-%m-%d'),
    'tee_style': TEST_TEE_STYLE,
    'tee_size': TEST_TEE_SIZE,
    'gender': TEST_GENDER,
    'program_knowledge': TEST_PROGRAM_KNOWLEDGE,
    }

class ProfileEditPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileEditPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    shipping_address = address_model.Address(
        name=TEST_SHIPPING_NAME, street=TEST_SHIPPING_STREET,
        street_extra=TEST_SHIPPING_STREET_EXTRA, city=TEST_SHIPPING_CITY,
        province=TEST_SHIPPING_PROVINCE, country=TEST_SHIPPING_COUNTRY,
        postal_code=TEST_SHIPPING_POSTAL_CODE)
    self.profile = profile_utils.seedNDBProfile(
        self.program.key(), shipping_address=shipping_address)
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
        'residential_street_extra': TEST_RESIDENTIAL_STREET_EXTRA,
        'residential_city': TEST_RESIDENTIAL_CITY,
        'residential_province': TEST_RESIDENTIAL_PROVINCE,
        'residential_country': TEST_RESIDENTIAL_COUNTRY,
        'residential_postal_code': TEST_RESIDENTIAL_POSTAL_CODE,
        'is_shipping_address_different': True,
        'shipping_name': OTHER_TEST_SHIPPING_NAME,
        'shipping_street': OTHER_TEST_SHIPPING_STREET,
        'shipping_street_extra': OTHER_TEST_SHIPPING_STREET_EXTRA,
        'shipping_city': OTHER_TEST_SHIPPING_CITY,
        'shipping_province': OTHER_TEST_SHIPPING_PROVINCE,
        'shipping_country': OTHER_TEST_SHIPPING_COUNTRY,
        'shipping_postal_code': OTHER_TEST_SHIPPING_POSTAL_CODE,
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
    self.assertEqual(profile.public_name, TEST_PUBLIC_NAME)
    self.assertEqual(profile.contact.web_page, TEST_WEB_PAGE)
    self.assertEqual(profile.contact.blog, TEST_BLOG)
    self.assertEqual(profile.contact.email, TEST_EMAIL)
    self.assertEqual(profile.first_name, TEST_FIRST_NAME)
    self.assertEqual(profile.last_name, TEST_LAST_NAME)
    self.assertEqual(profile.contact.phone, TEST_PHONE)

    # check residential address properties
    self.assertEqual(
        profile.residential_address.street, TEST_RESIDENTIAL_STREET)
    self.assertEqual(
        profile.residential_address.street_extra, TEST_RESIDENTIAL_STREET_EXTRA)
    self.assertEqual(
        profile.residential_address.city, TEST_RESIDENTIAL_CITY)
    self.assertEqual(
        profile.residential_address.province, TEST_RESIDENTIAL_PROVINCE)
    self.assertEqual(
        profile.residential_address.country, TEST_RESIDENTIAL_COUNTRY)
    self.assertEqual(
        profile.residential_address.postal_code, TEST_RESIDENTIAL_POSTAL_CODE)

    # check shipping address properties
    self.assertEqual(
        profile.shipping_address.name, OTHER_TEST_SHIPPING_NAME)
    self.assertEqual(
        profile.shipping_address.street, OTHER_TEST_SHIPPING_STREET)
    self.assertEqual(
        profile.shipping_address.street_extra, OTHER_TEST_SHIPPING_STREET_EXTRA)
    self.assertEqual(
        profile.shipping_address.city, OTHER_TEST_SHIPPING_CITY)
    self.assertEqual(
        profile.shipping_address.province, OTHER_TEST_SHIPPING_PROVINCE)
    self.assertEqual(
        profile.shipping_address.country, OTHER_TEST_SHIPPING_COUNTRY)
    self.assertEqual(
        profile.shipping_address.postal_code, OTHER_TEST_SHIPPING_POSTAL_CODE)

    self.assertEqual(profile.birth_date, TEST_BIRTH_DATE)
    #: TODO(daniel): handle program_knowledge
    #self.assertEqual(profile.program_knowledge, TEST_PROGRAM_KNOWLEDGE)
    self.assertEqual(profile.tee_style, profile_model.TeeStyle.FEMALE)
    self.assertEqual(profile.tee_size, profile_model.TeeSize.M)

    # check profile is not a student
    self.assertFalse(profile.is_student)
    self.assertIsNone(profile.student_data)

  def testClearShippingAddress(self):
    """Tests that shipping address is cleared properly."""
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
        'is_shipping_address_different': False,
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

    # check that shipping address is cleared
    profile = self.profile.key.get()
    self.assertIsNone(profile.shipping_address)

  def testIsShippingAddressDifferent(self):
    """Tests whether is_shipping_address_different is set correctly."""
    # different shipping address is used
    response = self.get(_getEditProfileUrl(self.program.key()))
    form = response.context['forms'][0]
    self.assertTrue(form.data['is_shipping_address_different'])

    # no shipping address is used
    self.profile.shipping_address = None
    self.profile.put()
    response = self.get(_getEditProfileUrl(self.program.key()))
    form = response.context['forms'][0]
    self.assertFalse(form.data['is_shipping_address_different'])

  def testInvalidData(self):
    """Tests that organization is not updated if data is not valid."""
    # check that data is really valid
    response = self.post(
        _getEditProfileUrl(self.program.key()), postdata=VALID_POSTDATA)
    self.assertResponseRedirect(
        response, url=_getEditProfileUrl(self.program.key()))

    # the birth date is not eligible (the user is too young)
    self.program.student_min_age = (
        (datetime.date.today() - TEST_BIRTH_DATE).days / 365 + 2)
    self.program.student_min_age_as_of = datetime.date.today()
    self.program.put()

    postdata = VALID_POSTDATA.copy()
    response = self.post(
        _getEditProfileUrl(self.program.key()), postdata=postdata)
    self.assertTrue(response.context['error'])

    # residential address fields have invalid characters
    fields = [
        'residential_street', 'residential_street_extra', 'residential_city',
        'residential_province', 'residential_country',
        'residential_postal_code', 'first_name', 'last_name']
    for field in fields:
      postdata = VALID_POSTDATA.copy()
      postdata[field] = '!N^al!D'
      response = self.post(
          _getEditProfileUrl(self.program.key()), postdata=postdata)
      self.assertTrue(response.context['error'])

    # shipping address fields have invalid characters
    fields = [
        'shipping_street', 'shipping_street_extra', 'shipping_city',
        'shipping_province', 'shipping_country', 'shipping_postal_code',
        'shipping_name']
    for field in fields:
      postdata = VALID_POSTDATA.copy()
      postdata[field] = '!N^al!D'
      response = self.post(
          _getEditProfileUrl(self.program.key()), postdata=postdata)
      self.assertTrue(response.context['error'])


class CleanShippingAddressPartTest(unittest.TestCase):
  """Unit tests for _cleanShippingAddressPart function."""

  def testShippingAddressIsNotDifferent(self):
    """Tests that only no value is accepted if address is not different."""
    # Empty or None values are accepted even when a field is required.
    result = profile_view._cleanShippingAddressPart(False, '', True)
    self.assertEqual(result, '')
    result = profile_view._cleanShippingAddressPart(False, None, True)
    self.assertIsNone(result)

    # Empty or None values are accepted when a field is not required.
    result = profile_view._cleanShippingAddressPart(False, '', False)
    self.assertEqual(result, '')
    result = profile_view._cleanShippingAddressPart(False, None, False)
    self.assertIsNone(result)

    # Actual values are not accepted no matter if a field is required or not
    with self.assertRaises(django_forms.ValidationError):
      profile_view._cleanShippingAddressPart(False, 'a value', True)
    with self.assertRaises(django_forms.ValidationError):
      profile_view._cleanShippingAddressPart(False, 'a value', False)

  def testShippingAddressIsDifferent(self):
    """Tests that values are cleaned and returned if address is different."""
    # Empty or None values are accepted for non-required fields
    result = profile_view._cleanShippingAddressPart(True, '', False)
    self.assertEqual(result, '')
    result = profile_view._cleanShippingAddressPart(True, None, False)
    self.assertIsNone(result)

    # Empty or None values are not accepted for required fields
    with self.assertRaises(django_forms.ValidationError):
      profile_view._cleanShippingAddressPart(True, '', True)
    with self.assertRaises(django_forms.ValidationError):
      profile_view._cleanShippingAddressPart(True, None, True)

    # Actual values is returned upon clearing
    result = profile_view._cleanShippingAddressPart(True, 'a value', False)
    self.assertEqual(result, 'a value')

  def testInvalidAddressCharacters(self):
    """Tests that invalid characters are not accepted."""
    # Empty or None values are not accepted for required fields
    with self.assertRaises(django_forms.ValidationError):
      profile_view._cleanShippingAddressPart(True, '!N^al!D', True)


class CleanBirthDateTest(unittest.TestCase):
  """Unit tests for cleanBirthDate function."""

  @mock.patch.object(
      validate, 'isAgeSufficientForProgram', return_value=True)
  def testForEligibleBirthDate(self, mock_func):
    """Tests that an eligible birth date is cleaned properly."""
    program = program_utils.seedGSoCProgram()
    result = profile_view.cleanBirthDate(TEST_BIRTH_DATE, program)
    self.assertEqual(result, TEST_BIRTH_DATE)

  @mock.patch.object(
      validate, 'isAgeSufficientForProgram', return_value=False)
  def testForIneligibleBirthDate(self, mock_func):
    """Tests that an error is raised for an ineligible birth date."""
    program = program_utils.seedGSoCProgram()
    with self.assertRaises(django_forms.ValidationError):
      profile_view.cleanBirthDate(TEST_BIRTH_DATE, program)


class ProfileShowPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileShowPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.get(_getShowProfileUrl(self.program.key()))
    self.assertResponseOK(response)

  def testProfileTabs(self):
    """Tests that correct profile related tabs are present in context."""
    self.timeline_helper.orgsAnnounced()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.get(_getShowProfileUrl(self.program.key()))

    # check that tabs are present in context
    self.assertIn('tabs', response.context)

    # check that tab to "Edit Profile" page is the selected one
    self.assertEqual(response.context['tabs'].selected_tab_id,
        tabs.VIEW_PROFILE_TAB_ID)


class ProfileAdminPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileAdminPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    # seed a profile to show
    profile = profile_utils.seedNDBProfile(self.program.key())

    response = self.get(_getAdminProfileUrl(profile.key))
    self.assertResponseOK(response)
