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

"""Tests for program related views."""

from soc.models.document import Document

from tests.test_utils import GSoCDjangoTestCase

# TODO: perhaps we should move this out?
from soc.modules.seeder.logic.seeder import logic as seeder_logic
from soc.modules.seeder.logic.providers.string import DocumentKeyNameProvider


class ListDocumentTest(GSoCDjangoTestCase):
  """Test document list page."""

  def setUp(self):
    self.init()
    self.profile_helper.createHost()

  def testListDocument(self):
    url = '/gsoc/documents/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertGSoCTemplatesUsed(response)

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))


class EditProgramTest(GSoCDjangoTestCase):
  """Tests program edit page."""

  def setUp(self):
    self.init()
    self.profile_helper.createUser()
    self.document = self.createDocument()

  def testShowDocument(self):
    url = '/gsoc/document/show/' + self.document.key().name()
    response = self.get(url)
    self.assertGSoCTemplatesUsed(response)

  def testCreateDocumentRestriction(self):
    # TODO(SRabbelier): test document ACL
    pass

  def testCreateDocumentWithDashboardVisibility(self):
    self.profile_helper.createHost()
    url = '/gsoc/document/edit/gsoc_program/%s/doc' % self.gsoc.key().name()
    response = self.get(url)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/document/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

    # test POST
    override = {
        'prefix': 'gsoc_program', 'scope': self.gsoc, 'link_id': 'doc',
        'key_name': DocumentKeyNameProvider(),
        'modified_by': self.profile_helper.user,
        'home_for': None,
        'author': self.profile_helper.user, 'is_featured': None,
        'write_access': 'admin', 'read_access': 'public',
        'dashboard_visibility': ['student', 'mentor'],
    }
    properties = seeder_logic.seed_properties(Document, properties=override)
    response = self.post(url, properties)
    self.assertResponseRedirect(response, url)

    key_name = properties['key_name']
    document = Document.get_by_key_name(key_name)
    self.assertPropertiesEqual(properties, document)

  def testCreateDocumentNoDashboardVisibility(self):
    self.profile_helper.createHost()
    url = '/gsoc/document/edit/gsoc_program/%s/doc' % self.gsoc.key().name()
    response = self.get(url)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/document/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

    # test POST
    override = {
        'prefix': 'gsoc_program', 'scope': self.gsoc, 'link_id': 'doc',
        'key_name': DocumentKeyNameProvider(),
        'modified_by': self.profile_helper.user,
        'home_for': None,
        'author': self.profile_helper.user, 'is_featured': None,
        'write_access': 'admin', 'read_access': 'public',
        'dashboard_visibility': [],
    }
    properties = seeder_logic.seed_properties(Document, properties=override)
    response = self.post(url, properties)
    self.assertResponseRedirect(response, url)

    key_name = properties['key_name']
    document = Document.get_by_key_name(key_name)
    self.assertPropertiesEqual(properties, document)


class EventsPageTest(GSoCDjangoTestCase):
  """Tests the events page."""

  def setUp(self):
    self.init()

  def testEventsPageLoads(self):
    response = self.get('/gsoc/events/%s' % self.gsoc.key().name())
    self.assertResponseOK(response)
    self.assertEqual(response.context['page_name'],'Events and Timeline')
    self.assertTemplateUsed(response, 'modules/gsoc/document/events.html')
    self.assertGSoCTemplatesUsed(response)
