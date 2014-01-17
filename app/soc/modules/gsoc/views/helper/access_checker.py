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

from google.appengine.ext import ndb
from google.appengine.ext import db

from django.utils.translation import ugettext

from melange.request import exception

from soc.logic import validate
from soc.models.org_app_record import OrgAppRecord
from soc.views.helper import access_checker

from melange.logic import connection as connection_logic
from melange.logic import user as user_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import slot_transfer as slot_transfer_logic
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord


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

DEF_NOT_ALLOWED_TO_UPLOAD_FORM = ugettext(
    'You are not allowed to upload forms.')

DEF_PROJECT_NOT_COMPLETED = ugettext(
    'The specified project has not been completed')

DEF_PROPOSAL_IGNORED_MESSAGE = ugettext(
    'An organization administrator has flagged this proposal to be '
    'ignored. If you think this is incorrect, contact an organization '
    'administrator to resolve the situation.')


class Mutator(access_checker.Mutator):
  """Mutator for the GSoC module.
  """

  def __init__(self, data):
    super(Mutator, self).__init__(data)

  def anonymousConnectionFromKwargs(self):
    """Set the anonymous_connection entity in the RequestData object.
    """
    token = self.data.kwargs['key']
    connection = connection_logic.queryAnonymousConnectionForToken(token)
    if connection:
      self.data.anonymous_connection = connection
    else:
      raise exception.Forbidden(
          message='Invalid key in url; unable to establish connection.')

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
      raise exception.NotFound(message=DEF_NO_STUDENT_EVALUATION % key_name)

  def studentEvaluationRecordFromKwargs(self):
    """Sets the student evaluation record in RequestData object.
    """
    assert access_checker.isSet(self.data.student_evaluation)

    # TODO(daniel): get rid of this ugly mutation!
    org_key = project_model.GSoCProject.org.get_value_for_datastore(
        self.data.url_project)
    self.data.organization = ndb.Key.from_old_key(org_key).get()

    q = GSoCProjectSurveyRecord.all()
    q.filter('project', self.data.url_project)
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
      raise exception.NotFound(message=DEF_NO_MENTOR_EVALUATION % key_name)

  def mentorEvaluationRecordFromKwargs(self):
    """Sets the mentor evaluation record in RequestData object.
    """
    assert access_checker.isSet(self.data.mentor_evaluation)

    # TODO(daniel): get rid of this ugly mutation!
    org_key = project_model.GSoCProject.org.get_value_for_datastore(
        self.data.url_project)
    self.data.organization = ndb.Key.from_old_key(org_key).get()

    q = GSoCGradingProjectSurveyRecord.all()
    q.filter('project', self.data.url_project)
    q.filter('survey', self.data.mentor_evaluation)
    self.data.mentor_evaluation_record = q.get()

  def gradingSurveyRecordFromKwargs(self):
    """Sets a GradingSurveyRecord entry in the RequestData object.
    """
    if not ('group' in self.data.kwargs and 'id' in self.data.kwargs):
      raise exception.BadRequest(message=access_checker.DEF_NOT_VALID_REQUEST)

    # url regexp ensures that it is a digit
    record_id = long(self.data.kwargs['record'])
    group_id = long(self.data.kwargs['group'])

    record = GSoCGradingRecord.get_by_id(
        record_id, parent=self.data.url_project)

    if not record or record.grading_survey_group.key().id() != group_id:
      raise exception.NotFound(message=DEF_NO_RECORD_FOUND)

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
      raise exception.NotFound(message=DEF_NO_ORG_APP_RECORD_FOUND)

    self.data.org_app_record = record

  def surveyGroupFromKwargs(self):
    """Sets the GradingSurveyGroup from kwargs.
    """
    assert access_checker.isSet(self.data.program)

    survey_group = GSoCGradingSurveyGroup.get_by_id(int(self.data.kwargs['id']))

    if not survey_group:
      raise exception.NotFound(
          message='Requested GSoCGradingSurveyGroup does not exist')

    if survey_group.program.key() != self.data.program.key():
      raise exception.NotFound(
          message=('Requested GSoCGradingSurveyGroup '
                   'does not exist in this program'))

    self.data.survey_group = survey_group

  def slotTransferEntities(self):
    self.data.slot_transfer_entities = (
        slot_transfer_logic.getSlotTransferEntitiesForOrg(
            self.data.url_ndb_org.key))


