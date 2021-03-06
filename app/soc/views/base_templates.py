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

"""This module contains the view for the site menus."""

from soc.models import program as program_model
from soc.models.site import Site

from soc.views.template import Template


PROGRAM_SELECT_TEMPLATE_PATH = 'soc/_program_select.html'

class ProgramSelect(Template):
  """Program select template."""

  def __init__(self, template_path, data, url_name):
    super(ProgramSelect, self).__init__(data)
    self.template_path = template_path
    self.url_name = url_name

  def context(self):
    def url(program):
      # TODO(nathaniel): make this .program call unnecessary.
      self.data.redirect.program(program=program)

      return self.data.redirect.urlOf(self.url_name)

    def attr(program):
      if program.key() == self.data.program.key():
        return "selected=selected"
      else:
        return ""

    program_key = Site.active_program.get_value_for_datastore(self.data.site)

    programs = []
    for program in self.data.programs:
      if program.status == program_model.STATUS_INVISIBLE:
        continue

      name = program.short_name
      if program.key() == program_key:
        name += ' (current)'
      programs.append((name, url(program), attr(program)))

    return {
        'programs': programs,
        'render': len(programs) > 1,
    }


class DefaultProgramSelect(ProgramSelect):
  """Subclass of ProgramSelect that always is always rendered using
  PROGRAM_SELECT_TEMPLATE_PATH as its template path.
  """

  def __init__(self, data, url_name):
    """See ProgramSelect.__init__ for specification."""
    super(DefaultProgramSelect, self).__init__(
        PROGRAM_SELECT_TEMPLATE_PATH, data, url_name)

