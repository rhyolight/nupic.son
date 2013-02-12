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

from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.forms import GSoCModelForm
from soc.modules.gsoc.views.helper.url_patterns import url


class TaxForm(GSoCModelForm):
  """Django form for the student tax form.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_form'
    fields = ['tax_form']
    widgets = {}

  tax_form = fields.FileField(label='Upload new tax form',
                              required=True)

  def fileFieldName(self):
    """Returns the name of the FileField in this form.
    """
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

    return 'gsoc_tax_form_download'

  def __init__(self, request_data, *args, **kwargs):
    super(TaxForm, self).__init__(*args, **kwargs)
    self.request_data = request_data
    field = self.fields['tax_form']

    if not (self.instance and self.instance.tax_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.tax_form
      field._link = self._r().urlOf(self._urlName())


class EnrollmentForm(GSoCModelForm):
  """Django form for the student enrollment form.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_form'
    fields = ['enrollment_form']
    widgets = {}

  enrollment_form = fields.FileField(label='Upload new enrollment form',
                                     required=True)

  def fileFieldName(self):
    """Returns the name of the FileField in this form.
    """
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

    return 'gsoc_enrollment_form_download'

  def __init__(self, request_data, *args, **kwargs):
    super(EnrollmentForm, self).__init__(*args, **kwargs)
    self.request_data = request_data
    field = self.fields['enrollment_form']

    if not (self.instance and self.instance.enrollment_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.enrollment_form
      field._link = self._r().urlOf(self._urlName())


class FormPage(GSoCRequestHandler):
  """View to upload student forms."""

  def djangoURLPatterns(self):
    return [
        url(r'student_forms/enrollment/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_enrollment_form',
            kwargs=dict(form='enrollment', admin=False)),
        url(r'student_forms/tax/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_tax_form',
            kwargs=dict(form='tax', admin=False)),
        url(r'student_forms/admin/enrollment/%s$' % url_patterns.PROFILE,
            self, name='gsoc_enrollment_form_admin',
            kwargs=dict(form='enrollment', admin=True)),
        url(r'student_forms/admin/tax/%s$' % url_patterns.PROFILE,
            self, name='gsoc_tax_form_admin',
            kwargs=dict(form='tax', admin=True)),
    ]

  def checkAccess(self, data, check, mutator):
    if self._admin(data):
      check.isHost()
      mutator.studentFromKwargs()
    else:
      check.isStudentWithProject()
      if data.POST:
        # No uploading after program ends.
        check.isProgramRunning()

  def templatePath(self):
    return 'v2/modules/gsoc/student_forms/base.html'

  def context(self, data, check, mutator):
    Form = self._form(data)
    form = Form(data, data.POST or None, instance=self._studentInfo(data))

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

  def _studentInfo(self, data):
    if self._admin(data):
      return data.url_student_info
    else:
      return data.student_info

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
    form = Form(data, data=data.POST,
                files=data.request.file_uploads,
                instance=self._studentInfo(data))

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blob from the cloud
      for blob_info in data.request.file_uploads.itervalues():
        blob_info.delete()

      # since this is a file upload we must return a 300 response
      error = form.errors[form.fileFieldName()]
      return self._r(data).to(
          self._urlName(data), extra=['error=%s' % error.as_text()])

    # delete the old blob, if it exists
    oldBlob = getattr(data.student_info, form.fileFieldName())
    if oldBlob:
      oldBlob.delete()

    # write information about the new blob to the datastore
    form.save()

    return self._r(data).to(self._urlName(data), validated=True)


class DownloadForm(GSoCRequestHandler):
  """View for downloading a student form."""

  def djangoURLPatterns(self):
    return [
        url(r'student_forms/enrollment/download/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_enrollment_form_download',
            kwargs=dict(form='enrollment', admin=False)),
        url(r'student_forms/tax/download/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_tax_form_download',
            kwargs=dict(form='tax', admin=False)),
        url(r'student_forms/admin/enrollment/download/%s$' %
                url_patterns.PROFILE,
            self, name='gsoc_enrollment_form_download_admin',
            kwargs=dict(form='enrollment', admin=True)),
        url(r'student_forms/admin/tax/download/%s$' % url_patterns.PROFILE,
            self, name='gsoc_tax_form_download_admin',
            kwargs=dict(form='tax', admin=True)),
    ]

  def checkAccess(self, data, check, mutator):
    if self._admin(data):
      check.isHost()
      mutator.studentFromKwargs()
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
