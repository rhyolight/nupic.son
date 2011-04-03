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

"""Tests for invite view.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import httplib

from google.appengine.ext import db

from soc.models.request import Request

from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import DjangoTestCase
from tests.timeline_utils import TimelineHelper

# TODO: perhaps we should move this out?
from soc.modules.seeder.logic.seeder import logic as seeder_logic


class RequestTest(DjangoTestCase):
  """Tests request page.
  """

  def setUp(self):
    self.init()

  def createRequest(self):
    """Creates and returns an accepted invitation for the current user.
    """
    # create other user to send invite to
    other_data = GSoCProfileHelper(self.gsoc, self.dev_test)
    other_data.createOtherUser('to_be_mentor@example.com')
    other_data.createProfile()
    other_user = other_data.user

    properties = {'role': 'mentor', 'user': other_user, 'group': self.org,
                  'status': 'pending', 'type': 'Request'}
    request = seeder_logic.seed(Request, properties=properties)
    return (other_data.profile, request)

  def assertRequestTemplatesUsed(self, response):
    """Asserts that all the request templates were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gsoc/invite/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/_form.html')

  def testRequestMentor(self):
    # test GET
    self.data.createProfile()
    url = '/gsoc/request/' + self.org.key().name()
    response = self.client.get(url)
    self.assertRequestTemplatesUsed(response)

    # test POST
    override = {'status': 'pending', 'role': 'mentor', 'type': 'Request',
                'user': self.data.user, 'group': self.org}
    response, properties = self.modelPost(url, Request, override)

    request = Request.all().get()
    self.assertPropertiesEqual(properties, request)

  def testAcceptRequest(self):
    self.data.createOrgAdmin(self.org)
    other_profile, request = self.createRequest()
    url = '/gsoc/request/%s/%s' % (self.gsoc.key().name(), request.key().id())
    response = self.client.get(url)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/soc/request/base.html')

    postdata = {'action': 'Reject'}
    response = self.post(url, postdata)
    self.assertResponseRedirect(response)
    invitation = Request.all().get()
    self.assertEqual('rejected', invitation.status)

    # test that you can change after the fact
    postdata = {'action': 'Accept'}
    response = self.post(url, postdata)
    self.assertResponseRedirect(response)

    profile = db.get(other_profile.key())
    self.assertEqual(1, profile.mentor_for.count(self.org.key()))
    self.assertTrue(profile.is_mentor)
    self.assertFalse(profile.is_student)
    self.assertFalse(profile.is_org_admin)
    self.assertFalse(profile.org_admin_for)
