(function(){if(window.melange===undefined)throw new Error("Melange not loaded");var a=window.melange;a.autocomplete=window.melange.autocomplete=function(){return new a.autocomplete};var e=a.logging.debugDecorator(a.autocomplete);a.error.createErrors([]);e.makeAutoComplete=function(f,g){jQuery.getJSON(g,function(c){var d={matchContains:true,formatItem:function(b){return b.link_id+" ("+b.title+")"},formatResult:function(b){return b.link_id}};c.autocomplete_options!==undefined&&jQuery.extend(d,c.autocomplete_options);
jQuery("#"+f).autocomplete(c.data,d)})}})();
