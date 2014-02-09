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

"""Unit tests for notification settings related views."""

from tests import profile_utils
from tests import test_utils


def _getNotificationSettingsUrl(program_key):
  """Returns URL to Notification Settings page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Notification Settings page.
  """
  return '/gsoc/profile/notifications/%s' % program_key.name()


TEST_POSTDATA = {
    'org_connections': True,
    'user_connections': True,
}

class NotificationSettingsPageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for NotificationSettingsPage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that the page loads properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.get(_getNotificationSettingsUrl(self.program.key()))
    self.assertResponseOK(response)

  def testNotificationSettingsSet(self):
    """Tests that notification settings are set properly."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile = profile_utils.seedNDBProfile(self.program.key(), user=user)

    response = self.post(
        _getNotificationSettingsUrl(self.program.key()), postdata=TEST_POSTDATA)
    self.assertResponseRedirect(response)

    # check that notification settings are set
    profile = profile.key.get()
    self.assertEqual(
        profile.notification_settings.org_connections,
        TEST_POSTDATA['org_connections'])
    self.assertEqual(
        profile.notification_settings.user_connections,
        TEST_POSTDATA['user_connections'])
