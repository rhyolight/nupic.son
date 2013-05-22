# Copyright 2013 the Melange authors.
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

"""Module for the site error-handling pages."""

import httplib

from django import http
from django.template import loader

from melange.appengine import system

_TEMPLATE = 'error.html'

_USER_ERROR_STYLE = 'user-error-style.css'
_SERVER_ERROR_STYLE = 'server-error-style.css'


def _handle(status, style_file, message=None):
  """Returns an appropriate http.HttpResponse.

  Args:
    status: A numeric HTTP status code.
    style_file: One of _USER_ERROR_STYLE or _SERVER_ERROR_STYLE.
    message: An optional message for the user. If not provided, the
      standard text for the given HTTP status code will be used.

  Returns:
    An appropriate http.HttpResponse.
  """
  message = httplib.responses.get(status, '') if message is None else message
  context = {
      'app_version': system.getMelangeVersion(),
      'code': status,
      'message': message,
      'page_name': httplib.responses[status],
      'style_file': style_file,
  }
  content = loader.render_to_string(_TEMPLATE, dictionary=context)

  return http.HttpResponse(content=content, status=status)


def handle404():
  """Returns a response appropriate for a nonexistent path.

  Returns:
    An http.HttpResponse appropriate for a nonexistent path.
  """
  return _handle(httplib.NOT_FOUND, _USER_ERROR_STYLE)


def handle500():
  """Returns a response indicating a failure within the server.

  Returns:
    An http.HttpResponse indicating a failure within the server.
  """
  return _handle(httplib.INTERNAL_SERVER_ERROR, _SERVER_ERROR_STYLE)


# TODO(nathaniel): This interface specification references RequestData
# objects. When RequestData is migrated from the "soc" package to the
# "melange" package, it will have to be placed at a "lower" level of
# abstraction (which is to be expected).
class ErrorHandler(object):
  """Interface for handlers of UserError and ServerError exceptions."""

  def handleUserError(self, user_error, data):
    """Returns a response appropriate for a given user error.

    Args:
      user_error: A UserError exception.
      data: A RequestData object describing the current request.

    Returns:
      An http.HttpResponse appropriate for the given user error.
    """
    raise NotImplementedError()

  def handleServerError(self, server_error, data):
    """Returns a response appropriate for a given server error.

    Args:
      server_error: A ServerError exception.
      data: A RequestData object describing the current request.

    Returns:
      An http.HttpResponse appripriate for the given server error.
    """
    raise NotImplementedError()


class MelangeErrorHandler(ErrorHandler):
  """An ErrorHandler implementation suitable for use anywhere in Melange."""

  def handleUserError(self, user_error, data):
    """See ErrorHandler.handleUserError for specification."""
    return _handle(user_error.status, _USER_ERROR_STYLE,
                   message=user_error.message)

  def handleServerError(self, server_error, data):
    """See ErrorHandler.handleServerError for specification."""
    return _handle(server_error.status, _SERVER_ERROR_STYLE,
                   message=server_error.message)

# Since MelangeErrorHandler is stateless there might as well be just one of it.
MELANGE_ERROR_HANDLER = MelangeErrorHandler()


def handleUserError(data, status, message=None):
  """Returns a response appropriate for a given user error.

  Args:
    data: A RequestData describing a request.
    status: A numeric HTTP status code.
    message: An optional message for the user.

  Returns:
    An http.HttpResponse appropriate for the given user error.
  """
  return _handle(status, _USER_ERROR_STYLE, message=message)


def handleServerError(data, status, message=None):
  """Returns a response appropriate for a given server error.

  Args:
    data: A RequestData describing a request.
    status: A numeric HTTP status code.
    message: An optional message for the user.

  Returns:
    An http.HttpResponse appropriate for the given server error.
  """
  return _handle(status, _SERVER_ERROR_STYLE, message=message)
