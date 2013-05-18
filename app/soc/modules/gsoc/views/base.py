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

from melange.request import render
from soc.views import base

from soc.modules.gsoc.views import base_templates
from soc.modules.gsoc.views.helper import access_checker
from soc.modules.gsoc.views.helper import request_data

_BASE_TEMPLATE = 'v2/modules/gsoc/base.html'


class GSoCRenderer(render.Renderer):
  """A Renderer customized for GSoC."""

  def __init__(self, delegate):
    """Constructs a GSoCRenderer.

    Args:
      delegate: A Renderer to which this Renderer may delegate
        some portion of its functionality.
    """
    self._delegate = delegate

  def render(self, data, template_path, context):
    """See render.Renderer.render for specification.

    The template is rendered against the given context content augmented
    by the following items:
      base_layout: The path to the base template.
      header: A rendered header.Header template for the passed data.
      mainmenu: A rendered site_menu.MainMenu template for the passed data.
      footer: A rendered site_menu.Footer template for the passed data.
    """
    augmented_context = dict(context)
    augmented_context.update({
        'base_layout': _BASE_TEMPLATE,
        'header': base_templates.Header(data),
        'mainmenu': base_templates.MainMenu(data),
        'footer': base_templates.Footer(data),
    })
    return self._delegate.render(data, template_path, augmented_context)


class GSoCRequestHandler(base.RequestHandler):
  """Customization required by GSoC to handle HTTP requests."""

  renderer = GSoCRenderer(render.MELANGE_RENDERER)

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
        content=self.renderer.render(data, template_path, context),
        status=status)
