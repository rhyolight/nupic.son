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

"""Unit tests for timeline logic."""

import unittest

from soc.logic import timeline as timeline_logic

from soc.models import program as program_model
from soc.models import timeline as timeline_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic


class IsTimelineForProgramTest(unittest.TestCase):
  """Unit tests for isTimelineForProgram function."""

  def testTimelineForProgram(self):
    # seed a new program and a timeline for it
    properties = {'key_name': 'test_keyname'}
    timeline = seeder_logic.seed(timeline_model.Timeline, properties)
    program = seeder_logic.seed(program_model.Program, properties)

    result = timeline_logic.isTimelineForProgram(timeline.key(), program.key())
    self.assertTrue(result)

  def testTimelineNotForProgram(self):
    # seed a new program and a timeline for it
    properties = {'key_name': 'test_keyname_one'}
    timeline_one = seeder_logic.seed(timeline_model.Timeline, properties)
    program_one = seeder_logic.seed(program_model.Program, properties)

    # seed another program and a timeline for it
    properties = {'key_name': 'test_keyname_two'}
    timeline_two = seeder_logic.seed(timeline_model.Timeline, properties)
    program_two = seeder_logic.seed(program_model.Program, properties)

    result = timeline_logic.isTimelineForProgram(
        timeline_one.key(), program_two.key())
    self.assertFalse(result)

    result = timeline_logic.isTimelineForProgram(
        timeline_two.key(), program_one.key())
    self.assertFalse(result)
