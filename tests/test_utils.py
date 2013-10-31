# Copyright 2008 the Melange authors.
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

"""Common testing utilities."""

import cgi
import hashlib
import os
import datetime
import httplib
import re
import StringIO
import urlparse
import unittest

# TODO(daniel): gaetestbed is deprecated; it should not be used.
import gaetestbed
from mox import stubout

from google.appengine.api import datastore
from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext import testbed

from django.test import client
from django.test import testcases

from soc.logic.helper import xsrfutil
from soc.middleware import xsrf as xsrf_middleware
from soc.modules import callback
from soc.tasks import mailer
from soc.views import template

from tests import profile_utils
from tests import program_utils
from tests import timeline_utils


# key of request argument associated with testbed object
TESTBED_ARG_KEY = 'TESTBED'

# root directory of the application source tree
APP_ROOT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '../app'))


class MockRequest(object):
  """Shared dummy request object to mock common aspects of a request.

  Before using the object, start should be called, when done (and
  before calling start on a new request), end should be called.
  """

  def __init__(self, path=None, method='GET'):
    """Creates a new empty request object.

    self.REQUEST, self.GET and self.POST are set to an empty
    dictionary, and path to the value specified.
    """

    self.REQUEST = {}
    self.GET = {}
    self.POST = {}
    self.META = {}
    self.path = path
    self.method = method

  def get_full_path(self):
    # TODO: if needed add GET params
    return self.path

  def start(self):
    """Readies the core for a new request.
    """

    core = callback.getCore()
    core.startNewRequest(self)

  def end(self):
    """Finishes up the current request.
    """

    core = callback.getCore()
    core.endRequest(self, False)


def get_general_raw(args_names):
  """Gets a general_raw function object.
  """

  def general_raw(*args, **kwargs):
    """Sends a raw information.

    That is the parameters passed to the return function that is mentioned
    in corresponding stubout.Set
    """

    num_args = len(args)
    result = kwargs.copy()
    for i, name in enumerate(args_names):
      if i < num_args:
        result[name] = args[i]
      else:
        result[name] = None
    if len(args_names) < num_args:
      result['__args__'] = args[num_args:]
    return result
  return general_raw


class StuboutHelper(object):
  """Utilities for view test.
  """

  def __init__(self):
    """Creates a new ViewTest object.
    """

    #Creates a StubOutForTesting object
    self.stubout = stubout.StubOutForTesting()

  def tearDown(self):
    """Tear down the stubs that were set up.
    """

    self.stubout.UnsetAll()

  def stuboutBase(self):
    """Applies basic stubout replacements.
    """
    pass

  def stuboutElement(self, parent, child_name, args_names):
    """Applies a specific stubout replacement.

    Replaces child_name's old definition with the new definition which has
    a list of arguments (args_names), in the context of the given parent.
    """

    self.stubout.Set(parent, child_name, get_general_raw(args_names))


class NonFailingFakePayload(object):
  """Extension of Django FakePayload class that includes seek and readline
  methods.
  """

  def __init__(self, content):
    self.__content = StringIO.StringIO(content)
    self.__len = len(content)

  def read(self, num_bytes=None):
    if num_bytes is None:
        num_bytes = self.__len or 1
    assert self.__len >= num_bytes, \
      "Cannot read more than the available bytes from the HTTP incoming data."
    content = self.__content.read(num_bytes)
    self.__len -= num_bytes
    return content

  def seek(self, pos, mode=0):
    return self.__content.seek(pos, mode)

  def readline(self, length=None):
    return self.__content.readline(length)

# monkey patch FakePayload class
# TODO(daniel): figure out why standard FakePayload does not work
client.FakePayload = NonFailingFakePayload


