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

import urllib

from django.utils.translation import ugettext

from google.appengine.ext import db

from melange.request import exception
from melange.request import links

from soc.models import document
from soc.models import org_app_record
from soc.models import program as program_model
from soc.views.helper.gdata_apis import oauth as oauth_helper

from summerofcode.logic import survey as survey_logic

DEF_AGREE_TO_TOS = ugettext(
    'You must agree to the <a href="%(tos_link)s">site-wide Terms of'
    ' Service</a> in your <a href="/user/edit_profile">User Profile</a>'
    ' in order to view this page.')

DEF_ALREADY_ADMIN = ugettext(
    'You cannot be an organization administrator for %s to access this page.')

DEF_ALREADY_MENTOR = ugettext(
    'You cannot be a mentor for %s to access this page.')

DEF_ALREADY_PARTICIPATING = ugettext(
    'You cannot become a Student because you are already participating '
    'in this program.')

DEF_ALREADY_PARTICIPATING_AS_STUDENT = ugettext(
    'You cannot register as a %s since you are already a '
    'student in %s.')

DEF_CANNOT_ACCESS_ORG_APP = ugettext(
    'You do not have access to this organization application.')

DEF_CANNOT_UPDATE_ENTITY = ugettext(
    'This %(name)s cannot be updated.')

DEF_DEV_LOGOUT_LOGIN = ugettext(
    'Please <a href="%%(sign_out)s">sign out</a>'
    ' and <a href="%%(sign_in)s">sign in</a>'
    ' again as %(role)s to view this page.')

DEF_ENTITY_DOES_NOT_BELONG_TO_YOU = ugettext(
    'This %(name)s does not belong to you.')

DEF_HAS_ALREADY_ROLE_FOR_ORG = ugettext(
    'You already have %(role)s role for %(org)s.')

DEF_ID_BASED_ENTITY_INVALID = ugettext(
    '%(model)s entity, whose id is %(id)s, is invalid at this time.')

DEF_ID_BASED_ENTITY_NOT_EXISTS = ugettext(
    '%(model)s entity, whose id is %(id)s, is does not exist.')

DEF_CONNECTION_CANNOT_BE_RESUBMITTED = ugettext(
    'Only withdrawn connections may be resubmitted.')

DEF_CONNECTION_UNACCESSIBLE = ugettext(
    'This connection is not accessible from this profile.')

DEF_IS_NOT_STUDENT = ugettext(
    'This page is inaccessible because you do not have a student role '
    'in the program.')

DEF_HAS_NO_PROJECT = ugettext(
    'This page is inaccessible because you do not have an accepted project '
    'in the program.')

DEF_IS_STUDENT = ugettext(
    'This page is inaccessible because you are registered as a student.')

DEF_NO_DOCUMENT = ugettext(
    'The document was not found')

DEF_NO_USERNAME = ugettext(
    'Username should not be empty')

DEF_NO_ORG_APP = ugettext(
    'The organization application for the program %s does not exist.')

DEF_NO_SLOT_TRANSFER = ugettext(
    'This page is inaccessible at this time. It is accessible only after '
    'the program administrator has made the slot allocations available and '
    'before %s')

DEF_NO_SUCH_PROGRAM = ugettext(
    'The url is wrong (no program was found).')

DEF_NO_SURVEY_ACCESS = ugettext (
    'You cannot take this evaluation because this evaluation is not created for'
    'your role in the program.')

DEF_NO_USER_LOGIN = ugettext(
    'Please create <a href="/user/create">User Profile</a>'
    ' in order to view this page.')

DEF_NO_USER_PROFILE = ugettext(
    'You must not have a User profile to visit this page.')

DEF_NO_USER = ugettext(
    'User with username %s does not exist.')

DEF_NOT_ADMIN = ugettext(
    'You need to be a organization administrator for %s to access this page.')

DEF_NOT_DEVELOPER = ugettext(
    'You need to be a site developer to access this page.')

DEF_NOT_HOST = ugettext(
    'You need to be a program administrator to access this page.')

DEF_NOT_MENTOR = ugettext(
    'You need to be a mentor for %s to access this page.')

DEF_NOT_PARTICIPATING = ugettext(
    'You are not participating in this program and have no access.')

