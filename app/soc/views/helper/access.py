#!/usr/bin/python2.5
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

"""Access control helper.

The functions in this module can be used to check access control
related requirements. When the specified required conditions are not
met, an exception is raised. This exception contains a views that
either prompts for authentication, or informs the user that they
do not meet the required criteria.
"""

__authors__ = [
  '"Todd Larsen" <tlarsen@google.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  '"Pawel Solyga" <pawel.solyga@gmail.com>',
  ]


from google.appengine.api import users

from django.utils.translation import ugettext_lazy
from django.core import urlresolvers

from soc.logic import accounts
from soc.logic import dicts
from soc.logic.models import host as host_logic
from soc.logic.models import notification as notification_logic
from soc.logic.models import user as user_logic
from soc.logic.models import request as request_logic
from soc.views import helper
from soc.views import out_of_band


DEF_NO_USER_LOGIN_MSG_FMT = ugettext_lazy(
  'Please create <a href="/user/edit">User Profile</a>'
  ' in order to view this page.')

DEF_DEV_LOGOUT_LOGIN_MSG_FMT = ugettext_lazy(
  'Please <a href="%%(sign_out)s">sign out</a>'
  ' and <a href="%%(sign_in)s">sign in</a>'
  ' again as %(role)s to view this page.')

DEF_PAGE_DENIED_MSG = ugettext_lazy(
  'Access to this page has been restricted')

DEF_LOGOUT_MSG_FMT = ugettext_lazy(
    'Please <a href="%(sign_out)s">sign out</a> in order to view this page')


def checkAccess(access_type, request, rights):
  """Runs all the defined checks for the specified type.

  Args:
    access_type: the type of request (such as 'list' or 'edit')
    request: the Django request object
    rights: a dictionary containing access check functions

  Rights usage: 
    The rights dictionary is used to check if the current user is allowed 
    to view the page specified. The functions defined in this dictionary 
    are always called with the django request object as argument. On any 
    request, regardless of what type, the functions in the 'any_access' value 
    are called. If the specified type is not in the rights dictionary, all 
    the functions in the 'unspecified' value are called. When the specified 
    type _is_ in the rights dictionary, all the functions in that access_type's 
    value are called.

  Returns:
    True: If all the required access checks have been made successfully
    False: If a check failed, in this case self._response will contain
      the response provided by the failed access check.
  """

  # Call each access checker
  for check in rights['any_access']:
    check(request)

  if access_type not in rights:
    for check in rights['unspecified']:
      # No checks defined, so do the 'generic' checks and bail out
      check(request)
    return

  for check in rights[access_type]:
    check(request)


def allow(request):
  """Never returns an alternate HTTP response.

  Args:
    request: a Django HTTP request
  """

  return

def deny(request):
  """Returns an alternate HTTP response.

  Args:
    request: a Django HTTP request

  Returns: 
    a subclass of django.http.HttpResponse which contains the
    alternate response that should be returned by the calling view.
  """

  context = {}
  context['title'] = 'Access denied'

  raise out_of_band.AccessViolation(DEF_PAGE_DENIED_MSG, context=context)


def checkIsLoggedIn(request):
  """Returns an alternate HTTP response if Google Account is not logged in.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if the user is logged in, or a subclass of
    django.http.HttpResponse which contains the alternate response
    that should be returned by the calling view.
  """

  if users.get_current_user():
    return

  raise out_of_band.LoginRequest()


def checkNotLoggedIn(request):
  """Returns an alternate HTTP response if Google Account is not logged in.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if the user is logged in, or a subclass of
    django.http.HttpResponse which contains the alternate response
    that should be returned by the calling view.
  """

  if not users.get_current_user():
    return

  raise out_of_band.LoginRequest(message_fmt=DEF_LOGOUT_MSG_FMT)


def checkIsUser(request):
  """Returns an alternate HTTP response if Google Account has no User entity.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if User exists for a Google Account, or a subclass of
    django.http.HttpResponse which contains the alternate response
    should be returned by the calling view.
  """

  checkIsLoggedIn(request)

  user = user_logic.logic.getForFields(
      {'account': users.get_current_user()}, unique=True)

  if user:
    return

  raise out_of_band.LoginRequest(message_fmt=DEF_NO_USER_LOGIN_MSG_FMT)


def checkIsDeveloper(request):
  """Returns an alternate HTTP response if Google Account is not a Developer.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if Google Account is logged in and logged-in user is a Developer,
    or a subclass of django.http.HttpResponse which contains the alternate
    response should be returned by the calling view.
  """

  checkIsUser(request)

  if accounts.isDeveloper(account=users.get_current_user()):
    return

  login_message_fmt = DEF_DEV_LOGOUT_LOGIN_MSG_FMT % {
      'role': 'a site developer '}

  raise out_of_band.LoginRequest(message_fmt=login_message_fmt)


