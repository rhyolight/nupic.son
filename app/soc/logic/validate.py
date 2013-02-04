# Copyright 2008 the Melange authors.
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

"""Common validation helper functions."""

import feedparser

from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors

from soc.models import linkable
from soc.models import user


def isFeedURLValid(feed_url=None):
  """Returns True if provided url is valid ATOM or RSS.

  Args:
    feed_url: ATOM or RSS feed url
  """

  # a missing or empty feed url is never valid
  if not feed_url:
    return False

  try:
    result = urlfetch.fetch(feed_url)
  except urlfetch_errors.Error:
    return False

  # 200 is the status code for 'all ok'
  if result.status_code != 200:
    return False

  try:
    parsed_feed = feedparser.parse(result.content)
  except:
    return False

  # version is always present if the feed is valid
  return bool(parsed_feed.version)


def isLinkIdFormatValid(link_id):
  """Returns True if link_id is in a valid format.

  Args:
    link_id: link ID used in URLs for identification
  """
  return bool(linkable.LINK_ID_REGEX.match(link_id))


def isScopePathFormatValid(scope_path):
  """Returns True if scope_path is in a valid format.

  Args:
    scope_path: scope path prepended to link ID
      used for identification.
  """
  return bool(linkable.SCOPE_PATH_REGEX.match(scope_path))


# TODO(nathaniel): In the offseason, change this so that the program host-
# supplied age values both represent allowed ages, rather than student_max_age
# representing "youngest disallowed age".
def isAgeSufficientForProgram(birth_date, program):
  """Returns True if a student with birth_date can participate in program.

  Args:
    birth_date: A datetime.date representing a student birth date.
    program: The program.

  Returns:
    True if the student meets all age requirements for the program, False
      if the student is either too old or too young. If the program does not
      set age requirements, the student is allowed to participate.
  """
  # do not check if the data is not present
  if not program.student_min_age_as_of:
    return True

  if program.student_min_age:
    latest_allowed_birth_year = (
        program.student_min_age_as_of.year - program.student_min_age)
    latest_allowed_birth_date = program.student_min_age_as_of.replace(
        year=latest_allowed_birth_year)
    if latest_allowed_birth_date < birth_date:
      return False

  if program.student_max_age:
    earliest_allowed_birth_year = (
        program.student_min_age_as_of.year - program.student_max_age)
    earliest_allowed_birth_date = program.student_min_age_as_of.replace(
        year=earliest_allowed_birth_year)
    # Yes - if it's your birthday on the program student-welcome date,
    # you're out of luck.
    if birth_date <= earliest_allowed_birth_date:
      return False

  return True


def hasNonStudentProfileForProgram(user, program, profile_model):
  """Returns True if the user has a non student profile for the given program.

  Args:
    user: User entity for the user whose must have a profile in the program.
    program: Program entity which must be checked for profile.

  Returns:
    True if the given user has a non student profile for the given program,
    False otherwise.
  """
  q = profile_model.all(keys_only=True)
  q.ancestor(user)
  q.filter('scope', program)
  q.filter('is_student', False)
  q.filter('status', 'active')

  # There should be exactly one profile entity for the given link id per
  # program, no more, no less
  return q.count() == 1
