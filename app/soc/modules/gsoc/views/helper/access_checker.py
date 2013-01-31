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

"""Module containing the AccessChecker class that contains helper functions
for checking access.
"""

from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation, BadRequest
from soc.logic.exceptions import NotFound
from soc.logic.exceptions import RedirectRequest
from soc.models.org_app_record import OrgAppRecord
from soc.views.helper import access_checker

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import slot_transfer as slot_transfer_logic
from soc.modules.gsoc.models.connection import GSoCConnection, GSoCAnonymousConnection
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.organization import GSoCOrganization


DEF_FAILED_PREVIOUS_EVAL = ugettext(
    'You cannot access %s for this project because this project was '
    'failed in the previous evaluation.')

DEF_MAX_PROPOSALS_REACHED = ugettext(
    'You have reached the maximum number of proposals (%d) allowed '
    'for this program.')

DEF_NO_ORG_APP_RECORD_FOUND = ugettext(
    'The organization application for the given organization ID was not found.')

DEF_NO_STUDENT_EVALUATION = ugettext(
    'The project evaluation with name %s parameters does not exist.')

DEF_NO_MENTOR_EVALUATION = ugettext(
    'The project evaluation with name %s does not exist.')

DEF_NO_PROJECT = ugettext('Requested project does not exist.')

DEF_NO_RECORD_FOUND = ugettext(
    'The Record with the specified key was not found.')

DEF_NO_ORG_ADMIN_PROFILE = ugettext(
    'You must have an organization administrator profile to apply to be an '
    'an organization. If you want to register as an organization '
    'administrator for %s please <a href="%s">click here</a>, register and '
    'then come back to this page.')

DEF_NOT_ADMIN_FOR_ORG_APP = ugettext(
    'You should be listed as the main/backup organization administrator for '
    'the organization in the organization application to create a new '
    'organization profile for this organization.')

DEF_MENTOR_EVAL_DOES_NOT_BELONG_TO_YOU = ugettext(
    'This evaluation does not correspond to the project you are mentor for, '
    'and hence you cannot access it.')

DEF_ORG_APP_NOT_FOUND = ugettext(
    'You cannot create the organization profile for %s because there '
    'is no organization application for that id.')

DEF_ORG_APP_NOT_ACCEPTED = ugettext(
    'You cannot create the organization profile for %s because the '
    'organization application for it has not been accepted.')

DEF_ORG_EXISTS = ugettext(
    'The organization with the ID %s already exists and hence you cannot '
    'create a new organization profile for the same ID. If you are actually '
    'looking for editing this organization profile please click <a href="%s">'
    'here</a>.')

DEF_STUDENT_EVAL_DOES_NOT_BELONG_TO_YOU = ugettext(
    'This evaluation does not correspond to your project, and hence you '
    'cannot access it.')

DEF_EVAL_NOT_ACCESSIBLE_FOR_PROJECT = ugettext(
    'You cannot access this evaluation because you do not have any '
    'ongoing project.')

DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT = ugettext(
    'You cannot register as a student since you are already a '
    'mentor or organization administrator in %s.')

DEF_NOT_ALLOWED_TO_DOWNLOAD_FORM = ugettext(
    'You are not allowed to download the form.')

DEF_PROJECT_NOT_COMPLETED = ugettext(
    'The specified project has not been completed')

DEF_PROPOSAL_IGNORED_MESSAGE = ugettext(
    'An organization administrator has flagged this proposal to be '
    'ignored. If you think this is incorrect, contact an organization '
    'administrator to resolve the situation.')


