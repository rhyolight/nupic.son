# Copyright 2013 the Melange authors.
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

"""Tests for organization logic."""

import unittest

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.logic import organization as org_logic
from melange.models import organization as org_model
from melange.models import survey as survey_model

from soc.models import program as program_model
from soc.models import survey as soc_survey_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import org_utils
from tests import program_utils
from tests import test_utils


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = 'Test Org Name'
TEST_DESCRIPTION = 'Test Org Description'
TEST_EMAIL = 'test@example.com'
TEST_LOGO_URL = 'http://www.test.logo.url.com'

class CreateOrganizationTest(unittest.TestCase):
  """Unit tests for createOrganization function."""

  def setUp(self):
    # seed a program
    self.program = seeder_logic.seed(program_model.Program)

    # seed an organization application
    self.survey = seeder_logic.seed(soc_survey_model.Survey)

  def testOrgAndApplicationCreated(self):
    """Tests that org entity and application are created successfully."""
    org_properties = {
        'description': TEST_DESCRIPTION,
        'logo_url': TEST_LOGO_URL,
        'name': TEST_ORG_NAME
        }
    result = org_logic.createOrganization(
        TEST_ORG_ID, self.program.key(), org_properties)
    self.assertTrue(result)

    # check that organization is created and persisted
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertIsNotNone(org)
    self.assertEqual(org.org_id, TEST_ORG_ID)
    self.assertEqual(org.description, TEST_DESCRIPTION)
    self.assertEqual(org.logo_url, TEST_LOGO_URL)
    self.assertEqual(org.name, TEST_ORG_NAME)
    self.assertEqual(org.status, org_model.Status.APPLYING)

  def testForTheSameOrgIdAndProgram(self):
    """Tests that two orgs cannot have the same id for the same program."""
    # create one organization with the given org ID
    org_properties = {
        'description': TEST_DESCRIPTION,
        'name': TEST_ORG_NAME
        }
    result = org_logic.createOrganization(
        TEST_ORG_ID, self.program.key(), org_properties)
    self.assertTrue(result)

    # try creating another organization with the same org ID but different name
    org_properties = {
        'description': TEST_DESCRIPTION,
        'name': TEST_ORG_NAME[::-1]
        }
    result = org_logic.createOrganization(
        TEST_ORG_ID, self.program.key(), org_properties)
    self.assertFalse(result)

    # check that the organization has old name
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.name, TEST_ORG_NAME)

  def testForTheSameOrgIdAndDifferentProgram(self):
    """Tests that two orgs cannot have the same id for different programs."""
    # create one organization with the given org ID
    org_properties = {
        'description': TEST_DESCRIPTION,
        'name': TEST_ORG_NAME
        }
    result = org_logic.createOrganization(
        TEST_ORG_ID, self.program.key(), org_properties)
    self.assertTrue(result)

    # create another organization with the given org ID for different program
    other_program = seeder_logic.seed(program_model.Program)
    result = org_logic.createOrganization(
        TEST_ORG_ID, other_program.key(), org_properties)
    self.assertTrue(result)

  def testForMissingProperty(self):
    """Tests that org is not created when a required property is missing."""
    # no description property
    org_properties = {'name': TEST_ORG_NAME}
    result = org_logic.createOrganization(
        TEST_ORG_ID, self.program.key(), org_properties)
    self.assertFalse(result)

  def testForInvalidLogoUrl(self):
    """Tests that org is not created when a link property has invalid values."""
    org_properties = {
        'logo_url': 'http://invalid',
        'name': TEST_ORG_NAME
        }
    result = org_logic.createOrganization(
        TEST_ORG_ID, self.program.key(), org_properties)
    self.assertFalse(result)


