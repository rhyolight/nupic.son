# Copyright 2010 the Melange authors.
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

"""Tasks related to accepting and rejecting student proposals"""

import datetime
import logging
import urllib

from django import http
from django.conf.urls import url as django_url

from google.appengine.api import taskqueue
from google.appengine.datastore import datastore_query
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.runtime import DeadlineExceededError

from melange.models import organization as org_model

from soc.logic import dicts
from soc.logic import mail_dispatcher
from soc.tasks.helper.timekeeper import Timekeeper
from soc.tasks.helper import error_handler
from soc.tasks import responses

from soc.modules.gsoc.logic import accept_proposals as conversion_logic
from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.proposal import GSoCProposal

from summerofcode.models import organization as soc_org_model


class ProposalAcceptanceTask(object):
  """Request handlers for accepting and rejecting proposals in form of a Task.
  """

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module
    """
    patterns = [
        django_url(r'^tasks/gsoc/accept_proposals/main$', self.convertProposals),
        django_url(r'^tasks/gsoc/accept_proposals/accept$', self.acceptProposals),
        django_url(r'^tasks/gsoc/accept_proposals/status$', self.status),
        django_url(r'^tasks/gsoc/accept_proposals/reject$', self.rejectProposals)]
    return patterns

  def convertProposals(self, request, *args, **kwargs):
    """Start tasks to convert proposals for all organizations.

    POST Args:
      program_key: the key of the program whose proposals should be converted
      org_cursor: the cursor indicating at which org we currently are
    """
    params = dicts.merge(request.POST, request.GET)

    if 'program_key' not in params:
      logging.error("missing program_key in params: '%s'", params)
      return responses.terminateTask()

    program = GSoCProgram.get_by_key_name(params['program_key'])

    if not program:
      logging.error("invalid program_key in params: '%s'", params)
      return responses.terminateTask()

    query = soc_org_model.SOCOrganization.query(
        soc_org_model.SOCOrganization.program ==
            ndb.Key.from_old_key(program.key()),
        soc_org_model.SOCOrganization.status == org_model.Status.ACCEPTED)

    org_cursor = params.get('org_cursor')
    start_cursor = (
        datastore_query.Cursor(urlsafe=urllib.unquote_plus(org_cursor))
        if org_cursor else None)

    # Add a task for a single organization
    organizations, next_cursor, _ = query.fetch_page(
        1, start_cursor=start_cursor)

    if organizations:
      organization = organizations[0]
      logging.info(
          'Enqueing task to accept proposals for %s.', organization.name)
      # Compounded accept/reject taskflow
      taskqueue.add(
        url='/tasks/gsoc/accept_proposals/accept',
        params={
          'org_key': organization.key.id(),
        })

      # Enqueue a new task to do the next organization
      params['org_cursor'] = next_cursor.urlsafe()
      taskqueue.add(url=request.path, params=params)

    # Exit this task successfully
    return responses.terminateTask()

  def acceptProposals(self, request, *args, **kwargs):
    """Accept proposals for an single organization.

    POST Args:
      org_key: The key of the organization
    """
    params = request.POST

    # Setup an artifical request deadline
    timekeeper = Timekeeper(20000)

    # Query proposals based on status
    org = soc_org_model.SOCOrganization.get_by_id(params['org_key'])
    proposals = proposal_logic.getProposalsToBeAcceptedForOrg(org)

    # Accept proposals
    try:
      for remain, proposal in timekeeper.iterate(proposals):
        logging.info("accept %s %s %s", remain, org.key.id(), proposal.key())
        self.acceptProposal(proposal)
    # Requeue this task for continuation
    except DeadlineExceededError:
      taskqueue.add(url=request.path, params=params)
      return responses.terminateTask()

    # Reject remaining proposals
    taskqueue.add(url='/tasks/gsoc/accept_proposals/reject', params=params)
    return responses.terminateTask()

  def rejectProposals(self, request, *args, **kwargs):
    """Reject proposals for an single organization.
    """
    params = request.POST

    # Setup an artifical request deadline
    timekeeper = Timekeeper(20000)

    # Query proposals
    org = soc_org_model.SOCOrganization.get_by_id(params['org_key'])
    q = GSoCProposal.all()
    q.filter('org', org.key.to_old_key())
    q.filter('status', 'pending')

    # Reject proposals
    try:
      for remain, proposal in timekeeper.iterate(q):
        logging.info("reject %s %s %s", remain, org.key.id(), proposal.key())
        self.rejectProposal(proposal)
    # Requeue this task for continuation
    except DeadlineExceededError:
      taskqueue.add(url=request.path, params=params)

    # Exit this task successfully
    return responses.terminateTask()

  def status(self, request, *args, **kwargs):
    """Update the status of proposals conversion.

    Expects the following to be present in the POST dict:
      program_key: Specifies the program key name for which to update the
                   conversion status
    Args:
      request: Django Request object
    """
    params = request.POST

    # retrieve the program_key from POST data
    program_key = params.get('program_key')

    if not program_key:
      # invalid task data, log and return OK
      return error_handler.logErrorAndReturnOK(
          '"Missing program_key in params: "%s"' % params)

    # get the program for the given keyname
    program_entity = GSoCProgram.get_by_key_name(program_key)

    if not program_entity:
      # invalid program specified, log and return OK
      return error_handler.logErrorAndReturnOK(
          'Invalid program key specified: "%s"' % program_key)

    # obtain the accept proposals status
    aps_entity = conversion_logic.getOrCreateStatusForProgram(program_entity)

    # update the accept proposals status
    aps_entity.status = 'proceeded'

    # if the first proposal set the started_on
    converted_projects = aps_entity.nr_converted_projects + 1
    if converted_projects == 1:
      aps_entity.started_on = datetime.datetime.now()

    # tracks the number of converted projects so far
    aps_entity.nr_converted_projects = converted_projects

    db.put(aps_entity)

    # return OK
    return http.HttpResponse()

  # Logic below ported from student_proposal_mailer.py
  def getAcceptProposalMailTxn(self, proposal, transactional=True):
    """Returns the function to sent an acceptance mail for the specified
    proposal.
    """
    sender_name, sender = mail_dispatcher.getDefaultMailSender()

    student_entity = ndb.Key.from_old_key(proposal.parent_key()).get()

    org_key = GSoCProposal.org.get_value_for_datastore(proposal)
    org = ndb.Key.from_old_key(org_key).get()
    program_entity = proposal.program

    context = {
      'to': student_entity.contact.email,
      'to_name': student_entity.first_name,
      'sender': sender,
      'sender_name': sender_name,
      'program_name': program_entity.name,
      'subject': 'Congratulations!',
      'proposal_title': proposal.title,
      'org_entity': org,
      }

    messages = program_entity.getProgramMessages()
    template_string = messages.accepted_students_msg

    return mail_dispatcher.getSendMailFromTemplateStringTxn(
        template_string, context, parent=student_entity,
        transactional=transactional)

  def getWelcomeMailTxn(self, proposal, transactional=True):
    """Returns the function to sent an welcome email for an accepted proposal.
    """
    sender_name, sender = mail_dispatcher.getDefaultMailSender()

    student_entity = ndb.Key.from_old_key(proposal.parent_key()).get()
    program_entity = proposal.program

    context = {
      'to': student_entity.contact.email,
      'to_name': student_entity.first_name,
      'sender': sender,
      'sender_name': sender_name,
      'program_name': program_entity.name,
      'subject': 'Welcome to %s' % program_entity.name,
      }

    messages = program_entity.getProgramMessages()
    template_string = messages.accepted_students_welcome_msg

    return mail_dispatcher.getSendMailFromTemplateStringTxn(
        template_string, context, parent=student_entity,
        transactional=transactional)

  def getRejectProposalMailTxn(self, proposal):
    """Returns the function to sent an rejectance mail for the specified
    proposal.
    """
    sender_name, sender = mail_dispatcher.getDefaultMailSender()

    student_entity = ndb.Key.from_old_key(proposal.parent_key()).get()

    org_key = GSoCProposal.org.get_value_for_datastore(proposal)
    org = ndb.Key.from_old_key(org_key).get()

    program_entity = proposal.program

    context = {
      'to': student_entity.contact.email,
      'to_name': student_entity.first_name,
      'sender': sender,
      'sender_name': sender_name,
      'proposal_title': proposal.title,
      'program_name': program_entity.name,
      'subject': 'Thank you for applying to %s' % (program_entity.name),
      'org_entity': org,
      }

    messages = program_entity.getProgramMessages()
    template_string = messages.rejected_students_msg

    return mail_dispatcher.getSendMailFromTemplateStringTxn(
        template_string, context, parent=student_entity)

  def acceptProposal(self, proposal, transactional=True):
    """Accept a single proposal.

    Args:
      proposal: The GSoCProposal entity to accept.
      transactional: Whether the mail task should run transactionally.
    """
    accepted_mail_txn = self.getAcceptProposalMailTxn(
        proposal, transactional=transactional)
    welcome_mail_txn = self.getWelcomeMailTxn(
        proposal, transactional=transactional)

    proposal_key = proposal.key()

    # pass these data along params as POST to the new task
    task_params = {'program_key': proposal.program.key().id_or_name()}
    task_url = '/tasks/gsoc/accept_proposals/status'

    status_task = taskqueue.Task(params=task_params, url=task_url)

    def acceptProposalTxn():
      """Transaction that puts the new project, sets the proposal to accepted
      and mails the lucky student.
      """

      # add a task that performs conversion status per proposal
      # TODO(daniel): run in transaction when proposal and project are NDB
      # status_task.add(transactional=transactional)
      status_task.add(transactional=False)

      proposal = db.get(proposal_key)
      proposal_logic.acceptProposal(proposal)

      accepted_mail_txn()
      welcome_mail_txn()

    # TODO(daniel): run in transaction when proposal and project are NDB
    # db.RunInTransaction(acceptProposalTxn)
    acceptProposalTxn()

  def rejectProposal(self, proposal):
    """Rejects a single proposal.

    Args:
      proposal: proposal entity
    """
    mail_txn = self.getRejectProposalMailTxn(proposal)
    proposal_key = proposal.key()

    def rejectProposalTxn():
      """Transaction that sets the proposal to rejected and mails the student.
      """
      proposal = db.get(proposal_key)
      proposal_logic.rejectProposal(proposal)

      mail_txn()

    # TODO(daniel): run in transaction when proposal and project are NDB
    # db.RunInTransaction(rejectProposalTxn)
    rejectProposalTxn()
