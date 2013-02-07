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

import httplib
import urllib

from google.appengine.ext import db

from django import http
from django.utils import simplejson
from django.template import loader

from soc.logic import exceptions
from soc.logic import links
from soc.views.helper import access_checker
from soc.views.helper import context as context_helper
from soc.views.helper import request_data


class RequestHandler(object):
  """Base class managing HTTP Requests."""

  # TODO(nathaniel): Pass this as a construction parameter like
  # a real injected dependency.
  linker = links.Linker()

  def context(self):
    return {}

  def get(self, data, check, mutator):
    """Handler for HTTP GET request.

    Default implementation calls templatePath and context and passes
    those to render to construct the page.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    context = self.context()
    template_path = self.templatePath()
    response_content = self.render(data, template_path, context)
    return http.HttpResponse(content=response_content)

  def json(self):
    """Handler for HTTP GET request with a 'fmt=json' parameter."""
    context = self.jsonContext()

    if isinstance(context, unicode) or isinstance(context, str):
      data = context
    else:
      data = simplejson.dumps(context)

    # NOTE(nathaniel): The Django documentation and code disagree
    # on what the default value of content_type is, so the best way
    # to use the default value is to avoid passing the parameter.
    if self.data.request.GET.get('plain'):
      response = http.HttpResponse(content=data)
    else:
      response = http.HttpResponse(
          content=data, content_type='application/json')

    # if the browser supports HTTP/1.1
    # post-check and pre-check and no-store for IE7
    # TODO(nathaniel): We need no longer support IE7. Can this be simplified
    # or eliminated?
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                                'post-check=0, pre-check=0' # HTTP/1.1, IE7
    response['Pragma'] = 'no-cache'

    # TODO(nathaniel): find a better way to do this - I mean, the
    # jsonContext method is already as exposed as this method.
    if self.data.request.GET.get('marker'):
      # allow the django test framework to capture the context dictionary
      loader.render_to_string('json_marker.html', dictionary=context)

    return response

  def jsonContext(self):
    """Defines the JSON object to be dumped and returned on a HTTP GET request
    with 'fmt=json' parameter.
    """
    return {
        'error': 'json() method not implemented',
    }

  def post(self, data, check, mutator):
    """Handler for HTTP POST request.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    return self.error(data, httplib.METHOD_NOT_ALLOWED)

  def head(self, data, check, mutator):
    """Handler for HTTP HEAD request.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    # TODO(nathaniel): This probably wouldn't be all that unreasonable to
    # implement?
    return self.error(data, httplib.METHOD_NOT_ALLOWED)

  def options(self, data, check, mutator):
    """Handler for HTTP OPTIONS request.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    return self.error(data, httplib.METHOD_NOT_ALLOWED)

  def put(self, data, check, mutator):
    """Handler for HTTP PUT request.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    return self.error(data, httplib.METHOD_NOT_ALLOWED)

  def delete(self, data, check, mutator):
    """Handler for HTTP DELETE request.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    return self.error(data, httplib.METHOD_NOT_ALLOWED)

  def trace(self, data, check, mutator):
    """Handler for HTTP TRACE request.

    Args:
      data: A request_data.RequestData.
      check: An access_checker.AccessChecker.
      mutator: An access_checker.Mutator.

    Returns:
      An http.HttpResponse appropriate for the given request parameters.
    """
    return self.error(data, httplib.METHOD_NOT_ALLOWED)

  def error(self, data, status, message=None):
    """Constructs an HttpResponse indicating an error.

    Args:
      data: The request_data.RequestData object for the current request.
      status: The HTTP status code for the error.
      message: A message to display to the user. If not supplied, a default
        appropriate for the given status code (such as "Bad Gateway" or
        "Payment Required") will be used.

    Returns:
      An http.HttpResponse indicating an error.
    """
    message = message or httplib.responses.get(status, '')

    template_path = 'error.html'
    context = {
        'page_name': message,
        'message': message,
    }

    return http.HttpResponse(
        content=self.render(data, template_path, context), status=status)

  def djangoURLPatterns(self):
    """Returns a list of Django URL pattern tuples.

    Implementing subclasses must override this method.
    """
    raise NotImplementedError()

  def checkAccess(self):
    # TODO(nathaniel): eliminate this - it doesn't actually simplify
    # the HTTP method implementations all that much to have it
    # separated out.
    """Ensure that the user's request should be satisfied.

    Implementing subclasses must override this method.

    Implementations must not mutate any of this RequestHandler's state and
    should merely raise an exception if the user's request should not be
    satisfied or return normally if the user's request should be satisfied.

    Raises:
      exceptions.Error: If the user's request should not be satisfied for
        any reason.
    """
    raise NotImplementedError()

  def render(self, data, template_path, render_context):
    """Renders the page content from the specified template and context.

    Values supplied by helper.context.default are used in the rendering in
    addition to those supplied by render_context (render_context overrides
    in cases of conflict).

    Args:
      data: The RequestData that should be used.
      template_path: The path of the template that should be used.
      render_context: The context dictionary that should be used.

    Returns:
      The page content.
    """
    context = context_helper.default(data)
    context.update(render_context)
    return loader.render_to_string(template_path, dictionary=context)

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
    """
    if data.request.method == 'GET':
      if data.request.GET.get('fmt') == 'json':
        return self.json()
      else:
        return self.get(data, check, mutator)
    elif data.request.method == 'POST':
      if db.WRITE_CAPABILITY.is_enabled():
        return self.post(data, check, mutator)
      else:
        referrer = data.request.META.get('HTTP_REFERER', '')
        params = urllib.urlencode({'dsw_disabled': 1})
        url_with_params = '%s?%s' % (referrer, params)
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
      return self.error(data, httplib.NOT_IMPLEMENTED)

  def init(self, request, args, kwargs):
    """Creates objects necessary for serving the request.

    Subclasses must override this abstract method.

    Args:
      request: The http.HttpRequest for the current request.
      args: Additional arguments passed to this request handler.
      kwargs: Additional keyword arguments passed to this request handler.

    Returns:
      A triplet of the RequestData, Check, and Mutator to be used to
        service the request.
    """
    raise NotImplementedError()

  # TODO(nathaniel): Migrate this elsewhere.
  def checkMaintenanceMode(self, data):
    """Checks whether or not the site is in maintenance mode.

    Raises:
      exceptions.MaintainceMode: If the site is in maintenance mode and the
        user is not a developer.
    """
    if data.site.maintenance_mode and not data.is_developer:
      raise exceptions.MaintainceMode(
          'The site is currently in maintenance mode. Please try again later.')

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
      # TODO(nathaniel): eliminate these attribute assignments by passing
      # the associated values through the call stack instead (issue 1665).
      self.data, self.check, self.mutator = self.init(
          request, args, kwargs)
      self.checkMaintenanceMode(self.data)
      self.checkAccess()
      return self._dispatch(self.data, self.check, self.mutator)
    except exceptions.LoginRequest, e:
      request.get_full_path().encode('utf-8')
      return self.data.redirect.login().to()
    except exceptions.RedirectRequest, e:
      return self.data.redirect.toUrl(e.url)
    except exceptions.GDocsLoginRequest, e:
      return self.data.redirect.toUrl('%s?%s' % (
          self.data.redirect.urlOf(e.url_name),
          urllib.urlencode({'next': e.path})))
    except exceptions.Error, e:
      return self.error(self.data, e.status, message=e.args[0])
    finally:
      self.data = None
      self.check = None
      self.mutator = None


class SiteRequestHandler(RequestHandler):
  """Customization required by global site pages to handle HTTP requests."""

  def init(self, request, args, kwargs):
    data = request_data.RequestData(request, args, kwargs)
    if data.is_developer:
      mutator = access_checker.DeveloperMutator(data)
      check = access_checker.DeveloperAccessChecker(data)
    else:
      mutator = access_checker.Mutator(data)
      check = access_checker.AccessChecker(data)
    return data, check, mutator
