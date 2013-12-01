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

"""Unit tests for program related views."""

import datetime
import tempfile

from google.appengine.ext import ndb

from melange.models import school as school_model

from soc.models import program as soc_program_model
from soc.modules.gsoc.models import program as program_model

from tests import test_utils

# TODO: perhaps we should move this out?
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class GSoCCreateProgramPageTest(test_utils.GSoCDjangoTestCase):
  """Tests GSoCCreateProgramPage view."""

  DEF_PROGRAM_ID = 'melange'

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/program/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def _getCreateProgramFormRequiredProperties(self):
    """Returns all properties to be sent in a POST dictionary that are required
    to create a new program.
    """
    return {
        'program_id': self.DEF_PROGRAM_ID,
        'name': 'Melange Program',
        'short_name': 'MP',
        'description': 'This is a Melange Program',
        'status': soc_program_model.STATUS_VISIBLE,
        'apps_tasks_limit': 20,
        'slots': 500,
        }

  def _getCreateProgramFormOptionalProperties(self):
    """Returns all properties to be optionally sent in a POST dictionary to
    create a new program.
    """
    return {
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

  def _getEditProgramUrl(self):
    """Returns a URL to edit the newly created program."""
    return '/'.join([
        '/gsoc/program/edit',
        self.sponsor.key().name(),
        self.DEF_PROGRAM_ID]) + '?validated'

  def _getProgramKeyName(self):
    """Returns a key name of the newly created program."""
    return '/'.join([self.sponsor.key().name(), self.DEF_PROGRAM_ID])

  def setUp(self):
    self.init()

  def testLoneUserAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createStudent()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createMentor(self.org)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createHost()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProgramTemplatesUsed(response)

  def testCreateProgramWithRequiredProperties(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createHost()

    properties = self._getCreateProgramFormRequiredProperties()

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self._getEditProgramUrl())

    program = program_model.GSoCProgram.get_by_key_name(
        self._getProgramKeyName())

    self.assertEqual(self._getProgramKeyName(), program.key().name())
    self.assertSameEntity(program.scope, self.sponsor)
    self.assertSameEntity(program.sponsor, self.sponsor)
    self.assertPropertiesEqual(properties, program)

  def testCreateProgramWithInsufficientData(self):
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createHost()

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
    url = '/gsoc/program/create/' + self.sponsor.key().name()
    self.profile_helper.createHost()

    properties = self._getCreateProgramFormRequiredProperties()
    properties.update(self._getCreateProgramFormOptionalProperties())

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self._getEditProgramUrl())

    program = program_model.GSoCProgram.get_by_key_name(
        self._getProgramKeyName())

    self.assertEqual(self._getProgramKeyName(), program.key().name())
    self.assertSameEntity(program.scope, self.sponsor)
    self.assertSameEntity(program.sponsor, self.sponsor)
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
    self.assertTemplateUsed(response, 'modules/gsoc/program/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def testEditProgramHostOnly(self):
    url = '/gsoc/program/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testEditProgramAsDeveloper(self):
    self.profile_helper.createDeveloper()
    url = '/gsoc/program/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProgramTemplatesUsed(response)

  def testEditProgram(self):
    from soc.models.document import Document
    self.profile_helper.createHost()
    url = '/gsoc/program/edit/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProgramTemplatesUsed(response)

    response = self.getJsonResponse(url)
    self.assertIsJsonResponse(response)
    self.assertEqual(1, len(response.context['data']))


class GSoCProgramMessagesPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for GSoCProgramMessagesPage view."""

  DEF_ACCEPTED_ORGS_MSG = 'Accepted Orgs Message'
  DEF_REJECTED_ORGS_MSG = 'Rejected Orgs Message'
  DEF_MENTOR_WELCOME_MSG = 'Mentor Welcome Message'
  DEF_ACCEPTED_STUDENTS_MSG = 'Accepted Students Messages'
  DEF_ACCEPTED_STUDENTS_WELCOME_MSG = 'Accepted Students Welcome Messages'
  DEF_REJECTED_STUDENTS_MSG = 'Rejected Students Message'

  def assertProgramTemplatesUsed(self, response):
    """Asserts that all the templates from the program were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/program/messages.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def _getUrl(self, validated=False):
    return ''.join([
        '/gsoc/program/messages/edit/',
        self.program.key().name(),
        '?validated' if validated else ''])

  def _getGSoCProgramMessagesFormProperties(self):
    return {
        'accepted_orgs_msg': self.DEF_ACCEPTED_ORGS_MSG,
        'rejected_orgs_msg': self.DEF_MENTOR_WELCOME_MSG,
        'mentor_welcome_msg': self.DEF_MENTOR_WELCOME_MSG,
        'accepted_students_msg': self.DEF_ACCEPTED_STUDENTS_MSG,
        'accepted_students_welcome_msg': self.DEF_ACCEPTED_STUDENTS_WELCOME_MSG,
        'rejected_students_msg': self.DEF_REJECTED_STUDENTS_MSG,
        }

  def _getEntities(self):
    return program_model.GSoCProgramMessages.all().ancestor(
        self.gsoc).fetch(1000)

  def setUp(self):
    self.init()

  def testLoneUserAccessForbidden(self):
    url = self._getUrl()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    url = self._getUrl()
    self.profile_helper.createStudent()
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    url = self._getUrl()
    self.profile_helper.createMentor(self.org)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    url = self._getUrl()
    self.profile_helper.createOrgAdmin(self.org)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)

  def testHostAccessGranted(self):
    url = self._getUrl()
    self.profile_helper.createHost()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProgramTemplatesUsed(response)

  def testEditProgramMessages(self):
    url = self._getUrl()
    self.profile_helper.createHost()

    properties = self._getGSoCProgramMessagesFormProperties()

    response = self.post(url, properties)
    self.assertResponseRedirect(response, self._getUrl(validated=True))

    # check if there is only one entity for the program
    entities = self._getEntities()
    self.assertEqual(1, len(entities))

    # check that the properties are set correctly
    entity = entities[0]
    for p in entity.properties():
      self.assertEqual(properties[p], getattr(entity, p))


