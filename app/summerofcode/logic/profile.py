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

"""Logic for profiles."""


def hasProject(profile):
  """Tells whether the specified profile has at least one project assigned.

  Args:
    profile: Profile entity.

  Returns:
    True if the profile is a student and has at least one project;
      False otherwise.
  """
  return profile.is_student and bool(profile.student_data.number_of_projects)
