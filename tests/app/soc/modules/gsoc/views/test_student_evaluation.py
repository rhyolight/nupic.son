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

"""Tests for student_evaluation views.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import DjangoTestCase
from tests import timeline_utils

from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey import ProjectSurvey

from soc.modules.seeder.logic.providers.string import LinkIDProvider
from soc.modules.seeder.logic.providers.string import SurveyKeyNameProvider


class StudentEvaluationTest(DjangoTestCase):
  """Tests proposal review page.
  """

  def setUp(self):
    super(StudentEvaluationTest, self).setUp()
    self.init()

  def assertEvaluationCreateTemplateUsed(self, response):
    """Asserts that all the proposal review were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/form_base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_evaluation.html')

  def testCreateEvaluationForNonHost(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    student = self.data.createStudent()
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    mentor = self.data.createMentor(self.org)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    student_proj = self.data.createStudentWithProject(self.org, mentor)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    mentor_proj = self.data.createMentorWithProject(self.org, student_proj)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    org_admin = self.data.createOrgAdmin(self.org)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def evalSchemaString(self):
    return ('[["frm-t1309871149671-item","frm-t1309871322655-item",'
        '"frm-t1309871157535-item","frm-t1309871294200-item",'
        '"frm-t1310822212610-item"],{"frm-t1309871149671-item":'
        '{"field_type":"input_text","required":true,"label":'
        '"What%20is%20your%20name%3F"},"frm-t1309871322655-item":'
        '{"field_type":"checkbox","required":false,"other":false,'
        '"values":[{"value":"Option%203","checked":true},{"value":'
        '"Option%202","checked":true},{"value":"Option%204","checked":true}'
        ',{"value":"Option%201","checked":true}],"label":"'
        'Give%20every%20option%20you%20think%20is%20right"},'
        '"frm-t1309871157535-item":{"field_type":"textarea","required":'
        'false,"label":"Write%20a%20detail%20of%20your%20project%3F"},'
        '"frm-t1309871294200-item":{"field_type":"radio","required":'
        'false,"other":false,"values":[{"value":"Amongst%20the%20best%20'
        'people%20I%27ve%20ever%20worked%20with%20","checked":false},'
        '{"value":"Don%27t%20Know","checked":false},{"value":"Yes","checked"'
        ':false}],"label":"Are%20you%20alright%3F"},"frm-t1310822212610-item"'
        ':{"field_type":"radio","required":true,"other":true,"values":'
        '[{"value":"Wa","checked":true},{"value":"Wa%20Wa","checked":false}]'
        ',"label":"Testing%20radio%20again%20%3A%29"}}]')

  def createEvaluation(self, host=None):
    if not host:
      host = self.data.createHost()

    properties = {
        'prefix': 'gsoc_program',
        'schema': self.evalSchemaString(),
        'survey_content': None,
        'author': host,
        'modified_by': host,
        'scope': self.gsoc,
        'key_name': SurveyKeyNameProvider(),
        }
    return self.seed(ProjectSurvey, properties)

  def createProject(self, override_properties={}):
    properties = {
        'is_featured': False, 'mentors': [],
        'status': 'accepted', 'program': self.gsoc, 'org': self.org,

    }
    properties.update(override_properties)
    return self.seed(GSoCProject, properties)

  def testCreateEvaluation(self):
    host = self.data.createHost()

    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertEvaluationCreateTemplateUsed(response)

    self.assertContains(
        response, 'Create new student evaluation')
    self.assertContains(
        response, '<input name="schema" type="hidden" id="schema" value="" />')

    override = {
        'survey_content': None,
        'author': host,
        'modified_by': host,
        }
    response, properties = self.modelPost(url, ProjectSurvey, override)
    self.assertResponseRedirect(response, url+'?validated')

  def testTakeEvaluation(self):
    eval = self.createEvaluation()
    mentor = self.data.createMentor(self.org)

    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('mentor@example.com')
    student_entity = student.createStudent()

    project = self.createProject({'parent': student.profile})

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    # test review GET
    base_url = '/gsoc/eval/student'
    url = '%s/%s' % (base_url, suffix)
    expected_url = '%s/show/%s' % (base_url, suffix)
    response = self.client.get(url)
    self.assertResponseRedirect(response, expected_url)
