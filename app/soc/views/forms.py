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

"""Module containing the boiler plate required to construct templates."""

import copy
import collections
import datetime
import itertools
import re

from google.appengine.api import datastore_errors
from google.appengine.ext import db

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.template import loader
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

from djangoforms import djangoforms

from soc.views.helper import surveys


def choiceWidget(field):
  """Returns a Select widget for the specified field.
  """
  choices = _generateChoices(field)
  label = field.verbose_name
  choices = [('', label)] + choices
  return forms.Select(choices=choices)


def _generateChoices(field):
  """Generates possible choices from a Model field.
  """
  choices = []
  for choice in field.choices:
    choices.append((str(choice), unicode(choice)))
  return choices


def choiceWidgets(model, fields):
  """Returns a dictionary of Select widgets for the specified fields.
  """
  return dict((i, choiceWidget(getattr(model, i))) for i in fields)


def hiddenWidget():
  """Returns a HiddenInput widget for the specified field.
  """
  return forms.HiddenInput()


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


class LabelVerificationNotRequiredState(object):
  """Represents the state where the AsyncFileField does not require
  verification label.
  """

  def toBeVerifiedHide(self):
    """ "To be verified" label should be hidden."""
    return 'button-hide'

  def verifiedHide(self):
    """ "Verified" label should be hidden."""
    return 'button-hide'


class LabelToBeVerifiedState(object):
  """Represents the state where the AsyncFileField should display the to be
  verified label.
  """

  def toBeVerifiedHide(self):
    """ "To be verified" label should be displayed (not hidden)."""
    return ''

  def verifiedHide(self):
    """ "Verified" label should be hidden."""
    return 'button-hide'


class LabelVerifiedState(object):
  """Represents the state where the AsyncFileField should display the verified
  label.
  """

  def toBeVerifiedHide(self):
    """ "To be verified" label should be hidden."""
    return 'button-hide'

  def verifiedHide(self):
    """ "Verified" label should be displayed (not hidden)."""
    return ''


# The standard input fields should be available to all importing modules
CharField = forms.CharField
CheckboxInput = forms.CheckboxInput
ChoiceField = forms.ChoiceField
DateInput = forms.DateInput
DateTimeInput = forms.DateTimeInput
FileField = forms.FileField
FileInput = forms.FileInput
HiddenInput = forms.HiddenInput
MultipleChoiceField = forms.MultipleChoiceField
RadioSelect = forms.RadioSelect
Select = forms.Select
SelectMultiple = forms.SelectMultiple
TextInput = forms.TextInput
Textarea = forms.Textarea

# The standard error classes should be available to all importing modules
ValidationError = forms.ValidationError


class AsyncFileInput(FileInput):
  """HTML field to be rendered for asynchronous file uploads.
  """

  def __init__(self, *args, **kwargs):
    self.download_url = kwargs.pop('download_url', None)

    # This mutation to kwargs is *required* because Django will complain
    # if you pass the kwargs that its widgets don't understand.
    verified = kwargs.pop('verified', None)

    # When there is no need for the files uploaded to be verified or when
    # such a feature is not required on the UI, this widget should neither
    # display the "verified" nor "to-be-verfied" label. So there is no need
    # for the underlying data model to also store the state. Which effectively
    # means that when this form field widget is constructed and the labels
    # are not required, the model does not know anything about the verfied
    # state and does not tell us anything. Thich is represented by "verified"
    # argument not being present in the keyword arguments to the constructor.
    # However, when there is a need for such a label, the underlying data
    # stores whether the file corresponding to this widget is verified or
    # not and that is represented by "True" and "False" values to the
    # "verified" keyword argument. And these states are translated into
    # classes here.
    if verified is None:
      self.verification = LabelVerificationNotRequiredState()
    elif not verified:
      self.verification = LabelToBeVerifiedState()
    else:
      self.verification = LabelVerifiedState()

    super(AsyncFileInput, self).__init__(*args, **kwargs)

  def render(self, name, value, attrs=None):
    download_hide = 'button-hide'
    upload_hide = ''

    to_be_verified_hide = self.verification.toBeVerifiedHide()
    verified_hide = self.verification.verifiedHide()

    if value is None:
      value = ''
    final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
    if value != '':
      # Only add the 'value' attribute if a value is non-empty.
      final_attrs['value'] = force_unicode(self._format_value(value.filename))
      download_hide = ''
      upload_hide = 'button-hide'

    iparams = u''.join([u' %s=%s' % (
        k, conditional_escape(v)) for k, v in final_attrs.items()])

    context = {
        'dhide': download_hide,
        'uhide': upload_hide,
        'verified_hide': verified_hide,
        'to_be_verified_hide': to_be_verified_hide,
        'durl': self.download_url,
        'fname': final_attrs.get('value', ''),
        'iparams': iparams,
        }

    rendered = loader.render_to_string(
        self.templatePath(), dictionary=context)

    # markup for buttons taken from bootstrap
    return mark_safe(rendered)

  def templatePath(self):
    return 'soc/_async_file_input_field.html'


