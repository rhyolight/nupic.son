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

"""Module containing the views for GCI documents page."""

from melange.request import access
from melange.request import exception
from soc.models import document as document_model
from soc.views import document
from soc.views.helper import url_patterns

from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views import forms
#from soc.modules.gci.views.base_templates import ProgramSelect
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns


class GCIDocumentForm(document.DocumentForm):
  """Django form for creating documents."""

  def __init__(self, **kwargs):
    super(GCIDocumentForm, self).__init__(forms.GCIBoundField, **kwargs)

  def templatePath(self):
    return 'modules/gci/_form.html'

  dashboard_visibility = forms.MultipleChoiceField(
      required=False,
      choices=[(c.identifier, c.verbose_name)
          for c in document_model.Document.DASHBOARD_VISIBILITIES],
      widget=forms.CheckboxSelectMultiple)

  Meta = document.DocumentForm.Meta


class EditDocumentPage(GCIRequestHandler):
  """Encapsulate all the methods required to edit documents.
  """

  def templatePath(self):
    return 'modules/gci/document/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'document/edit/%s$' % gci_url_patterns.DOCUMENT, self,
            name='edit_gci_document'),
        url(r'document/edit/%s$' % gci_url_patterns.ORG_DOCUMENT, self,
            name='edit_gci_document'),
    ]

  def checkAccess(self, data, check, mutator):
    check.canEditDocument()

  def context(self, data, check, mutator):
    form = GCIDocumentForm(data=data.POST or None, instance=data.document)

    # TODO(daniel): split that view into two different views (one for creation
    # and another one for editing documents) than make data.document raise
    # not found when document is not found
    if data.document:
      page_name = 'Edit %s' % data.document.title
    else:
      page_name = 'Create new Document'

    return {
        'page_name': page_name,
        'document_form': form,
    }

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    form = GCIDocumentForm(data=data.POST or None, instance=data.document)
    entity = document.validateForm(data, form)
    if entity:
      data.redirect.document(entity)
      # TODO(nathaniel): Self-redirection?
      return data.redirect.to('edit_gci_document')
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)


class DocumentPage(GCIRequestHandler):
  """Encapsulate all the methods required to show documents.
  """

  def templatePath(self):
    return 'modules/gci/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'document/show/%s$' % gci_url_patterns.DOCUMENT, self,
            name='show_gci_document'),
        url(r'document/show/%s$' % gci_url_patterns.ORG_DOCUMENT, self,
            name='show_gci_document'),
    ]

  def checkAccess(self, data, check, mutator):
    check.canViewDocument()

  def context(self, data, check, mutator):
    return {
        'tmpl': document.Document(data, data.document),
        'page_name': data.document.title,
    }


class EventsPage(GCIRequestHandler):
  """Encapsulates all the methods required to show the events page.
  """

  def templatePath(self):
    return 'modules/gci/document/events.html'

  def djangoURLPatterns(self):
    return [
        url(r'events/%s$' % url_patterns.PROGRAM, self,
            name='gci_events')
    ]

  def checkAccess(self, data, check, mutator):
    data.document = data.program.events_page
    check.canViewDocument()

  def context(self, data, check, mutator):
    return {
        'document': data.program.events_page,
        'frame_url': data.program.events_frame_url,
        'page_name': 'Events and Timeline',
    }


class GCIDocumentList(document.DocumentList):
  """Template for list of documents."""

  def __init__(self, data):
    super(GCIDocumentList, self).__init__(data, 'edit_gci_document')

  def templatePath(self):
    return 'modules/gci/document/_document_list.html'


class DocumentListPage(GCIRequestHandler):
  """View for the list documents page."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/document/document_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'documents/%s$' % url_patterns.PROGRAM, self,
            name='list_gci_documents'),
    ]

  def jsonContext(self, data, check, mutator):
    list_content = GCIDocumentList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Documents for %s" % data.program.name,
        'document_list': GCIDocumentList(data),
#        'program_select': ProgramSelect(data, 'list_gci_documents'),
    }