class UpdateOrganizationTest(unittest.TestCase):
  """Unit tests for updateOrganization function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)
    self.org = org_utils.seedOrganization(
        self.program.key(), org_id=TEST_ORG_ID, name=TEST_ORG_NAME)
    self.app_response = survey_model.SurveyResponse(parent=self.org.key)
    self.app_response.put()

  def testOrgIdInOrgProperties(self):
    """Tests that org id cannot be updated."""
    org_properties = {'org_id': TEST_ORG_ID}
    org_logic.updateOrganization(self.org, org_properties)

    # check that identifier has not changed
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.org_id, TEST_ORG_ID)

    org_properties = {'org_id': 'different_org_id'}
    with self.assertRaises(ValueError):
      org_logic.updateOrganization(self.org, org_properties)

  def testProgramInOrgProperties(self):
    """Tests that program cannot be updated."""
    org_properties = {'program': ndb.Key.from_old_key(self.program.key())}
    org_logic.updateOrganization(self.org, org_properties)

    # check that program has not changed
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.program, ndb.Key.from_old_key(self.program.key()))

    org_properties = {'program': ndb.Key('Program', 'other_program')}
    with self.assertRaises(ValueError):
      org_logic.updateOrganization(self.org, org_properties)

  def testOrgPropertiesUpdated(self):
    """Tests that organization properties are updated properly."""
    org_properties = {'name': 'Other Program Name'}
    org_logic.updateOrganization(self.org, org_properties)

    # check that properties are updated
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.name, 'Other Program Name')


FOO_ID = 'foo'
BAR_ID = 'bar'

TEST_FOO_ANSWER = 'Test foo answer'
TEST_BAR_ANSWER = 'Test bar answer'

OTHER_TEST_FOO_ANSWER = 'Other foo answer'
OTHER_TEST_BAR_ANSWER = 'Other bar answer'

TEST_APPLICATION_PROPERTIES = {
    FOO_ID: TEST_FOO_ANSWER,
    BAR_ID: TEST_BAR_ANSWER
    }

class SetApplicationResponseTest(unittest.TestCase):
  """Unit tests for setApplicationResponse function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = seeder_logic.seed(program_model.Program)
    self.org = org_utils.seedOrganization(program.key())

    self.survey_key = db.Key.from_path('Survey', 'test_survey_name')

  def testApplicationCreated(self):
    """Tests that application is created when it does not exist."""
    application = org_logic.setApplicationResponse(
        self.org.key, self.survey_key, TEST_APPLICATION_PROPERTIES)

    # check that application is persisted
    self.assertIsNotNone(application.key.get())

    # check that responses are stored in the entity
    self.assertEqual(application.foo, TEST_APPLICATION_PROPERTIES[FOO_ID])
    self.assertEqual(application.bar, TEST_APPLICATION_PROPERTIES[BAR_ID])

  def testApplicationUpdated(self):
    """Tests that application is updated if it has existed."""
    # seed organization application
    org_utils.seedApplication(
        self.org.key, self.survey_key, **TEST_APPLICATION_PROPERTIES)

    # set new answers to both questions
    properties = {
        FOO_ID: OTHER_TEST_FOO_ANSWER,
        BAR_ID: OTHER_TEST_BAR_ANSWER
        }
    application = org_logic.setApplicationResponse(
        self.org.key, self.survey_key, properties)

    # check that responses are updated properly
    self.assertEqual(application.foo, properties[FOO_ID])
    self.assertEqual(application.bar, properties[BAR_ID])

    # set answer to only one question
    properties = {FOO_ID: TEST_FOO_ANSWER}
    application = org_logic.setApplicationResponse(
        self.org.key, self.survey_key, properties)

    # check that the response for one question is updated and there is
    # no response for the other question
    self.assertEqual(application.foo, properties[FOO_ID])
    self.assertNotIn(BAR_ID, application._properties.keys())

    # set new answers to both questions again
    properties = {
        FOO_ID: OTHER_TEST_FOO_ANSWER,
        BAR_ID: OTHER_TEST_BAR_ANSWER
        }
    application = org_logic.setApplicationResponse(
        self.org.key, self.survey_key, properties)

    # check that responses are present for both questions
    self.assertEqual(application.foo, properties[FOO_ID])
    self.assertEqual(application.bar, properties[BAR_ID])


class SetStatusTest(test_utils.DjangoTestCase):
  """Unit tests for setStatus function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    self.program = seeder_logic.seed(program_model.Program)

    properties = {'parent': self.program}
    seeder_logic.seed(program_model.ProgramMessages, properties=properties)

    self.site = program_utils.seedSite()

    self.org = org_utils.seedOrganization(self.program.key())

  def testAcceptOrganization(self):
    """Tests that organization is successfully accepted."""
    org = org_logic.setStatus(
        self.org, self.program, self.site, org_model.Status.ACCEPTED,
        recipients=[TEST_EMAIL])

    self.assertEqual(org.status, org_model.Status.ACCEPTED)
    self.assertEmailSent()

  def testRejectOrganization(self):
    """Tests that organization is successfully rejected."""
    org = org_logic.setStatus(
        self.org, self.program, self.site, org_model.Status.REJECTED,
        recipients=[TEST_EMAIL])

    self.assertEqual(org.status, org_model.Status.REJECTED)
    self.assertEmailSent()

  def testPreAcceptOrganization(self):
    """Tests that organization is successfully pre-accepted."""
    org = org_logic.setStatus(
        self.org, self.program, self.site, org_model.Status.PRE_ACCEPTED,
        recipients=[TEST_EMAIL])

    self.assertEqual(org.status, org_model.Status.PRE_ACCEPTED)

    # TODO(daniel): make sure that email is not sent

  def testPreRejectOrganization(self):
    """Tests that organization is successfully pre-accepted."""
    org = org_logic.setStatus(
        self.org, self.program, self.site, org_model.Status.PRE_REJECTED,
        recipients=[TEST_EMAIL])

    self.assertEqual(org.status, org_model.Status.PRE_REJECTED)

    # TODO(daniel): make sure that email is not sent