def checkIsHost(request):
  """Returns an alternate HTTP response if Google Account has no Host entity
     for the specified program.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if Host exists for the specified program, or a subclass of
    django.http.HttpResponse which contains the alternate response
    should be returned by the calling view.
  """

  try:
    # if the current user is invited to create a host profile we allow access
    checkIsInvited(request)
    return
  except out_of_band.Error:
    pass

  checkIsUser(request)

  user = user_logic.logic.getForFields(
      {'account': users.get_current_user()}, unique=True)

  host = host_logic.logic.getForFields(
      {'user': user}, unique=True)

  if host:
    return

  login_message_fmt = DEF_DEV_LOGOUT_LOGIN_MSG_FMT % {
      'role': 'a host '}

  raise out_of_band.LoginRequest(message_fmt=login_message_fmt)


def checkIsInvited(request):
  """Returns an alternate HTTP response if Google Account has no Host entity
     for the specified program.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if Host exists for the specified program, or a subclass of
    django.http.HttpResponse which contains the alternate response
    should be returned by the calling view.
  """

  try:
    # if the current user is a developer we allow access
    checkIsDeveloper(request)
    return
  except out_of_band.Error:
    pass

  checkIsUser(request)

  login_message_fmt = DEF_DEV_LOGOUT_LOGIN_MSG_FMT % {
      'role': 'a host for this program'}

  splitpath = request.path.split('/')
  splitpath = splitpath[1:] # cut off leading ''

  if len(splitpath) < 4:
    # TODO: perhaps this needs a better explanation?
    deny(request)

  role = splitpath[0]
  group_id = splitpath[2]
  user_id = splitpath[3]

  user = user_logic.logic.getForFields(
      {'account': users.get_current_user()}, unique=True)

  if user_id != user.link_id:
    # TODO: perhaps this needs a better explanation?
    deny(request)

  properties = {
      'link_id': user_id,
      'role': role,
      'scope_path': group_id,
      'group_accepted': True,
      }

  request = request_logic.logic.getForFields(properties, unique=True)

  if request:
    return

  raise out_of_band.LoginRequest(message_fmt=login_message_fmt)

def checkIsMyNotification(request):
  """Returns an alternate HTTP response if this request is for a Notification belonging
     to the current user.

  Args:
    request: a Django HTTP request

   Raises:
     AccessViolationResponse: if the required authorization is not met

  Returns:
    None if the current User is allowed to access this Notification.
  """
  
  try:
    # if the current user is a developer we allow access
    checkIsDeveloper(request)
    return
  except out_of_band.Error:
    pass

  checkIsUser(request)
  
  splitpath = request.path.split('/')
  splitpath = splitpath[1:] # cut off leading ''
  
  # get the notification scope (user link_id) from the request path
  user_link_id = splitpath[2]
  # get the notification link_id from the request path
  notification_link_id = splitpath[3]
  
  properties = {
      'link_id': notification_link_id,
      'scope_path': user_link_id,
      }
  
  notification = notification_logic.logic.getForFields(properties, unique=True)
  
  user = user_logic.logic.getForCurrentAccount()
  
  # check if the key of the current user matches the key from the scope of the message
  if user.key() == notification.scope.key():
    # access granted
    return None
  else:
    # access denied
    deny(request)  

def checkCanInvite(request):
  """Checks to see if the current user can create an invite

  Note that if the current url is not in the default 'request' form
  this method either deny()s or performs the wrong access check.

  Args:
    request: a Django HTTP request
  """

  try:
    # if the current user is a developer we allow access
    checkIsDeveloper(request)
    return
  except out_of_band.Error:
    pass

  # Mine the url for params
  try:
    callback, args, kwargs = urlresolvers.resolve(request.path)
  except Exception:
    deny(request)

  # Construct a new url by reshufling the kwargs
  order = ['role', 'access_type', 'scope_path', 'link_id']
  url_params = dicts.unzip(kwargs, order)
  url = '/'.join([''] + list(url_params))

  # Mine the reshufled url
  try:
    callback, args, kwargs = urlresolvers.resolve(url)
  except Exception:
    deny(request)

  # Get the everything we need for the access check
  params = callback.im_self.getParams()
  access_type = kwargs['access_type']

  # Perform the access check
  helper.access.checkAccess(access_type, request, rights=params['rights'])

def checkIsDocumentPublic(request):
  """Checks whether a document is public.

  Args:
    request: a Django HTTP request
  """

  # TODO(srabbelier): A proper check needs to be done to see if the document
  # is public or not, probably involving analysing it's scope or such.
  allow(request)
