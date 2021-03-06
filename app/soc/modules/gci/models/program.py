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

"""This module contains the GCI specific Program Model."""

from google.appengine.ext import db

from django.utils import translation

from soc.models import document as soc_document_model
from soc.models import program as soc_program_model


class WinnerSelectionType(object):
  """Enumerates all winner selection types for GCI Programs."""

  ORG_NOMINATED = 'Nominated by Organizations'
  GLOBAL_RANKING = 'Global ranking'

WINNER_SELECTION_TYPES = [
    WinnerSelectionType.ORG_NOMINATED, WinnerSelectionType.GLOBAL_RANKING]


class GCIProgramMessages(soc_program_model.ProgramMessages):
  """The GCIProgramMessages model."""
  pass


class GCIProgram(soc_program_model.Program):
  """GCI Program model extends the basic Program model."""

  _messages_model = GCIProgramMessages

  #: string used as a prefix of various key names for other models
  #TODO(daniel): eliminate this
  prefix = 'gci_program'

  homepage_url_name = "gci_homepage"

  #: Required property containing the number of Tasks Students can work
  #: on simultaneously. For GCI it is 1
  nr_simultaneous_tasks = db.IntegerProperty(
      required=True, default=1,
      verbose_name=translation.ugettext('Simultaneous tasks'))
  nr_simultaneous_tasks.group = translation.ugettext('Contest')
  nr_simultaneous_tasks.help_text = translation.ugettext(
      'Number of tasks students can work on simultaneously in the program.')

  #: Determines what winner selection model is used for the program
  winner_selection_type = db.StringProperty(required=True,
      verbose_name=translation.ugettext('Winner selection type'),
      choices=WINNER_SELECTION_TYPES,
      default=WinnerSelectionType.ORG_NOMINATED)

  #: Required property containing the number of winners to be selected in
  #: the program. Defaults to 10
  nr_winners = db.IntegerProperty(
      required=True, default=10,
      verbose_name=translation.ugettext('Number of winners'))
  nr_winners.group = translation.ugettext('Contest')
  nr_winners.help_text = translation.ugettext(
      'Number of winners to be selected at the end of the program.')

  #: A list of task types that a Task can belong to
  task_types = db.StringListProperty(
      required=True, default=['Any'],
      verbose_name=translation.ugettext('Task Types'))
  task_types.group = translation.ugettext('Task Types')
  task_types.help_text = translation.ugettext(
      'List all the types a task can be in.')

  #: Document reference property used for the Student Agreement
  terms_and_conditions = db.ReferenceProperty(
      reference_class=soc_document_model.Document,
      verbose_name=translation.ugettext('Terms and Conditions'),
      collection_name='terms_and_conditions')
  terms_and_conditions.group = soc_program_model.PROGRAM_DOCUMENTS_GROUP
  terms_and_conditions.help_text = translation.ugettext(
      'Document containing Terms and Conditions for participants.')

  #: An URL to a page with example tasks so that students can get
  #: some intuition about the types of tasks in the program
  example_tasks = db.LinkProperty(
      required=False, verbose_name=translation.ugettext('Example tasks'))
  example_tasks.help_text = translation.ugettext(
      'URL to a page with example tasks.')

  #: URL to a page that contains the form translations.
  form_translations_url = db.LinkProperty(
      required=False, verbose_name=translation.ugettext(
          'Form translation URL'))
  form_translations_url.help_text = translation.ugettext(
      'URL to the page containing translations of the forms students '
      'should upload.')
