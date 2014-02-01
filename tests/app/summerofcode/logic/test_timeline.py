# Copyright 2014 the Melange authors.
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

import json
import unittest

from soc.modules.gsoc.views.helper import request_data

from summerofcode.logic import timeline as timeline_logic

from tests import program_utils
from tests import timeline_utils


class CreateTimelineDictTest(unittest.TestCase):
  """Unit tests for createTimelineDict function."""

  def setUp(self):
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedGSoCProgram(sponsor_key=sponsor.key())
    org_app = program_utils.seedApplicationSurvey(program.key())
    timeline_test_helper = timeline_utils.GSoCTimelineHelper(
        program.timeline, org_app)
    timeline_test_helper.orgSignup()
    self.timeline_helper = request_data.TimelineHelper(
        program.timeline, org_app)

  def testCreateTimelineDict(self):
    """Just a smoke test for now."""
    timeline_dict = timeline_logic.createTimelineDict(self.timeline_helper)
    self.assertIn('slices', timeline_dict)

    # Ensure that the dictionary serializes to something non-empty.
    self.assertTrue(json.dumps(timeline_dict))
