#!/usr/bin/env python2.5
#
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

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  '"John Westbrook" <johnwestbrook@google.com>',
  ]


import logging

from django.conf.urls.defaults import url

from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.runtime import DeadlineExceededError

from soc.logic import dicts
from soc.logic import mail_dispatcher
from soc.tasks.helper.timekeeper import Timekeeper
from soc.tasks import responses

from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.proposal import GSoCProposal

class ProposalAcceptanceTask:
  """Request handlers for accepting and rejecting proposals in form of a Task.
  """

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module
    """
    patterns = [
        url(r'tasks/gsoc/accept_proposals/main$', self.convertProposals),
        url(r'tasks/gsoc/accept_proposals/accept$', self.acceptProposals),
        url(r'tasks/gsoc/accept_proposals/reject$', self.rejectProposals)]
    return patterns

  def convertProposals(self, request, *args, **kwargs):
    """Start tasks to convert proposals for all organizations.

    POST Args:
      program_key: the key of the program whose proposals should be converted
      org_cursor: the cursor indicating at which org we currently are
    """
    params = dicts.merge(request.POST, request.GET)

    if 'program_key' not in params:
      logging.error("missing program_key in params: '%s'" %params)
      return responses.terminateTask()

    program = GSoCProgram.get_by_key_name(params['program_key'])

    if not program:
      logging.error("invalid program_key in params: '%s'" %params)
      return responses.terminateTask()

    q = GSoCOrganization.all()
    q.filter('scope', program)
    q.filter('status', 'active')

    # Continue from the next organization
    if 'org_cursor' in params:
      q.with_cursor(params['org_cursor'])

    # Add a task for a single organization
    org = q.get()

    if org:
      logging.info('Enqueing task to accept proposals for %s.' %org.name)
      # Compounded accept/reject taskflow
      taskqueue.add(
        url = '/tasks/gsoc/accept_proposals/accept',
        params = {
          'org_key': org.key().id_or_name(),
        })

      # Enqueue a new task to do the next organization
      params['org_cursor'] = q.cursor()
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
    org = GSoCOrganization.get_by_key_name(params['org_key'])
    proposals = proposal_logic.getProposalsToBeAcceptedForOrg(org)

    # Accept proposals
    try:
      for remain, proposal in timekeeper.iterate(proposals):
        logging.info("accept %s %s %s", remain, org.key(), proposal.key())
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
    org = GSoCOrganization.get_by_key_name(params['org_key'])
    q = GSoCProposal.all()
    q.filter('org', org)
    q.filter('status', 'pending')

    # Reject proposals
    try:
      for remain, proposal in timekeeper.iterate(q):
        logging.info("reject %s %s %s", remain, org.key(), proposal.key())
        self.rejectProposal(proposal)
    # Requeue this task for continuation
    except DeadlineExceededError:
      taskqueue.add(url=request.path, params=params)
  
    # Exit this task successfully
    return responses.terminateTask()

  # Logic below ported from student_proposal_mailer.py
  def getAcceptProposalMailTxn(self, proposal):
    """Returns the function to sent an acceptance mail for the specified
    proposal.
    """
    sender_name, sender = mail_dispatcher.getDefaultMailSender()

    student_entity = proposal.parent()
    org_entity = proposal.org
    program_entity = proposal.program

    context = {
      'to': student_entity.email,
      'to_name': student_entity.given_name,
      'sender': sender,
      'sender_name': sender_name,
      'program_name': program_entity.name,
      'subject': 'Congratulations!',
      'proposal_title': proposal.title,
      'org_entity': org_entity,
      }

    template = 'v2/soc/notification/gsoc2011_accepted_student.html'
    return mail_dispatcher.getSendMailFromTemplateTxn(template, context,
                                                      parent=proposal.parent())

  def getRejectProposalMailTxn(self, proposal):
    """Returns the function to sent an rejectance mail for the specified
    proposal.
    """
    sender_name, sender = mail_dispatcher.getDefaultMailSender()

    student_entity = proposal.parent()
    org_entity = proposal.org
    program_entity = proposal.program

    context = {
      'to': student_entity.email,
      'to_name': student_entity.given_name,
      'sender': sender,
      'sender_name': sender_name,
      'proposal_title': proposal.title,
      'program_name': program_entity.name,
      'subject': 'Thank you for applying to %s' % (program_entity.name),
      'org_entity': org_entity,
      }

    template = 'modules/gsoc/student_proposal/mail/rejected_gsoc2010.html'
    return mail_dispatcher.getSendMailFromTemplateTxn(template, context,
                                                      parent=proposal.parent())

  def acceptProposal(self, proposal):
    """Accept a single proposal.

    Args:
      proposal: The GSoCProposal entity to accept.
    """
    fields = {
      'org': proposal.org,
      'program': proposal.program,
      'title': proposal.title,
      'abstract': proposal.abstract,
      'mentor': proposal.mentor,
      }
    student_profile = proposal.parent()
    project = GSoCProject(parent=student_profile, **fields)

    mail_txn = self.getAcceptProposalMailTxn(proposal)

    def acceptProposalTxn():
      """Transaction that puts the new project, sets the proposal to accepted
      and mails the lucky student.
      """
      db.put(project)
      proposal.status = 'accepted'
      db.put(proposal)
      mail_txn()

    db.RunInTransaction(acceptProposalTxn)

  def rejectProposal(self, proposal):
    """Reject a single proposal.
    """
    mail_txn = self.getRejectProposalMailTxn(proposal)

    def rejectProposalTxn():
      """Transaction that sets the proposal to rejected and mails the student.
      """
      proposal.status = 'rejected'
      db.put(proposal)
      mail_txn()

    db.RunInTransaction(rejectProposalTxn)
