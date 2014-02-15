# Copyright 2012 the Melange authors.
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

"""Module with tests for task bulk create view."""

from google.appengine.ext import ndb

from tests import profile_utils
from tests.profile_utils import GCIProfileHelper
from tests.test_utils import GCIDjangoTestCase


class BulkTaskCreateViewTest(GCIDjangoTestCase):
  """Tests for task bulk create view.
  """

  def setUp(self):
    """Creates a published task for self.org.
    """
    super(BulkTaskCreateViewTest, self).setUp()
    self.init()

  def assertFullEditTemplatesUsed(self, response):
    """Asserts that all the task creation base templates along with full edit
    template is used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'modules/gci/bulk_create/base.html')

  def testBulkTaskCreatekBeforeOrgsAnnouncedForNoRole(self):
    """Tests the bulk task create view before the program is public
    for users with no role.
    """
    self.timeline_helper.orgSignup()

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createProfile()

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation has not started yet and no role to bulk create tasks
    self.assertResponseForbidden(response)

  def testBulkTaskCreateBeforeOrgsAnnouncedForOrgAdmin(self):
    """Tests the bulk task create view before the program is
    public for org admins.
    """
    self.timeline_helper.orgSignup()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation has not started yet
    self.assertResponseForbidden(response)

  def testBulkTaskCreateBeforeOrgsAnnouncedForMentor(self):
    """Tests the bulk task create view before the program is
    public for mentors.
    """
    self.timeline_helper.orgSignup()

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createMentor(self.org)

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation has not started yet
    self.assertResponseForbidden(response)

  def testBulkTaskCreateBeforeOrgsAnnouncedForStudent(self):
    """Tests the bulk task create view before the program is
    public for students.
    """
    self.timeline_helper.orgSignup()

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createStudent()

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation has not started yet
    self.assertResponseForbidden(response)

  def testBulkTaskCreateAfterClaimEndForNoRole(self):
    """Tests the bulk task create view after the task claim deadline
    for users with no role.
    """
    self.timeline_helper.taskClaimEnded()

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createProfile()

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation has not started yet and no role to create tasks
    self.assertResponseForbidden(response)

  def testBulkTaskCreateAfterClaimEndForOrgAdmin(self):
    """Tests the bulk task create view after the task claim deadline
    for org admins.
    """
    self.timeline_helper.taskClaimEnded()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation is not open
    self.assertResponseForbidden(response)

  def testBulkTaskCreateAfterClaimEndForMentor(self):
    """Tests the bulk task create view after the task claim deadline
    for mentors.
    """
    self.timeline_helper.taskClaimEnded()

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createMentor(self.org)

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation is not open
    self.assertResponseForbidden(response)

  def testBulkTaskCreateAfterClaimEndForStudent(self):
    """Tests the bulk task create view after the task claim deadline
    for students.
    """
    self.timeline_helper.taskClaimEnded()

    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createStudent()

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Task creation is not open
    self.assertResponseForbidden(response)

  def testBulkTaskCreateDuringProgramForNoRole(self):
    """Tests the bulk task create view during the program
    for users with no role.
    """
    self.timeline_helper.tasksPubliclyVisible()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Users with not role can't create tasks
    self.assertResponseForbidden(response)

  def testBulkTaskCreateDuringProgramForOrgAdmin(self):
    """Tests the bulk task create view during the program
    for org admins.
    """
    self.timeline_helper.tasksPubliclyVisible()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    self.assertResponseOK(response)
    self.assertFullEditTemplatesUsed(response)

  def testBulkTaskCreateDuringProgramForMentor(self):
    """Tests the bulk task create view during the program for mentors."""
    self.timeline_helper.tasksPubliclyVisible()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        mentor_for=[ndb.Key.from_old_key(self.org.key())])

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Mentors can't bulk create tasks
    self.assertResponseForbidden(response)

  def testBulkTaskCreateDuringProgramForStudent(self):
    """Tests the bulk task create view during the program
    for students.
    """
    self.timeline_helper.tasksPubliclyVisible()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBStudent(self.program, user=user)

    url = '/gci/bulk/' + self.org.key().name()
    response = self.get(url)

    # Student can't bulk create tasks
    self.assertResponseForbidden(response)
