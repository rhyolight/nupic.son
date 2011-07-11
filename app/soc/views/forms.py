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
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import collections
import itertools
import re
import urllib

from google.appengine.ext import db
from google.appengine.ext.db import djangoforms

from django.core.urlresolvers import reverse
from django.forms import forms
from django.forms import widgets
from django.forms.util import flatatt
from django.template import defaultfilters
from django.template import loader
from django.utils.encoding import force_unicode
from django.utils.formats import dateformat
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.simplejson import loads
from django.utils.translation import ugettext

import django


def choiceWidget(field):
  """Returns a Select widget for the specified field.
  """
  label = field.verbose_name

  choices = []
  choices.append(('', label))
  for choice in field.choices:
    choices.append((str(choice), unicode(choice)))
  return widgets.Select(choices=choices)


def choiceWidgets(model, fields):
  """Returns a dictionary of Select widgets for the specified fields.
  """
  return dict((i, choiceWidget(getattr(model, i))) for i in fields)


def hiddenWidget():
  """Returns a HiddenInput widget for the specified field.
  """
  return widgets.HiddenInput()

def hiddenWidgets(model, fields):
  """Returns a dictionary of Select widgets for the specified fields.
  """
  return dict((i, hiddenWidget()) for i in fields)

def mergeWidgets(*args):
  """Merges a list of widgets.
  """

  widgets = dict()
  for widget in args:
    for k, v in widget.iteritems():
      widgets[k] = v

  return widgets


class RadioInput(widgets.RadioInput):
  """The rendering customization to be used for individual radio elements.
  """

  def __unicode__(self):
    if 'id' in self.attrs:
      label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
    else:
      label_for = ''
    choice_label = conditional_escape(force_unicode(self.choice_label))
    return mark_safe(
        u'<label%s>%s <div class="radio-content">%s</div></label>' % (
        label_for, self.tag(), choice_label))



class RadioFieldRenderer(widgets.RadioFieldRenderer):
  """The rendering customization to use the Uniform CSS on radio fields.
  """

  def __iter__(self):
    for i, choice in enumerate(self.choices):
      yield RadioInput(self.name, self.value, self.attrs.copy(), choice, i)

  def render(self):
    """Outputs a <ul> for this set of radio fields.
    """
    return mark_safe(
        u'%s' % u'\n'.join([
        u'<div id="form-row-radio-%s" class="row radio">%s</div>'
        % (w.attrs.get('id', ''), force_unicode(w)) for w in self]))


class CheckboxSelectMultiple(widgets.SelectMultiple):
  def render(self, name, value, attrs=None, choices=()):
    if value is None:
      value = []
    has_id = attrs and 'id' in attrs
    final_attrs = self.build_attrs(attrs, name=name)
    output = [u'<div>']
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

      cb = widgets.CheckboxInput(
          final_attrs, check_test=lambda value: value in str_values)
      option_value = force_unicode(option_value)
      rendered_cb = cb.render(name, option_value)
      option_label = conditional_escape(force_unicode(option_label))
      output.append(
          u'<div id="form-row-radio-%s" class="row checkbox"><label%s>%s '
          '<div class="checkbox-content">%s</div></label></div>' % (
          final_attrs['id'], label_for, rendered_cb, option_label))
    output.append(u'</div>')
    return mark_safe(u'\n'.join(output))


class ReferenceWidget(widgets.TextInput):
  """Extends Django's TextInput widget to render the needed extra input field.
  """
  pass


class DocumentWidget(ReferenceWidget):
  """Extends the Django's TextInput widget to render the edit link to Documents.
  """
  pass


