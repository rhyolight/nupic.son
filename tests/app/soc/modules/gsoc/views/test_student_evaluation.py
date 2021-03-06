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

"""Tests for student_evaluation views."""

import json
import urllib

from google.appengine.ext import ndb

from django import forms as django_forms
from django.utils import html

from tests import profile_utils
from tests import timeline_utils
from tests.survey_utils import SurveyHelper
from tests import test_utils
from tests.utils import project_utils

from soc.views import forms

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models.project_survey import ProjectSurvey

from soc.modules.seeder.logic.providers.string import LinkIDProvider

from summerofcode.models import survey as survey_model


class StudentEvaluationTest(test_utils.GSoCDjangoTestCase):
  """Tests proposal review page.
  """

  def setUp(self):
    super(StudentEvaluationTest, self).setUp()
    self.init()
    self.evaluation = SurveyHelper(self.gsoc, self.dev_test)

  def assertEvaluationCreateTemplateUsed(self, response):
    """Asserts that all the evaluation create/edit templates were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/form_base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_evaluation.html')

  def assertEvaluationTakeTemplateUsed(self, response):
    """Asserts that all the evaluation take templates were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/form_base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_evaluation_take.html')

  def assertEvaluationShowTemplateUsed(self, response):
    """Asserts that all the evaluation show templates were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/_survey/show.html')

  def assertFieldChoices(self, schema_choices, form_choices):
    """Asserts if the form field has the same choices as defined in the schema.
    """
    choices = [c['value'] for c in schema_choices]
    self.assertEqual(choices.sort(), form_choices.sort())

  def assertFormFromSchema(self, form, schema_json):
    """Asserts if the form built from the schema is same as the schema defined.
    """
    order, fields = json.loads(urllib.unquote(schema_json))

    for field in order:
      field_dict = fields[field]
      form_field = form.fields[field]

      if field_dict['field_type'] == 'checkbox':
        self.assertTrue(isinstance(form_field,
                                   django_forms.MultipleChoiceField))
        self.assertTrue(isinstance(form_field.widget,
                                   forms.CheckboxSelectMultiple))
        self.assertFieldChoices(field_dict['values'], form_field.choices)
      elif field_dict['field_type'] == 'radio':
        self.assertTrue(isinstance(form_field, django_forms.ChoiceField))
        self.assertTrue(isinstance(form_field.widget,
                                   django_forms.RadioSelect))
        self.assertFieldChoices(field_dict['values'], form_field.choices)
      elif field_dict['field_type'] == 'textarea':
        self.assertTrue(isinstance(form_field, django_forms.CharField))
        self.assertTrue(isinstance(form_field.widget, django_forms.Textarea))
      elif field_dict['field_type'] == 'input_text':
        self.assertTrue(isinstance(form_field, django_forms.CharField))

      self.assertEqual(field_dict['label'], form_field.label)
      self.assertEqual(field_dict['required'], form_field.required)

  def createProject(self, override_properties=None):
    properties = {
        'is_featured': False,
        'mentors': [],
        'status': project_model.STATUS_ACCEPTED,
        'program': self.gsoc,
        'org': self.org,
        }
    properties.update(override_properties or {})
    return self.seed(project_model.GSoCProject, properties)

  def getStudentEvalRecordProperties(self, show=False):
    evaluation = self.evaluation.createStudentEvaluation()

    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    self.student = profile_utils.seedSOCStudent(self.program)
    project = project_utils.seedProject(self.student, self.program.key(),
        org_key=self.org.key, mentor_key=self.mentor.key)

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        self.student.profile_id, project.key().id())

    base_url = '/gsoc/eval/student'
    if show:
      url = '%s/show/%s' % (base_url, suffix)
    else:
      url = '%s/%s' % (base_url, suffix)

    return (url, evaluation, self.mentor)

  def ffPastEval(self, evaluation):
    evaluation.survey_start = timeline_utils.past(20)
    evaluation.survey_end = timeline_utils.past(10)
    evaluation.put()

  def setEvaluationPeriodToFuture(self, evaluation):
    evaluation.survey_start = timeline_utils.future(delta=10)
    evaluation.survey_end = timeline_utils.future(delta=20)
    evaluation.put()

  def testCreateEvaluationForStudentWithoutProject(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForMentorWithoutProject(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForStudent(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForMentor(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    student = profile_utils.seedNDBStudent(self.program)

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    project_utils.seedProject(
        student, self.program.key(), mentor_key=mentor.key)

    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForOrgAdmin(self):
    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    # test review GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testCreateEvaluationForHost(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    link_id = LinkIDProvider(ProjectSurvey).getValue()
    suffix = "%s/%s" % (self.gsoc.key().name(), link_id)

    # test student evaluation create/edit GET
    url = '/gsoc/eval/student/edit/' + suffix
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertEvaluationCreateTemplateUsed(response)

    self.assertContains(
        response, 'Create new student evaluation')
    self.assertContains(
        response, '<input name="schema" type="hidden" id="schema" value="" />',
        html=True)

    self.assertEqual(response.context['page_name'],
                     'Create new student evaluation')
    self.assertEqual(response.context['post_url'], url)
    form = response.context['forms'][0]

    expected_fields = ['author', 'title', 'short_name', 'content',
                       'survey_start', 'survey_end', 'schema'].sort()
    actual_fields = form.fields.keys().sort()
    self.assertEqual(expected_fields, actual_fields)

    # TODO(Madhu): Get rid of scope and author fields once the data
    # conversion is done.
    override = {
        'survey_content': None,
        'author': user.key.to_old_key(),
        'created_by': user.key.to_old_key(),
        'program': self.gsoc.key(),
        'modified_by': user.key.to_old_key(),
        'schema': self.evaluation.evalSchemaString(),
        }
    response, _ = self.modelPost(url, ProjectSurvey, override)
    self.assertResponseRedirect(response, url + '?validated')

    evaluation = ProjectSurvey.all().get()

    response = self.get(url)
    self.assertResponseOK(response)
    self.assertEvaluationCreateTemplateUsed(response)

    self.assertContains(
        response, 'Edit - %s' % (evaluation.title,))
    self.assertContains(
        response,
        '<input name="schema" type="hidden" id="schema" value=%s />'
            % (json.dumps(html.escape(evaluation.schema)),), html=True)

    self.assertEqual(response.context['page_name'],
                     'Edit - %s' % (evaluation.title,))
    self.assertEqual(response.context['post_url'], url)
    form = response.context['forms'][0]

    expected_fields = ['author', 'title', 'short_name', 'content',
                       'survey_start', 'survey_end', 'schema'].sort()
    actual_fields = form.fields.keys().sort()
    self.assertEqual(expected_fields, actual_fields)

  def testTakeEvaluationForMentor(self):
    url, _, _ = self.getStudentEvalRecordProperties()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    # test student evaluation take GET for a mentor of the same organization
    response = self.get(url)
    self.assertResponseForbidden(response)

    response = self.client.post(url)
    self.assertResponseForbidden(response)

    project = project_model.GSoCProject.all().get()
    project.mentors.append(mentor.key.to_old_key())
    project.put()
    # test student evaluation take GET for the mentor of the project
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testTakeEvaluationForAnotherOrgMentor(self):
    url, _, _ = self.getStudentEvalRecordProperties()

    another_org = self.createOrg()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[another_org.key])

    # test student evaluation take GET for a mentor of another organization
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testTakeEvaluationForAnotherOrgAdmin(self):
    url, _, _ = self.getStudentEvalRecordProperties()

    another_org = self.createOrg()
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[another_org.key])

    # test student evaluation take GET for an org admin of another organization
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testTakeEvaluationForOrgAdmin(self):
    """Test that if an org admin attempts to visit a student evaluation,
    they are redirected.
    """
    url, evaluation, _ = self.getStudentEvalRecordProperties()

    project = project_model.GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        self.student.profile_id, project.key().id())

    base_url = '/gsoc/eval/student'

    show_url = '%s/show/%s' % (base_url, suffix)
    user = profile_utils.seedNDBUser()
    profile_utils.seedNDBProfile(
        self.program.key(), admin_for=[self.org.key], user=user)
    profile_utils.loginNDB(user)

    response = self.get(url)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudentWithNoProject(self):
    """Test that if a student without a project attempts to visit the
    evaluation page, they will be redirected.
    """

    student = profile_utils.seedSOCStudent(self.program)
    # test student evaluation show GET for a for a student who
    # does not have a project in the program
    url, evaluation, _ = self.getStudentEvalRecordProperties()
    response = self.get(url)
    self.assertResponseForbidden(response)

    project = project_model.GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        self.student.profile_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(evaluation)
    response = self.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForAnotherStudentWithProject(self):
    url, evaluation, mentor = self.getStudentEvalRecordProperties()

    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(
        student, self.program.key(), mentor_key=mentor.key)
    # test student evaluation show GET for a for a student who
    # has another project in the same org and whose mentor is
    # same as the student whose survey is being accessed
    response = self.get(url)
    self.assertResponseForbidden(response)

    project = project_model.GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        self.student.profile_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(evaluation)
    response = self.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudentProjectWithAnotherMentor(self):
    """Test that a student with a project in the same org but with a
    different mentor than the current mentor will be redirected.
    """
    url, evaluation, _ = self.getStudentEvalRecordProperties()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(
        student, self.program.key(), mentor_key=mentor.key)

    response = self.get(url)
    self.assertResponseForbidden(response)

    project = project_model.GSoCProject.all().get()

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        self.student.profile_id, project.key().id())

    base_url = '/gsoc/eval/student'

    self.ffPastEval(evaluation)
    response = self.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testTakeEvalForStudentProjectWithAnotherOrg(self):
    """Test that if a student with a project for an org attempts to take
    an evaluation for a different org, they will be redirected.
    """
    url, evaluation, _ = self.getStudentEvalRecordProperties()
    other_org = self.createOrg()

    project = project_model.GSoCProject.all().get()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[other_org.key])
    other_student = profile_utils.seedSOCStudent(self.program)
    other_project = project_utils.seedProject(other_student,
        self.program.key(), org_key=other_org.key, mentor_key=mentor.key)

    response = self.get(url)
    self.assertResponseForbidden(response)

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        self.student.profile_id, project.key().id())

    self.ffPastEval(evaluation)
    response = self.get(url)
    show_url = '/gsoc/eval/student/show/%s' % suffix
    self.assertResponseRedirect(response, show_url)

  def testAccessBeforeEvaluationStarts(self):
    """Tests that student cannot access the page before survey starts."""
    evaluation = self.evaluation.createStudentEvaluation()
    self.setEvaluationPeriodToFuture(evaluation)

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()

    student = profile_utils.seedSOCStudent(self.program, user=user)
    project = project_utils.seedProject(student, self.program.key(),
        org_key=self.org.key, mentor_key=mentor.key)
    profile_utils.loginNDB(user)

    base_url = '/gsoc/eval/student'
    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        student.profile_id, project.key().id())

    url = '%s/%s' % (base_url, suffix)
    response = self.get(url)

    # response is forbidden as the evaluation period has yet to start
    self.assertResponseForbidden(response)

    # TODO(daniel): NDB migration
    ndb_survey_key = ndb.Key.from_old_key(evaluation.key())
    start_date = timeline_utils.past()

    extension = survey_model.PersonalExtension(
        parent=student.key, survey=ndb_survey_key, start_date=start_date)
    extension.put()

    response = self.get(url)

    # with extension it should be possible to access the evaluation
    self.assertResponseOK(response)

  def testTakeEvalForStudent(self):
    """Test that given that the current student is the student for the
    current project and mentor then they can take the evaluation.
    """
    evaluation = self.evaluation.createStudentEvaluation()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    student = profile_utils.seedSOCStudent(self.program, user=user)
    project = project_utils.seedProject(
        student, self.program.key(), mentor_key=mentor.key)

    base_url = '/gsoc/eval/student'
    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        student.profile_id, project.key().id())

    url = '%s/%s' % (base_url, suffix)

    project = project_model.GSoCProject.all().get()

    # test student evaluation show GET for a for a student who
    # has another project in a different organization
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertEvaluationTakeTemplateUsed(response)

    self.assertContains(response, '%s' % (evaluation.title))
    self.assertContains(response, 'Project: %s' % (project.title))

    self.assertEqual(response.context['page_name'], '%s' % (evaluation.title))
    form = response.context['forms'][0]

    self.assertFormFromSchema(form, evaluation.schema)

    postdata = {
        'frm-t1309871149671-item': 'one line text message',
        'frm-t1309871322655-item': ['Option 2', 'Option 3'],
        'frm-t1309871157535-item': """A quick brown fox jumped over a lazy dog.
        A quick brown fox jumped over a lazy dog. A quick brown fox jumped
        over a lazy dog. A quick brown fox jumped over a lazy dog.""",
        }
    response = self.post(url, postdata)
    self.assertResponseOK(response)
    self.assertFormError(
        response, 'form', 'frm-t1310822212610-item',
        'This field is required.')

    postdata = {
        'frm-t1309871149671-item': 'one line text message',
        'frm-t1309871322655-item': ['Option 2', 'Option 3'],
        'frm-t1309871157535-item': """A quick brown fox jumped over a lazy dog.
        A quick brown fox jumped over a lazy dog. A quick brown fox jumped
        over a lazy dog. A quick brown fox jumped over a lazy dog.""",
        'frm-t1310822212610-item': "Wa Wa",
        }
    response = self.post(url, postdata)
    self.assertResponseRedirect(response, '%s?validated' % (url,))

    self.ffPastEval(evaluation)
    response = self.get(url)
    show_url = '%s/show/%s' % (base_url, suffix)
    self.assertResponseRedirect(response, show_url)

  def testShowEvalForStudentWithNoProject(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    # test student evaluation show GET for a for a student who
    # does not have a project in the program
    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForAnotherStudentWithProject(self):
    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    # test student evaluation show GET for a for a student who
    # has another project in the same org and whose mentor is
    # same as the student whose survey is being accessed
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForStudentProjectWithAnotherMentor(self):
    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    # test student evaluation show GET for a for a student who
    # has another project whose mentor is different than the current
    # mentor but the project is in the same org
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForStudentProjectWithAnotherOrg(self):
    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)
    other_org = self.createOrg()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)
    project_utils.seedProject(
        student, self.program.key(), org_key=other_org.key)

    # test student evaluation show GET for a for a student who
    # has another project in a different organization
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvalForStudent(self):
    """Test that a student can view their mentor evaluation."""
    evaluation = self.evaluation.createStudentEvaluation()

    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    user = profile_utils.seedNDBUser()
    student = profile_utils.seedSOCStudent(self.program, user=user)
    project = project_utils.seedProject(student, self.program.key())
    profile_utils.loginNDB(user)

    suffix = "%s/%s/%s/%s" % (
        self.gsoc.key().name(), evaluation.link_id,
        student.profile_id, project.key().id())

    url = '/gsoc/eval/student/show/%s' % suffix

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertEvaluationShowTemplateUsed(response)

  def testShowEvaluationForMentor(self):
    # test student evaluation show GET for a mentor of the same organization
    url, evaluation, mentor = self.getStudentEvalRecordProperties(show=True)
    response = self.get(url)
    self.assertResponseForbidden(response)

    project = project_model.GSoCProject.all().get()

    project_mentors = project.mentors
    project.mentors.append(mentor.key.to_old_key())
    project.put()
    # test student evaluation show GET for the mentor of the project
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    project.mentors = project_mentors
    project.put()

    response = self.get(url)
    self.assertResponseForbidden(response)

    project.mentors.append(mentor.key.to_old_key())
    project.put()

    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvaluationForOtherOrgMentor(self):
    another_org = self.createOrg()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[another_org.key])

    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)

    # test student evaluation show GET for a mentor of another organization
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvaluationForOtherOrgAdmin(self):
    another_org = self.createOrg()
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[another_org.key])

    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)

    # test student evaluation show GET for an org admin of another organization
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testShowEvaluationForOrgAdmin(self):
    """Test that an org admin can access a project for the org of
    which they are an admin.
    """
    user = profile_utils.seedNDBUser()
    org_admin = profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])
    profile_utils.loginNDB(user)

    url, evaluation, _ = self.getStudentEvalRecordProperties(show=True)
    response = self.get(url)
    self.assertResponseForbidden(response)

    self.ffPastEval(evaluation)
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertEvaluationShowTemplateUsed(response)


class GSoCStudentEvaluationPreviewPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for GSoCStudentEvaluationPreviewPage class."""

  def setUp(self):
    self.init()
    self.evaluation = SurveyHelper(
        self.gsoc, self.dev_test).createStudentEvaluation()

  def _getUrl(self):
    """Returns URL to preview student evaluation.

    Returns:
      URL string to preview student evaluation.
    """
    return '/gsoc/eval/student/preview/%s/%s' % (
        self.program.key().name(), self.evaluation.survey_type)

  def _assertTemplatesUsed(self, response):
    """Asserts that all the evaluation preview templates were used.

    Args:
      response: HTTP response object.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/form_base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_evaluation_take.html')

  def testLoneUserAccessDenied(self):
    """Tests that users without profiles cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    response = self.get(self._getUrl())
    self.assertResponseForbidden(response)

  def testStudentAccessDenied(self):
    """Tests that students cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    response = self.get(self._getUrl())
    self.assertResponseForbidden(response)

  def testMentorAccessDenied(self):
    """Tests that mentors cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    response = self.get(self._getUrl())
    self.assertResponseForbidden(response)

  def testOrgAdminAccessDenied(self):
    """Tests that org admins cannot access the page."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(self._getUrl())
    self.assertResponseForbidden(response)

  def testProgramAdminAccessGranted(self):
    """Tests that program administrators can access the page."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self._getUrl())
    self.assertResponseOK(response)
    self._assertTemplatesUsed(response)

  def testForNonExistingSurvey(self):
    """Tests that error response is returned for non-existing surveys."""
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get('/gsoc/eval/student/preview/%s/fakesurvey' %
        self.program.key().name())
    self.assertResponseNotFound(response)
