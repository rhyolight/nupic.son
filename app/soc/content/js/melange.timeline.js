/* Copyright 2013 the Melange authors.
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
!function ($) {

  "use strict"; // jshint ;_;


 /* Timeline CLASS DEFINITION
  * ==================== */

  var Timeline = function (element, options) {
    this.init(element);
    this.setOptionsAndDraw(options);
  };

  Timeline.prototype = {

    constructor: Timeline,

    options_defaults: {
      color_blue: '#3089b6',
      color_blue_light: '#bff2ff',
      color_gray: '#e7e7ea',
      slice_faded_opacity: 0.2,
      title_element: '',
      timerange_element: '',
      colors_default: [
        '#d3d2d7',
        '#fb1714',
        '#fde733',
        '#92f13d',
        '#16d53d',
        '#419ca6',
        '#03588c'
      ],
      slices: [],
      slice_title_append: ' soon',
      slice_missing_shade: 30,
      now: new Date().getTime()
    },

    //TODO(Mario): This global state variable needs to be removed.
    slice_active: null,
  };

  Timeline.prototype.init = function (element) {
    this.R = this.enrichRaphaelObjectWithCustomAttributes(Raphael(element));
  };

  Timeline.prototype.enrichRaphaelObjectWithCustomAttributes = function (R) {
    R.customAttributes.segment = function (x, y, r, a1, a2) {
      var flag = (a2 - a1) > 180;

      a1 = (a1 % 360) * Math.PI / 180;
      a2 = (a2 % 360) * Math.PI / 180;

      return {
        path: [
          ["M", x, y],
          ["l", r * Math.cos(a1), r * Math.sin(a1)],
          ["A", r, r, 0, +flag, 1, x + r * Math.cos(a2), y + r * Math.sin(a2)],
          ["z"]
        ]
      };
    };

    R.customAttributes.arc = function (x, y, r, a1, a2) {
      var flag = (a2 - a1) > 180;

      a1 = (a1 % 360) * Math.PI / 180;
      a2 = (a2 % 360) * Math.PI / 180;

      return {
        path: [
          ["M", x + r * Math.cos(a1), y + r * Math.sin(a1)],
          ["A", r, r, 0, +flag, 1, x + r * Math.cos(a2), y + r * Math.sin(a2)]
        ]
      };
    };

    return R;
  };

  Timeline.prototype.setOptionsAndDraw = function (options) {
    // transform date into milliseconds
    if (
      (typeof(options.now) !== 'undefined') &&
      (isNaN(parseInt(options.now, 10)) || !isFinite(options.now))
    ) {
      options.now = this.dateToUTCMilliseconds(options.now);
    }

    options.title_element = $(options.title_selector);
    options.timerange_element = $(options.timerange_selector);

    this.options = $.extend({}, this.options_defaults, options);

    /* We calculate the year to be printed at the center of the widget here,
       before enrichSlides() kicks in and adds slices for the gaps. */
    var last_slice = this.options.slices[this.options.slices.length -1];
    var year_to_print = new Date(last_slice.to).getFullYear();

    this.enrichSlices(this.options.slices);

    this.R.clear();

    this.draw(this.R, this.options.slices, year_to_print, this.options,
              this.slice_active);
  };

  /*
    Parse ISO 8601 date string using custom function, since standard
    parse function is implementation dependent.
    Returns number of milliseconds from midnight January 1 1970.
  */
  Timeline.prototype.dateToUTCMilliseconds = function (date_string) {
    var parts = date_string.match(/(\d+)/g);
    return Date.UTC(
      parts[0],
      parts[1] - 1, // months are 0-based
      parts[2],
      parts[3],
      parts[4],
      parts[5] || 0
    );
  };

  /*
     The purpose of this function is to enrich the array of slices objects
     passed as parameters, so it has side effects over every object by design.
  */
  Timeline.prototype.enrichSlices = function (slices) {
    this.sortSlices(slices);

    var last_slice = slices[slices.length -1];

    for (var a = 0; a < slices.length; a++) {
      var current_slice = slices[a];

      current_slice.from_in_ms = this.dateToUTCMilliseconds(current_slice.from);
      current_slice.to_in_ms = this.dateToUTCMilliseconds(current_slice.to);

      var degrees_boundaries = this.datesToDegrees(
        current_slice.from_in_ms, current_slice.to_in_ms, last_slice.to);
      current_slice.from_degree = degrees_boundaries.from_degree;
      current_slice.to_degree = degrees_boundaries.to_degree;

      if (typeof (current_slice.color) === 'undefined') {
        var color = this.assignColors(a, this.options.colors_default);
        current_slice.color = color;
      }
    }

    // TODO(Mario): this deserves to be in a separate aptly named function,
    // instead of being part of "enrichSlices".
    var missing_slices = [];
    for (var a = 0; a < slices.length; a++) {
      var current_slice = slices[a];
      var next_slice = slices[(a + 1) % slices.length];

      var missing_slice = this
          .computeMissingSlice(current_slice, next_slice,
                               this.options.slice_title_append,
                               this.options.slice_missing_shade);
      if (missing_slice !== null) {
        missing_slices.push(missing_slice);
      }
    }
    Array.prototype.push.apply(slices, missing_slices);

    // TODO(Mario): this has to be done after all slices are done, but will
    // refactor everything in order to be more efficient.
    for (var a = 0; a < slices.length; a++) {
      var current_slice = slices[a];

      var readable_range = this.toReadableTimeRange(current_slice.from_in_ms,
                                                    current_slice.to_in_ms);
      current_slice.timerange = readable_range;

      var is_active_slice = this.isDateInMsWithinRange(current_slice.from_in_ms,
                                                       current_slice.to_in_ms,
                                                       this.options.now);
      current_slice.active = is_active_slice;
      if (is_active_slice === true) {
        this.slice_active = current_slice;
      }
    }
  };

  Timeline.prototype.sortSlices = function (slices) {
    slices.sort(
      function (a, b) {
        return a.from_in_ms - b.from_in_ms;
      }
    );
  };

  Timeline.prototype.datesToDegrees = function (from_in_ms, to_in_ms, time_end) {
    var MILLISECONDS_IN_ONE_DEGREE = 87600000 // 1000 * 60 * 60 * 24 * 365 / 360
    var time_zero_degrees;

    // 90 degrees is first day of last year
    // 0 degrees will be first day of last year minus 3 months
    time_zero_degrees = Date.UTC(new Date(time_end).getFullYear() - 1, 9, 1);

    return {
      from_degree: ((from_in_ms - time_zero_degrees) /
          MILLISECONDS_IN_ONE_DEGREE),
      to_degree: (to_in_ms - time_zero_degrees) / MILLISECONDS_IN_ONE_DEGREE
     };
  };

  Timeline.prototype.assignColors = function (index, colors) {
    return colors[index % colors.length];
  };

  Timeline.prototype.computeMissingSlice = function (current_slice, next_slice,
                                                     slice_title_append,
                                                     slice_missing_shade) {

    if (current_slice.to_in_ms != next_slice.from_in_ms) {
      return {
        title: next_slice.title + slice_title_append,
        from: current_slice.to,
        to: next_slice.from,
        from_in_ms: current_slice.to_in_ms,
        to_in_ms: next_slice.from_in_ms,
        from_degree: current_slice.to_degree,
        to_degree: next_slice.from_degree,
        color: (
          this.shadeColor(next_slice.color, slice_missing_shade)
        )
      };
    }
    return null;
  };

  Timeline.prototype.shadeColor = function (color, percent) {
    // Source http://stackoverflow.com/a/13542669/1194327
    var num = parseInt(color.slice(1), 16);
    var amt = Math.round(2.55 * percent);
    var R = (num >> 16) + amt;
    var B = (num >> 8 & 0x00FF) + amt;
    var G = (num & 0x0000FF) + amt;

    return "#" + (
      0x1000000 +
      (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
      (B < 255 ? B < 1 ? 0 : B : 255) * 0x100 +
      (G < 255 ? G < 1 ? 0 : G : 255)
    ).toString(16).slice(1);
  };

  Timeline.prototype.toReadableTimeRange = function (from_in_ms, to_in_ms) {
    var MONTH_NAMES = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December"
    ];

    var date_from = new Date(from_in_ms);
    var date_to = new Date(to_in_ms);

    var date_from_day = date_from.getUTCDate();
    var date_from_month = date_from.getUTCMonth();
    var date_to_day = date_to.getUTCDate();
    var date_to_month = date_to.getUTCMonth();

    if (date_from_month == date_to_month) {
      return [
        MONTH_NAMES[date_from_month],
        ' ',
        date_from_day,
        ' - ',
        date_to_day
      ].join('');
    } else {
      return [
        MONTH_NAMES[date_from_month],
        ' ',
        date_from_day,
        ' - ',
        MONTH_NAMES[date_to_month],
        ' ',
        date_to_day
      ].join('');
    }
  };

  Timeline.prototype.isDateInMsWithinRange = function (from_in_ms, to_in_ms,
                                                       now) {
    return from_in_ms < now && to_in_ms > now;
  };

  Timeline.prototype.draw = function (R, slices, year_to_print, options,
                                      slice_active) {
    // Add top lines
    R.path('M0 0.5L187 0.5').attr({stroke: options.color_blue});
    R.path('M0 1.5L187 1.5').attr({stroke: options.color_blue_light});

    for (var i in slices) {
      this.draw_slice(R, slices[i], options, slice_active);
    }

    // Draw inner circle
    R
    .circle(94, 78, 33)
    .attr({fill: "#ffffff", "stroke-width": 0}),

    // Draw inner text
    R
    .text(94, 78, year_to_print)
    .attr({
      font: [
        '700',
        '18px',
        [
          '"Helvetica Neue"',
          'Helvetica',
          '"Arial Unicode MS"',
          'Arial',
          'sans-serif'
        ].join(',')
      ].join(' '),
      fill: options.color_blue
    }),

    // Draw inner line
    R
    .path('M94 91L94 111')
    .attr({stroke: options.color_gray})
  };

  Timeline.prototype.draw_slice = function (R, slice, options, slice_active) {
    var that = this;

    // Create wires
    slice._wires = this
      .draw_wires(
        R,
        94,
        78,
        67,
        slice.from_degree,
        slice.to_degree,
        options.color_blue,
        options.color_blue_light
      )
      .attr({opacity: 0});

    // Create arc
    slice._arc = R.path()
      .attr({
        arc: [94, 78, 64, slice.from_degree, slice.to_degree],
        "stroke-width": 3,
        stroke: options.color_blue,
        opacity: options.slice_faded_opacity
      });

    // Create slice
    slice._piece = R.path()
      .attr({
        segment: [94, 78, 59, slice.from_degree, slice.to_degree],
        "stroke-width": 0,
        fill: slice.color,
        opacity: options.slice_faded_opacity
      })
      .mouseover(function () {
        // change opacity
        this.attr({opacity: 1});
        // change html contents
        options.title_element.html(slice.title);
        options.timerange_element.html(slice.timerange);
        slice._wires.attr({opacity: 1});
        slice._arc.attr({opacity: 1});

        if (slice != slice_active) {
          slice_active._piece.attr({opacity: options.slice_faded_opacity});
          slice_active._wires.attr({opacity: 0});
          slice_active._arc.attr({opacity: options.slice_faded_opacity});
        }
      }).mouseout(function () {
        // change opacity
        this.attr({opacity: options.slice_faded_opacity});
        // change html contents
        options.title_element.html(options.timeline_title_default);
        options.timerange_element.html(options.timeline_timerange_default);
        slice._wires.attr({opacity: 0});
        slice._arc.attr({opacity: options.slice_faded_opacity});

        slice_active._piece.attr({opacity: 1});
        slice_active._wires.attr({opacity: 1});
        slice_active._arc.attr({opacity: 1});
      });

    if (slice.active === true) {
      slice._piece.attr({opacity: 1});
      slice._wires.attr({opacity: 1});
      slice._arc.attr({opacity: 1});

      // Store default title and timeline
      options.timeline_title_default = slice.title;
      options.timeline_timerange_default = slice.timerange;

      // Set default title and timeline
      options.title_element.html(slice.title);
      options.timerange_element.html(slice.timerange);
    }

    return slice;
  };

  Timeline.prototype.draw_wires = function (R, x, y, r, a1, a2, color_w1,
                                            color_w2) {
    var wires = R.set();
    var a_middle = (((a1 + a2) / 2) + (a2 < a1 ? 180 : 0)) % 360;
    var a_middle_rad = (a_middle % 360) * Math.PI / 180;
    var is_bottom = a_middle <= 180;
    var is_left = a_middle > 90 && a_middle < 270;

    if (is_bottom) {
      // First line
      wires.push(R.path().attr({
        path: [
          [
            "M",
            ~~((is_left ? 6 : -6) + x + r * Math.cos(a_middle_rad)),
            ~~(y + 2 + r * Math.sin(a_middle_rad)) + 0.5
          ],
          [
            "l",
            (
              ~~(is_left ? (-r - 10 - r * Math.cos(a_middle_rad)) :
              (r + 10 - r * Math.cos(a_middle_rad))) + 0.5
            ),
            0
          ],
          [
            "l",
            0,
            -~~(y + 2 + r * Math.sin(a_middle_rad)) - 0.5
          ]
        ],
        stroke: color_w1
      }));

      // Second line
      wires.push(R.path().attr({
        path: [
          [
            "M",
            ~~((is_left ? 6 : -6) + x + r * Math.cos(a_middle_rad)),
            ~~(y + 2 + r * Math.sin(a_middle_rad)) + 1.5
          ],
          [
            "l",
            (
              ~~(is_left ? (-r - 11 - r * Math.cos(a_middle_rad)) :
              (r + 11 - r * Math.cos(a_middle_rad))) + 0.5
            ),
            0
          ],
          [
            "l",
            0,
            -~~(y + 2 + r * Math.sin(a_middle_rad)) - 0.5
          ]
        ],
        stroke: color_w2
      }));
    } else {
      // First line
      wires.push(R.path().attr({
        path: [
          [
            "M",
            ~~(x + r * Math.cos(a_middle_rad)) + 0.5,
            ~~(y + 4 + r * Math.sin(a_middle_rad))
          ],
          [
            "L",
            ~~(x + r * Math.cos(a_middle_rad)) + 0.5,
            0
          ]
        ],
        stroke: color_w1
      }));

      // Second line
      wires.push(R.path().attr({
        path: [
          [
            "M",
            ~~(x + r * Math.cos(a_middle_rad)) + 0.5 - (is_left ? 1 : -1),
            ~~(y + 4 + r * Math.sin(a_middle_rad))
          ],
          [
            "L",
            ~~(x + r * Math.cos(a_middle_rad)) + 0.5 - (is_left ? 1 : -1),
            1
          ]
        ],
        stroke: color_w2
      }));
    }

    return wires;
  }

 /* Timeline PLUGIN DEFINITION
  * ===================== */

  $.fn.timeline = function (option) {
    var parent_arguments = Array.prototype.slice.call(arguments);

    return this.each(function () {
      var $this = $(this),
        data = $this.data('timeline'),
        options = typeof option == 'object' && option;

      if (!data) {
        $this.data('timeline', (data = new Timeline(this, options)));
      }

      if (typeof option == 'string') {
        data[option].apply(data, parent_arguments.slice(1));
      }
    });
  };
}(window.jQuery);
