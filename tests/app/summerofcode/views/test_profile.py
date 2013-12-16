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

"""Unit tests for user profile related views."""


from tests import test_utils


def _getProfileRegisterAsOrgMemberUrl(program_key):
  """Returns URL to Register As Organization Member page.

  Args:
    program_key: Program key.

  Returns:
    A string containing the URL to Register As Organization Member page.
  """
  return '/gsoc/profile/register/org_member/%s' % program_key.name()


class ProfileOrgMemberCreatePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ProfileOrgMemberCreatePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getProfileRegisterAsOrgMemberUrl(self.program.key()))
    self.assertResponseOK(response)