class TOSWidget(widgets.CheckboxInput):
  """Widget that renders both the checkbox and the readonly text area.
  """

  def __init__(self, tos_text=None, attrs=None, check_test=bool):
    self.tos_text = tos_text
    super(TOSWidget, self).__init__(attrs, check_test)

  def render(self, name, value, attrs=None):
    readonly_attrs = {
        'id': 'tos-content',
        }
    if self.tos_text:
      text = mark_safe(
          u'<div id="tos-readonly-%s"><div %s>%s</div></div>' % (
          name, flatatt(readonly_attrs),
          conditional_escape(mark_safe(force_unicode(self.tos_text)))))
    else:
      text = mark_safe(
          u'<div id="tos-readonly-%s">Terms of Agreement content is not set.</div>')

    checkbox = super(TOSWidget, self).render(name, value, attrs)
    return mark_safe(u'%s%s' % (text, checkbox))


class ReferenceProperty(djangoforms.ReferenceProperty):
  # ReferenceProperty field allows setting to None.

  __metaclass__ = djangoforms.monkey_patch

  def get_form_field(self):
    """Return a Django form field appropriate for a reverse reference.

    This defaults to a CharField instance.
    """
    from soc.models.document import Document

    if self.data_type is Document:
      return django.forms.CharField(required=self.required,
                                    widget=DocumentWidget)
    else:
      return django.forms.CharField(required=self.required,
                                    widget=ReferenceWidget)

  def make_value_from_form(self, value):
    """Convert a form value to a property value.

    This turns a key string or object into a model instance.
    Returns None if value is ''.
    """

    if not value:
      return None
    if not isinstance(value, db.Model):
      try:
        value = db.get(value)
      except db.BadKeyError, e:
        raise forms.ValidationError(unicode(e))
    return value


class ModelFormOptions(object):
  """A simple class to hold internal options for a ModelForm class.

  Instance attributes:
    model: a db.Model class, or None
    fields: list of field names to be defined, or None
    exclude: list of field names to be skipped, or None
    widgets: dictionary of widgets to be used per field, or None

  These instance attributes are copied from the 'Meta' class that is
  usually present in a ModelForm class, and all default to None.
  """


  def __init__(self, options=None):
    self.model = getattr(options, 'model', None)
    self.fields = getattr(options, 'fields', None)
    self.exclude = getattr(options, 'exclude', None)
    self.widgets = getattr(options, 'widgets', None)


class ModelFormMetaclass(djangoforms.ModelFormMetaclass):
  """The metaclass for the ModelForm class defined below.

  This is our analog of Django's own ModelFormMetaclass.  (We
  can't conveniently subclass that class because there are quite a few
  differences.)

  See the docs for ModelForm below for a usage example.
  """

  def __new__(cls, class_name, bases, attrs):
    """Constructor for a new ModelForm class instance.

    The signature of this method is determined by Python internals.

    All Django Field instances are removed from attrs and added to
    the base_fields attribute instead.  Additional Field instances
    are added to this based on the Datastore Model class specified
    by the Meta attribute.
    """
    fields = sorted(((field_name, attrs.pop(field_name))
                     for field_name, obj in attrs.items()
                     if isinstance(obj, forms.Field)),
                     key=lambda obj: obj[1].creation_counter)
    for base in bases[::-1]:
      if hasattr(base, 'base_fields'):
        fields = base.base_fields.items() + fields
    declared_fields = django.utils.datastructures.SortedDict()
    for field_name, obj in fields:
      declared_fields[field_name] = obj

    opts = ModelFormOptions(attrs.get('Meta', None))
    attrs['_meta'] = opts

    base_models = []
    for base in bases:
      base_opts = getattr(base, '_meta', None)
      base_model = getattr(base_opts, 'model', None)
      if base_model is not None:
        base_models.append(base_model)
    if len(base_models) > 1:
      raise django.core.exceptions.ImproperlyConfigured(
          "%s's base classes define more than one model." % class_name)

    if opts.model is not None:
      if base_models and base_models[0] is not opts.model:
        raise django.core.exceptions.ImproperlyConfigured(
            '%s defines a different model than its parent.' % class_name)

      model_fields = django.utils.datastructures.SortedDict()
      for name, prop in sorted(opts.model.properties().iteritems(),
                               key=lambda prop: prop[1].creation_counter):
        if opts.fields and name not in opts.fields:
          continue
        if opts.exclude and name in opts.exclude:
          continue
        form_field = prop.get_form_field()
        if form_field is not None:
          model_fields[name] = form_field
        if opts.widgets and name in opts.widgets:
          model_fields[name].widget = opts.widgets[name]

      model_fields.update(declared_fields)
      attrs['base_fields'] = model_fields

      props = opts.model.properties()
      for name, field in model_fields.iteritems():
        prop = props.get(name)
        if prop:
          def clean_for_property_field(value, prop=prop, old_clean=field.clean):
            value = old_clean(value)
            djangoforms.property_clean(prop, value)
            return value
          field.clean = clean_for_property_field
    else:
      attrs['base_fields'] = declared_fields

    return super(djangoforms.ModelFormMetaclass, cls).__new__(cls,
                                                  class_name, bases, attrs)

