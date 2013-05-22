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

"""Tests for functions that respond in the context of errors."""

import httplib
import unittest

from django import http

from melange.request import error
from melange.request import exception
from soc.views.helper import request_data


class ErrorFunctionsTest(unittest.TestCase):
  """Tests the functions used as error-handling views."""

  def test404(self):
    """Tests that a reasonable 404 response is returned."""
    response = error.handle404()
    self.assertEqual(httplib.NOT_FOUND, response.status_code)
    self.assertTrue(response.content)

  def test500(self):
    """Tests that a reasonable 500 response is returned."""
    response = error.handle500()
    self.assertEqual(httplib.INTERNAL_SERVER_ERROR, response.status_code)
    self.assertTrue(response.content)

  def testUserError(self):
    """Tests that a reasonable response is returned for any user error."""
    data = request_data.RequestData(http.HttpRequest(), [], {})
    status_code = httplib.GONE
    message = 'test-user-error-message'

    response = error.handleUserError(data, status_code, message=message)
    self.assertEqual(status_code, response.status_code)
    self.assertIn(message, response.content)

  def testServerError(self):
    """Tests that a reasonable response is returned for any server error."""
    data = request_data.RequestData(http.HttpRequest(), [], {})
    status_code = httplib.NOT_IMPLEMENTED
    message = 'test-server-error-message'

    response = error.handleServerError(data, status_code, message=message)
    self.assertEqual(status_code, response.status_code)
    self.assertIn(message, response.content)


class MelangeErrorHandlerTest(unittest.TestCase):
  """Tests the MelangeErrorHandler implementation of ErrorHandler."""

  def testUserError(self):
    """Tests that a reasonable response is returned for any user error."""
    data = request_data.RequestData(http.HttpRequest(), [], {})
    status_code = httplib.EXPECTATION_FAILED
    message = 'test-user-error-message'

    user_error = exception.UserError(status_code, message=message)
    response = error.MELANGE_ERROR_HANDLER.handleUserError(user_error, data)
    self.assertEqual(status_code, response.status_code)
    self.assertIn(message, response.content)

  def testServerError(self):
    """Tests that a reasonable response is returned for any server error."""
    data = request_data.RequestData(http.HttpRequest(), [], {})
    status_code = httplib.GATEWAY_TIMEOUT
    message = 'test-server-error-message'

    server_error = exception.ServerError(status_code, message=message)
    response = error.MELANGE_ERROR_HANDLER.handleServerError(
        server_error, data)
    self.assertEqual(status_code, response.status_code)
    self.assertIn(message, response.content)
