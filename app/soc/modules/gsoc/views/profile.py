#!/usr/bin/env python2.5
#
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

"""Module for the GSoC profile page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from google.appengine.api import users
from google.appengine.ext import db

from django.forms import fields
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url

from soc.logic import cleaning
from soc.logic import dicts
from soc.views import forms

from soc.models.user import User

from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class EmptyForm(forms.ModelForm):
  """Empty form that is always valid.
  """

  def is_valid(self):
    return True


class UserForm(forms.ModelForm):
  """Django form for the user profile.
  """

  class Meta:
    model = User
    css_prefix = 'user'
    fields = ['link_id']

  clean_link_id = cleaning.clean_user_not_exist('link_id')


class StudentNotificationForm(forms.ModelForm):
  """Django form for student notification settings.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    fields = ['notify_public_comments']


MENTOR_FIELDS = [
    'notify_rejection', 'notify_new_invites',
    'notify_new_proposals', 'notify_proposal_updates',
    'notify_public_comments', 'notify_private_comments',
]

class AdminNotificationForm(forms.ModelForm):
  """Django form for mentor notification settings.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    fields = ['notify_new_requests'] + MENTOR_FIELDS


class MentorNotificationForm(forms.ModelForm):
  """Django form for mentor notification settings.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    fields = MENTOR_FIELDS


PROFILE_EXCLUDE = [
    'link_id', 'user', 'scope', 'scope_path', 'status',
    'agreed_to_tos_on', 'name_on_documents',
    # notifications
    'notify_new_requests', 'notify_new_invites', 'notify_rejection',
    'notify_new_proposals', 'notify_proposal_updates',
    'notify_public_comments', 'notify_private_comments',
    # role data
    'student_info', 'mentor_for', 'org_admin_for',
    'is_student', 'is_mentor', 'is_org_admin',
]


class ProfileForm(forms.ModelForm):
  """Django form for profile page.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    exclude = PROFILE_EXCLUDE + ['agreed_to_tos']
    widgets = forms.choiceWidgets(GSoCProfile,
        ['res_country', 'ship_country',
         'tshirt_style', 'tshirt_size', 'gender'])

  def __init__(self, *args, **kwargs):
    super(ProfileForm, self).__init__(*args, **kwargs)
    self.fields['given_name'].group = "2. Contact Info (Private)"
    self.fields['surname'].group = "2. Contact Info (Private)"

  public_name = fields.CharField(required=True)

  clean_given_name = cleaning.clean_valid_shipping_chars('given_name')
  clean_surname = cleaning.clean_valid_shipping_chars('surname')
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
    if country == 'United States' and (not state or len(state) != 2):
      self._errors['res_state'] = ["Please use a 2-letter state name"]

    country = self.cleaned_data.get('ship_country')
    state = self.cleaned_data.get('ship_state')
    if country == 'United States' and (not state or len(state) != 2):
      self._errors['ship_state'] = ["Please use a 2-letter state name"]
    return self.cleaned_data


class CreateProfileForm(ProfileForm):
  """Django edit form for profiles.
  """

  class Meta:
    model = ProfileForm.Meta.model
    css_prefix = ProfileForm.Meta.css_prefix
    exclude = PROFILE_EXCLUDE
    widgets = ProfileForm.Meta.widgets

  def __init__(self, tos_content, *args, **kwargs):
    super(CreateProfileForm, self).__init__(*args, **kwargs)
    self.tos_content = tos_content
    self.fields['agreed_to_tos'].widget = forms.TOSWidget(tos_content)

  def clean_agreed_to_tos(self):
    value = self.cleaned_data['agreed_to_tos']
    # no tos set, no need to clean it
    if not self.tos_content:
      return value

    if not value:
      self._errors['agreed_to_tos'] = [
          "You cannot register without agreeing to the Terms of Service"]

    return value


class StudentInfoForm(forms.ModelForm):
  """Django form for the student profile page.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_info'
    exclude = ['school', 'school_type', 'number_of_proposals']
    widgets = forms.choiceWidgets(GSoCStudentInfo,
        ['school_country', 'school_type', 'degree'])

  school_home_page = fields.URLField(required=True)
  clean_school_home_page =  cleaning.clean_url('school_home_page')


