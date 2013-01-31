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

"""Module containing the boilerplate required to construct GCI views."""

import httplib

from django import http

from soc.views import base

from soc.modules.gci.views import base_templates
from soc.modules.gci.views.helper import access_checker
from soc.modules.gci.views.helper import request_data


class GCIRequestHandler(base.RequestHandler):
  """Customization required by GCI to handle HTTP requests."""

  def render(self, template_path, context):
    """Renders the page using the specified context.

    See soc.views.base.RequestHandler for specification.

    The context object is extended with the following values:
      base_layout: path to the base template.
      header: a rendered header.Header template for the current self.data
      mainmenu: a rendered site_menu.MainMenu template for the current self.data
      footer: a rendered site_menu.Footer template for the current self.data
    """
    context['base_layout'] = 'v2/modules/gci/base.html'
    if self.data.user:
      context['status'] = base_templates.Status(self.data)
    context['header'] = base_templates.Header(self.data)
    context['mainmenu'] = base_templates.MainMenu(self.data)
    context['footer'] = base_templates.Footer(self.data)
    return super(GCIRequestHandler, self).render(template_path, context)

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

  def error(self, status, message=None):
    """See base.RequestHandler.error for specification."""
    if not self.data.program:
      return super(GCIRequestHandler, self).error(status, message)

    # If message is not set, set it to the default associated with the
    # given status (such as "Method Not Allowed" or "Service Unavailable").
    message = message or httplib.responses.get(status, '')

    template_path = 'v2/modules/gci/error.html'
    context = {
        'page_name': message,
        'message': message,
    }

    return http.HttpResponse(
        content=self.render(template_path, context), status=status)
