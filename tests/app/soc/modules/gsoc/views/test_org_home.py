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


"""Tests for Organization homepage related views.
"""


from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase


class OrgHomeProjectListTest(GSoCDjangoTestCase):
  """Tests organization homepage views.
  """

  def setUp(self):
    self.init()

  def createStudentProjects(self):
    """Creates two student projects.
    """
    mentor = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor.createOtherUser('mentor@example.com').createMentor(self.org)

    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudentWithProjects(self.org, mentor.profile, 2)

  def assertOrgHomeTemplatesUsed(self, response, show_project_list):
    """Asserts that all the org home templates were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/_connect_with_us.html')
    self.assertTemplateUsed(response, 'modules/gsoc/org_home/base.html')

    if show_project_list:
      self.assertTemplateUsed(
          response, 'modules/gsoc/org_home/_project_list.html')
    else:
      self.assertTemplateNotUsed(
          response, 'modules/gsoc/org_home/_project_list.html')

  def testOrgHomeDuringOrgSignup(self):
    """Tests the the org home page during the organization signup period.
    """
    self.timeline_helper.orgSignup()
    url = '/gsoc/org/' + self.org.key().name()
    response = self.get(url)
    self.assertOrgHomeTemplatesUsed(response, False)

  def testOrgHomeDuringStudentSignup(self):
    """Tests the the org home page during the student signup period.
    """
    self.timeline_helper.studentSignup()
    url = '/gsoc/org/' + self.org.key().name()
    response = self.get(url)
    self.assertOrgHomeTemplatesUsed(response, False)

  def testOrgHomeAfterStudentProjectsAnnounced(self):
    """Tests the the org home page after announcing accepted student projects.
    """
    self.timeline_helper.studentsAnnounced()
    self.createStudentProjects()
    url = '/gsoc/org/' + self.org.key().name()
    response = self.get(url)
    self.assertOrgHomeTemplatesUsed(response, True)
    data = self.getListData(url, 0)
    self.assertEqual(2, len(data))

  def testOrgHomeDuringOffseason(self):
    """Tests the the org home page after GSoC is over.
    """
    self.timeline_helper.offSeason()
    self.createStudentProjects()
    url = '/gsoc/org/' + self.org.key().name()
    response = self.get(url)
    self.assertOrgHomeTemplatesUsed(response, True)
    data = self.getListData(url, 0)
    self.assertEqual(2, len(data))


class OrgHomeApplyTest(GSoCDjangoTestCase):
  """Tests organization homepage views.
  """

  def setUp(self):
    self.init()

  def homepageContext(self):
    url = '/gsoc/org/' + self.org.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    return response.context

  def assertNoStudent(self, context):
    self.assertNotIn('student_apply_block', context)
    self.assertNotIn('student_profile_link', context)
    self.assertNotIn('submit_proposal_link', context)

  def assertNoMentor(self, context):
    self.assertNotIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def assertMentor(self):
    self.profile_helper.createMentor(self.org)
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertEqual('a mentor', context['role'])
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testAnonymousPreSignup(self):
    self.timeline_helper.orgSignup()
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testAnonymousDuringSignup(self):
    self.timeline_helper.studentSignup()
    context = self.homepageContext()
    self.assertIn('student_apply_block', context)
    self.assertIn('student_profile_link', context)
    self.assertNotIn('submit_proposal_link', context)

    self.assertNotIn('mentor_apply_block', context)
    self.assertIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testAnonymousPostSignup(self):
    self.timeline_helper.postStudentSignup()
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testAnonymousStudentsAnnounced(self):
    self.timeline_helper.studentsAnnounced()
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertNotIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testMentorPreSignup(self):
    self.timeline_helper.orgSignup()
    self.assertMentor()

  def testMentorDuringSignup(self):
    self.timeline_helper.studentSignup()
    self.assertMentor()

  def testMentorPostSignup(self):
    self.timeline_helper.postStudentSignup()
    self.assertMentor()

  def testMentorStudentsAnnounced(self):
    self.timeline_helper.studentsAnnounced()
    self.assertMentor()

  def testOrgAdmin(self):
    self.profile_helper.createOrgAdmin(self.org)
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertEqual('an administrator', context['role'])
    self.assertNotIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testAppliedMentor(self):
    self.profile_helper.createMentorRequest(self.org)
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertIn('mentor_applied', context)
    self.assertNotIn('invited_role', context)
    self.assertNotIn('mentor_request_link', context)

  def testInvitedMentor(self):
    self.profile_helper.createInvitation(self.org, 'mentor')
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertEqual('a mentor', context['invited_role'])
    self.assertNotIn('mentor_request_link', context)

  def testInvitedOrgAdmin(self):
    self.profile_helper.createInvitation(self.org, 'org_admin')
    context = self.homepageContext()
    self.assertNoStudent(context)

    self.assertIn('mentor_apply_block', context)
    self.assertNotIn('mentor_profile_link', context)
    self.assertNotIn('role', context)
    self.assertNotIn('mentor_applied', context)
    self.assertEqual('an administrator', context['invited_role'])
    self.assertNotIn('mentor_request_link', context)

  def testStudentDuringSignup(self):
    self.timeline_helper.studentSignup()
    self.profile_helper.createStudent()
    context = self.homepageContext()
    self.assertIn('student_apply_block', context)
    self.assertNotIn('student_profile_link', context)
    self.assertIn('submit_proposal_link', context)
    self.assertNoMentor(context)

  def testStudentPostSignup(self):
    self.timeline_helper.postStudentSignup()
    self.profile_helper.createStudent()
    context = self.homepageContext()
    self.assertNoStudent(context)
    self.assertNoStudent(context)
