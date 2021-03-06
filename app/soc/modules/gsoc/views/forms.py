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


from google.appengine.ext import db

from django.core.urlresolvers import reverse
from django.template import defaultfilters
from django.utils import html
from django.utils.formats import dateformat
from django.utils.safestring import mark_safe

from soc.models import document as document_model
from soc.views import forms


TEMPLATE_PATH = 'modules/gsoc/_form.html'

# The standard input fields should be available to all importing modules
AsyncFileInput = forms.AsyncFileInput
CharField = forms.CharField
CheckboxInput = forms.CheckboxInput
CheckboxSelectMultiple = forms.CheckboxSelectMultiple
DateInput = forms.DateInput
DateTimeInput = forms.DateTimeInput
FileField = forms.FileField
FileInput = forms.FileInput
HiddenInput = forms.HiddenInput
MultipleChoiceField = forms.MultipleChoiceField
RadioFieldRenderer = forms.RadioFieldRenderer
RadioSelect = forms.RadioSelect
Select = forms.Select
TextInput = forms.TextInput
Textarea = forms.Textarea

# The standard error classes should be available to all importing modules
ValidationError = forms.ValidationError


class GSoCModelForm(forms.ModelForm):
  """Django ModelForm class which uses our implementation of BoundField.
  """

  def __init__(self, **kwargs):
    super(GSoCModelForm, self).__init__(GSoCBoundField, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class SurveyEditForm(forms.SurveyEditForm):
  """Django form for creating and/or editing survey.
  """

  def __init__(self, **kwargs):
    super(SurveyEditForm, self).__init__(GSoCBoundField, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH

  schema = forms.CharField(widget=forms.HiddenInput())


class SurveyTakeForm(forms.SurveyTakeForm):
  """Django form for taking a survey.
  """

  def __init__(self, survey=None, **kwargs):
    super(SurveyTakeForm, self).__init__(
        GSoCBoundField, survey=survey, **kwargs)

  def templatePath(self):
    return TEMPLATE_PATH


class GSoCBoundField(forms.BoundField):
  """GSoC specific BoundField representation.
  """

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
    elif isinstance(widget, forms.ReadonlyWidget):
      return self.renderReadonlyWidget()

    return self.NOT_SUPPORTED_MSG_FMT % (
        widget.__class__.__name__)

  def renderReferenceWidget(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
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
        'id': self.name + "-pretty" + self.idSuffix(self),
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

  def renderCheckboxInput(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
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
        'id': 'melange-%s-textarea%s' % (self.name, self.idSuffix(self)),
        'class': 'textarea'
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def renderTextInput(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
        'class': 'text',
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
      scope_key_name = document_model.Document.scope.get_value_for_datastore(
          document).name()
      sponsor, program = scope_key_name.split('/')
      args = [document.prefix, sponsor, program, document.link_id]
    else:
      scope_key_name = self.form.request_data.program.key().id_or_name()
      sponsor, program = scope_key_name.split('/')
      args = ['gsoc_program', sponsor, program, self.name]

    edit_document_link = reverse('edit_gsoc_document', args=args)
    self.help_text = """<a href="%s">Click here to edit this document.</a>
        <br />%s""" % (edit_document_link, self.help_text)

  def renderSelect(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
        'style': 'opacity: 100;',
        }

    return mark_safe('%s%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_is_required(),
        self._render_error(),
        self._render_note(),
    ))

  def renderTOSWidget(self):
    checkbox_attrs = {
        'id': self.name + self.idSuffix(self),
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

  def renderReadonlyWidget(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
        'style': 'opacity: 100;',
        }

    return mark_safe(
        '<label>%s</label>' % (
        self.as_widget(attrs=attrs),
        ))

  def renderHiddenInput(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
        'name': self.name,
        'type': 'hidden',
        'value': self.field.initial or '',
        }
    return self.as_widget(attrs=attrs)

  def renderFileInput(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
        }

    current_file_fmt = """
        <br/>
        <p>
        File: <a href="%(link)s">%(name)s</a><br/>
        Size: %(size)s <br/>
        Uploaded on: %(uploaded)s UTC
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
        'id': self.name + self.idSuffix(self),
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def renderCheckSelectMultiple(self):
    attrs = {
        'id': self.name + self.idSuffix(self),
        }

    return mark_safe('%s%s%s%s' % (
        self._render_label(),
        self.as_widget(attrs=attrs),
        self._render_error(),
        self._render_note(),
    ))

  def _render_label(self):
    return '<label>%s%s</label>' % (
        self.field.label,
        self._render_is_required(),
    ) if self.field.label else ''

  def _render_error(self):
    if self.errors:
      # TODO(nathaniel): HTML in Python.
      return html.format_html(
          u'<div class="error-message">{0}</div>', self.errors[0])
    else:
      return ''

  def _render_is_required(self):
    if not self.field.required:
      return ''

    return '<span class="req">*</span>'

  def _render_note(self, note=None):
    return '<span class="note">%s</span>' % (
        note if note else self.help_text)

  def div_class(self):
    if hasattr(self.form, 'Meta'):
      prefix = getattr(self.form.Meta, 'css_prefix', None)
    else:
      prefix = None

    name = prefix + '_' + self.name if prefix else self.name

    widget_div_class = self.field.widget.attrs.get('div_class', None)
    if widget_div_class:
      name = '%s %s' % (widget_div_class, name)

    if self.errors:
      name += ' error'
    return name
