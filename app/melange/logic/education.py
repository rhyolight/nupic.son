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

"""Logic for education."""

from google.appengine.api import datastore_errors

from melange.models import education as education_model
from melange.utils import rich_bool


def createPostSecondaryEducation(
    school_id, school_country, expected_graduation, major, degree):
  """Creates a new post secondary education entity based on
  the supplied properties.

  Args:
    school_id: Identifier of the school.
    school_country: Country of the school.
    expected_graduation: Int determining the expected graduation year.
    major: Major for the education.
    degree: Degree type for the education.

  Returns:
    RichBool whose value is set to True if education has been successfully
    created. In that case, extra part points to the newly created education
    entity. Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why the action could not be completed.
  """
  try:
    return rich_bool.RichBool(
        True, education_model.PostSecondaryEducation(
            school_id=school_id, school_country=school_country,
            expected_graduation=expected_graduation, major=major,
            degree=degree))
  except datastore_errors.BadValueError as e:
    return rich_bool.RichBool(False, str(e))
