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

"""Module containing the profile related views for Summer Of Code."""

from django import forms as django_forms
from django.utils import translation

from melange.request import access
from melange.utils import countries

from soc.logic import cleaning

from soc.views.helper import url_patterns

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.views.helper import urls


PROFILE_ORG_MEMBER_CREATE_PAGE_NAME = translation.ugettext(
    'Create organization member profile')

USER_ID_HELP_TEXT = translation.ugettext(
    'Used as part of various URL links throughout the site. '
    'ASCII alphanumeric characters, digits, and underscores only.')

PUBLIC_NAME_HELP_TEXT = translation.ugettext(
    'Human-readable name (UTF-8) that will be displayed publicly on the site.')

WEB_PAGE_HELP_TEXT = translation.ugettext(
    'URL to your personal web page, if you have one.')

BLOG_HELP_TEXT = translation.ugettext(
    'URL to a page with your personal blog, if you have one.')

PHOTO_URL_HELP_TEXT = translation.ugettext(
    'URL to 64x64 pixel thumbnail image.')

FIRST_NAME_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

LAST_NAME_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

EMAIL_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

PHONE_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

RESIDENTIAL_STREET_HELP_TEXT = translation.ugettext(
    'Street number and name plus optional suite/apartment number.')

RESIDENTIAL_CITY_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

RESIDENTIAL_PROVINCE_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

RESIDENTIAL_COUNTRY_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

RESIDENTIAL_POSTAL_CODE_HELP_TEXT = translation.ugettext('TODO(daniel): do it')

BIRTH_DATE_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

TEE_STYLE_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

TEE_SIZE_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

GENDER_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

PROGRAM_KNOWLEDGE_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

USER_ID_LABEL = translation.ugettext('Username')

PUBLIC_NAME_LABEL = translation.ugettext('Public name')

WEB_PAGE_LABEL = translation.ugettext('Home page URL')

BLOG_LABEL = translation.ugettext('Blog URL')

PHOTO_URL_LABEL = translation.ugettext('Photo URL')

FIRST_NAME_LABEL = translation.ugettext('First name')

LAST_NAME_LABEL = translation.ugettext('Last name')

EMAIL_LABEL = translation.ugettext('Email')

PHONE_LABEL = translation.ugettext('Phone number')

RESIDENTIAL_STREET_LABEL = translation.ugettext('Address')

RESIDENTIAL_CITY_LABEL = translation.ugettext('City')

RESIDENTIAL_PROVINCE_LABEL = translation.ugettext('State/Province')

RESIDENTIAL_COUNTRY_LABEL = translation.ugettext('Country/Territory')

RESIDENTIAL_POSTAL_CODE_LABEL = translation.ugettext('ZIP/Postal code')

BIRTH_DATE_LABEL = translation.ugettext('Birth date')

TEE_STYLE_LABEL = translation.ugettext('T-Shirt style')

TEE_SIZE_LABEL = translation.ugettext('T-Shirt size')

GENDER_LABEL = translation.ugettext('Gender')

PROGRAM_KNOWLEDGE_LABEL = translation.ugettext(
    'How did you hear about the program?')

TEE_STYLE_CHOICES = (
    ('female', 'Female'),
    ('male', 'Male'))

TEE_SIZE_CHOICES = (
    ('xxs', 'XXS'),
    ('xs', 'XS'),
    ('s', 'S'),
    ('m', 'M'),
    ('l', 'L'),
    ('xl', 'XL'),
    ('xxl', 'XXL'),
    ('xxxl', 'XXXL'))

GENDER_CHOICES = (
    ('female', 'Female'),
    ('male', 'Male'),
    ('other', 'Other'),
    ('not_answered', 'I would prefer not to answer'))


def cleanUserId(user_id):
  """Cleans user_id field.

  Args:
    user_id: The submitted user ID.

  Returns:
    Cleaned value for user_id field.

  Raises:
    django_forms.ValidationError if the submitted value is not valid.
  """
  if not user_id:
    raise django_forms.ValidationError('This field is required.')

  cleaning.cleanLinkID(user_id)

  return user_id


