# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for grading record logic."""

import unittest

from soc.modules.gsoc.logic import grading_record as grading_record_logic
from soc.modules.gsoc.models import grading_project_survey_record \
  as grading_project_survey_record_model
from soc.modules.gsoc.models import grading_record as grading_record_model
from soc.modules.gsoc.models import grading_survey_group \
    as grading_survey_group_model
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import project_survey_record \
    as project_survey_record_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import survey_utils


class GetFieldsForGradingRecordTest(unittest.TestCase):
  """Unit tests for getFieldsForGradingRecord function."""

  def setUp(self):
    # seed a program
    self.program = seeder_logic.seed(program_model.GSoCProgram)

    survey_helper = survey_utils.SurveyHelper(self.program, False)

    # seed evaluations
    self.student_evaluation = survey_helper.createStudentEvaluation()
    self.mentor_evaluation = survey_helper.createMentorEvaluation()

    # seed grading survey group
    properties = {
        'program': self.program,
        'grading_survey': self.mentor_evaluation,
        'student_survey': self.student_evaluation,
        }
    self.survey_group = seeder_logic.seed(
        grading_survey_group_model.GSoCGradingSurveyGroup,
        properties=properties)

    # seed project
    self.project = seeder_logic.seed(project_model.GSoCProject)

  def testNoSurveyRecords(self):
    """Tests when no survey records has been filed for the project."""
    fields = grading_record_logic.getFieldsForGradingRecord(
        self.project, self.survey_group)

    # check that correct survey group is in fields
    self.assertEqual(
        fields['grading_survey_group'].key(), self.survey_group.key())

    # check that no mentor or students records are returned
    self.assertIsNone(fields['mentor_record'])
    self.assertIsNone(fields['student_record'])

    # check that grade decision is 'undecided'
    self.assertEquals(fields['grade_decision'],
        grading_record_model.GRADE_UNDECIDED)

  def testNoStudentRecord(self):
    """Tests when no student survey record has been filed for the project."""
    # seed mentor record with a passing grade
    properties = {
        'project': self.project,
        'grade': True,
        'survey': self.mentor_evaluation
        }
    mentor_record = seeder_logic.seed(
        grading_project_survey_record_model.GSoCGradingProjectSurveyRecord,
        properties=properties)

    fields = grading_record_logic.getFieldsForGradingRecord(
        self.project, self.survey_group)

    # check that no student record is returned
    self.assertIsNone(fields['student_record'])

    # check that mentor record is returned
    self.assertEqual(fields['mentor_record'].key(), mentor_record.key())

    # check that grade decision is 'fail'
    self.assertEqual(fields['grade_decision'], grading_record_model.GRADE_FAIL)

  def testNoMentorRecord(self):
    """Tests when no mentor survey record has been filed for the project."""
    # seed sudent record
    properties = {
        'project': self.project,
        'survey': self.student_evaluation,
        }
    student_record = seeder_logic.seed(
        project_survey_record_model.GSoCProjectSurveyRecord,
        properties=properties)

    fields = grading_record_logic.getFieldsForGradingRecord(
        self.project, self.survey_group)

    # check that no mentor record is returned
    self.assertIsNone(fields['mentor_record'])

    # check that student record is returned
    self.assertEqual(fields['student_record'].key(), student_record.key())

    # check that grade decision is 'undecided'
    self.assertEqual(fields['grade_decision'],
        grading_record_model.GRADE_UNDECIDED)

  def testMentorFailingRecord(self):
    """Tests when mentor record fails the project."""
    # seed sudent record
    properties = {
        'project': self.project,
        'survey': self.student_evaluation,
        }
    student_record = seeder_logic.seed(
        project_survey_record_model.GSoCProjectSurveyRecord,
        properties=properties)

    # seed mentor record with a failing grade
    properties = {
        'project': self.project,
        'grade': False,
        'survey': self.mentor_evaluation
        }
    mentor_record = seeder_logic.seed(
        grading_project_survey_record_model.GSoCGradingProjectSurveyRecord,
        properties=properties)

    fields = grading_record_logic.getFieldsForGradingRecord(
        self.project, self.survey_group)

    # check that both records are returned
    self.assertEqual(fields['student_record'].key(), student_record.key())
    self.assertEqual(fields['mentor_record'].key(), mentor_record.key())

    # check that grade decision is 'fail'
    self.assertEqual(fields['grade_decision'], grading_record_model.GRADE_FAIL)

  def testMentorPassingRecord(self):
    """Tests when mentor record passes the project."""
    # seed sudent record
    properties = {
        'project': self.project,
        'survey': self.student_evaluation,
        }
    student_record = seeder_logic.seed(
        project_survey_record_model.GSoCProjectSurveyRecord,
        properties=properties)

    # seed mentor record with a passing grade
    properties = {
        'project': self.project,
        'grade': True,
        'survey': self.mentor_evaluation
        }
    mentor_record = seeder_logic.seed(
        grading_project_survey_record_model.GSoCGradingProjectSurveyRecord,
        properties=properties)

    fields = grading_record_logic.getFieldsForGradingRecord(
        self.project, self.survey_group)

    # check that both records are returned
    self.assertEqual(fields['student_record'].key(), student_record.key())
    self.assertEqual(fields['mentor_record'].key(), mentor_record.key())

    # check that grade decision is 'fail'
    self.assertEqual(fields['grade_decision'], grading_record_model.GRADE_PASS)
