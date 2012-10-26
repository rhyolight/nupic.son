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

from google.appengine.ext import db

from django.forms import fields
from django.core.urlresolvers import reverse

from soc.logic import cleaning
from soc.logic import dicts
from soc.models.connection import RESPONSE_STATE_ACCEPTED
from soc.models.connection import RESPONSE_STATE_REJECTED
from soc.models.connection import RESPONSE_STATE_UNREPLIED
from soc.models.user import User
from soc.views import forms
from soc.views import profile
from soc.views.helper import url_patterns

from soc.models.universities import UNIVERSITIES

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.models.connection import GSoCConnection
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_names


class StudentNotificationForm(gsoc_forms.GSoCModelForm):
  """Django form for student notification settings.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    fields = ['notify_public_comments']


MENTOR_FIELDS = [
    'notify_request_handled', 'notify_invite_handled',
    'notify_new_invites', 'notify_new_proposals', 'notify_proposal_updates',
    'notify_public_comments', 'notify_private_comments',
]

class AdminNotificationForm(gsoc_forms.GSoCModelForm):
  """Django form for mentor notification settings.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    fields = ['notify_new_requests'] + MENTOR_FIELDS


class MentorNotificationForm(gsoc_forms.GSoCModelForm):
  """Django form for mentor notification settings.
  """

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    fields = MENTOR_FIELDS


class GSoCUserForm(gsoc_forms.GSoCModelForm):
  """Django form for User model in GSoC program.
  """

  class Meta:
    model = User
    css_prefix = 'user'
    fields = ['link_id']

  link_id = gsoc_forms.CharField(label='Username')
  clean_link_id = cleaning.clean_user_not_exist('link_id')


TO_EXCLUDE = [
    # notifications
    'notify_new_proposals', 'notify_proposal_updates',
    'notify_public_comments', 'notify_private_comments',
]

PROFILE_EXCLUDE = profile.PROFILE_EXCLUDE + TO_EXCLUDE

PREFILL_PROFILE_EXCLUDE = profile.PREFILL_PROFILE_EXCLUDE + TO_EXCLUDE


class GSoCProfileForm(profile.ProfileForm):
  """Django form for profile page.
  """

  def __init__(self, request_data=None, *args, **kwargs):
    self.program = request_data.program
    super(GSoCProfileForm, self).__init__(
        gsoc_forms.GSoCBoundField, request_data, *args, **kwargs)

  class Meta:
    model = GSoCProfile
    css_prefix = 'gsoc_profile'
    exclude = PROFILE_EXCLUDE + ['agreed_to_tos']

    _choiceWidgets = forms.choiceWidgets(GSoCProfile,
        ['res_country', 'ship_country',
         'tshirt_style', 'tshirt_size', 'gender'])
    _hiddenWidgets = forms.hiddenWidgets(GSoCProfile,
        ['longitude', 'latitude'])

    widgets = forms.mergeWidgets(_choiceWidgets, _hiddenWidgets)

  def templatePath(self):
    return gsoc_forms.TEMPLATE_PATH


class GSoCStudentProfileForm(GSoCProfileForm):
  """Django form for GSoC Student profile page.
  """

  class Meta(GSoCProfileForm.Meta):
    pass

  clean_birth_date = cleaning.clean_birth_date('birth_date')


class CreateGSoCProfileForm(GSoCProfileForm):
  """Django edit form for profiles.
  """

  class Meta:
    model = GSoCProfileForm.Meta.model
    css_prefix = GSoCProfileForm.Meta.css_prefix
    exclude = PROFILE_EXCLUDE
    widgets = GSoCProfileForm.Meta.widgets

  def __init__(self, tos_content, request_data=None, *args, **kwargs):
    super(CreateGSoCProfileForm, self).__init__(request_data, *args, **kwargs)
    self.tos_content = tos_content

    # do not display the field with ToS, if there is nothing to show
    if not tos_content:
      self.fields.pop('agreed_to_tos')
    else:
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


class CreateGSoCStudentProfileForm(CreateGSoCProfileForm):
  """Django edit form for Create Student profiles.
  """

  class Meta(CreateGSoCProfileForm.Meta):
    pass

  clean_birth_date = cleaning.clean_birth_date('birth_date')


