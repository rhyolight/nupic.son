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
    this.init(element, options);
  };

  Timeline.prototype = {

    constructor: Timeline,

    options: {
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

    slice_active: null,
    slices: []
  };

  Timeline.prototype.init = function (element, options) {
    // transform date into milliseconds
    if (
      (typeof(options.now) !== 'undefined') &&
      (isNaN(parseInt(options.now, 10)) || !isFinite(options.now))
    ) {
      options.now = this.dateToUTCMilliseconds(options.now);
    }

    $.extend(this.options, options);

    this.R = this.enrichRaphaelObjectWithCustomAttributes(Raphael(element));

    this.enrichSlices(this.options.slices);

    this.draw(this.options.slices);
  };

  /*
     The purpose of this function is to enrich the array of slices objects
     passed as parameters, so it has side effects over every object by design.
  */
  Timeline.prototype.enrichSlices = function(slices) {
    this.sortSlices(slices);

    var last_slice = slices[slices.length -1];

    for (var a = 0; a < slices.length; a++) {
      var current_slice = slices[a];

      var grades_boundaries = this.datesToGrades(
        current_slice.from, current_slice.to, last_slice.to);
      current_slice.from_grade = grades_boundaries.from_grade;
      current_slice.to_grade = grades_boundaries.to_grade;

      var color = this.assignColors(a, this.options.colors_default);
      current_slice.color = color;
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
  };

  Timeline.prototype.sortSlices = function(slices) {
    var _timeline = this;
    // Sort slices
    slices.sort(
      function (a, b) {
        return (
          _timeline.dateToUTCMilliseconds(a.from) -
          _timeline.dateToUTCMilliseconds(b.from)
        );
      }
    );
  }

  Timeline.prototype.datesToGrades = function (from, to, time_end) {
    var time_zero_grade;
    var millisecondsInOneGrade = 1000 * 60 * 60 * 24 * 365 / 360;

    // 90 grades is first day of last year
    // 0 grades will be first day of last year minus 3 months
    time_zero_grade = Date.UTC(new Date(time_end).getFullYear() - 1, 9, 1);

    // Store current year
    this.year = new Date(time_end).getFullYear();

    return {
      from_grade:
        (
          (this.dateToUTCMilliseconds(from) - time_zero_grade)
          / millisecondsInOneGrade
        ),
      to_grade:
        (
          (this.dateToUTCMilliseconds(to) - time_zero_grade)
          / millisecondsInOneGrade
        )
     };
  };

  Timeline.prototype.assignColors = function(index, colors) {
    return colors[index % colors.length];
  };


  Timeline.prototype.draw = function (slices) {
    this.clean();

    var options = this.options;
    var that = this;
    var i;

    slices = this.computeTimeRanges(slices);

    slices = this.setActiveSlice(slices, this.options.now);

    // Add top lines
    this.R.path('M0 0.5L187 0.5').attr({stroke: options.color_blue});
    this.R.path('M0 1.5L187 1.5').attr({stroke: options.color_blue_light});

    for (i in slices) {
      // Draw
      this.slices.push(this.draw_slice(slices[i]));
    }

    // Draw inner circle
    this.inner = {
      circle: that.R
              .circle(94, 78, 33)
              .attr({fill: "#ffffff", "stroke-width": 0}),
      text: that.R
            .text(94, 78, that.year)
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
      line: that.R.path('M94 91L94 111').attr({stroke: options.color_gray})
    };
  };

  Timeline.prototype.draw_wires = function (x, y, r, a1, a2, color_w1,
                                            color_w2) {
    var wires = this.R.set();
    var a_middle = (((a1 + a2) / 2) + (a2 < a1 ? 180 : 0)) % 360;
    var a_middle_rad = (a_middle % 360) * Math.PI / 180;
    var is_bottom = a_middle <= 180;
    var is_left = a_middle > 90 && a_middle < 270;

    color_w1 = color_w1 || this.options.color_blue;
    color_w2 = color_w2 || this.options.color_blue_light;

    if (is_bottom) {
      // First line
      wires.push(this.R.path().attr({
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
      wires.push(this.R.path().attr({
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
      wires.push(this.R.path().attr({
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
      wires.push(this.R.path().attr({
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

  Timeline.prototype.draw_slice = function (slice) {
    var options = this.options;
    var that = this;

    // Create wires
    slice._wires = this
      .draw_wires(
        94,
        78,
        67,
        slice.from_grade,
        slice.to_grade,
        options.color_blue,
        options.color_blue_light
      )
      .attr({opacity: 0});

    // Create arc
    slice._arc = this.R.path()
      .attr({
        arc: [94, 78, 64, slice.from_grade, slice.to_grade],
        "stroke-width": 3,
        stroke: options.color_blue,
        opacity: options.slice_faded_opacity
      });

    // Create slice
    slice._piece = this.R.path()
      .attr({
        segment: [94, 78, 59, slice.from_grade, slice.to_grade],
        "stroke-width": 0,
        fill: slice.color,
        opacity: options.slice_faded_opacity
      })
      .mouseover(function () {
        // change opacity
        this.attr({opacity: 1});
        // change html contents
        options.title_element.innerHTML = slice.title;
        options.timerange_element.innerHTML = slice.timerange;
        slice._wires.attr({opacity: 1});
        slice._arc.attr({opacity: 1});

        if (slice != that.slice_active) {
          that.slice_active._piece.attr({opacity: options.slice_faded_opacity});
          that.slice_active._wires.attr({opacity: 0});
          that.slice_active._arc.attr({opacity: options.slice_faded_opacity});
        }
      }).mouseout(function () {
        // change opacity
        this.attr({opacity: options.slice_faded_opacity});
        // change html contents
        options.title_element.innerHTML = options.timeline_title_default;
        options.timerange_element.innerHTML =
             options.timeline_timerange_default;
        slice._wires.attr({opacity: 0});
        slice._arc.attr({opacity: options.slice_faded_opacity});

        that.slice_active._piece.attr({opacity: 1});
        that.slice_active._wires.attr({opacity: 1});
        that.slice_active._arc.attr({opacity: 1});
      });

    if (slice.active === true) {
      this.slice_active = slice;
      slice._piece.attr({opacity: 1});
      slice._wires.attr({opacity: 1});
      slice._arc.attr({opacity: 1});

      // Store default title and timeline
      options.timeline_title_default = slice.title;
      options.timeline_timerange_default = slice.timerange;

      // Set default title and timeline
      options.title_element.innerHTML = slice.title;
      options.timerange_element.innerHTML = slice.timerange;
    }

    return slice;
  };

  Timeline.prototype.clean = function () {
    $.each(this.slices, function (index, slice) {
      // Remove each Raphael object and set
      slice._wires.remove();
      slice._arc.remove();
      slice._piece.remove();
    });

    // Empty array
    this.slices = [];
  };

  Timeline.prototype.computeMissingSlice = function (current_slice, next_slice,
                                                     slice_title_append,
                                                     slice_missing_shade) {
    if (
      this.dateToUTCMilliseconds(current_slice.to) !=
      this.dateToUTCMilliseconds(next_slice.from)
    ) {
      return {
        title: next_slice.title + slice_title_append,
        from: current_slice.to,
        to: next_slice.from,
        from_grade: current_slice.to_grade,
        to_grade: next_slice.from_grade,
        color: (
          this.shadeColor(next_slice.color, slice_missing_shade)
        )
      };
    }
    return null;
  };

  Timeline.prototype.computeTimeRanges = function (slices) {
    var month_names = [
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

    for (var i = slices.length - 1; i >= 0; i--) {
      if (slices[i].timerange === undefined) {
        var date_from = new Date(this.dateToUTCMilliseconds(slices[i].from));
        var date_to = new Date(this.dateToUTCMilliseconds(slices[i].to));

        if (date_from.getUTCMonth() == date_to.getUTCMonth()) {
          slices[i].timerange = [
            month_names[date_from.getUTCMonth()],
            ' ',
            date_from.getUTCDate(),
            ' - ',
            date_to.getUTCDate()
          ].join('');
        } else {
          slices[i].timerange = [
            month_names[date_from.getUTCMonth()],
            ' ',
            date_from.getUTCDate(),
            ' - ',
            month_names[date_to.getUTCMonth()],
            ' ',
            date_to.getUTCDate()
          ].join('');
        }
      }
    }

    return slices;
  };

  /*
    Parse yyyy-mm-dd hh:mm:ss using custom function, since standard parse
    function is implementation dependent.
    Returns number of milliseconds from midnight January 1 1970.
  */
  Timeline.prototype.dateToUTCMilliseconds = function (date) {
    var parts = date.match(/(\d+)/g);
    return Date.UTC(
      parts[0],
      parts[1] - 1, // months are 0-based
      parts[2],
      parts[3],
      parts[4],
      parts[5] || 0
    );
  };

  Timeline.prototype.setActiveSlice = function (slices, now) {
    var slices_count = slices.length;

    // Find active slice and set it as active
    for (var index = 0; index < slices_count; index++) {
      if (
        this.dateToUTCMilliseconds(slices[index].from) < this.options.now &&
        this.dateToUTCMilliseconds(slices[index].to) > this.options.now
      ) {
        slices[index].active = true;
        break;
      }
    }

    return slices;
  }

  Timeline.prototype.shadeColor = function(color, percent) {
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

  $.fn.timeline.Constructor = Timeline;

}(window.jQuery);
