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

"""Classes for initializing per-request objects."""

from soc.views.helper import request_data
from soc.views.helper import access_checker


class Initializer(object):
  """Interface for RequestData object creators."""

  def initialize(self, request, args, kwargs):
    """Creates a RequestData, AccessChecker, Mutator trio of objects.

    Args:
      request: An http.HttpRequest object describing the current request.
      args: Additional positional arguments passed with the request.
      kwargs: Additional keyword arguments passed with the request.

    Returns:
      A request_data.RequestData, access_checker.AccessChecker,
        access_checker.Mutator trio of objects.
    """
    raise NotImplementedError()


class MelangeInitializer(Initializer):
  """An Initializer implementation for use throughout Melange."""

  def initialize(self, request, args, kwargs):
    """See Initializer.initialize for specification."""
    data = request_data.RequestData(request, args, kwargs)
    mutator = access_checker.Mutator(data)
    if data.is_developer:
      check = access_checker.DeveloperAccessChecker(data)
    else:
      check = access_checker.AccessChecker(data)
    return data, check, mutator

# Since MelangeInitializer is stateless, there might as well be just one of it.
MELANGE_INITIALIZER = MelangeInitializer()