DEF_NOT_PROPOSER = ugettext(
    'You are not allowed to perform this action since you are not the'
    'author(proposer) for this proposal.')

DEF_NOT_PUBLIC_DOCUMENT = ugettext(
    'This document is not publically readable.')

DEF_NOT_VALID_CONNECTION = ugettext(
    'This is not a valid connection.')

DEF_ORG_DOES_NOT_EXISTS = ugettext(
    'Organization, whose Organization ID %(link_id)s, does not exist in '
    '%(program)s.')

DEF_ORG_NOT_ACTIVE = ugettext(
    'Organization %(name)s is not active in %(program)s.')

DEF_PAGE_INACTIVE = ugettext(
    'This page is inactive at this time.')

DEF_PAGE_INACTIVE_BEFORE = ugettext(
    'This page is inactive before %s')

DEF_PAGE_INACTIVE_OUTSIDE = ugettext(
    'This page is inactive before %s and after %s.')

DEF_PROGRAM_NOT_VISIBLE = ugettext(
    'This page is inaccessible because %s is not visible at this time.')

DEF_PROGRAM_NOT_RUNNING = ugettext(
    'This page is inaccessible because %s is not running at this time.')

DEF_PROPOSAL_IGNORED_MESSAGE = ugettext(
    'An organization administrator has flagged this proposal to be '
    'ignored. If you think this is incorrect, contact an organization '
    'administrator to resolve the situation.')

DEF_PROPOSAL_MODIFICATION_REQUEST = ugettext(
    'If you would like to update this proposal, request your organization '
    'to which this proposal belongs, to grant permission to modify the '
    'proposal.')

DEF_PROPOSAL_NOT_PUBLIC = ugettext(
    'This proposal is not made public, '
    'and you are not the student who submitted the proposal, '
    'nor are you a mentor for the organization it was submitted to.')

DEF_PROFILE_INACTIVE = ugettext(
    'This page is inaccessible because your profile is inactive in '
    'the program at this time.')

DEF_NO_PROFILE = ugettext(
    'This page is inaccessible because you do not have a profile '
    'in the program at this time.')

DEF_SCOPE_INACTIVE = ugettext(
    'The scope for this request is not active.')

DEF_ID_BASED_ENTITY_NOT_EXISTS = ugettext(
    'The requested %(model)s entity whose id is %(id)s does not exist.')

DEF_KEYNAME_BASED_ENTITY_NOT_EXISTS = ugettext(
    'The requested %(model)s entity whose keyname is %(key_name)s does not '
    'exist.')

DEF_KEYNAME_BASED_ENTITY_INVALID = ugettext(
    '%(model)s entity, whose keyname is %(key_name)s, is invalid at this time.')

DEF_MESSAGING_NOT_ENABLED = ugettext(
    'Messaging is not allowed for this program.')

unset = object()


def isSet(value):
  """Returns true iff value is not unset."""
  return value is not unset


