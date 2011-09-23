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

"""Module containing the views for GCI documents page.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from soc.logic.exceptions import AccessViolation
from soc.views import document
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.modules.gci.views.base import RequestHandler
#from soc.modules.gci.views.base_templates import ProgramSelect
from soc.modules.gci.views.helper.url_patterns import url


class EditDocumentPage(RequestHandler):
  """Encapsulate all the methods required to edit documents.
  """

  def templatePath(self):
    return 'v2/modules/gci/document/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'document/edit/%s$' % url_patterns.DOCUMENT, self,
            name='edit_gci_document')
    ]

  def checkAccess(self):
    self.mutator.documentKeyNameFromKwargs()

    assert isSet(self.data.key_name)

    self.check.canEditDocument()

  def context(self):
    form = document.DocumentForm(
        self.data.POST or None, instance=self.data.document)

    return {
        'page_name': 'Edit document',
        'document_form': form,
    }

  def post(self):
    """Handler for HTTP POST request.
    """
    entity = document.validateForm(self.data)
    if entity:
      self.redirect.document(entity)
      self.redirect.to('edit_gci_document')
    else:
      self.get()


class DocumentPage(RequestHandler):
  """Encapsulate all the methods required to show documents.
  """

  def templatePath(self):
    return 'v2/modules/gci/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'document/show/%s$' % url_patterns.DOCUMENT, self,
            name='show_gci_document'),
    ]

  def checkAccess(self):
    self.mutator.documentKeyNameFromKwargs()
    self.check.canViewDocument()

  def context(self):
    return {
        'tmpl': document.Document(self.data, self.data.document),
        'page_name': 'Document',
    }


class EventsPage(RequestHandler):
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


class DocumentList(document.DocumentList):
  """Template for list of documents.
  """

  def __init__(self, request, data):
    super(DocumentList, self).__init__(request, data, 'edit_gci_document')

  def templatePath(self):
    return 'v2/modules/gci/document/_document_list.html'


class DocumentListPage(RequestHandler):
  """View for the list documents page.
  """

  def templatePath(self):
    return 'v2/modules/gci/document/document_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'documents/%s$' % url_patterns.PROGRAM, self,
            name='list_gci_documents'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def jsonContext(self):
    list_content = DocumentList(self.request, self.data).getListData()

    if not list_content:
      raise AccessViolation('You do not have access to this data')
    return list_content.content()

  def context(self):
    return {
        'page_name': "Documents for %s" % self.data.program.name,
        'document_list': DocumentList(self.request, self.data),
#        'program_select': ProgramSelect(self.data, 'list_gci_documents'),
    }
