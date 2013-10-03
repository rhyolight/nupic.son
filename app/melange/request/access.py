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

from melange.request import exception

from soc.logic import links
from soc.models import program as program_model


_MESSAGE_NOT_PROGRAM_ADMINISTRATOR = translation.ugettext(
    'You need to be a program administrator to access this page.')

_MESSAGE_NOT_DEVELOPER = translation.ugettext(
    'This page is only accessible to developers.')

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

  def checkAccess(self, data, check, mutator):
    """Ensure that the user's request should be satisfied.

    Args:
      data: A request_data.RequestData describing the current request.
      check: An access_checker.AccessChecker object.
      mutator: An access_checker.Mutator object.

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

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    pass

ALL_ALLOWED_ACCESS_CHECKER = AllAllowedAccessChecker()


# TODO(nathaniel): There's some ninja polymorphism to be addressed here -
# RequestData doesn't actually have an "is_host" attribute, but its two
# major subclasses (the GCI-specific and GSoC-specific RequestData classes)
# both do, so this "works" but isn't safe or sanely testable.
class ProgramAdministratorAccessChecker(AccessChecker):
  """AccessChecker that ensures that the user is a program administrator."""

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    if data.is_developer:
      # NOTE(nathaniel): Developers are given all the powers of
      # program administrators.
      return
    elif not data.gae_user:
      raise exception.LoginRequired()
    elif not data.is_host:
      raise exception.Forbidden(message=_MESSAGE_NOT_PROGRAM_ADMINISTRATOR)

PROGRAM_ADMINISTRATOR_ACCESS_CHECKER = ProgramAdministratorAccessChecker()


# TODO(nathaniel): Eliminate this or make it a
# "SiteAdministratorAccessChecker" - there should be no aspects of Melange
# that require developer action or are limited only to developers.
class DeveloperAccessChecker(AccessChecker):
  """AccessChecker that ensures that the user is a developer."""

  def checkAccess(self, data, check, mutator):
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

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    for checker in self._checkers:
      checker.checkAccess(data, check, mutator)


class NonStudentUrlProfileAccessChecker(AccessChecker):
  """AccessChecker that ensures that the URL user has a non-student profile."""

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    if data.url_profile.status != 'active':
      raise exception.Forbidden(
          message=_MESSAGE_NO_URL_PROFILE % data.kwargs['user'])

    if data.url_profile.is_student:
      raise exception.Forbidden(message=_MESSAGE_STUDENTS_DENIED)

NON_STUDENT_URL_PROFILE_ACCESS_CHECKER = NonStudentUrlProfileAccessChecker()


class ProgramActiveAccessChecker(AccessChecker):
  """AccessChecker that ensures that the program is currently active.

  A program is considered active when the current point of time comes after
  its start date and before its end date. Additionally, its status has to
  be set to visible.
  """

  def checkAccess(self, data, check, mutator):
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

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    key_name = data.kwargs.get('user')
    if not key_name:
      raise exception.BadRequest('The request does not contain user data.')

    ensureLoggedIn(data)

    if not data.user or data.user.key().name() != key_name:
      raise exception.Forbidden(message=_MESSAGE_NOT_USER_IN_URL)

IS_URL_USER_ACCESS_CHECKER = IsUrlUserAccessChecker()


class IsUserOrgAdminForUrlOrg(AccessChecker):
  """AccessChecker that ensures that the logged in user is organization
  administrator for the organization whose identifier is uset in URL data.
  """

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    if not data.profile:
      raise exception.Forbidden(message=_MESSAGE_NO_PROFILE)

    if data.url_org.key() not in data.profile.org_admin_for:
      raise exception.Forbidden(
          message=_MESSAGE_NOT_ORG_ADMIN_FOR_ORG % data.url_org.key().name())

IS_USER_ORG_ADMIN_FOR_ORG = IsUserOrgAdminForUrlOrg()


# TODO(daniel): Remove when not needed
class HostOrDeveloperAccessChecker(AccessChecker):
  """AccessChecker that ensures that the user is a program administrator."""

  def checkAccess(self, data, check, mutator):
    """See AccessChecker.checkAccess for specification."""
    if data.is_developer:
      # NOTE(nathaniel): Developers are given all the powers of
      # program administrators.
      return
    elif not data.gae_user:
      raise exception.LoginRequired()
    elif not data.user.host_for:
      raise exception.Forbidden(message=_MESSAGE_NOT_PROGRAM_ADMINISTRATOR)
