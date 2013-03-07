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


"""MapReduce to add the program reference to the org app records.
"""


from mapreduce import operation

# Following three imports required for the model visibility for
# runnning mapreduce.
from soc.models.org_app_record import OrgAppRecord
from soc.models.org_app_survey import OrgAppSurvey

from soc.modules.gsoc.models.program import GSoCProgram


def process(org_app_record):
  org_app_record.program = org_app_record.survey.program

  yield operation.db.Put(org_app_record)
  yield operation.counters.Increment("action_comment_converted")
