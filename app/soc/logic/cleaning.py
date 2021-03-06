# Copyright 2008 the Melange authors.
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

"""Generic cleaning methods."""

import HTMLParser
import re

from google.appengine.api import users

from django import forms
from django.core import validators
from django.utils import translation
from django.utils import safestring

import html5lib
from html5lib import sanitizer
from html5lib import html5parser

from melange.logic import user as user_logic
from melange.models import user as user_model

from soc.logic import validate


DEF_INVALID_EMAIL_ADDRESS = translation.ugettext(
    '"%s" is not a valid email address.')

DEF_INVALID_LINK_ID = translation.ugettext(
    '"%s" is not a properly-formed username.')

DEF_VALID_SHIPPING_CHARS = re.compile(r'^[A-Za-z0-9\s-]+$')

DEF_LINK_ID_IN_USE = translation.ugettext(
    'This username is already in use, please specify another one')

DEF_NO_RIGHTS_FOR_ACL = translation.ugettext(
    'You do not have the required rights for that ACL.')

DEF_ORGANZIATION_NOT_ACTIVE = translation.ugettext(
    "This organization is not active or doesn't exist.")

DEF_NO_SUCH_DOCUMENT = translation.ugettext(
    'There is no such document with that username under this entity.')

DEF_MUST_BE_ABOVE_AGE_LIMIT = translation.ugettext(
    'To sign up as a student for this program, you '
    'must be at least %d years of age, as of %s.')

DEF_MUST_BE_ABOVE_LIMIT = translation.ugettext(
    'Must be at least %d characters, it has %d characters.')

DEF_MUST_BE_UNDER_LIMIT = translation.ugettext(
    'Must be under %d characters, it has %d characters.')

DEF_2_LETTER_STATE = translation.ugettext(
    'State should be 2-letter field since country is "%s".')

DEF_INVALID_SHIPPING_CHARS = translation.ugettext(
    'Invalid characters, only A-z, 0-9, - and whitespace are allowed. '
    'See also <a href="http://code.google.com/p/soc/issues/detail?id=903">'
    'Issue 903</a>, in particular <a href="'
    'http://code.google.com/p/soc/issues/detail?id=903#c16">comment 16</a>. '
    'Please <em>do not</em> create a new issue about this.')

DEF_ROLE_TARGET_COUNTRY = 'United States'

DEF_ROLE_COUNTRY_PAIRS = [('res_country', 'res_state'),
                          ('ship_country', 'ship_state')]

USER_DOES_NOT_EXIST_ERROR_MSG = 'User %s does not exist.'

# The Django documentation is unclear on why ValidationErrors carry a
# "code" and what that code is supposed to signify, but for some reason
# this seems to be necessary.
_INVALID_CODE = 'invalid'


def check_field_is_empty(field_name):
  """Returns decorator that bypasses cleaning for empty fields.
  """

  def decorator(fun):
    """Decorator that checks if a field is empty if so doesn't do the cleaning.

    Note Django will capture errors concerning required fields that are empty.
    """
    from functools import wraps

    @wraps(fun)
    def wrapper(self):
      """Decorator wrapper method.
      """
      field_content = self.cleaned_data.get(field_name)

      if not field_content:
        # field has no content so bail out
        return u''
      else:
        # field has contents
        return fun(self)
    return wrapper

  return decorator


def clean_empty_field(field_name):
  """Incorporates the check_field_is_empty as regular cleaner.
  """

  @check_field_is_empty(field_name)
  def wrapper(self):
    """Decorator wrapper method.
    """
    return self.cleaned_data.get(field_name)

  return wrapper


def cleanEmail(email):
  """Validates that a string is a properly formed email address.

  Args:
    email: Any string.

  Raises:
    forms.ValidationError: The string is not a valid email address.
  """
  try:
    validators.validate_email(email)
  except forms.ValidationError as e:
    # NOTE(nathaniel): The message that Django supplies in its raised
    # ValidationError does not include the string that generated it,
    # so for user-friendliness we substitute our own message that
    # does include the input string.
    message = translation.ugettext(DEF_INVALID_EMAIL_ADDRESS % email)
    raise forms.ValidationError(message, code=e.code)


