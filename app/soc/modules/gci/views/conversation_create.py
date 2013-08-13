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

import json

from datetime import datetime

from django import forms as django_forms
from django.utils import html
from django.utils import translation
from django.forms import util as forms_util

from google.appengine.ext import db
from google.appengine.ext import ndb

from soc.logic import cleaning

from soc.views import template
from soc.views.helper import url_patterns

from soc.models import conversation as conversation_model
from soc.models import user as user_model

from soc.modules.gci.views import base as base_views
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as gciurl_patterns
from soc.modules.gci.views.helper import url_names as gciurl_names

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.logic import message as gcimessage_logic
from soc.modules.gci.logic import organization as gciorganization_logic
from soc.modules.gci.logic import profile as gciprofile_logic

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

DEF_BLANK_MESSAGE = translation.ugettext('Your message cannot be blank.')
DEF_BLANK_SUBJECT = translation.ugettext('Your subject cannot be blank.')
DEF_NO_USERNAMES_SPECIFIED = translation.ugettext(
    'One or more usernames must be specified.')
DEF_NO_CONVERSATION_SPECIFIED = translation.ugettext(
    'An organization must be specified.')
DEF_NO_ROLES_SPECIFIED = translation.ugettext(
    'At least one role must be specified.')
DEF_INVALID_RECIPIENTS_TYPE = translation.ugettext('Invalid recipients type.')


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

  def __init__(self, data, *args, **kwargs):
    self.request_data = data
    self.POST = data.POST or None

    # POST data must be first arg for django form handler
    super(ConversationCreateForm, self).__init__(self.POST, *args, **kwargs)

    self.recipients_type_choices = [
      (conversation_model.USER, translation.ugettext('Specified users')),
    ]

    self.organizations = createOrganizationChoices(self.request_data)
    self.organization_role_choices = createOrganizationRoleChoices(
        self.request_data)

    if self.organizations and self.organization_role_choices:
      self.fields['organization'] = django_forms.ChoiceField(
          required=False, choices=map(
              lambda org: (org.key(), org.name), self.organizations))
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

  def create(self, commit=True, key_name=None, parent=None):
    """Save this form's cleaned data into a conversation model instance.

    See soc.views.forms.ModelForm.create for original specification.

    Args:
      commit: Optional bool, default True; If True, the conversation model  
              is also saved to the datastore. A message model will only be
              created if the conversation is comitted.
      key_name: The key name of the new model instance; None by default.
      parent: Key (ndb) for the entity that is the new entity's parent; None by
              default.

    Returns:
      The GCIConversation model instance created by this call.
    """

    cleaned_data = self.cleaned_data
    creator = cleaned_data['creator']
    organization = cleaned_data['organization']
    user_keys = set()

    if creator is not None:
      user_keys.add(creator)

    recipients_type = cleaned_data['recipients_type']

    if recipients_type != conversation_model.ORGANIZATION:
      organization = None

    conversation = gciconversation_model.GCIConversation(
        program=cleaned_data['program'], id=key_name, parent=parent,
        subject=cleaned_data['subject'], creator=creator,
        recipients_type=recipients_type, organization=organization,
        include_admins=cleaned_data.get('include_admins', False),
        include_mentors=cleaned_data.get('include_mentors', False),
        include_students=cleaned_data.get('include_students', False),
        auto_update_users=cleaned_data['auto_update_users'])

    if not commit:
      return conversation

    conversation.put()

    if recipients_type == conversation_model.USER:
      user_keys.update(cleaned_data['users'])
      for user_key in user_keys:
        gciconversation_logic.addUserToConversation(conversation.key, user_key)
    else:
      gciconversation_logic.refreshConversationParticipants(conversation.key)

    gciconversation_logic.createMessage(
        conversation=conversation.key, user=creator,
        content=cleaned_data['message_content'])

    return conversation

  def clean_organization(self):
    key_str = self.data.get('organization')
    if key_str:
      return ndb.Key(urlsafe=key_str)
    else:
      return None

  def clean_users(self):
    usernames = json.loads(self.data.get('users'))
    if not usernames or not isinstance(usernames, list):
      return []

    user_keys = []
    invalid_usernames = []
    for username in usernames:
      if username:
        key = db.Key.from_path('User', username)
        if db.get(key):
          user_keys.append(ndb.Key.from_old_key(key))
        else:
          invalid_usernames.append(username)

    if invalid_usernames:
      if len(invalid_usernames) == 1:
        error = (translation.ugettext('%s is not a valid username.') %
            invalid_usernames[0])
      elif len(invalid_usernames) == 2:
        error = (translation.ugettext('%s and %s are not valid usernames.') % 
            (invalid_usernames[0], invalid_usernames[1]))
      else:
        last = invalid_usernames.pop()
        error = (translation.ugettext('%s, and %s are not valid usernames.') % 
            (', '.join(invalid_usernames), last))
      raise django_forms.ValidationError(error)

    return user_keys

  def clean_message_content(self):
    content = cleaning.sanitize_html_string(
        self.data.get('message_content').strip())

    if len(html.strip_tags(content).strip()) == 0:
      raise django_forms.ValidationError(DEF_BLANK_MESSAGE)

    return content

  def clean_subject(self):
    subject = html.strip_tags(self.data.get('subject')).strip()

    if not subject:
      raise django_forms.ValidationError(DEF_BLANK_SUBJECT)

    return subject

  def clean(self):
    super(ConversationCreateForm, self).clean()

    cleaned_data = self.cleaned_data
    recipients_type = cleaned_data.get('recipients_type')

    if recipients_type == conversation_model.USER:
      if not cleaned_data.get('users'):
        errors = self._errors.setdefault('users', forms_util.ErrorList())
        errors.append(DEF_NO_USERNAMES_SPECIFIED)
    elif recipients_type == conversation_model.PROGRAM:
      roles = cleaned_data.get('program_roles')
      if roles:
        if ROLE_PROGRAM_ADMINISTRATORS in roles:
          self.cleaned_data['include_admins'] = True
        if ROLE_PROGRAM_MENTORS in roles:
          self.cleaned_data['include_mentors'] = True
        if ROLE_PROGRAM_STUDENTS in roles:
          self.cleaned_data['include_students'] = True
      else:
        errors = self._errors.setdefault('program_roles',
            forms_util.ErrorList())
        errors.append(DEF_NO_ROLES_SPECIFIED)
    elif recipients_type == conversation_model.ORGANIZATION:
      if not cleaned_data.get('organization'):
        errors = self._errors.setdefault('organization', forms_util.ErrorList())
        errors.append(DEF_NO_CONVERSATION_SPECIFIED)
      roles = cleaned_data.get('organization_roles')
      if roles:
        if ROLE_ORGANIZATION_ADMINISTRATORS in roles:
          self.cleaned_data['include_admins'] = True
        if ROLE_ORGANIZATION_MENTORS in roles:
          self.cleaned_data['include_mentors'] = True
      else:
        errors = self._errors.setdefault('organization_roles',
            forms_util.ErrorList())
        errors.append(DEF_NO_ROLES_SPECIFIED)
    else:
      errors = self._errors.setdefault('recipients_type',
          forms_util.ErrorList())
      errors.append(DEF_INVALID_RECIPIENTS_TYPE)

    cleaned_data['program'] = ndb.Key.from_old_key(
        self.request_data.program.key())

    cleaned_data['creator'] = ndb.Key.from_old_key(
        self.request_data.user.key())

    return cleaned_data


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
    form = ConversationCreateForm(self.data)

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

  def createConversationFromForm(self, data):
    """Creates a new conversation and message based on data inserted in the
    form.

    It also creates ConversationUsers for all the conversation participants.

    Args:
      data: A RequestData for the current request.

    Returns:
      The newly created GCIConversation entity.
    """
    form = ConversationCreateForm(data)

    form.is_valid()

    if not form.is_valid():
      return None

    return form.create()

  def post(self, data, check, mutator):
    """See soc.modules.gci.views.base.GCIRequestHandler.post for full
    specification.
    """
    conversation = self.createConversationFromForm(data)
    if conversation:
      return data.redirect.id(id=conversation.key.integer_id()).to(
          name=gciurl_names.GCI_CONVERSATION)
    else:
      return self.get(data, check, mutator)
