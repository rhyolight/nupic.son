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

"""Module for the GSoC student forms.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from google.appengine.ext import blobstore

from django.forms import fields

from soc.views import forms
from soc.views.helper import blobstore as bs_helper

from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


class TaxForm(forms.ModelForm):
  """Django form for the student tax form.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_form'
    fields = ['tax_form']
    widgets = {}

  tax_form = fields.FileField(label='Upload new tax form', required=False)

  def _admin(self):
    return self.data.kwargs['admin']

  def _r(self):
    r = self.data.redirect
    return r.profile() if self._admin() else r.program()

  def _urlName(self):
    if self._admin():
      return 'gsoc_tax_form_download_admin'

    return 'gsoc_tax_form_download'

  def __init__(self, data, *args, **kwargs):
    super(TaxForm, self).__init__(*args, **kwargs)
    self.data = data
    field = self.fields['tax_form']

    if not (self.instance and self.instance.tax_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.tax_form
      field._link = self._r().urlOf(self._urlName())

  def clean_tax_form(self):
    uploads = self.data.request.file_uploads
    return uploads[0] if uploads else None


class EnrollmentForm(forms.ModelForm):
  """Django form for the student enrollment form.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_form'
    fields = ['enrollment_form']
    widgets = {}

  enrollment_form = fields.FileField(label='Upload new enrollment form', required=False)

  def _admin(self):
    return self.data.kwargs['admin']

  def _r(self):
    r = self.data.redirect
    return r.profile() if self._admin() else r.program()

  def _urlName(self):
    if self._admin():
      return 'gsoc_enrollment_form_download_admin'

    return 'gsoc_enrollment_form_download'

  def __init__(self, data, *args, **kwargs):
    super(EnrollmentForm, self).__init__(*args, **kwargs)
    self.data = data
    field = self.fields['enrollment_form']

    if not (self.instance and self.instance.enrollment_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.enrollment_form
      field._link = self._r().urlOf(self._urlName())

  def clean_enrollment_form(self):
    uploads = self.data.request.file_uploads
    return uploads[0] if uploads else None


class FormPage(RequestHandler):
  """View to upload student forms.
  """

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

  def checkAccess(self):
    if self._admin():
      self.check.isHost()
      self.mutator.studentFromKwargs()
    else:
      self.check.isStudentWithProject()

  def templatePath(self):
    return 'v2/modules/gsoc/student_forms/base.html'

  def context(self):
    Form = self._form()
    form = Form(self.data, self.data.POST or None, instance=self._studentInfo())

    return {
        'page_name': self._name(),
        'forms': [form],
        'error': bool(form.errors),
        }

  def validate(self):
    Form = self._form()
    form = Form(self.data, self.data.POST, instance=self._studentInfo())

    if not form.is_valid():
      return False

    form.save()

  def _name(self):
    return 'Tax form' if self._tax() else 'Enrollment form'

  def _form(self):
    return TaxForm if self._tax() else EnrollmentForm

  def _studentInfo(self):
    if self._admin():
      return self.data.url_student_info
    else:
      return self.data.student_info

  def _admin(self):
    return self.kwargs['admin']

  def _tax(self):
    return self.kwargs['form'] == 'tax'

  def _urlName(self):
    if self._admin():
      if self._tax():
        return 'gsoc_tax_form_admin'
      return 'gsoc_enrollment_form_admin'

    if self._tax():
      return 'gsoc_tax_form'
    return 'gsoc_enrollment_form'

  def _r(self):
    return self.redirect.profile() if self._admin() else self.redirect.program()

  def json(self):
    url = self._r().urlOf(self._urlName(), secure=True)
    upload_url = blobstore.create_upload_url(url)
    self.response.write(upload_url)

  def post(self):
    validated = self.validate()
    self._r().to(self._urlName(), validated=validated)


class DownloadForm(RequestHandler):
  """View for downloading a student form.
  """

  def djangoURLPatterns(self):
    return [
        url(r'student_forms/enrollment/download/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_enrollment_form_download',
            kwargs=dict(form='enrollment', admin=False)),
        url(r'student_forms/tax/download/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_tax_form_download',
            kwargs=dict(form='tax', admin=False)),
        url(r'student_forms/admin/enrollment/download/%s$' % url_patterns.PROFILE,
            self, name='gsoc_enrollment_form_download_admin',
            kwargs=dict(form='enrollment', admin=True)),
        url(r'student_forms/admin/tax/download/%s$' % url_patterns.PROFILE,
            self, name='gsoc_tax_form_download_admin',
            kwargs=dict(form='tax', admin=True)),
    ]

  def checkAccess(self):
    if self._admin():
      self.check.isHost()
      self.mutator.studentFromKwargs()
    else:
      self.check.isProfileActive()

  def _admin(self):
    return self.kwargs['admin']

  def _tax(self):
    return self.kwargs['form'] == 'tax'

  def _studentInfo(self):
    if self._admin():
      return self.data.url_student_info
    else:
      return self.data.student_info

  def get(self):
    if self._tax():
      blob_key = str(self._studentInfo().tax_form.key())
    else:
      blob_key = str(self._studentInfo().enrollment_form.key())
    self.response = bs_helper.download_blob(blob_key)
