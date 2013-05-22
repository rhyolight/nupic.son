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

from melange.request import error


def handle404(request, *args, **kwargs):
  """Returns a response appropriate for a nonexistent path.

  This function is suitable for use as a Django view handling
  requests not captured by any other view.

  Args:
    request: An http.HttpRequest.
    *args: Positional arguments associated with the request.
    **kwargs: Keyword arguments associated with the request.

  Returns:
    An http.HttpResponse appropriate for a nonexistent path.
  """
  return error.handle404()


def handle500(request, *args, **kwargs):
  """Returns a response indicating a failure within the server.

  This function is suitable for use as a Django view handling
  requests the ordinary servicing of which resulted in a fault
  or failure of some kind.

  Args:
    request: An http.HttpRequest.
    *args: Positional arguments associated with the request.
    **kwargs: Keyword arguments associated with the request.

  Returns:
    An http.HttpResponse indicating a failure within the server.
  """
  return error.handle500()
