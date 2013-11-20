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

"""Tests for base templates."""

import unittest

from django import http

from google.appengine.api import users

from soc.modules.gci.views import base_templates

from tests import profile_utils


# TODO(nathaniel): Eliminate this class or at least unify it with the two
# other MockRequestData classes floating around tests/.
class MockRequestData(object):
  """Class used to simulate request_data.RequestData gae_user and request
  properties."""

  def __init__(self, user_email=None):
    """Initializes instance of this class.

    Args:
      user_email: the user email as a string.
    """
    if user_email is not None:
      user = profile_utils.seedUser(email=user_email)
      profile_utils.login(user)
      self.gae_user = users.User()
      self.user = user
    else:
      self.gae_user = None
      self.user = None
    self.request = http.HttpRequest()


class LoggedInAsTest(unittest.TestCase):
  """Unit tests for LoggedInAs template."""

  def testForLoggedInUser(self):
    """Tests context for a logged in user."""
    request_data = MockRequestData(user_email='test@example.com')
    context = base_templates.LoggedInAs(request_data).context()

    # check that LOGOUT_LINK_LABEL is used as link label
    self.assertEqual(context['link_label'], base_templates.LOGOUT_LINK_LABEL)

    # check that logged_in_as is set to user email
    self.assertEqual(context['logged_in_as'], 'test@example.com')

  def testForNotLoggedInUser(self):
    """Tests context for a not logged in user."""
    request_data = MockRequestData()
    context = base_templates.LoggedInAs(request_data).context()

    # check that LOGIN_LINK_LABEL is used as link label
    self.assertEqual(context['link_label'], base_templates.LOGIN_LINK_LABEL)

    # check that logged_in_as is set to the default text for not logged users
    self.assertEqual(context['logged_in_as'], base_templates.NOT_LOGGED_IN)
