#!/usr/bin/python2.5
#
# Copyright 2008 the Melange authors.
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

"""Views for Programs.
"""

__authors__ = [
    '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from google.appengine.api import users

from django import forms
from django.utils.translation import ugettext_lazy

from soc.logic import dicts
from soc.logic import cleaning
from soc.logic.models import sponsor as sponsor_logic
from soc.views.helper import redirects
from soc.views.models import base
from soc.views.models import sponsor as sponsor_view
from soc.views import helper

import soc.logic.models.program


class View(base.View):
  """View methods for the Sponsor model.
  """

  def __init__(self, params=None):
    """Defines the fields and methods required for the base View class
    to provide the user with list, public, create, edit and delete views.

    Params:
      params: a dict with params for this View
    """    

    new_params = {}
    new_params['logic'] = soc.logic.models.program.logic

    new_params['name'] = "Program"
    new_params['name_short'] = "Program"
    new_params['name_plural'] = "Programs"
    new_params['url_name'] = "program"
    new_params['module_name'] = "program"

    new_params['extra_dynaexclude'] = ['home']
    new_params['create_extra_dynafields'] = {
        'description': forms.fields.CharField(widget=helper.widgets.TinyMCE(
                  attrs={'rows':10, 'cols':40})),
        'scope_path': forms.CharField(widget=forms.HiddenInput,
                                   required=False),
        'clean_link_id': cleaning.clean_link_id,
        }

    params = dicts.merge(params, new_params)

    super(View, self).__init__(params=params)

  def create(self, request, **kwargs):
    """Specialized create view to enforce needing a scope_path

    This view simply gives control to the base.View.create if the
    scope_path is specified in kwargs. If it is not present, it
    instead displays the result of self.select. Refer to the
    respective docstrings on what they do.

    Args: 
      see base.View.create
    """

    if 'scope_path' in kwargs:
      return super(View, self).create(request, **kwargs)

    view = sponsor_view.view
    redirect = redirects.getCreateRedirect
    return self.select(request, view, redirect, **kwargs)

  def _editGet(self, request, entity, form):
    """See base.View._editGet().
    """

    # fill in the email field with the data from the entity
    form.fields['scope_path'].initial = entity.scope_path

  def _editPost(self, request, entity, fields):
    """See base.View._editPost().
    """

    sponsor = sponsor_logic.logic.getFromFields(link_id=fields['scope_path'])
    fields['scope'] = sponsor


  def getDjangoURLPatterns(self, params=None):
    """See base.View.getDjangoURLPatterns().
    """

    default_patterns = self._params['django_patterns_defaults']
    default_patterns += [
        (r'^%(url_name)s/create/(?P<scope_path>%(ulnp)s)$',
            'soc.views.models.%s.create', 'Create %(name_short)s')]

    params = {}
    params['django_patterns_defaults'] = default_patterns

    params = dicts.merge(params, self._params)
    patterns = super(View, self).getDjangoURLPatterns(params)

    return patterns


view = View()

create = view.create
delete = view.delete
edit = view.edit
list = view.list
public = view.public
