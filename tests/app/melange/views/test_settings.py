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

"""Unit tests for settings view."""

from tests import profile_utils
from tests import test_utils


def _getUserSettingsUrl(user):
  """Returns the URL to user settings page for the specified user.

  Args:
    user: User entity.

  Returns:
    a string containg URL to user settings page.
  """
  return '/site/settings/user/%s' % user.key.id()


class UserSettingsTest(test_utils.DjangoTestCase):
  """Unit tests for UserSettings class."""

  def _assertPageTemplatesUsed(self, response):
    """Asserts that all templates for the tested page are used."""
    self.assertTemplateUsed(
        response, 'melange/settings/user_settings.html')

  def testNonDeveloperAccessDenied(self):
    """Tests that access is denied for users who are not developers."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    response = self.get(_getUserSettingsUrl(user))
    self.assertResponseForbidden(response)

  def testPageLoads(self):
    """Tests that page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user, is_admin=True)

    response = self.get(_getUserSettingsUrl(user))
    self.assertResponseOK(response)
    self._assertPageTemplatesUsed(response)
