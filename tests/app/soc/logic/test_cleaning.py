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

import datetime

from django import forms

from soc.logic import cleaning

from tests import profile_utils
from tests import program_utils
from tests.test_utils import GSoCDjangoTestCase


class Form(object):
  """A dummy form class for CleaningTest.
  """
  def __init__(self):
    """Initialization.
    """
    self.cleaned_data = {}
    self._errors = {}


class CleaningTest(GSoCDjangoTestCase):
  """Tests related to cleaning logic.
  """
  def setUp(self):
    """Set up required for the cleaning logic tests.
    """
    self.init()
    # Ensure that current user is created
    self.user = profile_utils.seedUser(
        key_name='current_user', link_id='current_user', name='Current User')
    profile_utils.login(self.user)

    # Create another user
    self.another_user = profile_utils.seedUser(
        key_name='another_user', link_id='another_user', name='Another User')

    # Create a dummy form object
    self.form = Form()

  def testCleanEmptyField(self):
    """Tests that empty field can be cleaned.
    """
    field_name = 'test_empty_field'
    clean_field = cleaning.clean_empty_field(field_name)
    # Test that the same value will be returned, the cleaned_data of form
    # does not change and there is no error message if the value of field
    # is not empty
    field_value = 'v1_@?'
    cleaned_data_before = {field_name: field_value}
    self.form.cleaned_data = cleaned_data_before.copy()
    self.assertEqual(clean_field(self.form), field_value)
    self.assertEqual(self.form.cleaned_data, cleaned_data_before)
    self.assertEqual(self.form._errors, {})
    # Test that None will be returned, the cleaned_data of form does not change
    # and there is no error message if the value of field is empty
    field_value = ''
    cleaned_data_before = {field_name: field_value}
    self.form.cleaned_data = cleaned_data_before.copy()
    self.assertEqual(clean_field(self.form), u'')
    self.assertEqual(self.form.cleaned_data, cleaned_data_before)
    self.assertEqual(self.form._errors, {})

  def testCleanEmail(self):
    """Tests that an email is cleaned.
    """
    field_name = 'test_email'
    clean_field = cleaning.clean_email(field_name)
    #Test that the same value is returned, the cleaned_data of the from does
    #not change and there is no error message if the value of the field has a
    #valid email
    field_value = 'test@example.com'
    cleaned_data_before = {field_name: field_value}
    self.form.cleaned_data = cleaned_data_before.copy()
    self.assertEqual(clean_field(self.form), field_value)
    self.assertEqual(self.form.cleaned_data, cleaned_data_before)
    self.assertEqual(self.form._errors, {})
    #Test that forms.ValidationError is raised if email is not valid.
    field_value = '#$test&*('
    cleaned_data_before = {field_name: field_value}
    self.form.cleaned_data = cleaned_data_before.copy()
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    self.assertEqual(self.form.cleaned_data, cleaned_data_before)
    self.assertEqual(self.form._errors, {})

  def testCleanLinkId(self):
    """Tests that link_id field can be cleaned.
    """
    field_name = 'test_link_id'
    clean_field = cleaning.clean_link_id(field_name)
    # Test that the value will be returned, the cleaned_data of form does not
    # change and there is no error message if the value of field has a valid
    # link_id format
    field_value = 'valid_link_id'
    cleaned_data_before = {field_name: field_value}
    self.form.cleaned_data = cleaned_data_before.copy()
    self.assertEqual(clean_field(self.form), field_value)
    self.assertEqual(self.form.cleaned_data, cleaned_data_before)
    self.assertEqual(self.form._errors, {})
    # Test that forms.ValidationError will be raised, the cleaned_data of form
    # does not change and there is no error message if the value of field has
    # not a valid link_id format
    field_value = 'v1_@?'
    cleaned_data_before = {field_name: field_value}
    self.form.cleaned_data = cleaned_data_before.copy()
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    self.assertEqual(self.form.cleaned_data, cleaned_data_before)
    self.assertEqual(self.form._errors, {})

  def testCleanExistingUser(self):
    """Tests that the user field can be cleaned for existing users.
    """
    field_name = 'test_existing_user'
    clean_field = cleaning.clean_existing_user(field_name)
    # Test that the user will be returned if the value of field
    # is an existent user's link_id
    field_value = self.user.link_id
    self.form.cleaned_data = {field_name: field_value}
    cleaned_data_after = clean_field(self.form)
    self.assertEqual(cleaned_data_after.link_id, self.user.link_id)
    # Test that forms.ValidationError will be raised if the value of field
    # is not an existent user's link_id
    field_value = 'non_existent_user'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanUserIsCurrent(self):
    """Tests that the user field can be cleaned for current users.
    """
    field_name = 'test_user_is_current'
    clean_field = cleaning.clean_user_is_current(field_name)
    # Test that the user will be returned if the value of field is
    # an existent user's link_id
    field_value = self.user.link_id
    self.form.cleaned_data = {field_name: field_value}
    cleaned_data_after = clean_field(self.form)
    self.assertEqual(cleaned_data_after.link_id, self.user.link_id)
    # Test that forms.ValidationError will be raised if the value of field
    # is a user's link_id other than the current user's
    field_value = self.another_user.link_id
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    # Test that forms.ValidationError will be raised if the value of field
    # is not an existent user's link_id
    field_value = 'non_existent_user'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanUserNotExist(self):
    """Tests that the user field can be cleaned for non-existent users.
    """
    field_name = 'test_user_not_exist'
    clean_field = cleaning.clean_user_not_exist(field_name)
    # Test that the value will be returned if the value of field
    # is not an existent user's link_id
    field_value = 'non_existent_user'
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)
    # Test that forms.ValidationError will be raised if the value of field
    # is an existent user's link_id
    field_value = self.user.link_id
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanUsersNotSame(self):
    """Tests that the user field can be cleaned for non current users.
    """
    field_name = 'test_not_current_user'
    clean_field = cleaning.clean_users_not_same(field_name)
    # Test that forms.ValidationError will be raised if the value of field
    # is the current user's link_id
    field_value = self.user.link_id
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    # Test that the user will be returned if the value of field is
    # a user's link_id other than the current user
    field_value = self.another_user.link_id
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form).link_id, self.another_user.link_id)
    # Test that forms.ValidationError will be raised if the value of field
    # is not an existent user's link_id
    field_value = 'non_existent_user'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanUserAccount(self):
    """Test that user account can be cleaned.
    """
    field_name = 'test_user_account'
    clean_field = cleaning.clean_user_account(field_name)
    # Test that a new account will be returned if the value of field is
    # a valid new email address
    field_value = 'user_name@email.com'
    self.form.cleaned_data = {field_name: field_value}
    cleaned_data_after = clean_field(self.form)
    self.assertEqual(cleaned_data_after.email(), field_value)
    # Test that the existing account will be returned if the value of field is
    # an existent user's email address
    field_value = self.user.account.email()
    self.form.cleaned_data = {field_name: field_value}
    cleaned_data_after = clean_field(self.form)
    self.assertEqual(cleaned_data_after.email(), field_value)
    self.assertEqual(cleaned_data_after, self.user.account)
    # Test that a new account will be returned even if the value of field is
    # an invalid email address
    field_value = 'invalid_*mail'
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form).email(), field_value)

  def testCleanValidShippingChars(self):
    """Tests that the shipping fields can be cleaned.
    """
    field_name = 'test_ascii'
    clean_field = cleaning.clean_valid_shipping_chars(field_name)
    # Test that the value will be returned if the value of field is valid
    field_value = 'ab12'
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)
    # Test that forms.ValidationError will be raised if the value of field
    # is not valid ascii
    field_value = u'\ua000'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanContentLength(self):
    """Tests that content length can be cleaned.
    """
    field_name = 'test_content_length'
    clean_field = cleaning.clean_content_length(field_name, 3, 5)
    # Test that the value will be returned if the length of the value of field
    # is within min_length and max_length
    field_value = 'a1&'
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)
    # Test that forms.ValidationError will be raised if the length of the value
    # of field is less than min_length
    field_value = 'ab'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    # Test that forms.ValidationError will be raised if the length of the value
    # of field is more than max_length
    field_value = 'ab12&*'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanPhoneNumber(self):
    """Tests that phone number can be cleaned.
    """
    field_name = 'test_phone_number'
    clean_field = cleaning.clean_phone_number(field_name)
    # Test that the phone number will be returned if it contains digits only
    field_value = '0010208636479'
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)
    # Test that forms.ValidationError will be raised if
    # the phone number contains non digits (except '+')
    field_value = '001-020-8636479'
    self.form.cleaned_data[field_name] = field_value
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    # Test that the '+' will be replaced with 00 and then the modified number
    # will be returned if the phone number starts with a '+'
    field_value = '+10208636479'
    self.form.cleaned_data[field_name] = field_value
    expected = '00' + field_value[1:]
    self.assertEqual(clean_field(self.form), expected)
    # Test that forms.ValidationError will be raised if
    # a '+' is in the middle of the phone number
    field_value = '1+0208636479'
    self.form.cleaned_data[field_name] = field_value
    self.assertRaises(forms.ValidationError, clean_field, self.form)
    # Test that forms.ValidationError will be raised if
    # a '+' is at the end of the phone number
    field_value = '10208636479+'
    self.form.cleaned_data[field_name] = field_value
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanFeedUrl(self):
    """Tests that feed url can be cleaned."""
    field_name = 'test_feed_url'
    clean_field = cleaning.clean_feed_url(field_name)
    # Test that the value of the feed url field will be returned if
    # the value of the feed url field is an existent feed url
    field_value = 'http://rss.cnn.com/rss/edition.rss'
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)
    # Test that None will be returned if the value of the feed url field is
    # an empty string
    field_value = ''
    self.form.cleaned_data = {field_name: field_value}
    self.assertIsNone(clean_field(self.form))
    # Test that forms.ValidationError error will be raised if the value of
    # the feed url field is not an existent feed url
    field_value = 'http://example.com/invalidfeed/'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanHtmlContent(self):
    """Tests that html content can be cleaned.
    """
    field_name = 'test_html'
    clean_field = cleaning.clean_html_content(field_name)
    # Test that normal html can be cleaned
    expected = html = '<div>f9-+@4</div>'
    self.form.cleaned_data = {field_name: html}
    self.assertEqual(clean_field(self.form), expected)
    # Test that normal html can be cleaned
    html = '<html>f9-+@4</html>'
    self.form.cleaned_data = {field_name: html}
    expected = html.replace('<', '&lt;').replace('>', '&gt;')
    actual = clean_field(self.form)
    self.assertEqual(actual, expected)
    expected = html = u'\ua000'
    self.form.cleaned_data = {field_name: html}
    self.assertEqual(clean_field(self.form), expected)
    # Test that input with scripts will be encoded as well
    html = '<script></script>'
    self.form.cleaned_data = {field_name: html}
    actual = clean_field(self.form)
    expected = html.replace('<', '&lt;').replace('>', '&gt;')
    self.assertEqual(actual, expected)
    # Test that input can contain scripts when the current user is a developer
    self.user.is_developer = True
    self.user.put()
    expected = html = '<script></script>'
    self.form.cleaned_data = {field_name: html}
    self.assertEqual(clean_field(self.form), expected)

  def testCleanUrl(self):
    """Tests that url can be cleaned.
    """
    field_name = 'test_url'
    clean_field = cleaning.clean_url(field_name)
    # Test that the value of the url field will be returned
    # if it is a valid url
    field_value = 'http://exampleabc.com/'
    self.form.cleaned_data = {field_name: field_value}
    self.form.fields = {field_name: forms.URLField()}
    self.assertEqual(clean_field(self.form), field_value)
    # Test that None will be returned if the value of the url field
    # is an empty string
    field_value = ''
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), u'')
    # Test that forms.ValidationError error will be raised
    # if the value of the url field is not a valid url
    field_value = 'exampleabc'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testStr2Set(self):
    """Tests if symbol separated strings are cleaned.
    """
    string_field = 'test_string_field'
    clean_field = cleaning.str2set(string_field, separator=',')

    string_field_value = "a,b,c"
    cleaned_data_before = {string_field: string_field_value}
    self.form.cleaned_data = cleaned_data_before
    expected = string_field_value.split(',')
    self.assertEqual(clean_field(self.form), expected)

    string_field_value = "a"
    cleaned_data_before = {string_field: string_field_value}
    self.form.cleaned_data = cleaned_data_before
    expected = string_field_value.split()
    self.assertEqual(clean_field(self.form), expected)

    string_field_value = "a b c"
    clean_field = cleaning.str2set(string_field, separator=' ')
    cleaned_data_before = {string_field: string_field_value}
    self.form.cleaned_data = cleaned_data_before
    expected = string_field_value.split()
    self.assertEqual(clean_field(self.form), expected)

    string_field_value = "a, b, c, a"
    clean_field = cleaning.str2set(string_field, separator=',')
    cleaned_data_before = {string_field: string_field_value}
    self.form.cleaned_data = cleaned_data_before
    temp = string_field_value.split(',')
    expected = set([char.strip() for char in temp])
    actual = set(clean_field(self.form))
    self.assertEqual(expected, actual)

  def testCleanIrc(self):
    """Tests cleaning.clean_irc."""
    field_name = 'test_irc'
    clean_field = cleaning.clean_irc(field_name)

    # Test that the value of the irc field will be returned
    # if it is a valid irc url
    field_value = 'irc://exampleirc.com/'
    self.form.cleaned_data = {field_name: field_value}
    self.form.fields = {field_name: forms.URLField()}
    self.assertEqual(clean_field(self.form), field_value)

    # Test that the value of the irc field will be returned
    # if it is a valid irc url with channels
    field_value = 'irc://exampleirc.com/#channel'
    self.form.cleaned_data = {field_name: field_value}
    self.form.fields = {field_name: forms.URLField()}
    self.assertEqual(clean_field(self.form), field_value)

    # Test that empty string will be returned if the value of the irc field
    # is an empty string
    field_value = ''
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), u'')

    # Test that forms.ValidationError  will be raised
    # if the value of the irc field is not a valid irc url
    field_value = 'http://exampleirc'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

    # Test that forms.ValidationError  will be raised
    # if the value of the irc field is not a valid irc url
    field_value = 'irc://kthxbai$/'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

  def testCleanMailto(self):
    """Tests cleaning.clean_mailto."""
    field_name = 'test_mailto'
    clean_field = cleaning.clean_mailto(field_name)

    # Test that the value of the mail url field will be returned
    # if it is a valid mail url
    field_value = 'mailto:someone@something.com'
    self.form.cleaned_data = {field_name: field_value}
    self.form.fields = {field_name: forms.URLField()}
    self.assertEqual(clean_field(self.form), field_value)

    # Test that empty string will be returned if the value of the mailto field
    # is an empty string
    field_value = ''
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), u'')

    # Test that forms.ValidationError will be raised
    # if the value of the mailto field is not a valid mailto or http url.
    field_value = 'someone@something.com'
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

    # Test that the value of the mailto field will be returned
    # if it is a valid http url ( a mailing group, say)
    field_value = 'http://example.com/hereisawebmailinggroup'
    self.form.cleaned_data = {field_name: field_value}
    self.form.fields = {field_name: forms.URLField()}
    self.assertEqual(clean_field(self.form), field_value)

  def testCleanBirthdate(self):
    """Tests cleaning.clean_birth_date."""
    field_name = 'test_date_of_birth'
    clean_field = cleaning.clean_birth_date(field_name)

    test_program_start = datetime.date(2013, 5, 31)
    test_min_age = 13
    test_max_age = 20

    properties = {
        'student_min_age_as_of': test_program_start,
	      'student_min_age': test_min_age,
	      'student_max_age': test_max_age
        }

    self.form.program = program_utils.seedProgram(**properties)

    # Test that forms.ValidationError is raised
    # if the student is born after one year of program start
    test_birth_date = test_program_start.replace(
        year=test_program_start.year + 1)
    field_value = test_birth_date
    self.form.cleaned_data = {field_name: field_value}
    self.form.fields = {field_name: forms.DateField()}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

    # Test that forms.ValidationError is raised
    # if the student is younger than allowed age
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - 1)
    field_value = test_birth_date
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)

    # Test that the correct value would be returned
    # if the date of birth is program's start day
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_min_age)
    field_value = test_birth_date
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)

    # Test that the correct value would be returned
    # if the student is old enough by six months
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_min_age - 1)
    test_birth_date = test_birth_date + datetime.timedelta(180)
    field_value = test_birth_date
    self.form.cleaned_data = {field_name: field_value}
    self.assertEqual(clean_field(self.form), field_value)

    # Test that forms.ValidationError is raised
    # if the student is one year older than max age
    test_birth_date = test_program_start.replace(
        year=test_program_start.year - test_max_age - 1)
    field_value = test_birth_date
    self.form.cleaned_data = {field_name: field_value}
    self.assertRaises(forms.ValidationError, clean_field, self.form)
