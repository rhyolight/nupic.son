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

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import db

from django import forms as djangoforms
from django import http
from django.utils.translation import ugettext

from melange.request import access
from melange.request import exception

from soc.logic import accounts
from soc.logic import cleaning
from soc.models.user import User
from soc.views.dashboard import Dashboard
from soc.views.helper import addresses
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic.proposal import getProposalsToBeAcceptedForOrg
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.profile import GSoCStudentInfo
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.models.proposal import GSoCProposal
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.modules.gsoc.views import projects_list

from summerofcode.request import links
from summerofcode.views.helper import urls


class LookupForm(gsoc_forms.GSoCModelForm):
  """Django form for the lookup profile page."""

  class Meta:
    model = None

  def __init__(self, request_data=None, **kwargs):
    super(LookupForm, self).__init__(**kwargs)
    self.request_data = request_data

  email = djangoforms.CharField(label='Email')

  def clean_email(self):
    email_cleaner = cleaning.clean_email('email')

    try:
      email_address = email_cleaner(self)
    except djangoforms.ValidationError as e:
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

    q = GSoCProfile.all()
    q.filter('scope', self.request_data.program)
    q.ancestor(user)
    self.cleaned_data['profile'] = q.get()


class DashboardPage(base.GSoCRequestHandler):
  """Dashboard for admins."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_admin_dashboard'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/base.html'

  def context(self, data, check, mutator):
    """Context for dashboard page."""
    dashboards = []

    dashboards.append(MainDashboard(data))
    dashboards.append(ProgramSettingsDashboard(data))
    dashboards.append(ManageOrganizationsDashboard(data))
    dashboards.append(EvaluationsDashboard(data))
    dashboards.append(MentorEvaluationsDashboard(data))
    dashboards.append(StudentEvaluationsDashboard(data))
    dashboards.append(EvaluationGroupDashboard(data))
    dashboards.append(StudentsDashboard(data))

    return {
        'dashboards': dashboards,
        'page_name': 'Admin dashboard',
    }

  def post(self, data, check, mutator):
    """Handles a post request.

    Do nothing, since toggle button posting to this handler
    without expecting any response.
    """
    return http.HttpResponse()


class MainDashboard(Dashboard):
  """Dashboard for admin's main-dashboard."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    super(MainDashboard, self).__init__(data)

  def context(self):
    """Returns the context of main dashboard."""
    # TODO(nathaniel): Eliminate this state-setting call.
    self.data.redirect.program()

    manage_orgs = ManageOrganizationsDashboard(self.data)
    program_settings = ProgramSettingsDashboard(self.data)
    evaluations = EvaluationsDashboard(self.data)
    participants = ParticipantsDashboard(self.data)
    students = StudentsDashboard(self.data)

    subpages = [
        {
            'name': 'lookup_profile',
            'description': ugettext(
                'Lookup profile of mentor or student from various program.'),
            'title': 'Lookup profile',
            'link': self.data.redirect.urlOf('lookup_gsoc_profile')
        },
        {
            'name': 'allocate_slots',
            'description': ugettext(
                'Allocate slots (number of acceptable projects) per '
                'organization'),
            'title': 'Allocate slots',
            'link': self.data.redirect.urlOf('gsoc_slots')
        },
        {
            'name': 'slots_transfer',
            'description': ugettext(
                'Transfer slots for organizations'),
            'title': 'Slots transfer',
            'link': self.data.redirect.urlOf('gsoc_admin_slots_transfer')
        },
        {
            'name': 'duplicates',
            'description': ugettext(
                'Calculate how many duplicate proposals, students that have '
                'accepted proposals more than one'),
            'title': 'Duplicates',
            'link': self.data.redirect.urlOf('gsoc_view_duplicates')
        },
        {
            'name': 'accept_proposals',
            'description': ugettext(
                'Start proposals into projects conversion'),
            'title': 'Bulk accept proposals and send acceptance/rejection '
                     'emails',
            'link': self.data.redirect.urlOf('gsoc_accept_proposals')
        },
        {
            'name': 'manage_proposals',
            'description': ugettext(
                'Lists all the proposals submitted to the program and lets '
                'accept individual proposals.'),
            'title': 'Proposals submitted',
            'link': self.data.redirect.urlOf('gsoc_admin_accept_proposals')
        },
        {
            'name': 'withdraw_projects',
            'description': ugettext(
                'Withdraw accepted projects or accept withdrawn projects'),
            'title': 'Accept/withdraw projects',
            'link': self.data.redirect.urlOf('gsoc_withdraw_projects')
        },
        {
            'name': 'participants',
            'description': ugettext(
                'List of all participants in this program.'),
            'title': 'Participants',
            'link': '',
            'subpage_links': participants.getSubpagesLink(),
        },
        {
            'name': 'students',
            'description': ugettext(
                'Manage all the Student\'s projects.'),
            'title': 'Students',
            'link': '',
            'subpage_links': students.getSubpagesLink(),
        },
        {
            'name': 'manage_organizations',
            'description': ugettext(
                'Manage organizations from active program. You can allocate '
                'slots for organizations, list mentors and administrators '
                'from various organizations'),
            'title': 'Manage organizations',
            'link': '',
            'subpage_links': manage_orgs.getSubpagesLink(),
        },
        {
            'name': 'evaluations',
            'description': ugettext(
                'Send reminder, evaluation group, create, edit, '
                'view evaluations for mentors and students'),
            'title': 'Evaluations',
            'link': '',
            'subpage_links': evaluations.getSubpagesLink(),
        },
        {
            'name': 'program_settings',
            'description': ugettext(
                'Edit program settings and timeline'),
            'title': 'Program settings',
            'link': '',
            'subpage_links': program_settings.getSubpagesLink(),
        },
    ]

    return {
        'title': 'Admin Dashboard',
        'name': 'main',
        'subpages': self._divideSubPages(subpages),
        'enabled': True
    }


