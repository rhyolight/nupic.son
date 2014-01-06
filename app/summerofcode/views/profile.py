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

from google.appengine.ext import ndb

from django import http
from django import forms as django_forms
from django.utils import translation

from melange import types
from melange.logic import address as address_logic
from melange.logic import contact as contact_logic
from melange.logic import education as education_logic
from melange.logic import profile as profile_logic
from melange.logic import user as user_logic
from melange.models import education as education_model
from melange.models import profile as profile_model
from melange.request import access
from melange.request import exception
from melange.request import links
from melange.utils import countries
from melange.views.helper import form_handler

from soc.logic import cleaning

from soc.views import forms as soc_forms
from soc.views.helper import url_patterns

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.views.helper import urls


_ALPHANUMERIC_CHARACTERS_ONLY = unicode(
    'Please use alphanumeric characters (A-z, 0-9) and whitespaces only.')

PROFILE_ORG_MEMBER_CREATE_PAGE_NAME = translation.ugettext(
    'Create organization member profile')

PROFILE_STUDENT_CREATE_PAGE_NAME = translation.ugettext(
    'Create student profile')

PROFILE_EDIT_PAGE_NAME = translation.ugettext(
    'Edit profile')

# names of structures to group related fields together
_PUBLIC_INFORMATION_GROUP = translation.ugettext('1. Public information')
_CONTACT_GROUP = translation.ugettext('2. Contact information')
_RESIDENTIAL_ADDRESS_GROUP = translation.ugettext('3. Residential address')
_SHIPPING_ADDRESS_GROUP = translation.ugettext('4. Shipping address')
_OTHER_INFORMATION_GROUP = translation.ugettext('5. Other information')
_EDUCATION_GROUP = translation.ugettext('6. Education')
_TERMS_OF_SERVICE_GROUP = translation.ugettext('7. Terms Of Service')

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

