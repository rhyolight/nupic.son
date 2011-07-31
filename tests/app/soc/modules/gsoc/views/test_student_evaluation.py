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

  def assertEvaluationTakeTemplateUsed(self, response):
    """Asserts that all the proposal review were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/form_base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_evaluation_take.html')

  def assertEvaluationShowTemplateUsed(self, response):
    """Asserts that all the proposal review were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_survey/show.html')

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

  def createEvaluation(self, host=None, override={}):
    if not host:
      host_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
      host_profile.createOtherUser('mentor@example.com')
      host = host_profile.createHost()

    properties = {
        'prefix': 'gsoc_program',
        'schema': self.evalSchemaString(),
        'survey_content': None,
        'author': host,
        'modified_by': host,
        'scope': self.gsoc,
        'key_name': SurveyKeyNameProvider(),
        'survey_start': timeline_utils.past(),
        'survey_end': timeline_utils.future(),
        }
    properties.update(override)
    return self.seed(ProjectSurvey, properties)

  def createProject(self, override_properties={}):
    properties = {
        'is_featured': False, 'mentors': [],
        'status': 'accepted', 'program': self.gsoc, 'org': self.org,

    }
    properties.update(override_properties)
    return self.seed(GSoCProject, properties)

  def getStudentEvalRecordProperties(self, show=False):
    eval = self.createEvaluation()

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor@example.com')
    mentor = mentor_profile.createMentor(self.org)

    student_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    student_profile.createOtherUser('student_with_proj@example.com')
    student_profile.createStudentWithProject(self.org, mentor)

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    base_url = '/gsoc/eval/student'
    if show:
      url = '%s/show/%s' % (base_url, suffix)
    else:
      url = '%s/%s' % (base_url, suffix)

    return (url, eval, mentor)

  def ffPastEval(self, eval):
    eval.survey_start = timeline_utils.past(20)
    eval.survey_end = timeline_utils.past(10)
    eval.put()

  def testCreateEvaluationForStudentWithoutProject(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    self.data.createStudent()
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForMentorWithoutProject(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    self.data.createMentor(self.org)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForStudent(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor@example.com')
    mentor = mentor_profile.createMentor(self.org)

    self.data.createStudentWithProject(self.org, mentor)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForMentor(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    student_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    student_profile.createOtherUser('student_with_proj@example.com')
    student = student_profile.createStudent()

    self.data.createMentorWithProject(self.org, student)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForOrgAdmin(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    self.data.createOrgAdmin(self.org)
    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForHost(self):
    host = self.data.createHost()

    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    # test student evaluation create/edit GET
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
    response, _ = self.modelPost(url, ProjectSurvey, override)
    self.assertResponseRedirect(response, url+'?validated')

  def testTakeEvaluationForMentor(self):
    url, eval, _ = self.getStudentEvalRecordProperties()

    mentor = self.data.createMentor(self.org)

    # test student evaluation take GET for a mentor of the same organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    response = self.client.post(url)
    self.assertResponseForbidden(response)

    project = GSoCProject.all().get()
    project.mentors.append(mentor.key())
    project.put()
    # test student evaluation take GET for the mentor of the project
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testTakeEvaluationForAnotherOrgMentor(self):
    url, eval, _ = self.getStudentEvalRecordProperties()

    another_org = self.createOrg()
    self.data.createMentor(another_org)
    # test student evaluation take GET for a mentor of another organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testTakeEvaluationForAnotherOrgAdmin(self):
    url, eval, _ = self.getStudentEvalRecordProperties()

    another_org = self.createOrg()
    self.data.createOrgAdmin(another_org)
    # test student evaluation take GET for an org admin of another organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testTakeEvaluationForOrgAdmin(self):
    url, eval, _ = self.getStudentEvalRecordProperties()

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    base_url = '/gsoc/eval/student'

    show_url = '%s/show/%s' % (base_url, suffix)
    self.data.createOrgAdmin(self.org)
    response = self.client.get(url)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudentWithNoProject(self):
    self.data.createStudent()

    # test student evaluation show GET for a for a student who
    # does not have a project in the program
    url, eval, _ = self.getStudentEvalRecordProperties()
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(eval)
    response = self.client.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForAnotherStudentWithProject(self):
    url, eval, mentor = self.getStudentEvalRecordProperties()

    self.data.createStudentWithProject(self.org, mentor)
    # test student evaluation show GET for a for a student who
    # has another project in the same org and whose mentor is
    # same as the student whose survey is being accessed
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(eval)
    response = self.client.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudentProjectWithAnotherMentor(self):
    url, eval, _ = self.getStudentEvalRecordProperties()

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor_another@example.com')
    mentor = mentor_profile.createMentor(self.org)

    self.data.createStudentWithProject(self.org, mentor)
    # test student evaluation show GET for a for a student who
    # has another project whose mentor is different than the current
    # mentor but the project is in the same org
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(eval)
    response = self.client.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudentProjectWithAnotherOrg(self):
    url, eval, _ = self.getStudentEvalRecordProperties()
    other_org = self.createOrg()

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor_other_org@example.com')
    mentor = mentor_profile.createMentor(other_org)

    self.data.createStudentWithProject(other_org, mentor)
    # test student evaluation show GET for a for a student who
    # has another project in a different organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(eval)
    response = self.client.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudent(self):
    eval = self.createEvaluation()

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor@example.com')
    mentor = mentor_profile.createMentor(self.org)

    self.data.createStudentWithProject(self.org, mentor)

    project = GSoCProject.all().get()

    base_url = '/gsoc/eval/student'
    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    url = '%s/%s' % (base_url, suffix)

    # test student evaluation show GET for a for a student who
    # has another project in a different organization
    response = self.client.get(url)
    self.assertEvaluationTakeTemplateUsed(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

    #TODO (madhu): Add tests for POST requests for take

  def testShowEvalForStudentWithNoProject(self):
    self.data.createStudent()

    # test student evaluation show GET for a for a student who
    # does not have a project in the program
    url, eval, _ = self.getStudentEvalRecordProperties(show=True)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForAnotherStudentWithProject(self):
    url, eval, mentor = self.getStudentEvalRecordProperties(show=True)

    self.data.createStudentWithProject(self.org, mentor)
    # test student evaluation show GET for a for a student who
    # has another project in the same org and whose mentor is
    # same as the student whose survey is being accessed
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForStudentProjectWithAnotherMentor(self):
    url, eval, _ = self.getStudentEvalRecordProperties(show=True)

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor_another@example.com')
    mentor = mentor_profile.createMentor(self.org)

    self.data.createStudentWithProject(self.org, mentor)
    # test student evaluation show GET for a for a student who
    # has another project whose mentor is different than the current
    # mentor but the project is in the same org
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForStudentProjectWithAnotherOrg(self):
    url, eval, _ = self.getStudentEvalRecordProperties(show=True)
    other_org = self.createOrg()

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor_other_org@example.com')
    mentor = mentor_profile.createMentor(other_org)

    self.data.createStudentWithProject(other_org, mentor)
    # test student evaluation show GET for a for a student who
    # has another project in a different organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForStudent(self):
    eval = self.createEvaluation()

    mentor_profile = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_profile.createOtherUser('mentor@example.com')
    mentor = mentor_profile.createMentor(self.org)

    self.data.createStudentWithProject(self.org, mentor)

    project = GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), eval.link_id,
        project.parent().link_id, project.key().id())

    url = '/gsoc/eval/student/show/%s' % (suffix,)

    # test student evaluation show GET for a for a student who
    # has another project in a different organization
    response = self.client.get(url)
    self.assertEvaluationShowTemplateUsed(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertEvaluationShowTemplateUsed(response)

  def testShowEvaluationForMentor(self):
    # test student evaluation show GET for a mentor of the same organization
    url, eval, mentor = self.getStudentEvalRecordProperties(show=True)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    project = GSoCProject.all().get()

    project_mentors = project.mentors
    project.mentors.append(mentor.key())
    project.put()
    # test student evaluation show GET for the mentor of the project
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    project.mentors = project_mentors
    project.put()

    response = self.client.get(url)
    self.assertResponseForbidden(response)

    project.mentors.append(mentor.key())
    project.put()

    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvaluationForOtherOrgMentor(self):
    another_org = self.createOrg()
    self.data.createMentor(another_org)
    url, eval, _ = self.getStudentEvalRecordProperties(show=True)

    # test student evaluation show GET for a mentor of another organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvaluationForOtherOrgAdmin(self):
    another_org = self.createOrg()
    self.data.createOrgAdmin(another_org)
    url, eval, _ = self.getStudentEvalRecordProperties(show=True)

    # test student evaluation show GET for an org admin of another organization
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    self.assertResponseForbidden(response)

  def testShowEvaluationForOrgAdmin(self):
    self.data.createOrgAdmin(self.org)
    url, eval, _ = self.getStudentEvalRecordProperties(show=True)
    # test student evaluation show GET for an org admin of the org
    # to which project belongs to
    response = self.client.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(eval)
    response = self.client.get(url)
    print [t.name for t in response.template]
    self.assertEvaluationShowTemplateUsed(response)
