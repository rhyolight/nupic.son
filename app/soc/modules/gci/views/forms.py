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
from django.template import defaultfilters
from django.utils.formats import dateformat

from soc.views import forms
from soc.views import org_app


TEMPLATE_PATH = 'v2/modules/gci/_form.html'


class GCIModelForm(forms.ModelForm):
  """Django ModelForm class which uses our implementation of BoundField.
  """
  
  def __init__(self, *args, **kwargs):
    super(GCIModelForm, self).__init__(
        GCIBoundField, *args, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class OrgAppEditForm(org_app.OrgAppEditForm):
  """Form to create/edit GCI organization application survey.
  """

  def __init__(self, *args, **kwargs):
    super(OrgAppEditForm, self).__init__(
        GCIBoundField, *args, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class OrgAppTakeForm(org_app.OrgAppTakeForm):
  """Form for would-be organization admins to apply for a GCI program.
  """

  def __init__(self, *args, **kwargs):
    super(OrgAppTakeForm, self).__init__(
        GCIBoundField, *args, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class GCIBoundField(forms.BoundField):
  """GCI specific BoundField representation.
  """

  def __init__(self, form, field, name):
    super(GCIBoundField, self).__init__(form, field, name)

  def render(self):
    widget = self.field.widget

    if isinstance(widget, forms.DocumentWidget):
      self.setDocumentWidgetHelpText()

    if isinstance(widget, forms.ReferenceWidget):
      return self.renderReferenceWidget()
    elif isinstance(widget, forms.TOSWidget):
      return self.renderTOSWidget()
    elif isinstance(widget, forms.RadioSelect):
      return self.renderRadioSelect()
    elif isinstance(widget, forms.CheckboxSelectMultiple):
      return self.renderCheckSelectMultiple()
    elif isinstance(widget, forms.TextInput):
      return self.renderTextInput()
    elif isinstance(widget, forms.DateInput):
      return self.renderTextInput()
    elif isinstance(widget, forms.Select):
      return self.renderSelect()
    elif isinstance(widget, forms.CheckboxInput):
      return self.renderCheckboxInput()
    elif isinstance(widget, forms.Textarea):
      return self.renderTextArea()
    elif isinstance(widget, forms.DateTimeInput):
      return self.renderTextInput()
    elif isinstance(widget, forms.HiddenInput):
      return self.renderHiddenInput()
    elif isinstance(widget, forms.FileInput):
      return self.renderFileInput()

    return self.NOT_SUPPORTED_MSG_FMT % (
        widget.__class__.__name__)

  def renderTextInput(self):
    attrs = {
        'id': self.name,
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def renderCheckboxInput(self):
    attrs = {
        'id': self.name,
        'style': 'opacity: 100;',
        }

    return mark_safe(
        '<label>%s%s%s%s</label>%s' % (
        self.as_widget(attrs=attrs),
        self.field.label,
        self._render_is_required(),
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

  def renderReferenceWidget(self):
    attrs = {
        'id': self.name,
        'name': self.name,
        'type': "hidden",
        'class': 'text',
        }

    hidden = self.as_widget(attrs=attrs)
    original = self.form.initial.get(self.name)

    key = self.form.initial.get(self.name)

    if key:
      entity = db.get(key)
      if entity:
        self.form.initial[self.name] = entity.key().name()

    attrs = {
        'id': self.name + "-pretty",
        'name': self.name + "-pretty",
        'class': 'text',
        }
    pretty = self.as_widget(attrs=attrs)
    self.form.initial[self.name] = original

    return mark_safe('%s%s%s%s%s' % (
        self._render_label(),
        pretty,
        hidden,
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

  def renderTOSWidget(self):
    checkbox_attrs = {
        'id': self.name,
        'style': 'opacity: 100;',
        }

    return mark_safe(
        '<label>%s%s%s%s</label>%s' % (
        self.as_widget(attrs=checkbox_attrs),
        self.field.label,
        self._render_is_required(),
        self._render_error(),
        self._render_note(),
        ))

  def renderHiddenInput(self):
    attrs = {
        'id': self.name,
        'name': self.name,
        'type': 'hidden',
        'value': self.field.initial or '',
        }
    return self.as_widget(attrs=attrs)

  def renderFileInput(self):
    attrs = {
        'id': self.name,
        }

    current_file_fmt = """
        <br/>
        <p>
        File: <a href="%(link)s">%(name)s</a><br/>
        Size: %(size)s <br/>
        Uploaded on: %(uploaded)s UTC)
        <p>
    """

    current_file = current_file_fmt % {
        'name': self.field._file.filename,
        'link': self.field._link,
        'size': defaultfilters.filesizeformat(self.field._file.size),
        'uploaded': dateformat.format(
              self.field._file.creation, 'M jS Y, h:i:sA'),
    } if self.field._file else ""

    return mark_safe('%s%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
        current_file,
    ))

  def renderRadioSelect(self):
    attrs = {
        'id': self.name,
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def renderCheckSelectMultiple(self):
    attrs = {
        'id': self.name,
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
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
    if not self.errors:
      return ''

    return '<span class="form-row-error-msg">%s</span>' % (
        self.errors[0])

  def _render_note(self, note=None):
    return '<span class="note">%s</span>' % (
        note if note else self.help_text)

  def div_class(self):
    prefix = getattr(self.form.Meta, 'css_prefix', None)
    name = prefix + '-' + self.name if prefix else self.name

    widget_div_class = self.field.widget.attrs.get('div_class', None)
    if widget_div_class:
      name = '%s %s' % (widget_div_class, name)

    if self.errors:
      name += ' error'
    return name
