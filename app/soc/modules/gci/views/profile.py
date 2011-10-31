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

"""Module for the GCI profile page.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from django import forms as django_forms
from django.core.urlresolvers import reverse
from django.forms import fields
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic import dicts
from soc.models.user import User
from soc.views import forms
from soc.views import profile
from soc.views.helper import url_patterns

from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler


class GCIUserForm(gci_forms.GCIModelForm):
  """Django form for User model in GCI program.
  """
  link_id = gci_forms.CharField(label='Username')
  class Meta:
    model = User
    css_prefix = 'user'
    fields = ['link_id']

  link_id = gci_forms.CharField(label='Username')
  clean_link_id = cleaning.clean_user_not_exist('link_id')


PROFILE_EXCLUDE = profile.PROFILE_EXCLUDE + [
    'automatic_task_subscription', 'notify_comments'
    'agreed_to_tos', 'longtitude', 'latitude', 'publish_location']


class GCIProfileForm(profile.ProfileForm):
  """Django form to edit GCI profile page.
  """

  # Most of these countries are not even in the countries model, but
  # we still list them anyway.
  GCI_UNALLOWED_COUNTRIES = ['Cuba', 'Iran', 'Syria', 'North Korea', 'Sudan',
                             'Myanmar (Burma)', 'Brazil', 'Saudi Arabia',
                             'Italy']

  NOT_OPEN_TO_COUNTRY_MSG = ugettext(
      'This contest is not open to residents of this country.')

  NOT_OPEN_TO_QUEBEC_MSG = ugettext(
      'This contest is not open to residents of Quebec.')


  def __init__(self, request_data=None, *args, **kwargs):
    super(GCIProfileForm, self).__init__(
        gci_forms.GCIBoundField, request_data, *args, **kwargs)

  class Meta:
    model = GCIProfile
    css_prefix = 'gci_profile'
    exclude = PROFILE_EXCLUDE
    widgets = forms.choiceWidgets(model,
        ['res_country', 'ship_country',
         'tshirt_style', 'tshirt_size', 'gender'])

  def clean_res_country(self):
    """Validates the country against the list of unallowed countries.
    """
    country = self.cleaned_data.get('res_country')
    if self.request_data.kwargs.get('role') == 'student' or \
        (self.request_data.profile and self.request_data.profile.is_student):
      if country in self.GCI_UNALLOWED_COUNTRIES:
        raise django_forms.ValidationError(self.NOT_OPEN_TO_COUNTRY_MSG)

    return country

  def clean_ship_country(self):
    """Validates the shipping country against the list of unallowed countries.
    """
    country = self.cleaned_data.get('ship_country')
    if self.request_data.kwargs.get('role') == 'student' or \
        (self.request_data.profile and self.request_data.profile.is_student):
      if country in self.GCI_UNALLOWED_COUNTRIES:
        raise django_forms.ValidationError(self.NOT_OPEN_TO_COUNTRY_MSG)

    return country

  def clean(self):
    """Ensures that Canadian students fill in their province and produces errors
    when they are from Quebec.
    """
    if self.request_data.kwargs.get('role') == 'student' or \
        (self.request_data.profile and self.request_data.profile.is_student):
      country = self.cleaned_data.get('res_country')
      state = self.cleaned_data.get('res_state')
      if country == 'Canada':
        if state and state.lower().strip().startswith('q'):
          self._errors['res_state'] = [self.NOT_OPEN_TO_QUEBEC_MSG]

      country = self.cleaned_data.get('ship_country')
      state = self.cleaned_data.get('ship_state')
      if country == 'Canada':
        if state and state.lower().strip().startswith('q'):
          self._errors['ship_state'] = [self.NOT_OPEN_TO_QUEBEC_MSG]

    return super(GCIProfileForm, self).clean()

  def templatePath(self):
    return gci_forms.TEMPLATE_PATH


class CreateGCIProfileForm(GCIProfileForm):
  """Django edit form to create GCI profile page.
  """

  class Meta:
    model = GCIProfileForm.Meta.model
    css_prefix = GCIProfileForm.Meta.css_prefix
    exclude = PROFILE_EXCLUDE
    widgets = GCIProfileForm.Meta.widgets

  def __init__(self, tos_content, request_data=None, *args, **kwargs):
    super(CreateGCIProfileForm, self).__init__(request_data, *args, **kwargs)
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


class NotificationForm(gci_forms.GCIModelForm):
  """Django form for the notifications.
  """

  class Meta:
    model = GCIProfile
    css_prefix = 'gci_profile'
    fields = ['automatic_task_subscription', 'notify_comments']


class GCIStudentInfoForm(gci_forms.GCIModelForm):
  """Django form for the student profile page.
  """

  class Meta:
    model = GCIStudentInfo
    css_prefix = 'student_info'
    exclude = [
        'number_of_tasks_completed', 'parental_form_mail', 'consent_form',
        'consent_form_two', 'student_id_form', 'major', 'degree', 'school',
        'school_type',
    ]
    widgets = forms.choiceWidgets(model,
        ['school_country', 'school_type', 'degree'])

  school_home_page = fields.URLField(required=True)
  clean_school_home_page =  cleaning.clean_url('school_home_page')


class GCIProfilePage(profile.ProfilePage, RequestHandler):
  """View for the GCI participant profile.
  """

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.isProgramVisible()
  
    if 'role' in self.data.kwargs:
      role = self.data.kwargs['role']
      kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
      edit_url = reverse('edit_gci_profile', kwargs=kwargs)
      if role == 'student':
        self.check.canApplyStudent(edit_url)
      else:
        self.check.canApplyNonStudent(role, edit_url)
    else:
      self.check.isProfileActive()

  def templatePath(self):
    return 'v2/modules/gci/profile/base.html'

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
      organization = GCIOrganization.get_by_key_name(key_name)
    else:
      organization = None

    if not organization:
      self.redirect.program()
      self.redirect.to(self._getEditProfileURLName(), validated=True)
      return

    self.redirect.homepage()

    link = 'gci_homepage'
    self.redirect.to(link)

  def _getModulePrefix(self):
    return 'gci'

  def _getEditProfileURLName(self):
    return 'edit_gci_profile'

  def _getCreateProfileURLName(self):
    return 'create_gci_profile'

  def _getEditProfileURLPattern(self):
    return url_patterns.PROGRAM

  def _getCreateProfileURLPattern(self):
    return url_patterns.CREATE_PROFILE

  def _getCreateUserForm(self):
    return GCIUserForm(self.data.POST)

  def _getEditProfileForm(self, check_age):
    return GCIProfileForm(data=self.data.POST or None,
        request_data=self.data, instance=self.data.profile)

  def _getCreateProfileForm(self, check_age):
    tos_content = self._getTOSContent()
    return CreateGCIProfileForm(tos_content, data=self.data.POST or None,
        request_data=self.data)

  def _getNotificationForm(self):
    return NotificationForm

  def _getStudentInfoForm(self):
    return GCIStudentInfoForm(self.data.POST or None, 
        instance=self.data.student_info)

