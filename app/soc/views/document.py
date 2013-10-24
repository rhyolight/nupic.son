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

"""Module containing the template for documents."""


from soc.models import document as document_model
from soc.logic.helper import prefixes
from soc.views import forms
from soc.views import template
from soc.views.helper import lists


class DocumentForm(forms.ModelForm):
  """Django form for creating documents."""

  dashboard_visibility = forms.MultipleChoiceField(
      required=False,
      choices=[(c.identifier, c.verbose_name)
          for c in document_model.Document.DASHBOARD_VISIBILITIES],
      widget=forms.CheckboxSelectMultiple)

  def __init__(self, bound_field_class, **kwargs):
    super(DocumentForm, self).__init__(bound_field_class, **kwargs)
    if self.instance:
      self.initial['dashboard_visibility'] = self.instance.dashboard_visibility

  class Meta:
    model = document_model.Document
    exclude = [
        'scope', 'author', 'modified_by', 'prefix', 'home_for',
        'link_id', 'read_access', 'write_access', 'is_featured'
    ]


class Document(template.Template):
  def __init__(self, data, entity):
    assert(entity != None)
    self.data = data
    self.entity = entity

  def context(self):
    return {
        'content': self.entity.content,
        'title': self.entity.title,
    }

  def templatePath(self):
    return "soc/_document.html"


def validateForm(data, document_form):
  if not document_form.is_valid():
    return

  cleaned_data = document_form.cleaned_data
  cleaned_data['modified_by'] = data.user

  if data.document:
    document = document_form.save()
  else:
    prefix = data.kwargs['prefix']
    cleaned_data['link_id'] = data.kwargs['document']
    cleaned_data['author'] = data.user
    cleaned_data['prefix'] = prefix

    if prefix in ['gsoc_program', 'gci_program']:
      scope_key_name = '%s/%s' % (
          data.kwargs['sponsor'], data.kwargs['program'])
    else:
      scope_key_name = '%s/%s/%s' % (
          data.kwargs['sponsor'], data.kwargs['program'],
          data.kwargs['organization'])      
      
    cleaned_data['scope'] = prefixes.getScopeForPrefix(prefix, scope_key_name)
    document = document_form.create(key_name=data.key_name)

  return document


class DocumentList(template.Template):
  """Template for list of documents."""

  def __init__(self, data, edit_name):
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addSimpleColumn('link_id', 'Document ID', hidden=True)
    list_config.setRowAction(
        lambda e, *args: data.redirect.document(e).urlOf(edit_name))

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('title')

    self._list_config = list_config

  def context(self):
    description = 'List of documents for %s' % (
            self.data.program.name)

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list_configuration_response],
    }

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      q = document_model.Document.all()
      q.filter('scope', self.data.program)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, q, lists.keyStarter)

      return response_builder.build()
    else:
      return None