class SoCTestCase(unittest.TestCase):
  """Base test case to be subclassed.

  Common data are seeded and common helpers are created to make testing easier.
  """

  def programType(self):
    """Returns a string identifying the type of the program being tested.

    Extending classes must override this abstract method.

    Returns:
      A string such as "gsoc" or "gci" identifying the type of program being
        tested.
    """
    raise NotImplementedError()

  def init(self):
    """Performs test setup.

    Sets the following attributes:
      dev_test: True iff DEV_TEST is in environment (in parent)
    """
    self.dev_test = 'DEV_TEST' in os.environ

    self.testbed = testbed.Testbed()
    self.testbed.activate()

    self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
        probability=1)
    self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

    self.testbed.init_blobstore_stub()
    self.testbed.init_mail_stub()
    self.testbed.init_taskqueue_stub(root_path=APP_ROOT_PATH)

  @staticmethod
  def use_hr_schema(func):
    """Wrapper that makes the specified function to be called in HR datastore
    schema environment.

    It is important to mention that only the tested function is executed in
    this environment. In particular, setUp() and tearDown() function are
    run in the regular schema that is similar to Master/Slave.
    """

    def wrapper(self):
      """Wrapper that sets the probability to zero and calls the wrapped
      function.

      Args:
        self: an instance of SoCTestCase that invoked the wrapped function
      """
      self.policy.SetProbability(0)
      func(self)
      self.policy.SetProbability(1)

    return wrapper

  def assertSameEntity(self, expected_entity, actual_entity, msg=''):
    """App Engine entities comparison.

    It asserts that both expected_entity and actual_entity represent
    the same entity. The check is performed by comparing keys of the
    two specified entities.

    Args:
      expected_entity: the expected entity
      actual_entity: the actual entity
      msg: the optional message
    """
    if not isinstance(expected_entity, db.Model):
      raise TypeError('expected_entity has wrong type: %s' %
          type(expected_entity))

    if not isinstance(actual_entity, db.Model):
      raise TypeError('actual_entity has wrong type: %s' %
          type(actual_entity))

    self.assertEqual(expected_entity.key(), actual_entity.key(), msg)

  def createBlob(self, path, content=None):
    """Puts new Blob upload for the specified path and optional content.

    Args:
      path: path of the file to upload.
      content: content of the file.

    Returns:
      blobstore.BlobKey of the created blob.
    """
    filename = os.path.basename(path)
    content = content or 'fake content'
    # for some reason CreateBlob function returns datastore_types.Key instead
    # of datastore_types.BlobKey, whereas the latter type is required for
    # BlobReferenceProperty to work.
    self.testbed.get_stub('blobstore').CreateBlob(filename, content)
    return blobstore.BlobKey(filename)


# TODO(nathaniel): Drop "gsoc" attribute in favor of "program".
class GSoCTestCase(SoCTestCase):
  """GSoCTestCase for GSoC tests.

  Common data are seeded and common helpers are created to make testing easier.

  Attributes:
    gsoc: A GSoCProgram.
    program: The same GSoCProgram as "gsoc".
    org: A GSoCOrganization.
    org_app: An OrgAppSurvey.
    sponsor: A Sponsor.
    site: A Site.
    profile_helper: A GSoCProfileHelper.
    program_helper: A GSoCProgramHelper.
    timeline_helper: A GSoCTimelineHelper.
  """

  def programType(self):
    """See SoCTestCase.programType for specification."""
    return 'gsoc'

  def init(self):
    """Performs test set-up by seeding data and setting attributes."""
    super(GSoCTestCase, self).init()
    self.program_helper = program_utils.GSoCProgramHelper()
    self.sponsor = self.program_helper.createSponsor()
    self.gsoc = self.program = self.program_helper.createProgram()
    self.site = self.program_helper.createSite()
    self.org = self.program_helper.createOrg()
    self.org_app = self.program_helper.createOrgApp()
    self.timeline_helper = timeline_utils.GSoCTimelineHelper(
        self.gsoc.timeline, self.org_app)
    self.profile_helper = profile_utils.GSoCProfileHelper(
        self.gsoc, self.dev_test)


