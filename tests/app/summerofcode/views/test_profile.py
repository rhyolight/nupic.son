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

from google.appengine.api import users as users_api

from melange.models import user as user_model

from summerofcode.views import profile as profile_view

from tests import test_utils


TEST_BIRTH_DATE = '1993-01-01'
TEST_BLOG = 'http://www.test.blog.com/'
TEST_EMAIL = 'test@example.com'
TEST_FIRST_NAME = 'Test First'
TEST_GENDER = profile_view._GENDER_FEMALE_ID
TEST_LAST_NAME = 'Test Last'
TEST_PHONE = '1234567890'
TEST_PHOTO_URL = u'http://www.test.photo.url.com/'
TEST_PROGRAM_KNOWLEDGE = u'Test program knowledge'
TEST_PUBLIC_NAME = 'Test Public Name'
TEST_RESIDENTIAL_STREET = 'Test Street'
TEST_RESIDENTIAL_CITY = 'Test City'
TEST_RESIDENTIAL_PROVINCE = 'CA'
TEST_RESIDENTIAL_POSTAL_CODE = '90000'
TEST_RESIDENTIAL_COUNTRY = 'United States'
TEST_TEE_SIZE = profile_view._TEE_SIZE_M_ID
TEST_TEE_STYLE = profile_view._TEE_STYLE_FEMALE_ID
TEST_USER_ID = 'test_user_id'
TEST_WEB_PAGE = u'http://www.web.page.com/'


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

  def testOrgMemberProfileCreated(self):
    """Tests that profile entity is created correctly."""
    postdata = {
        'user_id': TEST_USER_ID,
        'public_name': TEST_PUBLIC_NAME,
        'web_page': TEST_WEB_PAGE,
        'blog': TEST_BLOG,
        'photo_url': TEST_PHOTO_URL,
        'first_name': TEST_FIRST_NAME,
        'last_name': TEST_LAST_NAME,
        'email': TEST_EMAIL,
        'phone': TEST_PHONE,
        'residential_street': TEST_RESIDENTIAL_STREET,
        'residential_city': TEST_RESIDENTIAL_CITY,
        'residential_province': TEST_RESIDENTIAL_PROVINCE,
        'residential_country': TEST_RESIDENTIAL_COUNTRY,
        'residential_postal_code': TEST_RESIDENTIAL_POSTAL_CODE,
        'birth_date': TEST_BIRTH_DATE,
        'tee_style': TEST_TEE_STYLE,
        'tee_size': TEST_TEE_SIZE,
        'gender': TEST_GENDER,
        'program_knowledge': TEST_PROGRAM_KNOWLEDGE,
        }
    response = self.post(
        _getProfileRegisterAsOrgMemberUrl(self.program.key()),
        postdata=postdata)

    # check that user entity has been created
    user = (user_model.User.query(
        user_model.User.account_id == users_api.get_current_user().user_id())
        .get())
    self.assertIsNotNone(user)
    self.assertEqual(user.key.id(), TEST_USER_ID)

    # TODO(daniel): complete this test
