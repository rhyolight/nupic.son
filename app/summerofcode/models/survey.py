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

"""Module with survey models."""

from google.appengine.ext import ndb

from soc.models import profile


class PersonalExtension(ndb.Model):
  """PersonalExtension model.

  It allows program administrators to set custom dates for the taker between
  which the survey has to be completed.

  Please note that it is intended that these dates are effective only if they
  actually extend the period when the user is allowed to take the survey,
  but this property is calculated and enforced by functions that use
  this model.
  In other words, start_date should take place before the start_date of the
  corresponding survey. Similarly, end_date should come after
  survey's end_survey date.

  Specifically, if an extension exists for a particular user, he or she will
  be able to take the survey from min(self.start_date,
  self.survey.survey_start) to max(self.end_date, self.survey.survey_end).

  At this moment end_date is not supported yet.

  Parent:
    models.profile.Profile
  """

  # key of the survey to which this extension applies
  # TODO(daniel): NDB migration: try adding kind and check if it works
  # when inheritance is in use
  survey = ndb.KeyProperty()

  # date from which the taker is allowed to complete the survey
  start_date = ndb.DateTimeProperty(indexed=False)

  # date before which the taker is allowed to complete they survey
  end_date = ndb.DateTimeProperty(indexed=False)
