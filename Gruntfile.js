module.exports = function(grunt) {
	grunt.initConfig({
		meta: {
			package: grunt.file.readJSON('package.json'),
			src: {
        css_dir: 'app/soc/content/css',
        css_soc_dir: '<%= meta.src.css_dir %>/soc',
        css_gsoc_dir: '<%= meta.src.css_dir %>/gsoc',
        css_gci_dir: '<%= meta.src.css_dir %>/gci',
        less_dir: 'app/soc/content/less',
        less_soc_dir: '<%= meta.src.less_dir %>/soc',
        less_gsoc_dir: '<%= meta.src.less_dir %>/gsoc',
        less_gci_dir: '<%= meta.src.less_dir %>/gci',
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
        css_dir: '<%= meta.build.build_dir %>/soc/content/css',
        css_gsoc_dir: '<%= meta.build.css_dir %>/gsoc',
        css_soc_dir: '<%= meta.build.css_dir %>/soc',
        css_gci_dir: '<%= meta.build.css_dir %>/gci'
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
          paths: ['<%= meta.src.less_dir %>']
        },
        files: {
          /* Development common SOC files */
          '<%= meta.src.css_soc_dir %>/search_page.css': '<%= meta.src.less_soc_dir %>/search_page.less',
          '<%= meta.src.css_soc_dir %>/server-error-style.css': '<%= meta.src.less_soc_dir %>/server-error-style.less',
          '<%= meta.src.css_soc_dir %>/user-error-style.css': '<%= meta.src.less_soc_dir %>/user-error-style.less',
          /* Development GSOC files */
          '<%= meta.src.css_gsoc_dir %>/admin.css': '<%= meta.src.less_gsoc_dir %>/admin.less',
          '<%= meta.src.css_gsoc_dir %>/buttons.css': '<%= meta.src.less_gsoc_dir %>/buttons.less',
          '<%= meta.src.css_gsoc_dir %>/dashboard.css': '<%= meta.src.less_gsoc_dir %>/dashboard.less',
          '<%= meta.src.css_gsoc_dir %>/forms.css': '<%= meta.src.less_gsoc_dir %>/forms.less',
          '<%= meta.src.css_gsoc_dir %>/global.css': '<%= meta.src.less_gsoc_dir %>/global.less',
          '<%= meta.src.css_gsoc_dir %>/map.css': '<%= meta.src.less_gsoc_dir %>/map.less',
          '<%= meta.src.css_gsoc_dir %>/menu.css': '<%= meta.src.less_gsoc_dir %>/menu.less',
          '<%= meta.src.css_gsoc_dir %>/others.css': '<%= meta.src.less_gsoc_dir %>/others.less',
          '<%= meta.src.css_gsoc_dir %>/readonly.css': '<%= meta.src.less_gsoc_dir %>/readonly.less',
          '<%= meta.src.css_gsoc_dir %>/structure.css': '<%= meta.src.less_gsoc_dir %>/structure.less',
          '<%= meta.src.css_gsoc_dir %>/surveys.css': '<%= meta.src.less_gsoc_dir %>/surveys.less',
          '<%= meta.src.css_gsoc_dir %>/tables.css': '<%= meta.src.less_gsoc_dir %>/tables.less',
          '<%= meta.src.css_gsoc_dir %>/typography.css': '<%= meta.src.less_gsoc_dir %>/typography.less',
          '<%= meta.src.css_gsoc_dir %>/user-messages.css': '<%= meta.src.less_gsoc_dir %>/user-messages.less',
          /* Development GCI files */
          '<%= meta.src.css_gci_dir %>/account_deletion.css': '<%= meta.src.less_gci_dir %>/account_deletion.less',
          '<%= meta.src.css_gci_dir %>/buttons.css': '<%= meta.src.less_gci_dir %>/buttons.less',
          '<%= meta.src.css_gci_dir %>/dashboard.css': '<%= meta.src.less_gci_dir %>/dashboard.less',
          '<%= meta.src.css_gci_dir %>/document.css': '<%= meta.src.less_gci_dir %>/document.less',
          '<%= meta.src.css_gci_dir %>/forms.css': '<%= meta.src.less_gci_dir %>/forms.less',
          '<%= meta.src.css_gci_dir %>/ie.css': '<%= meta.src.less_gci_dir %>/ie.less',
          '<%= meta.src.css_gci_dir %>/others.css': '<%= meta.src.less_gci_dir %>/others.less',
          '<%= meta.src.css_gci_dir %>/readonly.css': '<%= meta.src.less_gci_dir %>/readonly.less',
          '<%= meta.src.css_gci_dir %>/style.css': '<%= meta.src.less_gci_dir %>/style.less'
        }
      },
      production: {
        options: {
          paths: ['<%= meta.src.css_dir %>']
        },
        files: {
          /* Build common SOC files */
          '<%= meta.build.css_soc_dir %>/search_page.css': '<%= meta.src.less_soc_dir %>/search_page.less',
          '<%= meta.build.css_soc_dir %>/server-error-style.css': '<%= meta.src.less_soc_dir %>/server-error-style.less',
          '<%= meta.build.css_soc_dir %>/user-error-style.css': '<%= meta.src.less_soc_dir %>/user-error-style.less',
          /* Build GSOC files */
          '<%= meta.build.css_gsoc_dir %>/admin.css': '<%= meta.src.less_gsoc_dir %>/admin.less',
          '<%= meta.build.css_gsoc_dir %>/buttons.css': '<%= meta.src.less_gsoc_dir %>/buttons.less',
          '<%= meta.build.css_gsoc_dir %>/dashboard.css': '<%= meta.src.less_gsoc_dir %>/dashboard.less',
          '<%= meta.build.css_gsoc_dir %>/forms.css': '<%= meta.src.less_gsoc_dir %>/forms.less',
          '<%= meta.build.css_gsoc_dir %>/global.css': '<%= meta.src.less_gsoc_dir %>/global.less',
          '<%= meta.build.css_gsoc_dir %>/map.css': '<%= meta.src.less_gsoc_dir %>/map.less',
          '<%= meta.build.css_gsoc_dir %>/menu.css': '<%= meta.src.less_gsoc_dir %>/menu.less',
          '<%= meta.build.css_gsoc_dir %>/others.css': '<%= meta.src.less_gsoc_dir %>/others.less',
          '<%= meta.build.css_gsoc_dir %>/readonly.css': '<%= meta.src.less_gsoc_dir %>/readonly.less',
          '<%= meta.build.css_gsoc_dir %>/structure.css': '<%= meta.src.less_gsoc_dir %>/structure.less',
          '<%= meta.build.css_gsoc_dir %>/surveys.css': '<%= meta.src.less_gsoc_dir %>/surveys.less',
          '<%= meta.build.css_gsoc_dir %>/tables.css': '<%= meta.src.less_gsoc_dir %>/tables.less',
          '<%= meta.build.css_gsoc_dir %>/typography.css': '<%= meta.src.less_gsoc_dir %>/typography.less',
          '<%= meta.build.css_gsoc_dir %>/user-messages.css': '<%= meta.src.less_gsoc_dir %>/user-messages.less',
          /* Development GCI files */
          '<%= meta.build.css_gci_dir %>/account_deletion.css': '<%= meta.src.less_gci_dir %>/account_deletion.less',
          '<%= meta.build.css_gci_dir %>/buttons.css': '<%= meta.src.less_gci_dir %>/buttons.less',
          '<%= meta.build.css_gci_dir %>/dashboard.css': '<%= meta.src.less_gci_dir %>/dashboard.less',
          '<%= meta.build.css_gci_dir %>/document.css': '<%= meta.src.less_gci_dir %>/document.less',
          '<%= meta.build.css_gci_dir %>/forms.css': '<%= meta.src.less_gci_dir %>/forms.less',
          '<%= meta.build.css_gci_dir %>/ie.css': '<%= meta.src.less_gci_dir %>/ie.less',
          '<%= meta.build.css_gci_dir %>/others.css': '<%= meta.src.less_gci_dir %>/others.less',
          '<%= meta.build.css_gci_dir %>/readonly.css': '<%= meta.src.less_gci_dir %>/readonly.less',
          '<%= meta.build.css_gci_dir %>/style.css': '<%= meta.src.less_gci_dir %>/style.less'
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