#!/usr/bin/env python2.5
#
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

"""This module contains the GCI specific Comment Model.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.models.user import User

import soc.models.base


class GCIComment(soc.models.base.ModelWithFieldAttributes):
  """GCI Comment model for tasks, extends the basic Comment model.

    Parent:
      soc.modules.gci.models.task.GCITask
  """

  title = db.StringProperty(required=False, verbose_name=ugettext('Title'))

  #: The rich textual content of this comment
  content = db.TextProperty(required=False, verbose_name=ugettext('Content'))

  #: Property containing the human readable string that should be
  #: shown for the comment when something in the task changes, 
  #: code.google.com issue tracker style
  changes = db.StringListProperty(
      default=[], verbose_name=ugettext('Changes in the task'))

  #: Property storing the status of the comment.
  #: valid: comment is visible to all
  #: invalid: comment is deleted, which is marked as invalid
  status = db.StringProperty(default='valid',
                             choices=['valid','invalid'],
                             verbose_name=ugettext('Status of this Comment'))

  #: A non-required many:1 relationship with a comment entity indicating
  #: the user who provided that comment. If not available the system created
  #: the comment.
  created_by = db.ReferenceProperty(reference_class=User,
                                    required=False,
                                    collection_name="commented_by")

  #: Date when the comment was added
  created_on = db.DateTimeProperty(auto_now_add=True)

  # indicating wich user last modified the comment.
  modified_by = db.ReferenceProperty(reference_class=User,
                                     required=False,
                                     collection_name="comment_modified_by",
                                     verbose_name=ugettext('Modified by'))

  #: date when the work was last modified
  modified_on = db.DateTimeProperty(auto_now=True)