class Mutator(access_checker.Mutator):
  """Mutator for the GSoC module.
  """

  def unsetAll(self):
    """Clear the fields of the data object.
    """
    self.data.private_comments_visible = access_checker.unset
    self.data.proposal = access_checker.unset
    self.data.proposer = access_checker.unset
    self.data.public_comments_visible = access_checker.unset
    self.data.public_only = access_checker.unset
    super(Mutator, self).unsetAll()

  def profileFromKwargs(self):
    """Retrieves profile from the kwargs for GSoC.
    """
    super(Mutator, self).profileFromKwargs(GSoCProfile)

  def proposalFromKwargs(self):
    self.profileFromKwargs()
    assert access_checker.isSet(self.data.url_profile)

    # can safely call int, since regexp guarnatees a number
    proposal_id = int(self.data.kwargs['id'])

    if not proposal_id:
      raise NotFound('Proposal id must be a positive number')

    self.data.proposal = GSoCProposal.get_by_id(
        proposal_id, parent=self.data.url_profile)

    if not self.data.proposal:
      raise NotFound('Requested proposal does not exist')

    org_key = GSoCProposal.org.get_value_for_datastore(self.data.proposal)

    self.data.proposal_org = self.data.getOrganization(org_key)

    parent_key = self.data.proposal.parent_key()
    if self.data.profile and parent_key == self.data.profile.key():
      self.data.proposer = self.data.profile
    else:
      self.data.proposer = self.data.proposal.parent()

  def projectFromKwargs(self):
    """Sets the project entity in RequestData object.
    """
    self.profileFromKwargs()
    assert access_checker.isSet(self.data.url_profile)

    # can safely call int, since regexp guarnatees a number
    project_id = int(self.data.kwargs['id'])

    if not project_id:
      raise NotFound(ugettext('Proposal id must be a positive number'))

    self.data.project = GSoCProject.get_by_id(
        project_id, parent=self.data.url_profile)

    if not self.data.project:
      raise NotFound(DEF_NO_PROJECT)

    parent_key = self.data.project.parent_key()
    if self.data.profile and parent_key == self.data.profile.key():
      self.data.project_owner = self.data.profile
    else:
      self.data.project_owner = self.data.project.parent()

  def connectionFromKwargs(self):
    """ Set the connection entity in the RequestData object.
    """

    self.userFromKwargs()

    self.data.connection = GSoCConnection.get_by_id(
        long(self.data.kwargs['id']), self.data.url_user)
    if not self.data.connection:
      raise AccessViolation('This connection does not exist.')

  def anonymousConnectionFromKwargs(self):
    """ Set the anonymous_connection entity in the RequestData object.
    """

    q = GSoCAnonymousConnection.all().filter('hash_id =', self.data.kwargs['key'])
    self.data.anonymous_connection = q.get()
    if not self.data.anonymous_connection:
      raise AccessViolation('Invalid key in url; unable to establish connection.')

  def studentEvaluationFromKwargs(self, raise_not_found=True):
    """Sets the student evaluation in RequestData object.

    Args:
      raise_not_found: iff False do not send 404 response.
    """
    # kwargs which defines a survey
    fields = ['sponsor', 'program', 'survey']

    key_name = '/'.join(['gsoc_program'] +
                        [self.data.kwargs[field] for field in fields])
    self.data.student_evaluation = ProjectSurvey.get_by_key_name(key_name)

    if raise_not_found and not self.data.student_evaluation:
      raise NotFound(DEF_NO_STUDENT_EVALUATION % key_name)

  def studentEvaluationRecordFromKwargs(self):
    """Sets the student evaluation record in RequestData object.
    """
    assert access_checker.isSet(self.data.student_evaluation)
    assert access_checker.isSet(self.data.project)

    self.data.organization = self.data.project.org

    q = GSoCProjectSurveyRecord.all()
    q.filter('project', self.data.project)
    q.filter('survey', self.data.student_evaluation)
    self.data.student_evaluation_record = q.get()

  def mentorEvaluationFromKwargs(self, raise_not_found=True):
    """Sets the mentor evaluation in RequestData object.

    Args:
      raise_not_found: iff False do not send 404 response.
    """
    # kwargs which defines an evaluation
    fields = ['sponsor', 'program', 'survey']

    key_name = '/'.join(['gsoc_program'] +
                        [self.data.kwargs[field] for field in fields])
    self.data.mentor_evaluation = GradingProjectSurvey.get_by_key_name(
        key_name)

    if raise_not_found and not self.data.mentor_evaluation:
      raise NotFound(DEF_NO_MENTOR_EVALUATION % key_name)

  def mentorEvaluationRecordFromKwargs(self):
    """Sets the mentor evaluation record in RequestData object.
    """
    assert access_checker.isSet(self.data.mentor_evaluation)
    assert access_checker.isSet(self.data.project)

    self.data.organization = self.data.project.org

    q = GSoCGradingProjectSurveyRecord.all()
    q.filter('project', self.data.project)
    q.filter('survey', self.data.mentor_evaluation)
    self.data.mentor_evaluation_record = q.get()

  def gradingSurveyRecordFromKwargs(self):
    """Sets a GradingSurveyRecord entry in the RequestData object.
    """
    self.projectFromKwargs()

    if not ('group' in self.data.kwargs and 'id' in self.data.kwargs):
      raise BadRequest(access_checker.DEF_NOT_VALID_REQUEST)

    # url regexp ensures that it is a digit
    record_id = long(self.data.kwargs['record'])
    group_id = long(self.data.kwargs['group'])

    record = GSoCGradingRecord.get_by_id(record_id, parent=self.data.project)

    if not record or record.grading_survey_group.key().id() != group_id:
      raise NotFound(DEF_NO_RECORD_FOUND)

    self.data.record = record

  def orgAppRecord(self, org_id):
    """Sets the org app record corresponding to the given org id.

    Args:
      org_id: The link_id of the organization.
    """
    assert access_checker.isSet(self.data.program)

    q = OrgAppRecord.all()
    q.filter('org_id', org_id)
    q.filter('program', self.data.program)
    record = q.get()

    if not record:
      raise NotFound(DEF_NO_ORG_APP_RECORD_FOUND)

    self.data.org_app_record = record

  def surveyGroupFromKwargs(self):
    """Sets the GradingSurveyGroup from kwargs.
    """
    assert access_checker.isSet(self.data.program)

    survey_group = GSoCGradingSurveyGroup.get_by_id(int(self.data.kwargs['id']))

    if not survey_group:
      raise NotFound('Requested GSoCGradingSurveyGroup does not exist')

    if survey_group.program.key() != self.data.program.key():
      raise NotFound(
          'Requested GSoCGradingSurveyGroup does not exist in this program')

    self.data.survey_group = survey_group

  def slotTransferEntities(self):
    assert access_checker.isSet(self.data.organization)

    self.data.slot_transfer_entities = \
        slot_transfer_logic.getSlotTransferEntitiesForOrg(
            self.data.organization)


