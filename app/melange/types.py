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

"""Definitions of Melange types."""

from soc.models import profile


class Models(object):
  """Class that encapsulates methods that return appropriate model classes.

  Attributes:
    profile_model: class that represents profile model.
  """

  def __init__(self, profile_model=None):
    """Initializes new instance of Models class.

    Args:
      profile_model: class that represents profile model.
    """
    self.profile_model = profile_model

MELANGE_MODELS = Models(profile_model=profile.Profile)
