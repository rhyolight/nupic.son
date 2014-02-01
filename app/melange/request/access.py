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

"""Classes for checking access to pages."""

from django.utils import translation

from melange.logic import user as user_logic
from melange.models import profile as profile_model
from melange.request import exception
from melange.request import links

from soc.models import program as program_model


_MESSAGE_NOT_PROGRAM_ADMINISTRATOR = translation.ugettext(
    'You need to be a program administrator to access this page.')

_MESSAGE_NOT_DEVELOPER = translation.ugettext(
    'This page is only accessible to developers.')

_MESSAGE_HAS_PROFILE = translation.ugettext(
    'This page is accessible only to users without a profile.')

_MESSAGE_NO_PROFILE = translation.ugettext(
    'Active profile is required to access this page.')

_MESSAGE_NO_URL_PROFILE = translation.ugettext(
    'Active profile for %s is required to access this page.')

_MESSAGE_PROGRAM_NOT_EXISTING = translation.ugettext(
    'Requested program does not exist.')

_MESSAGE_PROGRAM_NOT_ACTIVE = translation.ugettext(
    'Requested program is not active at this moment.')

_MESSAGE_STUDENTS_DENIED = translation.ugettext(
    'This page is not accessible to users with student profiles.')

_MESSAGE_NOT_USER_IN_URL = translation.ugettext(
    'You are not logged in as the user in the URL.')

_MESSAGE_NOT_ORG_ADMIN_FOR_ORG = translation.ugettext(
    'You are not organization administrator for %s')

_MESSAGE_INACTIVE_BEFORE = translation.ugettext(
    'This page is inactive before %s.')

_MESSAGE_INACTIVE_OUTSIDE = translation.ugettext(
    'This page is inactive before %s and after %s.')

def ensureLoggedIn(data):
  """Ensures that the user is logged in.

  Args:
    data: request_data.RequestData for the current request.

  Raises:
    exception.LoginRequired: If the user is not logged in.
  """
  if not data.gae_user:
    raise exception.LoginRequired()


def ensureLoggedOut(data):
  """Ensures that the user is logged out.

  Args:
    data: request_data.RequestData for the current request.

  Raises:
    exception.Redirect: If the user is logged in this
      exception will redirect them to the logout page.
  """
  if data.gae_user:
    raise exception.Redirect(links.LINKER.logout(data.request))


class AccessChecker(object):
  """Interface for page access checkers."""

  def checkAccess(self, data, check):
    """Ensure that the user's request should be satisfied.

    Implementations of this method must not effect mutations of the
    passed parameters (or anything else).

    Args:
      data: A request_data.RequestData describing the current request.
      check: An access_checker.AccessChecker object.

    Raises:
      exception.LoginRequired: Indicating that the user is not logged
        in, but must log in to access the resource specified in their
        request.
      exception.Redirect: Indicating that the user is to be redirected
        to another URL.
      exception.UserError: Describing what was erroneous about the
        user's request and describing an appropriate response.
      exception.ServerError: Describing some problem that arose during
        request processing and describing an appropriate response.
    """
    raise NotImplementedError()


class AllAllowedAccessChecker(AccessChecker):
  """AccessChecker that allows all requests for access."""

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    pass

ALL_ALLOWED_ACCESS_CHECKER = AllAllowedAccessChecker()


# TODO(nathaniel): There's some ninja polymorphism to be addressed here -
# RequestData doesn't actually have an "is_host" attribute, but its two
# major subclasses (the GCI-specific and GSoC-specific RequestData classes)
# both do, so this "works" but isn't safe or sanely testable.
class ProgramAdministratorAccessChecker(AccessChecker):
  """AccessChecker that ensures that the user is a program administrator."""

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if data.is_developer:
      # NOTE(nathaniel): Developers are given all the powers of
      # program administrators.
      return
    elif not data.gae_user:
      raise exception.LoginRequired()
    elif not user_logic.isHostForProgram(data.ndb_user, data.program.key()):
      raise exception.Forbidden(message=_MESSAGE_NOT_PROGRAM_ADMINISTRATOR)

PROGRAM_ADMINISTRATOR_ACCESS_CHECKER = ProgramAdministratorAccessChecker()


# TODO(nathaniel): Eliminate this or make it a
# "SiteAdministratorAccessChecker" - there should be no aspects of Melange
# that require developer action or are limited only to developers.
class DeveloperAccessChecker(AccessChecker):
  """AccessChecker that ensures that the user is a developer."""

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not data.is_developer:
      raise exception.Forbidden(message=_MESSAGE_NOT_DEVELOPER)

DEVELOPER_ACCESS_CHECKER = DeveloperAccessChecker()


class ConjuctionAccessChecker(AccessChecker):
  """Aggregated access checker that holds a collection of other access
  checkers and ensures that access is granted only if each of those checkers
  grants access individually."""

  def __init__(self, checkers):
    """Initializes a new instance of the access checker.

    Args:
      checkers: list of AccessChecker objects to be examined by this checker.
    """
    self._checkers = checkers

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    for checker in self._checkers:
      checker.checkAccess(data, check)


class NonStudentUrlProfileAccessChecker(AccessChecker):
  """AccessChecker that ensures that the URL user has a non-student profile."""

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if data.url_ndb_profile.status != profile_model.Status.ACTIVE:
      raise exception.Forbidden(
          message=_MESSAGE_NO_URL_PROFILE % data.kwargs['user'])

    if data.url_ndb_profile.is_student:
      raise exception.Forbidden(message=_MESSAGE_STUDENTS_DENIED)

