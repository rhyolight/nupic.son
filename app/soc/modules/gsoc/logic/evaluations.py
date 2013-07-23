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

"""Logic for evaluations."""

from melange.utils import time

from summerofcode.logic import survey as survey_logic


def evaluationRowAdder(evals):
  """Add rows for each evaluation for each entity that is fetched.

  Args:
    evals: a dictionary containing  evaluations.

  Returns:
    adder function that can be used to add rows to a list of evaluations.
  """
  def adder(content_response, entity, *args):
    # get the last failed evaluation for the project so that an
    # entry for survey record need not be calculated after this
    # evaluation
    failed_eval = None
    if entity.failed_evaluations:
      failed_grading_record = entity.failed_evaluations[-1]
      fgr_ent = args[0].get(failed_grading_record)
      failed_eval = fgr_ent.grading_survey_group.grading_survey

    # since evals is an object of type Django's SortedDict
    # we can be sure that the evaluations are iterated in the order
    for eval_link_id, evaluation in evals.items():
      active_period = survey_logic.getSurveyActivePeriod(evaluation)
      has_started = active_period != survey_logic.PRE_PERIOD_STATE
      if not has_started:
        # try getting an extension for the project
        extension = survey_logic.getPersonalExtension(
            entity.parent_key(), evaluation.key())

        active_period = survey_logic.getSurveyActivePeriod(
            evaluation, extension=extension)

        has_started = active_period != survey_logic.PRE_PERIOD_STATE

      content_response.addRow(entity, eval_link_id, *args)

      if failed_eval and \
            failed_eval.key().id_or_name() == evaluation.key().id_or_name():
          break

  return adder
