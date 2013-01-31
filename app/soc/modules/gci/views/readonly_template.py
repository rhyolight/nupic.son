# Copyright 2012 the Melange authors.
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

"""Module containing the GCI readonly template classes.
"""


from soc.views import readonly_template


class GCIModelReadOnlyTemplate(readonly_template.ModelReadOnlyTemplate):
  """Class to render readonly templates for GCI models.
  """

  template_path = 'v2/modules/gci/_readonly_template.html'
