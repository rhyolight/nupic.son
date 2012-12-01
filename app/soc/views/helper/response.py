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

"""Module containing the Response object."""

import httplib

from django import http


# TODO(nathaniel): eliminate this in favor of using its superclass everywhere.
class Response(http.HttpResponse):
  """Response class that wraps the Django's HttpResponse class but
  with message for every possible HTTP response code.
  """

  def set_status(self, status, message=None):
    """Sets the HTTP status and message for this response.

    Args:
      status: HTTP status code
      message: the HTTP status string to use

    If no status string is given, we use the default from the HTTP/1.1
    specification defined httplib.responses.
    """
    if not message:
      message = httplib.responses.get(status, '')

    self.status_code = status
    self.content = message
