#!/usr/bin/python2.5
#
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

"""GCI org proposal processing mapreduce.
"""


from mapreduce import context
from mapreduce import operation

from soc.logic import org_app as org_app_logic
from soc.models.site import Site
from soc.models.org_app_record import OrgAppRecord
from soc.models.org_app_survey import OrgAppSurvey

from soc.modules.gsoc.models.program import GSoCProgram

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.views.helper.request_data import RedirectHelper


class MapreduceRequestData(object):
  """Simple class to use for convenience with RequestData object"""

  def __init__(self, program, site):
    self.program = program
    self.site = site


def process(org_app):
  ctx = context.get()
  params = ctx.mapreduce_spec.mapper.params

  program_type = params['program_type']
  program_key_str = params['program_key']

  if program_type == 'gci':
    program_model = GCIProgram
  elif program_type == 'gsoc':
    program_model = GSoCProgram

  program = program_model.get_by_key_name(program_key_str)

  survey_query = OrgAppSurvey.all(keys_only=True).filter('program', program)
  survey_key = survey_query.get()

  # We can skip the survey records not belonging to the given program.
  if org_app.survey.key() != survey_key:
    return

  # TODO(daniel): create a MapReduce/Task RequestData
  data = MapreduceRequestData(program, Site.get_by_key_name('site'))
  redirect = RedirectHelper(data)

  url = '/%s/profile/organization/%s' % (program_type, program_key_str)

  full_url = redirect._fullUrl(url, full=True, secure=False)

  if org_app.status == 'pre-accepted':
    org_app_logic.setStatus(data, org_app, 'accepted', full_url)
    yield operation.counters.Increment("proposals_accepted")
  elif org_app.status == 'pre-rejected':
    org_app_logic.setStatus(data, org_app, 'rejected', full_url)
    yield operation.counters.Increment("proposals_rejected")
  else:
    yield operation.counters.Increment("proposals_ignored")
