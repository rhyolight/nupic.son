module.exports = function(grunt) {
	grunt.initConfig({
		meta: {
			package: grunt.file.readJSON('package.json'),
			src: {
        css_dir: 'app/soc/content/css',
				js_dir: './app/soc/content/js',
        tests_dir: './tests',
				js_files: '<%= meta.src.js_dir %>/**/*.js',
				test_specs: '<%= meta.src.tests_dir %>/**/*_spec.js',
        test_all: '<%= meta.src.tests_dir %>/**/*.js'
			},
			reports: {
        reports_dir: 'js_reports',
        documentation: '<%= meta.reports.reports_dir %>/documentation',
				coverage: '<%= meta.reports.reports_dir %>/coverage',
				plato_source: '<%= meta.reports.reports_dir %>/plato',
				plato_tests: '<%= meta.reports.reports_dir %>/plato_tests',
        yuidoc: '<%= meta.reports.documentation %>/yuidoc'
			},
      build: {
        build_dir: './build',
        css_dir: '<%= meta.build.build_dir %>/soc/content/css/gsoc'
      }
		},
		jasmine: {
			coverage: {
				src: [
          '<%= meta.src.js_dir %>/melange.js',
          '<%= meta.src.js_dir %>/melange.list.js'
        ],
				options: {
					specs: '<%= meta.src.test_all %>',
					template: require('grunt-template-jasmine-istanbul'),
					templateOptions: {
						coverage: '<%= meta.reports.coverage %>/coverage.json',
						report: [
							{
								type: 'html',
								options: {
									dir: '<%= meta.reports.coverage %>/html'
								}
							}
						]
					},
          helpers: [
            './app/jquery/jquery-1.6.4.js',
            './app/jlinq/jLinq-2.2.1.js'
          ]
				}
			}
		},
    less: {
      development: {
        options: {
          paths: ['<%= meta.src.css_dir %>']
        },
        files: {
          '<%= meta.src.css_dir %>/gsoc/buttons.css': '<%= meta.src.css_dir %>/less/buttons.less',
          '<%= meta.src.css_dir %>/gsoc/forms.css': '<%= meta.src.css_dir %>/less/forms.less',
          '<%= meta.src.css_dir %>/gsoc/global.css': '<%= meta.src.css_dir %>/less/global.less',
          '<%= meta.src.css_dir %>/gsoc/map.css': '<%= meta.src.css_dir %>/less/map.less',
          '<%= meta.src.css_dir %>/gsoc/menu.css': '<%= meta.src.css_dir %>/less/menu.less',
          '<%= meta.src.css_dir %>/gsoc/readonly.css': '<%= meta.src.css_dir %>/less/readonly.less',
          '<%= meta.src.css_dir %>/gsoc/structure.css': '<%= meta.src.css_dir %>/less/structure.less',
          '<%= meta.src.css_dir %>/gsoc/surveys.css': '<%= meta.src.css_dir %>/less/surveys.less',
          '<%= meta.src.css_dir %>/gsoc/tables.css': '<%= meta.src.css_dir %>/less/tables.less',
          '<%= meta.src.css_dir %>/gsoc/typography.css': '<%= meta.src.css_dir %>/less/typography.less',
          '<%= meta.src.css_dir %>/gsoc/user-messages.css': '<%= meta.src.css_dir %>/less/user-messages.less'
        }
      },
      production: {
        options: {
          paths: ['<%= meta.src.css_dir %>']
        },
        files: {
          '<%= meta.build.css_dir %>/buttons.css': '<%= meta.src.css_dir %>/less/buttons.less',
          '<%= meta.build.css_dir %>/forms.css': '<%= meta.src.css_dir %>/less/forms.less',
          '<%= meta.build.css_dir %>/global.css': '<%= meta.src.css_dir %>/less/global.less',
          '<%= meta.build.css_dir %>/map.css': '<%= meta.src.css_dir %>/less/map.less',
          '<%= meta.build.css_dir %>/menu.css': '<%= meta.src.css_dir %>/less/menu.less',
          '<%= meta.build.css_dir %>/readonly.css': '<%= meta.src.css_dir %>/less/readonly.less',
          '<%= meta.build.css_dir %>/structure.css': '<%= meta.src.css_dir %>/less/structure.less',
          '<%= meta.build.css_dir %>/surveys.css': '<%= meta.src.css_dir %>/less/surveys.less',
          '<%= meta.build.css_dir %>/tables.css': '<%= meta.src.css_dir %>/less/tables.less',
          '<%= meta.build.css_dir %>/typography.css': '<%= meta.src.css_dir %>/less/typography.less',
          '<%= meta.build.css_dir %>/user-messages.css': '<%= meta.src.css_dir %>/less/user-messages.less'
        }
      }
    },
    plato: {
      source_files: {
        options : {
          complexity : {
            logicalor : false,
            forin : true,
            newmi: true,
            switchcase : false,
            trycatch : true
          }
        },
        files: {
          '<%= meta.reports.plato_source %>': ['<%= meta.src.js_files %>']
        }
      },
      test_files: {
        options : {
          complexity : {
            logicalor : false,
            forin : true,
            newmi: true,
            switchcase : false,
            trycatch : true
          }
        },
        files: {
          '<%= meta.reports.plato_tests %>': ['<%= meta.src.test_specs %>']
        }
      }
    },
    yuidoc: {
      compile: {
        name: '<%= meta.package.name %>',
        description: '<%= meta.package.description %>',
        options: {
          paths: '<%= meta.src.js_dir %>',
          outdir: '<%= meta.reports.yuidoc %>'
        }
      }
    }
	});

  grunt.loadNpmTasks('grunt-contrib-jasmine');
  grunt.loadNpmTasks('grunt-contrib-yuidoc');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-plato');

  grunt.registerTask('coverage', ['jasmine:coverage']);
  grunt.registerTask('documentation', ['yuidoc']);
  grunt.registerTask('plato_source', ['plato:source_files']);
  grunt.registerTask('plato_tests', ['plato:test_files']);
  grunt.registerTask('build', ['less:production']);
};