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

"""Module containing the notification related views for Summer Of Code."""

from melange.views import notification_settings as notification_settings_view

from soc.modules.gsoc.views import base as gsoc_base
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.request import error
from summerofcode.request import links
from summerofcode.request import render
from summerofcode.views.helper import urls as soc_urls


NOTIFICATIONS_SETTINGS_PAGE = (
    notification_settings_view.NotificationSettingsPage(
        gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
        error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
        soc_urls.UrlNames, 'modules/gsoc/form_base.html'))
