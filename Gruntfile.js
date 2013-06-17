module.exports = function(grunt) {
	grunt.initConfig({
		meta: {
			package: grunt.file.readJSON('package.json'),
			src: {
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
  grunt.loadNpmTasks('grunt-plato');

	grunt.registerTask('coverage', ['jasmine:coverage']);
  grunt.registerTask('documentation', ['yuidoc']);
	grunt.registerTask('plato_source', ['plato:source_files']);
	grunt.registerTask('plato_tests', ['plato:test_files']);
};