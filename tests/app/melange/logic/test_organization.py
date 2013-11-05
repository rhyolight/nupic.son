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

from google.appengine.ext import ndb

from django import http

from melange.logic import organization as org_logic
from melange.models import organization as org_model

from soc.models import program as program_model
from soc.models import survey as survey_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic
from soc.views.helper import request_data

from tests import org_utils
from tests import program_utils
from tests import test_utils


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = 'Test Org Name'
TEST_EMAIL = 'test@example.com'

class CreateOrganizationWithApplicationTest(unittest.TestCase):
  """Unit tests for createOrganizationWithApplication function."""

  def setUp(self):
    # seed a program
    self.program = seeder_logic.seed(program_model.Program)

    # seed an organization application
    self.survey = seeder_logic.seed(survey_model.Survey)

  def testOrgAndApplicationCreated(self):
    """Tests that org entity and application are created successfully."""
    org_properties = {'name': TEST_ORG_NAME}
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, self.program.key(), self.survey.key(), org_properties, {})
    self.assertTrue(result)

    # check that organization is created and persisted
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertIsNotNone(org)
    self.assertEqual(org.org_id, TEST_ORG_ID)
    self.assertEqual(org.name, TEST_ORG_NAME)
    self.assertEqual(org.status, org_model.Status.APPLYING)

    # check that organization application response is created and persisted
    app_response = org_model.ApplicationResponse.query(ancestor=org.key).get()
    self.assertIsNotNone(app_response)
    self.assertEqual(
        app_response.survey,
        ndb.Key.from_old_key(self.survey.key()))

  def testForTheSameOrgIdAndProgram(self):
    """Tests that two orgs cannot have the same id for the same program."""
    # create one organization with the given org ID
    org_properties = {'name': TEST_ORG_NAME}
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, self.program.key(), self.survey.key(), org_properties, {})
    self.assertTrue(result)

    # try creating another organization with the same org ID but different name
    org_properties = {'name': TEST_ORG_NAME[::-1]}
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, self.program.key(), self.survey.key(), org_properties, {})
    self.assertFalse(result)

    # check that the organization has old name
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.name, TEST_ORG_NAME)

  def testForTheSameOrgIdAndDifferentProgram(self):
    """Tests that two orgs cannot have the same id for different programs."""
    # create one organization with the given org ID
    org_properties = {'name': TEST_ORG_NAME}
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, self.program.key(), self.survey.key(), org_properties, {})
    self.assertTrue(result)

    # create another organization with the given org ID for different program
    other_program = seeder_logic.seed(program_model.Program)
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, other_program.key(), self.survey.key(),
        org_properties, {})
    self.assertTrue(result)


class UpdateOrganizationWithApplicationTest(unittest.TestCase):
  """Unit tests for updateOrganizationWithApplication function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)
    self.org = org_utils.seedOrganization(
        TEST_ORG_ID, self.program.key(), name=TEST_ORG_NAME)
    self.app_response = org_model.ApplicationResponse(parent=self.org.key)
    self.app_response.put()

  def testOrgIdInOrgProperties(self):
    """Tests that org id cannot be updated."""
    org_properties = {'org_id': TEST_ORG_ID}
    org_logic.updateOrganizationWithApplication(self.org, org_properties, {})

    # check that identifier has not changed
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.org_id, TEST_ORG_ID)

    org_properties = {'org_id': 'different_org_id'}
    with self.assertRaises(ValueError):
      org_logic.updateOrganizationWithApplication(self.org, org_properties, {})

  def testProgramInOrgProperties(self):
    """Tests that program cannot be updated."""
    org_properties = {'program': ndb.Key.from_old_key(self.program.key())}
    org_logic.updateOrganizationWithApplication(self.org, org_properties, {})

    # check that program has not changed
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.program, ndb.Key.from_old_key(self.program.key()))

    org_properties = {'program': ndb.Key('Program', 'other_program')}
    with self.assertRaises(ValueError):
      org_logic.updateOrganizationWithApplication(self.org, org_properties, {})

  def testOrgPropertiesUpdated(self):
    """Tests that organization properties are updated properly."""
    org_properties = {'name': 'Other Program Name'}
    org_logic.updateOrganizationWithApplication(self.org, org_properties, {})

    # check that properties are updated
    org = ndb.Key(
        org_model.Organization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertEqual(org.name, 'Other Program Name')


class SetStatusTest(test_utils.DjangoTestCase):
  """Unit tests for setStatus function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

    self.program = seeder_logic.seed(program_model.Program)

    properties = {'parent': self.program}
    seeder_logic.seed(program_model.ProgramMessages, properties=properties)

    self.site = program_utils.seedSite()

    self.org = org_utils.seedOrganization(TEST_ORG_ID, self.program.key())

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
