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

"""Module for managing Summer Of Code-specific URL generation."""

from django.core import urlresolvers

from melange.request import links

from soc.modules.gsoc.models import project_survey as project_survey_model


class SoCLinker(links.Linker):
  """URL creator for Summer Of Code."""

  def survey(self, survey, url_name):
    """Returns the URL of a survey's named page.

    Args:
      survey: Survey entity.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given survey.
    """
    program_key = (
        project_survey_model.ProjectSurvey.program.get_value_for_datastore(
            survey))

    # TODO(daniel): this should go to an utility function
    sponsor_id, program_id = program_key.name().split('/')

    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'survey': survey.survey_type,
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

# Since Linker is stateless, there might as well be just one of it.
SOC_LINKER = SoCLinker()
