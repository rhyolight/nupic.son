(function(){function E(j,h,r,p){var b=this,y={datatype:F,viewrecords:true},v={edit:false,add:false,del:false,refreshtext:"Refresh",searchtext:"Filter",afterRefresh:function(){b.refreshData();b.jqgrid.object.trigger("reloadGrid")}};j=j;h=h;this.configuration=r;this.operations=p;this.jqgrid={id:null,object:null,options:null,last_selected_row:null,editable_columns:[],dirty_fields:{},pager:{id:null,options:null}};this.data={data:[],all_data:[],filtered_data:null};var x={enableDisableButtons:function(a){return function(c){function i(m){m=
jQuery("#"+a.jqgrid.id).jqGrid("getRowData",m);var d=m.key.toString(),e=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(d);if(e!==null)d=e[2];var k=u.from(a.data.all_data).equals("columns.key",d).select()[0];if(a.jqgrid.dirty_fields[d]===undefined)a.jqgrid.dirty_fields[d]=[];var o=[],s=[];jQuery.each(m,function(l,q){q=q.toString();var C=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(q);if(C!==null)q=C[2];q!=k.columns[l]?o.push(l):s.push(l)});jQuery.each(o,function(l,q){jQuery.inArray(q,a.jqgrid.dirty_fields[d])===
-1&&a.jqgrid.dirty_fields[d].push(q)});jQuery.each(s,function(l,q){l=jQuery.inArray(q,a.jqgrid.dirty_fields[d]);l!==-1&&a.jqgrid.dirty_fields[d].splice(l,1)});a.jqgrid.dirty_fields[d].length===0&&delete a.jqgrid.dirty_fields[d];jQuery.each(a.operations.buttons,function(l,q){if(q.type==="post_edit"){l=jQuery("#"+a.jqgrid.id+"_buttonOp_"+q.id);D(a.jqgrid.dirty_fields)?l.attr("disabled","disabled"):l.removeAttr("disabled")}})}var g=a.jqgrid.object.jqGrid("getGridParam","multiselect")?"selarrrow":"selrow",
f=a.jqgrid.object.jqGrid("getGridParam",g);f instanceof Array||(f=[f]);if(f.length===1)if(c&&c!==a.jqgrid.last_selected_row){jQuery("#"+a.jqgrid.id).restoreRow(a.jqgrid.last_selected_row);jQuery("#"+a.jqgrid.id).jqGrid("editRow",c,true,null,null,"clientArray",null,i);a.jqgrid.last_selected_row=c}jQuery.each(a.operations.buttons,function(m,d){m=jQuery("#"+a.jqgrid.id+"_buttonOp_"+d.id);if(d.type!=="post_edit")if(f.length>=d.real_bounds[0]&&f.length<=d.real_bounds[1]){m.removeAttr("disabled");if(d.real_bounds[0]===
1&&d.real_bounds[1]===1&&m.data("melange")!==undefined){var e=a.jqgrid.object.jqGrid("getRowData",f[0]);e=u.from(a.data.all_data).equals("columns.key",e.key).select()[0];var k=m.data("melange").click;m.click(k(e.operations.buttons[d.id].link));m.attr("value",e.operations.buttons[d.id].caption)}}else m.attr("disabled","disabled")})}}(b),global_button_functions:{redirect_simple:function(a){return a.new_window?function(){window.open(a.link)}:function(){window.location.href=a.link}},redirect_custom:function(a){return function(c){return a.new_window?
function(){window.open(c)}:function(){window.location.href=c}}},post:function(a){return function(){var c=n.get(a.idx).jqgrid.object.jqGrid("getGridParam","multiselect")?"selarrrow":"selrow";c=n.get(a.idx).jqgrid.object.jqGrid("getGridParam",c);c instanceof Array||(c=c===null?[]:[c]);var i=[];if(!(c.length<a.real_bounds[0]||c.length>a.real_bounds[1])){jQuery.each(c,function(g,f){var m=jQuery("#"+n.get(a.idx).jqgrid.id).jqGrid("getRowData",f);u.from(n.get(a.idx).all_data).equals("columns.key",m.key).select();
var d={};jQuery.each(a.keys,function(e,k){e=m[k];if(jQuery(e).hasClass("listsnoul"))e=/^<a\b[^>]*>(.*?)<\/a>$/.exec(e)[1];d[k]=e});i.push(d)});if(a.url==="")a.url=window.location.href;jQuery.post(a.url,{xsrf_token:window.xsrf_token,idx:a.idx,button_id:a.button_id,data:JSON.stringify(i)},function(g){if(a.redirect=="true")try{var f=JSON.parse(g);if(f.data.url!==undefined)window.location.href=f.data.url}catch(m){}g=parseInt(a.refresh,10);if(!isNaN(g)){n.get(g).refreshData();jQuery("#"+n.get(g).jqgrid.id).trigger("reloadGrid")}if(a.refresh==
"current"){n.get(a.idx).refreshData();jQuery("#"+n.get(a.idx).jqgrid.id).trigger("reloadGrid")}else if(a.refresh=="all"){g=n.getAll();jQuery.each(g,function(d,e){e.refreshData();jQuery("#"+n.get(d).jqgrid.id).trigger("reloadGrid")})}})}}},post_edit:function(a){return function(){var c=n.get(a.idx).jqgrid,i={};if(!(c.editable_columns.length===0&&D(c.dirty_fields))){for(var g=c.object.jqGrid("getGridParam","records"),f=1;f<=g;f++){var m=jQuery("#"+c.id).jqGrid("getRowData",f),d=m.key.toString(),e=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(d);
if(e!==null)d=e[2];if(c.dirty_fields[d]!==undefined){i[d]={};jQuery.each(c.dirty_fields[d],function(k,o){k=m[o].toString();var s=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(k);if(s!==null)k=s[2];i[d][o]=k});a.keys!==undefined&&jQuery.each(a.keys,function(k,o){if(i[d][o]===undefined){k=m[o].toString();var s=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(k);if(s!==null)k=s[2];i[d][o]=k}})}}if(a.url==="")a.url=window.location.href;jQuery.post(a.url,{xsrf_token:window.xsrf_token,idx:a.idx,button_id:a.button_id,
data:JSON.stringify(i)},function(k){if(a.redirect=="true")try{var o=JSON.parse(k);if(o.data.url!==undefined)window.location.href=o.data.url}catch(s){}k=parseInt(a.refresh,10);if(!isNaN(k)){n.get(k).refreshData();jQuery("#"+n.get(k).jqgrid.id).trigger("reloadGrid")}if(a.refresh=="current"){n.get(a.idx).refreshData();jQuery("#"+n.get(a.idx).jqgrid.id).trigger("reloadGrid")}else if(a.refresh=="all"){k=n.getAll();jQuery.each(k,function(l,q){q.refreshData();jQuery("#"+n.get(l).jqgrid.id).trigger("reloadGrid")})}})}}}},
row_functions:{redirect_custom:function(a){return function(c,i){return a.new_window||i.which===2||i.which===1&&i.ctrlKey?function(){window.open(c)}:function(){window.location.href=c}}}}},B=function(){jQuery("#"+j).replaceWith(['<p id="temporary_list_placeholder_',h,'"></p>','<table id="'+b.jqgrid.id+'"',' cellpadding="0" cellspacing="0"></table>','<div id="'+b.jqgrid.pager.id+'"',' style="text-align:center"></div>'].join(""))},A=function(){var a="",c=0;jQuery("#load_"+b.jqgrid.id).show();var i=function(){var g=
"?";if(window.location.href.indexOf("?")!==-1)g="&";jQuery.ajax({async:true,cache:false,url:[window.location.href,g,"fmt=json&limit=150",a===""?"":"&start="+a,"&idx=",h].join(""),timeout:6E4,tryCount:1,retryLimit:5,error:function(f){if(f.status==500){this.tryCount++;if(this.tryCount<=this.retryLimit)jQuery.ajax(this);else{jQuery("#temporary_list_placeholder_"+h).html('<span style="color:red">Error retrieving data: please refresh the list or the whole page to try again</span>');jQuery("#load_"+b.jqgrid.id).hide()}}else{jQuery("#temporary_list_placeholder_"+
h).html('<span style="color:red">Error retrieving data: please refresh the list or the whole page to try again</span>');jQuery("#load_"+b.jqgrid.id).hide()}},success:function(f){var m=f.next==="done";if(f.data[a]!==undefined){if(b.configuration===null)b.configuration=f.configuration;if(b.operations===null)b.operations=f.operations;jQuery.each(f.data[a],function(){b.data.data.push(this.columns);b.data.all_data.push(this)});b.jqgrid.object===null?z():b.jqgrid.object.trigger("reloadGrid");if(m){jQuery("#temporary_list_placeholder_"+
h).remove();jQuery("#load_"+b.jqgrid.id).hide()}else{a=f.next;setTimeout(i,100);c++}}if(m){jQuery("#temporary_list_placeholder_"+h).remove();jQuery("#load_"+b.jqgrid.id).hide();jQuery("#"+b.jqgrid.id)[0].triggerToolbar();jQuery.each(b.configuration.colModel,function(d,e){e.editable!==undefined&&e.editable===true&&b.jqgrid.editable_columns.push(e.name)});jQuery("#t_"+b.jqgrid.id).children().remove();b.operations!==undefined&&b.operations.buttons!==undefined&&jQuery.each(b.operations.buttons,function(d,
e){d=b.jqgrid.id+"_buttonOp_"+e.id;var k=jQuery("<input type='button' value='"+e.caption+"' style='float:left' id='"+d+"'/>").button();jQuery("#t_"+b.jqgrid.id).append(k);e.parameters.idx=h;if(e.type!=="post_edit"){e.real_bounds=e.bounds;k=e.real_bounds.indexOf("all");if(k!==-1)e.real_bounds[k]=b.jqgrid.object.jqGrid("getGridParam","records");e.parameters.real_bounds=e.real_bounds}if(e.type==="post_edit"||e.real_bounds[0]>0)jQuery("#"+d).attr("disabled","disabled");e.parameters.button_id=e.id;jQuery("#"+
d).click(x.global_button_functions[e.type](e.parameters));e.type=="redirect_custom"&&jQuery("#"+d).data("melange",{click:x.global_button_functions[e.type](e.parameters)})});jQuery("#t_"+b.jqgrid.id).css("padding-bottom","3px");jQuery("#t_"+b.jqgrid.id).append("<input type='button' value='CSV Export' style='float:right;' id='csvexport_"+b.jqgrid.id+"'/>");jQuery("#csvexport_"+b.jqgrid.id).button();jQuery("#csvexport_"+b.jqgrid.id).click(function(){var d=[];d[0]=[];if(b.data.data[0]!==undefined||b.data.filtered_data[0]!==
undefined){var e=b.data.filtered_data||b.data.data;jQuery.each(b.configuration.colNames,function(o,s){o=s;o=o.replace(/\"|&quot;|&#34;/g,'""');if(o.indexOf(",")!==-1||o.indexOf('"')!==-1||o.indexOf("\r\n")!==-1)o='"'+o+'"';d[0].push(o)});d[0]=d[0].join(",");var k=[];jQuery.each(b.configuration.colModel,function(o,s){k.push(s.name)});jQuery.each(e,function(o,s){d[d.length]=[];jQuery.each(k,function(l,q){l=s[q];if(l===null)l="";if(l===undefined)l="";l=l.toString();q=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(l);
if(q!==null)l=q[1];l=l.replace(/\"|&quot;|&#34;/g,'""');if(l.indexOf(",")!==-1||l.indexOf('"')!==-1||l.indexOf("\r\n")!==-1)l='"'+l+'"';d[d.length-1].push(l)});d[d.length-1]=d[d.length-1].join(",")});d=d.join("\r\n");jQuery("#csv_dialog").remove();jQuery("body").append(["<div id='csv_dialog' style='display:none'>  <h3>Now you can copy and paste CSV data from the text area to a new file:</h3>  <textarea style='width:450px;height:250px'>",d,"</textarea></div>"].join(""));jQuery("#csv_dialog").dialog({height:420,
width:500,modal:true,buttons:{Close:function(){jQuery(this).dialog("close")}}})}});jQuery("#t_"+b.jqgrid.id).append("<div style='float:right;margin-right:4px;'><input type='checkbox' id='regexp_"+b.jqgrid.id+"'/>RegExp Search</div>");jQuery("#regexp_"+b.jqgrid.id).click(function(){jQuery("#"+b.jqgrid.id).jqGrid().trigger("reloadGrid")});f=jQuery.Event("melange_list_loaded");f.list_object=b;b.jqgrid.object.trigger(f);f=jQuery("#gview_"+b.jqgrid.id+" .ui-jqgrid-bdiv");f.width(f.width()+1)}}})};setTimeout(i,
100)};this.refreshData=function(){b.data={data:[],all_data:[],filtered_data:null};A()};var w=new (function(){var a=function(i){var g={hidden_columns:{}};jQuery.each(i,function(f,m){g.hidden_columns[m.name]=m.hidden});return g},c=function(i,g){return{sort_settings:{sortname:i,sortorder:g}}};this.saveCurrentTableConfiguration=function(){if(b.jqgrid.object){var i=t.cookie.getCookie(t.cookie.MELANGE_USER_PREFERENCES),g=b.jqgrid.object.jqGrid("getGridParam","colModel"),f=b.jqgrid.object.jqGrid("getGridParam",
"sortname"),m=b.jqgrid.object.jqGrid("getGridParam","sortorder");g=a(g);g=jQuery.extend(c(f,m),g);f={lists_configuration:{}};f.lists_configuration[h]=g;f.lists_configuration=jQuery.extend(i.lists_configuration,f.lists_configuration);t.cookie.saveCookie(t.cookie.MELANGE_USER_PREFERENCES,f,14,window.location.pathname)}};this.getPreviousTableConfiguration=function(i){var g=t.cookie.getCookie(t.cookie.MELANGE_USER_PREFERENCES),f=i.colModel;if(g.lists_configuration[h]!==undefined){jQuery.each(g.lists_configuration[h].hidden_columns,
function(d,e){d=u.from(f).equals("name",d).select()[0]||null;if(d!==null)d.hidden=e});if(g.lists_configuration[h].sort_settings!==undefined){var m=g.lists_configuration[h].sort_settings.sortname;g=g.lists_configuration[h].sort_settings.sortorder;if(u.from(f).equals("name",m).select()[0]!==undefined?true:false){i.sortname=m;i.sortorder=g}}}return i}}),z=function(){b.configuration=w.getPreviousTableConfiguration(b.configuration);var a=jQuery.extend(b.configuration,{postData:{my_index:h},onSelectAll:x.enableDisableButtons,
onSelectRow:x.enableDisableButtons,gridComplete:w.saveCurrentTableConfiguration}),c={caption:"Columns",buttonicon:"ui-icon-calculator",onClickButton:function(){jQuery("#"+b.jqgrid.id).setColumns({colnameview:false,jqModal:true,ShrinkToFit:true,afterSubmitForm:w.saveCurrentTableConfiguration});return false},position:"last",title:"Show/Hide Columns",cursor:"pointer"};jQuery("#"+b.jqgrid.id).jqGrid(jQuery.extend(b.jqgrid.options,a)).jqGrid("navGrid","#"+b.jqgrid.pager.id,b.jqgrid.pager.options,{},{},
{},{closeAfterSearch:true,multipleSearch:true},{}).jqGrid("navButtonAdd","#"+b.jqgrid.pager.id,c);jQuery("#"+b.jqgrid.id).jqGrid("filterToolbar",{searchOnEnter:false});jQuery("#load_"+b.jqgrid.id).closest("div").css("line-height","100%");jQuery("#load_"+b.jqgrid.id).html("<img src='/soc/content/"+t.config.app_version+"/images/jqgrid_loading.gif'></img>");b.jqgrid.object=jQuery("#"+b.jqgrid.id)};this.getDiv=function(){return j};this.getIdx=function(){return h};(function(){jQuery(function(){if(jQuery("#"+
j).length===0)throw new t.error.divNotExistent("Div "+j+" is not existent");b.jqgrid.id="jqgrid_"+j;b.jqgrid.pager.id="jqgrid_pager_"+j;b.jqgrid.options=jQuery.extend(y,{pager:"#"+b.jqgrid.pager.id});b.jqgrid.pager.options=v;n.add(b);B();z();A()})})()}if(window.melange===undefined)throw new Error("Melange not loaded");var t=window.melange;if(window.jLinq===undefined)throw new Error("jLinq not loaded");var u=window.jLinq;t.list=window.melange.list=function(){return new t.list};var G=t.logging.debugDecorator(t.list);
t.error.createErrors(["listIndexNotValid","divNotExistent","indexAlreadyExistent"]);var D=function(j){for(var h in j)return false;return true},F=function(j){var h=j.my_index,r=n.get(h).data.data,p=r,b="",y={eq:{method:"equals",not:false},ne:{method:"equals",not:true},lt:{method:"less",not:false},le:{method:"lessEquals",not:false},gt:{method:"greater",not:false},ge:{method:"greaterEquals",not:false},bw:{method:"startsWith",not:false},bn:{method:"startsWith",not:true},ew:{method:"endsWith",not:false},
en:{method:"endsWith",not:true},cn:{method:"contains",not:false},nc:{method:"contains",not:true},"in":{method:"match",not:false},ni:{method:"match",not:true}};if(j._search&&j.filters){var v=JSON.parse(j.filters);if(v.rules[0].data!==""){b=v.groupOp;if(b==="OR")p={};jQuery.each(v.rules,function(a,c){if(c.op==="in"||c.op==="ni")c.data=c.data.split(",").join("|");p=y[c.op].not?b==="OR"?u.from(p).union(u.from(r).not()[y[c.op].method](c.field,c.data).select()).select():u.from(p).not()[y[c.op].method](c.field,
c.data).select():b==="OR"?u.from(p).union(u.from(r)[y[c.op].method](c.field,c.data).select()).select():u.from(p)[y[c.op].method](c.field,c.data).select()})}}else r[0]!==undefined&&jQuery.each(r[0],function(a){if(j[a]!==undefined){var c=jQuery("#regexp_"+n.get(h).jqgrid.id).is(":checked"),i=false;jQuery.each(n.get(h).configuration.colModel,function(g,f){if(f.editoptions!==undefined&&a===f.name)i=true});p=c||i?u.from(p).match(a,j[a]).select():u.from(p).contains(a,j[a]).select()}});var x=j.sidx;v=j.sord;
jQuery.each(n.get(h).configuration.colModel,function(a,c){if(c.name===x&&(c.sorttype==="integer"||c.sorttype==="int"))jQuery.each(p,function(i,g){i=parseInt(g[x],10);isNaN(i)||(g[x]=i)})});v=v==="asc"?"":"-";if(p.length>0)p=u.from(p).ignoreCase().orderBy(v+x).select();n.get(h).data.filtered_data=p;if(j.rows===-1)j.rows=n.get(h).data.filtered_data.length;v=(j.page-1)*j.rows;for(var B=j.page*j.rows-1,A={page:j.page,total:p.length===0?0:Math.ceil(p.length/j.rows),records:p.length,rows:[]},w=v;w<=B;w++)if(p[w]!==
undefined){var z=[];r[0]!==undefined&&jQuery.each(n.get(h).configuration.colModel,function(a,c){var i;a=n.get(h).data.all_data;for(var g=0;g<a.length;g++)if(a[g].columns.key===p[w].key){i=a[g];break}a=p[w][c.name];if(i.operations!==undefined&&i.operations.row!==undefined&&i.operations.row.link!==undefined){c=c.editable||false;if(a!==null&&a!==undefined&&!c&&a.toString().match(/<a\b[^>]*>.*<\/a>/)===null)a='<a style="display:block;" href="'+i.operations.row.link+'" class="listsnoul">'+a+"</a>"}z.push(a)});
A.rows.push({key:p[w].key,cell:z})}jQuery("#"+n.get(h).jqgrid.id)[0].addJSONData(A)},n=function(){var j=[];return{add:function(h){j[h.getIdx()]=h},get:function(h){return j[h]!==undefined?j[h]:null},getAll:function(){return jQuery.extend({},j)},isExistent:function(h){return j[h]!==undefined?true:false}}}();G.loadList=function(j,h,r){r=parseInt(r,10);h=JSON.parse(h);if(isNaN(r)||r<0)throw new t.error.listIndexNotValid("List index "+r+" is not valid");if(n.isExistent(r))throw new t.error.indexAlreadyExistent("Index "+
r+" is already existent");new E(j,r,h.configuration,h.operations)}})();
