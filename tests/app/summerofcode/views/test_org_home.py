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

"""Unit tests for organization homepage views."""

from summerofcode.views import org_home as org_home_view

from tests import org_utils
from tests import test_utils


TEST_ORG_ID = 'test_org'
TEST_BLOG = 'http://www.test.blog.com/'
TEST_MAILING_LIST = 'mailinglist@example.com'
TEST_TWITTER = u'http://www.test.twitter.com/'

def _getOrgHomeUrl(org):
  """Returns URL to Organization Homepage.

  Args:
    org: Organization entity.

  Returns:
    A string containing the URL to Edit Organization Preferences page.
  """
  return '/gsoc/org2/home/%s' % org.key.id()


class OrgHomePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for OrgHomePage class."""

  def setUp(self):
    """See unittest.UnitTest.setUp for specification."""
    self.init()
    contact = {
        'blog': TEST_BLOG,
        'mailing_list': TEST_MAILING_LIST,
        'twitter': TEST_TWITTER,
        }
    self.org = org_utils.seedSOCOrganization(
        TEST_ORG_ID, self.program.key(), contact=contact)

  def testPageLoads(self):
    """Tests that page loads properly."""
    response = self.get(_getOrgHomeUrl(self.org))
    self.assertResponseOK(response)

  def testContactContext(self):
    """Tests that contact information is present in context."""
    response = self.get(_getOrgHomeUrl(self.org))

    # check that contact is present in the context
    self.assertIn('contact', response.context)

    # check that specified contact information are present in the context
    context = response.context['contact'].context()
    self.assertEqual(context['blogger_link'], TEST_BLOG)
    self.assertEqual(context['pub_mailing_list_link'], TEST_MAILING_LIST)
    self.assertEqual(context['twitter_link'], TEST_TWITTER)

    # check that not specified contact information are not set
    self.assertIsNone(context['facebook_link'])
    self.assertIsNone(context['google_plus_link'])
