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

"""Module containing the boiler plate required to construct templates
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from google.appengine.ext import db

from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from soc.views import forms
from soc.views import org_app


TEMPLATE_PATH = 'v2/modules/gci/_form.html'

class GCIModelForm(forms.ModelForm):
  """Django ModelForm class which uses our implementation of BoundField.
  """
  
  def __init__(self, *args, **kwargs):
    super(GCIModelForm, self).__init__(
        GCIBoundField, TEMPLATE_PATH, *args, **kwargs)


class OrgAppEditForm(org_app.OrgAppEditForm):
  """Form to create/edit GCI organization application survey.
  """

  def __init__(self, *args, **kwargs):
    super(OrgAppEditForm, self).__init__(
        GCIBoundField, TEMPLATE_PATH, *args, **kwargs)


class OrgAppTakeForm(org_app.OrgAppTakeForm):
  """Form for would-be organization admins to apply for a GCI program.
  """

  def __init__(self, *args, **kwargs):
    super(OrgAppTakeForm, self).__init__(
        GCIBoundField, TEMPLATE_PATH, *args, **kwargs)


class GCIBoundField(forms.BoundField):
  """GCI specific BoundField representation.
  """

  def render(self):
    widget = self.field.widget

    if isinstance(widget, forms.DocumentWidget):
      self.setDocumentWidgetHelpText()

    if isinstance(widget, forms.ReferenceWidget):
      return self.renderReferenceWidget()
    elif isinstance(widget, forms.TextInput):
      return self.renderTextInput()
    elif isinstance(widget, forms.Textarea):
      return self.renderTextArea()
    elif isinstance(widget, forms.DateInput):
      return self.renderTextInput()
    elif isinstance(widget, forms.Select):
      return self.renderSelect()

    return self.NOT_SUPPORTED_MSG_FMT % (
        widget.__class__.__name__)

  def renderTextInput(self):
    attrs = {
        'id': self.name,
        'class': 'text',
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def renderTextArea(self):
    attrs = {
        'id': 'melange-%s-textarea' % self.name,
        'class': 'textarea'
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def renderSelect(self):
    attrs = {
        'id': self.name,
        'style': 'opacity: 100;',
        }

    return mark_safe('%s%s%s%s' % (
        self.as_widget(attrs=attrs),
        self._render_is_required(),
        self._render_error(),
        self._render_note(),
    ))

  def setDocumentWidgetHelpText(self):
    value = self.form.initial.get(self.name, self.field.initial)

    if value:
      document = db.get(value)
      args = [document.prefix, document.scope_path + '/', document.link_id]
    else:
      scope_path = self.form.scope_path
      args = ['gci_program', scope_path + '/', self.name]

    edit_document_link = reverse('edit_gci_document', args=args)
    self.help_text = """<a href="%s">Click here to edit this document.</a>
        <br />%s""" % (edit_document_link, self.help_text)

  def _render_label(self):
    err = ''
    if self.errors:
      err = '<span class="form-row-error-msg">%s</span>' % (
        self.errors[0])

    return '<label class="form-label">%s%s%s</label>' % (
        self.field.label,
        self._render_is_required(),
        err,
    ) if self.field.label else ''

  def _render_is_required(self):
    return '<em>*</em>' if self.field.required else ''

  def _render_error(self):
    return ''

  def _render_note(self, note=None):
    return '<span class="note">%s</span>' % (
        note if note else self.help_text)

  def div_class(self):
    div_class = 'form-row'

    if self.errors:
      div_class += ' error'

    return div_class