NON_STUDENT_URL_PROFILE_ACCESS_CHECKER = NonStudentUrlProfileAccessChecker()


class NonStudentProfileAccessChecker(AccessChecker):
  """AccessChecker that ensures that the currently logged-in user
  has a non-student profile."""

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if (not data.ndb_profile
        or data.ndb_profile.status != profile_model.Status.ACTIVE):
      raise exception.Forbidden(message=_MESSAGE_NO_PROFILE)

    if data.ndb_profile.is_student:
      raise exception.Forbidden(message=_MESSAGE_STUDENTS_DENIED)

NON_STUDENT_PROFILE_ACCESS_CHECKER = NonStudentProfileAccessChecker()


class ProgramActiveAccessChecker(AccessChecker):
  """AccessChecker that ensures that the program is currently active.

  A program is considered active when the current point of time comes after
  its start date and before its end date. Additionally, its status has to
  be set to visible.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not data.program:
      raise exception.NotFound(message=_MESSAGE_PROGRAM_NOT_EXISTING)

    if (data.program.status != program_model.STATUS_VISIBLE
        or not data.timeline.programActive()):
      raise exception.Forbidden(message=_MESSAGE_PROGRAM_NOT_ACTIVE)

PROGRAM_ACTIVE_ACCESS_CHECKER = ProgramActiveAccessChecker()


class IsUrlUserAccessChecker(AccessChecker):
  """AccessChecker that ensures that the logged in user is the user whose
  identifier is set in URL data.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    key_id = data.kwargs.get('user')
    if not key_id:
      raise exception.BadRequest('The request does not contain user data.')

    ensureLoggedIn(data)

    if not data.ndb_user or data.ndb_user.key.id() != key_id:
      raise exception.Forbidden(message=_MESSAGE_NOT_USER_IN_URL)

IS_URL_USER_ACCESS_CHECKER = IsUrlUserAccessChecker()


class IsUserOrgAdminForUrlOrg(AccessChecker):
  """AccessChecker that ensures that the logged in user is organization
  administrator for the organization whose identifier is set in URL data.
  """

  # TODO(daniel): remove this when all organizations moved to NDB
  def __init__(self, is_ndb=False):
    """Initializes a new instance of this access checker.

    Args:
      is_ndb: a bool used to specify if the access checker will be used
        for old db organizations or newer ndb organizations.
    """
    self._is_ndb = is_ndb

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not self._is_ndb:
      if not data.profile:
        raise exception.Forbidden(message=_MESSAGE_NO_PROFILE)
      # good ol' db
      if data.url_org.key() not in data.profile.org_admin_for:
        raise exception.Forbidden(
            message=_MESSAGE_NOT_ORG_ADMIN_FOR_ORG % data.url_org.key().name())
    else:
      if not data.ndb_profile:
        raise exception.Forbidden(message=_MESSAGE_NO_PROFILE)
      if data.url_ndb_org.key not in data.ndb_profile.admin_for:
        raise exception.Forbidden(
            message=_MESSAGE_NOT_ORG_ADMIN_FOR_ORG %
                data.url_ndb_org.key.id())

IS_USER_ORG_ADMIN_FOR_ORG = IsUserOrgAdminForUrlOrg()
IS_USER_ORG_ADMIN_FOR_NDB_ORG = IsUserOrgAdminForUrlOrg(is_ndb=True)


class HasProfileAccessChecker(AccessChecker):
  """AccessChecker that ensures that the logged in user has an active profile
  for the program specified in the URL.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if (not data.ndb_profile
        or data.ndb_profile.status != profile_model.Status.ACTIVE):
      raise exception.Forbidden(message=_MESSAGE_NO_PROFILE)

HAS_PROFILE_ACCESS_CHECKER = HasProfileAccessChecker()


class HasNoProfileAccessChecker(AccessChecker):
  """AccessChecker that ensures that the logged in user does not have a profile
  for the program specified in the URL.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    ensureLoggedIn(data)
    if data.ndb_profile:
      raise exception.Forbidden(message=_MESSAGE_HAS_PROFILE)

HAS_NO_PROFILE_ACCESS_CHECKER = HasNoProfileAccessChecker()


class OrgSignupStartedAccessChecker(AccessChecker):
  """AccessChecker that ensures that organization sign-up period has started
  for the program specified in the URL.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not data.timeline.afterOrgSignupStart():
      active_from = data.timeline.orgSignupStart()
      raise exception.Forbidden(message=_MESSAGE_INACTIVE_BEFORE % active_from)

ORG_SIGNUP_STARTED_ACCESS_CHECKER = OrgSignupStartedAccessChecker()


class OrgsAnnouncedAccessChecker(AccessChecker):
  """AccessChecker that ensures that organizations have been announced for
  the program specified in the URL.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not data.timeline.orgsAnnounced():
      active_from = data.timeline.orgsAnnouncedOn()
      raise exception.Forbidden(message=_MESSAGE_INACTIVE_BEFORE % active_from)


class StudentSignupActiveAccessChecker(AccessChecker):
  """AccessChecker that ensures that student sign-up period has started
  for the program specified in the URL.
  """

  def checkAccess(self, data, check):
    """See AccessChecker.checkAccess for specification."""
    if not data.timeline.studentSignup():
      raise exception.Forbidden(message=_MESSAGE_INACTIVE_OUTSIDE % (
          data.timeline.studentsSignupBetween()))

STUDENT_SIGNUP_ACTIVE_ACCESS_CHECKER = StudentSignupActiveAccessChecker()
