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

from soc.logic.exceptions import AccessViolation
from soc.models.document import Document
from soc.views import document
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.forms import GCIModelForm
#from soc.modules.gci.views.base_templates import ProgramSelect
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns


class GCIDocumentForm(GCIModelForm):
  """Django form for creating documents.
  """

  class Meta:
    model = Document
    exclude = [
        'scope', 'scope_path', 'author', 'modified_by', 'prefix', 'home_for',
        'link_id', 'read_access', 'write_access', 'is_featured'
    ]


class EditDocumentPage(GCIRequestHandler):
  """Encapsulate all the methods required to edit documents.
  """

  def templatePath(self):
    return 'v2/modules/gci/document/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'document/edit/%s$' % gci_url_patterns.DOCUMENT, self,
            name='edit_gci_document'),
        url(r'document/edit/%s$' % gci_url_patterns.ORG_DOCUMENT, self,
            name='edit_gci_document'),
    ]

  def checkAccess(self):
    self.mutator.documentKeyNameFromKwargs()

    assert isSet(self.data.key_name)

    self.check.canEditDocument()

  def context(self):
    form = GCIDocumentForm(self.data.POST or None, instance=self.data.document)

    if self.data.document:
      page_name = 'Edit %s' % self.data.document.title
    else:
      page_name = 'Create new Document'

    return {
        'page_name': page_name,
        'document_form': form,
    }

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    form = GCIDocumentForm(data.POST or None, instance=data.document)
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
    return 'v2/modules/gci/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'document/show/%s$' % gci_url_patterns.DOCUMENT, self,
            name='show_gci_document'),
        url(r'document/show/%s$' % gci_url_patterns.ORG_DOCUMENT, self,
            name='show_gci_document'),
    ]

  def checkAccess(self):
    self.mutator.documentKeyNameFromKwargs()
    self.check.canViewDocument()

  def context(self):
    return {
        'tmpl': document.Document(self.data, self.data.document),
        'page_name': self.data.document.title,
    }


class EventsPage(GCIRequestHandler):
  """Encapsulates all the methods required to show the events page.
  """

  def templatePath(self):
    return 'v2/modules/gci/document/events.html'

  def djangoURLPatterns(self):
    return [
        url(r'events/%s$' % url_patterns.PROGRAM, self,
            name='gci_events')
    ]

  def checkAccess(self):
    self.data.document = self.data.program.events_page
    self.check.canViewDocument()

  def context(self):
    return {
        'document': self.data.program.events_page,
        'frame_url': self.data.program.events_frame_url,
        'page_name': 'Events and Timeline',
    }


class GCIDocumentList(document.DocumentList):
  """Template for list of documents."""

  def __init__(self, data):
    super(GCIDocumentList, self).__init__(data, 'edit_gci_document')

  def templatePath(self):
    return 'v2/modules/gci/document/_document_list.html'


class DocumentListPage(GCIRequestHandler):
  """View for the list documents page."""

  def templatePath(self):
    return 'v2/modules/gci/document/document_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'documents/%s$' % url_patterns.PROGRAM, self,
            name='list_gci_documents'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def jsonContext(self, data, check, mutator):
    list_content = GCIDocumentList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise AccessViolation('You do not have access to this data')

  def context(self):
    return {
        'page_name': "Documents for %s" % self.data.program.name,
        'document_list': GCIDocumentList(self.data),
#        'program_select': ProgramSelect(self.data, 'list_gci_documents'),
    }