class ProgramSettingsDashboard(Dashboard):
  """Dashboard for admin's program-settings-dashboard."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    # TODO(nathaniel): Eliminate this state-setting call.
    data.redirect.program()

    subpages = [
        {
            'name': 'edit_program',
            'description': ugettext(
                'Edit your program settings such as information, slots, '
                'documents, etc.'),
            'title': 'Edit program settings',
            'link': data.redirect.urlOf(url_names.GSOC_PROGRAM_EDIT)
        },
        {
            'name': 'edit_timeline',
            'description': ugettext(
                'Edit your program timeline such as program start/end date, '
                'student signup start/end date, etc.'),
            'title': 'Edit timeline',
            'link': data.redirect.urlOf('edit_gsoc_timeline')
        },
        {
            'name': 'edit_program_messages',
            'description': ugettext(
                'Edit program messages which will be sent in emails '
                'to the specified participants.'),
            'title': 'Edit messages',
            'link': data.redirect.urlOf(url_names.GSOC_EDIT_PROGRAM_MESSAGES)
        },
        {
            'name': 'documents',
            'description': ugettext(
                'List of documents from various program.'),
            'title': 'List of documents',
            'link': data.redirect.urlOf('list_gsoc_documents')
        },
        {
            'name': 'create_program',
            'description': ugettext(
                'Create a new program.'),
            'title': 'Create a program',
            'link': links.SOC_LINKER.sponsor(
                data.sponsor, url_names.GSOC_PROGRAM_CREATE),
        },
    ]

    super(ProgramSettingsDashboard, self).__init__(data, subpages)

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


class ManageOrganizationsDashboard(Dashboard):
  """Dashboard for admin's manage-organizations-dashboard."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    # TODO(nathaniel): Eliminate this state-setting call.
    data.redirect.program()

    subpages = [
        {
            'name': 'edit_org_app',
            'description': ugettext(
                'Create or edit organization application'),
            'title': 'Edit organization application',
            'link': data.redirect.urlOf('gsoc_edit_org_app')
        },
        {
            'name': 'preview_org_app',
            'description': ugettext(
                'Preview of the organization application.'),
            'title': 'Preview organization application',
            'link': data.redirect.urlOf('gsoc_preview_org_app')
        },
        {
            'name': 'org_app_records',
            'description': ugettext(
                'List of submitted organization application'),
            'title': 'Organization application records',
            'link': data.redirect.urlOf('gsoc_list_org_app_records')
        },
        {
            'name': 'accepted_orgs',
            'description': ugettext(
                'List of accepted organizations'),
            'title': 'Accepted Organizations',
            'link': data.redirect.urlOf(url_names.GSOC_ORG_LIST_FOR_HOST),
        },
    ]

    super(ManageOrganizationsDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of manage organizations dashboard."""
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Manage Organizations',
        'name': 'manage_organizations',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class EvaluationsDashboard(Dashboard):
  """Dashboard for admin's evaluations-dashboard."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    mentor_evaluations = MentorEvaluationsDashboard(data)
    student_evaluations = StudentEvaluationsDashboard(data)
    evaluation_group = EvaluationGroupDashboard(data)

    # TODO(nathaniel): Eliminate this state-setting call.
    data.redirect.program()

    subpages = [
        {
            'name': 'reminder_emails',
            'description': ugettext(
                'Send reminder emails for evaluations.'),
            'title': 'Send reminder',
            'link': data.redirect.urlOf('gsoc_survey_reminder_admin')
        },
        {
            'name': 'mentor_evaluations',
            'description': ugettext(
                'Create, edit and view evaluations for mentors'),
            'title': 'Mentor Evaluations',
            'link': '',
            'subpage_links': mentor_evaluations.getSubpagesLink(),
        },
        {
            'name': 'student_evaluations',
            'description': ugettext(
                'Create, edit and view evaluations for students'),
            'title': 'Student Evaluations',
            'link': '',
            'subpage_links': student_evaluations.getSubpagesLink(),
        },
        {
            'name': 'evaluation_group',
            'description': ugettext('Manage the results of the evaluation'),
            'title': 'Evaluation Group',
            'link': '',
            'subpage_links': evaluation_group.getSubpagesLink(),
        },
    ]

    super(EvaluationsDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of manage organizations dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Evaluations',
        'name': 'evaluations',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class MentorEvaluationsDashboard(Dashboard):
  """Dashboard for mentor's evaluations."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    survey_key = db.Key.from_path(
        GradingProjectSurvey.kind(), '%s/%s' % (
            data.program.key().name(), 'midterm'))
    subpages = [
        {
            'name': 'edit_mentor_evaluation',
            'description': ugettext('Create or edit midterm evaluation for '
                'mentors in active program'),
            'title': 'Create or Edit Midterm',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_edit_mentor_evaluation')
        },
        {
            'name': 'preview_mentor_evaluation',
            'description': ugettext('Preview midterm evaluation to be '
                'administered mentors.'),
            'title': 'Preview Midterm Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_preview_mentor_evaluation')
        },
        {
            'name': 'view_mentor_evaluation',
            'description': ugettext('View midterm evaluation for mentors'),
            'title': 'View Midterm Records',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_list_mentor_eval_records')
        },
    ]

    survey_key = db.Key.from_path(
        GradingProjectSurvey.kind(), '%s/%s' % (
            data.program.key().name(), 'final'))
    subpages += [
        {
            'name': 'edit_mentor_evaluation',
            'description': ugettext('Create or edit midterm evaluation for '
                'mentors in active program'),
            'title': 'Create or Edit Final Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_edit_mentor_evaluation')
        },
        {
            'name': 'preview_mentor_evaluation',
            'description': ugettext('Preview final evaluation to be '
                'administered mentors.'),
            'title': 'Preview Final Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_preview_mentor_evaluation')
        },
        {
            'name': 'view_mentor_evaluation',
            'description': ugettext('View final evaluation for mentors'),
            'title': 'View Final Evaluation Records',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_list_mentor_eval_records')
        },
    ]

    super(MentorEvaluationsDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of mentor evaluations dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Mentor Evaluations',
        'name': 'mentor_evaluations',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
            {
                'to': 'evaluations',
                'title': 'Evaluations'
            },
        ],
        'subpages': subpages
    }


class StudentEvaluationsDashboard(Dashboard):
  """Dashboard for student's evaluations."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    survey_key = db.Key.from_path(
        ProjectSurvey.kind(), '%s/%s' % (data.program.key().name(), 'midterm'))
    subpages = [
        {
            'name': 'edit_student_evaluation',
            'description': ugettext('Create or edit midterm evaluation for '
                'students in active program'),
            'title': 'Create or Edit Midterm Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_edit_student_evaluation')
        },
        {
            'name': 'preview_student_evaluation',
            'description': ugettext('Preview midterm evaluation to be '
                'administered to the students.'),
            'title': 'Preview Midterm Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_preview_student_evaluation')
        },
        {
            'name': 'view_student_evaluation',
            'description': ugettext('View midterm evaluation for students'),
            'title': 'View Midterm Evaluation Records',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_list_student_eval_records')
        },
    ]

    survey_key = db.Key.from_path(
        ProjectSurvey.kind(), '%s/%s' % (data.program.key().name(), 'final'))
    subpages += [
        {
            'name': 'edit_student_evaluation',
            'description': ugettext('Create or edit final evaluation for '
                'students in active program'),
            'title': 'Create or Edit Final Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_edit_student_evaluation')
        },
        {
            'name': 'preview_student_evaluation',
            'description': ugettext('Preview final evaluation to be '
                'administered to the students.'),
            'title': 'Preview Final Evaluation',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_preview_student_evaluation')
        },
        {
            'name': 'view_student_evaluation',
            'description': ugettext('View final evaluation for students'),
            'title': 'View Final Evaluation Records',
            'link': links.SOC_LINKER.survey(
                survey_key, 'gsoc_list_student_eval_records')
        },
    ]

    super(StudentEvaluationsDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of student evaluations dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Student Evaluations',
        'name': 'student_evaluations',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
            {
                'to': 'evaluations',
                'title': 'Evaluations'
            },
        ],
        'subpages': subpages
    }


