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

"""Classes for rendering Summer Of Code-specific HTTP responses."""

from melange.request import render

from soc.modules.gsoc.views import base_templates


_GSOC_BASE_TEMPLATE = 'modules/gsoc/base.html'

class SOCRenderer(render.Renderer):
  """A Renderer customized for Summer Of Code."""

  def __init__(self, delegate):
    """Constructs a SOCRenderer.

    Args:
      delegate: A Renderer to which this Renderer may delegate
        some portion of its functionality.
    """
    self._delegate = delegate

  def render(self, data, template_path, context):
    """See render.Renderer.render for specification.

    The template is rendered against the given context content augmented
    by the following items:
      base_layout: The path to the base template.
      header: A rendered header.Header template for the passed data.
      mainmenu: A rendered site_menu.MainMenu template for the passed data.
      footer: A rendered site_menu.Footer template for the passed data.
    """
    augmented_context = dict(context)
    augmented_context.update({
        'base_layout': _GSOC_BASE_TEMPLATE,
        'header': base_templates.Header(data),
        'mainmenu': base_templates.MainMenu(data),
        'footer': base_templates.Footer(data),
    })
    return self._delegate.render(data, template_path, augmented_context)


# Since SOCRenderer is stateless, there might as well be just one of it.
SOC_RENDERER = SOCRenderer(render.MELANGE_RENDERER)
