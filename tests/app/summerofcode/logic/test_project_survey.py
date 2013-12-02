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

"""Unit tests for project survey logic."""

import unittest

from google.appengine.ext import db

from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project_survey as project_survey_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode.logic import project_survey as project_survey_logic

from tests import program_utils


class ConstructEvaluationKeyTest(unittest.TestCase):
  """Unit tests for constructEvaluationKey function."""

  def testGetMidtermEvaluationKey(self):
    """Tests that correct midterm evaluation key is returned."""
    program = program_utils.seedGSoCProgram()
    actual_key = project_survey_logic.constructEvaluationKey(
        program.key(), project_survey_model.MIDTERM_EVAL)
    expected_key = db.Key.from_path(
        project_survey_model.ProjectSurvey.kind(), 'gsoc_program/%s/%s' % (
            program.key().name(), project_survey_model.MIDTERM_EVAL))
    self.assertEqual(actual_key, expected_key)

  def testGetFinalEvaluationKey(self):
    """Tests that correct final evaluation key is returned."""
    program = program_utils.seedGSoCProgram()
    actual_key = project_survey_logic.constructEvaluationKey(
        program.key(), project_survey_model.FINAL_EVAL)
    expected_key = db.Key.from_path(
        project_survey_model.ProjectSurvey.kind(), 'gsoc_program/%s/%s' % (
            program.key().name(), project_survey_model.FINAL_EVAL))
    self.assertEqual(actual_key, expected_key)

  def testUnknownSurveyType(self):
    """Tests that error is raised when survey type is not supported."""
    program = program_utils.seedGSoCProgram()
    with self.assertRaises(ValueError):
      project_survey_logic.constructEvaluationKey(program.key(), 'unknown')


class GetStudentEvaluationsTest(unittest.TestCase):
  """Unit tests for getStudentEvaluations function."""

  def setUp(self):
    self.program = program_utils.seedGSoCProgram()

    self.evaluation_keys = set()

    evaluation_properties = {
        'program': self.program,
        'link_id': project_survey_model.MIDTERM_EVAL,
        'key_name': 'gsoc_program/%s/%s' % (
            self.program.key().name(), project_survey_model.MIDTERM_EVAL)
        }
    self.evaluation_keys.add(seeder_logic.seed(
        project_survey_model.ProjectSurvey,
        properties=evaluation_properties).key())

    evaluation_properties = {
        'program': self.program,
        'link_id': project_survey_model.FINAL_EVAL,
        'key_name': 'gsoc_program/%s/%s' % (
            self.program.key().name(), project_survey_model.FINAL_EVAL)
        }
    self.evaluation_keys.add(seeder_logic.seed(
        project_survey_model.ProjectSurvey,
        properties=evaluation_properties).key())

  def testEvaluationsForProgram(self):
    """Tests that all evaluations are returned for the program."""
    evaluations = project_survey_logic.getStudentEvaluations(
        self.program.key())
    self.assertSetEqual(set(evaluation.key() for evaluation in evaluations),
        self.evaluation_keys)

  def testNoEvaluationsForProgram(self):
    """Tests that no evaluations are returned for program with no surveys."""
    other_program = program_utils.seedGSoCProgram()
    evaluations = project_survey_logic.getStudentEvaluations(
        other_program.key())
    self.assertSetEqual(evaluations, set())