# TODO(nathaniel): Drop "gci" attribute in favor of "program".
class GCITestCase(SoCTestCase):
  """GCITestCase for GCI tests.

  Common data are seeded and common helpers are created to make testing easier.

  Attributes:
    gci: A GCIProgram.
    program: The same GCIProgram as "gci".
    site: A Site.
    sponsor: A Sponsor.
    org: A GCIOrganization.
    org_app: An OrgAppSurvey.
    profile_helper: A GCIProfileHelper.
    program_helper: A GCIProgramHelper.
    timeline_helper: A GCITimelineHelper.
  """

  def programType(self):
    """See SoCTestCase.programType for specification."""
    return 'gci'

  def init(self):
    """Performs test set-up by seeding data and setting attributes."""
    super(GCITestCase, self).init()
    self.program_helper = program_utils.GCIProgramHelper()
    self.sponsor = self.program_helper.createSponsor()
    self.gci = self.program = self.program_helper.createProgram()
    self.site = self.program_helper.createSite()
    self.org = self.program_helper.createOrg()
    self.org_app = self.program_helper.createOrgApp()
    self.timeline_helper = timeline_utils.GCITimelineHelper(
        self.gci.timeline, self.org_app)
    self.profile_helper = profile_utils.GCIProfileHelper(
        self.gci, self.dev_test)


