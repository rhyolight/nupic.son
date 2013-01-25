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

"""Module containing the view for GCI request page."""

from google.appengine.ext import db

from soc.logic import exceptions
from soc.logic.helper import notifications

from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.helper.access_checker import isSet
from soc.views.template import Template

from soc.tasks import mailer

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.request import GCIRequest
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class RequestForm(gci_forms.GCIModelForm):
  """Django form for the invite page."""

  class Meta:
    model = GCIRequest
    css_prefix = 'gci_intivation'
    fields = ['message']

class SendRequestPage(GCIRequestHandler):
  """Encapsulate all the methods required to generate Send Request page."""

  def templatePath(self):
    return 'v2/modules/gci/request/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/send/%s$' % url_patterns.REQUEST,
            self, name=url_names.GCI_SEND_REQUEST)
    ]

  def checkAccess(self):
    """Access checks for GCI Send Request page.
    """
    #TODO(dhans): check if the program is visible
    self.check.isProfileActive()
    # check if the user is not a student
    # check if the user does not have role for the organization

  def context(self):
    """Handler to for GCI Send Request page HTTP get request.
    """
    request_form = RequestForm(self.data.POST or None)

    return {
        'logout_link': self.data.redirect.logout(),
        'forms': [request_form],
        'page_name': self._constructPageName()
        }

  def _constructPageName(self):
    role = 'Mentor' if self.data.kwargs['role'] == 'mentor' else 'Org Admin'
    return "Request to become %s" % role

  def validate(self):
    """Validates the form data.

    Returns a newly created request entity or None if an error occurs.
    """
    assert isSet(self.data.organization)

    request_form = RequestForm(self.data.POST)

    if not request_form.is_valid():
      return None

    request_form.cleaned_data['org'] = self.data.organization
    request_form.cleaned_data['role'] = self.data.kwargs['role']
    request_form.cleaned_data['type'] = 'Request'
    request_form.cleaned_data['user'] = self.data.user

    q = GCIProfile.all().filter('org_admin_for', self.data.organization)
    q = q.filter('status', 'active').filter('notify_new_requests', True)
    admins = q.fetch(1000)
    admin_emails = [i.email for i in admins]

    def create_request_txn():
      request = request_form.create(commit=True, parent=self.data.user)
      context = notifications.requestContext(self.data, request, admin_emails)
      sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
      sub_txn()
      return request

    return db.run_in_transaction(create_request_txn)

  def post(self):
    """Handler to for GCI Send Request Page HTTP post request."""
    request = self.validate()
    if request:
      return self.redirect.id(request.key().id()).to(
          url_names.GCI_MANAGE_REQUEST)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get()


class ManageRequestPage(GCIRequestHandler):
  """View to manage the invitation by the sender."""

  def templatePath(self):
    return 'v2/modules/gci/request/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/manage/%s$' % url_patterns.ID, self,
            name=url_names.GCI_MANAGE_REQUEST)
    ]

  def checkAccess(self):
    self.check.isProfileActive()

    request_id = int(self.data.kwargs['id'])
    self.data.request_entity = GCIRequest.get_by_id(
        request_id, parent=self.data.user)
    self.check.isRequestPresent(request_id)

    self.check.canManageRequest()

    # check if the submitted action is legal
    if self.data.POST:
      if 'withdraw' not in self.data.POST and 'resubmit' not in self.data.POST:
        raise exceptions.BadRequest(
            'Valid action is not specified in the request.')
      self.check.isRequestManageable()

  def context(self):
    page_name = self._constructPageName()

    form = RequestForm(
        self.data.POST or None, instance=self.data.request_entity)

    button_name = self._constructButtonName()
    button_value = self._constructButtonValue()

    return {
        'page_name': page_name,
        'forms': [form],
        'button_name': button_name,
        'button_value': button_value
        }

  def post(self):
    if 'withdraw' in self.data.POST:
      def withdraw_request_txn():
        request = db.get(self.data.request_entity.key())
        request.status = 'withdrawn'
        request.put()
      db.run_in_transaction(withdraw_request_txn)
    elif 'resubmit' in self.data.POST:
      def resubmit_request_txn():
        request = db.get(self.data.request_entity.key())
        request.status = 'pending'
        request.put()
      db.run_in_transaction(resubmit_request_txn)

    return self.redirect.id().to(url_names.GCI_MANAGE_REQUEST)

  def _constructPageName(self):
    request = self.data.request_entity
    return "%s Request To %s" % (request.role, request.org.name)

  def _constructButtonName(self):
    request = self.data.request_entity
    if request.status == 'pending':
      return 'withdraw'
    if request.status in ['withdrawn', 'rejected']:
      return 'resubmit'

  def _constructButtonValue(self):
    request = self.data.request_entity
    if request.status == 'pending':
      return 'Withdraw'
    if request.status in ['withdrawn', 'rejected']:
      return 'Resubmit'


