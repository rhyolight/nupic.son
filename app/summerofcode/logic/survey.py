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

"""Logic for surveys."""

from google.appengine.ext import ndb

# TODO(daniel): replace with logic functions
from soc.views.helper import request_data
from summerofcode.models import survey as survey_model


PRE_PERIOD_STATE = 'pre_period'
IN_PERIOD_STATE = 'in_period'
POST_PERIOD_STATE = 'post_period'

PERIOD_STATES = [PRE_PERIOD_STATE, IN_PERIOD_STATE, POST_PERIOD_STATE]

# TODO(daniel): move Period to its own utility classes
class Period(object):
  """Class to represent relationship between the current moment and
  the specified period.

  A period is defined by two dates that stand for its beginning and end,
  respectively. If at least one of these dates is absent, the period
  is considered unbounded.
  """

  def __init__(self, start=None, end=None):
    """Initializes new instance of this class with the specified start and
    end dates.

    Args:
      start: start date of the period. May be None if unspecified.
      end: end date of the period. May be None if unspecified.
    """
    self.start = start
    self.end = end

  @property
  def state(self):
    """Returns state of the period with respect to the current moment in time.

    For the period bounded at both start and end,there are
    three possibilities. The current moment may be:
    - before the period
    - in the period
    - after the period

    For a period with no start date defined, the current moment may be:
    - in the period
    - after the period

    For period with no end date defined, the current moment may be:
    - before the period
    - in the period

    Returns:
      A constant representing the current state of the period. Can be one of
      PRE_PERIOD_STATE, IN_PERIOD_STATE or POST_PERIOD_STATE.
    """
    # unbounded period
    if not self.start and not self.end:
      return IN_PERIOD_STATE

    # period right-unbounded
    elif self.start and not self.end:
      if request_data.isBefore(self.start):
        return PRE_PERIOD_STATE
      else:
        return IN_PERIOD_STATE

    # period left-unbounded
    elif not self.start and self.end:
      if request_data.isAfter(self.end):
        return POST_PERIOD_STATE
      else:
        return IN_PERIOD_STATE

    # period bounded
    elif request_data.isBefore(self.start):
      return PRE_PERIOD_STATE
    elif request_data.isAfter(self.end):
      return POST_PERIOD_STATE
    else:
      return IN_PERIOD_STATE


def getPersonalExtension(profile_key, survey_key):
  """Returns personal extension for the specified survey and profile.

  Args:
    profile_key: profile key.
    survey_key: survey key.

  Returns:
    survey_model.PersonalExtension if an entity for the specified parameters
    exists, None otherwise.
  """
  # TODO(daniel): NDB migration
  ndb_survey_key = ndb.Key.from_old_key(survey_key)
  ndb_profile_key = ndb.Key.from_old_key(profile_key)

  query = survey_model.PersonalExtension.query(
      survey_model.PersonalExtension.survey == ndb_survey_key,
      ancestor=ndb_profile_key)
  return query.get()


def getSurveyActivePeriod(survey, extension=None):
  """Returns period during which the specified survey is active.

  If no extension is specified, the period is simply defined by start and
  end dates of the specified survey.

  Otherwise, it is checked if the extension actually extends this period
  in any direction. Specifically, if its start date comes before the survey
  start date, the period of activeness starts when the extension starts.
  Similarly, if the extension ends after the survey normally ends, the period
  of activeness is extended to that point.

  Args:
    survey: survey entity
    extension: optional extension for the survey

  Returns:
    Period object describing when the specified survey is active.
  """
  if not extension:
    period_start = survey.survey_start
    period_end = survey.survey_end
  else:
    if not extension.start_date:
      period_start = survey.survey_start
    else:
      period_start = min(survey.survey_start, extension.start_date)

    if not extension.end_date:
      period_end = survey.survey_end
    else:
      period_end = max(survey.survey_end, extension.end_date)

  return Period(start=period_start, end=period_end)


def createOrUpdatePersonalExtension(profile_key, survey_key, **kwargs):
  """Creates personal extension for the specified survey and profile.

  In order to make sure that there is at most one personal extension between
  a particular profile and a survey, this function should be run within
  a transaction.

  The result of this function is saved in the datastore.

  Args:
    profile_key: profile_key.
    survey_key: survey key.

  Returns:
    newly created or updated personal extension entity.
  """
  extension = getPersonalExtension(profile_key, survey_key)
  if extension:
    extension.populate(**kwargs)
  else:
    # TODO(daniel): NDB migration; key does not need to be translated
    # when Profile and Survey models migrate to NDB
    ndb_survey_key = ndb.Key.from_old_key(survey_key)
    ndb_profile_key = ndb.Key.from_old_key(profile_key)
    extension = survey_model.PersonalExtension(
        parent=ndb_profile_key, survey=ndb_survey_key, **kwargs)
  extension.put()

  return extension
