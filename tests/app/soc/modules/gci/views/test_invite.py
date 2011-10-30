#!/usr/bin/env python2.5
#
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


"""Tests for invite related views.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from tests.test_utils import GCIDjangoTestCase


class InviteViewTest(GCIDjangoTestCase):
  """Tests user invite views.
  """

  def setUp(self):
    super(InviteViewTest, self).setUp()
    self.init()

  def testLoggedInCannotInvite(self):
    url = self._inviteMentorUrl()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = self._inviteOrgAdminUrl()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testUserCannotInvite(self):
    self.data.createUser()

    url = self._inviteMentorUrl()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = self._inviteOrgAdminUrl()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def testMentorCannotInvite(self):
    self.data.createMentor(self.org)

    url = self._inviteMentorUrl()
    response = self.get(url)
    self.assertResponseForbidden(response)

    url = self._inviteOrgAdminUrl()
    response = self.get(url)
    self.assertResponseForbidden(response)

  def _inviteOrgAdminUrl(self):
    return '/gci/invite/org_admin/%s' % self.org.key().name()

  def _inviteMentorUrl(self):
    return '/gci/invite/mentor/%s' % self.org.key().name()
