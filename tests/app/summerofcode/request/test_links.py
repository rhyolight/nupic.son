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

"""Tests for Summer Of Code links module."""

import unittest

from summerofcode.request import links

from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project_survey as project_survey_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


TEST_SURVEY_ID = 'test_survey_id'

class SoCLinkerTest(unittest.TestCase):
  """Tests the SoCLinker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.linker = links.SoCLinker()

  def testSurvey(self):
    """Tests survey function."""
    # seed a program
    program = seeder_logic.seed(program_model.GSoCProgram)

    # seed a survey
    survey_properties = {
        'program': program,
        'link_id': TEST_SURVEY_ID,
        'key_name': '%s/%s' % (program.key().name(), TEST_SURVEY_ID)
        }
    survey = seeder_logic.seed(
        project_survey_model.ProjectSurvey, properties=survey_properties)

    self.assertEqual(
        '/gsoc/eval/mentor/edit/%s/%s' % (
            survey.program.key().name(), survey.survey_type),
        self.linker.survey(survey.key(), 'gsoc_edit_mentor_evaluation'))
