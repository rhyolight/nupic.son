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


import itertools

from google.appengine.ext import db

from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.template import defaultfilters
from django.utils.formats import dateformat

from soc.views import forms
from soc.views import org_app


TEMPLATE_PATH = 'v2/modules/gci/_form.html'

# The standard input fields should be available to all importing modules
CharField = forms.CharField
CheckboxInput = forms.CheckboxInput
DateInput = forms.DateInput
DateTimeInput = forms.DateTimeInput
FileInput = forms.FileInput
HiddenInput = forms.HiddenInput
RadioSelect = forms.RadioSelect
Select = forms.Select
TextInput = forms.TextInput
Textarea = forms.Textarea

# The standard error classes should be available to all importing modules
ValidationError = forms.ValidationError


class RadioInput(forms.RadioInput):
  """The rendering customization to be used for individual radio elements.
  """

  def __unicode__(self):
    if 'id' in self.attrs:
      label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
    else:
      label_for = ''
    choice_label = conditional_escape(force_unicode(self.choice_label))
    return mark_safe(
        u'%s <label%s>%s</label>' % (
        self.tag(), label_for, choice_label))


class RadioFieldRenderer(forms.RadioFieldRenderer):
  """The rendering customization to use the Uniform CSS on radio fields.
  """

  def __iter__(self):
    for i, choice in enumerate(self.choices):
      yield RadioInput(self.name, self.value, self.attrs.copy(), choice, i)

  def render(self):
    """Outputs the enclosing <div> for this set of radio fields.
    """
    return mark_safe(u'<div class="form-radio">%s</div>' % u'\n'.join([
        u'<div id="form-row-radio-%s" class="form-radio-item">%s</div>'
        % (w.attrs.get('id', ''), force_unicode(w)) for w in self]))


class CheckboxSelectMultiple(forms.CheckboxSelectMultiple):
  def render(self, name, value, attrs=None, choices=()):
    if value is None:
      value = []
    has_id = attrs and 'id' in attrs
    final_attrs = self.build_attrs(attrs, name=name)
    output = [u'<div class="form-checkbox">']
    # Normalize to strings
    str_values = set([force_unicode(v) for v in value])
    for i, (option_value, option_label) in enumerate(
        itertools.chain(self.choices, choices)):
      # If an ID attribute was given, add a numeric index as a suffix,
      # so that the checkboxes don't all have the same ID attribute.
      if has_id:
        final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
        label_for = u' for="%s"' % final_attrs['id']
      else:
        label_for = ''

      cb = forms.CheckboxInput(
          final_attrs, check_test=lambda value: value in str_values)
      option_value = force_unicode(option_value)
      rendered_cb = cb.render(name, option_value)
      option_label = conditional_escape(force_unicode(option_label))
      output.append(
          u'<div id="form-row-checkbox-%s" class="form-checkbox-item">'
          '%s<label%s>%s</label></div>' % (
          final_attrs['id'], rendered_cb, label_for, option_label))
    output.append(u'</div>')
    return mark_safe(u'\n'.join(output))


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

  class Meta(org_app.OrgAppEditForm.Meta):
    pass

  def __init__(self, *args, **kwargs):
    super(OrgAppEditForm, self).__init__(
        GCIBoundField, *args, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class OrgAppTakeForm(org_app.OrgAppTakeForm):
  """Form for would-be organization admins to apply for a GCI program.
  """

  CHECKBOX_SELECT_MULTIPLE = CheckboxSelectMultiple

  RADIO_FIELD_RENDERER = RadioFieldRenderer

  class Meta(org_app.OrgAppTakeForm.Meta):
    pass

  def __init__(self, survey, tos_content, *args, **kwargs):
    super(OrgAppTakeForm, self).__init__(
        survey, tos_content, GCIBoundField, *args, **kwargs)

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

    return mark_safe('%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
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
    } if getattr(self.field, '_file', False) else ""

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
    return '<label class="form-label">%s%s%s</label>' % (
        self.field.label,
        self._render_is_required(),
        self._render_error(),
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