class ModelForm(djangoforms.ModelForm):
  """Django ModelForm class which uses our implementation of BoundField.
  """

  __metaclass__ = ModelFormMetaclass

  template_path = 'v2/modules/gsoc/_form.html'

  def __init__(self, *args, **kwargs):
    """Fixes label and help_text issues after parent initialization.

    Args:
      *args, **kwargs:  passed through to parent __init__() constructor
    """

    super(djangoforms.ModelForm, self).__init__(*args, **kwargs)

    renames = {
        'verbose_name': 'label',
        'help_text': 'help_text',
        'example_text': 'example_text',
        'group': 'group',
        }

    for field_name in self.fields.iterkeys():
      field = self.fields[field_name]

      # Since fields can be added only to the ModelForm subclass, check to
      # see if the Model has a corresponding field first.
      # pylint: disable=E1101
      if not hasattr(self.Meta.model, field_name):
        continue

      model_prop = getattr(self.Meta.model, field_name)

      for old, new in renames.iteritems():
        value = getattr(model_prop, old, None)
        if value and not getattr(field, new, None):
          setattr(field, new, value)

  def __iter__(self):
    grouping = collections.defaultdict(list)

    for name, field in self.fields.items():
      bound = BoundField(self, field, name)
      group = getattr(field, 'group', '0. ')
      grouping[group].append(bound)

    rexp = re.compile(r"\d+. ")

    for group, fields in sorted(grouping.items()):
      yield rexp.sub('', group), fields

  def create(self, commit=True, key_name=None, parent=None):
    """Save this form's cleaned data into a new model instance.

    Args:
      commit: optional bool, default True; if true, the model instance
        is also saved to the datastore.
      key_name: the key_name of the new model instance, default None
      parent: the parent of the new model instance, default None

    Returns:
      The model instance created by this call.
    Raises:
      ValueError if the data couldn't be validated.
    """
    if not self.is_bound:
      raise ValueError('Cannot save an unbound form')
    opts = self._meta
    instance = self.instance
    if self.instance:
      raise ValueError('Cannot create a saved form')
    if self.errors:
      raise ValueError("The %s could not be created because the data didn't "
                       'validate.' % opts.model.kind())
    cleaned_data = self._cleaned_data()
    converted_data = {}
    for name, prop in opts.model.properties().iteritems():
      value = cleaned_data.get(name)
      if value is not None:
        converted_data[name] = prop.make_value_from_form(value)
    try:
      instance = opts.model(key_name=key_name, parent=parent, **converted_data)
      self.instance = instance
    except db.BadValueError, err:
      raise ValueError('The %s could not be created (%s)' %
                       (opts.model.kind(), err))
    if commit:
      instance.put()
    return instance

  def render(self):
    """Renders the template to a string.

    Uses the context method to retrieve the appropriate context, uses the
    self.templatePath() method to retrieve the template that should be used.
    """

    context = {
      'form': self,
    }

    rendered = loader.render_to_string(self.template_path, dictionary=context)
    return rendered