class RespondRequestPage(GCIRequestHandler):
  """View to accept or reject requests by organization admins."""

  def templatePath(self):
    return 'v2/modules/gci/request/show.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/respond/%s$' % url_patterns.USER_ID, self,
            name=url_names.GCI_RESPOND_REQUEST)
    ]

  def checkAccess(self):
    self.check.isProfileActive()

    key_name = self.data.kwargs['user']
    user_key = db.Key.from_path('User', key_name)

    # fetch the request entity based on the id and parent key
    request_id = int(self.data.kwargs['id'])
    self.data.request_entity = GCIRequest.get_by_id(
        request_id, parent=user_key)
    self.check.isRequestPresent(request_id)

    # get the organization and check if the current user can manage the request
    self.data.organization = self.data.request_entity.org
    self.check.isOrgAdmin()

    self.data.is_respondable = self.data.request_entity.status == 'pending'

  def context(self):
    """Handler to for GCI Respond Request page HTTP get request.
    """
    return {
        'request': self.data.request_entity,
        'page_name': 'Respond to request',
        'is_respondable': self.data.is_respondable
        }

  def post(self):
    """Handler to for GCI Respond Request Page HTTP post request."""
    user_key = GCIRequest.user.get_value_for_datastore(
        self.data.request_entity)

    profile_key_name = '/'.join([
        self.data.program.key().name(), user_key.name()])
    profile_key = db.Key.from_path(
        'GCIProfile', profile_key_name, parent=user_key)

    self.data.requester_profile = profile = db.get(profile_key)

    if 'accept' in self.data.POST:
      options = db.create_transaction_options(xg=True)

      request_key = self.data.request_entity.key()
      organization_key = self.data.organization.key()
      messages = self.data.program.getProgramMessages()

      def accept_request_txn():
        request = db.get(request_key)

        request.status = 'accepted'

        profile.is_mentor = True
        profile.mentor_for.append(organization_key)
        profile.mentor_for = list(set(profile.mentor_for))

        new_mentor = not profile.is_mentor
        profile.is_mentor = True
        profile.mentor_for.append(organization_key)
        profile.mentor_for = list(set(profile.mentor_for))

        # Send out a welcome email to new mentors.
        if new_mentor:
          mentor_mail = notifications.getMentorWelcomeMailContext(
              profile, self.data, messages)
          if mentor_mail:
            mailer.getSpawnMailTaskTxn(mentor_mail, parent=request)()

        profile.put()
        request.put()

        context = notifications.handledRequestContext(self.data, request.status)
        sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
        sub_txn()

      db.run_in_transaction_options(options, accept_request_txn)

    else: # reject
      def reject_request_txn():
        request = db.get(self.data.request_entity.key())
        request.status = 'rejected'
        request.put()

        context = notifications.handledRequestContext(self.data, request.status)
        sub_txn = mailer.getSpawnMailTaskTxn(context, parent=request)
        sub_txn()

      db.run_in_transaction(reject_request_txn)

    return self.redirect.userId(user_key.name()).to(
        url_names.GCI_RESPOND_REQUEST)


class UserRequestsList(Template):
  """Template for list of requests that have been sent by the current user.
  """

  def __init__(self, request, data):
    self.request = request
    self.data = data
    r = data.redirect

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('org', 'To',
        lambda entity, *args: entity.org.name)
    list_config.addSimpleColumn('status', 'Status')
    list_config.setRowAction(
        lambda e, *args: r.id(e.key().id())
            .urlOf(url_names.GCI_MANAGE_REQUEST))

    self._list_config = list_config

  def getListData(self):
    q = GCIRequest.all()
    q.filter('type', 'Request')
    q.filter('user', self.data.user)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, lists.keyStarter)

    return response_builder.build()

  def context(self):
    request_list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0)

    return {
        'lists': [request_list],
    }

  def templatePath(self):
    return 'v2/modules/gci/request/_request_list.html'


class ListUserRequestsPage(GCIRequestHandler):
  """View for the page that lists all the requests which have been sent by
  the current user.
  """

  def templatePath(self):
    return 'v2/modules/gci/request/request_list.html'

  def djangoURLPatterns(self):
    return [
        url(r'request/list_user/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_LIST_REQUESTS),
    ]

  def checkAccess(self):
    self.check.isProfileActive()

  def jsonContext(self):
    # TODO(nathaniel): Drop the first parameter of UserRequestsList.
    list_content = UserRequestsList(self.data.request, self.data).getListData()

    if not list_content:
      raise exceptions.AccessViolation('You do not have access to this data')

    return list_content.content()

  def context(self):
    return {
        'page_name': 'Your requests',
        'request_list': UserRequestsList(self.data.request, self.data),
    }
