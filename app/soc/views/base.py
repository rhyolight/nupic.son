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

"""Module containing the boiler plate required to construct views. This
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
from soc.views.helper import response as response_helper


class RequestHandler(object):
  """Base class managing HTTP Requests."""

  # TODO(nathaniel): Pass this as a construction parameter like
  # a real injected dependency.
  linker = links.Linker()

  def context(self):
    return {}

  def get(self):
    """Handler for HTTP GET request.

    Default implementation calls templatePath and context and passes
    those to render to construct the page.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        attribute.
    """
    context = self.context()
    template_path = self.templatePath()
    response_content = self.render(template_path, context)

    # TODO(nathaniel): return a new object here instead of this attribute
    # of self.
    self.response.write(response_content)
    return self.response

  def json(self):
    """Handler for HTTP GET request with a 'fmt=json' parameter."""
    context = self.jsonContext()

    if isinstance(context, unicode) or isinstance(context, str):
      data = context
    else:
      data = simplejson.dumps(context)

    if self.data.request.GET.get('plain'):
      content_type = http.DEFAULT_CONTENT_TYPE
    else:
      content_type = 'application/json'

    response = http.HttpResponse(content=data, content_type=content_type)

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

  def post(self):
    """Handler for HTTP POST request.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    self.response = self.error(httplib.METHOD_NOT_ALLOWED)

  def head(self):
    """Handler for HTTP HEAD request.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    return self.error(httplib.METHOD_NOT_ALLOWED)

  def options(self):
    """Handler for HTTP OPTIONS request.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    return self.error(httplib.METHOD_NOT_ALLOWED)

  def put(self):
    """Handler for HTTP PUT request.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    return self.error(httplib.METHOD_NOT_ALLOWED)

  def delete(self):
    """Handler for HTTP DELETE request.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    return self.error(httplib.METHOD_NOT_ALLOWED)

  def trace(self):
    """Handler for HTTP TRACE request.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    return self.error(httplib.METHOD_NOT_ALLOWED)

  def error(self, status, message=None):
    """Constructs an HttpResponse indicating an error.

    Args:
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
        content=self.render(template_path, context), status=status)

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

  def render(self, template_path, render_context):
    """Renders the page content from the specified template and context.

    Values supplied by helper.context.default are used in the rendering in
    addition to those supplied by render_context (render_context overrides
    in cases of conflict).

    Args:
      template_path: The path of the template that should be used.
      render_context: The context dictionary that should be used.

    Returns:
      The page content.
    """
    context = context_helper.default(self.data)
    context.update(render_context)
    return loader.render_to_string(template_path, dictionary=context)

  def templatePath(self):
    """Returns the path to the template that should be used in render().

    Implementing subclasses must override this method.
    """
    raise NotImplementedError()

  def _dispatch(self):
    """Dispatches the HTTP request to its respective handler method.

    Returns:
      An http.HttpResponse appropriate for this RequestHandler's request
        object.
    """
    if self.data.request.method == 'GET':
      if self.data.request.GET.get('fmt') == 'json':
        return self.json()
      else:
        return self.get()
    elif self.data.request.method == 'POST':
      if db.WRITE_CAPABILITY.is_enabled():
        return self.post()
      else:
        referrer = self.data.request.META.get('HTTP_REFERER', '')
        params = urllib.urlencode({'dsw_disabled': 1})
        url_with_params = '%s?%s' % (referrer, params)
        return http.HttpResponseRedirect('%s?%s' % (referrer, params))
    elif self.data.request.method == 'HEAD':
      return self.head()
    elif self.data.request.method == 'OPTIONS':
      return self.options()
    elif self.data.request.method == 'PUT':
      return self.put()
    elif self.data.request.method == 'DELETE':
      return self.delete()
    elif self.data.request.method == 'TRACE':
      return self.trace()
    else:
      return self.error(httplib.NOT_IMPLEMENTED)

  # TODO(nathaniel): Note that while this says that it sets the "data" and
  # "check" attributes, this implementation makes use of the "data" attribute
  # without having set it. Therefore extending classes must set at least the
  # "data" attribute before calling this superclass implementation if they
  # choose to do so (they do). This is an obstacle just waiting to cause
  # bigger problems.
  def init(self, request, args, kwargs):
    """Initializes the RequestHandler.

    Sets the data and check fields.
    """
    if self.data.site.maintenance_mode and not self.data.is_developer:
      raise exceptions.MaintainceMode(
          'The site is currently in maintenance mode. Please try again later.')

  def __call__(self, request, *args, **kwargs):
    """Returns the response object for the requested URL.

    In detail, this method does the following:
    1. Initialize request, arguments and keyword arguments as instance variables
    2. Construct the response object.
    3. Calls the access check.
    4. Delegates dispatching to the handler to the _dispatch method.
    5. Returns the response.
    """
    self.request = request
    self.args = args
    self.kwargs = kwargs

    self.response = response_helper.Response()

    try:
      self.init(request, args, kwargs)
      self.checkAccess()
      self.response = self._dispatch()
    except exceptions.LoginRequest, e:
      request.get_full_path().encode('utf-8')
      self.redirect.login().to()
    except exceptions.RedirectRequest, e:
      self.response = self.redirect.toUrl(e.url)
    except exceptions.GDocsLoginRequest, e:
      self.response = self.redirect.toUrl(
          '%s?%s' % (self.redirect.urlOf(e.url_name),
                     urllib.urlencode({'next':e.next_param})))
    except exceptions.Error, e:
      self.response = self.error(e.status, message=e.args[0])
    finally:
      response = self.response
      self.response = None
      self.request = None
      self.args = None
      self.kwargs = None
      self.data = None
      self.check = None
      self.mutator = None
      self.redirect = None

    return response


class SiteRequestHandler(RequestHandler):
  """Customization required by global site pages to handle HTTP requests."""

  def init(self, request, args, kwargs):
    self.data = request_data.RequestData()
    self.redirect = request_data.RedirectHelper(self.data, self.response)
    self.data.populate(None, request, args, kwargs)
    if self.data.is_developer:
      self.mutator = access_checker.DeveloperMutator(self.data)
      self.check = access_checker.DeveloperAccessChecker(self.data)
    else:
      self.mutator = access_checker.Mutator(self.data)
      self.check = access_checker.AccessChecker(self.data)
    super(SiteRequestHandler, self).init(request, args, kwargs)
