# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing utility functions related to time and time formatting."""

from datetime import datetime


def relativeTime(date):
  """Converts a past datetime in to a relative string describing how long ago.
  Examples: "just now"
            "13 minutes ago"
            "6 days ago"

  If the given date is either in the future, or is one week or more in the past,
  the returned string is the date's ctime(), not a relative string.

  Returns:
    A string of the time relative to datetime.utcnow().
  """
  diff = datetime.utcnow() - date

  if diff.days > 7 or diff.days < 0:
    return date.ctime()
  elif diff.days == 1:
    return '1 day ago'
  elif diff.days > 1:
    return '%d days ago' % diff.days
  elif diff.seconds <= 1:
    return 'just now'
  elif diff.seconds < 60:
    return '%d seconds ago' % diff.seconds
  elif diff.seconds < (60 * 2):
    return '1 minute ago'
  elif diff.seconds < (60 * 60):
    return '%d minutes ago' % (diff.seconds / 60)
  elif diff.seconds < (60 * 60 * 2):
    return '1 hour ago'
  else:
    return '%d hours ago' % (diff.seconds / (60 * 60))
