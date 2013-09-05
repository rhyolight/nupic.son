# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the view for a new conversation form."""

from django import forms as django_forms
from django.utils import translation

from soc.views import template
from soc.views.helper import url_patterns

from soc.models import conversation as conversation_model

from soc.modules.gci.views import base as base_views
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as gciurl_patterns
from soc.modules.gci.views.helper import url_names as gciurl_names

from soc.modules.gci.logic import organization as gciorganization_logic

from soc.modules.gci.models import conversation as gciconversation_model

DEF_ROLE_PROGRAM_ADMINISTRATORS = translation.ugettext('Administrators')
DEF_ROLE_PROGRAM_MENTORS = translation.ugettext('Mentors')
DEF_ROLE_PROGRAM_STUDENTS = translation.ugettext('Students')
DEF_ROLE_ORGANIZATION_ADMINISTRATORS = translation.ugettext(
    'Administrators of this organization')
DEF_ROLE_ORGANIZATION_MENTORS = translation.ugettext(
    'Mentors of this organization')

ROLE_PROGRAM_ADMINISTRATORS = 'ProgramAdministrators'
ROLE_PROGRAM_MENTORS = 'ProgramMentors'
ROLE_PROGRAM_STUDENTS = 'ProgramStudents'
ROLE_ORGANIZATION_ADMINISTRATORS = 'OrganizationAdministrators'
ROLE_ORGANIZATION_MENTORS = 'OrganizationMentors'


def createProgramRoleChoices(data):
  """Creates a list of valid program role choices for user.

  Args:
    data: RequestData for the request.

  Returns:
    A list of tuples of choices, formatted as (value, name).
  """
  choices = set()

  # If user is an org admin let them send a message to all other org admins in
  # the program.
  if data.profile.is_org_admin:
    choices.update([
          (ROLE_PROGRAM_ADMINISTRATORS, DEF_ROLE_PROGRAM_ADMINISTRATORS)
        ])

  # If user is a host for the current program sponsor or a dev, let them send
  # a message to all org admins, mentors, and students in the program.
  if (data.program.sponsor.key() in data.user.host_for
      or data.user.is_developer):
    choices.update([
          (ROLE_PROGRAM_ADMINISTRATORS, DEF_ROLE_PROGRAM_ADMINISTRATORS),
          (ROLE_PROGRAM_MENTORS, DEF_ROLE_PROGRAM_MENTORS),
          (ROLE_PROGRAM_STUDENTS, DEF_ROLE_PROGRAM_STUDENTS),
        ])

  return list(choices)


