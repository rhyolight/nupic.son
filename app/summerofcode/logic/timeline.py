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

"""Functions for the Summer Of Code timeline."""

import datetime


def _createSlice(title, start, end):
  """Creates a dictionary representing a single timeline slice.

  Args:
    title: The name of the slice.
    start: A datetime.datetime indicating the beginning of the slice.
    end: A datetime.datetime indicating the end of the slice.

  Returns:
    A dictionary representing the slice to be JSON-encoded.
  """
  return {
      'title': title,
      'from': start.isoformat(),
      'to': end.isoformat(),
      }


def createTimelineDict(timeline_helper):
  """Creates a dictionary of timeline data for the timeline widget.

  Args:
    timeline_helper: A
      soc.modules.gsoc.views.helper.request_data.TimelineHelper describing
      the timeline of a Summer Of Code program.

  Returns:
    A dictionary of timeline data suitable for JSON-encoding and subsequent
      use with the timeline widget.
  """
  # TODO(nathaniel): This logic would have to be modified to handle
  # programs that span more than one calendar year.
  year_start = timeline_helper.timeline.program_start.replace(
      month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
  year_end = timeline_helper.timeline.program_end.replace(
      month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

  # TODO(nathaniel): Seriously, there's no representation in the data store
  # of when community bonding ends and the student coding begins? This explicit
  # specification of four weeks only applies to the 2014 program.
  four_weeks = datetime.timedelta(days=28)
  coding_start = (
      timeline_helper.timeline.accepted_students_announced_deadline +
      four_weeks)
  # TODO(nathaniel): And none of when the coding ends?
  thirteen_weeks = datetime.timedelta(days=91)
  coding_end = coding_start + thirteen_weeks

  first_off_season = _createSlice(
      'Off season', year_start, timeline_helper.timeline.program_start)
  organization_applications = _createSlice(
      'Organization applications', timeline_helper.orgSignupStart(),
      timeline_helper.orgSignupEnd())
  student_applications = _createSlice(
      'Student applications', timeline_helper.timeline.student_signup_start,
      timeline_helper.timeline.student_signup_end)
  community_bonding = _createSlice(
      'Community bonding',
      timeline_helper.timeline.accepted_students_announced_deadline,
      coding_start)
  coding = _createSlice('Students coding', coding_start, coding_end)
  second_off_season = _createSlice('Off season', coding_end, year_end)

  # TODO(nathaniel): Eliminate this in favor of one off season before the program
  # and another off season after the program.
  magic_begin = coding_end.replace(year=coding_end.year - 1)
  magic_off_season = _createSlice(
      'Off season', magic_begin, timeline_helper.orgSignupStart())

  return {
      'title_selector': '#timeline-head-title',
      'timerange_selector': '#timeline-head-timerange',
      'now': datetime.datetime.utcnow().isoformat(),
      'slices': [
          magic_off_season,
          organization_applications,
          student_applications,
          community_bonding,
          coding,
          # TODO(nathaniel): Enhance the widget to support a second off season
          # taking place between the program end and the calendar year's end.
          # second_off_season,
          ],
      }
