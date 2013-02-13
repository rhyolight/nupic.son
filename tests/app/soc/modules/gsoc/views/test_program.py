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

"""Unit tests for program related views.
"""

from tests import test_utils

# TODO: perhaps we should move this out?
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class GSoCCreateProgramPageTest(test_utils.GSoCDjangoTestCase):
  """Tests GSoCCreateProgramPage view.
  """

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/program/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def setUp(self):
    self.init()

  def testLoneUserAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createStudent()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createMentor(self.org)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createOrgAdmin(self.org)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createHost()
    response = self.get(url)
    self.assertProgramTemplatesUsed(response)


class EditProgramTest(GSoCDjangoTestCase):
  """Tests program edit page.
  """

  def setUp(self):
    self.init()

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/program/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def testEditProgramHostOnly(self):
    url = '/gsoc/program/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testEditProgramAsDeveloper(self):
    self.data.createDeveloper()
    url = '/gsoc/program/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertProgramTemplatesUsed(response)

  def testEditProgram(self):
    from soc.models.document import Document
    self.data.createHost()
    url = '/gsoc/program/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertProgramTemplatesUsed(response)

    response = self.getJsonResponse(url)
    self.assertIsJsonResponse(response)
    self.assertEqual(1, len(response.context['data']))
