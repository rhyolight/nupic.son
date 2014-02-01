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

"""Tests for soc.logic.helper.timeformat."""

import unittest

from datetime import datetime
from datetime import timedelta

from soc.logic.helper import timeformat


class TimeFormatTest(unittest.TestCase):
  """Tests for time format helper functions."""

  def testRelativeTime(self):
    """Tests that relativeTime() correctly returns a relative time string for
    various datetimes.
    """
    now = datetime.utcnow()

    expected = 'just now'
    actual = timeformat.relativeTime(now - timedelta(seconds=0.5))
    self.assertEqual(expected, actual)

    expected = '5 seconds ago'
    actual = timeformat.relativeTime(now - timedelta(seconds=5.4))
    self.assertEqual(expected, actual)

    expected = '1 minute ago'
    actual = timeformat.relativeTime(now - timedelta(minutes=1, seconds=20))
    self.assertEqual(expected, actual)

    expected = '13 minutes ago'
    actual = timeformat.relativeTime(now - timedelta(minutes=13, seconds=20))
    self.assertEqual(expected, actual)

    expected = '1 hour ago'
    actual = timeformat.relativeTime(now - timedelta(hours=1, minutes=20))
    self.assertEqual(expected, actual)

    expected = '19 hours ago'
    actual = timeformat.relativeTime(now - timedelta(hours=19, minutes=20))
    self.assertEqual(expected, actual)

    expected = '1 day ago'
    actual = timeformat.relativeTime(now - timedelta(days=1, hours=8))
    self.assertEqual(expected, actual)

    expected = '6 days ago'
    actual = timeformat.relativeTime(now - timedelta(days=6, hours=8))
    self.assertEqual(expected, actual)

    date = now - timedelta(days=8)
    expected = date.ctime()
    actual = timeformat.relativeTime(date)
    self.assertEqual(expected, actual)
