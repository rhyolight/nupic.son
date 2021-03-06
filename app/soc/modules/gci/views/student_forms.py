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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from codein.logic import profile as ci_profile_logic

from melange.request import exception

from soc.logic import dicts
from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.views import base
from soc.modules.gci.views import forms as gci_forms
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
  """Django form to upload student forms."""

  Meta = object

  consent_form = gci_forms.FileField(required=False)
  enrollment_form = gci_forms.FileField(required=False)

  def __init__(self, request_data, **kwargs):
    """Initializes the FileFields.
    """
    super(UploadForm, self).__init__(**kwargs)

    self.request_data = request_data

    # TODO(nathaniel): make this .program() call unnecessary.
    request_data.redirect.program()

    base_url = request_data.redirect.urlOf(url_names.GCI_STUDENT_FORM_UPLOAD)

    self['consent_form'].field.widget = gci_forms.AsyncFileInput(
        download_url='%s?%s' % (base_url, url_names.CONSENT_FORM_GET_PARAM),
        verified=request_data.ndb_profile
            .student_data.is_consent_form_verified)
    self['enrollment_form'].field.widget = gci_forms.AsyncFileInput(
        download_url='%s?%s' % (base_url, url_names.ENROLLMENT_FORM_GET_PARAM),
        verified=request_data.ndb_profile
            .student_data.is_enrollment_form_verified)

    self['consent_form'].field.help_text = (
        DEF_CONSENT_FORM_HELP_TEXT % (
            self['consent_form'].field.help_text,
            request_data.program.form_translations_url))
    self['enrollment_form'].field.help_text = (
        DEF_STUDENT_ID_FORM_TEXT_HELP %
            request_data.program.form_translations_url)

  def clean(self):
    """Ensure that at least one of the fields has data.
    """
    cleaned_data = self.cleaned_data

    consent_form = cleaned_data.get('consent_form')
    enrollment_form = cleaned_data.get('enrollment_form')

    if not (consent_form or enrollment_form):
      raise gci_forms.ValidationError(DEF_NO_UPLOAD)

    return cleaned_data

  def save(self, commit=True):
    if self.cleaned_data.get('consent_form'):
      self.request_data.ndb_profile.student_data.consent_form = (
          self.cleaned_data.get('consent_form').key())
      self.request_data.ndb_profile.student_data.is_consent_form_verified = (
          False)

    if self.cleaned_data.get('enrollment_form'):
      self.request_data.ndb_profile.student_data.enrollment_form = (
          self.cleaned_data.get('enrollment_form').key())
      self.request_data.ndb_profile.student_data.is_enrollment_form_verified = (
          False)

    if commit:
      self.request_data.ndb_profile.put()

    return self.request_data.ndb_profile


class StudentFormUpload(base.GCIRequestHandler):
  """View for uploading your student forms."""

  def djangoURLPatterns(self):
    """The URL pattern for the view.
    """
    return [
        url(r'student/forms/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_STUDENT_FORM_UPLOAD)]

  def checkAccess(self, data, check, mutator):
    """Denies access if you are not a student or the program is not running.
    """
    check.isActiveStudent()
    if data.POST:
      check.isProgramRunning()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'modules/gci/student_forms/base.html'

  def jsonContext(self, data, check, mutator):
    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

    url = data.redirect.urlOf('gci_student_form_upload', secure=True)
    return {
        'upload_link': blobstore.create_upload_url(url),
        }

  def get(self, data, check, mutator):
    """Handles download of the forms otherwise resumes normal rendering."""
    if 'consent_form' not in data.GET and 'enrollment_form' not in data.GET:
      # no download request has been specified
      return super(StudentFormUpload, self).get(data, check, mutator)
    elif 'consent_form' in data.GET:
      download = data.ndb_profile.student_data.consent_form
    elif 'enrollment_form' in data.GET:
      download = data.ndb_profile.student_data.enrollment_form

    # download has been requested
    if download:
      return bs_helper.sendBlob(blobstore.BlobInfo(download))
    else:
      raise exception.NotFound(message='File not found')

  def context(self, data, check, mutator):
    """Handler for default HTTP GET request."""
    context = {'page_name': 'Student form upload'}

    form_data = {}
    if data.ndb_profile.student_data.consent_form:
      form_data['consent_form'] = blobstore.BlobInfo(
          data.ndb_profile.student_data.consent_form)
    if data.ndb_profile.student_data.enrollment_form:
      form_data['enrollment_form'] = blobstore.BlobInfo(
          data.ndb_profile.student_data.enrollment_form)

    upload_form = UploadForm(data, initial=form_data)

    if profile_logic.hasStudentFormsUploaded(data.ndb_profile):
      kwargs = dicts.filter(data.kwargs, ['sponsor', 'program'])
      claim_tasks_url = reverse('gci_list_tasks', kwargs=kwargs)
      context['form_instructions'] = CLAIM_TASKS_NOW % claim_tasks_url
    # TODO(ljvderijk): This can be removed when AppEngine supports 200 response
    # in the BlobStore API.
    if data.GET:
      for key, error in data.GET.iteritems():
        if not key.startswith('error_'):
          continue
        field_name = key.split('error_', 1)[1]
        upload_form.errors[field_name] = upload_form.error_class([error])

    context['form'] = upload_form
    context['form_verification_awaiting'] = (
        ci_profile_logic.isFormVerificationAwaiting(data.ndb_profile))

    return context

  def post(self, data, check, mutator):
    """Handles POST requests for the bulk create page."""
    form = UploadForm(data, data=data.POST, files=data.request.file_uploads)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blobs from the cloud
      for f in data.request.file_uploads.itervalues():
        f.delete()

      # since this is a file upload we must return a 300 response
      extra_args = []
      for field, error in form.errors.iteritems():
        extra_args.append('error_%s=%s' %(field, error.as_text()))

      return data.redirect.to('gci_student_form_upload', extra=extra_args)

    # delete existing data
    cleaned_data = form.cleaned_data
    for field_name in data.request.file_uploads.keys():
      if field_name in cleaned_data:
        existing = getattr(data.ndb_profile.student_data, field_name)
        if existing:
          blobstore.BlobInfo(existing).delete()

    form.save()

    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

    return data.redirect.to('gci_student_form_upload')


class StudentFormDownload(base.GCIRequestHandler):
  """View for uploading your student forms."""

  def djangoURLPatterns(self):
    """The URL pattern for the view."""
    return [
        url(r'student/forms/%s$' % url_patterns.PROFILE, self,
            name=url_names.GCI_STUDENT_FORM_DOWNLOAD)]

  def checkAccess(self, data, check, mutator):
    """Denies access if you are not a host."""
    check.isHost()

  def get(self, data, check, mutator):
    """Allows hosts to download the student forms."""
    if url_names.CONSENT_FORM_GET_PARAM in data.GET:
      download = data.url_ndb_profile.student_data.consent_form
    elif url_names.ENROLLMENT_FORM_GET_PARAM in data.GET:
      download = data.url_ndb_profile.student_data.enrollment_form
    else:
      raise exception.BadRequest(message='No file requested')

    # download has been requested
    if download:
      return bs_helper.sendBlob(blobstore.BlobInfo(download))
    else:
      raise exception.NotFound(message='File not found')