class EvaluationGroupDashboard(Dashboard):
  """Dashboard for evaluation group."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    # TODO(nathaniel): Eliminate this state-setting call.
    data.redirect.program()

    subpages = [
        {
            'name': 'edit_evaluation_group',
            'description': ugettext('Create evaluation group'),
            'title': 'Create',
            'link': data.redirect.urlOf('gsoc_grading_group')
        },
    ]

    q = GSoCGradingSurveyGroup.all()
    q.filter('program', data.program)

    for group in q:
      data.redirect.id(group.key().id())
      subpages.append(
        {
            'name': 'view_evaluation_group_%s' % group.key().id(),
            'description': ugettext('View this group'),
            'title': 'View %s' % group.name,
            'link': data.redirect.urlOf('gsoc_grading_record_overview')
        }
      )

    super(EvaluationGroupDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of evaluation group dashboard."""
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Evaluation Group',
        'name': 'evaluation_group',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
            {
                'to': 'evaluations',
                'title': 'Evaluations'
            },
        ],
        'subpages': subpages
    }


class ParticipantsDashboard(Dashboard):
  """Dashboard for admin's all participants dashboard
  """

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    # TODO(nathaniel): Eliminate this state-setting call.
    data.redirect.program()

    subpages = [
        {
            'name': 'list_mentors',
            'description': ugettext(
                'List of all the organization admins and mentors'),
            'title': 'List mentors and admins',
            'link': data.redirect.urlOf('gsoc_list_mentors')
        },
        {
            'name': 'list_students',
            'description': ugettext(
                'List of all participating students'),
            'title': 'List students',
            'link': data.redirect.urlOf('gsoc_students_list_admin')
        },
    ]

    super(ParticipantsDashboard, self).__init__(data, subpages)

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