class DjangoTestCase(SoCTestCase, testcases.TestCase):
  """Class extending Django TestCase in order to extend its functions.

  As well as remove the functions which are not supported by Google App Engine,
  e.g. database flush and fixtures loading without the assistance of Google
  App Engine Helper for Django.
  """

  _request_id = 0

  def _pre_setup(self):
    """Performs any pre-test setup."""
    # NOTE: super is not called, as TestCase class performs initialization
    # that is not suitable for Melange tests, because no real Django datastore
    # backend is used.
    self.client = client.Client()
    self.dev_test = False

  def _post_teardown(self):
    """ Performs any post-test cleanup."""
    # presence of this function is required by Django test runner
    pass

  def createOrg(self, override={}):
    """Creates an organization for the defined properties.
    """
    pass

  def seed(self, model, properties):
    """Returns a instance of model, seeded with properties.
    """
    from soc.modules.seeder.logic.seeder import logic as seeder_logic
    return seeder_logic.seed(model, properties, recurse=False)

  def seedProperties(self, model, properties):
    """Returns seeded properties for the specified model.
    """
    from soc.modules.seeder.logic.seeder import logic as seeder_logic
    return seeder_logic.seed_properties(model, properties, recurse=False)

  def gen_request_id(self):
    """Generate a request id.
    """
    os.environ['REQUEST_ID_HASH'] = hashlib.sha1(str(
        DjangoTestCase._request_id)).hexdigest()[:8].upper()
    DjangoTestCase._request_id += 1

  def get(self, url):
    """Performs a get to the specified url.
    """
    self.gen_request_id()
    response = self.client.get(url)
    return response

  def post(self, url, postdata={}):
    """Performs a post to the specified url with postdata.

    Takes care of setting the xsrf_token.
    """
    self.gen_request_id()
    postdata['xsrf_token'] = self.getXsrfToken(url, site=self.site)

    extra = {TESTBED_ARG_KEY: self.testbed}
    response = self.client.post(url, postdata, **extra)
    postdata.pop('xsrf_token')
    return response

  def modelPost(self, url, model, properties):
    """Performs a post to the specified url after seeding for model.

    Calls post().
    """
    properties = self.seedProperties(model, properties)
    response = self.post(url, properties)
    return response, properties

  def buttonPost(self, url, button_name, postdata=None):
    """Performs a post to url simulating that button_name is clicked.

    Calls post().
    """
    combined_postdata = {button_name: ''}
    if postdata:
      combined_postdata.update(postdata)
    url = '%s?button' % url
    response = self.post(url, combined_postdata)
    return response

  def createDocumentForPrefix(self, prefix, override={}):
    """Creates a document for the specified properties.
    """
    from soc.models.document import Document
    from soc.modules.seeder.logic.providers.string import (
        DocumentKeyNameProvider)
    properties = {
        'modified_by': self.profile_helper.user,
        'author': self.profile_helper.user,
        'home_for': None,
        'prefix': prefix,
        'scope': self.program,
        'read_access': 'public',
        'key_name': DocumentKeyNameProvider(),
    }
    properties.update(override)
    return self.seed(Document, properties)

  @classmethod
  def getXsrfToken(cls, path=None, method='POST', data={}, site=None, **extra):
    """Returns an XSRF token for request context.

    It is signed by Melange XSRF middleware.
    Add this token to POST data in order to pass the validation check of
    Melange XSRF middleware for HTTP POST.
    """

    """
    request = HttpRequest()
    request.path = path
    request.method = method
    """
    # request is currently not used in _getSecretKey
    class SiteContainingRequest(object):
      def __init__(self, site):
        if site:
          self.site = site
    request = SiteContainingRequest(site)
    # TODO(nathaniel): module API violation.
    key = xsrf_middleware._GetSecretKey(request)
    user_id = xsrfutil._getCurrentUserId()
    xsrf_token = xsrfutil._generateToken(key, user_id)
    return xsrf_token

  def getJsonResponse(self, url):
    """Returns the list reponse for the specified url and index.
    """
    return self.client.get(url + '?fmt=json&marker=1')

  def getListResponse(self, url, idx, start=None, limit=None):
    """Returns the list reponse for the specified url and index.
    """
    url = [url,'?fmt=json&marker=1&&idx=', str(idx)]
    if limit:
      url += ["&limit=", str(limit)]
    if start:
      url += ['&start=', start]
    return self.client.get(''.join(url))

  def getListData(self, url, idx):
    """Returns all data from a list view.
    """
    result = []
    start = ''

    i = 0

    while start != 'done':
      i += 1
      response = self.getListResponse(url, idx, start, 1000)
      self.assertIsJsonResponse(response)
      data = response.context['data'][start]
      result += data
      start = response.context['next']

    return result

  def assertRenderAll(self, response):
    """Calls render on all objects that are renderable.

    Args:
      response: Django's http.HttpResponse object.
    """
    for contexts in response.context or []:
      for context in contexts:
        values = context.values() if isinstance(context, dict) else [context]
        for value in values:
          try:
            iterable = iter(value)
          except TypeError:
            iterable = [value]
          for i in iterable:
            # make it easier to debug render failures
            if isinstance(i, template.Template):
              i.render()

  def assertErrorTemplatesUsed(self, response):
    """Assert that all the error templates were used.

    Args:
      response: Django's http.HttpResponse object.
    """
    self.assertNotEqual(response.status_code, httplib.OK)
    # TODO(SRabbelier): update this when we use an error template again
    # self.assertTemplateUsed(response, 'soc/error.html')

  def assertResponseCode(self, response, status_code):
    """Asserts that the response status is status_code.

    Args:
      response: Django's http.HttpResponse object.
      status_code: expected status code of the response.
    """
    # first ensure that no render failures occurred
    self.assertRenderAll(response)

    if response.status_code != status_code:
      verbose_codes = [
          httplib.FOUND,
      ]
      message_codes = [
          httplib.FORBIDDEN, httplib.BAD_REQUEST, httplib.NOT_FOUND,
      ]
      url_codes = [httplib.NOT_FOUND]

      if response.status_code in verbose_codes:
        print response

      if response.context and response.status_code in message_codes:
        try:
          print response.context['message']
        except KeyError:
          pass

      if response.status_code in url_codes:
        print response.request['PATH_INFO']

    self.assertEqual(status_code, response.status_code)

  def assertResponseOK(self, response):
    """Asserts that the response status is OK.

    Args:
      response: Django's http.HttpResponse object.
    """
    self.assertResponseCode(response, httplib.OK)

  def assertResponseRedirect(self, response, url=None):
    """Asserts that the response status is FOUND.

    Args:
      response: Django's http.HttpResponse object.
      url: expected URL to which the response should redirect.
    """
    self.assertResponseCode(response, httplib.FOUND)
    if url:
      url = "http://testserver" + url
      self.assertEqual(url, response["Location"])

  def assertResponseForbidden(self, response):
    """Asserts that the response status is FORBIDDEN.

    Does not raise an error if dev_test is set.

    Args:
      response: Django's http.HttpResponse object.
    """
    if self.dev_test:
      return
    self.assertResponseCode(response, httplib.FORBIDDEN)

  def assertResponseBadRequest(self, response):
    """Asserts that the response status is BAD_REQUEST.
    """
    self.assertResponseCode(response, httplib.BAD_REQUEST)

  def assertResponseNotFound(self, response):
    """Asserts that the response status is NOT_FOUND.

    Args:
      response: Django's http.HttpResponse object.
    """

    self.assertResponseCode(response, httplib.NOT_FOUND)

  def assertResponseMethodNotAllowed(self, response):
    """Asserts that the response status is NOT_FOUND.

    Args:
      response: Django's http.HttpResponse object.
    """
    self.assertResponseCode(response, httplib.METHOD_NOT_ALLOWED)

  def assertIsJsonResponse(self, response):
    """Asserts that all the templates from the base view were used.

    Args:
      response: Django's http.HttpResponse object.
    """
    self.assertResponseOK(response)
    self.assertEqual('application/json', response['Content-Type'])
    self.assertTemplateUsed(response, 'json_marker.html')

  def assertPropertiesEqual(self, properties, entity):
    """Asserts that all properties are set on the specified entity.

    Reference properties are compared by their key.
    Any date/time objects are ignored.
    """
    errors = []

    for key, value in properties.iteritems():
      if key == 'key_name':
        prop = entity.key().name()
      elif key == 'parent':
        prop = entity.parent()
      else:
        prop = getattr(entity, key)

      if isinstance(value, db.Model) or isinstance(prop, db.Model):
        value = repr(value.key()) if value else value
        prop = repr(prop.key()) if prop else prop

      if isinstance(value, datetime.date) or isinstance(value, datetime.time):
        continue

      msg = "property %s: '%r' != '%r'" % (key, value, prop)

      try:
        self.assertEqual(value, prop, msg=msg)
      except AssertionError:
        errors.append(msg)

    if errors:
      self.fail("\n".join(errors))

  def assertEmailSent(
      self, to=None, cc=None, bcc=None, sender=None, subject=None,
      body=None, html=None):
    """Tests that an email with the specified attributes has been sent.

    Args:
      to: Recipient of the emial.
      cc: CC recipient of the email.
      bcc: BCC recipients of the email.
      sender: Sender of the email.
      subject: Subject of the email.
      body: Body required to be included in the email.
      html: HTML (body) required to be included in the email.
    """
    # some tasks might have been sent via 'mail' task queue
    # so let us execute all pending tasks to make sure they are not waiting
    self.executeTasks(mailer.SEND_MAIL_URL, 'mail')

    # get_sent_messages function treats subject as regex pattern
    subject = subject and re.escape(subject)

    mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
    messages = mail_stub.get_sent_messages(
        to=to, sender=sender, subject=subject, body=body, html=html)

    # unfortunately, the returned by get_sent_messages EmailMessage objects
    # does not offer an option to easily filter messages by CC or BCC
    # the workaround is to transform messages back to PB
    if cc is not None:
      messages = [m for m in messages if filter(
          lambda cc_recipient: re.search(cc, cc_recipient),
          m.ToProto().cc_list())]

    if bcc is not None:
      messages = [m for m in messages if filter(
          lambda bcc_recipient: re.search(bcc, bcc_recipient),
          m.ToProto().bcc_list())]

    if not messages:
      failure_message = 'Expected e-mail message sent.'

      details = []
      if to is not None:
        details.append('To: %s' % to)
      if sender is not None:
        details.append('From: %s' % sender)
      if cc is not None:
        details.append('CC: %s' % cc)
      if bcc is not None:
        details.append('BCC: %s' % bcc)
      if subject is not None:
        details.append('Subject: %s' % subject)
      if body is not None:
        details.append('Body (contains): %s' % body)
      if html is not None:
        details.append('HTML (appends): %s' % html)

      if details:
        failure_message += ' Expected arguments: %s' % ', '.join(details)

      self.fail(failure_message)

  def executeTasks(self, url, queue_names=None):
    """Executes tasks with specified URL in specified task queues.

    Args:
      url: URL associated with the task to run.
      queue_names: Names of the task queues by which the tasks should be
        executed.
    """
    taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names=queue_names)

    for queue_name in queue_names:
      taskqueue_stub.FlushQueue(queue_name)

    for task in tasks:
      postdata = urlparse.parse_qs(task.payload)
      postdata.update(xsrf_token=self.getXsrfToken(path=url, data=postdata))
      # Run the task with Django test client
      self.post(url, postdata)