class ProfilePage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/profile/%s$' % url_patterns.PROGRAM,
         self, name='edit_gsoc_profile'),
        url(r'^gsoc/profile/%s$' % url_patterns.PROFILE,
         self, name='create_gsoc_profile'),
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.isProgramActive()

    if 'role' in self.data.kwargs:
      role = self.data.kwargs['role']
      kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
      edit_url = reverse('edit_gsoc_profile', kwargs=kwargs)
      if role == 'student':
        self.check.canApplyStudent(edit_url)
      else:
        self.check.canApplyNonStudent(role, edit_url)
    else:
      self.check.isProfileActive()

  def templatePath(self):
    return 'v2/modules/gsoc/profile/base.html'

  def _getTOSContent(self):
    """Convenience method to obtain the relevant Terms of Service content
    for the role in the program.
    """
    tos_content = None
    role = self.data.kwargs.get('role')

    program = self.data.program
    if role == 'student' and program.student_agreement:
      tos_content = program.student_agreement.content
    elif role == 'mentor' and program.mentor_agreement:
      tos_content = program.mentor_agreement.content
    elif role == 'org_admin' and program.org_admin_agreement:
      tos_content = program.org_admin_agreement.content

    return tos_content

  def context(self):
    role = self.data.kwargs.get('role')
    if self.data.student_info or role == 'student':
      student_info_form = StudentInfoForm(self.data.POST or None,
          instance=self.data.student_info)
    else:
      student_info_form = EmptyForm()

    if not role:
      page_name = 'Edit your Profile'
    elif role == 'student':
      page_name = 'Register as a Student'
    elif role == 'mentor':
      page_name = 'Register as a Mentor'
    elif role == 'org_admin':
      page_name = 'Register as Org Admin'

    tos_content = self._getTOSContent()

    form = EmptyForm if self.data.user else UserForm
    user_form = form(self.data.POST or None, instance=self.data.user)
    if self.data.profile:
      self.data.profile._fix_name()
      profile_form = ProfileForm(self.data.POST or None,
                                 instance=self.data.profile)
    else:
      profile_form = CreateProfileForm(tos_content, self.data.POST or None)
    error = user_form.errors or profile_form.errors or student_info_form.errors

    form = self.notificationForm()
    notification_form = form(self.data.POST or None,
                             instance=self.data.profile)

    forms = [user_form, profile_form, notification_form, student_info_form]

    context = {
        'page_name': page_name,
        'form_top_msg': LoggedInMsg(self.data, apply_role=True),
        'forms': forms,
        'error': error,
    }

    return context

  def validateUser(self, dirty):
    if self.data.user:
      user_form = EmptyForm()
    else:
      user_form = UserForm(self.data.POST)

    if not user_form.is_valid():
      return user_form

    if self.data.user:
      return user_form

    key_name = user_form.cleaned_data['link_id']
    account = users.get_current_user()
    user_form.cleaned_data['account'] = account
    user_form.cleaned_data['user_id'] = account.user_id()
    self.data.user = user_form.create(commit=False, key_name=key_name)
    dirty.append(self.data.user)
    return user_form

  def validateProfile(self, dirty):
    if self.data.profile:
      profile_form = ProfileForm(self.data.POST,
                                 instance=self.data.profile)
    else:
      tos_content = self._getTOSContent()
      profile_form = CreateProfileForm(tos_content, self.data.POST)

    if not profile_form.is_valid():
      return profile_form, None

    key_name = '%s/%s' % (self.data.program.key().name(),
                          self.data.user.link_id)
    profile_form.cleaned_data['link_id'] = self.data.user.link_id
    profile_form.cleaned_data['user'] = self.data.user
    profile_form.cleaned_data['scope'] = self.data.program

    if self.data.profile:
      profile = profile_form.save(commit=False)
    else:
      profile = profile_form.create(commit=False, key_name=key_name,
                                    parent=self.data.user)

    dirty.append(profile)

    return profile_form, profile

  def notificationForm(self):
    if self.data.student_info or self.data.kwargs.get('role') == 'student':
      return StudentNotificationForm

    if self.data.org_admin_for:
      return AdminNotificationForm

    return MentorNotificationForm

  def validateNotifications(self, dirty, profile):
    if not profile:
      return EmptyForm(self.data.POST)

    form = self.notificationForm()

    notification_form = form(self.data.POST, instance=profile)

    if not notification_form.is_valid():
      return notification_form

    notification_form.save(commit=False)
    if profile not in dirty:
      dirty.append(profile)

    return notification_form

  def validateStudent(self, dirty, profile):
    if not (self.data.student_info or
        self.data.kwargs.get('role') == 'student'):
      return EmptyForm(self.data.POST)

    student_form = StudentInfoForm(
        self.data.POST, instance=self.data.student_info)

    if not(profile and student_form.is_valid()):
      return student_form

    key_name = profile.key().name()

    if self.data.student_info:
      student_info = student_form.save(commit=False)
    else:
      student_info = student_form.create(
          commit=False, key_name=key_name, parent=profile)
      profile.is_student = True
      profile.student_info = student_info

    dirty.append(student_info)

    return student_form

  def validate(self):
    dirty = []
    user_form = self.validateUser(dirty)
    if not user_form.is_valid():
      return False
    profile_form, profile = self.validateProfile(dirty)

    notification_form = self.validateNotifications(dirty, profile)

    student_form = self.validateStudent(dirty, profile)

    if (user_form.is_valid() and profile_form.is_valid() and
        notification_form.is_valid() and student_form.is_valid()):
      db.run_in_transaction(db.put, dirty)
      return True
    else:
      return False

  def post(self):
    """Handler for HTTP POST request.
    """
    if not self.validate():
      self.get()
      return

    link_id = self.data.GET.get('org')
    if link_id:
      key_name = '%s/%s' % (
          self.data.program.key().name(), link_id
          )
      organization = GSoCOrganization.get_by_key_name(key_name)
    else:
      organization = None

    if not organization:
      self.redirect.program()
      self.redirect.to('edit_gsoc_profile', validated=True)
      return

    self.redirect.organization(organization)

    if self.data.student_info:
      link = 'submit_gsoc_proposal'
    else:
      link = 'gsoc_org_home'

    self.redirect.to(link)