class AccessChecker(access_checker.AccessChecker):
  """Helper classes for access checking in GSoC module.
  """

  def canStudentPropose(self):
    """Checks if the student is eligible to submit a proposal.
    """
    # check if the timeline allows submitting proposals
    self.studentSignupActive()

    # check how many proposals the student has already submitted
    # TODO(daniel): replace this query with checking on number_of_proposals
    query = proposal_model.GSoCProposal.all()
    query.ancestor(self.data.ndb_profile.key.to_old_key())
    query.filter(proposal_model.GSoCProposal.status.name, 'pending')

    if query.count() >= self.data.program.apps_tasks_limit:
      # too many proposals access denied
      raise exception.Forbidden(message=DEF_MAX_PROPOSALS_REACHED % (
          self.data.program.apps_tasks_limit))

  def isStudentForSurvey(self):
    """Checks if the student can take survey for the project.
    """
    self.isProjectInURLValid()

    # check if the project belongs to the current user and if so he
    # can access the survey
    expected_profile_key = self.data.url_project.parent_key()
    if expected_profile_key != self.data.ndb_profile.key.to_old_key():
      raise exception.Forbidden(
          message=DEF_STUDENT_EVAL_DOES_NOT_BELONG_TO_YOU)

    # check if the project is still ongoing
    if self.data.url_project.status in ['invalid', 'withdrawn']:
      raise exception.Forbidden(message=DEF_EVAL_NOT_ACCESSIBLE_FOR_PROJECT)

    # check if the project has failed in a previous evaluation
    # TODO(Madhu): This still has a problem that when the project fails
    # in the final evaluation, the users will not be able to access the
    # midterm evaluation show page. Should be fixed.
    if (self.data.url_project.status == 'failed'
        and self.data.url_project.failed_evaluations):
      failed_evals = db.get(self.data.url_project.failed_evaluations)
      fe_keynames = [f.grading_survey_group.grading_survey.key(
          ).id_or_name() for f in failed_evals]
      if self.data.student_evaluation.key().id_or_name() not in fe_keynames:
        raise exception.Forbidden(message=DEF_FAILED_PREVIOUS_EVAL % (
            self.data.student_evaluation.short_name.lower()))

  def isMentorForSurvey(self):
    """Checks if the user is the mentor for the project or org admin.
    """
    self.isProjectInURLValid()

    # check if the project is still ongoing
    if self.data.url_project.status in ['invalid', 'withdrawn']:
      raise exception.Forbidden(message=DEF_EVAL_NOT_ACCESSIBLE_FOR_PROJECT)

    # check if the project has failed in a previous evaluation
    # TODO(Madhu): This still has a problem that when the project fails
    # in the final evaluation, the users will not be able to access the
    # midterm evaluation show page. Should be fixed.
    if (self.data.url_project.status == 'failed'
        and self.data.url_project.failed_evaluations):
      failed_evals = db.get(self.data.url_project.failed_evaluations)
      fe_keynames = [f.grading_survey_group.grading_survey.key(
          ).id_or_name() for f in failed_evals]
      if self.data.mentor_evaluation.key().id_or_name() not in fe_keynames:
        raise exception.Forbidden(message=DEF_FAILED_PREVIOUS_EVAL % (
            self.data.mentor_evaluation.short_name.lower()))

    if self.data.orgAdminFor(self.data.url_ndb_org.key):
      return

    # check if the currently logged in user is the mentor or co-mentor
    # for the project in request or the org admin for the org
    if self.data.profile.key.to_old_key() not in self.data.url_project.mentors:
      raise exception.Forbidden(message=DEF_MENTOR_EVAL_DOES_NOT_BELONG_TO_YOU)

  def canApplyStudent(self, edit_url):
    """Checks if the user can apply as a student.
    """
    self.isLoggedIn()

    if self.data.ndb_profile and self.data.ndb_profile.is_student:
      raise exception.Redirect(edit_url)

    self.studentSignupActive()

    if not self.data.ndb_profile:
      return

    raise exception.Forbidden(message=
        DEF_ALREADY_PARTICIPATING_AS_NON_STUDENT % self.data.program.name)

  def canStudentUploadForms(self):
    """Checks if the current user can upload student forms.

    Raises:
      exception.UserError: If the current user is not allowed
          to upload forms.
    """
    self.isStudentWithProject()

    # check if the forms can already be submitted
    if not self.data.timeline.afterFormSubmissionStart():
      raise exception.Forbidden(message=DEF_NOT_ALLOWED_TO_UPLOAD_FORM)

    # POST requests actually uploading a form are not allowed after
    # the program ends
    if self.data.POST:
      self.isProgramRunning()

  def canStudentDownloadForms(self):
    """Checks if the user can download the forms.
    """
    self.isProfileActive()
    if not (self.data.ndb_profile.is_student
        and self.data.ndb_profile.student_data.number_of_projects):
      raise exception.Forbidden(message=DEF_NOT_ALLOWED_TO_DOWNLOAD_FORM)

  def canTakeOrgApp(self):
    """A user can take the GSoC org app if he has org admin profile in the
    program.
    """
    self.isLoggedIn()

    program = self.data.program

    # TODO(nathaniel): Eliminate this state-setting call.
    self.data.redirect.createProfile('org_admin')

    msg = DEF_NO_ORG_ADMIN_PROFILE % (
          program.short_name,
          self.data.redirect.urlOf('create_gsoc_profile', secure=True))

    if not self.data.user:
      raise exception.Forbidden(message=msg)

    if not validate.hasNonStudentProfileForProgram(
        self.data.user, program, GSoCProfile):
      raise exception.Forbidden(message=msg)

  def canCreateOrgProfile(self):
    """Checks if the current user is an admin or a backup admin for the org app
    and also check whether the organization application is accepted.
    """
    app_record = self.data.org_app_record

    if not app_record:
      raise exception.NotFound(
          message=DEF_ORG_APP_NOT_FOUND % app_record.org_id)

    if self.data.user.key() not in [
        app_record.main_admin.key(), app_record.backup_admin.key()]:
      raise exception.Forbidden(message=DEF_NOT_ADMIN_FOR_ORG_APP)

    if app_record.status != 'accepted':
      raise exception.Forbidden(
          message=DEF_ORG_APP_NOT_ACCEPTED % (app_record.org_id))

  def isProjectCompleted(self):
    """Checks whether the project specified in the request is completed.
    """
    if len(self.data.url_project.passed_evaluations) < \
        project_logic.NUMBER_OF_EVALUATIONS:
      raise exception.Forbidden(message=DEF_PROJECT_NOT_COMPLETED)

  def canStudentUpdateProposal(self):
    """Checks if the student is eligible to submit a proposal.
    """
    self.isActiveStudent()
    self.isProposalInURLValid()

    # check if the timeline allows updating proposals
    # TODO(nathaniel): Yep, this is weird.
    try:
      self.studentSignupActive()
    except exception.UserError:
      self.canStudentUpdateProposalPostSignup()

    # check if the proposal belongs to the current user
    expected_profile_key = self.data.url_proposal.parent_key()
    if expected_profile_key != self.data.ndb_profile.key.to_old_key():
      error_msg = access_checker.DEF_ENTITY_DOES_NOT_BELONG_TO_YOU % {
          'name': 'proposal'
          }
      raise exception.Forbidden(message=error_msg)

    # check if the status allows the proposal to be updated
    status = self.data.url_proposal.status
    if status == 'ignored':
      raise exception.Forbidden(message=DEF_PROPOSAL_IGNORED_MESSAGE)
    elif status in ['invalid', proposal_model.STATUS_ACCEPTED, 'rejected']:
      raise exception.Forbidden(
          message=access_checker.DEF_CANNOT_UPDATE_ENTITY % {
             'name': 'proposal'
              })

    # determine what can be done with the proposal
    if status == 'new' or status == 'pending':
      self.data.is_pending = True
    elif status == 'withdrawn':
      self.data.is_pending = False

  def canStudentUpdateProject(self):
    """Checks if the student can edit the project details."""
    assert access_checker.isSet(self.data.program)
    assert access_checker.isSet(self.data.timeline)

    self.isProjectInURLValid()

    # check if the timeline allows updating project
    self.isProgramVisible()
    self.acceptedStudentsAnnounced()

    # check if the current used is an active student
    self.isActiveStudent()

    # check if the project belongs to the current user
    expected_profile_key = self.data.url_project.parent_key()
    if expected_profile_key != self.data.ndb_profile.key.to_old_key():
      error_msg = access_checker.DEF_ENTITY_DOES_NOT_BELONG_TO_YOU % {
          'name': 'project'
          }
      raise exception.Forbidden(message=error_msg)

    # check if the status allows the project to be updated
    if self.data.url_project.status in ['invalid', 'withdrawn', 'failed']:
      raise exception.Forbidden(
          message=access_checker.DEF_CANNOT_UPDATE_ENTITY % {
              'name': 'project'
              })

  def canOrgAdminUpdateProject(self):
    """Checks if the organization admin can edit the project details."""
    assert access_checker.isSet(self.data.program)
    assert access_checker.isSet(self.data.timeline)

    self.isProjectInURLValid()

    # check if the timeline allows updating project
    self.isProgramVisible()
    self.acceptedStudentsAnnounced()

    # check if the person is an organization admin for the organization
    # to which the project was assigned
    org_key = project_model.GSoCProject.org.get_value_for_datastore(
        self.data.url_project)
    self.isOrgAdminForOrganization(org_key)

    # check if the status allows the project to be updated
    if self.data.url_project.status in ['invalid', 'withdrawn', 'failed']:
      raise exception.Forbidden(
          message=access_checker.DEF_CANNOT_UPDATE_ENTITY % {
              'name': 'project'
              })

  def canUpdateProject(self):
    """Checks if the current user is allowed to update project details."""
    self.isLoggedIn()
    if not user_logic.isHostForProgram(
        self.data.ndb_user, self.data.program.key()):
      self.hasProfile()
      if self.data.ndb_profile.is_student:
        # check if this is a student trying to update their project
        self.canStudentUpdateProject()
      elif self.data.is_org_admin:
        # check if this is an organization admin trying to update a project
        # belonging to one the students working for their organization
        self.canOrgAdminUpdateProject()
      else:
        raise exception.Forbidden(
            message=access_checker.DEF_CANNOT_UPDATE_ENTITY % {
                'name': 'project'
            })


# TODO(nathaniel): Silly class.
class DeveloperAccessChecker(access_checker.DeveloperAccessChecker):
  pass