class GSoCStudentInfoForm(gsoc_forms.GSoCModelForm):
  """Django form for the student profile page.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_info'
    exclude = [
        'school', 'school_type', 'number_of_proposals', 'number_of_projects',
        'tax_form', 'enrollment_form', 'project_for_orgs', 'passed_evaluations',
        'failed_evaluations', 'grade', 'program',
    ]
    widgets = forms.choiceWidgets(GSoCStudentInfo,
        ['school_country', 'school_type', 'degree'])

  school_home_page = fields.URLField(required=True)
  clean_school_home_page =  cleaning.clean_url('school_home_page')


class GSoCProfilePage(profile.ProfilePage, RequestHandler):
  """View for the GSoC participant profile.
  """

  def djangoURLPatterns(self):
    return profile.ProfilePage.djangoURLPatterns(self) + [
        url_patterns.url(self._getModulePrefix(),
            r'profile/%s$' % self._getCreateConnectedProfileURLPattern(),
            self, name=self._getCreateConnectedProfileURLName())
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.isProgramVisible()
    self.check.isProgramRunning()

    if 'key' in self.data.kwargs:
      self.mutator.anonymousConnectionFromKwargs()
    else:
      self.data.anonymous_connection = None

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

  def context(self):
    """Context for the profile page.
    """
    context = super(GSoCProfilePage, self).context()

    # GSoC has a special "you are logged in" message on top of the form
    context['form_top_msg'] = LoggedInMsg(self.data, apply_role=True)

    return context

  def templatePath(self):
    return 'v2/modules/gsoc/profile/base.html'

  def jsonContext(self):
    return UNIVERSITIES

  def post(self):
    """Handler for HTTP POST request.
    """

    if not self.validate():
      self.get()
      return

    if self.data.anonymous_connection:
      self._handleAnonymousConnection()

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
      self.redirect.to('edit_gsoc_profile', validated=True, secure=True)
      return

    if self.data.anonymous_connection:
      self.redirect.dashboard()
    else:
      self.redirect.organization(organization)

    extra_get_args = []
    if self.data.student_info:
      link = 'submit_gsoc_proposal'
    else:
      link = url_names.GSOC_USER_CONNECTION
      extra_get_args.append('profile=created')

    user = User.get_by_key_name(self.data.request.POST['public_name'])
    
    self.redirect.connect(user, organization)
    self.redirect.to(link, extra=extra_get_args)

  def _handleAnonymousConnection(self):
    """ Handler for automatically created and accepting a new connection.
    """
    
    @db.transactional(xg=True)
    def activate_new_connection_txn():
      # This should be the profile that was just created.
      user = User.get_by_key_name(self.data.request.POST['public_name'])
      profile = GSoCProfile.all().ancestor(user.key()).get()
      # Create the new connection based on the values of the placeholder.
      connection = GSoCConnection(parent=user.key(), 
          organization=self.data.anonymous_connection.parent(),
          profile=profile)
      # Set the apropriate fields to automatically accept the connection.
      connection.role = self.data.anonymous_connection.role
      connection.org_state = connection.user_state = RESPONSE_STATE_ACCEPTED
      connection.put()
      # The user and org should "agree" on a role; promote the user.
      profile.is_mentor = True
      profile.mentor_for.append(connection.organization.key())
      profile.mentor_for = list(set(profile.mentor_for))
      if connection.user_org_admin:  
        profile.is_org_admin = True
        profile.org_admin_for.append(connection.organization.key())
        profile.org_admin_for = list(set(profile.org_admin_for))
      profile.put()
      # We no longer need the placeholder.
      self.data.anonymous_connection.delete()

    activate_new_connection_txn()

  def _getModulePrefix(self):
    return 'gsoc'

  def _getEditProfileURLName(self):
    return 'edit_gsoc_profile'

  def _getCreateProfileURLName(self):
    return 'create_gsoc_profile'

  def _getCreateConnectedProfileURLName(self):
    return url_names.GSOC_ANONYMOUS_CONNECTION

  def _getEditProfileURLPattern(self):
    return url_patterns.PROGRAM

  def _getCreateProfileURLPattern(self):
    return url_patterns.CREATE_PROFILE

  def _getCreateConnectedProfileURLPattern(self):
    return url_patterns.ANONYMOUS_CONNECTION

  def _getCreateUserForm(self):
    return GSoCUserForm(self.data.POST or None)

  def _getEditProfileForm(self, check_age):
    if check_age:
      return GSoCStudentProfileForm(data=self.data.POST or None,
        instance=self.data.profile, request_data=self.data)
    else:
      return GSoCProfileForm(data=self.data.POST or None,
        instance=self.data.profile, request_data=self.data)

  def _getCreateProfileForm(self, check_age, save=False, prefill_data=False):
    tos_content = self._getTOSContent()

    if prefill_data:
      prefilled_data = self.prefilledProfileData()
    else:
      prefilled_data = None

    if check_age:
      form = CreateGSoCStudentProfileForm(tos_content, request_data=self.data,
        data=self.data.POST or prefilled_data)
    else:
      form = CreateGSoCProfileForm(tos_content, request_data=self.data,
        data=self.data.POST or prefilled_data)

    return form

  def _getNotificationForm(self):
    if self.data.student_info or self.data.kwargs.get('role') == 'student':
      return StudentNotificationForm

    if self.data.is_org_admin or self.data.kwargs.get('role') == 'org_admin':
      return AdminNotificationForm

    return MentorNotificationForm

  def _getStudentInfoForm(self):
    return GSoCStudentInfoForm(self.data.POST or None, 
        instance=self.data.student_info)

  def _getProfileForCurrentUser(self):
    query = profile_logic.queryProfilesForUser(self.data.user)
    profiles = query.fetch(1000)

    return profiles[-1] if profiles else None

  def _getFieldsToExcludeInPrefill(self):
    return PREFILL_PROFILE_EXCLUDE