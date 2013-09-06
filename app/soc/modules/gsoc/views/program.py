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

"""Module for the program settings pages."""

import csv
import StringIO

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import forms as django_forms
from django import http
from django.utils import html as html_utils
from django.utils import translation

from melange.logic import universities as universities_logic
from melange.request import access

from soc.logic import links
from soc.logic import mail_dispatcher
from soc.logic.helper import notifications
from soc.models import document
from soc.views import program as soc_program_view
from soc.views.helper import access_checker
from soc.views.helper import url_patterns as soc_url_patterns

from soc.modules.gsoc.models import program
from soc.modules.gsoc.models import timeline as timeline_model
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper import url_patterns


TEST_EMAIL_HELP_TEXT = translation.ugettext(
    'Email address to which test messages must be sent. If provided, a '
    'test email is sent for each of the messages on this page to '
    'the given address.')

TEST_ORG_ID = 'test_org'

TEST_ORG_NAME = 'Test organization name'

TEST_ORG_ENTITY = {
    'name': TEST_ORG_NAME,
    'accepted_student_msg': translation.ugettext(
        "This part of the email will be filled out by the organization on "
        "their organization profile page's accepted student message field."
        "This is just a test stub."),
    'rejected_student_msg': translation.ugettext(
        "This part of the email will be filled out by the organization on "
        "their organization profile page's rejected student message field."
        "This is just a test stub."),
    }

TEST_PROPOSAL_TITLE = translation.ugettext(
    'Proposal title for test')

_UNIVERSITIES_LIST_LABEL = translation.ugettext('List of Universities')

_UNIVERSITIES_LIST_HELP_TEXT = translation.ugettext(
    'Each line should contain comma separated university unique identifier, '
    'name, and country.')

class TimelineForm(forms.GSoCModelForm):
  """Django form to edit timeline settings."""

  class Meta:
    css_prefix = 'timeline_form'
    model = timeline_model.GSoCTimeline
    exclude = ['link_id', 'scope']


class CreateProgramForm(forms.GSoCModelForm):
  """Django form to create the settings for a new program."""

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data
    super(CreateProgramForm, self).__init__(**kwargs)

  class Meta:
    css_prefix = 'create_program_form'
    model = program.GSoCProgram
    exclude = [
        'scope', 'timeline', 'slots_allocation', 'events_page',
        'student_max_age', 'min_slots', 'org_admin_agreement',
        'mentor_agreement', 'student_agreement', 'about_page',
        'connect_with_us_page', 'help_page', 'link_id',
        'sponsor']


class EditProgramForm(forms.GSoCModelForm):
  """Django form to edit the settings of an existing program."""

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data
    super(EditProgramForm, self).__init__(**kwargs)

  class Meta:
    css_prefix = 'edit_program_form'
    model = program.GSoCProgram
    exclude = [
        'link_id', 'scope', 'timeline', 'min_slots',
        'slots_allocation', 'student_max_age', 'program_id',
        'sponsor']


