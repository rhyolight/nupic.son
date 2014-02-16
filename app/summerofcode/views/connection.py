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

from melange.models import organization as org_model
from melange.request import access
from melange.views import connection as connection_view

from summerofcode.request import error
from summerofcode.request import links
from summerofcode.request import render
from summerofcode.views.helper import urls as soc_urls


START_CONNECTION_AS_ORG = connection_view.StartConnectionAsOrg(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
    error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'modules/gsoc/form_base.html')


START_CONNECTION_AS_USER_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.PROGRAM_ACTIVE_ACCESS_CHECKER,
    access.NON_STUDENT_PROFILE_ACCESS_CHECKER,
    access.UrlOrgStatusAccessChecker([org_model.Status.ACCEPTED]),
    connection_view.NoConnectionExistsAccessChecker(soc_urls.UrlNames)])

START_CONNECTION_AS_USER = connection_view.StartConnectionAsUser(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
    error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'modules/gsoc/form_base.html',
    START_CONNECTION_AS_USER_ACCESS_CHECKER)


LIST_CONNECTION_FOR_USER = connection_view.ListConnectionsForUser(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
    error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'summerofcode/connection/connection_list.html')


MANAGE_CONNECTION_AS_ORG = connection_view.ManageConnectionAsOrg(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
    error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'summerofcode/connection/manage_connection.html')


MANAGE_CONNECTION_AS_USER = connection_view.ManageConnectionAsUser(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
    error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'summerofcode/connection/manage_connection.html')


PICK_ORGANIZATION_TO_CONNECT = connection_view.PickOrganizationToConnectPage(
    gsoc_base._GSOC_INITIALIZER, links.SOC_LINKER, render.SOC_RENDERER,
    error.SOC_ERROR_HANDLER, soc_url_patterns.SOC_URL_PATTERN_CONSTRUCTOR,
    soc_urls.UrlNames, 'modules/gsoc/accepted_orgs/base.html')
