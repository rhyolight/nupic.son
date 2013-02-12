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


from google.appengine.ext import db

from django import forms as django_forms
from django.utils import translation

from soc.logic import mail_dispatcher
from soc.logic.helper import notifications
from soc.models import document
from soc.views import program as soc_program_view
from soc.views.helper import access_checker
from soc.views.helper import url_patterns as soc_url_patterns

from soc.modules.gsoc.models import program
from soc.modules.gsoc.models import timeline
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


class TimelineForm(forms.GSoCModelForm):
  """Django form to edit timeline settings."""

  class Meta:
    css_prefix = 'timeline_form'
    model = timeline.GSoCTimeline
    exclude = ['link_id', 'scope', 'scope_path']


class ProgramForm(forms.GSoCModelForm):
  """Django form for the program settings."""

  def __init__(self, request_data, *args, **kwargs):
    self.request_data = request_data
    super(ProgramForm, self).__init__(*args, **kwargs)

  class Meta:
    css_prefix = 'program_form'
    model = program.GSoCProgram
    exclude = ['link_id', 'scope', 'scope_path', 'timeline',
               'home', 'slots_allocation', 'student_max_age',
               'min_slots']


class GSoCProgramMessagesForm(forms.GSoCModelForm):
  """Django form for the program settings."""

  test_email = django_forms.EmailField(
      max_length=254, label='Test email address',
      help_text=TEST_EMAIL_HELP_TEXT, required=False)

  def __init__(self, request_data, *args, **kwargs):
    self.request_data = request_data
    super(GSoCProgramMessagesForm, self).__init__(*args, **kwargs)

  class Meta:
    css_prefix = 'program_messages_form'
    model = program.GSoCProgramMessages

  def getSendMailFromTemplateStringTxn(self, to, subject, template_string, context):
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


class ProgramPage(base.GSoCRequestHandler):
  """View for the program profile."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'program/%s$' % soc_url_patterns.PROGRAM, self,
            name='edit_gsoc_program'),
        url_patterns.url(r'program/edit/%s$' % soc_url_patterns.PROGRAM, self),
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

  def checkAccess(self, data, check, mutator):
    check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/program/base.html'

  def context(self, data, check, mutator):
    program_form = ProgramForm(data, data.POST or None, instance=data.program)
    return {
        'page_name': 'Edit program settings',
        'forms': [program_form],
        'error': program_form.errors,
    }

  def validate(self, data):
    program_form = ProgramForm(data, data.POST, instance=data.program)

    if program_form.is_valid():
      program_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    if self.validate(data):
      data.redirect.program()
      return data.redirect.to('edit_gsoc_program', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)


class TimelinePage(base.GSoCRequestHandler):
  """View for the participant profile."""

  def djangoURLPatterns(self):
    return [
        url_patterns.url(r'timeline/%s$' % soc_url_patterns.PROGRAM, self,
            name='edit_gsoc_timeline'),
        url_patterns.url(r'timeline/edit/%s$' % soc_url_patterns.PROGRAM, self),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/timeline/base.html'

  def context(self, data, check, mutator):
    timeline_form = TimelineForm(data.POST or None,
                                 instance=data.program_timeline)
    return {
        'page_name': 'Edit program timeline',
        'forms': [timeline_form],
        'error': timeline_form.errors,
    }

  def validate(self, data):
    timeline_form = TimelineForm(data.POST, instance=data.program_timeline)
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
    return 'v2/modules/gsoc/program/messages.html'

  def _getForm(self, data, entity):
    return GSoCProgramMessagesForm(data, data.POST or None, instance=entity)

  def _getModel(self):
    return program.GSoCProgramMessages

  def _getUrlName(self):
    return url_names.GSOC_EDIT_PROGRAM_MESSAGES
