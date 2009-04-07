#!/usr/bin/python2.5
#
# Copyright 2009 the Melange authors.
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

"""Views for Student Project.
"""

__authors__ = [
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import time

from django import forms

from soc.logic import cleaning
from soc.logic import dicts
from soc.logic.models import mentor as mentor_logic
from soc.logic.models.organization import logic as org_logic
from soc.logic.models.org_admin import logic as org_admin_logic
from soc.logic.models import student as student_logic
from soc.logic.models.student_project import logic as project_logic
from soc.views import out_of_band
from soc.views.helper import access
from soc.views.helper import decorators
from soc.views.helper import dynaform
from soc.views.helper import forms as forms_helper
from soc.views.helper import lists
from soc.views.helper import params as params_helper
from soc.views.helper import redirects
from soc.views.helper import responses
from soc.views.models import base
from soc.views.models import organization as org_view

import soc.logic.models.student_project


class View(base.View):
  """View methods for the Student Project model.
  """

  def __init__(self, params=None):
    """Defines the fields and methods required for the base View class
    to provide the user with list, public, create, edit and delete views.

    Params:
      params: a dict with params for this View
    """

    rights = access.Checker(params)
    rights['create'] = ['checkIsDeveloper']
    rights['edit'] = ['checkIsDeveloper']
    rights['delete'] = ['checkIsDeveloper']
    rights['show'] = ['allow']
    rights['list'] = ['checkIsDeveloper']
    rights['manage'] = [('checkHasActiveRoleForScope',
                         org_admin_logic),
        ('checkStudentProjectHasStatus', ['accepted', 'mid_term_passed'])]
    rights['manage_overview'] = [('checkHasActiveRoleForScope',
                         org_admin_logic)]
    # TODO lack of better name here!
    rights['st_edit'] = ['checkIsMyStudentProject',
        ('checkStudentProjectHasStatus', 
            ['accepted', 'mid_term_passed', 'passed'])
        ]

    new_params = {}
    new_params['logic'] = soc.logic.models.student_project.logic
    new_params['rights'] = rights
    new_params['name'] = "Student Project"
    new_params['url_name'] = "student_project"
    new_params['sidebar_grouping'] = 'Students'

    new_params['scope_view'] = org_view
    new_params['scope_redirect'] = redirects.getCreateRedirect

    new_params['no_create_with_key_fields'] = True

    new_params['extra_dynaexclude'] = ['program', 'status', 'link_id',
                                       'mentor', 'student']

    new_params['create_extra_dynaproperties'] = {
        'scope_path': forms.CharField(widget=forms.HiddenInput,
            required=True),
        'student_id': forms.CharField(label='Student Link ID',
            required=True),
        'mentor_id': forms.CharField(label='Mentor Link ID',
            required=True),
        'clean_abstract': cleaning.clean_content_length('abstract'),
        'clean_student': cleaning.clean_link_id('student'),
        'clean_mentor': cleaning.clean_link_id('mentor'),
        'clean_additional_info': cleaning.clean_url('additional_info'),
        'clean_feed_url': cleaning.clean_feed_url,
        'clean': cleaning.validate_student_project('scope_path',
            'mentor_id', 'student_id')
        }

    new_params['edit_extra_dynaproperties'] = {
        'link_id': forms.CharField(widget=forms.HiddenInput),
        }

    patterns = [
        (r'^%(url_name)s/(?P<access_type>manage_overview)/%(scope)s$',
        'soc.views.models.%(module_name)s.manage_overview',
        'Overview of %(name_plural)s to Manage for'),
        (r'^%(url_name)s/(?P<access_type>manage)/%(key_fields)s$',
        'soc.views.models.%(module_name)s.manage',
        'Manage %(name)s'),
        (r'^%(url_name)s/(?P<access_type>st_edit)/%(key_fields)s$',
        'soc.views.models.%(module_name)s.st_edit',
        'Edit my %(name)s'),
    ]

    new_params['extra_django_patterns'] = patterns

    new_params['edit_template'] = 'soc/student_project/edit.html'

    # TODO(ljvderijk) list all projects for one student
    # TODO(ljvderijk) add manage item to org menu for admins

    params = dicts.merge(params, new_params)

    super(View, self).__init__(params=params)

    # create the form that students will use to edit their projects
    dynaproperties = {
        'clean_abstract': cleaning.clean_content_length('abstract'),
        'clean_additional_info': cleaning.clean_url('additional_info'),
        'clean_feed_url': cleaning.clean_feed_url,
        }

    student_edit_form = dynaform.newDynaForm(
        dynabase = params['dynabase'],
        dynamodel = params['logic'].getModel(),
        dynaexclude = params['create_dynaexclude'],
        dynaproperties = dynaproperties,
    )

    params['student_edit_form'] = student_edit_form


  def _editGet(self, request, entity, form):
    """See base.View._editGet().
    """

    form.fields['link_id'].initial = entity.link_id
    form.fields['student_id'].initial = entity.student.link_id
    form.fields['mentor_id'].initial = entity.mentor.link_id

    return super(View, self)._editGet(request, entity, form)

  def _editPost(self, request, entity, fields):
    """See base.View._editPost().
    """

    if not entity:
      fields['link_id'] = 't%i' % (int(time.time()*100))
    else:
      fields['link_id'] = entity.link_id

    # fill in the scope via call to super
    super(View, self)._editPost(request, entity, fields)

    # editing a project so set the program, student and mentor field
    if entity:
      organization = entity.scope
    else:
      organization = fields['scope']

    fields['program'] = organization.scope

    filter = {'scope': fields['program'],
              'link_id': fields['student_id']}
    fields['student'] = student_logic.logic.getForFields(filter, unique=True)

    filter = {'scope': organization,
              'link_id': fields['mentor_id'],
              'status': 'active'}
    fields['mentor'] = mentor_logic.logic.getForFields(filter, unique=True)

  @decorators.merge_params
  @decorators.check_access
  def manage(self, request, access_type,
             page_name=None, params=None, **kwargs):
    """View that allows Organization Admins to manage their Student Projects.

    For params see base.View().public()
    """

    try:
      entity = self._logic.getFromKeyFieldsOr404(kwargs)
    except out_of_band.Error, error:
      return responses.errorResponse(
          error, request, template=params['error_public'])

    # get the context for this webpage
    context = responses.getUniversalContext(request)
    responses.useJavaScript(context, params['js_uses_all'])
    context['page_name'] = "%s '%s' from %s" % (page_name, entity.title,
                                                entity.student.name())

    # use another template and make the cancel button goes to the public view
    params['edit_template'] = 'soc/student_project/manage.html'
    params['edit_cancel_redirect'] = redirects.getManageOverviewRedirect(
        entity.scope, params)

    # get all mentors for this organization
    fields = {'scope': entity.scope,
              'status': 'active'}
    mentors = mentor_logic.logic.getForFields(fields)

    choices = [(mentor.link_id,'%s (%s)' %(mentor.name(), mentor.link_id))
                  for mentor in mentors]

    # create the form that org admins will use to reassign a mentor
    dynafields = [
        {'name': 'mentor_id',
         'base': forms.ChoiceField,
         'label': 'Mentor',
         'required': True,
         'passthrough': ['required', 'choices', 'label'],
         'choices': choices,
        },]

    dynaproperties = params_helper.getDynaFields(dynafields)

    mentor_edit_form = dynaform.newDynaForm(
        dynabase = params['dynabase'],
        dynaproperties = dynaproperties,
    )

    params['mentor_edit_form'] = mentor_edit_form

    if request.POST:
      return self.managePost(request, context, params, entity, **kwargs)
    else: #request.GET
      return self.manageGet(request, context, params, entity, **kwargs)

  def manageGet(self, request, context, params, entity, **kwargs):
    """Handles the GET request for the project's manage page.

    Args:
        entity: the student project entity
        rest: see base.View.public()
    """

    # populate form with the current mentor
    initial = {'mentor_id': entity.mentor.link_id}
    form = params['mentor_edit_form'](initial=initial)

    return self._constructResponse(request, entity, context, form, params)

  def managePost(self, request, context, params, entity, **kwargs):
    """Handles the POST request for the project's manage page.

    Args:
        entity: the student project entity
        rest: see base.View.public()
    """

    form = params['mentor_edit_form'](request.POST)

    if not form.is_valid():
      return self._constructResponse(request, entity, context, form, params)

    _, fields = forms_helper.collectCleanedFields(form)

    # get the mentor from the form
    fields = {'link_id': fields['mentor_id'],
              'scope': entity.scope,
              'status': 'active'}
    mentor = mentor_logic.logic.getForFields(fields, unique=True)

    # update the project with the assigned mentor
    fields = {'mentor': mentor}
    project_logic.updateEntityProperties(entity, fields)

    return self.manageGet(request, context, params, entity)

  @decorators.merge_params
  @decorators.check_access
  def manageOverview(self, request, access_type,
             page_name=None, params=None, **kwargs):
    """View that allows Organization Admins to see an overview of 
       their Organization's Student Projects.

    For params see base.View().public()
    """

    # make sure the organization exists
    org_entity = org_logic.getFromKeyNameOr404(kwargs['scope_path'])
    fields = {'scope': org_entity}

    # get the context for this webpage
    context = responses.getUniversalContext(request)
    responses.useJavaScript(context, params['js_uses_all'])
    context['page_name'] = '%s %s' % (page_name, org_entity.name)

    list_params = params.copy()

    #list all active projects
    fields['status'] = ['accepted', 'mid_term_passed']
    active_params = list_params.copy()
    active_params['list_description'] = \
        'List of all active %(name_plural)s' % list_params
    active_params['list_action'] = (redirects.getManageRedirect, list_params)

    active_list = lists.getListContent(
        request, active_params, fields, idx=0)

    # list all failed projects
    fields['status'] = ['mid_term_failed', 'final_failed']
    failed_params = list_params.copy()
    failed_params['list_description'] = ('List of all failed %(name_plural)s, '
        'these cannot be managed.') % list_params
    failed_params['list_action'] = (redirects.getPublicRedirect, list_params)

    failed_list = lists.getListContent(
        request, failed_params, fields, idx=1, need_content=True)

    #list all completed projects
    fields['status'] = ['passed']
    completed_params = list_params.copy()
    completed_params['list_description'] = ('List of %(name_plural)s that have '
        'successfully completed the program, '
        'these cannot be managed.' % list_params)
    completed_params['list_action'] = (redirects.getPublicRedirect, list_params)

    completed_list = lists.getListContent(
        request, completed_params, fields, idx=2, need_content=True)

    # always show the list with active projects
    content = [active_list]

    if failed_list != None:
      # do not show empty failed list
      content.append(failed_list)

    if completed_list != None:
      # do not show empty completed list
      content.append(completed_list)

    # call the _list method from base to display the list
    return self._list(request, list_params, content,
                      context['page_name'], context)

  @decorators.merge_params
  @decorators.check_access
  def stEdit(self, request, access_type,
             page_name=None, params=None, **kwargs):
    """View that allows students to edit information about their project.

    For params see base.View().public()
    """

    try:
      entity = self._logic.getFromKeyFieldsOr404(kwargs)
    except out_of_band.Error, error:
      return responses.errorResponse(
          error, request, template=params['error_public'])

    # get the context for this webpage
    context = responses.getUniversalContext(request)
    responses.useJavaScript(context, params['js_uses_all'])
    context['page_name'] = page_name
    # cancel should go to the public view
    params['edit_cancel_redirect'] = redirects.getPublicRedirect(entity, params)

    if request.POST:
      return self.stEditPost(request, context, params, entity, **kwargs)
    else: #request.GET
      return self.stEditGet(request, context, params, entity, **kwargs)

  def stEditGet(self, request, context, params, entity, **kwargs):
    """Handles the GET request for the student's edit page.

    Args:
        entity: the student project entity
        rest: see base.View.public()
    """

    # populate form with the existing entity
    form = params['student_edit_form'](instance=entity)

    return self._constructResponse(request, entity, context, form, params)

  def stEditPost(self, request, context, params, entity, **kwargs):
    """Handles the POST request for the student's edit page.

    Args:
        entity: the student project entity
        rest: see base.View.public()
    """

    form = params['student_edit_form'](request.POST)

    if not form.is_valid():
      return self._constructResponse(request, entity, context, form, params)

    _, fields = forms_helper.collectCleanedFields(form)

    project_logic.updateEntityProperties(entity, fields)

    return self.stEditGet(request, context, params, entity, **kwargs)


view = View()

admin = decorators.view(view.admin)
create = decorators.view(view.create)
delete = decorators.view(view.delete)
edit = decorators.view(view.edit)
list = decorators.view(view.list)
manage = decorators.view(view.manage)
manage_overview = decorators.view(view.manageOverview)
public = decorators.view(view.public)
st_edit = decorators.view(view.stEdit)
export = decorators.view(view.export)
pick = decorators.view(view.pick)
