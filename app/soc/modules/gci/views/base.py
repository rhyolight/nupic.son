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

from melange.request import error
from melange.request import render
from soc.views import base

from soc.modules.gci.views import base_templates
from soc.modules.gci.views.helper import access_checker
from soc.modules.gci.views.helper import request_data

_GCI_BASE_TEMPLATE = 'v2/modules/gci/base.html'
_GCI_ERROR_TEMPLATE = 'v2/modules/gci/error.html'


class GCIRenderer(render.Renderer):
  """A Renderer customized for GCI."""

  def __init__(self, delegate):
    """Constructs a GCIRenderer.

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
        'base_layout': _GCI_BASE_TEMPLATE,
        'header': base_templates.Header(data),
        'mainmenu': base_templates.MainMenu(data),
        'footer': base_templates.Footer(data),
    })
    if data.user:
      context['status'] = base_templates.Status(data)
    return self._delegate.render(data, template_path, augmented_context)


class GCIErrorHandler(error.ErrorHandler):
  """A GCI implementation of error.ErrorHandler."""

  def __init__(self, renderer, delegate):
    """Constructs a GCIErrorHandler.

    Args:
      renderer: A render.Renderer to be used to render
        response content.
      delegate: An error.ErrorHandler to be used to handle
        errors that this GCIErrorHandler does not wish or
        is not able to handle.
    """
    self._renderer = renderer
    self._delegate = delegate

  def handleUserError(self, user_error, data):
    """See error.ErrorHandler.handleUserError for specification."""
    if not data.program:
      return self._delegate.handleUserError(user_error, data)

    # If message is not set, set it to the default associated with the
    # given status (such as "Method Not Allowed" or "Forbidden").
    message = user_error.message if user_error.message else (
        httplib.responses.get(user_error.status, ''))

    context = {
        'page_name': message,
        'message': message,
    }

    return http.HttpResponse(
        content=self._renderer.render(data, _GCI_ERROR_TEMPLATE, context),
        status=user_error.status)

  def handleServerError(self, server_error, data):
    """See error.ErrorHandler.handleServerError for specification."""
    return self._delegate.handleServerError(server_error, data)


class GCIRequestHandler(base.RequestHandler):
  """Customization required by GCI to handle HTTP requests."""

  renderer = GCIRenderer(render.MELANGE_RENDERER)
  error_handler = GCIErrorHandler(renderer, error.MELANGE_ERROR_HANDLER)

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
      return super(GCIRequestHandler, self).error(
          data, status, message=message)

    # If message is not set, set it to the default associated with the
    # given status (such as "Method Not Allowed" or "Service Unavailable").
    message = message or httplib.responses.get(status, '')

    template_path = 'v2/modules/gci/error.html'
    context = {
        'page_name': message,
        'message': message,
    }

    return http.HttpResponse(
        content=self.renderer.render(data, template_path, context),
        status=status)
