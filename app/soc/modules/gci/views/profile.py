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

"""Module for the GCI profile page."""

from django import forms as django_forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from soc.logic import cleaning
from soc.logic import dicts
from soc.logic.exceptions import RedirectRequest
from soc.models.sponsor import Sponsor
from soc.models.user import User
from soc.views import forms
from soc.views import profile
from soc.views.helper import url_patterns

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models.avatars import AVATARS_BY_COLOR
from soc.modules.gci.models.avatars import COLORS
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names

LINK_ID_HELP_TEXT = ugettext(
    'This is a username that will be displayed on your dashboard URL, but '
    'it is not the public name that will be displayed in correspondence '
    'with mentors, on the tasks pages, etc. [a-z, 0-9 and underscores only]')

PARENTAL_CONSENT_ADVICE = ugettext(
    'Please make sure that you have your parent or guardian\'s permission '
    'to participate in Google Code-in before filling out your profile!')

UPLOAD_FORMS_REMINDER = ugettext(
    'You need to upload your forms <a href="%s">here</a> before '
    'you can claim tasks in the program.')

SCHOOL_NAME_HELP_TEXT = ugettext(
    'Please enter the full name of your school in this field. Please use the '
    'formal name of your school, e.g. Smith Collins High School, instead of '
    'SCHS. Please provide your school name in English so that it will be '
    'easier for the program administrators to match up schools and students '
    'for statistical purposes.')

GCI_PROFILE_EXCLUDE = ['automatic_task_subscription', 'notify_comments',
                       'photo_url']

PROFILE_EXCLUDE = profile.PROFILE_EXCLUDE + GCI_PROFILE_EXCLUDE

PREFILL_PROFILE_EXCLUDE = profile.PREFILL_PROFILE_EXCLUDE + GCI_PROFILE_EXCLUDE

STUDENT_EXCLUDE = PROFILE_EXCLUDE

PREFILL_STUDENT_EXCLUDE = PREFILL_PROFILE_EXCLUDE

SHOW_STUDENT_EXCLUDE = STUDENT_EXCLUDE + [
    'birth_date',
]


class GCIUserForm(gci_forms.GCIModelForm):
  """Django form for User model in GCI program.
  """
  link_id = gci_forms.CharField(label='URL ID')
  class Meta:
    model = User
    css_prefix = 'user'
    fields = ['link_id']

  link_id = gci_forms.CharField(label='URL ID', help_text=LINK_ID_HELP_TEXT)
  clean_link_id = cleaning.clean_user_not_exist('link_id')


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
    self.fields['avatar'].widget = gci_forms.AvatarWidget(
        avatars=AVATARS_BY_COLOR, colors=COLORS)
    self.program = request_data.program

  class Meta:
    model = GCIProfile
    css_prefix = 'gci_profile'
    exclude = PREFILL_PROFILE_EXCLUDE
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


class GCICreateProfileForm(GCIProfileForm):
  """Django edit form to create GCI profile page.
  """

  class Meta:
    model = GCIProfileForm.Meta.model
    css_prefix = GCIProfileForm.Meta.css_prefix
    exclude = PROFILE_EXCLUDE
    widgets = GCIProfileForm.Meta.widgets

  def __init__(self, tos_content, request_data=None, *args, **kwargs):
    super(GCICreateProfileForm, self).__init__(request_data, *args, **kwargs)
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


class GCIStudentProfileForm(GCIProfileForm):
  """Django edit form to create GCI student profile page.
  """

  class Meta:
    model = GCIProfileForm.Meta.model
    css_prefix = GCIProfileForm.Meta.css_prefix
    exclude = PREFILL_STUDENT_EXCLUDE
    widgets = GCIProfileForm.Meta.widgets

  clean_birth_date = cleaning.clean_birth_date('birth_date')


class GCICreateStudentProfileForm(GCICreateProfileForm):
  """Django edit form to edit GCI student profile page.
  """

  class Meta:
    model = GCICreateProfileForm.Meta.model
    css_prefix = GCICreateProfileForm.Meta.css_prefix
    exclude = STUDENT_EXCLUDE
    widgets = GCICreateProfileForm.Meta.widgets

  clean_birth_date = cleaning.clean_birth_date('birth_date')


class GCIShowCreateStudentProfileForm(GCICreateProfileForm):
  """Django edit form to edit GCI student profile page.
  """

  class Meta:
    model = GCICreateProfileForm.Meta.model
    css_prefix = GCICreateProfileForm.Meta.css_prefix
    exclude = SHOW_STUDENT_EXCLUDE
    widgets = GCICreateProfileForm.Meta.widgets


