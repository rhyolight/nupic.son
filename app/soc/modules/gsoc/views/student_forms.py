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
from django.template import defaultfilters
from django.utils.formats import dateformat

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
    if self.instance:
      uploaded_form = self.instance.tax_form
      if uploaded_form:
        link = data.redirect.program().urlOf('gsoc_tax_forms_download')
        file_download = """
            <br/>
            File: <a href="%(link)s">%(name)s</a><br/>
            Size: %(size)s <br/>
            Uploaded on: %(uploaded)s UTC)
            """ % {
                'name': uploaded_form.filename,
                'link': link,
                'size': defaultfilters.filesizeformat(uploaded_form.size),
                'uploaded': dateformat.format(
                      uploaded_form.creation, 'M jS Y, h:i:sA'),
            }
        self.fields['tax_form'].help_text += file_download

  def clean_tax_form(self):
    uploads = self.data.request.file_uploads
    return uploads[0] if uploads else None


class TaxFormPage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/student_forms/tax/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_tax_forms'),
    ]

  def checkAccess(self):
    self.check.isProfileActive()

  def templatePath(self):
    return 'v2/modules/gsoc/student_forms/tax.html'

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
    url = self.redirect.program().urlOf('gsoc_tax_forms')
    upload_url = blobstore.create_upload_url(url)
    self.response.write(upload_url)

  def post(self):
    validated = self.validate()
    self.redirect.program().to('gsoc_tax_forms', validated=validated)


class DownloadTaxForm(RequestHandler):
  """View for downloading the tax form.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/student_forms/tax/download/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_tax_forms_download'),
    ]

  def checkAccess(self):
    self.check.isProfileActive()

  def get(self):
    blob_key = str(self.data.student_info.tax_form.key())

    self.response = bs_helper.download_blob(blob_key)
