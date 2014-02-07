# Copyright 2014 the Melange authors.
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

"""Module for Summer Of Code-specific error-handling pages."""

import httplib

from django import http

from melange.request import error

from summerofcode.request import render


_GSOC_ERROR_TEMPLATE = 'modules/gsoc/error.html'

class SOCErrorHandler(error.ErrorHandler):
  """A Summer Of Code implementation of error.ErrorHandler."""

  def __init__(self, renderer, delegate):
    """Constructs a SOCErrorHandler.

    Args:
      renderer: A render.Renderer to be used to render response content.
      delegate: An error.ErrorHandler to be used to handle errors
        that this SOCErrorHandler does not wish or is not able to handle.
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


# Since GSoCInitializer is stateless, there might as well be just one of it.
SOC_ERROR_HANDLER = SOCErrorHandler(
    render.SOC_RENDERER, error.MELANGE_ERROR_HANDLER)
