/* Copyright 2011 the Melange authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * @author <a href="mailto:admin@gedex.web.id">Akeda Bagus</a>
 */

melange.templates.inherit(
  function (_self, context) {
    jQuery('.' + context.dashboard_link_class).bind('click', function() {
      var target_str = jQuery(this).attr('href') + context.dashboard_id_suffix;
      var dashboard = jQuery(target_str);

      // hide other dashboards
      jQuery('.' + context.dashboard_class).addClass('disabled');
      // show clicked dashboard
      dashboard.removeClass('disabled').show();
    });
  }
);

