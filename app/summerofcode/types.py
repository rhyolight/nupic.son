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

"""Definitions of Summer Of Code-specific types."""

from melange import types

from soc.modules.gsoc.models import profile
from soc.modules.gsoc.models import program
from soc.modules.gsoc.models import timeline

from summerofcode.models import organization
from summerofcode.models import profile as soc_profile


SOC_MODELS = types.Models(
    ndb_org_model=organization.SOCOrganization,
    org_model=organization.SOCOrganization,
    profile_model=profile.GSoCProfile,
    program_model=program.GSoCProgram,
    program_messages_model=program.GSoCProgramMessages,
    student_data_model=soc_profile.SOCStudentData,
    timeline_model=timeline.GSoCTimeline)
