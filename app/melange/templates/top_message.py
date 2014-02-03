# Copyright 2014 the Melange authors.
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

"""Module containing a template for top message."""

from soc.views import template


class TopMessage(template.Template):
  """Template for a message to be displayed on the top of the main part
  of the message.
  """

  def __init__(self, data, template_path, message):
    """Initializes a new instance of this class.

    Args:
      data: request_data.RequestData object for the current request.
      template_path: Path to the HTML template to use for rendering.
      message: String with a message to be displayed.
    """
    super(TopMessage, self).__init__(data)
    self._template_path = template_path
    self._message = message

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return self._template_path

  def context(self):
    """See template.Template.context for specification."""
    return {'top_message': self._top_message}