TEST_SCHOOLS_GOOD_INPUT = """
uid1\tname 1\tcountry 1
uid2\tname 2\tcountry 2
uid3\tname 3\tcountry 3
"""

TEST_SCHOOLS_BAD_INPUT = """
uid1\tname 1\tcountry 1\textra field1
uid2\tname 2, country 2
"""

class UploadSchoolsPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for UploadSchoolsPage view."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/program/schools.html')

  def _getUrl(self):
    """Returns URL to the tested page."""
    return '/gsoc/program/schools/upload/%s' % self.program.key().name()

  def testPageLoads(self):
    """Tests that page loads properly."""
    self.profile_helper.createHost()
    response = self.get(self._getUrl())
    self.assertResponseOK(response)
    self._assertPageTemplatesUsed(response)

  def testSchoolsUploaded(self):
    """Tests that schools are uploaded correctly."""
    self.profile_helper.createHost()

    # check that there is no file with schools at this stage
    self.assertIsNone(self.program.schools)

    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getUrl()
      postdata = {'schools': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(response, url)

      # check if the file has been uploaded
      program = program_model.GSoCProgram.get(self.program.key())
      self.assertIsNotNone(program.schools)

  def testSchoolsNotUploadedOnBadInput(self):
    """Tests that schools are not uploaded if input is not valid."""
    self.profile_helper.createHost()

    post_data = {'schools': TEST_SCHOOLS_BAD_INPUT}
    response = self.post(self._getUrl(), post_data)

    # TODO(daniel): update the test when bad requests do not return 200
    self.assertResponseOK(response)

    # check that no schools are uploaded
    school_cluster = ndb.Query(
        kind=school_model.SchoolCluster._get_kind(),
        ancestor=ndb.Key.from_old_key(self.program.key())).get()
    self.assertIsNone(school_cluster)
