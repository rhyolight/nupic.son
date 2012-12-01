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

from django.utils import simplejson
from django.template import loader

from soc.logic import exceptions
from soc.views.helper import access_checker
from soc.views.helper import context as context_helper
from soc.views.helper import request_data
from soc.views.helper import response as response_helper

# TODO(nathaniel): Clean up this legacy API re-export by redirecting
# clients using this module attribute to its actual definition.
Response = response_helper.Response


class RequestHandler(object):
  """Base class managing HTTP Requests."""

  def context(self):
    return {}

  def get(self):
    """Handler for HTTP GET request.

    Default implementation calls templatePath and context and passes
    those to render to construct the page.
    """
    context = self.context()
    self.render(self.templatePath(), context)

  def json(self):
    """Handler for HTTP GET request with a 'fmt=json' parameter."""

    if not self.request.GET.get('plain'):
      self.response['Content-Type'] = 'application/json'

    # if the browser supports HTTP/1.1
    # post-check and pre-check and no-store for IE7
    # TODO(nathaniel): We need no longer support IE7. Can this be simplified
    # or eliminated?
    self.response['Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                                     'post-check=0, pre-check=0' # HTTP/1.1, IE7
    self.response['Pragma'] = 'no-cache'

    context = self.jsonContext()

    if self.request.GET.get('marker'):
      # allow the django test framework to capture the context dictionary
      loader.render_to_string('json_marker.html', dictionary=context)

    if isinstance(context, unicode) or isinstance(context, str):
      data = context
    else:
      data = simplejson.dumps(context)

    self.response.write(data)

  def jsonContext(self):
    """Defines the JSON object to be dumped and returned on a HTTP GET request
    with 'fmt=json' parameter.
    """
    return {
        'error': 'json() method not implemented',
    }

  def post(self):
    """Handler for HTTP POST request."""
    self.error(httplib.METHOD_NOT_ALLOWED)

  def head(self):
    """Handler for HTTP HEAD request."""
    self.error(httplib.METHOD_NOT_ALLOWED)

  def options(self):
    """Handler for HTTP OPTIONS request."""
    self.error(httplib.METHOD_NOT_ALLOWED)

  def put(self):
    """Handler for HTTP PUT request."""
    self.error(httplib.METHOD_NOT_ALLOWED)

  def delete(self):
    """Handler for HTTP DELETE request."""
    self.error(httplib.METHOD_NOT_ALLOWED)

  def trace(self):
    """Handler for HTTP TRACE request."""
    self.error(httplib.METHOD_NOT_ALLOWED)

  def error(self, status, message=None):
    """Sets the error response code and message when an error is encountered.

    Args:
      status: the HTTP status error code
      message: the message to set, uses default if None
    """
    # If message is not set, set it to the default associated with the
    # given status (such as "Method Not Allowed" or "Service Unavailable").
    message = message or httplib.responses.get(status, '')

    template_path = 'error.html'
    context = {
        'page_name': message,
        'message': message,
    }

    self.response.status_code = status
    self.render(template_path, context)

  def djangoURLPatterns(self):
    """Returns a list of Django URL pattern tuples.

    Implementing subclasses must override this method.
    """
    raise NotImplementedError()

  def checkAccess(self):
    # TODO(nathaniel): this doesn't actually raise an exception as it says.
    # TODO(nathaniel): what exception should it raise if it did?
    """Raise an exception if the user doesn't have access to the requested URL.
    """
    self.error(
        httplib.UNAUTHORIZED,
        'RequestHandler.checkAccess has not been overridden to allow access')

  def render(self, template_path, render_context):
    """Renders the page using the specified context.

    The page is rendered using the template and context specified and
    is written to the response object.

    The context object is extended with the values from helper.context.default.

    Args:
      template_path: the path of the template that should be used
      render_context: the context that should be used
    """
    context = context_helper.default(self.data)
    context.update(render_context)
    rendered = loader.render_to_string(template_path, dictionary=context)
    self.response.write(rendered)

  def templatePath(self):
    """Returns the path to the template that should be used in render().

    Implementing subclasses must override this method.
    """
    raise NotImplementedError()

  def accessViolation(self, status, message):
    """Default access violation handler."""
    self.error(status, message)

  def _dispatch(self):
    """Dispatches the HTTP request to its respective handler method."""
    if self.request.method == 'GET':
      if self.request.GET.get('fmt') == 'json':
        self.json()
      else:
        self.get()
    elif self.request.method == 'POST':
      if db.WRITE_CAPABILITY.is_enabled():
        self.post()
      else:
        referrer = self.request.META.get('HTTP_REFERER', '')
        params = urllib.urlencode({'dsw_disabled': 1})
        url_with_params = '%s?%s' % (referrer, params)
        self.redirect.toUrl(url_with_params)
    elif self.request.method == 'HEAD':
      self.head()
    elif self.request.method == 'OPTIONS':
      self.options()
    elif self.request.method == 'PUT':
      self.put()
    elif self.request.method == 'DELETE':
      self.delete()
    elif self.request.method == 'TRACE':
      self.trace()
    else:
      self.error(httplib.NOT_IMPLEMENTED)

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
      self._dispatch()
    except exceptions.LoginRequest, e:
      request.get_full_path().encode('utf-8')
      self.redirect.login().to()
    except exceptions.RedirectRequest, e:
      self.redirect.toUrl(e.url)
    except exceptions.AccessViolation, e:
      self.accessViolation(e.status, e.args[0])
    except exceptions.GDocsLoginRequest, e:
      self.redirect.toUrl('%s?%s' % (self.redirect.urlOf(e.url_name),
                                     urllib.urlencode({'next':e.next})))
    except exceptions.Error, e:
      self.error(e.status, message=e.args[0])
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
