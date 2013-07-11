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

"""Module with time utilities."""

import datetime


def isBefore(date):
  """Tells whether the specified date is in the future.

  Args:
    date: datetime.datetime or datetime.date object

  Returns:
    True if it is before the specified date; False otherwise, or
      when the date is not given. 
  """
  return date and datetime.datetime.utcnow() < date


def isAfter(date):
  """Tells whether the specified date is in the past.

  Args:
    date: datetime.datetime or datetime.date object

  Returns:
    True if it is after the specified date; False otherwise, or
      when the date is not given. 
  """
  return date and date < datetime.datetime.utcnow()


def isBetween(start_date, end_date):
  """Tells whether it is between the the specified start date and the
  specified end date.

  It is assumed, and therefore not checked, if start date comes before end date.
  If that condition does not hold true, the result of this function is
  unspecified.

  Args:
    start_date: datetime.datetime or datetime.date object
    end_date: datetime.datetime or datetime.date object

  Returns:
    True if it is between the specified dates; False otherwise or if at least
      one of the dates is not given.
  """
  return isAfter(start_date) and isBefore(end_date)

