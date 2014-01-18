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

from soc.logic import program as program_logic
from soc.models import survey as survey_model


class SoCLinker(links.Linker):
  """URL creator for Summer Of Code."""

  def shipmentInfo(self, program, entity_id, url_name):
    """Returns the URL of a shipment info's named page.

    Args:
      program: A program.
      entity_id: Numeric ID of entity.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given survey.
    """
    kwargs = {
        'program': program.link_id,
        'sponsor': program_logic.getSponsorKey(program).name(),
        'id': entity_id,
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def survey(self, survey_key, url_name):
    """Returns the URL of a survey's named page.

    Args:
      survey_key: Survey key.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given survey.
    """
    kwargs = {
        'sponsor': survey_model.getSponsorId(survey_key),
        'program': survey_model.getProgramId(survey_key),
        'survey': survey_model.getSurveyId(survey_key),
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

# Since Linker is stateless, there might as well be just one of it.
SOC_LINKER = SoCLinker()
