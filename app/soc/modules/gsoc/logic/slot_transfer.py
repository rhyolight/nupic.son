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

"""Logic for slot transfers."""

from soc.modules.gsoc.models import slot_transfer as slot_transfer_model


def getSlotTransferEntitiesForOrg(org_key, limit=1000):
  """Returns the slot transfer entity for the specified organization.

  Args:
    org_key: NDB Organization key.

  Returns:
    The slot transfer entity for the specified organization.
  """
  query = slot_transfer_model.GSoCSlotTransfer.all().ancestor(
      org_key.to_old_key())
  return query.fetch(limit=limit)
