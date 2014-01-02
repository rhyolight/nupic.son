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
from melange.logic import profile as profile_logic
from melange.logic import user as user_logic
from melange.models import profile as profile_model
from melange.request import access
from melange.request import exception
from melange.request import links
from melange.utils import countries

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

PROFILE_EDIT_PAGE_NAME = translation.ugettext(
    'Edit profile')

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
    'ZIP/Postal code information.')

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

TERMS_OF_SERVICE_LABEL = translation.ugettext(
    'I have read and agree to the terms of service')

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

_USER_PROPERTIES_FORM_KEYS = ['user_id']

_PROFILE_PROPERTIES_FORM_KEYS = [
    'public_name', 'photo_url', 'first_name', 'last_name', 'birth_date',
    'tee_style', 'tee_size', 'gender', 'terms_of_service']

_CONTACT_PROPERTIES_FORM_KEYS = ['web_page', 'blog', 'email', 'phone']

_RESIDENTIAL_ADDRESS_PROPERTIES_FORM_KEYS = [
    'residential_street', 'residential_city', 'residential_province',
    'residential_country', 'residential_postal_code']


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

  Meta = object

  def __init__(self, terms_of_service=None, **kwargs):
    """Initializes a new form.

    Args:
      terms_of_service: Document with Terms of Service that has to be accepted
        by the user.
    """
    super(_UserProfileForm, self).__init__(**kwargs)
    self.terms_of_service = terms_of_service

    # remove terms of service field if no document is defined
    if not self.terms_of_service:
      del self.fields['terms_of_service']
    else:
      self.fields['terms_of_service'].widget = soc_forms.TOSWidget(
          self.terms_of_service.content)

  def clean_user_id(self):
    """Cleans user_id field.

    Returns:
      Cleaned value for user_id field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanUserId(self.cleaned_data['user_id'])

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


def _profileFormToRegisterAsOrgMember(
    register_user, terms_of_service, **kwargs):
  """Returns a Django form to register a new profile for organization members.

  Args:
    register_user: If set to True, the constructed form will also be used to
      create a new User entity along with a new Profile entity.
    terms_of_service: Document with Terms of Service that has to be accepted by
      the user.

  Returns:
    _UserProfileForm adjusted to create a new profile for organization members.
  """
  form = _UserProfileForm(terms_of_service=terms_of_service, **kwargs)

  if not register_user:
    del form.fields['user_id']

  return form


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
    return 'modules/gsoc/form_base.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'profile/register/org_member/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.PROFILE_REGISTER_AS_ORG_MEMBER)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _profileFormToRegisterAsOrgMember(
        data.ndb_user is None, data.program.org_admin_agreement, data=data.POST)

    return {
        'page_name': PROFILE_ORG_MEMBER_CREATE_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _profileFormToRegisterAsOrgMember(
        data.ndb_user is None, data.program.org_admin_agreement, data=data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      profile_properties = _getProfileEntityPropertiesFromForm(form)

      user = data.ndb_user
      if not user:
        # try to make sure that no user entity exists for the current account.
        # it should be guaranteed by the condition above evaluating to None,
        # but there is a slim chance that an entity has been created in
        # the meantime.
        user = user_logic.getByCurrentAccount()

      username = form.getUserProperties()['user_id'] if not user else None

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
    return 'modules/gsoc/form_base.html'

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

  contact_properties = form.getContactProperties()
  result = contact_logic.createContact(**contact_properties)
  if not result:
    raise exception.BadRequest(message=result.extra)
  else:
    profile_properties['contact'] = result.extra

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
