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

_USER_ERROR_STYLE_FILE = 'user-error-style.css'
_SERVER_ERROR_STYLE_FILE = 'server-error-style.css'


def _handle(status, style_file, message=None):
  """Returns an appropriate http.HttpResponse.

  Args:
    status: A numeric HTTP status code.
    style_file: One of _USER_ERROR_STYLE_FILE or _SERVER_ERROR_STYLE_FILE.
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
  return _handle(httplib.NOT_FOUND, _USER_ERROR_STYLE_FILE)


def handle500():
  """Returns a response indicating a failure within the server.

  Returns:
    An http.HttpResponse indicating a failure within the server.
  """
  return _handle(httplib.INTERNAL_SERVER_ERROR, _SERVER_ERROR_STYLE_FILE)


def handleUserError(data, status, message=None):
  """Returns a response appropriate for a given user error.

  Args:
    data: A RequestData describing a request.
    status: A numeric HTTP status code.
    message: An optional message for the user.

  Returns:
    An http.HttpResponse appropriate for the given user error.
  """
  return _handle(status, _USER_ERROR_STYLE_FILE, message=message)


def handleServerError(data, status, message=None):
  """Returns a response appropriate for a given server error.

  Args:
    data: A RequestData describing a request.
    status: A numeric HTTP status code.
    message: An optional message for the user.

  Returns:
    An http.HttpResponse appropriate for the given server error.
  """
  return _handle(status, _SERVER_ERROR_STYLE_FILE, message=message)
