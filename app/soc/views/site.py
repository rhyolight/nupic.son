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

"""Module for the site global pages."""

import httplib
import os

from google.appengine.api import users

from django import http
from django.conf.urls.defaults import url as django_url
from django.forms import widgets as django_widgets
from django.utils.translation import ugettext

from melange.request import exception
from soc.logic import cleaning
from soc.logic import site as site_logic
from soc.models import document
from soc.models import site
from soc.views import base
from soc.views import forms as views_forms

DEF_NO_DEVELOPER = ugettext(
    'This page is only accessible to developers.')


def getProgramMap():
  # TODO(nathaniel): Magic string? This isn't a program.
  choices = [('', '-----')]

  # TODO(nathaniel): Eliminate the circularity behind this non-top-level
  # import.
  from soc.modules import callback
  choices += callback.getCore().getProgramMap()
  return choices


class SiteForm(views_forms.ModelForm):
  """Django form for the site settings."""

  class Meta:
    model = site.Site
    exclude = ['xsrf_secret_key']
    # NOTE(nathaniel): There aren't really no choices, it's just that we
    # can't know what the choices are at module-load-time. For the moment
    # we have to set the available choices below in EditSitePage.context.
    widgets = {'active_program': django_widgets.Select(choices=[])}

  def clean_tos(self):
    return '' if self.cleaned_data['tos'] is None else self.cleaned_data['tos']

  def templatePath(self):
    return 'modules/gsoc/_form.html'

  clean_noreply_email = cleaning.clean_empty_field('noreply_email')


class EditSitePage(base.RequestHandler):
  """View for the participant profile."""

  def djangoURLPatterns(self):
    return [
        django_url(r'^site/edit$', self, name='edit_site_settings'),
    ]

  def jsonContext(self, data, check, mutator):
    entities = document.Document.all().filter('prefix', 'site')

    json_data = [{'key': str(i.key()),
                  'link_id': i.link_id,
                  'label': i.title}
                 for i in entities]

    return {'data': json_data}

  def checkAccess(self, data, check, mutator):
    if not data.is_developer:
      raise exception.Forbidden(message=DEF_NO_DEVELOPER)

  def templatePath(self):
    # TODO: make this specific to the current active program
    return 'soc/site/base.html'

  def context(self, data, check, mutator):
    # TODO: suboptimal
    from soc.modules.gsoc.views.forms import GSoCBoundField
    site_form = SiteForm(GSoCBoundField, data.POST or None, instance=data.site)

    # NOTE(nathaniel): This is an unfortunate workaround for the fact
    # that in its current form the SiteForm class will only ever present
    # to the user those choices that were discoverable at module-load time.
    site_form.fields['active_program'].widget = django_widgets.Select(
        choices=getProgramMap())

    return {
        'app_version': os.environ.get('CURRENT_VERSION_ID', '').split('.')[0],
        'page_name': 'Edit site settings',
        'site_form': site_form,
    }

  def validate(self, data):
    from soc.modules.gsoc.views.forms import GSoCBoundField
    site_form = SiteForm(GSoCBoundField, data.POST, instance=data.site)

    if site_form.is_valid():
      site_form.save()
      return True
    else:
      return False

  def post(self, data, check, mutator):
    """Handler for HTTP POST request."""
    post_accepted = self.validate(data)
    context = self.context(data, check, mutator)
    template_path = self.templatePath()
    response_content = self.renderer.render(data, template_path, context)
    return http.HttpResponse(
        status=httplib.OK if post_accepted else httplib.BAD_REQUEST,
        content=response_content)


class SiteHomepage(base.RequestHandler):
  """View for the site home page."""

  def djangoURLPatterns(self):
    return [
        django_url(r'^$', self, name='site_home'),
        django_url(r'^(login)$', self, name='login'),
        django_url(r'^(logout)$', self, name='logout'),
    ]

  def __call__(self, request, *args, **kwargs):
    """Custom call implementation that avoids looking up unneeded data."""
    try:
      data, _, _ = self.initializer.initialize(request, args, kwargs)

      self.checkMaintenanceMode(data)

      action = args[0] if args else ''

      if action == 'login':
        return data.redirect.toUrl(users.create_login_url('/'))
      elif action == 'logout':
        return data.redirect.toUrl(users.create_logout_url('/'))
      else:
        settings = site_logic.singleton()
        program = settings.active_program
        if program:
          program_url = self.linker.program(program, program.homepage_url_name)
          return http.HttpResponseRedirect(program_url)
        else:
          return data.redirect.to('edit_site_settings')
    except exception.UserError as user_error:
      return self.error_handler.handleUserError(user_error, data)
    except exception.ServerError as server_error:
      return self.error_handler.handleServerError(server_error, data)
