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

"""Module containing FormHandler interface to handle POST data."""

class FormHandler(object):
  """Simplified version of request handler that is able to take care of
  the received data.
  """

  # TODO(daniel): remove view from this list.
  def __init__(self, view, url=None):
    """Initializes new instance of form handler.

    Args:
      view: callback to implementation of base.RequestHandler
        that creates this object.
      url: URL that should be used for redirect after the request is
        handled successfully. If it is not specified, the handler should
        return response with status of 200 or construct a URL to redirect to
        on its own.
    """
    self._view = view
    self._url = url

  def handle(self, data, check, mutator):
    """Handles the data that was received in the current request and returns
    an appropriate HTTP response.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    raise NotImplementedError
