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
 * @author <a href="mailto:dhans@google.com">Daniel Hans</a>
 */

melange.templates.inherit(function (_self, context) {

  // TODO: replace eval with a safe json library 
  eval('var urls = ' + context.urls);
  eval('var visualizations = ' + context.visualizations);

  var statistic = {
	'admins': '/gsoc/statistic/fetch/admins',
	'profiles': '/gsoc/statistic/fetch/profiles',
	'mentors': '/gsoc/statistic/fetch/mentors',
	'students': '/gsoc/statistic/fetch/students',
	'students_per_country': '/gsoc/statistic/fetch/students_per_country',
	'mentors_per_country': '/gsoc/statistic/fetch/mentors_per_country',
	'proposals_per_student': '/gsoc/statistic/fetch/proposals_per_student',
	'students_with_proposals': '/gsoc/statistic/fetch/students_with_proposals',
  };

  var key_name = null;
  var obj = null
  var statistic_data = {}

  var drawStatisticVisualization = function (key_name) {
	var chart = new google.visualization.Table(document.getElementById('statistic-presentation-div'));
	/* check if the data for a given statistic has already been downloaded. */
	if (statistic_data[key_name] !== undefined) {
	  chart.draw(statistic_data[key_name], {width: 400, height: 240});
	} else {
	  var action_url = statistic[key_name];
	  jQuery.get(
		action_url,
		{'fmt': 'json', 'type': 'gviz'},
		function (data) {
		  eval('var _data = ' + data);
		  statistic_data[key_name] = new google.visualization.DataTable(_data);
	      chart.draw(statistic_data[key_name], {width: 400, height: 240});
		},
		'text'
	  );
	}
  }

  var selectionChanged = function () {
	jQuery('#statistic-select :selected').each(function (index) {
	  key_name = jQuery(this).attr('id');
	  drawStatisticVisualization(jQuery(this).attr('id'));
	});
  };
  
  var initialize = function () {
	jQuery('#statistic-select :selected').each(function (index) {
	  key_name = jQuery(this).attr('id');
	  drawStatisticVisualization(key_name);
	});
  };
  
  jQuery(function () {
	jQuery('#statistic-select').change(selectionChanged)
	melange.loadGoogleApi('visualization', '1', {'packages':['table']}, initialize);
  });
});
