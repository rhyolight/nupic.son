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

"""Module for the admin pages."""

from google.appengine.api import users

from django import forms as djangoforms
from django import http
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.models.user import User
from soc.views.dashboard import Dashboard
from soc.views.helper import url_patterns

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class LookupForm(gci_forms.GCIModelForm):
  """Django form for the lookup profile page.
  """

  class Meta:
    model = None

  def __init__(self, request_data, *args):
    super(LookupForm, self).__init__(*args)
    self.request_data = request_data

  email = djangoforms.CharField(label='Email')

  def clean_email(self):
    email_cleaner = cleaning.clean_email('email')

    try:
      email_address = email_cleaner(self)
    except djangoforms.ValidationError, e:
      if e.code != 'invalid':
        raise
      msg = ugettext(u'Enter a valid email address.')
      raise djangoforms.ValidationError(msg, code='invalid')

    account = users.User(email_address)
    user_account = accounts.normalizeAccount(account)
    user = User.all().filter('account', user_account).get()

    if not user:
      raise djangoforms.ValidationError(
          "There is no user with that email address")

    self.cleaned_data['user'] = user

    q = GCIProfile.all()
    q.filter('scope', self.request_data.program)
    q.ancestor(user)
    self.cleaned_data['profile'] = q.get()


class DashboardPage(GCIRequestHandler):
  """Dashboard for admins.
  """

  def djangoURLPatterns(self):
    return [
        url(r'admin/%s$' % url_patterns.PROGRAM,
         self, name='gci_admin_dashboard'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gci/admin/base.html'

  def context(self):
    """Context for dashboard page.
    """
    dashboards = []

    dashboards.append(MainDashboard(self.request, self.data))
    dashboards.append(ProgramSettingsDashboard(self.request, self.data))
    dashboards.append(OrgDashboard(self.request, self.data))
    dashboards.append(ParticipantsDashboard(self.request, self.data))

    return {
        'dashboards': dashboards,
        'page_name': 'Admin dashboard',
    }

  def post(self):
    """Handles a post request.

    Do nothing, since toggle button posting to this handler
    without expecting any response.
    """
    return http.HttpResponse()


class MainDashboard(Dashboard):
  """Dashboard for admin's main-dashboard
  """

  def __init__(self, request, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    super(MainDashboard, self).__init__(request, data)

  def context(self):
    """Returns the context of main dashboard.
    """
    r = self.data.redirect
    r.program()

    program_settings = ProgramSettingsDashboard(self.request, self.data)
    organizations = OrgDashboard(self.request, self.data)
    participants = ParticipantsDashboard(self.request, self.data)

    subpages = [
        {
            'name': 'lookup_profile',
            'description': ugettext(
                'Lookup profile of mentor or student from various program.'),
            'title': 'Lookup profile',
            'link': r.urlOf('lookup_gci_profile')
        },
        {
            'name': 'program_settings',
            'description': ugettext(
                'Edit program settings and timeline'),
            'title': 'Program settings',
            'link': '',
            'subpage_links': program_settings.getSubpagesLink(),
        },
        {
            'name': 'org_app',
            'description': ugettext(
                'Edit organization application'),
            'title': 'Organizations',
            'link': '',
            'subpage_links': organizations.getSubpagesLink(),
        },
        {
            'name': 'participants',
            'description': ugettext(
                'List of organization admins, mentors and students'),
            'title': 'Participants',
            'link': '',
            'subpage_links': participants.getSubpagesLink(),
        },
    ]

    return {
        'title': 'Admin Dashboard',
        'name': 'main',
        'subpages': self._divideSubPages(subpages),
        'enabled': True
    }


class ProgramSettingsDashboard(Dashboard):
  """Dashboard for admin's program-settings-dashboard
  """

  def __init__(self, request, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    r = data.redirect
    r.program()

    subpages = [
        {
            'name': 'edit_program',
            'description': ugettext(
                'Edit your program settings such as information, slots, '
                'documents, etc.'),
            'title': 'Edit program',
            'link': r.urlOf('edit_gci_program')
        },
        {
            'name': 'edit_timeline',
            'description': ugettext(
                'Edit your program timeline such as program start/end date, '
                'student signup start/end date, etc.'),
            'title': 'Edit timeline',
            'link': r.urlOf('edit_gci_timeline')
        },
        {
            'name': 'edit_program_messages',
            'description': ugettext(
                'Edit program messages which will be sent in emails '
                'to the specified participants.'),
            'title': 'Edit messages',
            'link': r.urlOf(url_names.GCI_EDIT_PROGRAM_MESSAGES)
        },
        {
            'name': 'documents',
            'description': ugettext(
                'List of documents from various program.'),
            'title': 'List of documents',
            'link': r.urlOf('list_gci_documents')
        },
    ]

    super(ProgramSettingsDashboard, self).__init__(request, data, subpages)

  def context(self):
    """Returns the context of program settings dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Program Settings',
        'name': 'program_settings',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class OrgDashboard(Dashboard):
  """Dashboard for admin's Organization related information.

  This page includes links for Org app surveys, mentoring org info, etc.
  """

  def __init__(self, request, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    r = data.redirect
    r.program()

    subpages = [
        {
            'name': 'edit_org_app',
            'description': ugettext(
                'Create or edit organization application'),
            'title': 'Edit organization application',
            'link': r.urlOf('gci_edit_org_app')
        },
        {
            'name': 'org_app_records',
            'description': ugettext(
                'List of submitted organization application'),
            'title': 'Organization application records',
            'link': r.urlOf('gci_list_org_app_records')
        },
        {
            'name': 'accepted_orgs',
            'description': ugettext(
                'List of accepted organizations'),
            'title': 'Accepted Organizations',
            'link': r.urlOf('gci_admin_accepted_orgs')
        },
        {
            'name': 'org_scores',
            'description': ugettext(
                'List of student scores for the chosen organization'),
            'title': 'Organization Scores',
            'link': r.urlOf(url_names.GCI_ORG_CHOOSE_FOR_SCORE)
        },
        {
            'name': 'org_tasks',
            'description': ugettext(
                'List of tasks that have been created by '
                'the chosen organization'),
            'title': 'Organization Tasks',
            'link': r.urlOf(url_names.GCI_ORG_CHOOSE_FOR_ALL_TASKS)
        },
        {
            'name': 'proposed_winners',
            'description': ugettext(
                'List of the Grand Prize Winners that have been proposed by '
                'organizations'),
            'title': 'Proposed Grand Prize Winners',
            'link': r.urlOf(url_names.GCI_VIEW_PROPOSED_WINNERS)
        },
    ]

    super(OrgDashboard, self).__init__(request, data, subpages)

  def context(self):
    """Returns the context of organization dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Organization Application',
        'name': 'org_app',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class ParticipantsDashboard(Dashboard):
  """Dashboard for admin's all participants dashboard
  """

  def __init__(self, request, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    r = data.redirect
    r.program()

    subpages = [
        {
            'name': 'list_mentors',
            'description': ugettext(
                'List of all the organization admins and mentors'),
            'title': 'List mentors and admins',
            'link': r.urlOf('gci_list_mentors')
        },
        {
            'name': 'list_students',
            'description': ugettext(
                'List of all participating students'),
            'title': 'List students',
            'link': r.urlOf(url_names.GCI_STUDENTS_INFO)
        },
        {
            'name': 'leaderboard',
            'description': ugettext(
                'Leaderboard for the program'),
            'title': 'Leaderboard',
            'link': r.urlOf(url_names.GCI_LEADERBOARD)
        },
    ]

    super(ParticipantsDashboard, self).__init__(request, data, subpages)

  def context(self):
    """Returns the context of participants dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Participants',
        'name': 'participants',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class LookupLinkIdPage(GCIRequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'admin/lookup/%s$' % url_patterns.PROGRAM,
         self, name='lookup_gci_profile'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gci/admin/lookup.html'

  def post(self):
    # TODO(nathaniel): problematic self-call.
    return self.get()

  def context(self):
    form = LookupForm(self.data, self.data.POST or None)
    error = bool(form.errors)

    forms = [form]
    profile = None

    if not form.errors and self.data.request.method == 'POST':
      profile = form.cleaned_data.get('profile')

    if profile:
      # TODO(nathaniel): setting redirection in a context() method?
      self.redirect.profile(profile.link_id)
      self.redirect.to(url_names.GCI_PROFILE_SHOW_ADMIN, secure=True)

    return {
      'forms': forms,
      'error': error,
      'posted': error,
      'page_name': 'Lookup profile',
    }
