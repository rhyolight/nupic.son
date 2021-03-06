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

import datetime

from google.appengine.ext import ndb

from soc.models import program as soc_program_model

from soc.modules.gci.models import program as program_model

from tests import profile_utils
from tests import test_utils
from tests.test_utils import GCIDjangoTestCase


class GCICreateProgramPageTest(test_utils.GCIDjangoTestCase):
  """Tests GCICreateProgramPage view.
  """

  DEF_PROGRAM_ID = 'melange'

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used."""
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/program/base.html')
    self.assertTemplateUsed(response, 'modules/gci/_form.html')

  def _getCreateProgramFormRequiredProperties(self):
    """Returns all properties to be sent in a POST dictionary that are required
    to create a new program.
    """
    # TODO(daniel): test task types somehow
    return {
        'program_id': self.DEF_PROGRAM_ID,
        'name': 'Melange Program',
        'short_name': 'MP',
        'description': 'This is a Melange Program',
        'status': soc_program_model.STATUS_VISIBLE,
        'nr_simultaneous_tasks': 1,
        'winner_selection_type':
            program_model.WinnerSelectionType.ORG_NOMINATED,
        'nr_winners': 15,
        }

  def _getCreateProgramFormOptionalProperties(self):
    """Returns all properties to be optionally sent in a POST dictionary to
    create a new program.
    """
    return {
        'nr_accepted_orgs': 20,
        'student_min_age': 13,
        'student_max_age': 18,
        'student_min_age_as_of': datetime.date.today(),
        'events_frame_url': u'http://www.example1.com/',
        'privacy_policy_url': u'http://www.example2.com/',
        'blogger': u'http://www.example3.com/',
        'gplus': u'http://www.example4.com/',
        'feed_url': u'http://www.example5.com/',
        'email': 'test@example.com',
        'irc': 'irc://test@freenode.net',
        'example_tasks': u'http://www.example6.com/',
        'form_translations_url': u'http://www.example7.com/',
        }

  def _getCreateProgramUrl(self):
    """Returns a URL to create a new program."""
    return '/'.join([
        '/gci/program/create', self.sponsor.key().name()])

  def _getEditProgramUrl(self):
    """Returns a URL to edit the newly created program."""
    return '/'.join([
        '/gci/program/edit',
        self.sponsor.key().name(),
        self.DEF_PROGRAM_ID]) + '?validated'

  def _getProgramKeyName(self):
    """Returns a key name of the newly created program."""
    return '/'.join([self.sponsor.key().name(), self.DEF_PROGRAM_ID])

  def setUp(self):
    self.init()

  def testLoneUserAccessForbidden(self):
    url = self._getCreateProgramUrl()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(self._getCreateProgramUrl())
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    url = self._getCreateProgramUrl()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = self._getCreateProgramUrl()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    url = self._getCreateProgramUrl()
    response = self.get(url)
    self.assertProgramTemplatesUsed(response)

  def testCreateProgramWithRequiredProperties(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    url = self._getCreateProgramUrl()

    properties = self._getCreateProgramFormRequiredProperties()

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self._getEditProgramUrl())

    program = program_model.GCIProgram.get_by_key_name(
        self._getProgramKeyName())

    self.assertEqual(self._getProgramKeyName(), program.key().name())
    self.assertSameEntity(program.scope, self.sponsor)
    self.assertSameEntity(program.sponsor, self.sponsor)
    self.assertPropertiesEqual(properties, program)

  def testCreateProgramWithInsufficientData(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    url = self._getCreateProgramUrl()

    properties = self._getCreateProgramFormRequiredProperties()

    for k, v in properties.items():
      # remove the property from the dictionary so as to check if
      # it is possible to create a program without it
      del properties[k]
      response = self.post(url, properties)

      self.assertResponseOK(response)
      self.assertIn(k, response.context['error'])

      # restore the property
      properties[k] = v

  def testCreateProgramWithAllData(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    url = self._getCreateProgramUrl()

    properties = self._getCreateProgramFormRequiredProperties()
    properties.update(self._getCreateProgramFormOptionalProperties())

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self._getEditProgramUrl())

    program = program_model.GCIProgram.get_by_key_name(
        self._getProgramKeyName())

    self.assertEqual(self._getProgramKeyName(), program.key().name())
    self.assertSameEntity(program.scope, self.sponsor)
    self.assertSameEntity(program.sponsor, self.sponsor)
    self.assertPropertiesEqual(properties, program)


class EditProgramTest(GCIDjangoTestCase):
  """Tests program edit page.
  """

  def setUp(self):
    self.init()

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/program/base.html')
    self.assertTemplateUsed(response, 'modules/gci/_form.html')

  def testEditProgramHostOnly(self):
    url = '/gci/program/edit/' + self.gci.key().name()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testEditProgramAsDeveloper(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user, is_admin=True)

    url = '/gci/program/edit/' + self.gci.key().name()
    response = self.get(url)
    self.assertProgramTemplatesUsed(response)

  def testEditProgram(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    url = '/gci/program/edit/' + self.gci.key().name()

    response = self.get(url)
    self.assertProgramTemplatesUsed(response)

    response = self.getJsonResponse(url)
    self.assertIsJsonResponse(response)
    self.assertEqual(1, len(response.context['data']))
