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

"""This module contains the GSoC Slot Transfer model.
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
]


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.base


class GSoCSlotTransfer(soc.models.base.ModelWithFieldAttributes):
  """Model that stores the organization has decided to give up.
  """

  #: The number of slots the organization has decided to give up
  nr_slots = db.IntegerProperty(
      required=True, verbose_name=ugettext('Slots to transfer'))
  nr_slots.help_text = ugettext('Number of slots you would like to transfer '
                                'to the pool.')

  #: The remarks text explaining why the slots were given
  remarks = db.StringProperty(
      required=True, verbose_name=ugettext('Remarks'))
  remarks.help_text = ugettext(
      'A brief explanation mentioning the reason for transferring the '
      'slots back to the pool.')

  #: The status of slot transfer
  #: pending: requested by the org, but the program admin has not taken action
  #: accepted: program admin accepted the slot transfer
  #: rejected: program admin rejected the request to transfer the slots
  status = db.StringProperty(required=True, default='pending',
      choices=['pending', 'accepted', 'rejected'],
      verbose_name='Status')

  #: date when the proposal was created
  created_on = db.DateTimeProperty(required=True, auto_now_add=True,
                                   verbose_name=ugettext('Created On'))

  #: date when the proposal was last modified, should be set manually on edit
  last_modified_on = db.DateTimeProperty(
      required=True, auto_now=True,
      verbose_name=ugettext('Last Modified On'))
