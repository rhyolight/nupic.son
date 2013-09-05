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

"""This module contains the helpers to start a mapper job given the name in
mapreduce.yaml for the job.
"""

from mapreduce import control
from mapreduce import status


def start_map(name, params=None, eta=None, countdown=None):
  for config in status.MapReduceYaml.to_dict(status.get_mapreduce_yaml()):
    if config.get('name') == name:
      break

  # Add the mapreduce specific parameters to the params dictionary
  config['mapper_params'].update(params if params else {})

  control.start_map(config['name'], config['mapper_handler'],
                    config['mapper_input_reader'], config['mapper_params'],
                    eta=eta,
                    countdown=countdown)
