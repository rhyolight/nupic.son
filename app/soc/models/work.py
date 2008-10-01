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

"""This module contains the Work Model."""

__authors__ = [
  '"Todd Larsen" <tlarsen@google.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
]

from google.appengine.ext import db

from django.utils.translation import ugettext_lazy

import polymodel


class Work(polymodel.PolyModel):
  """Model of a Work created by one or more Persons in Roles.

  Work is a "base entity" of other more specific "works" created by Persons
  serving in "roles".

   authors)  a many:many relationship with Roles, stored in a separate
     WorksAuthors model, used to represent authorship of the Work.  See
     the WorksAuthors model class for details.

   reviews)  a 1:many relationship between a Work and the zero or more
     Reviews of that Work.  This relation is implemented as the 'reviews'
     back-reference Query of the Review model 'reviewed' reference.
  """

  #: Required field indicating the "title" of the work, which may have
  #: different uses depending on the specific type of the work. Works
  #: can be indexed, filtered, and sorted by 'title'.
  title = db.StringProperty(required=True,
      verbose_name=ugettext_lazy('Title'))
  title.help_text = ugettext_lazy(
      'title of the document; often used in the window title')

  #: optional, indexed plain text field used for different purposes,
  #: depending on the specific type of the work
  abstract = db.StringProperty(multiline=True)
  abstract.help_text = ugettext_lazy(
      'short abstract, summary, or snippet;'
      ' 500 characters or less, plain text displayed publicly')

  #: Required path, prepended to a "link name" to form the document URL.
  #: The combined path and link name must be globally unique on the
  #: site.  Except in /site/docs (Developer) forms, this field is not
  #: usually directly editable by the User, but is instead set by controller
  #: logic to match the "scope" of the document.
  partial_path = db.StringProperty(required=True,
      verbose_name=ugettext_lazy('Partial path'))
  partial_path.help_text = ugettext_lazy(
    'path portion of URLs, prepended to link name')

  #: Required link name, appended to a "path" to form the document URL.
  #: The combined path and link name must be globally unique on the
  #: site (but, unlike some link names, a Work link name can be reused,
  #: as long as the combination with the preceding path is unique).
  link_name = db.StringProperty(required=True,
      verbose_name=ugettext_lazy('Link name'))
  link_name.help_text = ugettext_lazy('link name used in URLs')

  #: short name used in places such as the sidebar menu and breadcrumb trail
  #: (optional: title will be used if short_name is not present)
  short_name = db.StringProperty(verbose_name=ugettext_lazy('Short name'))
  short_name.help_text = ugettext_lazy(
      'short name used, for example, in the sidebar menu')
  
  #: date when the work was created
  created = db.DateTimeProperty(auto_now_add=True)
  
  #: date when the work was last modified
  modified = db.DateTimeProperty(auto_now=True)
