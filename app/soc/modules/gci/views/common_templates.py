#!/usr/bin/env python2.5
#
# Copyright 2011 the Melange authors.
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

"""This module contains the templates which are used across the views."""


from soc.views.base_templates import ProgramSelect
from soc.views.template import Template

from soc.modules.gci.logic import ranking as ranking_logic
from soc.modules.gci.logic.ranking import winnersForProgram
from soc.modules.gci.views.helper import url_names


class Timeline(Template):
  """Timeline template.
  """

  def context(self):

    if self.data.timeline.tasksPubliclyVisible():
      rem_days, rem_hours, rem_mins = self.data.timeline.remainingTime()
      remaining_time_message = 'Remaining'
    else:
      rem_days, rem_hours, rem_mins = self.data.timeline.tasksVisibleInTime()
      remaining_time_message = 'Starts in'

    complete_percentage = self.data.timeline.completePercentage()
    stopwatch_percentage = self.data.timeline.stopwatchPercentage()
    return {
        'remaining_days': rem_days,
        'remaining_hours': rem_hours,
        'remaining_minutes': rem_mins,
        'complete_percentage': complete_percentage,
        'stopwatch_percentage': stopwatch_percentage,
        'remaining_time_message': remaining_time_message
    }

  def templatePath(self):
    return "v2/modules/gci/common_templates/_timeline.html"


class YourScore(Template):
  """Template that is used to show score of the current user, provided
  he or she is a student.
  """

  def __init__(self, data):
    self.data = data
    self.score = None

    if self.data.profile and self.data.profile.student_info:
      self.score = ranking_logic.get(self.data.profile)

  def context(self):
    return {} if not self.score else {
        'points': self.score.points,
        'tasks': len(self.score.tasks),
        'my_tasks_link': self.data.redirect.profile(
            self.data.profile.link_id).urlOf(url_names.GCI_STUDENT_TASKS)
        }

  def render(self):
    """This template should only render to a non-empty string, if the
    current user is a student.
    """
    if not self.score:
      return ''

    return super(YourScore, self).render()

  def templatePath(self):
    return 'v2/modules/gci/common_templates/_your_score.html'


class ProgramSelect(ProgramSelect):
  """Program select template.
  """

  def templatePath(self):
    return 'v2/modules/gci/common_templates/_program_select.html'


class Winners(Template):
  """Templates to display winners of the program.
  """

  def context(self):
    winners = winnersForProgram(self.data)

    return {
        'winners': winners,
        }

  def templatePath(self):
    return 'v2/modules/gci/common_templates/_winners.html'
