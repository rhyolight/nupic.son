#!/usr/bin/env python2.5
#
# Copyright 2008 the Melange authors.
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

"""Set of available avatars to choose.
"""

__authors__ = [
  '"Akeda Bagus" <admin@gedex.web.id>',
]


from soc.logic.system import getMelangeVersion


AVATAR_PATH = 'soc/content/%s/images/v2/gci/avatars' % getMelangeVersion()

# mapping of avatar colors to their relative path
AVATAR_COLORS = {
    'blue': '%s/%d-blue.jpg',
    'brown': '%s/%d-brown.jpg',
    'green': '%s/%d-green.jpg',
    'orange': '%s/%d-orange.jpg',
    'pink': '%s/%d-pink.jpg',
    'purple': '%s/%d-purple.jpg',
    'red': '%s/%d-red.jpg',
    }

# List of avatars
AVATARS = [c % (AVATAR_PATH, i) for i in range(1, 26) for _, c in AVATAR_COLORS.items()]