class DeveloperMutator(access_checker.DeveloperMutator, Mutator):
  pass


class AccessChecker(access_checker.AccessChecker):
  """Helper classes for access checking in GSoC module.
  """

  def canStudentPropose(self):
    """Checks if the student is eligible to submit a proposal.
    """
    # check if the timeline allows submitting proposals
    self.studentSignupActive()

    # check how many proposals the student has already submitted 
    query = GSoCProposal.all()
    query.ancestor(self.data.profile)

    if query.count() >= self.data.program.apps_tasks_limit:
      # too many proposals access denied
      raise AccessViolation(DEF_MAX_PROPOSALS_REACHED % (
          self.data.program.apps_tasks_limit))

  def isStudentForSurvey(self):
    """Checks if the student can take survey for the project.
    """
    assert access_checker.isSet(self.data.profile)
    assert access_checker.isSet(self.data.project)

    self.isProjectInURLValid()

    project = self.data.project

    # check if the project belongs to the current user and if so he
    # can access the survey
    expected_profile_key = project.parent_key()
    if expected_profile_key != self.data.profile.key():
      raise AccessViolation(DEF_STUDENT_EVAL_DOES_NOT_BELONG_TO_YOU)

    # check if the project is still ongoing
    if project.status in ['invalid', 'withdrawn']:
      raise AccessViolation(DEF_EVAL_NOT_ACCESSIBLE_FOR_PROJECT)

    # check if the project has failed in a previous evaluation
    # TODO(Madhu): This still has a problem that when the project fails
    # in the final evaluation, the users will not be able to access the
    # midterm evaluation show page. Should be fixed.
    if project.status == 'failed' and project.failed_evaluations:
      failed_evals = db.get(project.failed_evaluations)
      fe_keynames = [f.grading_survey_group.grading_survey.key(
          ).id_or_name() for f in failed_evals]
      if self.data.student_evaluation.key().id_or_name() not in fe_keynames:
        raise AccessViolation(DEF_FAILED_PREVIOUS_EVAL % (
            self.data.student_evaluation.short_name.lower()))

  def isMentorForSurvey(self):
    """Checks if the user is the mentor for the project or org admin.
    """
    assert access_checker.isSet(self.data.project)

    self.isProjectInURLValid()

    project = self.data.project

    # check if the project is still ongoing
    if project.status in ['invalid', 'withdrawn']:
      raise AccessViolation(DEF_EVAL_NOT_ACCESSIBLE_FOR_PROJECT)

    # check if the project has failed in a previous evaluation
    # TODO(Madhu): This still has a problem that when the project fails
    # in the final evaluation, the users will not be able to access the
    # midterm evaluation show page. Should be fixed.
    if project.status == 'failed' and project.failed_evaluations:
      failed_evals = db.get(project.failed_evaluations)
      fe_keynames = [f.grading_survey_group.grading_survey.key(
          ).id_or_name() for f in failed_evals]
      if self.data.mentor_evaluation.key().id_or_name() not in fe_keynames:
        raise AccessViolation(DEF_FAILED_PREVIOUS_EVAL % (
            self.data.mentor_evaluation.short_name.lower()))

    if self.data.orgAdminFor(self.data.organization):
      return

    # check if the currently logged in user is the mentor or co-mentor
    # for the project in request or the org admin for the org
    if self.data.profile.key() not in project.mentors:
      raise AccessViolation(DEF_MENTOR_EVAL_DOES_NOT_BELONG_TO_YOU)

  def canApplyStudent(self, edit_url):
    """Checks if the user can apply as a student.
    """
    self.isLoggedIn()

    if self.data.profile and self.data.profile.student_info:
      raise RedirectRequest(edit_url)

    self.studentSignupActive()

    if not self.data.profile:
      return

    raise AccessViolation(
        DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT % self.data.program.name)

  def canStudentDownloadForms(self):
    """Checks if the user can download the forms.
    """
    self.isProfileActive()
    si = self.data.profile.student_info
    if si:
      if si.number_of_projects > 0:
        return
    raise AccessViolation(DEF_NOT_ALLOWED_TO_DOWNLOAD_FORM)

  def canTakeOrgApp(self):
    """A user can take the GSoC org app if he has org admin profile in the
    program.
    """
    self.isLoggedIn()

    program = self.data.program
    r = self.data.redirect.createProfile('org_admin')
    msg = DEF_NO_ORG_ADMIN_PROFILE % (
          program.short_name, r.urlOf('create_gsoc_profile', secure=True))

    if not self.data.user:
      raise AccessViolation(msg)

    q = GSoCProfile.all(keys_only=True)
    q.ancestor(self.data.user)
    q.filter('scope', self.data.program)
    q.filter('is_student', False)
    q.filter('status', 'active')
    gsoc_profile = q.get()
    if not gsoc_profile:
      raise AccessViolation(msg)

  def orgDoesnotExist(self, org_id):
    """Checks if the organization with the given ID doesn't exist.

    We cannot create organizations which are already created.

    Args:
      org_id: The link_id of the organization.
    """
    q = GSoCOrganization.all()
    q.filter('link_id', org_id)
    q.filter('scope', self.data.program)
    gsoc_org = q.get()

    if gsoc_org:
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=gsoc_org)

      edit_url = self.data.redirect.urlOf('edit_gsoc_org_profile')

      raise AccessViolation(DEF_ORG_EXISTS % (org_id, edit_url))

  def canCreateOrgProfile(self):
    """Checks if the current user is an admin or a backup admin for the org app
    and also check whether the organization application is accepted.
    """
    app_record = self.data.org_app_record

    if not app_record:
      raise NotFound(DEF_ORG_APP_NOT_FOUND % app_record.org_id)

    if self.data.user.key() not in [
        app_record.main_admin.key(), app_record.backup_admin.key()]:
      raise AccessViolation(DEF_NOT_ADMIN_FOR_ORG_APP)

    if app_record.status != 'accepted':
      raise AccessViolation(DEF_ORG_APP_NOT_ACCEPTED % (app_record.org_id))

  def isProjectCompleted(self):
    """Checks whether the project specified in the request is completed.
    """
    if len(self.data.project.passed_evaluations) < \
        project_logic.NUMBER_OF_EVALUATIONS:
      raise AccessViolation(DEF_PROJECT_NOT_COMPLETED)

  def canStudentUpdateProposal(self):
    """Checks if the student is eligible to submit a proposal.
    """
    assert access_checker.isSet(self.data.proposal)

    self.isActiveStudent()
    self.isProposalInURLValid()

    # check if the timeline allows updating proposals
    try:
      self.studentSignupActive()
    except AccessViolation:
      self.canStudentUpdateProposalPostSignup()

    # check if the proposal belongs to the current user
    expected_profile = self.data.proposal.parent()
    if expected_profile.key().name() != self.data.profile.key().name():
      error_msg = access_checker.DEF_ENTITY_DOES_NOT_BELONG_TO_YOU % {
          'model': 'GSoCProposal'
          }
      raise AccessViolation(error_msg)

    # check if the status allows the proposal to be updated
    status = self.data.proposal.status
    if status == 'ignored':
      raise AccessViolation(DEF_PROPOSAL_IGNORED_MESSAGE)
    elif status in ['invalid', 'accepted', 'rejected']:
      raise AccessViolation(access_checker.DEF_CANNOT_UPDATE_ENTITY % {
          'name': 'proposal'
          })

    # determine what can be done with the proposal
    if status == 'new' or status == 'pending':
      self.data.is_pending = True
    elif status == 'withdrawn':
      self.data.is_pending = False


class DeveloperAccessChecker(access_checker.DeveloperAccessChecker):
  pass
