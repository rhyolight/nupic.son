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

"""Exceptions used in HTTP request processing."""

import httplib

_MAINTENANCE_MESSAGE = (
    'The site is currently in maintenance mode. Please try again later.')


class LoginRequired(Exception):
  """Indicates that user must be logged in to view the requested resource."""
  pass


class Redirect(Exception):
  """Indicates that the user should be redirected to specific URL.

  Attributes:
    url: The URL to which the user should be redirected.
  """

  def __init__(self, url):
    """Constructs a new RedirectRequest.

    Args:
      url: The URL to which the user should be redirected.
    """
    self.url = url


class UserError(Exception):
  """Indicates user fault or a problem with the user's request.

  Attributes:
    status: A numeric HTTP status code with which to respond to the user's
      request.
    message: An optional message to be conveyed to the user, or None if
      there is no such message.
  """

  def __init__(self, status, message=None):
    """Constructs a new UserError.

    Args:
      status: A numeric HTTP status code.
      message: An optional message for the user.
    """
    self.status = status
    self.message = message


def Forbidden(message=None):
  """Returns a UserError indicating a 403 Forbidden response.

  Args:
    message: An optional message for the user.
  """
  return UserError(httplib.FORBIDDEN, message=message)


def NotFound(message=None):
  """Returns a UserError indicating a 404 Not Found response.

  Args:
    message: An optional message for the user.
  """
  return UserError(httplib.NOT_FOUND, message=message)


def MethodNotAllowed():
  """Returns a UserError indicating a 405 Method Not Allowed response."""
  return UserError(httplib.METHOD_NOT_ALLOWED)


def BadRequest():
  """Returns a UserError indicating a 400 Bad Request response."""
  return UserError(httplib.BAD_REQUEST)


class ServerError(Exception):
  """Indicates a server fault or problem internal to Melange.

  Attributes:
    status: A numeric HTTP status code with which to respond to the user's
      request.
    message: An optional message to be conveyed to the user, or None if
      there is no such message.
  """

  def __init__(self, status, message=None):
    """Constructs a new ServerError.

    Args:
      status: A numeric HTTP status code.
      message: An optional message for the user.
    """
    self.status = status
    self.message = message


def MaintenanceMode():
  """Returns a ServerError indicating that Melange is in maintenance."""
  return ServerError(httplib.SERVICE_UNAVAILABLE, message=_MAINTENANCE)
