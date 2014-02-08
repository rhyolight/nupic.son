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

from django.test import client

from soc.modules.gci.views import base_templates
from soc.modules.gci.views.helper import request_data

from tests import profile_utils


class LoggedInAsTest(unittest.TestCase):
  """Unit tests for LoggedInAs template."""

  def testForLoggedInUser(self):
    """Tests context for a logged in user."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    request = client.RequestFactory().get('http://some-unused.url.com/')

    data = request_data.RequestData(request, None, None)
    context = base_templates.LoggedInAs(data).context()

    # check that LOGOUT_LINK_LABEL is used as link label
    self.assertEqual(context['link_label'], base_templates.LOGOUT_LINK_LABEL)

    # check that logged_in_as is set to user email
    self.assertEqual(context['logged_in_as'], 'test@example.com')

  def testForNotLoggedInUser(self):
    """Tests context for a not logged in user."""
    profile_utils.logout()

    request = client.RequestFactory().get('http://some-unused.url.com/')

    data = request_data.RequestData(request, None, None)
    context = base_templates.LoggedInAs(data).context()

    # check that LOGIN_LINK_LABEL is used as link label
    self.assertEqual(context['link_label'], base_templates.LOGIN_LINK_LABEL)

    # check that logged_in_as is set to the default text for not logged users
    self.assertEqual(context['logged_in_as'], base_templates.NOT_LOGGED_IN)
