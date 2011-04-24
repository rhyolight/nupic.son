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

"""Module containing the view for GSoC project details page.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from django.conf.urls.defaults import url

from soc.views.forms import ModelForm

from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns


class ProjectDetailsForm(ModelForm):
  """Constructs the form to edit the project details
  """

  class Meta:
    model = GSoCProject
    css_prefix = 'gsoc_project'
    fields = ['title', 'abstract', 'public_info',
              'additional_info', 'feed_url']


class ProjectDetailsUpdate(RequestHandler):
  """Encapsulate the methods required to generate Project Details update form.
  """

  def templatePath(self):
    return 'v2/modules/gsoc/project_details/update.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping.
    """

    return [
        url(r'^gsoc/project/update/%s$' % url_patterns.PROJECT, self,
            name='gsoc_update_project')
    ]

  def checkAccess(self):
    """Access checks for GSoC project details page.
    """
    self.check.isLoggedIn()
    self.check.isActiveStudent()
    self.mutator.projectFromKwargs()
    self.check.canStudentUpdateProject()

  def context(self):
    """Handler to for GSoC project details page HTTP get request.
    """
    project_details_form = ProjectDetailsForm(self.data.POST or None,
                                              instance=self.data.project)

    context = {
        'page_name': 'Edit project details',
        'program': self.data.program,
        'project': self.data.project,
        'forms': [project_details_form],
        'error': project_details_form.errors,
    }

    return context

  def validate(self):
    """Validate the form data and save if valid.
    """
    project_details_form = ProjectDetailsForm(self.data.POST or None,
                                              instance=self.data.project)

    if not project_details_form.is_valid():
      return False

    project_details_form.save()
    return True

  def post(self):
    """Post handler for the project details update form.
    """
    if self.validate():
      self.redirect.project()
      self.redirect.to('gsoc_project_details')
    else:
      self.get()


class ProjectDetails(RequestHandler):
  """Encapsulate all the methods required to generate GSoC project
  details page.
  """

  def templatePath(self):
    return 'v2/modules/gsoc/project_details/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping.
    """

    return [
        url(r'^gsoc/project/%s$' % url_patterns.PROJECT, self,
            name='gsoc_project_details')
    ]

  def checkAccess(self):
    """Access checks for GSoC project details page.
    """
    self.mutator.projectFromKwargs()

  def context(self):
    """Handler to for GSoC project details page HTTP get request.
    """
    context = {
        'page_name': 'Project details',
        'program': self.data.program,
        'project': self.data.project,
    }

    r = self.redirect.project()

    user_is_owner = self.data.user and \
        (self.data.user.key() == self.data.project_owner.parent_key())
    if user_is_owner:
      context['update_link'] = r.urlOf('gsoc_edit_project')

    return context
