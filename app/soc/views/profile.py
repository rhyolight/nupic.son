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

"""Module for the profile page."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django.forms import fields

from soc.logic import accounts
from soc.logic import cleaning

from soc.models import profile as profile_model

from soc.views import forms
from soc.views.helper import url_patterns


class EmptyForm(forms.ModelForm):
  """Empty form that is always valid.
  """

  def __init__(self, **kwargs):
    super(EmptyForm, self).__init__(forms.BoundField, **kwargs)

  def render(self):
    return ''

  def is_valid(self):
    return True


PROFILE_EXCLUDE = [
    # identification fields
    'link_id', 'user', 'scope', 'status',
    'agreed_to_tos_on', 'name_on_documents', 'program',
    # notification fields
    'notify_new_requests', 'notify_request_handled',
    # role data fields
    'student_info', 'mentor_for', 'org_admin_for',
    'is_student', 'is_mentor', 'is_org_admin',
]

PREFILL_PROFILE_EXCLUDE = PROFILE_EXCLUDE + ['agreed_to_tos']


class ProfileForm(forms.ModelForm):
  """Django form for profile page.
  """

  TWO_LETTER_STATE_REQ = ['United States', 'Canada']

  def __init__(self, bound_field_class, request_data=None, **kwargs):
    super(ProfileForm, self).__init__(bound_field_class, **kwargs)
    self.fields['given_name'].group = "2. Contact Info (Private)"
    self.fields['surname'].group = "2. Contact Info (Private)"
    self.request_data = request_data
    self.program = request_data.program if request_data else None

  public_name = fields.CharField(required=True)

  clean_public_name = cleaning.clean_html_content('public_name')
  clean_name_on_documents = cleaning.clean_html_content('name_on_documents')
  clean_im_network = cleaning.clean_html_content('im_network')
  clean_im_handle = cleaning.clean_html_content('im_handle')
  clean_program_knowledge = cleaning.clean_html_content('program_knowledge')

  clean_given_name = cleaning.clean_valid_shipping_chars('given_name')
  clean_surname = cleaning.clean_valid_shipping_chars('surname')
  clean_email = cleaning.clean_email('email')
  clean_phone = cleaning.clean_phone_number('phone')
  clean_res_street = cleaning.clean_valid_shipping_chars('res_street')
  clean_res_street_extra = cleaning.clean_valid_shipping_chars(
      'res_street_extra')
  clean_res_city = cleaning.clean_valid_shipping_chars('res_city')
  clean_res_state = cleaning.clean_valid_shipping_chars('res_state')
  clean_res_postalcode = cleaning.clean_valid_shipping_chars(
      'res_postalcode')
  clean_ship_name = cleaning.clean_valid_shipping_chars('ship_name')
  clean_ship_street = cleaning.clean_valid_shipping_chars('ship_street')
  clean_ship_street_extra = cleaning.clean_valid_shipping_chars(
      'ship_street_extra')
  clean_ship_city = cleaning.clean_valid_shipping_chars('ship_city')
  clean_ship_state = cleaning.clean_valid_shipping_chars('ship_state')
  clean_ship_postalcode = cleaning.clean_valid_shipping_chars(
      'ship_postalcode')
  clean_home_page = cleaning.clean_url('home_page')
  clean_blog = cleaning.clean_url('blog')
  clean_photo_url = cleaning.clean_url('photo_url')

  def clean(self):
    country = self.cleaned_data.get('res_country')
    state = self.cleaned_data.get('res_state')
    if country in self.TWO_LETTER_STATE_REQ and (not state or len(state) != 2):
      self._errors['res_state'] = ["Please use a 2-letter state/province name"]

    country = self.cleaned_data.get('ship_country')
    state = self.cleaned_data.get('ship_state')
    if country in self.TWO_LETTER_STATE_REQ and (not state or len(state) != 2):
      self._errors['ship_state'] = ["Please use a 2-letter state/province name"]
    return self.cleaned_data


class ProfilePage(object):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url_patterns.url(
            self._getModulePrefix(),
            r'profile/%s$' % self._getEditProfileURLPattern(),
            self, name=self._getEditProfileURLName()),
        url_patterns.url(
            self._getModulePrefix(),
            r'profile/%s$' % self._getCreateProfileURLPattern(),
            self, name=self._getCreateProfileURLName()),
    ]

  def _getTOSContent(self, data):
    """Convenience method to obtain the relevant Terms of Service content
    for the role in the program.
    """
    tos_content = None
    role = data.kwargs.get('role')

    program = data.program
    if role == 'student' and program.student_agreement:
      tos_content = program.student_agreement.content
    elif role == 'mentor' and program.mentor_agreement:
      tos_content = program.mentor_agreement.content
    elif role == 'org_admin' and program.org_admin_agreement:
      tos_content = program.org_admin_agreement.content

    return tos_content

  def isCreateProfileRequest(self, data):
    """Returns True if the current request is supposed to create a new profile.
    Otherwise, the result is false.
    """
    return data.kwargs.get('role') is not None

  def isStudentRequest(self, data):
    """Returns True if the current request refers to a student which means it
    is either Create or Edit Student Profile.
    """
    return data.student_info or data.kwargs.get('role') == 'student'

  def prefilledProfileData(self, data):
    if not data.user:
      return None

    profile = self._getProfileForCurrentUser(data)
    if not profile:
      return None

    properties = {}
    for property_name in profile.properties():
      if property_name in self._getFieldsToExcludeInPrefill():
        continue

      properties[property_name] = getattr(profile, property_name)

    return properties

  def context(self, data, check, mutator):
    """See soc.views.base.RequestHandler.context for specification."""
    role = data.kwargs.get('role')
    if data.student_info or role == 'student':
      student_info_form = self._getStudentInfoForm(data)
      # student's age should be checked
      is_student = True
    else:
      student_info_form = EmptyForm()
      is_student = False

    if not role:
      page_name = 'Edit your Profile'
    elif role == 'student':
      page_name = 'Register as a Student'
    elif role == 'mentor':
      page_name = 'Register as a Mentor'
    elif role == 'org_admin':
      page_name = 'Register as an Org Admin'

    if data.user:
      user_form = EmptyForm(data=data.POST or None, instance=data.user)
    else:
      user_form = self._getCreateUserForm(data)

    if data.profile:
      data.profile._fix_name()
      profile_form = self._getEditProfileForm(data, is_student)
    else:
      profile_form = self._getCreateProfileForm(
          data, is_student, prefill_data=True)

    error = user_form.errors or profile_form.errors or student_info_form.errors

    form = self._getNotificationForm(data)
    notification_form = form(
        data=data.POST or None, instance=data.profile)

    forms = [user_form, profile_form, notification_form, student_info_form]

    context = {
        'page_name': page_name,
        'forms': forms,
        'error': error,
    }

    return context

  def validateUser(self, data, dirty):
    if data.user:
      return EmptyForm(), data.user
    else:
      user_form = self._getCreateUserForm(data)

    if not user_form.is_valid():
      return user_form, None

    key_name = user_form.cleaned_data['link_id']
    account = data.gae_user
    norm_account = accounts.normalizeAccount(account)
    user_form.cleaned_data['account'] = norm_account
    user_form.cleaned_data['user_id'] = account.user_id()

    user = user_form.create(commit=False, key_name=key_name)
    dirty.append(user)

    return user_form, user

  def validateProfile(self, data, dirty, user):
    check_age = data.student_info or data.kwargs.get('role') == 'student'

    if data.profile:
      profile_form = self._getEditProfileForm(data, check_age)
    else:
      profile_form = self._getCreateProfileForm(data, check_age, save=True)

    if not profile_form.is_valid() or not user:
      return profile_form, None

    key_name = '%s/%s' % (data.program.key().name(), user.link_id)

    profile_form.cleaned_data['user'] = user
    profile_form.cleaned_data['link_id'] = user.link_id
    profile_form.cleaned_data['scope'] = data.program
    profile_form.cleaned_data['program'] = data.program

    if data.profile:
      profile = profile_form.save(commit=False)
    else:
      profile = profile_form.create(commit=False, key_name=key_name,
          parent=user)

    dirty.append(profile)

    # synchronize the public name in the profile with the one in user
    user.name = profile_form.cleaned_data['public_name']
    dirty.append(user)

    return profile_form, profile

  def validateNotifications(self, data, dirty, profile):
    if not profile:
      return EmptyForm(data=data.POST)

    form = self._getNotificationForm(data)

    notification_form = form(data=data.POST, instance=profile)

    if not notification_form.is_valid():
      return notification_form

    notification_form.save(commit=False)
    if profile not in dirty:
      dirty.append(profile)

    return notification_form

  def validateStudent(self, data, dirty, profile):
    if not (data.student_info or data.kwargs.get('role') == 'student'):
      return EmptyForm(data=data.POST)

    student_form = self._getStudentInfoForm(data)

    if not profile or not student_form.is_valid():
      return student_form

    key_name = profile.key().name()

    if data.student_info:
      student_info = student_form.save(commit=False)
    else:
      student_info = student_form.create(
          commit=False, key_name=key_name, parent=profile)
      student_info.program = data.program
      profile.is_student = True
      profile.student_info = student_info

    dirty.append(student_info)

    return student_form

  def validate(self, data, entities=None):
    """Validate the user and profile data from the forms.

    Args:
      data: RequestData object with the forms to validate.
      entities: List to which the new profile will be appended.

    Returns:
      True if all forms were valid, False otherwise.
    """
    dirty = []
    user_form, user = self.validateUser(data, dirty)

    if not user_form.is_valid():
      return False

    profile_form, profile = self.validateProfile(data, dirty, user)

    notification_form = self.validateNotifications(data, dirty, profile)

    student_form = self.validateStudent(data, dirty, profile)

    if (user_form.is_valid() and profile_form.is_valid() and
        notification_form.is_valid() and student_form.is_valid()):
      db.run_in_transaction(db.put, dirty)
      # TODO(dcrodman): This is a pretty hacky fix for issue 1785.
      if entities is not None:
        entities.append(profile)
      return True
    else:
      return False

  def _getModulePrefix(self):
    raise NotImplementedError

  def _getEditProfileURLName(self):
    raise NotImplementedError

  def _getCreateProfileURLName(self):
    raise NotImplementedError

  def _getEditProfileURLPattern(self):
    raise NotImplementedError

  def _getCreateProfileURLPattern(self):
    raise NotImplementedError

  def _getEditProfileForm(self, data, check_age):
    raise NotImplementedError

  def _getCreateProfileForm(
      self, data, check_age, save=False, prefill_data=False):
    raise NotImplementedError

  def _getNotificationForm(self, data):
    raise NotImplementedError

  def _getStudentInfoForm(self, data):
    raise NotImplementedError

  def _getProfileForCurrentUser(self, data):
    raise NotImplementedError

  def _getFieldsToExcludeInPrefill(self):
    raise NotImplementedError
