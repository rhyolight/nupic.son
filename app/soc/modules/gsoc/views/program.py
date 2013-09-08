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

from google.appengine.ext import blobstore
from google.appengine.ext import db

from django import forms as django_forms
from django import http
from django.utils import html as html_utils
from django.utils import translation

from melange.logic import school as school_logic
from melange.request import access

from soc.logic import links
from soc.logic import mail_dispatcher
from soc.logic.helper import notifications
from soc.models import document
from soc.views import program as soc_program_view
from soc.views.helper import access_checker
from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns as soc_url_patterns

from soc.modules.gsoc.models import program as program_model
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

_SCHOOLS_LIST_LABEL = translation.ugettext('File to upload')

_SCHOOLS_LIST_HELP_TEXT = translation.ugettext(
    'File with a list of predefined schools to be uploaded for the program. '
    'Each line should contain tab separated unique school identifier, '
    'name, and country, respectively.')

_UPLOAD_SCHOOLS_PAGE_NAME = translation.ugettext('Upload schools for program')

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
    model = program_model.GSoCProgram
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
    model = program_model.GSoCProgram
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
    model = program_model.GSoCProgramMessages

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
    return program_model.GSoCProgramMessages

  def _getUrlName(self):
    return url_names.GSOC_EDIT_PROGRAM_MESSAGES


# TODO(daniel): this function should be transactional once Program is NDB
#@ndb.transactional
def _uploadSchoolsTxn(input_data, program):
  """Uploads a list of predefined schools from the specified input data
  for the specified program in a transaction.

  Args:
    input_data: data containing schools, as received from SchoolsForm.
    program_key: program key.
  """
  school_logic.uploadSchools(input_data, program)


class UploadSchoolsForm(forms.GSoCModelForm):
  """Form to upload list of predefined schools for the program."""

  schools = forms.FileField(
      label=_SCHOOLS_LIST_LABEL, help_text=_SCHOOLS_LIST_HELP_TEXT)

  def __init__(self, blob_info=None, download_link=None, **kwargs):
    """Initializes a new instance of the form.

    Args:
      blob_info: blobstore.BlobInfo with the previously uploaded file.
      download_link: URL to download the previously uploaded file.
    """
    super(UploadSchoolsForm, self).__init__(**kwargs)
    field = self.fields['schools']
    field._file = blob_info
    field._link = download_link


class UploadSchoolsPage(base.GSoCRequestHandler):
  """View for program administrators to upload list of predefined schools
  for the program."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GSoCRequestHandler.djangoURLPatterns for specification."""
    return [
        url_patterns.url(
            r'program/schools/upload/%s$' % soc_url_patterns.PROGRAM,
            self, name=url_names.GSOC_PROGRAM_UPLOAD_SCHOOLS),
    ]

  def templatePath(self):
    """See base.GSoCRequestHandler.templatePath for specification."""
    return 'modules/gsoc/program/schools.html'

  def jsonContext(self, data, check, mutator):
    """See base.GSoCRequestHandler.jsonContext for specification."""
    url = links.Linker().program(
        data.program, url_names.GSOC_PROGRAM_UPLOAD_SCHOOLS)
    return {
        'upload_link': blobstore.create_upload_url(url),
        }

  def context(self, data, check, mutator):
    """See base.GSoCRequestHandler.context for specification."""
    if data.program.schools is not None:
      form = UploadSchoolsForm(
          data=data.POST or None, blob_info=data.program.schools,
          download_link=links.Linker().program(
              data.program, url_names.GSOC_PROGRAM_DOWNLOAD_SCHOOLS))
    else:
      form = UploadSchoolsForm(data=data.POST or None)

    return {
        'page_name': _UPLOAD_SCHOOLS_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors),
        }

  def post(self, data, check, mutator):
    """See base.GSoCRequestHandler.post for specification."""
    form = UploadSchoolsForm(data=data.POST, files=data.request.file_uploads)
    if not form.is_valid():
      # we are not storing this form, remove the uploaded blob from the cloud
      for blob_info in data.request.file_uploads.itervalues():
        blob_info.delete()

      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      data.program.schools = blobstore.BlobInfo(form.cleaned_data['schools'])
      data.program.put()

    # TODO(daniel): inform user about possible errors somehow
    url = links.Linker().program(
        data.program, url_names.GSOC_PROGRAM_UPLOAD_SCHOOLS)
    return http.HttpResponseRedirect(url)


class DownloadSchoolsHandler(base.GSoCRequestHandler):
  """Handler to download a previously uploaded file with schools that are
  defined for the specified program.
  """

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.GSoCRequestHandler.djangoURLPatterns for specification."""
    return [
        url_patterns.url(
            r'program/schools/download/%s$' % soc_url_patterns.PROGRAM,
            self, name=url_names.GSOC_PROGRAM_DOWNLOAD_SCHOOLS),
    ]

  def get(self, data, check, mutator):
    """See base.GSoCRequestHandler.get for specification."""
    return bs_helper.sendBlob(data.program.schools)
