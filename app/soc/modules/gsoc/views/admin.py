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
from google.appengine.ext import db
from google.appengine.ext import ndb

from django import forms as djangoforms
from django import http
from django.utils.translation import ugettext

from melange.models import profile as profile_model
from melange.models import user as user_model
from melange.request import access
from melange.request import exception

from soc.logic import cleaning
from soc.views.dashboard import Dashboard
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic.proposal import getProposalsToBeAcceptedForOrg
from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
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

  user_id = djangoforms.CharField(label='Username')

  def clean_user_id(self):
    user_id_cleaner = cleaning.clean_link_id('user_id')

    try:
      user_id = user_id_cleaner(self)
    except djangoforms.ValidationError as e:
      if e.code != 'invalid':
        raise
      msg = ugettext(u'Enter a valid username.')
      raise djangoforms.ValidationError(msg, code='invalid')

    user = user_model.User.get_by_id(user_id)
    if not user:
      raise djangoforms.ValidationError(
          'There is no user with that email address')

    self.cleaned_data['user'] = user

    query = profile_model.Profile.query(
        profile_model.Profile.program == ndb.Key.from_old_key(
            self.request_data.program.key()),
        ancestor=user.key)
    self.cleaned_data['profile'] = query.get()


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
    dashboards.append(ParticipantsDashboard(data))

    dashboards.append(ShipmentTrackingDashboard(data))
    dashboards.append(ShipmentInfoDashboard(data))

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
    shipment_tracking = ShipmentTrackingDashboard(self.data)

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
        {
            'name': 'shipment_tracking',
            'description': ugettext(
                'Shipment tracking for students'),
            'title': 'Tracking Information',
            'link': '',
            'subpage_links': shipment_tracking.getSubpagesLink(),
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
                'List of organization application that have been '
                'submitted to the program'),
            'title': 'Submitted organization applications',
            'link': links.SOC_LINKER.program(
                data.program, urls.UrlNames.ORG_APPLICATION_LIST)
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


class ShipmentTrackingDashboard(Dashboard):
  """Dashboard for shipment tracking.
  """

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    shipment_info = ShipmentInfoDashboard(data)

    subpages = [
        {
            'name': 'shipment_infos',
            'description': ugettext('Manage Shipment Information'),
            'title': 'Shipment Information',
            'link': '',
            'subpage_links': shipment_info.getSubpagesLink(),
        },
        {
            'name': 'sync_data',
            'description': ugettext('Sync Data'),
            'title': 'Sync Data',
            'link': links.SOC_LINKER.program(
                data.program, url_names.GSOC_SHIPMENT_LIST),
        },
    ]

    super(ShipmentTrackingDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of shipment tracking dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Shipment Tracking Information',
        'name': 'shipment_tracking',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
        ],
        'subpages': subpages
    }


class ShipmentInfoDashboard(Dashboard):
  """Dashboard for shipment infos.
  """

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      request: The HTTPRequest object
      data: The RequestData object
    """
    subpages = [
        {
            'name': 'create_shipment_info',
            'description': ugettext('Create shipment information'),
            'title': 'Create',
            'link': links.SOC_LINKER.program(data.program, url_names.GSOC_CREATE_SHIPMENT_INFO),
        },
        {
            'name': 'edit_shipment_infos',
            'description': ugettext('Edit shipment informations'),
            'title': 'Edit',
            'link': links.SOC_LINKER.program(data.program, url_names.GSOC_SHIPMENT_INFO_RECORDS),
        },
    ]

    super(ShipmentInfoDashboard, self).__init__(data, subpages)

  def context(self):
    """Returns the context of shipment infos dashboard.
    """
    subpages = self._divideSubPages(self.subpages)

    return {
        'title': 'Shipment Information',
        'name': 'shipment_infos',
        'backlinks': [
            {
                'to': 'main',
                'title': 'Admin dashboard'
            },
            {
                'to': 'shipment_tracking',
                'title': 'Shipment Tracking Information'
            }
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
      raise exception.Redirect(
          links.SOC_LINKER.profile(profile, urls.UrlNames.PROFILE_ADMIN))
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

  def __init__(self, data):
    """Initializes this proposals list."""
    self.data = data

    def getStudentEmail(entity, *args):
      """Helper function to get a value for Student Email column."""
      profile = ndb.Key.from_old_key(entity.parent_key()).get()
      return profile.contact.email

    def getStudent(entity, *args):
      """Helper function to get a value for Student column."""
      profile = ndb.Key.from_old_key(entity.parent_key()).get()
      return profile.public_name

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn(
        'email', 'Student Email', getStudentEmail, hidden=True)
    list_config.addSimpleColumn('score', 'Score')
    list_config.addSimpleColumn('nr_scores', '#scores', hidden=True)

    def getAverage(ent):
      if not ent.nr_scores:
        return float(0)

      average = float(ent.score) / float(ent.nr_scores)
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

    def getOrganizationKey(entity, *args):
      """Helper function to get value of organization key column."""
      org_key = GSoCProposal.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).id()

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
    list_config.addPlainTextColumn('student', 'Student', getStudent)
    list_config.addSimpleColumn('accept_as_project', 'Should accept')

    # hidden keys
    list_config.addPlainTextColumn(
        'full_proposal_key', 'Full proposal key',
        (lambda ent, *args: str(ent.key())), hidden=True)
    list_config.addPlainTextColumn(
        'org_key', 'Organization key', getOrganizationKey, hidden=True)

    list_config.setDefaultSort('last_modified_on', 'desc')

    self._list_config = list_config

  def templatePath(self):
    return'modules/gsoc/admin/_proposals_list.html'

  def context(self):
    description = (
        'List of proposals submitted into %s' % self.data.url_ndb_org.name)

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

    program = self.data.program

    # Hold all the accepted projects for orgs where this user is a member of
    accepted = []
    # Hold all duplicates for either the entire program or the orgs of the user.
    duplicates = []
    dupQ = GSoCProposalDuplicate.all()
    dupQ.filter('is_duplicate', True)
    dupQ.filter('org', self.data.url_ndb_org.key.to_old_key())
    dupQ.filter('program', program)

    accepted.extend(
        p.key() for p in getProposalsToBeAcceptedForOrg(self.data.url_ndb_org))

    duplicate_entities = dupQ.fetch(1000)
    for dup in duplicate_entities:
      duplicates.extend(dup.duplicates)

    q = GSoCProposal.all()
    q.filter('org', self.data.url_ndb_org.key.to_old_key())
    q.filter('program', program)

    starter = lists.keyStarter

    # TODO(daniel): enable prefetching from ndb models ('org', 'parent')
    # prefetcher = lists.ModelPrefetcher(GSoCProposal, [], parent=True)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter, prefetcher=None)
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
    list_content = ProposalsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    """Handler for POST requests."""
    proposals_list = ProposalsList(data)
    if proposals_list.post():
      return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    return {
        'page_name': 'Proposal page',
        'list': ProposalsList(data),
    }


class ProjectsList(Template):
  """Template for listing all projects of particular org."""

  def __init__(self, request, data):

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = GSoCProject.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('student', 'Student',
        lambda entity, *args: entity.parent().name())
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)
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
            self.data.url_ndb_org.name, self.data.program.name))

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