class SurveyEditForm(ModelForm):
  """Django form for creating and/or editing survey.
  """

  schema = django.forms.CharField(widget=django.forms.HiddenInput())


class SurveyTakeForm(ModelForm):
  """Django form for taking a survey.
  """

  def __init__(self, survey, *args, **kwargs):
    super(SurveyTakeForm, self).__init__(*args, **kwargs)
    self.survey = survey
    self.constructForm()

  def create(self, commit=True, key_name=None, parent=None):
    """Save this form's cleaned data as dynamic properties of a new
    model instance.

    Args:
      commit: optional bool, default True; if true, the model instance
        is also saved to the datastore.
      key_name: the key_name of the new model instance, default None
      parent: the parent of the new model instance, default None

    Returns:
      The model instance created by this call.
    Raises:
      ValueError if the data couldn't be validated.
    """
    instance = super(SurveyTakeForm, self).create(
        commit=False, key_name=key_name, parent=parent)

    for name, value in self.cleaned_data.iteritems():
      # if the property is not to be updated, skip it
      if self._meta.exclude:
        if name in self._meta.exclude:
          continue
      if self._meta.fields:
        if name not in self._meta.fields:
          continue

      # we do not want to set empty datastructures as property values,
      # however for boolean fields value itself can be False so this
      # or logic
      if value == False or value:
        # If the widget for the field that must be saved is a Textarea
        # widget use the Text property
        field = self.fields.get(name, None)
        if field and isinstance(field.widget, django.forms.Textarea):
          value = db.Text(value)
        setattr(instance, name, value)

    if commit:
      instance.put()
    return instance

  def save(self, commit=True):
    """Save this form's cleaned data into a model instance.

    Args:
      commit: optional bool, default True; if true, the model instance
        is also saved to the datastore.

    Returns:
      A model instance.  If a model instance was already associated
      with this form instance (either passed to the constructor with
      instance=...  or by a previous save() call), that same instance
      is updated and returned; if no instance was associated yet, one
      is created by this call.

    Raises:
      ValueError if the data couldn't be validated.
    """
    instance = super(SurveyTakeForm, self).save(commit=False)

    opts = self._meta
    cleaned_data = self._cleaned_data()
    additional_names = set(cleaned_data.keys() +
        self.instance.dynamic_properties())

    try:
      for name in additional_names:
        value = cleaned_data.get(name)
        field = self.fields.get(name, None)
        if field and isinstance(field.widget, django.forms.Textarea):
          value = db.Text(value)
        setattr(instance, name, value)
    except db.BadValueError, err:
      raise ValueError('The %s could not be updated (%s)' %
                       (opts.model.kind(), err))

    if commit:
      instance.put()
    return instance

  def constructForm(self):
    """Constructs the form based on the schema stored in the survey content
    """
    # insert dynamic survey fields
    if self.survey:
      order, fields = loads(self.survey.schema)
      for field_id in order:
        self.constructField(field_id, fields.get(field_id, {}))

  def constructField(self, field_name, field_dict):
    """Constructs the field for the given field metadata

    Args:
      field_name: Unique ID assigned to the field while creating it
      field_dict: Meta data containing how the field must be constructed
    """
    type = field_dict.get('field_type', '')
    label = urllib.unquote(field_dict.get('label', ''))
    required = field_dict.get('required', True)
    other = field_dict.get('other', False)
    help_text = field_dict.get('tip', '')
    values = field_dict.get('values', '')

    widget = None

    if type == 'checkbox':
      field = django.forms.MultipleChoiceField
      widget = CheckboxSelectMultiple()
    elif type == 'radio':
      field = django.forms.ChoiceField
      widget = django.forms.RadioSelect(renderer=RadioFieldRenderer)
    elif type == 'textarea':
      field = django.forms.CharField
      widget = django.forms.Textarea()
    elif type == 'input_text':
      field = django.forms.CharField

    self.fields[field_name] = field(label=label, required=required,
                                    help_text=help_text)
    if widget:
      self.fields[field_name].widget = widget

    if isinstance(values, list):
      choices = []
      for choice in values:
        value = urllib.unquote(choice.get('value'))
        choices.append((value, value))
        if choice['checked']:
          self.fields[field_name].initial = str(value)
      else:
        if other:
          choices.append(('Other', 'Other'))
          ofn = '%s-other' % (field_name)
          self.fields[ofn] = django.forms.CharField(
              required=False, initial=getattr(self.instance, ofn, None),
              widget=forms.TextInput(attrs={'div_class':'other'}))
      self.fields[field_name].choices = choices
    if self.instance:
      self.fields[field_name].initial = getattr(
          self.instance, field_name, None)


