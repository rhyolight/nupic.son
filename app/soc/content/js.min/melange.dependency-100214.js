(function(){if(window.melange===undefined)throw new Error("Melange not loaded");var d=window.melange;d.dependency=window.melange.dependency=function(){return new d.dependency};var g=d.logging.debugDecorator(d.dependency);d.error.createErrors([]);var a={};a.google=d.config.google_api_key!==undefined?["http://www.google.com/jsapi?key="+d.config.google_api_key]:["http://www.google.com/jsapi"];a.jquery=d.config.is_local!==undefined&&d.config.is_local===true?["/jquery/jquery-1.5.js"]:["http://ajax.googleapis.com/ajax/libs/jquery/1.5/jquery.min.js"];
a.json=["/json/json2.js"];a.tinymce=["/tiny_mce/tiny_mce.js"];a.purr=[a.jquery,null,"/jquery/jquery-purr.js"];a.spin=[a.jquery,null,"/jquery/jquery-spin-1.1.1.js"];a.bgiframe=[a.jquery,null,"/jquery/jquery-bgiframe.js"];a.ajaxQueue=[a.jquery,null,"/jquery/jquery-ajaxQueue.js"];a.autocomplete=[a.jquery,null,"/jquery/jquery-autocomplete.js"];a.thickbox=[a.jquery,null,"/jquery/jquery-thickbox.js"];a.progressbar=[a.jquery,null,"/jquery/jquery-progressbar.js"];a.jqueryui=[a.jquery,null,"/jquery/jquery-ui.core.js"];
a.jqgrid=[a.jquery,null,"/jquery/jquery-jqgrid.locale-en.js",null,"/jquery/jquery-jqgrid.base.js",null,"/jquery/jquery-jqgrid.custom.js","/jquery/jquery-jqgrid.setcolumns.js"];a.jqgridediting=[a.jqgrid,null,"/jquery/jquery-jqgrid.common.js","/jquery/jquery-jqgrid.formedit.js",null,"/jquery/jquery-jqgrid.searchFilter.js","/jquery/jquery-jqgrid.inlinedit.js",null,"/jquery/jquery-jqgrid.jqDnR.js",null,"/jquery/jquery-jqgrid.jqModal.js"];a.cookie=[a.jquery,null,"/jquery/jquery-cookie.js"];a.jlinq=["/jlinq/jLinq-2.2.1.js"];
a.melange={};a.melange.main=[a.jquery,a.json,a.google,null,"/soc/content/js/melange-091015.js"];a.melange.datetimepicker=[a.jqueryui,null,"/jquery-ui.datetimepicker.js",null,"/soc/content/js/datetimepicker-090825.js",null,"/soc/content/js/datetime-loader-090825.js"];a.melange.menu=[a.cookie,null,"/soc/content/js/menu-110128.js"];a.melange.duplicates=[a.progressbar,null,"/soc/content/js/duplicate-slots-090825.js"];a.melange.form=[a.melange.main];a.melange.list=[a.jqgrid,a.jlinq,null,a.jqgridediting,
null,"/soc/content/js/melange.list-110204.js"];a.melange.tooltip=[a.melange,a.purr,null];a.melange.autocomplete=[a.autocomplete,null,"/soc/content/js/melange.autocomplete-110204.js"];a.melange.graph=[a.melange,a.google,null,"/soc/content/js/melange.graph-100501.js"];a.melange.uploadform=[a.melange,null,"/soc/content/js/upload-form-101205.js"];g.s=a;var i=function(c){for(var b=[],f=0,h=c.length;f<h;f++){var e=c[f];if(typeof e==="object"&&e instanceof Array){e=i(e);b=b.concat(e)}else b.push(e)}return b};
g.loadScripts=function(c){c=i(c);for(var b=0,f=c.length;b<f;b++)if(typeof c[b]=="string")$LAB=$LAB.script(c[b]);else if(c[b])if(typeof c[b]=="object"&&c[b]instanceof g.templateWithContext)$LAB=$LAB.script(c[b].script_template).wait(function(h){return function(){d.templates.setContextToLast(h)}}(c[b].context)).wait();else{if(typeof c[b]=="function")$LAB=$LAB.wait(c[b])}else $LAB=$LAB.wait()};g.templateWithContext=function(c,b){this.script_template=c;this.context=b}})();
