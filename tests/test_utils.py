#!/usr/bin/env python2.5
#
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
"""Common testing utilities.
"""


__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  '"Augie Fackler" <durin42@gmail.com>',
  '"Leo (Chong Liu)" <HiddenPython@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import os
import datetime
import httplib
import StringIO
import unittest

import gaetestbed
from mox import stubout

from google.appengine.ext import db

from django.test import client
from django.test import TestCase

from soc.logic.helper import xsrfutil
from soc.middleware.xsrf import XsrfMiddleware
from soc.modules import callback


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


class DjangoTestCase(TestCase):
  """Class extending Django TestCase in order to extend its functions.

  As well as remove the functions which are not supported by Google App Engine,
  e.g. database flush and fixtures loading without the assistance of Google
  App Engine Helper for Django.
  """

  def _pre_setup(self):
    """Performs any pre-test setup.
    """
    client.FakePayload = NonFailingFakePayload

  def _post_teardown(self):
    """ Performs any post-test cleanup.
    """
    import os
    os.environ['USER_EMAIL'] = 'test@example.com'
    os.environ['USER_ID'] = '42'

  def init(self):
    """Performs test setup.

    Sets the following attributes:
      dev_test: True iff DEV_TEST is in environment
      founder: a founder instance
      sponsor: a sponsor instance
    """
    from soc.models.user import User
    from soc.models.sponsor import Sponsor

    self.dev_test = 'DEV_TEST' in os.environ

    properties = {}
    self.founder = self.seed(User, properties)

    properties = {'founder': self.founder, 'home': None}
    self.sponsor = self.seed(Sponsor, properties)

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

  def get(self, url):
    """Performs a get to the specified url.
    """
    response = self.client.get(url)
    return response

  def post(self, url, postdata={}):
    """Performs a post to the specified url with postdata.

    Takes care of setting the xsrf_token.
    """
    postdata['xsrf_token'] = self.getXsrfToken(url, site=self.site)
    response = self.client.post(url, postdata)
    postdata.pop('xsrf_token')
    return response

  def modelPost(self, url, model, properties):
    """Performs a post to the specified url after seeding for model.

    Calls post().
    """
    properties = self.seedProperties(model, properties)
    response = self.post(url, properties)
    return response, properties

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
    xsrf = XsrfMiddleware()
    key = xsrf._getSecretKey(request)
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
      data = response.context['data'][start]
      self.assertIsJsonResponse(response)
      result += data
      start = response.context['next']

    return result

  def assertErrorTemplatesUsed(self, response):
    """Assert that all the error templates were used.
    """
    self.assertNotEqual(response.status_code, httplib.OK)
    # TODO(SRabbelier): update this when we use an error template again
    # self.assertTemplateUsed(response, 'soc/error.html')

  def assertResponseCode(self, response, status_code):
    """Asserts that the response status is OK.
    """
    if response.status_code != status_code:
      verbose_codes = [
          httplib.BAD_REQUEST, httplib.NOT_FOUND, httplib.FOUND,
      ]
      message_codes = [httplib.FORBIDDEN]

      if response.status_code in verbose_codes:
        print response

      if response.status_code in message_codes:
        print response.context['message']

    self.assertEqual(status_code, response.status_code)

  def assertResponseOK(self, response):
    """Asserts that the response status is OK.
    """
    self.assertResponseCode(response, httplib.OK)

  def assertResponseRedirect(self, response, url=None):
    """Asserts that the response status is FOUND.
    """
    self.assertResponseCode(response, httplib.FOUND)
    if url:
      url = "http://testserver" + url
      self.assertEqual(url, response["Location"])

  def assertResponseForbidden(self, response):
    """Asserts that the response status is FORBIDDEN.

    Does not raise an error if dev_test is set.
    """
    if self.dev_test:
      return
    self.assertResponseCode(response, httplib.FORBIDDEN)

  def assertResponseBadRequest(self, response):
    """Asserts that the response status is BAD_REQUEST.
    """
    self.assertResponseCode(response, httplib.BAD_REQUEST)

  def assertIsJsonResponse(self, response):
    """Asserts that all the templates from the base view were used.
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
      except AssertionError, e:
        errors.append(msg)

    if errors:
      self.fail("\n".join(errors))


class GSoCDjangoTestCase(DjangoTestCase):
  """DjangoTestCase specifically for GSoC view tests.
  """

  def init(self):
    """Performs test setup.

    Sets the following attributes:
      dev_test: True iff DEV_TEST is in environment (in parent)
      founder: a founder instance (in parent)
      sponsor: a sponsor instance (in parent)
      gsoc: a GSoCProgram instance
      org_app: a OrgAppSurvey instance
      org: a GSoCOrganization instance
      timeline: a GSoCTimelineHelper instance
      data: a GSoCProfileHelper instance
    """
    from soc.models.site import Site
    from soc.models.document import Document
    from soc.modules.gsoc.models.program import GSoCProgram
    from soc.modules.gsoc.models.timeline import GSoCTimeline
    from soc.modules.seeder.logic.providers.string import DocumentKeyNameProvider
    from soc.models.org_app_survey import OrgAppSurvey
    from tests.timeline_utils import GSoCTimelineHelper
    from tests.profile_utils import GSoCProfileHelper

    # Initialize instances in the parent first
    super(GSoCDjangoTestCase, self).init()
    properties = {'scope': self.sponsor}
    self.program_timeline = self.seed(GSoCTimeline, properties)

    properties = {'timeline': self.program_timeline,
                  'status': 'visible', 'apps_tasks_limit': 20,
                  'scope': self.sponsor,
                  'student_agreement': None, 'events_page': None,
                  'help_page': None, 'connect_with_us_page': None,
                  'mentor_agreement': None, 'org_admin_agreement': None,
                  'terms_and_conditions': None, 'home': None, 'about_page': None}
    self.gsoc = self.seed(GSoCProgram, properties)

    properties = {
        'prefix': 'gsoc_program', 'scope': self.gsoc,
        'read_access': 'public', 'key_name': DocumentKeyNameProvider(),
        'modified_by': self.founder, 'author': self.founder,
        'home_for': None,
    }
    document = self.seed(Document, properties=properties)

    self.gsoc.about_page = document
    self.gsoc.events_page = document
    self.gsoc.help_page = document
    self.gsoc.connect_with_us_page = document
    self.gsoc.privacy_policy = document
    self.gsoc.put()

    self.site = Site(key_name='site', link_id='site',
                     active_program=self.gsoc)
    self.site.put()

    # TODO (Madhu): Remove scope and author fields once the data
    # conversion is done.
    properties = {'scope': self.gsoc, 'program': self.gsoc,
                  'modified_by': self.founder,
                  'created_by': self.founder,
                  'author': self.founder,
                  'survey_content': None,}
    self.org_app = self.seed(OrgAppSurvey, properties)

    self.org = self.createOrg()

    self.timeline = GSoCTimelineHelper(self.gsoc.timeline, self.org_app)
    self.data = GSoCProfileHelper(self.gsoc, self.dev_test)

  def createOrg(self, override={}):
    """Creates an organization for the defined properties.
    """
    from soc.modules.gsoc.models.organization import GSoCOrganization

    properties = {'scope': self.gsoc, 'status': 'active',
                  'scoring_disabled': False, 'max_score': 5,
                  'founder': self.founder,
                  'home': None,}
    properties.update(override)
    return self.seed(GSoCOrganization, properties)

  def assertGSoCTemplatesUsed(self, response):
    """Asserts that all the templates from the base view were used.
    """
    self.assertResponseOK(response)
    for contexts in response.context:
      for context in contexts:
        for value in context.values():
          # make it easier to debug render failures
          if hasattr(value, 'render'):
            value.render()
    self.assertTemplateUsed(response, 'v2/modules/gsoc/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/footer.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/header.html')
    self.assertTemplateUsed(response, 'v2/modules/gsoc/mainmenu.html')

  def assertGSoCColorboxTemplatesUsed(self, response):
    """Asserts that all the templates from the base_colorbox view were used.
    """
    self.assertResponseOK(response)
    for contexts in response.context:
      for context in contexts:
        for value in context.values():
          # make it easier to debug render failures
          if hasattr(value, 'render'):
            value.render()
    self.assertTemplateUsed(response, 'v2/modules/gsoc/base_colorbox.html')


class GCIDjangoTestCase(DjangoTestCase):
  """DjangoTestCase specifically for GCI view tests.
  """

  def init(self):
    """Performs test setup.

    Sets the following attributes:
      dev_test: True iff DEV_TEST is in environment (in parent)
      founder: a founder instance (in parent)
      sponsor: a sponsor instance (in parent)
      gci: a GCIProgram instance
      org_app: a OrgAppSurvey instance
      org: a GCIOrganization instance
      timeline: a GCITimelineHelper instance
      data: a GCIProfileHelper instance
    """
    from datetime import date
    from soc.models.site import Site
    from soc.models.document import Document
    from soc.modules.gci.models.program import GCIProgram
    from soc.modules.gci.models.timeline import GCITimeline
    from soc.modules.seeder.logic.providers.string import DocumentKeyNameProvider
    from soc.models.org_app_survey import OrgAppSurvey
    from tests.timeline_utils import GCITimelineHelper
    from tests.profile_utils import GCIProfileHelper

    # Initialize instances in the parent first
    super(GCIDjangoTestCase, self).init()
    properties = {'scope': self.sponsor}
    self.program_timeline = self.seed(GCITimeline, properties)

    properties = {
        'timeline': self.program_timeline,
        'status': 'visible',
        'scope': self.sponsor,
        'student_agreement': None, 'events_page': None,
        'help_page': None, 'connect_with_us_page': None,
        'mentor_agreement': None, 'org_admin_agreement': None,
        'terms_and_conditions': None, 'home': None, 'about_page': None,
        'nr_simultaneous_tasks': 5,
        'student_min_age': 13, 'student_max_age': 17,
        'student_min_age_as_of': date.today(),
        'task_difficulties': ['easy', 'moderate', 'hard'],
        'task_types': ['code', 'documentation', 'design'],
    }
    self.gci = self.seed(GCIProgram, properties)

    properties = {
        'prefix': 'gci_program', 'scope': self.gci,
        'read_access': 'public', 'key_name': DocumentKeyNameProvider(),
        'modified_by': self.founder, 'author': self.founder,
        'home_for': None,
    }
    document = self.seed(Document, properties=properties)

    self.gci.about_page = document
    self.gci.events_page = document
    self.gci.help_page = document
    self.gci.connect_with_us_page = document
    self.gci.privacy_policy = document
    self.gci.put()

    self.site = Site(key_name='site', link_id='site',
                     active_program=self.gci)
    self.site.put()

    # TODO (Madhu): Remove scope and author fields once the data
    # conversion is done.
    properties = {'scope': self.gci, 'program': self.gci,
                  'modified_by': self.founder,
                  'created_by': self.founder,
                  'author': self.founder,
                  'survey_content': None,}
    self.org_app = self.seed(OrgAppSurvey, properties)

    self.org = self.createOrg()

    self.timeline = GCITimelineHelper(self.gci.timeline, self.org_app)
    self.data = GCIProfileHelper(self.gci, self.dev_test)

  def createOrg(self, override={}):
    """Creates an organization for the defined properties.
    """
    from soc.modules.gci.models.organization import GCIOrganization

    properties = {'scope': self.gci, 'status': 'active',
                  'founder': self.founder,
                  'home': None,
                  'task_quota_limit': 100}
    properties.update(override)
    return self.seed(GCIOrganization, properties)

  def assertGCITemplatesUsed(self, response):
    """Asserts that all the templates from the base view were used.
    """
    self.assertResponseOK(response)
    for contexts in response.context:
      for context in contexts:
        for value in context.values():
          # make it easier to debug render failures
          if hasattr(value, 'render'):
            value.render()
    self.assertTemplateUsed(response, 'v2/modules/gci/base.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/_footer.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/_header.html')
    self.assertTemplateUsed(response, 'v2/modules/gci/_mainmenu.html')


def runTasks(url = None, name=None, queue_names = None):
  """Run tasks with specified url and name in specified task queues.
  """

  task_queue_test_case = gaetestbed.taskqueue.TaskQueueTestCase()
  # Get all tasks with specified url and name in specified task queues
  tasks = task_queue_test_case.get_tasks(url=url, name=name, 
                                         queue_names=queue_names)
  for task in tasks:
    postdata = task['params']
    xsrf_token = GSoCDjangoTestCase.getXsrfToken(url, data=postdata)
    postdata.update(xsrf_token=xsrf_token)
    client.FakePayload = NonFailingFakePayload
    c = client.Client()
    # Run the task with Django test client
    c.post(url, postdata)


class MailTestCase(gaetestbed.mail.MailTestCase, unittest.TestCase):
  """Class extending gaetestbed.mail.MailTestCase to extend its functions.

  Difference:
  * Subclass unittest.TestCase so that all its subclasses need not subclass
  unittest.TestCase in their code.
  * Override assertEmailSent method.
  """

  def setUp(self):
    """Sets up gaetestbed.mail.MailTestCase.
    """

    super(MailTestCase, self).setUp()

  def assertEmailSent(self, to=None, sender=None, subject=None,
                      body=None, html=None, n=None, fullbody=False):
    """Override gaetestbed.mail.MailTestCase.assertEmailSent method.

    Difference:
    * It prints out all sent messages to facilitate debug in case of failure.
    * It accepts an optional argument n which is used to assert exactly n
    messages satisfying the criteria are sent out.
    * Clips textbody to the first 50 characters, unless fullbody is True.
    """

    # Run all mail tasks first so that all mails will be sent out
    runTasks(url = '/tasks/mail/send_mail', queue_names = ['mail'])
    messages = self.get_sent_messages(
        to = to,
        sender = sender,
        subject = subject,
        body = body,
        html = html,
    )
    failed = False
    if not messages:
      failed = True
      failure_message = "Expected e-mail message sent. No messages sent"
      details = self._get_email_detail_string(to, sender, subject, body, html)
      if details:
        failure_message += ' with %s.' % details
      else:
        failure_message += '.'
    elif n:
      actual_n = len(messages)
      if n != actual_n:
        failed = True
        failure_message = ("Expected e-mail message sent."
                           "Expected %d messages sent" % n)
        details = self._get_email_detail_string(to, sender, subject, body, html)
        if details:
          failure_message += ' with %s;' % details
        else:
          failure_message += ';'
        failure_message += ' but actually %d.' % actual_n
    # If failed, raise error and display all messages sent
    if failed:
      all_messages = self.get_sent_messages()
      failure_message += '\nAll messages sent: '
      if all_messages:
        failure_message += '\n'
        for message in all_messages:
          if not fullbody:
            message.set_textbody(message.textbody()[:50])
            message.set_htmlbody(message.htmlbody()[:50])
          failure_message += str(message)
      else:
        failure_message += 'None'
      self.fail(failure_message)


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
