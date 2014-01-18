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

"""This module contains models for student shipments.
"""


from google.appengine.ext import ndb


class StudentShipment(ndb.Model):
  """Model for storing shipments for students.

  Parent is Profile entity of the student for whom shipment is sent.
  """

  #: string property indicates which shipment info this entity belongs to
  #: key is of type summerofcode.models.shipment_tracking.ShipmentInfo
  shipment_info = ndb.KeyProperty(required=True)

  #: string property holds tracking (number) property
  tracking = ndb.StringProperty()
