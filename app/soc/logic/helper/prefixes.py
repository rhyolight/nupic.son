# Copyright 2010 the Melange authors.
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

"""Prefix helper module for models with document prefixes."""

from melange.models import user as user_model

from soc.models import program as program_model
from soc.models import organization as org_model
from soc.models import site as site_model

from soc.modules.gsoc.models import program as gsoc_program_model

from soc.modules.gci.models import organization as gci_org_model
from soc.modules.gci.models import program as gci_program_model

from summerofcode.models import organization as soc_org_model


def getScopeForPrefix(prefix, key_name):
  """Gets the scope for the given prefix and key_name.

  Args:
    prefix: Prefix of the document.
    key_name: key_name of the document.

  Returns:
    Scope entity for the specified document and prefix.

  Raises:
    ValueError if no scope model is found for the specified prefix.
  """
  # use prefix to generate dict key
  scope_types = {
      'gsoc_program': gsoc_program_model.GSoCProgram,
      'gci_program': gci_program_model.GCIProgram,
      'program': program_model.Program,
      'gci_org': gci_org_model.GCIOrganization,
      'org': org_model.Organization,
      'user': user_model.User,
      'site': site_model.Site,
  }

  # determine the type of the scope
  scope_type = scope_types.get(prefix)

  # NDB models are handled by different API
  if prefix == 'user':
    return scope_type.get_by_id(key_name)
  elif scope_type:
    return scope_type.get_by_key_name(key_name)
  else:
    # try finding a scope among NDB models
    scope_types = {
        'gsoc_org': soc_org_model.SOCOrganization,
        }

    # determine the type of the scope
    scope_type = scope_types.get(prefix)

    if scope_type:
      return scope_type.get_by_id(key_name)
    else:
      # no matching scope type found
      raise ValueError('No Matching Scope type found for %s' % prefix)
