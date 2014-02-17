# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the Summer Of Code callback."""

from summerofcode.views import connection
from summerofcode.views import org_app
from summerofcode.views import org_home
from summerofcode.views import profile
from summerofcode.views import project_manage
from summerofcode.views import shipment_tracking
from summerofcode.tasks import shipment_tracking as shipment_tracking_tasks


class Callback(object):
  """Callback object that handles interaction between the core."""

  # This constant is required by soc.modules.core module. If its values
  # does not match the one defined there, the callback is rejected.
  API_VERSION = 1

  def __init__(self, core):
    """Initializes a new Callback object for the specified core."""

    self.core = core
    self.views = []

  def registerViews(self):
    """Instantiates all view objects."""
    self.views.append(connection.LIST_CONNECTION_FOR_USER)
    self.views.append(connection.MANAGE_CONNECTION_AS_ORG)
    self.views.append(connection.MANAGE_CONNECTION_AS_USER)
    self.views.append(connection.PICK_ORGANIZATION_TO_CONNECT)
    self.views.append(connection.START_CONNECTION_AS_ORG)
    self.views.append(connection.START_CONNECTION_AS_USER)
    self.views.append(org_app.OrgAppShowPage())
    self.views.append(org_app.OrgApplicationListPage())
    self.views.append(org_app.OrgApplicationSubmitPage())
    self.views.append(org_app.OrgPreferencesEditPage())
    self.views.append(org_app.OrgProfileCreatePage())
    self.views.append(org_app.OrgProfileEditPage())
    self.views.append(org_app.PublicOrganizationListPage())
    self.views.append(org_app.SurveyResponseShowPage())
    self.views.append(org_home.OrgHomePage())
    self.views.append(profile.ProfileAdminPage())
    self.views.append(profile.ProfileEditPage())
    self.views.append(profile.ProfileRegisterAsOrgMemberPage())
    self.views.append(profile.ProfileRegisterAsStudentPage())
    self.views.append(profile.ProfileShowPage())
    self.views.append(project_manage.ManageProjectProgramAdminView())
    self.views.append(shipment_tracking.CallbackPage())
    self.views.append(shipment_tracking.CreateShipmentInfo())
    self.views.append(shipment_tracking.ShipmentInfoListPage())
    self.views.append(shipment_tracking.ShipmentTrackingPage())
    self.views.append(shipment_tracking.SyncData())

    # Appengine Task related views
    self.views.append(shipment_tracking_tasks.ShipmentSyncTask())

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered."""
    self.core.requireUniqueService('registerWithSitemap')

    # Redesigned view registration
    for view in self.views:
      self.core.registerSitemapEntry(view.djangoURLPatterns())