class StudentsDashboard(Dashboard):
  """Dashboard for student related items."""

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    # TODO(nathaniel): Eliminate this state-setting call.
    data.redirect.program()

    subpages = [
        {
            'name': 'list_projects',
            'description': ugettext(
                'List of all the projects who have accepted to the program.'),
            'title': 'View All Projects',
            'link': data.redirect.urlOf('gsoc_projects_list_admin')
        },
        {
            'name': 'manage_projects',
            'description': ugettext(
                'Manage the projects that have accepted to the program.'),
            'title': 'Manage Projects',
            'link': data.redirect.urlOf(
                url_names.GSOC_ADMIN_MANAGE_PROJECTS_LIST)
        },
    ]

    super(StudentsDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of manage students dashboard."""
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Students',
        'name': 'students',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class LookupLinkIdPage(base.GSoCRequestHandler):
  """View for the participant profile."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/lookup/%s$' % url_patterns.PROGRAM, self,
            name='lookup_gsoc_profile'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/lookup.html'

  def post(self, data, check, mutator):
    # TODO(nathaniel): problematic self-call.
    return self.get(data, check, mutator)

  def context(self, data, check, mutator):
    form = LookupForm(request_data=data, data=data.POST or None)
    error = bool(form.errors)

    forms = [form]
    profile = None

    if not form.errors and data.request.method == 'POST':
      profile = form.cleaned_data.get('profile')

    if profile:
      # TODO(nathaniel): Find a cleaner way to do this rather than
      # generating a response and then tossing it.
      data.redirect.profile(profile.link_id)
      response = data.redirect.to(
          url_names.GSOC_PROFILE_SHOW_ADMIN, secure=True)
      raise exception.Redirect(response['Location'])
    else:
      return {
        'forms': forms,
        'error': error,
        'posted': error,
        'page_name': 'Lookup profile',
      }


class ProposalsList(Template):
  """Template for listing all the proposals sent to org.
  """

  def __init__(self, request, data):
    """Initializes this proposals list."""
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn(
        'email', 'Student Email',
        (lambda ent, *args: ent.parent().email), hidden=True)
    list_config.addSimpleColumn('score', 'Score')
    list_config.addSimpleColumn('nr_scores', '#scores', hidden=True)
    def getAverage(ent):
      if not ent.nr_scores:
        return float(0)

      average = float(ent.score)/float(ent.nr_scores)
      return float("%.2f" % average)

    list_config.addNumericalColumn(
        'average', 'Average', lambda ent, *a: getAverage(ent))

    def getStatusOnDashboard(proposal, accepted, duplicates):
      """Method for determining which status to show on the dashboard."""
      # TODO(nathaniel): HTML in Python.
      if proposal.status == 'pending':
        if proposal.accept_as_project and (
            not GSoCProposal.mentor.get_value_for_datastore(proposal)):
          return """<strong><font color="red">No mentor assigned</font></strong>"""
        elif proposal.key() in duplicates:
          return """<strong><font color="red">Duplicate</font></strong>"""
        elif proposal.key() in accepted:
          return """<strong><font color="green">Pending acceptance</font><strong>"""
      # not showing duplicates or proposal doesn't have an interesting state
      return proposal.status
    options = [
        # TODO(nathaniel): This looks like structured data that should be
        # properly modeled in first-class structured Python objects.
        ('(pending|accepted|rejected|duplicate|mentor)', 'Valid'),
        ('(duplicate|mentor)', 'Needs attention'),
        ('(duplicate)', 'Duplicate'),
        ('(accepted)', 'Accepted'),
        ('(rejected)', 'Rejected'),
        ('(mentor)', 'No mentor assigned'),
        ('', 'All'),
        ('(invalid|withdrawn|ignored)', 'Invalid'),
    ]
    list_config.addHtmlColumn('status', 'Status',
        getStatusOnDashboard, options=options)

    list_config.addSimpleColumn('last_modified_on', 'Last modified',
                                column_type=lists.DATE)
    list_config.addSimpleColumn('created_on', 'Created on',
                                column_type=lists.DATE, hidden=True)
    list_config.addPlainTextColumn(
        'student', 'Student',
        lambda ent, *args: ent.parent().name())
    list_config.addSimpleColumn('accept_as_project', 'Should accept')

    # hidden keys
    list_config.addPlainTextColumn(
        'full_proposal_key', 'Full proposal key',
        (lambda ent, *args: str(ent.key())), hidden=True)
    list_config.addPlainTextColumn(
        'org_key', 'Organization key',
        (lambda ent, *args: ent.org.key().name()), hidden=True)

    list_config.setDefaultSort('last_modified_on', 'desc')

    self._list_config = list_config

  def templatePath(self):
    return'modules/gsoc/admin/_proposals_list.html'

  def context(self):
    description = 'List of proposals submitted into %s' % self.data.organization.name

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0, description=description)
    return {
        'name': 'proposals_submitted',
        'title': 'PROPOSALS SUBMITTED TO MY ORGS',
        'lists': [list_configuration_response],
        }

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    org = self.data.organization
    program = self.data.program

    # Hold all the accepted projects for orgs where this user is a member of
    accepted = []
    # Hold all duplicates for either the entire program or the orgs of the user.
    duplicates = []
    dupQ = GSoCProposalDuplicate.all()
    dupQ.filter('is_duplicate', True)
    dupQ.filter('org', org)
    dupQ.filter('program', program)

    accepted.extend([p.key() for p in getProposalsToBeAcceptedForOrg(org)])

    duplicate_entities = dupQ.fetch(1000)
    for dup in duplicate_entities:
      duplicates.extend(dup.duplicates)

    q = GSoCProposal.all()
    q.filter('org', org)
    q.filter('program', program)

    starter = lists.keyStarter
    prefetcher = lists.ModelPrefetcher(GSoCProposal, ['org'], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter, prefetcher=prefetcher)
    return response_builder.build(accepted, duplicates)