# TODO(nathaniel): Find some terms with which to document this. It's
# like a mixin... function... method... thing?
def clean_email(field_name):
  """Checks if the field_name value is in an email format.
  """
  @check_field_is_empty(field_name)
  def wrapper(self):
    """Decorator wrapper method.
    """
    # convert to lowercase for user comfort
    email = self.cleaned_data.get(field_name)
    cleanEmail(email)
    return email

  return wrapper


def cleanLinkID(link_id):
  """Validates that a string fits the form required of a link ID.

  Args:
    link_id: Any string.

  Raises:
    forms.ValidationError: The string does not fit the form required
      of a link ID.
  """
  if not validate.isLinkIdFormatValid(link_id):
    raise forms.ValidationError(
        DEF_INVALID_LINK_ID % link_id, code=_INVALID_CODE)


# TODO(nathaniel): Document this too in some form or another.
def clean_link_id(field_name):
  """Checks if the field_name value is in a valid link ID format.
  """

  @check_field_is_empty(field_name)
  def wrapper(self):
    """Decorator wrapper method.
    """
    # convert to lowercase for user comfort
    link_id = self.cleaned_data.get(field_name).lower()
    cleanLinkID(link_id)
    return link_id
  return wrapper


def clean_existing_user(field_name):
  """Check if the field_name field is a valid user.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method."""
    user_id = clean_link_id(field_name)(self)
    user = user_model.User.get_by_id(user_id)

    if not user:
      # user does not exist
      raise forms.ValidationError(
          USER_DOES_NOT_EXIST_ERROR_MSG % user_id)

    return user
  return wrapped


def clean_user_is_current(field_name, as_user=True):
  """Check if the field_name value is a valid link_id and resembles the
     current user.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method."""
    user_id = clean_link_id(field_name)(self)

    current_user = user_logic.getByCurrentAccount()
    if not current_user or current_user.user_id != user_id:
      # this user is not the current user
      raise forms.ValidationError('This user is not you.')

    return current_user if as_user else user_id
  return wrapped


def clean_user_not_exist(field_name):
  """Check if the field_name value is a valid link_id and a user with the
     link id does not exist.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method."""
    user_id = clean_link_id(field_name)(self)
    user = user_model.User.get_by_id(user_id)

    if user:
      # user exists already
      raise forms.ValidationError('There is already a user with this username.')

    return user_id
  return wrapped


def clean_users_not_same(field_name):
  """Check if the field_name field is a valid user and is not
     equal to the current user.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method.
    """
    clean_user_field = clean_existing_user(field_name)
    user = clean_user_field(self)

    current_user = user_logic.getByCurrentAccount()
    if user.key == current_user.key:
      # users are equal
      raise forms.ValidationError('You cannot enter yourself here.')

    return user
  return wrapped


def cleanValidAddressCharacters(value):
  """Cleaning method for a value that is submitted as a part of an address
  information. It ensures that it complies with Google's character
  requirements for shipping purposes.

  Args:
    value: The value submitted in the form as a part of an address.

  Returns:
    Cleaned value for the field.

  Raises:
    django_forms.ValidationError if the submitted value contains invalid
    characters.
  """
  if value and not DEF_VALID_SHIPPING_CHARS.match(value):
    raise forms.ValidationError(
        safestring.mark_safe(DEF_INVALID_SHIPPING_CHARS))
  else:
    return value


def clean_content_length(field_name, min_length=0, max_length=500):
  """Clean method for cleaning a field which must contain at least min and
     not more then max length characters.

  Args:
    field_name: the name of the field needed cleaning
    min_length: the minimum amount of allowed characters
    max_length: the maximum amount of allowed characters
  """

  @check_field_is_empty(field_name)
  def wrapper(self):
    """Decorator wrapper method.
    """

    value = self.cleaned_data[field_name]
    value_length = len(value)

    if value_length < min_length:
      raise forms.ValidationError(DEF_MUST_BE_ABOVE_LIMIT %(
          min_length, value_length))

    if value_length > max_length:
      raise forms.ValidationError(DEF_MUST_BE_UNDER_LIMIT %(
          max_length, value_length))

    return value
  return wrapper


