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


"""Tests for GCITask public view.
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from tests.profile_utils import GCIProfileHelper
from tests.test_utils import GCIDjangoTestCase


class TaskViewTest(GCIDjangoTestCase):
  """Tests GCITask public view.
  """

  def setUp(self):
    self.init()

  def testBasicTaskView(self):
    """Tests the rendering of the task view.
    """
    # Create a task, status published
    profile = GCIProfileHelper(self.gci, self.dev_test)
    task = profile.createOtherUser('mentor@example.com').\
        createMentorWithTask(self.org)

    # Set timeline to taskPubliclyVisible
    # TODO(ljvderijk): Use timeline helper from GCI.
    #self.timeline.taskPubliclyVisible()

    # Use a non-logged-in request to the page for that task
    self.profile.clear()

    url = '/gci/task/view/%s/%s' %(task.program.key().name(), task.key().id())
    response = self.client.get(url)

    # Expect a proper response (200)
    self.assertResponseOK(response)
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'v2/modules/gci/task/public.html')
