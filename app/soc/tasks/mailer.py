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

"""Task to send out an email message."""

import json
import logging

from google.appengine.api import datastore_errors
from google.appengine.api import mail
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine.runtime.apiproxy_errors import DeadlineExceededError

from django.conf.urls import url as django_url

from melange.appengine import system

# new style NDB model for email
from melange.models import email as ndb_email_model

# old style DB model for email
from soc.models import email as db_email_model
from soc.tasks import responses
from soc.tasks.helper import error_handler


SEND_MAIL_URL = '/tasks/mail/send_mail'


def getMailContext(to, subject, html, sender=None, bcc=None):
  """Constructs a mail context for the specified arguments.
  """
  if not sender:
    sender = system.getApplicationNoReplyEmail()

  context = {
      'subject': subject,
      'html': html,
      'sender': sender,
  }

  if to:
    context['to'] = to

  if bcc:
    context['bcc'] = bcc

  return context


# TODO(daniel): remove transactional argument
def getSpawnMailTaskTxn(context, parent=None, transactional=True):
  """Spawns a new Task that sends out an email with the given dictionary."""
  if not (context.get('to') or context.get('bcc')):
    context['body'] = context.get('body', '')[:10]
    logging.debug("Not sending email: '%s'", context)
    # no-one cares :(
    return lambda: None

  # TODO(daniel): drop this when DB models are not used anymore
  if not parent or isinstance(parent, db.Model):
    mail_entity = db_email_model.Email(
        context=json.dumps(context), parent=parent)
    transactional = ndb.in_transaction()
  else:
    mail_entity = ndb_email_model.Email(
        parent=parent.key, context=json.dumps(context))
    transactional = db.is_in_transaction()

  def txn():
    """Transaction to ensure that a task get enqueued for each mail stored.
    """
    mail_entity.put()

    if isinstance(mail_entity, db.Model):
      mail_entity_key = mail_entity.key()
    else:
      mail_entity_key = mail_entity.key.urlsafe()

    task_params = {'mail_key': str(mail_entity_key)}
    # Setting a countdown because the mail_entity might not be stored to
    # all the replicas yet.
    new_task = taskqueue.Task(params=task_params, url=SEND_MAIL_URL,
                              countdown=5)
    new_task.add(queue_name='mail', transactional=transactional)

  return txn


class MailerTask(object):
  """Request handler for mailer.
  """

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module.
    """
    return [
        django_url(r'^tasks/mail/send_mail$', self.sendMail,
                   name='send_email_task'),
    ]

  def sendMail(self, request):
    """Sends out an email that is stored in the datastore.

    The POST request should contain the following entries:
      mail_key: Datastore key for an Email entity.
    """
    post_dict = request.POST

    mail_key = post_dict.get('mail_key', None)

    if not mail_key:
      return error_handler.logErrorAndReturnOK('No email key specified')

    # TODO(daniel): so ugly...
    try:
      mail_entity = db.get(mail_key)
    except datastore_errors.BadKeyError:
      mail_entity = ndb.Key(urlsafe=mail_key).get()

    if not mail_entity:
      return error_handler.logErrorAndReturnOK(
          'No email entity found for key %s' % mail_key)

    # construct the EmailMessage from the given context
    loaded_context = json.loads(mail_entity.context)

    context = {}
    for key, value in loaded_context.iteritems():
      # If we don't do this python will complain about kwargs not being
      # strings.
      context[str(key)] = value

    logging.info('Sending %s', context)
    message = mail.EmailMessage(**context)

    try:
      message.check_initialized()
    except Exception as e:
      logging.exception(e)
      context['body'] = context.get('body', '')[:10]
      logging.error('This message was not properly initialized: "%s"', context)
      mail_entity.delete()
      return responses.terminateTask()

    def txn():
      """Transaction that ensures the deletion of the Email entity only if
      the mail has been successfully sent.
      """
      mail_entity.delete()
      message.send()

    try:
      db.RunInTransaction(txn)
    except mail.Error as exception:
      # shouldn't happen because validate has been called, keeping the Email
      # entity for study purposes.
      return error_handler.logErrorAndReturnOK(exception)
    except (OverQuotaError, DeadlineExceededError) as e:
      return responses.repeatTask()

    # mail successfully sent
    return responses.terminateTask()