class GSoCProgramMessagesForm(forms.GSoCModelForm):
  """Django form for the program settings."""

  test_email = django_forms.EmailField(
      max_length=254, label='Test email address',
      help_text=TEST_EMAIL_HELP_TEXT, required=False)

  def __init__(self, request_data=None, **kwargs):
    self.request_data = request_data
    super(GSoCProgramMessagesForm, self).__init__(**kwargs)

  class Meta:
    css_prefix = 'program_messages_form'
    model = program.GSoCProgramMessages

  def getSendMailFromTemplateStringTxn(
        self, to, subject, template_string, context):
    """Returns the transaction for sending the email

    Args:
      to: Email address to which the test messages must be sent.
      subject: Subject for the mail.
      template_string: Template string to be used to construct mail body.
      context: Context variables to render the mail body from template string.

    Returns:
      A function object for sending email in the background using task queue.
    """
    sender_name, sender = mail_dispatcher.getDefaultMailSender()

    common_context = {
        'to': to,
        'sender': sender,
        'sender_name': sender_name,
        'program_name': self.request_data.program.name,
        'subject': subject,
        }
    context.update(common_context)
    return mail_dispatcher.getSendMailFromTemplateStringTxn(
          template_string, context, parent=self.request_data.user,
          transactional=True)

  def sendTestEmail(self, message_entity):
    """Send the test emails to the requested address.

    Args:
      messages_entity: Messages entity containing the messages to be emailed.
    """
    assert access_checker.isSet(self.request_data.program)

    test_email_addr = self.cleaned_data.get('test_email', None)
    if not test_email_addr:
      return

    self.request_data.redirect.program()
    apply_url = self.request_data.redirect.urlOf(
        'create_gsoc_org_profile', full=True, secure=True)

    org_app_context = {
      'url': apply_url + '?org_id=' + TEST_ORG_ID,
      'org': TEST_ORG_NAME,
      }

    proposal_context = {
        'proposal_title': TEST_PROPOSAL_TITLE,
        'org_entity': TEST_ORG_ENTITY,
        }

    mail_txns = []

    if message_entity.accepted_orgs_msg:
      mail_txns.append(self.getSendMailFromTemplateStringTxn(
          test_email_addr, notifications.DEF_ACCEPTED_ORG % (org_app_context),
          message_entity.accepted_orgs_msg, org_app_context))

    if message_entity.rejected_orgs_msg:
      mail_txns.append(self.getSendMailFromTemplateStringTxn(
          test_email_addr, notifications.DEF_REJECTED_ORG % (org_app_context),
          message_entity.rejected_orgs_msg, org_app_context))

    if message_entity.accepted_students_msg:
      mail_txns.append(self.getSendMailFromTemplateStringTxn(
          test_email_addr, 'Congratulations!',
          message_entity.accepted_students_msg, proposal_context))

    if message_entity.rejected_students_msg:
      mail_txns.append(self.getSendMailFromTemplateStringTxn(
          test_email_addr,
          'Thank you for applying to %s' % (self.request_data.program.name),
          message_entity.rejected_students_msg, proposal_context))

    def txn():
      for mail_txn in mail_txns:
        mail_txn()

    db.run_in_transaction(txn)

  def create(self, *args, **kwargs):
    """After creating the entity, send the test emails to the requested address.
    """
    entity = super(GSoCProgramMessagesForm, self).create(*args, **kwargs)
    self.sendTestEmail(entity)

  def save(self, *args, **kwargs):
    """After saving the form, send the test emails to the requested address."""
    entity = super(GSoCProgramMessagesForm, self).save(*args, **kwargs)
    self.sendTestEmail(entity)


class GSoCEditProgramPage(base.GSoCRequestHandler):
  """View to edit the program settings."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'program/edit/%s$' % soc_url_patterns.PROGRAM, self,
            name=url_names.GSOC_PROGRAM_EDIT),
    ]

  def jsonContext(self, data, check, mutator):
    q = document.Document.all()
    q.filter('prefix', 'gsoc_program')
    q.filter('scope', data.program.key())

    json_data = [{'key': str(i.key()),
                  'key_name': i.key().name(),
                  'label': i.title}
                  for i in q]

    return {'data': json_data}

  def templatePath(self):
    return 'modules/gsoc/program/base.html'

  def context(self, data, check, mutator):
    program_form = EditProgramForm(
        request_data=data, data=data.POST or None, instance=data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self, data):
    program_form = EditProgramForm(
        request_data=data, data=data.POST, instance=data.program)

    if program_form.is_valid():
      program_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate(data):
      data.redirect.program()
      return data.redirect.to(url_names.GSOC_PROGRAM_EDIT, validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCCreateProgramPage(soc_program_view.CreateProgramPage,
    base.GSoCRequestHandler):
  """View to create a new GSoC program."""

  def djangoURLPatterns(self):
    """See soc.views.base.RequestHandler.djangoURLPatterns
    for specification.
    """
    return [
        url_patterns.url(
            r'program/create/%s$' % soc_url_patterns.SPONSOR, self,
            name=url_names.GSOC_PROGRAM_CREATE),
    ]

  def templatePath(self):
    """See soc.views.base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/program/base.html'

  def _getForm(self, data):
    """See soc.views.program.CreateProgram._getForm for specification."""
    return CreateProgramForm(request_data=data, data=data.POST or None)

  def _getTimelineModel(self):
    """See soc.views.program.CreateProgram._getTimelineModel
    for specification.
    """
    return timeline_model.GSoCTimeline

  def _getUrlNameForRedirect(self):
    """See soc.views.program.CreateProgram._getUrlNameForRedirect
    for specification.
    """
    return url_names.GSOC_PROGRAM_EDIT


