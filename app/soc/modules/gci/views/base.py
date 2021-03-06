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
from melange.request import initialize
from melange.request import links
from melange.request import render
from soc.views import base

from soc.modules.gci.views import base_templates
from soc.modules.gci.views.helper import access_checker
from soc.modules.gci.views.helper import request_data

_GCI_BASE_TEMPLATE = 'modules/gci/base.html'
_GCI_ERROR_TEMPLATE = 'modules/gci/error.html'


class GCIInitializer(initialize.Initializer):
  """An Initializer customized for GCI.

  This Initializer creates GCI-specific subclasses of RequestData,
  AccessChecker, and Mutator.
  """

  def initialize(self, request, args, kwargs):
    """See initialize.Initializer.initialize for specification.

    Args:
      request: An http.HttpRequest object describing the current request.
      args: Additional positional arguments passed with the request.
      kwargs: Additional keyword arguments passed with the request.

    Returns:
      A trio of instances of GCI-specific subclasses of RequestData,
        AccessChecker, and Mutator.
    """
    data = request_data.RequestData(request, args, kwargs)
    mutator = access_checker.Mutator(data)
    if data.is_developer:
      check = access_checker.DeveloperAccessChecker(data)
    else:
      check = access_checker.AccessChecker(data)
    return data, check, mutator

# Since GCIInitializer is stateless, there might as well be just one of it.
_GCI_INITIALIZER = GCIInitializer()


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
        'logged_in_as': base_templates.LoggedInAs(data),
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

  def __init__(self):
    """Initializes a new instance of the request handler for Code In."""
    renderer = GCIRenderer(render.MELANGE_RENDERER)
    super(GCIRequestHandler, self).__init__(
        _GCI_INITIALIZER, links.LINKER, renderer,
        GCIErrorHandler(renderer, error.MELANGE_ERROR_HANDLER))