class RadioInput(forms.widgets.RadioInput):
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


class RadioFieldRenderer(forms.widgets.RadioFieldRenderer):
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


class CheckboxSelectMultiple(SelectMultiple):
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

      cb = forms.CheckboxInput(
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


class ReferenceWidget(forms.TextInput):
  """Extends Django's TextInput widget to render the needed extra input field.
  """
  pass


class DocumentWidget(ReferenceWidget):
  """Extends the Django's TextInput widget to render the edit link to Documents.
  """
  pass


class TOSWidget(forms.CheckboxInput):
  """Widget that renders both the checkbox and the readonly text area.
  """

  def __init__(self, tos_text=None, attrs=None, check_test=bool):
    self.tos_text = tos_text
    super(TOSWidget, self).__init__(attrs, check_test)

  def render(self, name, value, attrs=None):
    readonly_attrs = {
        'id': 'tos-content',
        'class': 'tos',
        }
    if self.tos_text:
      text = mark_safe(
          u'<div id="tos-readonly-%s"><div %s>%s</div></div>' % (
          name, forms.util.flatatt(readonly_attrs),
          conditional_escape(mark_safe(force_unicode(self.tos_text)))))
    else:
      text = mark_safe(
          u'<div id="tos-readonly-%s">Terms of Agreement content is not set.</div>')

    checkbox = super(TOSWidget, self).render(name, value, attrs)
    return mark_safe(u'%s%s' % (text, checkbox))


class ReadonlyWidget(object):
  """Widget that renders text in read-only mode inside a form.
  """

  def __init__(self, text=None, attrs=None):
    self.text = text
    #super(ReadonlyWidget, self).__init__(attrs)

  def render(self, name, value, attrs=None):
    readonly_attrs = {
        'class': 'tos'
        }
    text = mark_safe(
        u'<div id="readonly-%s"><div %s>%s</div></div>' % (
        name, forms.util.flatatt(readonly_attrs),
        conditional_escape(mark_safe(force_unicode(self.text)))))

    return text


class ReferenceProperty(djangoforms.ReferenceProperty):
  # ReferenceProperty field allows setting to None.

  __metaclass__ = djangoforms.monkey_patch

  def get_form_field(self):
    """Return a Django form field appropriate for a reverse reference.

    This defaults to a CharField instance.
    """
    from soc.models.document import Document

    if self.data_type is Document:
      return forms.CharField(required=self.required,
                             widget=DocumentWidget)
    else:
      return forms.CharField(required=self.required,
                             widget=ReferenceWidget)

  def make_value_from_form(self, value):
    """Convert a value submitted in a form to a property value that is allowed
    for ReferenceProperty.

    If the specified value is a string (or unicode) representation of
    a datastore key is transformed into an actual instance of db.Key.

    If the specified value is an instance of db.Key or db.Model, it is returned
    as is.

    None if returned if the specified value is the empty string. It means that
    a user does not want to specify any value for this property.

    Returns:
      Value to be set for the ReferenceProperty as described above.
    """
    if not value:
      return None
    if isinstance(value, unicode):
      try:
        return db.Key(value)
      except datastore_errors.BadKeyError:
        raise forms.ValidationError(
            'Supplied unicode representation of db.Key is not valid. '
            'Found: %s' % value)
    elif not isinstance(value, db.Model) and not isinstance(value, db.Key):
      raise forms.ValidationError(
          u'Value for reference property must be either an instance of '
          'db.Model or db.Key. Found: %s' % type(value))
    else:
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
    declared_fields = SortedDict()
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
      raise ImproperlyConfigured(
          "%s's base classes define more than one model." % class_name)

    if opts.model is not None:
      if base_models and base_models[0] is not opts.model:
        raise ImproperlyConfigured(
            '%s defines a different model than its parent.' % class_name)

      model_fields = SortedDict()
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
          def clean_for_property_field(value, initial=None, prop=prop,
                                       old_clean=field.clean):
            value = old_clean(value)
            djangoforms.property_clean(prop, value)
            return value
          field.clean = clean_for_property_field
    else:
      attrs['base_fields'] = declared_fields

    # We're intentionally not calling our super's __new__ method, but we _do_
    # want call the __new__ method on its super class (which is type).
    # pylint: disable=bad-super-call
    return super(djangoforms.ModelFormMetaclass, cls).__new__(cls,
                                                  class_name, bases, attrs)

class ModelForm(djangoforms.ModelForm):
  """Django ModelForm class which uses our implementation of BoundField.
  """

  __metaclass__ = ModelFormMetaclass

  def __init__(self, bound_field_class, name=None, **kwargs):
    """Fixes label and help_text issues after parent initialization.

    Args:
      name: a string containing name of the form.
      **kwargs:  passed through to parent __init__() constructor
    """
    assert bound_field_class
    assert issubclass(bound_field_class, BoundField)
    self.__bound_field_class = bound_field_class
    self._name = name

    # We're intentionally not calling our super's __init__ method, but we _do_
    # want call the __init__ method on its super class (which is BaseModelForm).
    # pylint: disable=bad-super-call
    super(djangoforms.ModelForm, self).__init__(**kwargs)

    renames = {
        'verbose_name': 'label',
        'help_text': 'help_text',
        'group': 'group',
        }

    opts = ModelFormOptions(getattr(self, 'Meta', None))

    for field_name in self.fields.iterkeys():
      field = self.fields[field_name]

      # Since fields can be added only to the ModelForm subclass, check to
      # see if the Model has a corresponding field first.
      if not hasattr(opts.model, field_name):
        continue

      model_prop = getattr(opts.model, field_name)

      for old, new in renames.iteritems():
        value = getattr(model_prop, old, None)
        if value and not getattr(field, new, None):
          setattr(field, new, value)

    for field_name in opts.exclude or []:
      if field_name in self.fields:
        del self.fields[field_name]

  def __iter__(self):
    grouping = collections.defaultdict(list)

    for name, field in self.fields.items():
      bound = self.__bound_field_class(self, field, name)
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
      parent: instance or Key instance for the entity that is the new
        entity's parent; None by default

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

    converted_data = {}
    for name, prop in opts.model.properties().iteritems():
      value = self.cleaned_data.get(name)
      if value is not None:
        converted_data[name] = prop.make_value_from_form(value)
    try:
      instance = opts.model(key_name=key_name, parent=parent, **converted_data)
      self.instance = instance
    except db.BadValueError as err:
      raise ValueError('The %s could not be created (%s)' %
                       (opts.model.kind(), err))
    if commit:
      instance.put()
    return instance

  def asDict(self):
    """Returns a dictionary that maps all the form fields with
    the corresponding values.

    Please note that a copy of the internal structure is returned, so
    modifications made to it are not reflected in the form data.

    Returns:
      a dictionary mapping all the fields with the values.
    """
    return copy.deepcopy(self.cleaned_data)

  def render(self):
    """Renders the template to a string.

    Uses the context method to retrieve the appropriate context, uses the
    self.templatePath() method to retrieve the template that should be used.
    """

    context = {
      'form': self,
    }

    rendered = loader.render_to_string(
        self.templatePath(), dictionary=context)

    return rendered

  def idSuffix(self, field):
    return ""

  def name(self):
    """Returns name of the form.

    Returns:
      name of the form.
    """
    return self._name

  def _getPropertiesForFields(self, field_keys):
    """Maps fields specified by their keys to the corresponding values
    that were submitted in the form data.

    Fields, for which the empty string was received as their value, will be
    mapped to None. This is because an occurrence of the empty string is
    regarded as if the user did not specify any actual value for the field.

    Not only are explicit None values more straightforward, but also
    there are more convenient to be persisted in AppEngine datastore.

    Args:
      form: A form.
      field_keys: A collection of identifiers of the form fields.

    Returns:
      A dict mapping the specified keys to their values.
    """
    return {
        field_key: field_value
        for field_key, field_value in self.cleaned_data.iteritems()
        if field_key in field_keys and field_value != ''
    }


class SurveyEditForm(ModelForm):
  """Django form for creating and/or editing survey.
  """

  schema = forms.CharField(widget=forms.HiddenInput())


OTHER_OPTION_FIELD_ID = '%s-other'

class SurveyTakeForm(ModelForm):
  """Django form for taking a survey.
  """

  CHECKBOX_SELECT_MULTIPLE = CheckboxSelectMultiple

  RADIO_FIELD_RENDERER = RadioFieldRenderer

  def __init__(self, bound_field_class, survey=None, **kwargs):
    super(SurveyTakeForm, self).__init__(bound_field_class, **kwargs)
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
        if field and isinstance(field.widget, forms.Textarea):
          value = db.Text(value)
        setattr(instance, name, value)

    if commit:
      instance.modified = datetime.datetime.now()
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
    additional_names = set(self.cleaned_data.keys() +
        self.instance.dynamic_properties())

    try:
      for name in additional_names:
        value = self.cleaned_data.get(name)
        field = self.fields.get(name, None)
        if field and isinstance(field.widget, forms.Textarea):
          value = db.Text(value)
        setattr(instance, name, value)
    except db.BadValueError as err:
      raise ValueError('The %s could not be updated (%s)' %
                       (opts.model.kind(), err))

    if commit:
      instance.modified = datetime.datetime.now()
      instance.put()
    return instance

  def constructForm(self):
    """Constructs the form based on the schema stored in the survey content
    """
    # insert dynamic survey fields
    if self.survey:
      survey_schema = surveys.SurveySchema(self.survey)
      for field in survey_schema:
        self.constructField(field)

  def constructField(self, field_obj):
    """Constructs the field for the given field metadata

    Args:
      field_obj: A survey field object containing all the meta data for the survey.
    """
    type = field_obj.getType()
    label = field_obj.getLabel()
    required = field_obj.isRequired()
    help_text = field_obj.getHelpText()

    field_name = field_obj.getFieldName()

    widget = None

    kwargs = {'label': label,
              'required': required,
              'help_text': help_text
              }

    if type == 'checkbox':
      field = forms.MultipleChoiceField
      widget = self.CHECKBOX_SELECT_MULTIPLE()
    elif type == 'radio':
      field = forms.ChoiceField
      widget = forms.RadioSelect(renderer=self.RADIO_FIELD_RENDERER)
    elif type == 'textarea':
      field = forms.CharField
      widget = forms.Textarea()
    elif type == 'input_text':
      field = forms.CharField
      kwargs['max_length'] = 500

    self.fields[field_name] = field(**kwargs)

    if widget:
      self.fields[field_name].widget = widget

    if isinstance(field_obj.getValues(), list):
      choices = field_obj.getChoices()

      if field_obj.requireOtherField():
        choices.append(('Other', 'Other'))
        ofn = '%s-other' % (field_name)
        self.fields[ofn] = forms.CharField(
            required=False, initial=getattr(self.instance, ofn, None),
            widget=forms.TextInput(attrs={'div_class':'other'}))

      self.fields[field_name].choices = choices
    if self.instance:
      self.fields[field_name].initial = getattr(
          self.instance, field_name, None)

  def getSurveyResponseProperties(self):
    """Returns answers to the survey questions that were submitted in this form.

    Returns:
      A dict mapping question identifiers to corresponding responses.
    """
    # list of field IDs that belong to the organization application
    field_ids = [field.field_id for field in surveys.SurveySchema(self.survey)]

    properties = {}
    for field_id, value in self.cleaned_data.iteritems():
      if field_id in field_ids:
        properties[field_id] = value

        # add possible value of 'other' option
        other_option_field_id = OTHER_OPTION_FIELD_ID % field_id
        if other_option_field_id in self.cleaned_data:
          properties[other_option_field_id] = self.cleaned_data[
              other_option_field_id]

    return properties


class BoundField(forms.forms.BoundField):
  """BoundField base class.
  """

  NOT_SUPPORTED_MSG_FMT = ugettext('Widget %s is not supported.')

  def idSuffix(self, field):
    return self.form.idSuffix(field)

  def is_required(self):
    return self.field.required

  def render(self):
    raise NotImplementedError
