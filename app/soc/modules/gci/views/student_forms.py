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

"""Module for students in GCI to upload their forms."""

from google.appengine.ext import blobstore
from google.appengine.dist import httplib

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from soc.logic import dicts
from soc.logic.exceptions import BadRequest
from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


DEF_NO_UPLOAD = ugettext('Please choose at least one file to upload.')

CLAIM_TASKS_NOW = ugettext('You can now claim tasks <a href="%s">here</a>')

DEF_CONSENT_FORM_HELP_TEXT = ugettext(
    '%s.<br />To download the sample form or one of its translations '
    '<a href="%s">click here.</a>')

DEF_STUDENT_ID_FORM_TEXT_HELP = ugettext(
    'A scan of your Student ID, School transcript or letter from school. '
    'For examples <a href="%s">click here</a>.')


class UploadForm(gci_forms.GCIModelForm):
  """Django form to upload student forms
  """

  class Meta:
    model = GCIStudentInfo
    css_prefix = 'gci_student_forms'
    fields = ['consent_form', 'student_id_form']

  consent_form = gci_forms.FileField(required=False)
  student_id_form = gci_forms.FileField(required=False)

  def __init__(self, request_data, *args, **kwargs):
    """Initializes the FileFields.
    """
    super(UploadForm, self).__init__(*args, **kwargs)

    base_url = request_data.redirect.program().urlOf(
        url_names.GCI_STUDENT_FORM_UPLOAD)

    self['consent_form'].field.widget = gci_forms.AsyncFileInput(
        download_url='%s?%s' % (base_url, url_names.CONSENT_FORM_GET_PARAM),
        verified=self.instance.consent_form_verified)
    self['student_id_form'].field.widget = gci_forms.AsyncFileInput(
        download_url='%s?%s' % (base_url, url_names.STUDENT_ID_FORM_GET_PARAM),
        verified=self.instance.student_id_form_verified)

    self['consent_form'].field.help_text = (
        DEF_CONSENT_FORM_HELP_TEXT % (
            self['consent_form'].field.help_text,
            request_data.program.form_translations_url))
    self['student_id_form'].field.help_text = (
        DEF_STUDENT_ID_FORM_TEXT_HELP % 
            request_data.program.form_translations_url)

  def clean(self):
    """Ensure that at least one of the fields has data.
    """
    cleaned_data = self.cleaned_data

    consent_form = cleaned_data.get('consent_form')
    student_id_form = cleaned_data.get('student_id_form')

    if not (consent_form or student_id_form):
      raise gci_forms.ValidationError(DEF_NO_UPLOAD)

    return cleaned_data

  def save(self, commit=True):
    student_info = super(UploadForm, self).save(commit=False)
    cleaned_data = self._cleaned_data()

    if cleaned_data.get('consent_form'):
      student_info.consent_form_verified = False

    if cleaned_data.get('student_id_form'):
      student_info.student_id_form_verified = False

    if commit:
      student_info.put()

    return student_info


class StudentFormUpload(GCIRequestHandler):
  """View for uploading your student forms."""

  def djangoURLPatterns(self):
    """The URL pattern for the view.
    """
    return [
        url(r'student/forms/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_STUDENT_FORM_UPLOAD)]

  def checkAccess(self):
    """Denies access if you are not a student or the program is not running.
    """
    self.check.isActiveStudent()
    if self.data.POST:
      self.check.isProgramRunning()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'v2/modules/gci/student_forms/base.html'

  def jsonContext(self):
    url = self.redirect.program().urlOf('gci_student_form_upload', secure=True)
    return {
        'upload_link': blobstore.create_upload_url(url),
        }

  def get(self):
    """Handles download of the forms otherwise resumes normal rendering.
    """
    if 'consent_form' in self.data.GET:
      download = self.data.student_info.consent_form
    elif 'student_id_form' in self.data.GET:
      download = self.data.student_info.student_id_form
    else:
      return super(StudentFormUpload, self).get()

    # download has been requested
    if not download:
      self.response = self.error(httplib.NOT_FOUND, message='File not found')
      return

    self.response = bs_helper.sendBlob(download)

  def context(self):
    """Handler for default HTTP GET request.
    """
    context = {
        'page_name': 'Student form upload'
        }

    upload_form = UploadForm(self.data, instance=self.data.student_info)

    if profile_logic.hasStudentFormsUploaded(self.data.student_info):
      kwargs = dicts.filter(self.data.kwargs, ['sponsor', 'program'])
      claim_tasks_url = reverse('gci_list_tasks', kwargs=kwargs)
      context['form_instructions'] = CLAIM_TASKS_NOW % claim_tasks_url
    # TODO(ljvderijk): This can be removed when AppEngine supports 200 response
    # in the BlobStore API.
    if self.data.GET:
      for key, error in self.data.GET.iteritems():
        if not key.startswith('error_'):
          continue
        field_name = key.split('error_', 1)[1]
        upload_form.errors[field_name] = upload_form.error_class([error])

    context['form'] = upload_form

    return context

  def post(self):
    """Handles POST requests for the bulk create page.
    """
    form = UploadForm(
        self.data, data=self.data.POST, instance=self.data.student_info,
        files=self.data.request.file_uploads)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blobs from the cloud
      for f in self.data.request.file_uploads.itervalues():
        f.delete()

      # since this is a file upload we must return a 300 response
      extra_args = []
      for field, error in form.errors.iteritems():
        extra_args.append('error_%s=%s' %(field, error.as_text()))

      self.data.redirect.to('gci_student_form_upload', extra=extra_args)
      return

    # delete existing data
    cleaned_data = form.cleaned_data
    for field_name in self.data.request.file_uploads.keys():
      if field_name in cleaned_data:
        existing = getattr(self.data.student_info, field_name)
        if existing:
          existing.delete()

    form.save()

    self.redirect.program().to('gci_student_form_upload')


class StudentFormDownload(GCIRequestHandler):
  """View for uploading your student forms."""

  def djangoURLPatterns(self):
    """The URL pattern for the view."""
    return [
        url(r'student/forms/%s$' % url_patterns.PROFILE, self,
            name=url_names.GCI_STUDENT_FORM_DOWNLOAD)]

  def checkAccess(self):
    """Denies access if you are not a host."""
    self.check.isHost()
    self.mutator.studentFromKwargs()

  def get(self):
    """Allows hosts to download the student forms."""
    download = None
    if url_names.CONSENT_FORM_GET_PARAM in self.data.GET:
      download = self.data.url_student_info.consent_form
    elif url_names.STUDENT_ID_FORM_GET_PARAM in self.data.GET:
      download = self.data.url_student_info.student_id_form
    else:
      raise BadRequest('No file requested')

    # download has been requested
    if not download:
      self.response = self.error(httplib.NOT_FOUND, 'File not found')
      return

    self.response = bs_helper.sendBlob(download)
