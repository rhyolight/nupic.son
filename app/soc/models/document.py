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

"""This module contains the Document Model."""


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.models import user as user_model

import soc.models.linkable


class DashboardVisibility(object):
  """Represent different categories of visibilities for Document.

  In other words, the main purpose of this class is to specify a group
  of users for which a document tagged with a specific category will be
  visible or listed.

  This class should not be instantiated. Clients should use constants
  which are defined here or in related modules.
  """

  def __init__(self, identifier, verbose_name):
    """Constructs a new visibility category with the specified
    identifier and verbose name.

    This constructor is private to this module and related modules,
    i.e. containing subclasses of Document model. It should not
    be called by clients directly.

    Args:
      identifier: identifier of the category which will be stored
        in the datastore.
      verbose_name: verbose name of the category which will be displayed
        to users.
    """
    self.identifier = identifier
    self.verbose_name = verbose_name

STUDENT_VISIBILITY = DashboardVisibility('student', 'Students')
MENTOR_VISIBILITY = DashboardVisibility('mentor', 'Mentors')
ORG_ADMIN_VISIBILITY = DashboardVisibility(
    'org_admin', 'Organization Admins')
# TODO(daniel): the last one should be moved somewhere to a SoC specific
# module, as it makes sense only for those programs
ACCEPTED_STUDENT_VISIBILITY = DashboardVisibility(
    'accepted_student', 'Accepted Students')


class Document(soc.models.linkable.Linkable):
  """Model of a Document.
  
  Document is used for things like FAQs, front page text, etc.

  The specific way that the properties and relations inherited from Work
  are used with a Document are described below.

    work.title:  the title of the Document

    work.content:  the rich-text contents of the Document
  """

  # list of all possible dashboard visibilities
  DASHBOARD_VISIBILITIES = [
      STUDENT_VISIBILITY, MENTOR_VISIBILITY, ORG_ADMIN_VISIBILITY,
      ACCEPTED_STUDENT_VISIBILITY,
      ]

  DOCUMENT_ACCESS = ['admin', 'restricted', 'member', 'user']

  #: Required 1:1 relationship indicating the User who initially authored the
  #: Document (this relationship is needed to keep track of lifetime document
  #: creation limits, used to prevent spamming, etc.).
  author = db.ReferenceProperty(
      reference_class=user_model.User, required=True,
      collection_name="created_documents", verbose_name=ugettext('Created by'))

  #: Required field indicating the "title" of the document. Entities
  #: can be indexed, filtered, and sorted by 'title'.
  title = db.StringProperty(required=True,
      verbose_name=ugettext('Title'))
  title.help_text = ugettext(
      'title of the document; often used in the window title')

  #: Required db.TextProperty containing the content of the Document.
  #: The content is only to be displayed to people eligible to
  #: view them (which may be anyone, for example, with the site front page).
  content = db.TextProperty(verbose_name=ugettext('Content'))

  #: date when the work was created
  created = db.DateTimeProperty(auto_now_add=True)

  #: date when the work was last modified
  modified = db.DateTimeProperty(auto_now=True)

  # indicating wich user last modified the work. Used in displaying Work
  modified_by = db.ReferenceProperty(
     reference_class=soc.models.user.User, required=True,
     collection_name="modified_documents",
     verbose_name=ugettext('Modified by'))

  #: field storing the prefix of this document
  prefix = db.StringProperty(default='user', required=True,
      choices=['site', 'club', 'sponsor',
               'program', 'gci_program', 'gsoc_program',
               'org', 'gci_org', 'gsoc_org',
               'user'],
      verbose_name=ugettext('Prefix'))
  prefix.help_text = ugettext(
      'Indicates the prefix of the document,'
      ' determines which access scheme is used.')

  #: field storing the required access to read this document
  read_access = db.StringProperty(default='public', required=True,
      choices=DOCUMENT_ACCESS + ['public'],
      verbose_name=ugettext('Read Access'))
  read_access.help_text = ugettext(
      'Indicates the state of the document, '
      'determines the access scheme.')

  #: field storing the required access to write to this document
  write_access = db.StringProperty(default='admin', required=True,
      choices=DOCUMENT_ACCESS,
      verbose_name=ugettext('Write Access'))
  write_access.help_text = ugettext(
      'Indicates the state of the document, '
      'determines the access scheme.')

  #: field which indicates on whose dashboard's documents list should this
  #: document be listed.
  dashboard_visibility = db.StringListProperty(
      default=[], verbose_name=ugettext('Dashboard visibility'))
  dashboard_visibility.help_text = ugettext(
      'Indicates on whose dashboard the document should be listed.')

  #: field storing whether a link to the Document should be featured in
  #: the sidebar menu (and possibly elsewhere); FAQs, Terms of Service,
  #: and the like are examples of "featured" Document
  is_featured = db.BooleanProperty(
      verbose_name=ugettext('Is Featured'))
  is_featured.help_text = ugettext(
      'Field used to indicate if a Work should be featured, for example,'
      ' in the sidebar menu.')

  #: Reference to Document containing the contents of the "/home" page
  home_for = db.ReferenceProperty(
    reference_class=soc.models.linkable.Linkable,
    collection_name='home_docs')
  home_for.help_text = ugettext(
      'The Precense this document is the home document for.')

  def name(self):
    """Alias 'title' Property as 'name' for use in common templates."""
    return self.title
