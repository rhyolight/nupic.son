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

"""Definitions of Code In-specific types."""

from melange import types

from soc.modules.gci.models import organization
from soc.modules.gci.models import profile
from soc.modules.gci.models import program
from soc.modules.gci.models import timeline


CI_MODELS = types.Models(
    org_model=organization.GCIOrganization,
    profile_model=profile.GCIProfile,
    program_model=program.GCIProgram,
    program_messages_model=program.GCIProgramMessages,
    timeline_model=timeline.GCITimeline)
