# Copyright 2014 the Melange authors.
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

"""Unit tests for connection related views."""

import unittest

from soc.modules.gsoc.views.helper import request_data

from melange.request import exception
from melange.views import connection as connection_view

from summerofcode.views.helper import urls

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests.utils import connection_utils


def _getManageAsUserUrl(connection):
  """Returns URL to 'Manage Connection As User' page for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Manage Connection As User' for the specified connection.
  """
  return '/gsoc/connection/manage/user/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


def _getManageAsOrgUrl(connection):
  """Returns URL to 'Manage Connection As Org' page for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Manage Connection As Org' for the specified connection.
  """
  return '/gsoc/connection/manage/org/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


def _getListConnectionsForOrgAdminUrl(profile):
  """Returns URL to 'List Connections For Org Admin' page for the specified
  profile entity.

  Args:
    profile: profile entity.

  Returns:
    The URL to 'List Connection For Org Admin' for the specified profile.
  """
  return '/gsoc/connection/list/org/%s' % profile.key.id()


def _getMarkAsSeenByOrgUrl(connection):
  """Returns URL to 'Mark Connection As Seen By Org' handler for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Mark Connection As Seen By Org' for the specified connection.
  """
  return '/gci/connection/mark_as_seen/org/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


def _getMarkAsSeenByUserUrl(connection):
  """Returns URL to 'Mark Connection As Seen By User' handler for the specified
  connection entity.

  Args:
    connection: connection entity.

  Returns:
    The URL to 'Mark Connection As Seen By User' for the specified connection.
  """
  return '/gci/connection/mark_as_seen/user/%s/%s' % (
      connection.key.parent().id(), connection.key.id())


class NoConnectionExistsAccessCheckerTest(unittest.TestCase):
  """Unit tests for NoConnectionExistsAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedGSoCProgram(sponsor_key=sponsor.key())
    self.organization = org_utils.seedSOCOrganization(program.key())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    self.profile = profile_utils.seedNDBProfile(program.key(), user=user)

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': program.program_id,
        'organization': self.organization.org_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testNoConnectionExists(self):
    """Tests that access is granted if no connection exists."""
    access_checker = (
        connection_view.NoConnectionExistsAccessChecker(urls.UrlNames))
    access_checker.checkAccess(self.data, None)

  def testConnectionExists(self):
    """Tests that access is denied if connection already exists."""
    # seed a connection between the profile and organization
    connection_utils.seed_new_connection(
        self.profile.key, self.organization.key)

    access_checker = (
        connection_view.NoConnectionExistsAccessChecker(urls.UrlNames))
    with self.assertRaises(exception.Redirect):
      access_checker.checkAccess(self.data, None)