class ProposalsPage(base.GSoCRequestHandler):
  """View for proposals for particular org."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/proposals/%s$' % url_patterns.ORG, self,
            name='gsoc_proposals_org'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_content = ProposalsList(data.request, data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    """Handler for POST requests."""
    proposals_list = ProposalsList(data.request, data)
    if proposals_list.post():
      return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Proposal page',
      # TODO(nathaniel): Drop the first parameter of ProposalsList.
      'list': ProposalsList(data.request, data),
    }


class ProjectsList(Template):
  """Template for listing all projects of particular org."""

  def __init__(self, request, data):
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('student', 'Student',
        lambda entity, *args: entity.parent().name())
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization',
        lambda entity, *args: entity.org.name)
    list_config.addPlainTextColumn(
        'mentors', 'Mentor',
        lambda entity, m, *args: [m[i].name() for i in entity.mentors])
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('student')

    self._list_config = list_config

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0,
        description='List of projects under %s that ' \
            'accepted into %s' % (
            self.data.organization.name, self.data.program.name))

    return {
        'lists': [list_configuration_response],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      list_query = project_logic.getAcceptedProjectsQuery(
          program=self.data.program, org=self.data.organization)

      starter = lists.keyStarter
      prefetcher = lists.ListModelPrefetcher(
          GSoCProject, ['org'], ['mentors'], parent=True)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, list_query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return "modules/gsoc/admin/_projects_list.html"


class SurveyReminderPage(base.GSoCRequestHandler):
  """Page to send out reminder emails to fill out a Survey."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/survey_reminder/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_survey_reminder_admin'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/survey_reminder.html'

  def post(self, data, check, mutator):
    post_dict = data.request.POST

    task_params = {
        'program_key': data.program.key().id_or_name(),
        'survey_key': post_dict['key'],
        'survey_type': post_dict['type']
    }

    task = taskqueue.Task(url=data.redirect.urlOf('spawn_survey_reminders'),
                          params=task_params)
    task.add()

    return http.HttpResponseRedirect(
        data.request.path + '?msg=Reminders are being sent')

  def context(self, data, check, mutator):
    q = GradingProjectSurvey.all()
    q.filter('scope', data.program)
    mentor_surveys = q.fetch(1000)

    q = ProjectSurvey.all()
    q.filter('scope', data.program)
    student_surveys = q.fetch(1000)

    return {
      'page_name': 'Sending Evaluation Reminders',
      'mentor_surveys': mentor_surveys,
      'student_surveys': student_surveys,
      'msg': data.request.GET.get('msg', '')
    }


