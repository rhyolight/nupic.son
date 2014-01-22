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

"""Module for the GSoC student forms."""

from google.appengine.ext import blobstore

from django.forms import fields

from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms
from soc.modules.gsoc.views.helper import url_patterns as gsoc_url_patterns


class TaxForm(forms.GSoCModelForm):
  """Django form for the student tax form."""

  class Meta:
    model = profile_model.GSoCStudentInfo
    css_prefix = 'student_form'
    fields = ['tax_form']
    widgets = {}

  tax_form = fields.FileField(label='Upload new tax form',
                              required=True)

  def fileFieldName(self):
    """Returns the name of the FileField in this form."""
    return 'tax_form'

  def _admin(self):
    return self.request_data.kwargs['admin']

  def _r(self):
    if self._admin():
      self.request_data.redirect.profile()
    else:
      self.request_data.redirect.program()
    return self.request_data.redirect

  def _urlName(self):
    if self._admin():
      return 'gsoc_tax_form_download_admin'
    else:
      return 'gsoc_tax_form_download'

  def __init__(self, request_data=None, **kwargs):
    super(TaxForm, self).__init__(**kwargs)
    self.request_data = request_data
    field = self.fields['tax_form']

    if not (self.instance and self.instance.tax_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.tax_form
      field._link = self._r().urlOf(self._urlName())


class EnrollmentForm(forms.GSoCModelForm):
  """Django form for the student enrollment form."""

  Meta = object

  enrollment_form = fields.FileField(
      label='Upload new enrollment form', required=True)

  def fileFieldName(self):
    """Returns the name of the FileField in this form."""
    return 'enrollment_form'

  def _admin(self):
    return self.request_data.kwargs['admin']

  def _r(self):
    if self._admin():
      self.request_data.redirect.profile()
    else:
      self.request_data.redirect.program()
    return self.request_data.redirect

  def _urlName(self):
    if self._admin():
      return 'gsoc_enrollment_form_download_admin'
    else:
      return 'gsoc_enrollment_form_download'

  def __init__(self, request_data=None, **kwargs):
    super(EnrollmentForm, self).__init__(**kwargs)
    self.request_data = request_data
    field = self.fields['enrollment_form']

    if not (self.instance and self.instance.enrollment_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.enrollment_form
      field._link = self._r().urlOf(self._urlName())


class FormPage(base.GSoCRequestHandler):
  """View to upload student forms."""

  def djangoURLPatterns(self):
    return [
        gsoc_url_patterns.url(
            r'student_forms/enrollment/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_enrollment_form',
            kwargs=dict(form='enrollment', admin=False)),
        gsoc_url_patterns.url(r'student_forms/tax/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_tax_form',
            kwargs=dict(form='tax', admin=False)),
        gsoc_url_patterns.url(
            r'student_forms/admin/enrollment/%s$' % url_patterns.PROFILE,
            self, name='gsoc_enrollment_form_admin',
            kwargs=dict(form='enrollment', admin=True)),
        gsoc_url_patterns.url(
            r'student_forms/admin/tax/%s$' % url_patterns.PROFILE,
            self, name='gsoc_tax_form_admin',
            kwargs=dict(form='tax', admin=True)),
    ]

  def checkAccess(self, data, check, mutator):
    if self._admin(data):
      check.isHost()
    else:
      check.canStudentUploadForms()

  def templatePath(self):
    return 'modules/gsoc/student_forms/base.html'

  def context(self, data, check, mutator):
    Form = self._form(data)
    form = Form(request_data=data, data=data.POST or None)

    if 'error' in data.GET:
      error = data.GET['error']
      form.errors[form.fileFieldName()] = form.error_class([error])

    return {
        'page_name': self._name(data),
        'forms': [form],
        'error': bool(form.errors),
        }

  def _name(self, data):
    return 'Tax form' if self._tax(data) else 'Enrollment form'

  def _form(self, data):
    return TaxForm if self._tax(data) else EnrollmentForm

  def _profile(self, data):
    if self._admin(data):
      return data.url_ndb_profile
    else:
      return data.ndb_profile

  def _admin(self, data):
    return data.kwargs['admin']

  def _tax(self, data):
    return data.kwargs['form'] == 'tax'

  def _urlName(self, data):
    if self._admin(data):
      if self._tax(data):
        return 'gsoc_tax_form_admin'
      else:
        return 'gsoc_enrollment_form_admin'
    else:
      if self._tax(data):
        return 'gsoc_tax_form'
      else:
        return 'gsoc_enrollment_form'

  def _r(self, data):
    if self._admin(data):
      data.redirect.profile()
    else:
      data.redirect.program()
    return data.redirect

  def jsonContext(self, data, check, mutator):
    url = self._r(data).urlOf(self._urlName(data), secure=True)
    return {
        'upload_link': blobstore.create_upload_url(url),
        }

  def post(self, data, check, mutator):
    Form = self._form(data)
    form = Form(request_data=data, data=data.POST,
        files=data.request.file_uploads)

    profile = self._profile(data)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blob from the cloud
      for blob_info in data.request.file_uploads.itervalues():
        blob_info.delete()

      # since this is a file upload we must return a 300 response
      error = form.errors[form.fileFieldName()]
      return self._r(data).to(
          self._urlName(data), extra=['error=%s' % error.as_text()])

    # delete the old blob, if it exists
    old_blob_key = getattr(profile.student_data, form.fileFieldName())
    if old_blob_key:
      blob_info = blobstore.get(old_blob_key)
      if blob_info:
        blob_info.delete()

    # write information about the new blob to the datastore
    blob_key = form.cleaned_data[form.fileFieldName()].key()
    setattr(profile.student_data, form.fileFieldName(), blob_key)
    profile.put()

    return self._r(data).to(self._urlName(data), validated=True)


class DownloadForm(base.GSoCRequestHandler):
  """View for downloading a student form."""

  def djangoURLPatterns(self):
    return [
        gsoc_url_patterns.url(
            r'student_forms/enrollment/download/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_enrollment_form_download',
            kwargs=dict(form='enrollment', admin=False)),
        gsoc_url_patterns.url(
            r'student_forms/tax/download/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_tax_form_download',
            kwargs=dict(form='tax', admin=False)),
        gsoc_url_patterns.url(
            (r'student_forms/admin/enrollment/download/%s$' %
             url_patterns.PROFILE),
            self, name='gsoc_enrollment_form_download_admin',
            kwargs=dict(form='enrollment', admin=True)),
        gsoc_url_patterns.url(
            r'student_forms/admin/tax/download/%s$' % url_patterns.PROFILE,
            self, name='gsoc_tax_form_download_admin',
            kwargs=dict(form='tax', admin=True)),
    ]

  def checkAccess(self, data, check, mutator):
    if self._admin(data):
      check.isHost()
    else:
      check.canStudentDownloadForms()

  def _admin(self, data):
    return data.kwargs['admin']

  def _tax(self, data):
    return data.kwargs['form'] == 'tax'

  def _studentInfo(self, data):
    return data.url_student_info if self._admin(data) else data.student_info

  def get(self, data, check, mutator):
    if self._tax(data):
      blob_info = self._studentInfo(data).tax_form
    else:
      blob_info = self._studentInfo(data).enrollment_form

    return bs_helper.sendBlob(blob_info)
