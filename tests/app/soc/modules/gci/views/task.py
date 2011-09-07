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


from tests.test_utils import DjangoTestCase


class TaskViewTest(DjangoTestCase):
  """Tests GCITask public view.
  """

  def setUp(self):
    self.init()

  def testBasicTaskView(self):
    """Tests the rendering of the task view.
    """
    # TODO(ljvderijk): Write this task after discussion on test framework
    # Create a task, status published
    # Set timeline to taskPubliclyVisible
    # Use a non-logged-in request to the page for that task
    # Expect a proper response (200)
    pass