def taxFormSubmittedValue(profile, prefetched_data):
  """Returns value for 'Tax Form Submitted' column in the list of all students.

  Args:
    profile: profile entity.
    prefetched_data: a dict mapping profile keys with prefetched
      student info entities.

  Returns:
    'N/A' if the specified student does not have any projects;
    'No' if the specified student has a project but has yet to submit their
      tax form;
    'Yes' if the specified student has a project and has already submitted
      their tax form;
  """
  student_info = prefetched_data[profile.key()]
  if not profile_logic.hasProject(student_info):
    return 'N/A'
  else:
    return 'Yes' if student_info.getTaxFormKey() else 'No'


def enrollmentFormSubmittedValue(profile, prefetched_data):
  """Returns value for 'Enrollment Form Submitted' column in the
  list of all students.

  Args:
    profile: profile entity.
    prefetched_data: a dict mapping profile keys with prefetched
      student info entities.

  Returns:
    'N/A' if the specified student does not have any projects;
    'No' if the specified student has a project but has yet to submit their
      enrollment form;
    'Yes' if the specified student has a project and has already submitted
      their enrollment form;
  """
  student_info = prefetched_data[profile.key()]
  if not profile_logic.hasProject(student_info):
    return 'N/A'
  else:
    return 'Yes' if student_info.getEnrollmentFormKey() else 'No'


