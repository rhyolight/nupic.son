# Copyright 2010 the Melange authors.
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

"""Tests XSS in errors on the mentor sign-up page."""

from django.utils import html

from tests import test_utils


class ProfileXSSTest(object):
  """Tests sanitization of user-given strings at mentor sign-up.

  This mixin class is abstract and must be co-inherited with (exactly
  one of) GCIDjangoTestCase or GSoCDjangoTestCase.
  """

  def setUp(self):
    self.init()
    self.timeline_helper.studentSignup()

  def testSanitization(self):
    xss_payload = '><img src=http://www.google.com/images/srpr/logo4w.png>'

    role_url = '/%(program_type)s/profile/%(role)s/%(suffix)s' % {
        'program_type': self.programType(),
        'role': 'mentor',
        'suffix': self.program.key().name(),
        }

    postdata = {
        'link_id': xss_payload,
        'user': self.profile_helper.user,
        'parent': self.profile_helper.user,
        'scope': self.program,
        'status': 'active',
        'email': xss_payload,
        'mentor_for': [],
        'org_admin_for': [],
        'is_org_admin': False,
        'is_mentor': False,
        'birth_date': xss_payload,
    }

    response = self.post(role_url, postdata)
    self.assertNotIn(xss_payload, response.content)
    self.assertIn(html.escape(xss_payload), response.content)


class GSoCProfileXSSTest(ProfileXSSTest, test_utils.GSoCDjangoTestCase):
  pass


class GCIProfileXSSTest(ProfileXSSTest, test_utils.GCIDjangoTestCase):
  pass