FIRST_NAME_HELP_TEXT = translation.ugettext(
    'First name of the participant. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

LAST_NAME_HELP_TEXT = translation.ugettext(
    'Last name of the participant. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

EMAIL_HELP_TEXT = translation.ugettext(
    'Email address of the participant. All program related emails '
    'will be sent to this address. Please note this information is kept '
    'private and visible only to program administrators.')

PHONE_HELP_TEXT = translation.ugettext(
    'Phone number of the participant. Please use digits only and remember '
    'to include the country code. Please note this information is kept '
    'private and visible only to program administrators who may need to '
    'contact you occasionally.')

RESIDENTIAL_STREET_HELP_TEXT = translation.ugettext(
    'Street number and name information plus optional suite/apartment number. '
    + _ALPHANUMERIC_CHARACTERS_ONLY)

RESIDENTIAL_CITY_HELP_TEXT = translation.ugettext(
    'City information. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

RESIDENTIAL_PROVINCE_HELP_TEXT = translation.ugettext(
    'State or province information. In case you live in the United States, '
    'type the two letter state abbreviation. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

RESIDENTIAL_COUNTRY_HELP_TEXT = translation.ugettext('Country information.')

RESIDENTIAL_POSTAL_CODE_HELP_TEXT = translation.ugettext(
    'ZIP/Postal code information. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

IS_SHIPPING_ADDRESS_DIFFERENT_HELP_TEXT = translation.ugettext(
    'Please check this box if your shipping address is different than '
    'the residential address provided above.')

SHIPPING_NAME_HELP_TEXT = translation.ugettext(
    'Fill in the name of the person who should be receiving your packages. '
    + _ALPHANUMERIC_CHARACTERS_ONLY)

SHIPPING_STREET_HELP_TEXT = translation.ugettext(
    'Street number and name information plus optional suite/apartment number. '
    + _ALPHANUMERIC_CHARACTERS_ONLY)

SHIPPING_CITY_HELP_TEXT = translation.ugettext(
    'City information. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

SHIPPING_PROVINCE_HELP_TEXT = translation.ugettext(
    'State or province information. In case packages should be sent to '
    'the United States, type the two letter state abbreviation. '
    + _ALPHANUMERIC_CHARACTERS_ONLY)

SHIPPING_COUNTRY_HELP_TEXT = translation.ugettext('Country information.')

SHIPPING_POSTAL_CODE_HELP_TEXT = translation.ugettext(
    'ZIP/Postal code information. ' + _ALPHANUMERIC_CHARACTERS_ONLY)

BIRTH_DATE_HELP_TEXT = translation.ugettext(
    'Birth date of the participant. Use YYYY-MM-DD format. Please note this '
    'information is kept private and visible only to program administrators '
    'in order to determine program eligibility.')

TEE_STYLE_HELP_TEXT = translation.ugettext(
    'Style of a T-Shirt that may be sent to you upon program completion.')

TEE_SIZE_HELP_TEXT = translation.ugettext(
    'Size of a T-Shirt that may be sent to you upon program completion.')

GENDER_HELP_TEXT = translation.ugettext(
    'Gender information of the participant. Please note this information'
    'is kept private and visible only to program administrators for '
    'statistical purposes.')

PROGRAM_KNOWLEDGE_HELP_TEXT = translation.ugettext(
    'Please be as specific as possible, e.g. blog post (include URL '
    'if possible), mailing list (please include list address), information '
    'session (please include location and speakers if you can), etc.')

SCHOOL_COUNTRY_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

SCHOOL_NAME_HELP_TEXT = translation.ugettext('TODO(daniel): complete')

MAJOR_HELP_TEXT = translation.ugettext('Your major at the university.')

DEGREE_HELP_TEXT = translation.ugettext(
    'Select degree that is the one you are working towards today.')

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

IS_SHIPPING_ADDRESS_DIFFERENT_LABEL = translation.ugettext(
    'Shipping address is different than residential address')

SHIPPING_NAME_LABEL = translation.ugettext('Full recipient name')

SHIPPING_STREET_LABEL = translation.ugettext('Address')

SHIPPING_CITY_LABEL = translation.ugettext('City')

SHIPPING_PROVINCE_LABEL = translation.ugettext('State/Province')

SHIPPING_COUNTRY_LABEL = translation.ugettext('Country/Territory')

SHIPPING_POSTAL_CODE_LABEL = translation.ugettext('ZIP/Postal code')

BIRTH_DATE_LABEL = translation.ugettext('Birth date')

TEE_STYLE_LABEL = translation.ugettext('T-Shirt style')

TEE_SIZE_LABEL = translation.ugettext('T-Shirt size')

GENDER_LABEL = translation.ugettext('Gender')

PROGRAM_KNOWLEDGE_LABEL = translation.ugettext(
    'How did you hear about the program?')

TERMS_OF_SERVICE_LABEL = translation.ugettext(
    'I have read and agree to the terms of service')

SCHOOL_COUNTRY_LABEL = translation.ugettext('School country')

SCHOOL_NAME_LABEL = translation.ugettext('School name')

MAJOR_LABEL = translation.ugettext('Major')

DEGREE_LABEL = translation.ugettext('Degree')

TERMS_OF_SERVICE_NOT_ACCEPTED = translation.ugettext(
    'You cannot register without agreeing to the Terms of Service')

_TEE_STYLE_FEMALE_ID = 'female'
_TEE_STYLE_MALE_ID = 'male'

TEE_STYLE_CHOICES = (
    (_TEE_STYLE_FEMALE_ID, 'Female'),
    (_TEE_STYLE_MALE_ID, 'Male'))

_TEE_SIZE_XXS_ID = 'xxs'
_TEE_SIZE_XS_ID = 'xs'
_TEE_SIZE_S_ID = 's'
_TEE_SIZE_M_ID = 'm'
_TEE_SIZE_L_ID = 'l'
_TEE_SIZE_XL_ID = 'xl'
_TEE_SIZE_XXL_ID = 'xxl'
_TEE_SIZE_XXXL_ID = 'xxxl'

TEE_SIZE_CHOICES = (
    (_TEE_SIZE_XXS_ID, 'XXS'),
    (_TEE_SIZE_XS_ID, 'XS'),
    (_TEE_SIZE_S_ID, 'S'),
    (_TEE_SIZE_M_ID, 'M'),
    (_TEE_SIZE_L_ID, 'L'),
    (_TEE_SIZE_XL_ID, 'XL'),
    (_TEE_SIZE_XXL_ID, 'XXL'),
    (_TEE_SIZE_XXXL_ID, 'XXXL'))

_GENDER_FEMALE_ID = 'female'
_GENDER_MALE_ID = 'male'
_GENDER_OTHER_ID = 'other'
_GENDER_NOT_ANSWERED_ID = 'not_answered'

GENDER_CHOICES = (
    (_GENDER_FEMALE_ID, 'Female'),
    (_GENDER_MALE_ID, 'Male'),
    (_GENDER_OTHER_ID, 'Other'),
    (_GENDER_NOT_ANSWERED_ID, 'I would prefer not to answer'))

_DEGREE_UNDERGRADUATE_ID = 'undergraduate'
_DEGREE_MASTERS_ID = 'masters'
_DEGREE_PHD_ID = 'phd'

DEGREE_CHOICES = (
    (_DEGREE_UNDERGRADUATE_ID, translation.ugettext('Undergraduate')),
    (_DEGREE_MASTERS_ID, translation.ugettext('Master\'s')),
    (_DEGREE_PHD_ID, translation.ugettext('PhD')))

_USER_PROPERTIES_FORM_KEYS = ['user_id']

_PROFILE_PROPERTIES_FORM_KEYS = [
    'public_name', 'photo_url', 'first_name', 'last_name', 'birth_date',
    'tee_style', 'tee_size', 'gender', 'terms_of_service']

_CONTACT_PROPERTIES_FORM_KEYS = ['web_page', 'blog', 'email', 'phone']

_RESIDENTIAL_ADDRESS_PROPERTIES_FORM_KEYS = [
    'residential_street', 'residential_city', 'residential_province',
    'residential_country', 'residential_postal_code']

_SHIPPING_ADDRESS_PROPERTIES_FORM_KEYS = [
    'shipping_name', 'shipping_street', 'shipping_city', 'shipping_province',
    'shipping_country', 'shipping_postal_code']

_STUDENT_DATA_PROPERTIES_FORM_FIELDS = [
    'school_country', 'school_name', 'major', 'degree']

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


def _cleanShippingAddressPart(
    is_shipping_address_different, value, is_required):
  """Cleans a field that represents a part of the shipping address.

  Args:
    is_shipping_address_different: A bool indicating if the shipping address
      to provide is different than the residential address.
    value: The actual submitted value for the cleaned field.
    is_required: Whether a value for the cleaned field is required or not.

  Returns:
    Cleaned value for the field.

  Raises:
    django_forms.ValidationError if the submitted value is not valid.
  """
  if not is_shipping_address_different and value:
    raise django_forms.ValidationError(
        'This field cannot be specified if the shipping address is the same '
        'as the residential address.')
  elif is_shipping_address_different and not value and is_required:
    raise django_forms.ValidationError('This field is required.')
  else:
    return value


def cleanTermsOfService(is_accepted, terms_of_service):
  """Cleans terms_of_service field.

  Args:
    is_accepted: A bool determining whether the user has accepted the terms
      of service of not.
    terms_of_service: Document entity that contains the terms of service that
      need to be accepted.

  Returns:
    Cleaned value of terms_of_service field. Specifically, it is a key
    of a document entity that contains the accepted terms of service.

  Raises:
    django_forms.ValidationError is the submitted value is not valid.
  """
  if not terms_of_service:
    return None
  elif not is_accepted:
    raise django_forms.ValidationError(TERMS_OF_SERVICE_NOT_ACCEPTED)
  else:
    return ndb.Key.from_old_key(terms_of_service.key())


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

  phone = django_forms.CharField(
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

  is_shipping_address_different = django_forms.BooleanField(
      required=False, label=IS_SHIPPING_ADDRESS_DIFFERENT_LABEL,
      help_text=IS_SHIPPING_ADDRESS_DIFFERENT_HELP_TEXT)

  shipping_name = django_forms.CharField(
      required=False, label=SHIPPING_NAME_LABEL,
      help_text=SHIPPING_NAME_HELP_TEXT)

  shipping_street = django_forms.CharField(
      required=False, label=SHIPPING_STREET_LABEL,
      help_text=SHIPPING_STREET_HELP_TEXT)

  shipping_city = django_forms.CharField(
      required=False, label=SHIPPING_CITY_LABEL,
      help_text=SHIPPING_CITY_HELP_TEXT)

  shipping_province = django_forms.CharField(
      required=False, label=SHIPPING_PROVINCE_LABEL,
      help_text=SHIPPING_PROVINCE_HELP_TEXT)

  shipping_country = django_forms.CharField(
      required=False,label=SHIPPING_COUNTRY_LABEL,
      help_text=SHIPPING_COUNTRY_HELP_TEXT,
      widget=django_forms.Select(
          choices=[('', 'Not Applicable')] + [
              (country, country)
              for country in countries.COUNTRIES_AND_TERRITORIES]))

  shipping_postal_code = django_forms.CharField(
      required=False, label=SHIPPING_POSTAL_CODE_LABEL,
      help_text=SHIPPING_POSTAL_CODE_HELP_TEXT)

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

  terms_of_service = django_forms.BooleanField(
      required=True, label=TERMS_OF_SERVICE_LABEL)

  school_country = django_forms.CharField(
      required=True, label=SCHOOL_COUNTRY_LABEL,
      help_text=SCHOOL_COUNTRY_HELP_TEXT,
      widget=django_forms.Select(
          choices=[
              (country, country)
              for country in countries.COUNTRIES_AND_TERRITORIES]))

  school_name = django_forms.CharField(
      required=True, label=SCHOOL_NAME_LABEL, help_text=SCHOOL_NAME_HELP_TEXT)

  major = django_forms.CharField(
      required=True, label=MAJOR_LABEL, help_text=MAJOR_HELP_TEXT)

  degree = django_forms.CharField(
      required=True, label=DEGREE_LABEL, help_text=DEGREE_HELP_TEXT,
      widget=django_forms.Select(choices=DEGREE_CHOICES))

  Meta = object

  def __init__(self, terms_of_service=None, has_student_data=None, **kwargs):
    """Initializes a new form.

    Args:
      terms_of_service: Document with Terms of Service that has to be accepted
        by the user.
      has_student_data: If specified to True, the form will contain fields
        related to student data for the profile.
    """
    super(_UserProfileForm, self).__init__(**kwargs)
    self.terms_of_service = terms_of_service
    self.has_student_data = has_student_data

    # group public information related fields together
    self.fields['public_name'].group = _PUBLIC_INFORMATION_GROUP
    self.fields['web_page'].group = _PUBLIC_INFORMATION_GROUP
    self.fields['blog'].group = _PUBLIC_INFORMATION_GROUP
    self.fields['photo_url'].group = _PUBLIC_INFORMATION_GROUP

    # group contact information related fields together
    self.fields['first_name'].group = _CONTACT_GROUP
    self.fields['last_name'].group = _CONTACT_GROUP
    self.fields['email'].group = _CONTACT_GROUP
    self.fields['phone'].group = _CONTACT_GROUP

    # group residential address related fields together
    self.fields['residential_street'].group = _RESIDENTIAL_ADDRESS_GROUP
    self.fields['residential_city'].group = _RESIDENTIAL_ADDRESS_GROUP
    self.fields['residential_province'].group = _RESIDENTIAL_ADDRESS_GROUP
    self.fields['residential_country'].group = _RESIDENTIAL_ADDRESS_GROUP
    self.fields['residential_postal_code'].group = _RESIDENTIAL_ADDRESS_GROUP

    # group residential address related fields together
    self.fields['is_shipping_address_different'].group = _SHIPPING_ADDRESS_GROUP
    self.fields['shipping_name'].group = _SHIPPING_ADDRESS_GROUP
    self.fields['shipping_street'].group = _SHIPPING_ADDRESS_GROUP
    self.fields['shipping_city'].group = _SHIPPING_ADDRESS_GROUP
    self.fields['shipping_province'].group = _SHIPPING_ADDRESS_GROUP
    self.fields['shipping_country'].group = _SHIPPING_ADDRESS_GROUP
    self.fields['shipping_postal_code'].group = _SHIPPING_ADDRESS_GROUP

    # group other information related fields together
    self.fields['birth_date'].group = _OTHER_INFORMATION_GROUP
    self.fields['tee_style'].group = _OTHER_INFORMATION_GROUP
    self.fields['tee_size'].group = _OTHER_INFORMATION_GROUP
    self.fields['gender'].group = _OTHER_INFORMATION_GROUP
    self.fields['program_knowledge'].group = _OTHER_INFORMATION_GROUP

    # remove terms of service field if no document is defined
    if not self.terms_of_service:
      del self.fields['terms_of_service']
    else:
      self.fields['terms_of_service'].widget = soc_forms.TOSWidget(
          self.terms_of_service.content)
      self.fields['terms_of_service'].group = _TERMS_OF_SERVICE_GROUP

    if not self.has_student_data:
      # remove all fields associated with student data
      for field_name in _STUDENT_DATA_PROPERTIES_FORM_FIELDS:
        del self.fields[field_name]
    else:
      # group education related fields together
      self.fields['school_country'].group = _EDUCATION_GROUP
      self.fields['school_name'].group = _EDUCATION_GROUP
      self.fields['major'].group = _EDUCATION_GROUP
      self.fields['degree'].group = _EDUCATION_GROUP

  def clean_user_id(self):
    """Cleans user_id field.

    Returns:
      Cleaned value for user_id field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanUserId(self.cleaned_data['user_id'])

  def clean_shipping_name(self):
    """Cleans shipping_name field.

    Returns:
      Cleaned value for shipping_name field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return _cleanShippingAddressPart(
        self.cleaned_data['is_shipping_address_different'],
        self.cleaned_data['shipping_name'], False)

  def clean_shipping_street(self):
    """Cleans shipping_street field.

    Returns:
      Cleaned value for shipping_street field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return _cleanShippingAddressPart(
        self.cleaned_data['is_shipping_address_different'],
        self.cleaned_data['shipping_street'], True)

  def clean_shipping_city(self):
    """Cleans shipping_city field.

    Returns:
      Cleaned value for shipping_city field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return _cleanShippingAddressPart(
        self.cleaned_data['is_shipping_address_different'],
        self.cleaned_data['shipping_city'], True)

  def clean_shipping_province(self):
    """Cleans shipping_province field.

    Returns:
      Cleaned value for shipping_province field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return _cleanShippingAddressPart(
        self.cleaned_data['is_shipping_address_different'],
        self.cleaned_data['shipping_province'], False)

  def clean_shipping_country(self):
    """Cleans shipping_country field.

    Returns:
      Cleaned value for shipping_country field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return _cleanShippingAddressPart(
        self.cleaned_data['is_shipping_address_different'],
        self.cleaned_data['shipping_country'], True)

  def clean_shipping_postal_code(self):
    """Cleans shipping_postal_code field.

    Returns:
      Cleaned value for shipping_postal_code field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return _cleanShippingAddressPart(
        self.cleaned_data['is_shipping_address_different'],
        self.cleaned_data['shipping_postal_code'], True)

  def clean_terms_of_service(self):
    """Cleans terms_of_service_field.

    Returns:
      Cleaned value of terms_of_service field. Specifically, it is a key
      of a document entity that contains the accepted terms of service.

    Raises:
      django_forms.ValidationError is the submitted value is not valid.
    """
    return cleanTermsOfService(
        self.cleaned_data['terms_of_service'], self.terms_of_service)

  def getUserProperties(self):
    """Returns properties of the user that were submitted in this form.

    Returns:
      A dict mapping user properties to the corresponding values.
    """
    return self._getPropertiesForFields(_USER_PROPERTIES_FORM_KEYS)

  def getProfileProperties(self):
    """Returns properties of the profile that were submitted in this form.

    Returns:
      A dict mapping profile properties to the corresponding values.
    """
    return self._getPropertiesForFields(_PROFILE_PROPERTIES_FORM_KEYS)

  def getContactProperties(self):
    """Returns properties of the contact information that were submitted
    in this form.

    Returns:
      A dict mapping profile properties to the corresponding values.
    """
    return self._getPropertiesForFields(_CONTACT_PROPERTIES_FORM_KEYS)

  def getResidentialAddressProperties(self):
    """Returns properties of the residential address that were submitted
    in this form.

    Returns:
      A dict mapping residential address properties to the corresponding values.
    """
    return self._getPropertiesForFields(
        _RESIDENTIAL_ADDRESS_PROPERTIES_FORM_KEYS)

  def getShippingAddressProperties(self):
    """Returns properties of the shipping address that were submitted in
    this form.

    Returns:
      A dict mapping shipping address properties to the corresponding values
      or None, if the shipping address has not been specified.
    """
    return (self._getPropertiesForFields(_SHIPPING_ADDRESS_PROPERTIES_FORM_KEYS)
        if self.cleaned_data['is_shipping_address_different'] else None)

  def getStudentDataProperties(self):
    """Returns properties of the student data that were submitted in this form.

    Returns:
      A dict mapping student data properties to the corresponding values
      or None, if student data does not apply to this form.
    """
    return (self._getPropertiesForFields(_STUDENT_DATA_PROPERTIES_FORM_FIELDS)
        if self.has_student_data else None)


_TEE_STYLE_ID_TO_ENUM_LINK = (
    (_TEE_STYLE_FEMALE_ID, profile_model.TeeStyle.FEMALE),
    (_TEE_STYLE_MALE_ID, profile_model.TeeStyle.MALE)
    )
_TEE_STYLE_ID_TO_ENUM_MAP = dict(_TEE_STYLE_ID_TO_ENUM_LINK)
_TEE_STYLE_ENUM_TO_ID_MAP = dict(
    (v, k) for (k, v) in _TEE_STYLE_ID_TO_ENUM_LINK)

_TEE_SIZE_ID_TO_ENUM_LINK = (
    (_TEE_SIZE_XXS_ID, profile_model.TeeSize.XXS),
    (_TEE_SIZE_XS_ID, profile_model.TeeSize.XS),
    (_TEE_SIZE_S_ID, profile_model.TeeSize.S),
    (_TEE_SIZE_M_ID, profile_model.TeeSize.M),
    (_TEE_SIZE_L_ID, profile_model.TeeSize.L),
    (_TEE_SIZE_XL_ID, profile_model.TeeSize.XL),
    (_TEE_SIZE_XXL_ID, profile_model.TeeSize.XXL),
    (_TEE_SIZE_XXXL_ID, profile_model.TeeSize.XXXL)
    )
_TEE_SIZE_ID_TO_ENUM_MAP = dict(_TEE_SIZE_ID_TO_ENUM_LINK)
_TEE_SIZE_ENUM_TO_ID_MAP = dict((v, k) for (k, v) in _TEE_SIZE_ID_TO_ENUM_LINK)


_GENDER_ID_TO_ENUM_LINK = (
    (_GENDER_FEMALE_ID, profile_model.Gender.FEMALE),
    (_GENDER_MALE_ID, profile_model.Gender.MALE),
    (_GENDER_OTHER_ID, profile_model.Gender.OTHER),
    (_GENDER_NOT_ANSWERED_ID, None)
    )
_GENDER_ID_TO_ENUM_MAP = dict(_GENDER_ID_TO_ENUM_LINK)
_GENDER_ENUM_TO_ID_MAP = dict((v, k) for (k, v) in _GENDER_ID_TO_ENUM_LINK)


_DEGREE_ID_TO_ENUM_LINK = (
    (_DEGREE_UNDERGRADUATE_ID, education_model.Degree.UNDERGRADUATE),
    (_DEGREE_MASTERS_ID, education_model.Degree.MASTERS),
    (_DEGREE_PHD_ID, education_model.Degree.PHD)
    )
_DEGREE_ID_TO_ENUM_MAP = dict(_DEGREE_ID_TO_ENUM_LINK)
_DEGREE_ENUM_TO_ID_MAP = dict((v, k) for (k, v) in _DEGREE_ID_TO_ENUM_LINK)

def _adaptProfilePropertiesForDatastore(form_data):
  """Adopts properties corresponding to profile's properties, which
  have been submitted in a form, to the format that is compliant with
  profile_model.Profile model.

  Args:
    form_data: A dict containing data submitted in a form.

  Returns:
    A dict mapping properties of profile model to values based on
    data submitted in a form.
  """
  properties = {
      profile_model.Profile.first_name._name: form_data.get('first_name'),
      profile_model.Profile.last_name._name: form_data.get('last_name'),
      profile_model.Profile.photo_url._name: form_data.get('photo_url'),
      profile_model.Profile.birth_date._name: form_data.get('birth_date'),
      }

  if 'tee_style' in form_data:
    properties[profile_model.Profile.tee_style._name] = (
        _TEE_STYLE_ID_TO_ENUM_MAP[form_data['tee_style']])

  if 'tee_size' in form_data:
    properties[profile_model.Profile.tee_size._name] = (
        _TEE_SIZE_ID_TO_ENUM_MAP[form_data['tee_size']])

  if 'gender' in form_data:
    properties[profile_model.Profile.gender._name] = (
        _GENDER_ID_TO_ENUM_MAP[form_data['gender']])

  if 'terms_of_service' in form_data:
    properties[profile_model.Profile.accepted_tos._name] = (
        [form_data.get('terms_of_service')])

  return properties


def _adaptStudentDataPropertiesForDatastore(form_data):
  """Adopts properties corresponding to profile's student data properties, which
  have been submitted in a form, to the format that is compliant with
  profile_model.StudentData model.

  Args:
    form_data: A dict containing data submitted in a form.

  Returns:
    A dict mapping properties of student data model to values based on
    data submitted in a form.
  """
  school_id = form_data.get('school_name')
  school_country = form_data.get('school_country')
  degree = _DEGREE_ID_TO_ENUM_MAP[form_data.get('degree')]
  # TODO(daniel): support it
  expected_graduation = None
  major = form_data.get('major')

  result = education_logic.createPostSecondaryEducation(
      school_id, school_country, expected_graduation, major, degree)
  if not result:
    raise exception.BadRequest(message=result.extra)
  else:
    return {profile_model.StudentData.education._name: result.extra}


def _adoptContactPropertiesForForm(contact_properties):
  """Adopts properties of a contact entity, which are persisted in datastore,
  to representation which may be passed to populate _UserProfileForm.

  Args:
    contact_properties: A dict containing contact properties as persisted
      in datastore.

  Returns:
    A dict mapping properties of contact model to values which can be
    populated to a user profile form.
  """
  return {
      key: contact_properties.get(key) for key in _CONTACT_PROPERTIES_FORM_KEYS}


def _adoptResidentialAddressPropertiesForForm(address_properties):
  """Adopts properties of a address entity, which are persisted in datastore
  as residential address, to representation which may be passed to
  populate _UserProfileForm.

  Args:
    address_properties: A dict containing residential address properties
      as persisted in datastore.

  Returns:
    A dict mapping properties of address model to values which can be
    populated to a user profile form.
  """
  return {
      'residential_street': address_properties['street'],
      'residential_city': address_properties['city'],
      'residential_country': address_properties['country'],
      'residential_postal_code': address_properties['postal_code'],
      'residential_province': address_properties['province'],
      }


def _adoptShippingAddressPropertiesForForm(address_properties):
  """Adopts properties of an address entity, which are persisted in datastore
  as shipping address, to representation which may be passed to
  populate _UserProfileForm.

  Args:
    address_properties: A dict containing shipping address properties
      as persisted in datastore or None, if no shipping address is specified.

  Returns:
    A dict mapping properties of address model to values which can be
    populated to a user profile form.
  """
  address_properties = address_properties or {}
  return {
      'is_shipping_address_different': bool(address_properties),
      'shipping_name': address_properties.get('name'),
      'shipping_street': address_properties.get('street'),
      'shipping_city': address_properties.get('city'),
      'shipping_country': address_properties.get('country'),
      'shipping_postal_code': address_properties.get('postal_code'),
      'shipping_province': address_properties.get('province'),
      }


def _adoptStudentDataPropertiesForForm(student_data_properties):
  """Adopts properties of a student data entity, which are persisted in
  datastore, to representation which may be passed to populate _UserProfileForm.

  Args:
    student_data_properties: A dict containing student data properties as
      persisted in datastore.

  Returns:
    A dict mapping properties of student profile model to values which can be
    populated to a user profile form.
  """
  student_data_properties = student_data_properties or {}

  education = student_data_properties[profile_model.StudentData.education._name]
  return {
      'school_country': education.get(
          education_model.Education.school_country._name),
      'school_name': education.get(education_model.Education.school_id._name),
      'major': education.get(
          education_model.PostSecondaryEducation.major._name),
      'degree': _DEGREE_ENUM_TO_ID_MAP[
          education.get(education_model.PostSecondaryEducation.degree._name)]
      }


def _adoptProfilePropertiesForForm(profile_properties):
  """Adopts properties of a profile entity, which are persisted in datastore,
  to representation which may be passed to populate _UserProfileForm.

  Args:
    profile_properties: A dict containing profile properties as
      persisted in datastore.

  Returns:
    A dict mapping properties of profile model to values which can be
    populated to a user profile form.
  """
  form_data = {
      key: profile_properties.get(key) for key in
      ['first_name', 'last_name', 'photo_url', 'birth_date']}

  # residential address information
  form_data.update(
      _adoptResidentialAddressPropertiesForForm(
          profile_properties[profile_model.Profile.residential_address._name]))

  # shipping address information
  form_data.update(
      _adoptShippingAddressPropertiesForForm(
          profile_properties[profile_model.Profile.shipping_address._name]))

  # contact information
  if profile_model.Profile.contact._name in profile_properties:
    form_data.update(_adoptContactPropertiesForForm(
        profile_properties[profile_model.Profile.contact._name]))

  form_data['tee_style'] = (
      _TEE_STYLE_ENUM_TO_ID_MAP[profile_properties['tee_style']])
  form_data['tee_size'] = (
      _TEE_SIZE_ENUM_TO_ID_MAP[profile_properties['tee_size']])
  form_data['gender'] = _GENDER_ENUM_TO_ID_MAP[profile_properties['gender']]

  return form_data


def _profileFormToRegisterProfile(
    register_user, terms_of_service, has_student_data=None, **kwargs):
  """Returns a Django form to register a new profile.

  Args:
    register_user: If set to True, the constructed form will also be used to
      create a new User entity along with a new Profile entity.
    terms_of_service: Document with Terms of Service that has to be accepted by
      the user.
    has_student_data: If specified to True, the form will contain fields
      related to student data for the profile.

  Returns:
    _UserProfileForm adjusted to create a new profile.
  """
  form = _UserProfileForm(
      terms_of_service=terms_of_service,
      has_student_data=has_student_data, **kwargs)

  if not register_user:
    del form.fields['user_id']

  return form


# TODO(daniel): should this function also handle student profiles?
def _profileFormToEditProfile(**kwargs):
  form = _UserProfileForm(**kwargs)

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
    return 'summerofcode/profile/profile_edit.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'profile/register/org_member/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.PROFILE_REGISTER_AS_ORG_MEMBER)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _profileFormToRegisterProfile(
        data.ndb_user is None, data.program.org_admin_agreement, data=data.POST)

    return {
        'page_name': PROFILE_ORG_MEMBER_CREATE_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _profileFormToRegisterProfile(
        data.ndb_user is None, data.program.org_admin_agreement, data=data.POST)

    # TODO(daniel): eliminate passing self object.
    handler = CreateProfileFormHandler(self, form)
    return handler.handle(data, check, mutator)


class ProfileRegisterAsStudentPage(base.GSoCRequestHandler):
  """View to create student profile.

  It will be used by prospective students. Users with such profiles will be
  eligible to submit proposals to organizations and work on projects
  upon acceptance.
  """

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'summerofcode/profile/profile_edit.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'profile/register/student/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.PROFILE_REGISTER_AS_STUDENT)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _profileFormToRegisterProfile(
        data.ndb_user is None, data.program.student_agreement,
        has_student_data=True, data=data.POST)

    return {
        'page_name': PROFILE_STUDENT_CREATE_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _profileFormToRegisterProfile(
        data.ndb_user is None, data.program.org_admin_agreement,
        has_student_data=True, data=data.POST)

    # TODO(daniel): eliminate passing self object.
    handler = CreateProfileFormHandler(self, form)
    return handler.handle(data, check, mutator)


class CreateProfileFormHandler(form_handler.FormHandler):
  """Form handler implementation to handle incoming data that is supposed to
  create new profiles.
  """

  def __init__(self, view, form):
    """Initializes new instance of form handler.

    Args:
      view: Callback to implementation of base.RequestHandler
        that creates this object.
      form: Instance of _UserProfileForm whose data is to be handled.
    """
    super(CreateProfileFormHandler, self).__init__(view)
    self.form = form

  def handle(self, data, check, mutator):
    """Creates and persists a new profile based on the data that was sent
    in the current request and supplied to the form.

    See form_handler.FormHandler.handle for specification.
    """
    if not self.form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self._view.get(data, check, mutator)
    else:
      profile_properties = _getProfileEntityPropertiesFromForm(self.form)

      user = data.ndb_user
      if not user:
        # try to make sure that no user entity exists for the current account.
        # it should be guaranteed by the condition above evaluating to None,
        # but there is a slim chance that an entity has been created in
        # the meantime.
        user = user_logic.getByCurrentAccount()

      username = self.form.getUserProperties()['user_id'] if not user else None

      createProfileTxn(
          data.program.key(), profile_properties, username=username, user=user,
          models=data.models)

      return http.HttpResponseRedirect(
          links.LINKER.program(data.program, urls.UrlNames.PROFILE_EDIT))


class ProfileEditPage(base.GSoCRequestHandler):
  """View to edit user profiles."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'summerofcode/profile/profile_edit.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'profile/edit/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.PROFILE_EDIT)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form_data = _adoptProfilePropertiesForForm(data.ndb_profile.to_dict())
    form = _profileFormToEditProfile(data=data.POST or form_data)

    return {
        'page_name': PROFILE_EDIT_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _profileFormToEditProfile(data=data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      profile_properties = _getProfileEntityPropertiesFromForm(form)
      editProfileTxn(data.ndb_profile.key, profile_properties)

      return http.HttpResponseRedirect(
          links.LINKER.program(data.program, urls.UrlNames.PROFILE_EDIT))


def _getProfileEntityPropertiesFromForm(form):
  """Extracts properties for a profile entity from the specified form.

  Args:
    form: Instance of _UserProfileForm.

  Returns:
    A dict with complete set of properties of profile entity.
  """
  profile_properties = _adaptProfilePropertiesForDatastore(
      form.getProfileProperties())

  address_properties = form.getResidentialAddressProperties()
  result = address_logic.createAddress(
      address_properties['residential_street'],
      address_properties['residential_city'],
      address_properties['residential_country'],
      address_properties['residential_postal_code'],
      province=address_properties.get('residential_province')
      )
  if not result:
    raise exception.BadRequest(message=result.extra)
  else:
    profile_properties['residential_address'] = result.extra

  address_properties = form.getShippingAddressProperties()
  if address_properties:
    result = address_logic.createAddress(
        address_properties['shipping_street'],
        address_properties['shipping_city'],
        address_properties['shipping_country'],
        address_properties['shipping_postal_code'],
        province=address_properties.get('shipping_province'),
        name=address_properties.get('shipping_name'))
    if not result:
      raise exception.BadRequest(message=result.extra)
    else:
      profile_properties['shipping_address'] = result.extra
  else:
    profile_properties['shipping_address'] = None

  contact_properties = form.getContactProperties()
  result = contact_logic.createContact(**contact_properties)
  if not result:
    raise exception.BadRequest(message=result.extra)
  else:
    profile_properties['contact'] = result.extra

  student_data_properties = form.getStudentDataProperties()
  if student_data_properties:
    profile_properties['student_data'] = profile_logic.createStudentData(
        _adaptStudentDataPropertiesForDatastore(student_data_properties))

  return profile_properties


@ndb.transactional
def createProfileTxn(
    program_key, profile_properties, username=None, user=None,
    models=types.MELANGE_MODELS):
  """Creates a new user profile based on the specified properties.

  Args:
    program_key: Program key.
    profile_properties: A dict mapping profile properties to their values.
    username: Username for a new User entity that will be created along with
      the new Profile. May only be passed if user argument is omitted.
    user: User entity for the profile. May only be passed if username argument
      is omitted.
    models: instance of types.Models that represent appropriate models.
  """
  if username and user:
    raise ValueError('Username and user arguments cannot be set together.')
  elif not (username or user):
    raise ValueError('Exactly one of username or user argument must be set.')

  if username:
    result = user_logic.createUser(username)
    if not result:
      raise exception.BadRequest(message=result.extra)
    else:
      user = result.extra

  result = profile_logic.createProfile(
      user.key, program_key, profile_properties, models=models)
  if not result:
    raise exception.BadRequest(message=result.extra)
  else:
    return result.extra


@ndb.transactional
def editProfileTxn(profile_key, profile_properties):
  """Edits an existing profile based on the specified properties.

  Args:
    profile_key: Profile key of an existing profile to edit.
    profile_properties: A dict mapping profile properties to their values.
  """
  result = profile_logic.editProfile(profile_key, profile_properties)
  if not result:
    raise exception.BadRequest(message=result.extra)
  else:
    return result.extra