class Mutator(object):
  """Helper class for access checking.

  Mutates the data object as requested.
  """

  def __init__(self, data):
    self.data = data
    self.unsetAll()

  def unsetAll(self):
    self.data.action = unset
    self.data.document = unset
    self.data.key_name = unset
    self.data.scope_key_name = unset
    self.data.url_student_info = unset

  def documentKeyNameFromKwargs(self):
    """Returns the document key fields from kwargs.

    Returns False if not all fields were supplied/consumed.
    """
    fields = []
    kwargs = self.data.kwargs.copy()

    prefix = kwargs.pop('prefix', None)
    fields.append(prefix)

    if prefix in ['gsoc_program', 'gsoc_org', 'gci_program', 'gci_org']:
      fields.append(kwargs.pop('sponsor', None))
      fields.append(kwargs.pop('program', None))

    if prefix in ['gsoc_org', 'gci_org']:
      fields.append(kwargs.pop('organization', None))

    fields.append(kwargs.pop('document', None))

    if any(kwargs.values()):
      raise exception.BadRequest(message="Unexpected value for document url")

    if not all(fields):
      raise exception.BadRequest(message="Missing value for document url")

    self.data.scope_key_name = '/'.join(fields[1:-1])
    self.data.key_name = '/'.join(fields)
    self.data.document = document.Document.get_by_key_name(self.data.key_name)

  def studentFromKwargs(self):
    self.data.url_student_info = self.data.url_profile.student_info

    if not self.data.url_student_info:
      raise exception.NotFound(message='Requested user is not a student')

  def commentVisible(self, organization):
    """Determines whether or not a comment is visible to a user.

    Args:
      organization: The organization for which a mentor or org admin may be
          attemtping to view a connection.
    """
    assert isSet(self.data.url_user)

    self.data.public_comments_visible = False
    self.data.private_comments_visible = False

    # if the user is not logged in, no comments can be made
    if not self.data.user:
      return

    # if the current user is the proposer, he or she may access public comments
    if self.data.user.key() == self.data.url_user.key():
      self.data.public_comments_visible = True
      return

    # All the mentors and org admins from the organization may access public
    # and private comments.
    if self.data.mentorFor(organization):
      self.data.public_comments_visible = True
      self.data.private_comments_visible = True

  def host(self):
    assert isSet(self.data.user)

    if self.data.user.host_for:
      self.data.is_host = True

  def orgAppRecordIfIdInKwargs(self):
    """Sets the organization application in RequestData object."""
    assert self.data.org_app

    self.data.org_app_record = None

    org_app_id = self.data.kwargs.get('id')
    if org_app_id:
      self.data.org_app_record = org_app_record.OrgAppRecord.get_by_id(
          int(org_app_id))

      if not self.data.org_app_record:
        raise exception.NotFound(
            message=DEF_NO_ORG_APP % self.data.program.name)


class DeveloperMutator(Mutator):

  def commentVisible(self, organization):
    self.data.public_comments_visible = True
    self.data.private_comments_visible = True

  def hostFromKwargs(self):
    """Set the host entity for the given user in the kwargs.
    """
    self.data.host_user_key = None

    key_name = self.data.kwargs.get('link_id', '')
    if not key_name:
      self.host()
      if self.data.is_host:
        return
      else:
        raise exception.NotFound(message=DEF_NO_USERNAME)

    user_key = db.Key.from_path('User', key_name)

    if not user_key:
      raise exception.NotFound(message=DEF_NO_USER % key_name)

    self.data.host_user_key = user_key


class BaseAccessChecker(object):
  """Helper class for access checking.

  Should contain all access checks that apply to both regular users
  and developers.
  """

  def __init__(self, data):
    """Initializes the access checker object."""
    self.data = data

  def fail(self, message):
    """Raises an appropriate exception.UserError with the specified message."""
    raise exception.Forbidden(message=message)

  def isLoggedIn(self):
    """Ensures that the user is logged in."""
    if not self.data.gae_user:
      raise exception.LoginRequired()

  def isLoggedOut(self):
    """Ensures that the user is logged out."""
    if self.data.gae_user:
      raise exception.Redirect(links.LINKER.logout(self.data.request))

  def isUser(self):
    """Checks if the current user has an User entity.
    """
    self.isLoggedIn()

    if self.data.user:
      return

    raise exception.Forbidden(message=DEF_NO_USER_LOGIN)

  def isNotUser(self):
    """Checks if the current user does not have an User entity.

    To perform this check a User must be logged in.
    """
    self.isLoggedIn()

    if not self.data.user:
      return

    raise exception.Forbidden(message=DEF_NO_USER_PROFILE)


  def isDeveloper(self):
    """Checks if the current user is a Developer."""
    if self.data.is_developer:
      return

    raise exception.Forbidden(message=DEF_NOT_DEVELOPER)

  def hasProfile(self):
    """Checks if the user has a profile for the current program.
    """
    self.isLoggedIn()

    if self.data.profile:
      return

    raise exception.Forbidden(message=DEF_NO_PROFILE)

  def isProfileActive(self):
    """Checks if the profile of the current user is active.
    """
    self.hasProfile()

    if self.data.profile.status == 'active':
      return

    raise exception.Forbidden(message=DEF_PROFILE_INACTIVE)

  def canAccessGoogleDocs(self):
    """Checks if user has a valid access token to access Google Documents."""
    self.isUser()
    access_token = oauth_helper.getAccessToken(self.data.user)
    if not access_token: #TODO(orc.avs):check token is valid
      # TODO(nathaniel): This is complicated - add it to links.Linker?
      raise exception.Redirect('%s?%s' % (
          self.data.redirect.urlOf('gdata_oauth_redirect'),
          urllib.urlencode({'next': self.data.request.get_full_path()})))

  def isMessagingEnabled(self):
    """Checks whether the program has messaging enabled. If not, accessing
    views related to the messaging system is not allowed.
    """
    if not self.data.program:
      raise exception.NotFound(message=DEF_NO_SUCH_PROGRAM)

    self.isProgramVisible()

    if not self.data.program.messaging_enabled:
      raise exception.Forbidden(message=DEF_MESSAGING_NOT_ENABLED)