def createOrganizationRoleChoices(data):
  """Creates a list of valid organization role choices for user.

  Although it currently returns a fixed set of choices, this may change in the
  future as more special role choices are added.

  Args:
    data: RequestData for the request.

  Returns:
    A list of tuples of choices, formatted as (value, name).
  """
  return [
    (ROLE_ORGANIZATION_ADMINISTRATORS, DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
    (ROLE_ORGANIZATION_MENTORS, DEF_ROLE_ORGANIZATION_MENTORS),
  ]


def createOrganizationChoices(data):
  """Creates a list of valid organizations for user.

  This is a list of organizations the user is either mentoring for or
  administrates. If the user is a developer, all organizations are choices.

  Only organizations within the program are returned.

  Args:
    data: RequestData for the request.

  Returns:
    A list of tuples of choices, formatted as (org key name, org name).
  """
  organization_query = gciorganization_logic.queryForProgramAndStatus(
      program=data.program.key(), status='active')

  if (data.program.sponsor.key() not in data.user.host_for and
      not data.user.is_developer):
    organization_query.filter(
        '__key__ IN', 
        list(set(data.profile.org_admin_for + data.profile.mentor_for)))

  return organization_query.fetch(limit=None)


class ConversationCreateForm(gci_forms.GCIModelForm):
  """Django form for creating a conversation."""

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data
    self.POST = request_data.POST or None

    super(ConversationCreateForm, self).__init__(data=self.POST, **kwargs)

    self.recipients_type_choices = [
      (conversation_model.USER, translation.ugettext('Specified users')),
    ]

    self.organizations = createOrganizationChoices(self.request_data)
    self.organization_role_choices = createOrganizationRoleChoices(
        self.request_data)

    if self.organizations and self.organization_role_choices:
      self.fields['organization'] = django_forms.ChoiceField(
          choices=[(org.key(), org.name) for org in self.organizations])
      self.fields['organization_roles'] = django_forms.MultipleChoiceField(
          label=translation.ugettext('Roles'), required=False,
          choices=self.organization_role_choices,
          widget=gci_forms.CheckboxSelectMultiple)
      self.recipients_type_choices.append((
          conversation_model.ORGANIZATION,
          translation.ugettext('Users within an organization')))

    self.program_role_choices = createProgramRoleChoices(self.request_data)
    if self.program_role_choices:
      self.fields['program_roles'] = django_forms.MultipleChoiceField(
          label=translation.ugettext('Roles'), required=False,
          choices=self.program_role_choices,
          widget=gci_forms.CheckboxSelectMultiple)
      self.recipients_type_choices.append((
          conversation_model.PROGRAM,
          translation.ugettext('Users with specified roles')))

    self.fields['recipients_type'] = django_forms.ChoiceField(
        choices=self.recipients_type_choices)

    self.fields['users'] = django_forms.CharField(
        label=translation.ugettext('Users'))

    self.fields['auto_update_users'] = django_forms.BooleanField(
        label=translation.ugettext('Automatically Update Users'), initial=True,
        required=False, help_text=
            gciconversation_model.GCIConversation.auto_update_users.help_text)

    self.fields['subject'] = django_forms.CharField(
        label=translation.ugettext('Subject'))

    self.fields['message_content'] = django_forms.BooleanField(
        widget=django_forms.Textarea)

    # Bind all the fields here to boundclass since we do not iterate
    # over the fields using iterator for this form.
    self.bound_fields = {}
    for name, field in self.fields.items():
      self.bound_fields[name] = gci_forms.GCIBoundField(self, field, name)


class ConversationFormErrorTemplate(template.Template):
  """Conversation form error message template."""

  def __init__(self, data, errors):
    self.data = data
    self.errors = errors

  def context(self):
    """See soc.views.template.Template.context for full specification."""
    return {
      'errors': self.errors,
    }

  def templatePath(self):
    """See soc.views.template.Template.templatePath for full specification."""
    return 'modules/gci/conversation_create/_error_msg.html'


class ConversationFormTemplate(template.Template):
  """Conversation form template."""

  def __init___(self, data):
    self.data = data

  def context(self):
    """See soc.views.template.Template.context for full specification."""
    form = ConversationCreateForm(request_data=self.data)

    return {
      'title': translation.ugettext('New message'),
      'form': form,
      'error': ConversationFormErrorTemplate(self.data, form.errors),
    }

  def templatePath(self):
    """See soc.views.template.Template.templatePath for full specification."""
    return 'modules/gci/conversation_create/_edit.html'


class ConversationCreatePage(base_views.GCIRequestHandler):
  """View for creating a conversation."""

  def templatePath(self):
    """See soc.modules.gci.views.base.GCIRequestHandler.templatePath for full
    specification.
    """
    return 'modules/gci/conversation_create/base.html'

  def djangoURLPatterns(self):
    """See soc.modules.gci.views.base.GCIRequestHandler.djangoURLPatterns for
    full specification.
    """
    return [
        gciurl_patterns.url(r'conversation/create/%s$' % url_patterns.PROGRAM,
            self, name=gciurl_names.GCI_CONVERSATION_CREATE),
    ]

  def checkAccess(self, data, check, mutator):
    """See soc.modules.gci.views.base.GCIRequestHandler.checkAccess for full
    specification.
    """
    check.isProgramVisible()
    check.isProfileActive()
    check.isMessagingEnabled()

  def context(self, data, check, mutator):
    """See soc.modules.gci.views.base.GCIRequestHandler.context for full
    specification.
    """
    return {
        'page_name': translation.ugettext('Create a new conversation'),
        'conversation_form_template': ConversationFormTemplate(data),
    }