class GSoCDjangoTestCase(DjangoTestCase, GSoCTestCase):
  """DjangoTestCase specifically for GSoC view tests.
  """

  def init(self):
    """Performs test setup.
    """
    # Initialize instances in the parent first
    super(GSoCDjangoTestCase, self).init()

  def createOrg(self, override={}):
    """Creates an organization for the defined properties.
    """
    from soc.modules.gsoc.models.organization import GSoCOrganization

    properties = {'scope': self.gsoc, 'status': 'active',
                  'scoring_disabled': False, 'max_score': 5,
                  'home': None, 'program': self.gsoc}
    properties.update(override)
    return self.seed(GSoCOrganization, properties)

  def createDocument(self, override={}):
    return self.createDocumentForPrefix('gsoc_program', override)

  def assertGSoCTemplatesUsed(self, response):
    """Asserts that all the templates from the base view were used.

    Args:
      response: Django's http.HttpResponse object.
    """
    self.assertTemplateUsed(response, 'modules/gsoc/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/footer.html')
    self.assertTemplateUsed(response, 'modules/gsoc/header.html')
    self.assertTemplateUsed(response, 'modules/gsoc/mainmenu.html')


class GCIDjangoTestCase(DjangoTestCase, GCITestCase):
  """DjangoTestCase specifically for GCI view tests.
  """

  def init(self):
    """Performs test setup.
    """
    # Initialize instances in the parent first
    super(GCIDjangoTestCase, self).init()
    super(GCIDjangoTestCase, self).init()

  def assertGCITemplatesUsed(self, response):
    """Asserts that all the templates from the base view were used.

    Args:
      response: Django's http.HttpResponse object.
    """
    self.assertResponseOK(response)
    for contexts in response.context:
      for context in contexts:
        for value in context.values():
          # make it easier to debug render failures
          if isinstance(value, template.Template):
            value.render()
    self.assertTemplateUsed(response, 'modules/gci/base.html')
    self.assertTemplateUsed(response, 'modules/gci/_footer.html')
    self.assertTemplateUsed(response, 'modules/gci/_header.html')
    self.assertTemplateUsed(response, 'modules/gci/_mainmenu.html')

  def createDocument(self, override={}):
    return self.createDocumentForPrefix('gci_program', override)


