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

import re

from soc.views.base_templates import ProgramSelect
from soc.views.template import Template

from soc.modules.gci.logic import program as program_logic
from soc.modules.gci.logic import ranking as ranking_logic
from soc.modules.gci.logic.ranking import winnersForProgram
from soc.modules.gci.views import forms
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


class GlobalRankingWinners(Template):
  """Templates to display winners of the program.
  """

  def context(self):
    winners = winnersForProgram(self.data)

    return {
        'winners': winners,
        }

  def templatePath(self):
    return 'v2/modules/gci/common_templates/_winners.html'


class OrgNominatedWinners(Template):
  """Template to display Grand Prize Winners of the program in
  which each organization nominates students who receive the award.
  """

  class Winner(object):
    """Representation of a single winner used by the template."""

    def __init__(self, profile):
      self.profile = profile
      self.avatar_name = None
      self.avatar_prefix = None

      if profile.avatar:
        avatar_groups = re.findall(forms.RE_AVATAR_COLOR, profile.avatar)
        # Being a bit pessimistic
        if avatar_groups:
          # We only want the first match, so pick group[0]
          name, prefix = avatar_groups[0]
          self.avatar_name = '%s-%s.jpg' % (name, prefix)
          self.avatar_prefix = prefix

    def organization(self):
      """Returns GCIOrganization associated with the winner."""
      return self.profile.student_info.winner_for

    def avatarPrefix(self):
      """Returns avatar prefix associated with the winner."""
      return self.avatar_prefix

    def avatarName(self):
      """Returns avatar name associated with the winner."""
      return self.avatar_name

  def context(self):
    winners = self._getWinnersForProgram(self.data.program)

    return {
        'winners': winners,
        }

  def templatePath(self):
    return 'v2/modules/gci/common_templates/_org_nominated_winners.html'

  def _getWinnersForProgram(self, program):
    """Returns the Grand Prize Winners for the specified program.

    Args:
      program: GCIProgram instance for which to retrieve the winners.

    Returns:
      a list containing GCIProfile instances which represent the winners
      ordered by the first name.
    """
    winners = []

    profiles = program_logic.getWinnersForProgram(program)
    for profile in profiles:
      winners.append(OrgNominatedWinners.Winner(profile))

    winners.sort(key=lambda o: o.profile.given_name.lower())

    return winners
