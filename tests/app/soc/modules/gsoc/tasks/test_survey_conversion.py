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


__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import httplib
import urllib

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import DjangoTestCase
from tests.test_utils import TaskQueueTestCase

from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.models.grading_project_survey_record import \
    GradingProjectSurveyRecord
from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.grading_record import GradingRecord
from soc.modules.gsoc.models.grading_survey_group import GradingSurveyGroup
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.models.student_project import StudentProject
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.models.project_survey_record import ProjectSurveyRecord


class SurveyConversionTest(DjangoTestCase, TaskQueueTestCase):
  """Test the code that converts the old surveys.
  """

  PSR_URL = '/tasks/gsoc/convert_surveys/project_survey_record'
  GPSR_URL = '/tasks/gsoc/convert_surveys/grading_project_survey_record'
  GSG_URL = '/tasks/gsoc/convert_surveys/grading_survey_group'
  GR_URL = '/tasks/gsoc/convert_surveys/grading_record'


  def setUp(self):
    super(SurveyConversionTest, self).setUp()
    self.init()
    self.createMentor()
    self.createStudent()
    self.createSurveys()

  def createMentor(self):
    """Creates a new mentor.
    """
    profile_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('mentor@example.com')
    self.mentor = profile_helper.createMentor(self.org)

  def createStudent(self):
    """Creates a Student with a project.
    """
    profile_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('student@example.com')
    self.student = profile_helper.createStudentWithProject(self.org,
                                                            self.mentor)
    self.project = GSoCProject.all().ancestor(self.student).get()

    values = {
        'link_id': 'link_id',
        'scope': self.org,
        'scope_path': self.org.key().id_or_name(),
        'student': self.student}
    for prop in self.project.properties().keys():
      values[prop] = getattr(self.project, prop)
    self.old_project = StudentProject(key_name='keyname', **values)
    self.old_project.put()

  def createSurveys(self):
    """Creates the surveys and records required for the tests in the old
    format.
    """
    survey_values = {
        'author': self.founder,
        'title': 'Title',
        'modified_by': self.founder,
        'link_id': 'link_id',
        'scope': self.gsoc,
        'scope_path': self.gsoc.key().id_or_name()}

    self.project_survey = ProjectSurvey(**survey_values)
    self.project_survey.put()

    record_values = {
        'user': self.student.user,
        'org': self.org,
        'project': self.old_project,
        'survey': self.project_survey}
    self.project_survey_record = ProjectSurveyRecord(**record_values)
    self.project_survey_record.put()

    self.grading_survey = GradingProjectSurvey(**survey_values)
    self.grading_survey.put()

    record_values = {
        'user': self.student.user,
        'org': self.org,
        'project': self.old_project,
        'survey': self.grading_survey,
        'grade': True}
    self.grading_survey_record = GradingProjectSurveyRecord(**record_values)
    self.grading_survey_record.put()

    group_values = {
        'name': 'Survey Group Name',
        'grading_survey': self.grading_survey,
        'student_survey': self.project_survey,
        'link_id': 'link_id',
        'scope': self.gsoc,
        'scope_path': self.gsoc.key().id_or_name()}
    self.survey_group = GradingSurveyGroup(key_name='keyname', **group_values)
    self.survey_group.put()

    record_values = {
        'grading_survey_group': self.survey_group,
        'mentor_record': self.grading_survey_record,
        'student_record': self.project_survey_record,
        'project': self.old_project,
        'grade_decision': 'pass'}
    self.grading_record = GradingRecord(**record_values)
    self.grading_record.put()

    self.project.passed_evaluations = [self.grading_record.key()]
    self.project.put()
    self.old_project.passed_evaluations = [self.grading_record.key()]
    self.old_project.put()

  def createGSoCGSurveyGroup(self):
    """Creates a GSoCSurveyGroup
    """
    values = {
        'name': 'Survey Group Name',
        'grading_survey': self.grading_survey,
        'student_survey': self.project_survey,
        'program': self.gsoc}
    self.gsoc_survey_group = GSoCGradingSurveyGroup(**values)
    self.gsoc_survey_group.put()

  def testConvertProjectSurveyRecords(self):
    """Test conversion of ProjectSurveyRecords.
    """
    self.assertEqual(GSoCProjectSurveyRecord.all().count(1), 0)

    response = self.post(self.PSR_URL, {})

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(1)
    self.assertTasksInQueue(n=1, url=self.PSR_URL)
    self.assertEqual(GSoCProjectSurveyRecord.all().count(2), 1)

    record = GSoCProjectSurveyRecord.all().get()
    self.assertEqual(record.user.key(), self.project_survey_record.user.key())

  def testConvertGradingProjectSurveyRecords(self):
    """Test conversion of GradingProjectSurveyRecords.
    """
    self.assertEqual(GSoCGradingProjectSurveyRecord.all().count(1), 0)

    response = self.post(self.GPSR_URL, {})

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(1)
    self.assertTasksInQueue(n=1, url=self.GPSR_URL)
    self.assertEqual(GSoCGradingProjectSurveyRecord.all().count(2), 1)
    record = GSoCGradingProjectSurveyRecord.all().get()
    self.assertEqual(record.user.key(), self.grading_survey_record.user.key())


  def testConvertGradingSurveyGroup(self):
    """Test conversion of the GradingSurveyGroup.
    """
    self.assertEqual(GSoCGradingSurveyGroup.all().count(1), 0)

    response = self.post(self.GSG_URL, {})

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(2)
    self.assertTasksInQueue(n=1, url=self.GSG_URL)
    self.assertTasksInQueue(n=1, url=self.GR_URL)
    self.assertEqual(GSoCGradingSurveyGroup.all().count(2), 1)

    group = GSoCGradingSurveyGroup.all().get()
    self.assertEqual(group.grading_survey.key(),
                     self.survey_group.grading_survey.key())
    self.assertEqual(group.student_survey.key(),
                     self.survey_group.student_survey.key())

  def testConvertGradingRecord(self):
    """Test conversion of GradingRecord.
    """
    self.createGSoCGSurveyGroup()

    self.assertEqual(GSoCGradingRecord.all().count(1), 0)

    post_data = {'old_group': self.survey_group.key().id_or_name(),
                 'new_group': self.gsoc_survey_group.key().id_or_name()}
    response = self.post(self.GR_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(1)
    self.assertTasksInQueue(n=1, url=self.GR_URL)
    self.assertEqual(GSoCGradingRecord.all().count(2), 1)

    record = GSoCGradingRecord.all().get()
    self.assertEqual(record.grade_decision, self.grading_record.grade_decision)
