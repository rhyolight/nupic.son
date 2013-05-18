# Copyright 2013 the Melange authors.
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

"""Classes for rendering HTTP responses."""

from django.template import loader

from soc.views.helper import context as soc_context_helper


class Renderer(object):
  """Interface for HTTP response renderers."""

  def render(self, data, template_path, context):
    """Renders the page content from the given template and context.

    Args:
      data: A RequestData object describing the current request.
      template_path: The path of the template to be used.
      context: The context dictionary to be used.

    Returns:
      The rendered template as a string.
    """
    raise NotImplementedError()


class MelangeRenderer(Renderer):
  """A Renderer implementation for use throughout Melange."""

  def render(self, data, template_path, context):
    """See Renderer.render for specification."""
    render_context = soc_context_helper.default(data)
    render_context.update(context)
    return loader.render_to_string(template_path, dictionary=render_context)

# Since MelangeRenderer is stateless, there might as well be just one of it.
MELANGE_RENDERER = MelangeRenderer()