class NotificationForm(gci_forms.GCIModelForm):
  """Django form for the notifications.
  """

  class Meta:
    model = GCIProfile
    css_prefix = 'gci_profile'
    fields = ['automatic_task_subscription']


class GCIStudentInfoForm(gci_forms.GCIModelForm):
  """Django form for the student profile page.
  """

  school_name = forms.CharField(
      max_length=1024, help_text=SCHOOL_NAME_HELP_TEXT)

  class Meta:
    model = GCIStudentInfo
    css_prefix = 'student_info'
    exclude = [
        'number_of_completed_tasks', 'task_closed', 'parental_form_mail',
        'consent_form', 'consent_form_verified', 'consent_form_two',
        'student_id_form', 'major', 'student_id_form_verified', 'degree',
        'school', 'school_type', 'program',
    ]
    widgets = forms.choiceWidgets(
        model, ['school_country', 'school_type', 'degree'])

  clean_school_name = cleaning.clean_html_content('school_name')
  clean_major = cleaning.clean_html_content('major')


class GCIProfilePage(profile.ProfilePage, GCIRequestHandler):
  """View for the GCI participant profile."""

  def checkAccess(self):
    self.check.isProgramVisible()
    self.check.isProgramRunning()

    if 'role' in self.data.kwargs:
      role = self.data.kwargs['role']
      kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
      edit_url = reverse('edit_gci_profile', kwargs=kwargs)
      if role == 'student':
        self.check.canApplyStudent(edit_url)
      else:
        self.check.isLoggedIn()
        self.check.canApplyNonStudent(role, edit_url)
    else:
      self.check.isProfileActive()

  def templatePath(self):
    return 'v2/modules/gci/profile/base.html'

  def context(self):
    context = super(GCIProfilePage, self).context()

    if self.isCreateProfileRequest():
      if self.isStudentRequest():
        context['form_instructions'] = PARENTAL_CONSENT_ADVICE
    else:
      if self.data.is_student and \
          not profile_logic.hasStudentFormsUploaded(self.data.student_info):
        kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
        upload_forms_url = reverse(
            url_names.GCI_STUDENT_FORM_UPLOAD, kwargs=kwargs)

        context['form_instructions'] = UPLOAD_FORMS_REMINDER % upload_forms_url
      context['edit_profile'] = True

    return context

  def post(self):
    """Handler for HTTP POST request.

    Based on the action, the request is dispatched to a specific handler.
    """
    if 'delete_account' in self.data.POST:
      return self.deleteAccountPostAction()
    else: # regular POST request
      return self.editProfilePostAction()

  def deleteAccountPostAction(self):
    """Handler for Delete Account POST action."""
    # TODO(nathaniel): make this .program() call unnecessary.
    self.redirect.program()

    return self.redirect.to('gci_delete_account', secure=True)

  def editProfilePostAction(self):
    """Handler for regular (edit/create profile) POST action."""
    if not self.validate():
      # TODO(nathaniel): problematic self-call.
      return self.get()

    org_id = self.data.GET.get('new_org')

    if org_id:
      create_url = self.linker.program(
          self.data.program, 'create_gci_org_profile')
      raise RedirectRequest(create_url + '?org_id=' + org_id)
    else:
      # TODO(nathaniel): make this .program() call unnecessary.
      self.redirect.program()

      return self.redirect.to(
          self._getEditProfileURLName(), validated=True, secure=True)

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
    return GCIUserForm(self.data.POST or None)

  def _getEditProfileForm(self, is_student):
    if is_student:
      form = GCIStudentProfileForm
    else:
      form = GCIProfileForm
    return form(data=self.data.POST or None,
        request_data=self.data, instance=self.data.profile)

  def _getCreateProfileForm(self, is_student, save=False, prefill_data=False):
    if is_student:
      if save:
        form = GCICreateStudentProfileForm
      else:
        form = GCIShowCreateStudentProfileForm
      if self.data.POST:
        birth_date = self.data.request.COOKIES.get('age_check')
        self.data.POST = self.data.POST.copy()
        self.data.POST['birth_date'] = birth_date
    else:
      form = GCICreateProfileForm

    tos_content = self._getTOSContent()
    return form(tos_content, data=self.data.POST or None,
                      request_data=self.data)

  def _getNotificationForm(self):
    return NotificationForm

  def _getStudentInfoForm(self):
    return GCIStudentInfoForm(self.data.POST or None,
                              instance=self.data.student_info)