def formsSubmittedValue(profile, prefetched_data):
  """Returns value for 'Forms Submitted' column in the list of all students.

  Args:
    profile: profile entity.
    prefetched_data: a dict mapping profile keys with prefetched
      student info entities.

  Returns:
    'N/A' if the specified student does not have any projects;
    'No' if the specified student has a project but has yet to submit
      at least one of required forms;
    'Yes' if the specified student has a project and has already submitted
      all required forms;
  """
  student_info = prefetched_data[profile.key()]
  if not profile_logic.hasProject(student_info):
    return 'N/A'
  else:
    return 'Yes' if profile_logic.allFormsSubmitted(student_info) else 'No'


class StudentsList(Template):
  """List configuration for listing all the students involved with the program.
  """

  class ListPrefetcher(lists.Prefetcher):
    """Prefetcher used by StudentsList.

    See lists.Prefetcher for specification.
    """

    def prefetch(self, entities):
      """See lists.Prefetcher.prefetch for specification."""
      keys = []

      for entity in entities:
        key = GSoCProfile.student_info.get_value_for_datastore(entity)
        if key:
          keys.append(key)

      student_infos = db.get(keys)
      prefetched_student_info_dict = dict(
          (student_info.parent_key(), student_info)
          for student_info in student_infos if student_info
          )

      orgs = db.get(set(sum(
          (student_info.project_for_orgs for student_info in student_infos),
          [])))
      prefetched_organization_dict = dict(
          (org.key(), org) for org in orgs if org)

      return ([prefetched_student_info_dict, prefetched_organization_dict], {})


  def __init__(self, request, data):
    """Initializes this component."""
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn(
        'name', 'Name', lambda ent, *args: ent.name())
    list_config.addSimpleColumn('link_id', "Username")
    list_config.addSimpleColumn('email', "Email")
    list_config.addSimpleColumn('given_name', "Given name", hidden=True)
    list_config.addSimpleColumn('surname', "Surname", hidden=True)
    list_config.addSimpleColumn('name_on_documents', "Legal name", hidden=True)
    list_config.addSimpleColumn('gender', 'Gender', hidden=True)
    list_config.addSimpleColumn('birth_date', "Birthdate",
                                column_type=lists.BIRTHDATE, hidden=True)
    list_config.setRowAction(
        lambda e, *args: data.redirect.profile(e.link_id).urlOf(
            url_names.GSOC_PROFILE_SHOW_ADMIN, secure=True))

    def formsSubmitted(ent, si):
      info = si[ent.key()]
      tax = GSoCStudentInfo.tax_form.get_value_for_datastore(info)
      enroll = GSoCStudentInfo.enrollment_form.get_value_for_datastore(info)
      return [tax, enroll]

    list_config.addPlainTextColumn(
        'tax_submitted', "Tax form submitted",
        lambda ent, si, *args: taxFormSubmittedValue(ent, si), hidden=True)

    list_config.addPlainTextColumn(
        'enroll_submitted', "Enrollment form submitted",
        lambda ent, si, *args: enrollmentFormSubmittedValue(ent, si),
        hidden=True)

    list_config.addPlainTextColumn(
        'forms_submitted', "Forms submitted",
        lambda ent, si, *args: formsSubmittedValue(ent, si))

    addresses.addAddressColumns(list_config)

    list_config.addPlainTextColumn('school_name', "school_name",
        (lambda ent, si, *args: si[ent.key()].school_name), hidden=True)
    list_config.addPlainTextColumn('school_country', "school_country",
        (lambda ent, si, *args: si[ent.key()].school_country), hidden=True)
    list_config.addPlainTextColumn('school_home_page', "school_home_page",
        (lambda ent, si, *args: si[ent.key()].school_home_page), hidden=True)
    list_config.addPlainTextColumn('school_type', "school_type",
        (lambda ent, si, *args: si[ent.key()].school_type), hidden=True)
    list_config.addPlainTextColumn('major', "major",
        (lambda ent, si, *args: si[ent.key()].major), hidden=True)
    list_config.addPlainTextColumn('degree', "degree",
        (lambda ent, si, *args: si[ent.key()].degree), hidden=True)
    list_config.addPlainTextColumn('expected_graduation', "expected_graduation",
        (lambda ent, si, *args: si[ent.key()].expected_graduation), hidden=True)

    list_config.addNumericalColumn(
        'number_of_proposals', "#proposals",
        lambda ent, si, *args: si[ent.key()].number_of_proposals)
    list_config.addNumericalColumn(
        'number_of_projects', "#projects",
        lambda ent, si, *args: si[ent.key()].number_of_projects)
    list_config.addNumericalColumn(
        'passed_evaluations', "#passed",
        lambda ent, si, *args: si[ent.key()].passed_evaluations)
    list_config.addNumericalColumn(
        'failed_evaluations', "#failed",
        lambda ent, si, *args: si[ent.key()].failed_evaluations)
    list_config.addPlainTextColumn(
        'project_for_orgs', "Organizations",
        lambda ent, si, o, *args: ', '.join(
            [o[i].name for i in si[ent.key()].project_for_orgs]))

    self._list_config = list_config

  def templatePath(self):
    return 'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    if idx != 0:
      return None

    q = GSoCProfile.all()

    q.filter('scope', self.data.program)
    q.filter('is_student', True)

    starter = lists.keyStarter
    prefetcher = StudentsList.ListPrefetcher()

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=prefetcher)

    return response_builder.build()

  def context(self):
    description = ugettext('List of participating students')
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0, description=description)

    return {
        'name': 'students',
        'title': 'Participating students',
        'lists': [list_configuration_response],
    }