class TaskQueueTestCase(gaetestbed.taskqueue.TaskQueueTestCase,
                        unittest.TestCase):
  """Class extending gaetestbed.taskqueue.TaskQueueTestCase.

  Difference:
  * Subclass unittest.TestCase so that all its subclasses need not subclass
  unittest.TestCase in their code.
  """

  def setUp(self):
    """Sets up gaetestbed.taskqueue.TaskQueueTestCase.
    """

    super(TaskQueueTestCase, self).setUp()


class FakeBlobstoreMiddleware(object):
  """Middleware class to pre-process file uploads so that they are accessible
  by test functions.

  Actual files cannot be handled properly by the regular, as Django does not
  recognize them as Blob uploads, as in production or on devappserver they
  are first processed by AppEngine.

  This class manually finds file uploads by checking if there is 'filename'
  element in their Content-Disposition header. Mock BlobInfo instances
  are added to the processed request so that actual views see them.
  """

  def process_request(self, request):
    """Processes request by handling all possible file uploads.

    It implements a hook for Django middleware as described in its
    documentation.

    Args:
      request: A django.http.HttpRequest.
    """
    request.file_uploads = {}

    # we only care about POST and which has form data with file.
    if request.method == 'POST' and (
        'multipart/form-data' in request.META.get('CONTENT_TYPE', '')):

      testbed = request.META[TESTBED_ARG_KEY]
      wsgi_input = request.META['wsgi.input']
      wsgi_input.seek(0)

      fields = cgi.FieldStorage(wsgi_input, environ=request.META)

      for key in fields:
        field = fields[key]
        if isinstance(field, cgi.FieldStorage):
          if ('content-disposition' in field.headers and 
              'filename' in field.disposition_options):

            # create a mock blob info and assign it to request data
            filename = field.disposition_options['filename']
            blob_info = testbed.get_stub('blobstore').CreateBlob(
                filename, 'fake content')

            # set other properties of blob info
            blob_info['filename'] = filename
            blob_info['content_type'] = field.headers['content-type']
            datastore.Put(blob_info)

            # set request data
            request.file_uploads[key] = blob_info
            request.POST[key] = filename

            # format blob info for Django by adding the name property.
            blob_info.name = field.disposition_options['filename']
            blob_info.size = blob_info['size']
