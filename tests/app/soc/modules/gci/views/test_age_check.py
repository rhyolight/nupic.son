# Copyright 2011 the Melange authors.
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


"""Tests for age check related views.
"""


from datetime import date
from datetime import timedelta

from tests import profile_utils
from tests.test_utils import GCIDjangoTestCase


STUDENT_MIN_AGE = 13

class AgeCheckTest(GCIDjangoTestCase):
  """Tests age check page.
  """

  def setUp(self):
    self.init()
    self.timeline_helper.studentSignup()

    # set minimal age for the program
    self.program.student_min_age = STUDENT_MIN_AGE
    self.program.student_min_age_as_of = date.today()
    self.program.put()

  def assertAgeCheckTemplatesUsed(self, response):
    """Asserts that all the templates were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/age_check/base.html')

  def testAgeCheckLogsOut(self):
    url = '/gci/age_check/' + self.gci.key().name()
    response = self.get(url)
    self.assertResponseRedirect(response)

  def testAgeCheckRejectsTooYoung(self):
    profile_utils.logout()
    url = '/gci/age_check/' + self.gci.key().name()
    birth_date = str(date.today() - timedelta(365*(STUDENT_MIN_AGE - 1)))
    postdata = {'birth_date': birth_date}
    response = self.post(url, postdata)
    self.assertResponseRedirect(response)
    self.assertEqual('0', response.cookies['age_check'].value)

  def testAgeCheckPassedRedirects(self):
    profile_utils.logout()
    url = '/gci/age_check/' + self.gci.key().name()
    response = self.get(url)
    self.assertAgeCheckTemplatesUsed(response)

    birth_date = str(date.today() - timedelta(365 * (STUDENT_MIN_AGE + 1)))
    postdata = {'birth_date': birth_date}
    response = self.post(url, postdata)
    self.assertResponseRedirect(response)
    self.assertEqual(birth_date, response.cookies['age_check'].value)

    redirect_url = '/gci/profile/student/' + self.gci.key().name()
    self.client.cookies['age_check'] = '1'
    response = self.get(url)
    self.assertResponseRedirect(response, redirect_url)
