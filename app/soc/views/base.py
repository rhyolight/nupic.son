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

"""Module containing the boilerplate required to construct views. This
module is largely based on appengine's webapp framework's code.
"""

import json
import urllib

from google.appengine.ext import db

from django import http
from django.template import loader

from melange.request import error
from melange.request import exception
from melange.request import initialize
from melange.request import links
from melange.request import render


class RequestHandler(object):
  """Base class managing HTTP Requests."""

  # TODO(nathaniel): Pass these as construction parameters like
  # real injected dependencies.
  initializer = initialize.MELANGE_INITIALIZER
  linker = links.LINKER
  renderer = render.MELANGE_RENDERER
  error_handler = error.MELANGE_ERROR_HANDLER
  access_checker = None

  def context(self, data, check, mutator):
    """Provides a dictionary of values needed to render a template.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      A dictionary of values to be used in rendering a template.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    return {}

  def get(self, data, check, mutator):
    """Handler for HTTP GET request.

    Default implementation calls templatePath and context and passes
    those to render to construct the page.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    context = self.context(data, check, mutator)
    template_path = self.templatePath()
    response_content = self.renderer.render(data, template_path, context)
    return http.HttpResponse(content=response_content)

  def json(self, data, check, mutator):
    """Handler for HTTP GET request with a 'fmt=json' parameter.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    context = self.jsonContext(data, check, mutator)

    if isinstance(context, unicode) or isinstance(context, str):
      json_formatted_context = context
    else:
      json_formatted_context = json.dumps(context)

    # NOTE(nathaniel): The Django documentation and code disagree
    # on what the default value of content_type is, so the best way
    # to use the default value is to avoid passing the parameter.
    if data.request.GET.get('plain'):
      response = http.HttpResponse(content=json_formatted_context)
    else:
      response = http.HttpResponse(
          content=json_formatted_context, content_type='application/json')

    # if the browser supports HTTP/1.1
    # post-check and pre-check and no-store for IE7
    # TODO(nathaniel): We need no longer support IE7. Can this be simplified
    # or eliminated?
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                                'post-check=0, pre-check=0' # HTTP/1.1, IE7
    response['Pragma'] = 'no-cache'

    # TODO(nathaniel): find a better way to do this - I mean, the
    # jsonContext method is already as exposed as this method.
    if data.request.GET.get('marker'):
      # allow the django test framework to capture the context dictionary
      loader.render_to_string('json_marker.html', dictionary=context)

    return response

  def jsonContext(self, data, check, mutator):
    """Defines the JSON object to be dumped and returned on a HTTP GET request
    with 'fmt=json' parameter.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An object to be used as the content in a response to a json GET request
        after having been put through json.dumps if it is not a string
        or unicode object.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    # TODO(nathaniel): That return value description is a travesty. Just make
    # this method return "a dictionary to be serialized into JSON response
    # content" or something like that always.
    return {
        'error': 'json() method not implemented',
    }

  def post(self, data, check, mutator):
    """Handler for HTTP POST request.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    raise exception.MethodNotAllowed()

  def head(self, data, check, mutator):
    """Handler for HTTP HEAD request.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    # TODO(nathaniel): This probably wouldn't be all that unreasonable to
    # implement?
    raise exception.MethodNotAllowed()

  def options(self, data, check, mutator):
    """Handler for HTTP OPTIONS request.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    raise exception.MethodNotAllowed()

  def put(self, data, check, mutator):
    """Handler for HTTP PUT request.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    raise exception.MethodNotAllowed()

  def delete(self, data, check, mutator):
    """Handler for HTTP DELETE request.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    raise exception.MethodNotAllowed()

  def trace(self, data, check, mutator):
    """Handler for HTTP TRACE request.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    raise exception.MethodNotAllowed()

  def djangoURLPatterns(self):
    """Returns a list of Django URL pattern tuples.

    Implementing subclasses must override this method.
    """
    raise NotImplementedError()

  def checkAccess(self, data, check, mutator):
    # TODO(nathaniel): eliminate this - it doesn't actually simplify
    # the HTTP method implementations all that much to have it
    # separated out.
    """Ensure that the user's request should be satisfied.

    Implementing subclasses must override this method.

    Implementations must not mutate any of this RequestHandler's state and
    should merely raise an exception if the user's request should not be
    satisfied or return normally if the user's request should be satisfied.

    Args:
      data: A soc.views.helper.request_data.RequestData.
      check: A soc.views.helper.access_checker.AccessChecker.
      mutator: A soc.views.helper.access_checker.Mutator.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    # TODO(nathaniel): Eliminate this method entirely after eliminating
    # all overriding implementations.
    return self.access_checker.checkAccess(data, check, mutator)

  def templatePath(self):
    """Returns the path to the template that should be used in render().

    Implementing subclasses must override this method.
    """
    raise NotImplementedError()

  def _dispatch(self, data, check, mutator):
    """Dispatches the HTTP request to its respective handler method.

    Args:
      data: The request_data.RequestData object for the current request.
      check: The access_checker.AccessChecker object for the current
        request.
      mutator: The access_checker.Mutator object for the current
        request.

    Returns:
      An http.HttpResponse appropriate for the current request.

    Raises:
      exception.LoginRequired: An exception.LoginRequired indicating
        that the user is not logged in, but must log in to access the
        resource specified in their request.
      exception.Redirect: An exception.Redirect indicating that the
        user is to be redirected to another URL.
      exception.UserError: An exception.UserError describing what was
        erroneous about the user's request and describing an appropriate
        response.
      exception.ServerError: An exception.ServerError describing some
        problem that arose during request processing and describing an
        appropriate response.
    """
    if data.request.method == 'GET':
      if data.request.GET.get('fmt') == 'json':
        return self.json(data, check, mutator)
      else:
        return self.get(data, check, mutator)
    elif data.request.method == 'POST':
      if db.WRITE_CAPABILITY.is_enabled():
        return self.post(data, check, mutator)
      else:
        referrer = data.request.META.get('HTTP_REFERER', '')
        params = urllib.urlencode({'dsw_disabled': 1})
        return http.HttpResponseRedirect('%s?%s' % (referrer, params))
    elif data.request.method == 'HEAD':
      return self.head(data, check, mutator)
    elif data.request.method == 'OPTIONS':
      return self.options(data, check, mutator)
    elif data.request.method == 'PUT':
      return self.put(data, check, mutator)
    elif data.request.method == 'DELETE':
      return self.delete(data, check, mutator)
    elif data.request.method == 'TRACE':
      return self.trace(data, check, mutator)
    else:
      raise exception.MethodNotAllowed()

  # TODO(nathaniel): Migrate this elsewhere.
  def checkMaintenanceMode(self, data):
    """Checks whether or not the site is in maintenance mode.

    Raises:
      exception.ServerError: If the site is in maintenance mode and
        the user is not a developer.
    """
    if data.site.maintenance_mode and not data.is_developer:
      raise exception.MaintenanceMode()

  def __call__(self, request, *args, **kwargs):
    """Returns the response object for the requested URL.

    In detail, this method does the following:
    1. Initialize request, arguments and keyword arguments as instance variables
    2. Calls the access check.
    3. Delegates dispatching to the handler to the _dispatch method.
    4. Handles several known exception types that may have been raised.
    5. Returns the response.
    """
    try:
      data, check, mutator = self.initializer.initialize(request, args, kwargs)
      self.checkMaintenanceMode(data)
      self.checkAccess(data, check, mutator)
      return self._dispatch(data, check, mutator)
    except exception.LoginRequired:
      return data.redirect.toUrl(self.linker.login(request))
    except exception.Redirect as redirect:
      return data.redirect.toUrl(redirect.url)
    except exception.UserError as user_error:
      return self.error_handler.handleUserError(user_error, data)
    except exception.ServerError as server_error:
      return self.error_handler.handleServerError(server_error, data)
