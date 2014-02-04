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

"""Module with Summer Of Code-specific connection related views."""

from soc.modules.gsoc.views import base as gsoc_base
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns
from melange.request import render
from melange.request import error
from melange.views import connection as connection_view

from summerofcode.request import links
from summerofcode.views.helper import urls as soc_urls

renderer = gsoc_base.GSoCRenderer(render.MELANGE_RENDERER)
START_CONNECTION_AS_ORG = connection_view.StartConnectionAsOrg(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, renderer,
    gsoc_base.GSoCErrorHandler(renderer, error.MELANGE_ERROR_HANDLER),
    soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'modules/gsoc/form_base.html')
