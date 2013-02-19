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

import datetime

from soc.modules.gsoc.models import program as program_model

from tests import test_utils

# TODO: perhaps we should move this out?
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class GSoCCreateProgramPageTest(test_utils.GSoCDjangoTestCase):
  """Tests GSoCCreateProgramPage view.
  """

  DEF_LINK_ID = 'melange'

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/program/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def getCreateProgramFormRequiredProperties(self):
    """Returns all properties to be sent in a POST dictionary that are required
    to create a new program.
    """
    return {
        'link_id': self.DEF_LINK_ID,
        'name': 'Melange Program',
        'short_name': 'MP',
        'description': 'This is a Melange Program',
        'status': 'visible',
        'apps_tasks_limit': 20,
        'slots': 500,
        }

  def getCreateProgramFormOptionalProperties(self):
    """Returns all properties to be optionally sent in a POST dictionary to
    create a new program.
    """
    return {
        'group_label': 'soc',
        'nr_accepted_orgs': 200,
        'student_min_age': 18,
        'student_min_age_as_of': datetime.date.today(),
        'events_frame_url': u'http://www.example1.com/',
        'privacy_policy_url': u'http://www.example2.com/',
        'blogger': u'http://www.example3.com/',
        'gplus': u'http://www.example4.com/',
        'feed_url': u'http://www.example5.com/',
        'email': 'test@example.com',
        'irc': 'irc://test@freenode.net',
        'max_slots': 10,
        'allocations_visible': True,
        'duplicates_visible': True,
        }

  def getEditProgramUrl(self):
    """Returns a URL to edit the newly created program."""
    return '/'.join([
        '/gsoc/program/edit',
        self.sponsor.key().name(),
        self.DEF_LINK_ID]) + '?validated'

  def getProgramKeyName(self):
    """Returns a key name of the newly created program."""
    return '/'.join([self.sponsor.key().name(), self.DEF_LINK_ID])

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

  def testCreateProgramWithRequiredProperties(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createHost()

    properties = self.getCreateProgramFormRequiredProperties()

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self.getEditProgramUrl())

    program = program_model.GSoCProgram.get_by_key_name(
        self.getProgramKeyName())

    self.assertEqual(self.getProgramKeyName(), program.key().name())
    self.assertSameEntity(program.scope, self.sponsor)
    self.assertPropertiesEqual(properties, program)

  def testCreateProgramWithInsufficientData(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createHost()

    properties = self.getCreateProgramFormRequiredProperties()

    for k, v in properties.items():
      # remove the property from the dictionary so as to check if
      # it is possible to create a program without it
      del properties[k]
      response = self.post(url, properties)

      self.assertResponseOK(response)
      self.assertTrue(k in response.context['error'])

      # restore the property
      properties[k] = v

  def testCreateProgramWithAllData(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.data.createHost()

    properties = self.getCreateProgramFormRequiredProperties()
    properties.update(self.getCreateProgramFormOptionalProperties())

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self.getEditProgramUrl())

    program = program_model.GSoCProgram.get_by_key_name(
        self.getProgramKeyName())

    self.assertEqual(self.getProgramKeyName(), program.key().name())
    self.assertSameEntity(program.scope, self.sponsor)
    self.assertPropertiesEqual(properties, program)


class EditProgramTest(test_utils.GSoCDjangoTestCase):
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
