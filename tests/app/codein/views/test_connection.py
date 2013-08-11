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

"""Unit tests for connection related views."""

from tests import test_utils


class StartConnectionAsUserTest(test_utils.GCIDjangoTestCase):
  """Unit tests for ShowConnectionAsUser class."""

  def setUp(self):
    """See testcase.setUp for specification."""
    self.init()

  def _getUrl(self, profile, org):
    """Returns URL to 'start connection as user' view for the specified
    profile and organization.

    Args:
      profile: profile entity.
      org: organization entity.

    Returns:
      URL to 'start connection as user' view.
    """
    return '/gci/connection/start/user/%s/%s' % (
        profile.key().name(), org.link_id)

  def testStudentAccessDenied(self):
    """Tests that students cannot access the site."""
    profile = self.profile_helper.createStudent()
    url = self._getUrl(profile, self.org)
    response = self.get(url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testNonStudentAccessGranted(self):
    """Tests that a user with non-student profile can access the site."""
    profile = self.profile_helper.createProfile()
    url = self._getUrl(profile, self.org)
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertTemplateUsed(
        response, 'modules/gci/form_base.html')
