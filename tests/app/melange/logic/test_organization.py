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

from melange.logic import organization as org_logic
from melange.models import organization as org_model

from soc.models import program as program_model
from soc.models import survey as survey_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = 'Test Org Name'

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