class StudentsListPage(base.GSoCRequestHandler):
  """View that lists all the students associated with the program."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/students/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_students_list_admin'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_content = StudentsList(data.request, data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Students list page',
      # TODO(nathaniel): Drop the first parameter of StudentsList.
      'list': StudentsList(data.request, data),
    }


class ProjectsListPage(base.GSoCRequestHandler):
  """View that lists all the projects associated with the program."""

  LIST_IDX = 1

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/all_projects/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_projects_list_admin'),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_query = project_logic.getProjectsQuery(program=data.program)
    list_content = projects_list.ProjectList(
        data, list_query, idx=self.LIST_IDX).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    list_query = project_logic.getProjectsQuery(program=data.program)
    return {
      'page_name': 'Projects list page',
      'list': projects_list.ProjectList(data, list_query, idx=self.LIST_IDX),
    }


class ManageProjectsListPage(base.GSoCRequestHandler):
  """View that lists all the projects associated with the program and
  redirects admin to manage page."""

  LIST_IDX = 1

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/manage_projects/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GSOC_ADMIN_MANAGE_PROJECTS_LIST),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_query = project_logic.getProjectsQuery(program=data.program)
    list_content = projects_list.ProjectList(
        data, list_query, idx=self.LIST_IDX,
        row_action=_getManageProjectRowAction).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    list_query = project_logic.getProjectsQuery(program=data.program)
    return {
      'page_name': 'Projects list page',
      'list': projects_list.ProjectList(data, list_query, idx=self.LIST_IDX,
          row_action=_getManageProjectRowAction),
    }


def _getManageProjectRowAction(data):
  """Returns a row action that redirects to the manage project page.

  Args:
    data: request_data.RequestData object for the current request.

  Returns:
    A function takes a project entity as its first argument and returns
    URL to the manage project page.
  """
  return lambda e, *args: links.SOC_LINKER.userId(
      e.parent_key(), e.key().id(), urls.UrlNames.PROJECT_MANAGE_ADMIN)