class BoundField(forms.BoundField):
  """
  """

  NOT_SUPPORTED_MSG_FMT = ugettext('Widget %s is not supported.')

  def is_required(self):
    return self.field.required

  def render(self):
    attrs = {
        'id': self.name
        }

    widget = self.field.widget

    if isinstance(widget, DocumentWidget):
      self.setDocumentWidgetHelpText()

    if isinstance(widget, ReferenceWidget):
      return self.renderReferenceWidget()
    elif isinstance(widget, TOSWidget):
      return self.renderTOSWidget()
    elif isinstance(widget, widgets.RadioSelect):
      return self.renderRadioSelect()
    elif isinstance(widget, CheckboxSelectMultiple):
      return self.renderCheckSelectMultiple()
    elif isinstance(widget, widgets.TextInput):
      return self.renderTextInput()
    elif isinstance(widget, widgets.DateInput):
      return self.renderTextInput()
    elif isinstance(widget, widgets.Select):
      return self.renderSelect()
    elif isinstance(widget, widgets.CheckboxInput):
      return self.renderCheckboxInput()
    elif isinstance(widget, widgets.Textarea):
      return self.renderTextArea()
    elif isinstance(widget, widgets.DateTimeInput):
      return self.renderTextInput()
    elif isinstance(widget, widgets.HiddenInput):
      return self.renderHiddenInput()
    elif isinstance(widget, widgets.FileInput):
      return self.renderFileInput()

    return self.NOT_SUPPORTED_MSG_FMT % (
        widget.__class__.__name__)

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
      from google.appengine.ext import db
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

  def setDocumentWidgetHelpText(self):
    value = self.form.initial.get(self.name, self.field.initial)

    if value:
      document = db.get(value)
      args = [document.prefix, document.scope_path + '/', document.link_id]
    else:
      scope_path = self.form.scope_path
      args = ['gsoc_program', scope_path + '/', self.name]

    edit_document_link = reverse('edit_gsoc_document', args=args)
    self.help_text = """<a href="%s">Click here to edit this document.</a>
        <br />%s""" % (edit_document_link, self.help_text)

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

  def _render_label(self):
    return '<label>%s%s</label>' % (
        self.field.label,
        self._render_is_required(),
    ) if self.field.label else ''

  def _render_error(self):
    if not self.errors:
      return ''

    return '<div class="error-message">%s</div>' % (
        self.errors[0])

  def _render_is_required(self):
    if not self.field.required:
      return ''

    return '<span class="req">*</span>'

  def _render_note(self, note=None):
    return '<span class="note">%s</span>' % (
        note if note else self.help_text)

  def div_class(self):
    prefix = getattr(self.form.Meta, 'css_prefix', None)
    name = prefix + '_' + self.name if prefix else self.name

    widget_div_class = self.field.widget.attrs.get('div_class', None)
    if widget_div_class:
      name = '%s %s' % (widget_div_class, name)

    if self.errors:
      name += ' error'
    return name
