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

from melange.request import error
from melange.request import initialize

from soc.views import base
from soc.modules.gsoc.views.helper import access_checker
from soc.modules.gsoc.views.helper import request_data

from summerofcode.request import links
from summerofcode.request import render


_GSOC_ERROR_TEMPLATE = 'modules/gsoc/error.html'

class GSoCInitializer(initialize.Initializer):
  """An Initializer customized for GSoC.

  This Initializer creates GSoC-specific subclasses of RequestData,
  AccessChecker, and Mutator.
  """

  def initialize(self, request, args, kwargs):
    """See initialize.Initializer.initialize for specification.

    Args:
      request: An http.HttpRequest object describing the current request.
      args: Additional positional arguments passed with the request.
      kwargs: Additional keyword arguments passed with the request.

    Returns:
      A trio of instances of GSoC-specific subclasses of RequestData,
        AccessChecker, and Mutator.
    """
    data = request_data.RequestData(request, args, kwargs)
    mutator = access_checker.Mutator(data)
    if data.is_developer:
      check = access_checker.DeveloperAccessChecker(data)
    else:
      check = access_checker.AccessChecker(data)
    return data, check, mutator

# Since GSoCInitializer is stateless, there might as well be just one of it.
_GSOC_INITIALIZER = GSoCInitializer()


class GSoCErrorHandler(error.ErrorHandler):
  """A GSoC implementation of error.ErrorHandler."""

  def __init__(self, renderer, delegate):
    """Constructs a GSoCErrorHandler.

    Args:
      renderer: A render.Renderer to be used to render
        response content.
      delegate: An error.ErrorHandler to be used to handle
        errors that this GSoCErrorHandler does not wish or
        is not able to handle.
    """
    self._renderer = renderer
    self._delegate = delegate

  def handleUserError(self, user_error, data):
    """See error.ErrorHandler.handleUserError for specification."""
    if not data.program:
      return self._delegate.handleUserError(user_error, data)

    # If message is not set, set it to the default associated with the
    # given status (such as "Method Not Allowed" or "Service Unavailable").
    message = user_error.message if user_error.message else (
        httplib.responses.get(user_error.status, ''))

    context = {
        'page_name': message,
        'message': message,
    }

    return http.HttpResponse(
        content=self._renderer.render(data, _GSOC_ERROR_TEMPLATE, context),
        status=user_error.status)

  def handleServerError(self, server_error, data):
    """See error.ErrorHandler.handleServerError for specification."""
    return self._delegate.handleServerError(server_error, data)


class GSoCRequestHandler(base.RequestHandler):
  """Customization required by GSoC to handle HTTP requests."""

  def __init__(self):
    """Initializes a new instance of the request handler for Summer of Code."""
    super(GSoCRequestHandler, self).__init__(
        _GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
        GSoCErrorHandler(render.SOC_RENDERER, error.MELANGE_ERROR_HANDLER))