def clean_phone_number(field_name):
  """Clean method for cleaning a field that may only contain numerical values.
  """

  @check_field_is_empty(field_name)
  def wrapper(self):
    """Decorator wrapped method.
    """

    value = self.cleaned_data.get(field_name)

    # allow for a '+' prefix which means '00'
    if value[0] == '+':
      value = '00' + value[1:]

    if not value.isdigit():
      raise forms.ValidationError('Only numerical characters are allowed')

    return value
  return wrapper


def clean_feed_url(field_name):
  """Clean method for cleaning feed url.
  """

  def wrapper(self):
    """Decorator wrapped method.
    """
    feed_url = self.cleaned_data.get(field_name)

    if feed_url == '':
      # feed url not supplied (which is OK), so do not try to validate it
      return None

    if not validate.isFeedURLValid(feed_url):
      raise forms.ValidationError('This URL is not a valid ATOM or RSS feed.')

    return feed_url
  return wrapper


def sanitize_html_string(content):
  """Sanitizes the given html string.

  Raises:
    forms.ValidationError in case of an error.
  """
  try:
    parser = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer)
    parsed = parser.parseFragment(content, encoding='utf-8')
    cleaned_content = ''.join([tag.toxml() for tag in parsed.childNodes])
  except (HTMLParser.HTMLParseError, html5parser.ParseError) as msg:
    raise forms.ValidationError(msg)

  return cleaned_content


def clean_html_content(field_name):
  """Clean method for cleaning HTML content.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method.
    """
    content = self.cleaned_data.get(field_name)

    # clean_html_content is called when writing data into GAE rather than
    # when reading data from GAE. This short-circuiting of the sanitizer
    # only affects html authored by developers. The is_current_user_admin test
    # for example allows developers to add javascript.
    if users.is_current_user_admin():
      return content

    content = sanitize_html_string(content)

    return content

  return wrapped


def clean_url(field_name):
  """Clean method for cleaning a field belonging to a LinkProperty.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method.
    """

    value = self.cleaned_data.get(field_name)
    validator = validators.URLValidator()

    # call the Django URLField cleaning method to
    # properly clean/validate this field
    try:
      validator(value)
    except forms.ValidationError as e:
      if e.code == 'invalid':
        msg = translation.ugettext(u'Enter a valid URL.')
        raise forms.ValidationError(msg, code='invalid')
    return value
  return wrapped


def clean_irc(field_name):
  """Clean method for cleaning an irc field.
  """

  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method.
    """

    value = self.cleaned_data.get(field_name)
    validator = validators.URLValidator()

    to_clean = value

    if value.startswith('irc://'):
      to_clean = value.replace('irc://', 'http://', 1)

    # call the Django URLField cleaning method to
    # properly clean/validate this field
    try:
      validator(to_clean)
    except forms.ValidationError as e:
      if e.code == 'invalid':
        msg = translation.ugettext(u'Enter a valid URL or irc:// url.')
        raise forms.ValidationError(msg, code='invalid')
    return value
  return wrapped


def clean_mailto(field_name):
  @check_field_is_empty(field_name)
  def wrapped(self):
    """Decorator wrapper method.
    """

    value = self.cleaned_data.get(field_name)
    validator = validators.URLValidator()

    to_clean = value

    if value.startswith('mailto:'):
      to_clean = value.replace('mailto:', '', 1)
      validator = validators.validate_email

    # call the Django URLField cleaning method to
    # properly clean/validate this field
    try:
      validator(to_clean)
    except forms.ValidationError as e:
      if e.code == 'invalid':
        msg = translation.ugettext(u'Enter a valid URL or mailto: link.')
        raise forms.ValidationError(msg, code='invalid')
    return value
  return wrapped

def str2set(string_field, separator=','):
  """Clean method for cleaning comma separated strings.

  Obtains the separated string from the form and returns it as
  a set of strings.
  """

  def wrapper(self):
    """Decorator wrapper method.
    """
    cleaned_data = self.cleaned_data

    string_data = cleaned_data.get(string_field)

    list_data = []
    for string in string_data.split(separator):
      string_strip = string.strip()
      if string_strip and string_strip not in list_data:
        list_data.append(string_strip)

    return list_data

  return wrapper
