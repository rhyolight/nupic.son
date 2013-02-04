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

"""Module containing the views for GCI home page."""


from django.utils import translation

from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.logic import organization as org_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models import program as program_model
from soc.modules.gci.views import common_templates
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


class HowItWorks(Template):
  """How it works template."""

  CONTEST_BEGINS_ON_MSG = translation.ugettext('Contest begins on %s')

  CONTEST_CLOSED_ON_MSG = translation.ugettext('Contest closed on %s')

  GET_STARTED_NOW_MSG = translation.ugettext('Get Started Now!')

  def __init__(self, data):
    self.data = data

  def context(self):
    program = self.data.program

    from soc.modules.gci.models.program import GCIProgram
    about_page = GCIProgram.about_page.get_value_for_datastore(program)

    example_tasks_link = ''
    all_tasks_link = ''

    main_text = self._getMainText()

    if self.data.timeline.orgSignup():
      # TODO(nathaniel): make this .program() call unnecessary.
      self.data.redirect.program()

      start_text = 'Sign up as organization'
      start_link = self.data.redirect.urlOf('gci_take_org_app')
      if self.data.program.example_tasks:
        example_tasks_link = self.data.program.example_tasks
    elif self.data.timeline.studentSignup() and not self.data.profile:
      start_text = 'Register as a Student'

      start_link = self.data.redirect.createProfile('student').urlOf(
          'create_gci_profile', secure=True)

      # TODO(nathaniel): make this .program() call unnecessary.
      self.data.redirect.program()

      all_tasks_link = self.data.redirect.urlOf(url_names.GCI_ALL_TASKS_LIST)
    elif self.data.timeline.tasksPubliclyVisible():
      # TODO(nathaniel): make this .program() call unnecessary.
      self.data.redirect.program()

      start_text = 'Search for tasks'
      start_link = self.data.redirect.urlOf('gci_list_tasks')
    elif self.data.program.example_tasks:
      start_text = 'See example tasks'
      start_link = self.data.program.example_tasks
    else:
      start_text = start_link = ''

    return {
        'about_link': self.data.redirect.document(about_page).url(),
        'start_text': start_text,
        'start_link': start_link,
        'example_tasks_link': example_tasks_link,
        'all_tasks_link': all_tasks_link,
        'main_text': main_text,
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_how_it_works.html"

  def _getMainText(self):
    if self.data.timeline.beforeStudentSignupStart():
      sign_up_start = self.data.timeline.studentSignupStart()
      return self.CONTEST_BEGINS_ON_MSG % (sign_up_start.strftime('%b %d'),)
    elif self.data.timeline.studentSignup():
      return self.GET_STARTED_NOW_MSG
    elif self.data.timeline.afterStopAllWorkDeadline():
      contest_closed = self.data.timeline.stopAllWorkDeadline()
      return self.CONTEST_CLOSED_ON_MSG % (contest_closed.strftime('%b %d'),)


class FeaturedTask(Template):
  """Featured task template.
  """

  def __init__(self, data, featured_task):
    self.data = data
    self.featured_task = featured_task

  def context(self):
    task_url = self.data.redirect.id(self.featured_task.key().id()).urlOf(
        'gci_view_task')

    return {
        'featured_task': self.featured_task,
        'featured_task_url': task_url,
        }

  def templatePath(self):
    return "v2/modules/gci/homepage/_featured_task.html"


class ParticipatingOrgs(Template):
  """Participating orgs template."""

  _TABLE_WIDTH = 5
  _ORG_COUNT = 10

  def __init__(self, data):
    self.data = data

  def context(self):
    participating_orgs = []
    current_orgs = org_logic.participating(
        self.data.program, org_count=self._ORG_COUNT)
    for org in current_orgs:
      participating_orgs.append({
          'link': self.data.redirect.orgHomepage(org.link_id).url(),
          'logo': org.logo_url,
          'name': org.short_name,
          })

    participating_orgs_table_rows = []
    orgs = list(participating_orgs)
    while True:
      if not orgs:
        break
      elif len(orgs) <= self._TABLE_WIDTH:
        participating_orgs_table_rows.append(orgs)
        break
      else:
        row, orgs = orgs[:self._TABLE_WIDTH], orgs[self._TABLE_WIDTH:]
        participating_orgs_table_rows.append(row)

    # TODO(nathaniel): make this .program() call unnecessary.
    self.data.redirect.program()

    accepted_orgs_url = self.data.redirect.urlOf('gci_accepted_orgs')

    return {
        'participating_orgs': participating_orgs,
        'participating_orgs_table_rows': participating_orgs_table_rows,
        'org_list_url': accepted_orgs_url,
        'all_participating_orgs': (
            self.data.program.nr_accepted_orgs <= len(participating_orgs)),
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_participating_orgs.html"


class Leaderboard(Template):
  """Leaderboard template."""

  def __init__(self, data):
    self.data = data

  def context(self):
    # TODO(nathaniel): make this .program() call unnecessary.
    self.data.redirect.program()

    return {
        'leaderboard_url': self.data.redirect.urlOf(url_names.GCI_LEADERBOARD),
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_leaderboard.html"


class ConnectWithUs(Template):
  """Connect with us template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'program': self.data.program,
    }

  def templatePath(self):
    return "v2/modules/gci/homepage/_connect_with_us.html"


class Homepage(GCIRequestHandler):
  """Encapsulate all the methods required to generate GCI Home page.
  """

  def templatePath(self):
    return 'v2/modules/gci/homepage/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'homepage/%s$' % url_patterns.PROGRAM, self,
            name='gci_homepage'),
        url(r'program/home/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self):
    self.check.isProgramVisible()

  def context(self):
    current_timeline = self.data.timeline.currentPeriod()

    context = {
        'page_name': '%s - Home page' % (self.data.program.name),
        'how_it_works': HowItWorks(self.data),
        'participating_orgs': ParticipatingOrgs(self.data),
        'timeline': common_templates.Timeline(self.data),
        'complete_percentage': self.data.timeline.completePercentage(),
        'current_timeline': current_timeline,
        'connect_with_us': ConnectWithUs(self.data),
        'program': self.data.program,
    }

    if current_timeline in ['student_signup_period',
        'working_period', 'offseason']:
      featured_task = task_logic.getFeaturedTask(self.data.program)

      if featured_task:
        context['featured_task'] = FeaturedTask(self.data, featured_task)

    if self.data.is_host or self.data.timeline.winnersAnnounced():
      context['winners'] = self._getWinnersTemplate(
          self.data.program.winner_selection_type)

    return context

  def _getWinnersTemplate(self, winner_selection_type):
    """Factory method that returns a template to displays the Grand
    Prize Winners of the program with the specified winner selection type.

    Args:
      winner_selection_type: the specified WinnerSelectionType.

    Returns:
      a template appropriate for the specified winner selection type.
    """
    if (winner_selection_type ==
        program_model.WinnerSelectionType.ORG_NOMINATED):
      return common_templates.OrgNominatedWinners(self.data)
    elif (winner_selection_type ==
        program_model.WinnerSelectionType.GLOBAL_RANKING):
      return common_templates.GlobalRankingWinners(self.data)
    else:
      raise ValueError(
         'Invalid value of winner_selection_type %s' % winner_selection_type)
