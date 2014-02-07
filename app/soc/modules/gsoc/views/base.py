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

from melange.request import initialize

from soc.views import base
from soc.modules.gsoc.views.helper import access_checker
from soc.modules.gsoc.views.helper import request_data

from summerofcode.request import error
from summerofcode.request import links
from summerofcode.request import render


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


class GSoCRequestHandler(base.RequestHandler):
  """Customization required by GSoC to handle HTTP requests."""

  def __init__(self):
    """Initializes a new instance of the request handler for Summer of Code."""
    super(GSoCRequestHandler, self).__init__(
        _GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
        error.SOC_ERROR_HANDLER)
