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

"""Module containing the boilerplate required to construct GSoC views."""

import httplib

from django import http

from soc.views import base

from soc.modules.gsoc.views import base_templates
from soc.modules.gsoc.views.helper import access_checker
from soc.modules.gsoc.views.helper import request_data


class GSoCRequestHandler(base.RequestHandler):
  """Customization required by GSoC to handle HTTP requests."""

  def render(self, data, template_path, context):
    """Renders the page using the specified context.

    See soc.views.base.RequestHandler for specification.

    The context object is extended with the following values:
      base_layout: path to the base template.
      header: a rendered header.Header template for the passed data.
      mainmenu: a rendered site_menu.MainMenu template for the passed data.
      footer: a rendered site_menu.Footer template for the passed data.
    """
    context['base_layout'] = 'v2/modules/gsoc/base.html'
    context['header'] = base_templates.Header(data)
    context['mainmenu'] = base_templates.MainMenu(data)
    context['footer'] = base_templates.Footer(data)
    return super(GSoCRequestHandler, self).render(data, template_path, context)

  def init(self, request, args, kwargs):
    """See base.RequestHandler.init for specification."""
    data = request_data.RequestData(request, args, kwargs)
    if data.is_developer:
      mutator = access_checker.DeveloperMutator(data)
      check = access_checker.DeveloperAccessChecker(data)
    else:
      mutator = access_checker.Mutator(data)
      check = access_checker.AccessChecker(data)
    return data, check, mutator

  def error(self, data, status, message=None):
    """See base.RequestHandler.error for specification."""
    if not data.program:
      return super(GSoCRequestHandler, self).error(
          data, status, message=message)

    # If message is not set, set it to the default associated with the
    # given status (such as "Method Not Allowed" or "Service Unavailable").
    message = message or httplib.responses.get(status, '')

    template_path = 'v2/modules/gsoc/error.html'
    context = {
        'page_name': message,
        'message': message,
        'logged_in_msg': base_templates.LoggedInMsg(data, apply_link=False),
    }

    return http.HttpResponse(
        content=self.render(data, template_path, context), status=status)
