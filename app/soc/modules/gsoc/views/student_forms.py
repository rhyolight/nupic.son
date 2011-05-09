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
from django.conf.urls.defaults import url

from soc.views import forms
from soc.views.helper import blobstore as bs_helper

from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns


class TaxForm(forms.ModelForm):
  """Django form for the student tax form.
  """

  class Meta:
    model = GSoCStudentInfo
    css_prefix = 'student_form'
    fields = ['tax_form']
    widgets = {}

  tax_form = fields.FileField(label='Upload new tax form', required=False)

  def __init__(self, data, *args, **kwargs):
    super(TaxForm, self).__init__(*args, **kwargs)
    self.data = data
    field = self.fields['tax_form']

    if not (self.instance and self.instance.tax_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.tax_form
      field._link = data.redirect.program().urlOf('gsoc_tax_form_download')

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

  def __init__(self, data, *args, **kwargs):
    super(EnrollmentForm, self).__init__(*args, **kwargs)
    self.data = data
    field = self.fields['enrollment_form']

    if not (self.instance and self.instance.enrollment_form):
      field._file = None
      field._link = None
    else:
      field._file = self.instance.enrollment_form
      field._link = data.redirect.program().urlOf('gsoc_enrollment_form_download')

  def clean_enrollment_form(self):
    uploads = self.data.request.file_uploads
    return uploads[0] if uploads else None


class TaxFormPage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/student_forms/tax/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_tax_form'),
    ]

  def checkAccess(self):
    self.check.isStudentWithProject()

  def templatePath(self):
    return 'v2/modules/gsoc/student_forms/base.html'

  def context(self):
    tax_form = TaxForm(self.data, self.data.POST or None,
                       instance=self.data.student_info)

    return {
        'page_name': 'Tax form',
        'forms': [tax_form],
        'error': bool(tax_form.errors),
        }

  def validate(self):
    tax_form = TaxForm(self.data, self.data.POST,
                       instance=self.data.student_info)
    if not tax_form.is_valid():
      return False

    tax_form.save()

  def json(self):
    url = self.redirect.program().urlOf('gsoc_tax_form', secure=True)
    upload_url = blobstore.create_upload_url(url)
    self.response.write(upload_url)

  def post(self):
    validated = self.validate()
    self.redirect.program().to('gsoc_tax_form', validated=validated)


class EnrollmentFormPage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/student_forms/enrollment/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_enrollment_form'),
    ]

  def checkAccess(self):
    self.check.isStudentWithProject()

  def templatePath(self):
    return 'v2/modules/gsoc/student_forms/base.html'

  def context(self):
    enrollment_form = EnrollmentForm(self.data, self.data.POST or None,
                       instance=self.data.student_info)

    return {
        'page_name': 'Enrollment form',
        'forms': [enrollment_form],
        'error': bool(enrollment_form.errors),
        }

  def validate(self):
    enrollment_form = EnrollmentForm(self.data, self.data.POST,
                       instance=self.data.student_info)
    if not enrollment_form.is_valid():
      return False

    enrollment_form.save()

  def json(self):
    url = self.redirect.program().urlOf('gsoc_enrollment_form', secure=True)
    upload_url = blobstore.create_upload_url(url)
    self.response.write(upload_url)

  def post(self):
    validated = self.validate()
    self.redirect.program().to('gsoc_enrollment_form', validated=validated)


class DownloadTaxForm(RequestHandler):
  """View for downloading the tax form.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/student_forms/tax/download/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_tax_form_download'),
    ]

  def checkAccess(self):
    self.check.isProfileActive()

  def get(self):
    blob_key = str(self.data.student_info.tax_form.key())
    self.response = bs_helper.download_blob(blob_key)


class DownloadEnrollmentForm(RequestHandler):
  """View for downloading the enrollment form.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/student_forms/enrollment/download/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_enrollment_form_download'),
    ]

  def checkAccess(self):
    self.check.isProfileActive()

  def get(self):
    blob_key = str(self.data.student_info.enrollment_form.key())
    self.response = bs_helper.download_blob(blob_key)