class _UserProfileForm(gsoc_forms.GSoCModelForm):
  """Form to set profile properties by a user."""

  user_id = django_forms.CharField(
      required=True, label=USER_ID_LABEL, help_text=USER_ID_HELP_TEXT)

  public_name = django_forms.CharField(
      required=True, label=PUBLIC_NAME_LABEL, help_text=PUBLIC_NAME_HELP_TEXT)

  web_page = django_forms.URLField(
      required=False, label=WEB_PAGE_LABEL, help_text=WEB_PAGE_HELP_TEXT)

  blog = django_forms.URLField(
      required=False, label=BLOG_LABEL, help_text=BLOG_HELP_TEXT)

  photo_url = django_forms.URLField(
      required=False, label=PHOTO_URL_LABEL, help_text=PHOTO_URL_HELP_TEXT)

  first_name = django_forms.CharField(
      required=True, label=FIRST_NAME_LABEL, help_text=FIRST_NAME_HELP_TEXT)

  last_name = django_forms.CharField(
      required=True, label=LAST_NAME_LABEL, help_text=LAST_NAME_HELP_TEXT)

  email = django_forms.EmailField(
      required=True, label=EMAIL_LABEL, help_text=EMAIL_HELP_TEXT)

  phone = django_forms.EmailField(
      required=True, label=PHONE_LABEL, help_text=PHONE_HELP_TEXT)

  residential_street = django_forms.CharField(
      required=True, label=RESIDENTIAL_STREET_LABEL,
      help_text=RESIDENTIAL_STREET_HELP_TEXT)

  residential_city = django_forms.CharField(
      required=True, label=RESIDENTIAL_CITY_LABEL,
      help_text=RESIDENTIAL_CITY_HELP_TEXT)

  residential_province = django_forms.CharField(
      required=False, label=RESIDENTIAL_PROVINCE_LABEL,
      help_text=RESIDENTIAL_PROVINCE_HELP_TEXT)

  residential_country = django_forms.CharField(
      required=True, label=RESIDENTIAL_COUNTRY_LABEL,
      help_text=RESIDENTIAL_COUNTRY_HELP_TEXT,
      widget=django_forms.Select(
          choices=[
              (country, country)
              for country in countries.COUNTRIES_AND_TERRITORIES]))

  residential_postal_code = django_forms.CharField(
      required=True, label=RESIDENTIAL_POSTAL_CODE_LABEL,
      help_text=RESIDENTIAL_POSTAL_CODE_HELP_TEXT)

  birth_date = django_forms.DateField(
      required=True, label=BIRTH_DATE_LABEL, help_text=BIRTH_DATE_HELP_TEXT)

  tee_style = django_forms.CharField(
      required=False, label=TEE_STYLE_LABEL, help_text=TEE_STYLE_HELP_TEXT,
      widget=django_forms.Select(choices=TEE_STYLE_CHOICES))

  tee_size = django_forms.CharField(
      required=False, label=TEE_SIZE_LABEL, help_text=TEE_SIZE_HELP_TEXT,
      widget=django_forms.Select(choices=TEE_SIZE_CHOICES))

  gender = django_forms.CharField(
      required=True, label=GENDER_LABEL, help_text=GENDER_HELP_TEXT,
      widget=django_forms.Select(choices=GENDER_CHOICES))

  program_knowledge = django_forms.CharField(
      required=True, label=PROGRAM_KNOWLEDGE_LABEL,
      help_text=PROGRAM_KNOWLEDGE_HELP_TEXT,
      widget=django_forms.Textarea())

  Meta = object

  def clean_user_id(self):
    """Cleans user_id field.

    Returns:
      Cleaned value for user_id field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanUserId(self.cleaned_data['user_id'])


def _profileFormToRegisterAsOrgMember(register_user, **kwargs):
  """Returns a Django form to register a new profile for organization members.

  Args:
    register_user: If set to True, the constructed form will also be used to
      create a new User entity along with a new Profile entity.

  Returns:
    _UserProfileForm adjusted to create a new profile for organization members.
  """
  form = _UserProfileForm(**kwargs)

  if not register_user:
    del form.fields['user_id']

  return form


class ProfileRegisterAsOrgMemberPage(base.GSoCRequestHandler):
  """View to create organization member profile.

  It will be used by prospective organization members. Users with such profiles
  will be eligible to connect with organizations and participate in the program
  as administrators or mentors.
  """

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/form_base.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'profile/register/org_member/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.PROFILE_REGISTER_AS_ORG_MEMBER)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _profileFormToRegisterAsOrgMember(data.user is None, data=data.POST)

    return {
        'page_name': PROFILE_ORG_MEMBER_CREATE_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _profileFormToRegisterAsOrgMember(data.user is None, data=data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      # TODO(daniel): implement it
      pass
