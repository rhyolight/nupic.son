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

"""Logic for organization."""

from soc.logic import organization as org_logic

from soc.modules.gsoc.models import organization as org_model


def participating(program):
  """Return a list of GSoC organizations to display on GSoC program homepage.

  Function that acts as a GSoC module wrapper for fetching participating
  organizations.

  Args:
    program: GSoCProgram entity for which the organizations need to be fetched.

  Returns:
    list of GSoCOrganization entities
  """
  return org_logic.participating(org_model.GSoCOrganization, program)
