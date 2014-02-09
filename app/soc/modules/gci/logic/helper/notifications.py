# Copyright 2009 the Melange authors.
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

"""Notifications for the GCI module.
"""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django.template import loader
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext

from melange.models import profile as profile_model

from soc.logic import accounts
from soc.logic import dicts
from soc.logic import mail_dispatcher
from soc.logic import program as program_logic
from soc.logic import site
from soc.tasks import mailer

from soc.modules.gci.models import comment as comment_model
from soc.modules.gci.views.helper import url_names


DEF_BULK_CREATE_COMPLETE_SUBJECT = ugettext(
    'Bulk creation of tasks completed')

DEF_BULK_CREATE_COMPLETE_TEMPLATE = 'modules/gci/reminder/bulk_create.html'

DEF_FIRST_TASK_CONFIRMATION_SUBJECT = ugettext(
    'You have completed your first task in Google Code-in program')

DEF_FIRST_TASK_CONFIRMATION_TEMPLATE = \
    'modules/gci/notification/first_task_confirmation.html'

DEF_PARENTAL_FORM_SUBJECT = ugettext(
    '[%(program_name)s]: Parental Consent Form - Please Respond')

DEF_NEW_TASK_COMMENT_SUBJECT = ugettext(
    '[%(program_name)s] New comment on %(task_title)s')

DEF_NEW_TASK_COMMENT_NOTIFICATION_TEMPLATE = \
    'modules/gci/notification/new_task_comment.html'

DEF_NEW_MESSAGE_SUBJECT = ugettext(
    '[%(program_name)s] New reply from %(author_name)s: '
    'Re: %(conversation_subject)s')

DEF_NEW_CONVERSATION_SUBJECT = ugettext(
    '[%(program_name)s] New message from %(author_name)s: '
    '%(conversation_subject)s')

DEF_NEW_MESSAGE_NOTIFICATION_TEMPLATE = \
    'modules/gci/notification/new_message.html'

DEF_NEW_CONVERSATION_NOTIFICATION_TEMPLATE = \
    'modules/gci/notification/new_conversation.html'


def sendMail(to_user, subject, message_properties, template):
  """Sends an email with the specified properties and mail content

  Args:
    to_user: user entity to whom the mail should be sent
    subject: subject of the mail
    message_properties: contains those properties that need to be
                        customized
    template: template that holds the content of the mail
  """

  site_entity = site.singleton()
  site_name = site_entity.site_name

  # get the default mail sender
  default_sender = mail_dispatcher.getDefaultMailSender()

  if not default_sender:
    # no valid sender found, abort
    return
  else:
    (sender_name, sender) = default_sender

  to = accounts.denormalizeAccount(to_user.account).email()

  # create the message contents
  new_message_properties = {
      'to_name': to_user.name,
      'sender_name': sender_name,
      'to': to,
      'sender': sender,
      'site_name': site_name,
      'subject': force_unicode(subject)
      }

  messageProperties = dicts.merge(message_properties, new_message_properties)

  # send out the message using the default new notification template
  mail_dispatcher.sendMailFromTemplate(template, messageProperties)

def sendTaskUpdateMail(subscriber, subject, message_properties=None):
  """Sends an email to a user about an update to a Task.

    Args:
      subscriber: The user entity to whom the message must be sent
      subject: Subject of the mail
      message_properties: The mail message properties
      template: Optional django template that is used to build the message body
  """

  template = 'modules/gci/task/update_notification.html'

  # delegate sending mail to the helper function
  sendMail(subscriber, subject, message_properties, template)

def sendBulkCreationCompleted(bulk_data):
  """Sends out a notification that the bulk creation of tasks has been
  completed.

  Any error messages that have been generated are also added to the notification.

  Args:
    bulk_data: GCIBulkCreateData entity containing information needed to
               populate the notification.
  """
  message_properties = {
      'bulk_data' : bulk_data
      }

  subject = DEF_BULK_CREATE_COMPLETE_SUBJECT
  template = DEF_BULK_CREATE_COMPLETE_TEMPLATE

  sendMail(bulk_data.created_by.user, subject, message_properties, template)

def sendParentalConsentFormRequired(user_entity, program_entity):
  """Sends out a notification to the student who completed first task that
  a parent consent form is necessary to receive prizes.

  Args:
    user_entity: User entity who completed his/her first task
    program_entity: The entity for the program for which the task
                    was completed.
  """
  subject = DEF_PARENTAL_FORM_SUBJECT % {
      'program_name': program_entity.name
      }
  template = 'modules/gci/notification/messages/parental_form_required.html'

  # delegate sending mail to the helper function
  sendMail(user_entity, subject, {}, template)