class DeveloperAccessChecker(BaseAccessChecker):
  """Helper class for access checking.

  Allows most checks.
  """

  def __getattr__(self, name):
    return lambda *args, **kwargs: None


class AccessChecker(BaseAccessChecker):
  """Helper class for access checking.
  """

  def isHost(self):
    """Checks whether the current user has a host role.
    """
    self.isLoggedIn()

    if self.data.is_host:
      return

    raise exception.Forbidden(message=DEF_NOT_HOST)

  def isProgramRunning(self):
    """Checks whether the program is running now by making sure the current
    data is between program start and end and the program is visible to
    normal users.
    """
    if not self.data.program:
      raise exception.NotFound(message=DEF_NO_SUCH_PROGRAM)

    self.isProgramVisible()

    if self.data.timeline.programActive():
      return

    raise exception.Forbidden(
        message=DEF_PROGRAM_NOT_RUNNING % self.data.program.name)

  def isProgramVisible(self):
    """Checks whether the program exists and is visible to the user.
    Visible programs are either in the visible.

    Programs are always visible to hosts.
    """
    if not self.data.program:
      raise exception.NotFound(message=DEF_NO_SUCH_PROGRAM)

    if self.data.program.status == program_model.STATUS_VISIBLE:
      return

    # TODO(nathaniel): Sure this is weird, but it's a consequence
    # of boolean-question-named methods having return-None-or-raise-
    # exception semantics.
    try:
      self.isHost()
      return
    except exception.UserError:
      raise exception.Forbidden(
          message=DEF_PROGRAM_NOT_VISIBLE % self.data.program.name)

  def acceptedOrgsAnnounced(self):
    """Checks if the accepted orgs have been announced.
    """
    self.isProgramVisible()

    if self.data.timeline.orgsAnnounced():
      return

    period = self.data.timeline.orgsAnnouncedOn()
    raise exception.Forbidden(message=DEF_PAGE_INACTIVE_BEFORE % period)

  def acceptedStudentsAnnounced(self):
    """Checks if the accepted students have been announced.
    """
    self.isProgramVisible()

    if self.data.timeline.studentsAnnounced():
      return

    period = self.data.timeline.studentsAnnouncedOn()
    raise exception.Forbidden(message=DEF_PAGE_INACTIVE_BEFORE % period)

  def canApplyNonStudent(self, role, edit_url):
    """Checks if the user can apply as a mentor or org admin.
    """
    self.isLoggedIn()

    if self.data.profile and not self.data.profile.student_info:
      raise exception.Redirect(edit_url)

    if role == 'org_admin' and self.data.timeline.beforeOrgSignupStart():
      period = self.data.timeline.orgSignupStart()
      raise exception.Forbidden(message=DEF_PAGE_INACTIVE_BEFORE % period)

    if role == 'mentor' and not self.data.timeline.orgsAnnounced():
      period = self.data.timeline.orgsAnnouncedOn()
      raise exception.Forbidden(message=DEF_PAGE_INACTIVE_BEFORE % period)

    if not self.data.profile:
      return

    raise exception.Forbidden(message=DEF_ALREADY_PARTICIPATING_AS_STUDENT % (
        role, self.data.program.name))

  def isActiveStudent(self):
    """Checks if the user is an active student.
    """
    self.isProfileActive()

    if self.data.student_info:
      return

    raise exception.Forbidden(message=DEF_IS_NOT_STUDENT)

  def isStudentWithProject(self):
    self.isActiveStudent()

    if self.data.student_info.number_of_projects > 0:
      return

    raise exception.Forbidden(message=DEF_HAS_NO_PROJECT)

  def notStudent(self):
    """Checks if the current user has a non-student profile.
    """
    self.isProfileActive()

    if not self.data.student_info:
      return

    raise exception.Forbidden(message=DEF_IS_STUDENT)

  def notOrgAdmin(self):
    """Checks if the user is not an admin.
    """
    self.isProfileActive()
    assert isSet(self.data.organization)

    if self.data.organization.key() not in self.data.profile.org_admin_for:
      return

    raise exception.Forbidden(
        message=DEF_ALREADY_ADMIN % self.data.organization.name)

  def notMentor(self):
    """Checks if the user is not a mentor.
    """
    self.isProfileActive()
    assert isSet(self.data.organization)

    if not self.data.mentorFor(self.data.organization):
      return

    raise exception.Forbidden(
        message=DEF_ALREADY_MENTOR % self.data.organization.name)

  def isOrgAdmin(self):
    """Checks if the user is an org admin.
    """
    assert isSet(self.data.organization)
    self.isOrgAdminForOrganization(self.data.organization)

  def isMentor(self):
    """Checks if the user is a mentor.
    """
    assert isSet(self.data.organization)
    self.isMentorForOrganization(self.data.organization)

  def isOrgAdminForOrganization(self, org):
    """Checks if the user is an admin for the specified organiztaion.
    """
    self.isProfileActive()

    if self.data.orgAdminFor(org):
      return

    raise exception.Forbidden(message=DEF_NOT_ADMIN % org.name)

  def isMentorForOrganization(self, org):
    """Checks if the user is a mentor for the specified organiztaion.
    """
    self.isProfileActive()

    if self.data.mentorFor(org):
      return

    raise exception.Forbidden(message=DEF_NOT_MENTOR % org.name)

  def isOrganizationInURLActive(self):
    """Checks if the organization in URL exists and if its status is active.
    """
    assert isSet(self.data.organization)

    if not self.data.organization:
      error_msg = DEF_ORG_DOES_NOT_EXISTS % {
          'link_id': self.data.kwargs['organization'],
          'program': self.data.program.name
          }
      raise exception.Forbidden(message=error_msg)

    self.isOrganizationActive(self.data.organization)

  def isOrganizationActive(self, organization):
    """Checks if the specified organization is active.
    """
    if organization.status != 'active':
      error_msg = DEF_ORG_NOT_ACTIVE % {
          'name': organization.name,
          'program': self.data.program.name
          }
      raise exception.Forbidden(message=error_msg)

  def isProposalInURLValid(self):
    """Checks if the proposal in URL exists.
    """
    if not self.data.url_proposal:
      error_msg = DEF_ID_BASED_ENTITY_NOT_EXISTS % {
          'model': 'GSoCProposal',
          'id': self.data.kwargs['id']
          }
      raise exception.Forbidden(message=error_msg)

    if self.data.url_proposal.status == 'invalid':
      error_msg = DEF_ID_BASED_ENTITY_INVALID % {
          'model': 'GSoCProposal',
          'id': self.data.kwargs['id'],
          }
      raise exception.Forbidden(message=error_msg)

  def studentSignupActive(self):
    """Checks if the student signup period is active.
    """
    self.isProgramVisible()

    if self.data.timeline.studentSignup():
      return

    raise exception.Forbidden(message=DEF_PAGE_INACTIVE_OUTSIDE % (
        self.data.timeline.studentsSignupBetween()))

  def canStudentUpdateProposalPostSignup(self):
    """Checks if the student signup deadline has passed.
    """
    self.isProgramVisible()

    if (self.data.timeline.afterStudentSignupEnd() and
        self.data.url_proposal.is_editable_post_deadline):
      return

    violation_message = '%s %s'% ((DEF_PAGE_INACTIVE_OUTSIDE %
        self.data.timeline.studentsSignupBetween()),
        DEF_PROPOSAL_MODIFICATION_REQUEST)
    raise exception.Forbidden(message=violation_message)

  def canStudentUpdateProposal(self):
    """Checks if the student is eligible to submit a proposal.
    """
    assert isSet(self.data.url_proposal)

    self.isActiveStudent()
    self.isProposalInURLValid()

    # check if the timeline allows updating proposals
    # TODO(nathaniel): This remains weird.
    try:
      self.studentSignupActive()
    except exception.UserError:
      self.canStudentUpdateProposalPostSignup()

    # check if the proposal belongs to the current user
    expected_profile = self.data.url_proposal.parent()
    if expected_profile.key().name() != self.data.profile.key().name():
      error_msg = DEF_ENTITY_DOES_NOT_BELONG_TO_YOU % {
          'model': 'GSoCProposal',
          'name': 'request'
          }
      raise exception.Forbidden(message=error_msg)

    # check if the status allows the proposal to be updated
    status = self.data.url_proposal.status
    if status == 'ignored':
      raise exception.Forbidden(message=DEF_PROPOSAL_IGNORED_MESSAGE)
    elif status in ['invalid', 'accepted', 'rejected']:
      raise exception.Forbidden(message=DEF_CANNOT_UPDATE_ENTITY % {
          'model': 'GSoCProposal'
          })

    # determine what can be done with the proposal
    if status == 'new' or status == 'pending':
      self.data.is_pending = True
    elif status == 'withdrawn':
      self.data.is_pending = False

  def canOrgMemberAccessConnection(self):
    """Checks if the current user is an org admin allowed to access a
    Connection entity.
    """
    assert isSet(self.data.profile)
    # Org admins may only view a connection if they are admins for the org
    # involved in the connection.
    org_key = self.data.url_connection.organization.key()
    if org_key not in self.data.profile.org_admin_for:
      raise exception.Forbidden(message=DEF_CONNECTION_UNACCESSIBLE)

  def canUserAccessConnection(self):
    """Checks if the current user is allowed to access a Connection entity.
    """
    assert isSet(self.data.profile)
    # Only org admins and the user involved in the connection may view it.
    if self.data.url_connection.parent_key() != self.data.profile.key():
      raise exception.Forbidden(message=DEF_CONNECTION_UNACCESSIBLE)


  def canAccessProposalEntity(self):
    """Checks if the current user is allowed to access a Proposal entity.
    """
    assert isSet(self.data.url_user)

    # if the proposal is public, everyone may access it
    if self.data.url_proposal.is_publicly_visible:
      return

    if not self.data.user:
      raise exception.Forbidden(message=DEF_PROPOSAL_NOT_PUBLIC)

    self.isProfileActive()
    # if the current user is the proposer, he or she may access it
    if self.data.user.key() == self.data.url_user.key():
      return

    # all the mentors and org admins from the organization may access it
    if self.data.mentorFor(self.data.url_proposal.org):
      return

    raise exception.Forbidden(message=DEF_PROPOSAL_NOT_PUBLIC)

  def canEditDocument(self):
    self.isHost()

  def canViewDocument(self):
    """Checks if the specified user can see the document.
    """
    assert isSet(self.data.document)

    if not self.data.document:
      raise exception.NotFound(message=DEF_NO_DOCUMENT)

    self.isProgramVisible()

    if self.data.document.read_access == 'public':
      return

    raise exception.Forbidden(message=DEF_NOT_PUBLIC_DOCUMENT)

  def isProposer(self):
    """Checks if the current user is the author of the proposal.
    """
    self.isProgramVisible()
    self.isProfileActive()

    if self.data.url_profile.key() == self.data.profile.key():
      return

    raise exception.Forbidden(message=DEF_NOT_PROPOSER)

  def isSlotTransferActive(self):
    """Checks if the slot transfers are active at the time.
    """
    assert isSet(self.data.program)
    assert isSet(self.data.timeline)

    if (self.data.program.allocations_visible and
        self.data.timeline.beforeStudentsAnnounced()):
      return

    raise exception.Forbidden(message=DEF_NO_SLOT_TRANSFER % (
        self.data.timeline.studentsAnnouncedOn()))

  def isProjectInURLValid(self):
    """Checks if the project in URL exists.
    """
    assert isSet(self.data.project)

    if not self.data.project:
      error_msg = DEF_ID_BASED_ENTITY_NOT_EXISTS % {
          'model': 'GSoCProject',
          'id': self.data.kwargs['id']
          }
      raise exception.Forbidden(message=error_msg)

    if self.data.project.status == 'invalid':
      error_msg = DEF_ID_BASED_ENTITY_INVALID % {
          'model': 'GSoCProject',
          'id': self.data.kwargs['id'],
          }
      raise exception.Forbidden(message=error_msg)

  def canStudentUpdateProject(self):
    """Checks if the student can edit the project details.
    """
    assert isSet(self.data.program)
    assert isSet(self.data.timeline)
    assert isSet(self.data.project)
    assert isSet(self.data.project_owner)

    self.isProjectInURLValid()

    # check if the timeline allows updating project
    self.isProgramVisible()
    self.acceptedStudentsAnnounced()

    # check if the project belongs to the current user
    expected_profile_key = self.data.project.parent_key()
    if expected_profile_key != self.data.profile.key():
      error_msg = DEF_ENTITY_DOES_NOT_BELONG_TO_YOU % {
          'name': 'project'
          }
      raise exception.Forbidden(message=error_msg)

    # check if the status allows the project to be updated
    if self.data.project.status in ['invalid', 'withdrawn', 'failed']:
      raise exception.Forbidden(message=DEF_CANNOT_UPDATE_ENTITY % {
          'name': 'project'
          })

  def isSurveyActive(self, survey, show_url=None):
    """Checks if the survey in the request data is active.

    Args:
      survey: the survey entity for which the access must be checked
      show_url: The survey show page url to which the user must be
          redirected to
    """
    assert isSet(self.data.program)
    assert isSet(self.data.timeline)

    if self.data.timeline.surveyPeriod(survey):
      return

    if self.data.timeline.afterSurveyEnd(survey) and show_url:
      raise exception.Redirect(show_url)

    raise exception.Forbidden(message=DEF_PAGE_INACTIVE_OUTSIDE % (
        survey.survey_start, survey.survey_end))

  def isStudentSurveyActive(self, survey, student, show_url=None):
    """Checks if the student survey can be taken by the specified student.

    Args:
      survey: a survey entity.
      student: a student profile entity.
      show_url: survey show page URL to which the user should be redirected.

    Raises:
      exception.Redirect: if the active period is over and URL to redirect
        is specified.
      exception.Forbidden: if it is not possible to access survey
        at this time.
    """
    active_period = survey_logic.getSurveyActivePeriod(survey)
    if active_period.state != survey_logic.IN_PERIOD_STATE:
      # try finding a personal extension for the student
      extension = survey_logic.getPersonalExtension(
          student.key(), survey.key())
      active_period = survey_logic.getSurveyActivePeriod(
          survey, extension=extension)

      if active_period.state == survey_logic.POST_PERIOD_STATE and show_url:
        raise exception.Redirect(show_url)

      if active_period.state != survey_logic.IN_PERIOD_STATE:
        raise exception.Forbidden(message=DEF_PAGE_INACTIVE_OUTSIDE % (
            active_period.start, active_period.end))

  def canUserTakeSurvey(self, survey, taking_access='user'):
    """Checks if the user with the given profile can take the survey.

    Args:
      survey: the survey entity for which the access must be checked
    """
    assert isSet(self.data.program)
    assert isSet(self.data.timeline)

    self.isProjectInURLValid()

    if taking_access == 'student':
      self.isActiveStudent()
      return
    elif taking_access == 'org':
      assert isSet(self.data.organization)

      self.isMentor()
      return
    elif taking_access == 'user':
      self.isUser()
      return

    raise exception.Forbidden(message=DEF_NO_SURVEY_ACCESS)

  def canRetakeOrgApp(self):
    """Checks if the user can edit the org app record.
    """
    assert isSet(self.data.org_app_record)

    self.isUser()

    allowed_keys = [self.data.org_app_record.main_admin.key(),
                    self.data.org_app_record.backup_admin.key()]
    if self.data.user.key() not in allowed_keys:
      raise exception.Forbidden(message=DEF_CANNOT_ACCESS_ORG_APP)

  def canViewOrgApp(self):
    """Checks if the user can view the org app record. Only the org admins and
    hosts are allowed to view.
    """
    assert isSet(self.data.org_app_record)

    # TODO(nathaniel): Yep, this is weird.
    try:
      self.canRetakeOrgApp()
      return
    except exception.UserError:
      pass

    self.isHost()
