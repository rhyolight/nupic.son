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

"""This module contains the Summer Of Code-specific profile related models."""

from melange.models import profile as profile_model


# TODO(daniel): Figure out if it is still feasible to have this class
# if Structured Properties do not support inheritance.
class SOCStudentData(profile_model.StudentData):
  """Model that represents Summer Of Code-specific student information to be
  associated with the specified profile.
  """
