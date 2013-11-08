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

"""Tests for Summer Of Code-specific organization logic."""

import unittest

from google.appengine.ext import ndb

from melange.logic import organization as org_logic

from soc.modules.gsoc.models import program as program_model
from soc.models import survey as survey_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode import types
from summerofcode.models import organization as org_model


TEST_ORG_ID = 'test_org_id'
TEST_ORG_NAME = 'Test Org Name'
TEST_DESCRIPTION = u'Test Organization Description'
TEST_IDEAS_PAGE = 'http://www.test.ideas.com'

class CreateOrganizationWithApplicationTest(unittest.TestCase):
  """Unit tests for Summer Of Code specific behavior of
  createOrganizationWithApplication function.
  """

  def setUp(self):
    # seed a program
    self.program = seeder_logic.seed(program_model.GSoCProgram)

    # seed an organization application
    self.survey = seeder_logic.seed(survey_model.Survey)

  def testPropertiesAreSet(self):
    """Tests that Summer Of Code-specific properties are set correctly."""
    org_properties = {
       'description': TEST_DESCRIPTION,
       'ideas_page': TEST_IDEAS_PAGE,
       'name': TEST_ORG_NAME,
       }
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, self.program.key(), self.survey.key(), org_properties, {},
        models=types.SOC_MODELS)
    self.assertTrue(result)

    # check that organization is created and persisted
    org = ndb.Key(
        org_model.SOCOrganization._get_kind(),
        '%s/%s' % (self.program.key().name(), TEST_ORG_ID)).get()
    self.assertIsNotNone(org)
    self.assertEqual(org.ideas_page, TEST_IDEAS_PAGE)

  def testForInvalidIdeasPage(self):
    """Tests that org is not created when a link property has invalid values."""
    org_properties = {
        'ideas_page': 'http://invalid',
        'name': TEST_ORG_NAME
        }
    result = org_logic.createOrganizationWithApplication(
        TEST_ORG_ID, self.program.key(), self.survey.key(), org_properties, {},
        models=types.SOC_MODELS)
    self.assertFalse(result)