def getFirstTaskConfirmationContext(student):
  """Sends notification to the GCI student, when he or she completes their
  first task.

  Args:
    student: the student who should receive the confirmation
  """
  to = student.contact.email

  subject = DEF_FIRST_TASK_CONFIRMATION_SUBJECT

  program_key = student.program

  kwargs = {
      'sponsor': profile_model.getSponsorId(student.key),
      'program': profile_model.getProgramId(student.key)
      }
  url = reverse('gci_student_form_upload', kwargs=kwargs)

  protocol = 'http'
  hostname = site.getHostname()

  context = {
      'student_forms_link': '%s://%s%s' % (protocol, hostname, url),
      }

  template = DEF_FIRST_TASK_CONFIRMATION_TEMPLATE
  body = loader.render_to_string(template, context)

  return mailer.getMailContext(to=to, subject=subject, html=body, bcc=[])

def getTaskCommentContext(task, comment, to_emails):
  """Sends out notifications to the subscribers.

  Args:
    task: task entity that comment made on.
    comment: comment entity.
    to_emails: list of recepients for the notification.
  """
  url_kwargs = {
    'sponsor': program_logic.getSponsorKey(task.program).name(),
    'program': task.program.link_id,
    'id': task.key().id(),
  }

  task_url = 'http://%(host)s%(task)s' % {
      'host': site.getHostname(),
      'task': reverse('gci_view_task', kwargs=url_kwargs)}

  author_key = (
      comment_model.GCIComment.created_by
          .get_value_for_datastore(comment))
  author = ndb.Key.from_old_key(author_key).get() if author_key else None
  commented_by = author.user_id if author else 'Melange'

  message_properties = {
      'commented_by': commented_by,
      'comment_title': comment.title,
      'comment_content': comment.content,
      'group': task.org.name,
      'program_name': task.program.name,
      'sender_name': 'The %s Team' % site.singleton().site_name,
      'task_title': task.title,
      'task_url': task_url,
  }

  subject = DEF_NEW_TASK_COMMENT_SUBJECT % message_properties
  template = DEF_NEW_TASK_COMMENT_NOTIFICATION_TEMPLATE
  body = loader.render_to_string(template, dictionary=message_properties)

  return mailer.getMailContext(to=[], subject=subject, html=body, bcc=to_emails)


def getTaskConversationMessageContext(message, to_emails, is_reply):
  """Sends out notifications to the conversation's participants.

  Args:
    message: Key (ndb) of GCIMessage to send.
    to_emails: List of recipients for the notification.
    is_reply: Whether this message is a reply to an existing conversation.

  Returns:
    Context dictionary for a mailer task.
  """
  message_ent = message.get()
  conversation_ent = message_ent.conversation.get()
  program_ent = db.get(ndb.Key.to_old_key(conversation_ent.program))
  author_ent = message_ent.author.get()

  url_kwargs = {
    'sponsor': program_logic.getSponsorKey(program_ent).name(),
    'program': program_ent.link_id,
    'id': conversation_ent.key.integer_id(),
  }

  conversation_url = 'http://%(host)s%(conversation)s' % {
      'host': site.getHostname(),
      'conversation': reverse(url_names.GCI_CONVERSATION, kwargs=url_kwargs)}

  message_url = 'http://%(host)s%(conversation)s#m%(message_id)s' % {
      'host': site.getHostname(),
      'conversation': reverse(url_names.GCI_CONVERSATION, kwargs=url_kwargs),
      'message_id': message.integer_id()}

  message_by = author_ent.user_id if author_ent else 'Melange'

  message_properties = {
      'author_name': message_by,
      'conversation_subject': conversation_ent.subject,
      'message_content': message_ent.content,
      'sender_name': 'The %s Team' % site.singleton().site_name,
      'conversation_url': conversation_url,
      'message_url': message_url,
      'program_name': program_ent.name,
      'is_reply': is_reply,
  }

  subject = ((
      DEF_NEW_MESSAGE_SUBJECT if is_reply else DEF_NEW_CONVERSATION_SUBJECT)
         % message_properties)

  template = (
      DEF_NEW_MESSAGE_NOTIFICATION_TEMPLATE if is_reply
      else DEF_NEW_CONVERSATION_NOTIFICATION_TEMPLATE)

  body = loader.render_to_string(template, dictionary=message_properties)

  return mailer.getMailContext(to=[], subject=subject, html=body, bcc=to_emails)
