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

"""Module for students in GCI to upload their forms.
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]

from django import forms
from django.utils.translation import ugettext

from google.appengine.dist import httplib
from google.appengine.ext import blobstore

from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns

from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


DEF_NO_UPLOAD_MSG = ugettext('Please choose at least one file to upload.')


class UploadForm(gci_forms.GCIModelForm):
  """Django form to upload student forms
  """

  class Meta:
    model = GCIStudentInfo
    css_prefix = 'gci_student_forms'
    fields = ['consent_form', 'student_id_form']

  consent_form = forms.FileField(required=False)
  student_id_form = forms.FileField(required=False)

  def __init__(self, r, *args, **kwargs):
    """Initializes the FileFields.
    """
    super(UploadForm, self).__init__(*args, **kwargs)

    if self.instance:
      self.fields['consent_form']._file = self.instance.consent_form
      download_url = '%s?consent_form' %r.program().urlOf('gci_student_form_upload')
      self.fields['consent_form']._link = download_url

      self.fields['student_id_form']._file = self.instance.student_id_form
      download_url = '%s?student_id_form' %r.program().urlOf('gci_student_form_upload')
      self.fields['student_id_form']._link = download_url

  def clean(self):
    """Ensure that at least one of the fields has data.
    """
    cleaned_data = self.cleaned_data

    consent_form = cleaned_data.get('consent_form')
    student_id_form = cleaned_data.get('student_id_form')

    if not (consent_form or student_id_form):
      raise gci_forms.ValidationError(DEF_NO_UPLOAD_MSG)

    return cleaned_data


class StudentFormUpload(RequestHandler):
  """View for uploading your student forms.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the view.
    """
    return [
        url(r'student/forms/%s$' % url_patterns.PROGRAM, self,
            name='gci_student_form_upload')]

  def checkAccess(self):
    """Denies access if you are not a student.
    """
    self.check.isActiveStudent()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'v2/modules/gci/student_forms/base.html'

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
      self.error(httplib.NOT_FOUND, 'File not found')

    self.response = bs_helper.send_blob(download, save_as=True)

  def context(self):
    """Handler for default HTTP GET request.
    """
    context = {
        'page_name': 'Student form upload'
        }

    if self.data.POST:
      upload_form = UploadForm(self.redirect, self.data.POST,
                               instance=self.data.student_info)
    else:
      upload_form = UploadForm(self.redirect, instance=self.data.student_info)

    context['form'] = upload_form
    url = self.redirect.program().urlOf('gci_student_form_upload')
    context['upload_url'] = blobstore.create_upload_url(url)

    return context

  def post(self):
    """Handles POST requests for the bulk create page.
    """
    form = UploadForm(
        self.redirect,data=self.data.POST, instance=self.data.student_info,
        files=self.data.request.file_uploads)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blobs from the cloud
      for file in self.data.request.file_uploads.itervalues():
        file.delete()

      return self.get()

    # delete existing data
    cleaned_data = form.cleaned_data
    for field_name in self.data.request.file_uploads.keys():
      if field_name in cleaned_data:
        existing = getattr(self.data.student_info, field_name)
        if existing:
          existing.delete()

    form.save()

    self.redirect.program().to('gci_student_form_upload')