class TimelinePage(base.GSoCRequestHandler):
  """View for the participant profile."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'timeline/%s$' % soc_url_patterns.PROGRAM, self,
            name='edit_gsoc_timeline'),
        url_patterns.url(r'timeline/edit/%s$' % soc_url_patterns.PROGRAM, self),
    ]

  def templatePath(self):
    return 'modules/gsoc/timeline/base.html'

  def context(self, data, check, mutator):
    timeline_form = TimelineForm(
        data=data.POST or None, instance=data.program_timeline)
    return {
        'page_name': 'Edit program timeline',
        'forms': [timeline_form],
        'error': timeline_form.errors,
        'description' : 'Please note that all times are UTC.'
    }

  def validate(self, data):
    timeline_form = TimelineForm(
        data=data.POST, instance=data.program_timeline)
    if timeline_form.is_valid():
      timeline_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate(data):
      data.redirect.program()
      return data.redirect.to('edit_gsoc_timeline', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class GSoCProgramMessagesPage(
    soc_program_view.ProgramMessagesPage, base.GSoCRequestHandler):
  """View for the content of GSoC program specific messages to be sent."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(
            r'program/messages/edit/%s$' % soc_url_patterns.PROGRAM, self,
            name=self._getUrlName()),
    ]

  def templatePath(self):
    return 'modules/gsoc/program/messages.html'

  def _getForm(self, data, entity):
    return GSoCProgramMessagesForm(
        request_data=data, data=data.POST or None, instance=entity)

  def _getModel(self):
    return program.GSoCProgramMessages

  def _getUrlName(self):
    return url_names.GSOC_EDIT_PROGRAM_MESSAGES


class UniversitiesForm(forms.GSoCModelForm):
  """Form to submit list of universities."""

  universities = forms.CharField(
      widget=forms.Textarea(), label=_UNIVERSITIES_LIST_LABEL, 
      help_text=_UNIVERSITIES_LIST_HELP_TEXT)

  def clean_universities(self):
    """Cleans data passed to universities field.

    Returns:
      list of tuples. Each element of that tuple represents a single
      university and has exactly three elements. The first one is unique
      identifier of the university, the second one is its name and the third
      one is the country in which the institution is located.
    """
    reader = csv.reader(StringIO.StringIO(self.cleaned_data['universities']))

    universities = []
    for i, row in enumerate(reader):
      # skip empty lines
      if not row:
        continue

      # check if each university description has correct number of positions
      if len(row) != 3:
        raise forms.ValidationError(
            'University in line %s has wrong number of fields' % i)
      else:
        universities.append((
            html_utils.escape(row[0]),
            html_utils.escape(row[1]),
            html_utils.escape(row[2])))

    return universities


@ndb.transactional
def _uploadUniversitiesTxn(input_data, program_key):
  """Uploads a list of predefined universities from the specified input data
  for the specified program in a transaction.

  Args:
    input_data: data containing universities, as received 
      from UniversitiesForm.
    program_key: program key.
  """
  universities_logic.uploadUniversities(input_data, program_key)


class UploadUniversitiesPage(base.GSoCRequestHandler):
  """View for program administrators to upload list of predefined universities
  for the program."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GSoCRequestHandler.djangoURLPatterns for specification."""
    return [
        url_patterns.url(
            r'program/universities/upload/%s$' % soc_url_patterns.PROGRAM,
            self, name=url_names.GSOC_PROGRAM_UPLOAD_UNIVERSITIES),
    ]

  def templatePath(self):
    """See base.GSoCRequestHandler.templatePath for specification."""
    return 'modules/gsoc/form_base.html'

  def context(self, data, check, mutator):
    """See base.GSoCRequestHandler.context for specification."""
    return {
        'forms': [UniversitiesForm(data=data.POST or None)]
        }

  def post(self, data, check, mutator):
    """See base.GSoCRequestHandler.post for specification."""
    form = UniversitiesForm(data=data.POST)
    if form.is_valid():
      _uploadUniversitiesTxn(
          form.cleaned_data['universities'], data.program.key())

      url = links.Linker().program(
          data.program, url_names.GSOC_PROGRAM_UPLOAD_UNIVERSITIES)
      return http.HttpResponseRedirect(url)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)
    