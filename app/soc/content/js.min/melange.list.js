(function(){function D(i,g,p,n){var b=this,x={datatype:E,viewrecords:true},u={edit:false,add:false,del:false,afterRefresh:function(){b.refreshData();b.jqgrid.object.trigger("reloadGrid")}};i=i;g=g;this.configuration=p;this.operations=n;this.jqgrid={id:null,object:null,options:null,last_selected_row:null,editable_columns:[],dirty_fields:{},pager:{id:null,options:null}};this.data={data:[],all_data:[],filtered_data:null};var v={enableDisableButtons:function(a){return function(c){function h(m){var d=
jQuery("#"+a.jqgrid.id).jqGrid("getRowData",m),e=t.from(a.data.all_data).equals("columns.key",d.key).select()[0];if(a.jqgrid.dirty_fields[d.key]===undefined)a.jqgrid.dirty_fields[d.key]=[];var s=[],q=[];jQuery.each(d,function(o,l){l!=e.columns[o]?s.push(o):q.push(o)});jQuery.each(s,function(o,l){jQuery.inArray(l,a.jqgrid.dirty_fields[d.key])===-1&&a.jqgrid.dirty_fields[d.key].push(l)});jQuery.each(q,function(o,l){o=jQuery.inArray(l,a.jqgrid.dirty_fields[d.key]);o!==-1&&a.jqgrid.dirty_fields[d.key].splice(o,
1)});a.jqgrid.dirty_fields[d.key].length===0&&delete a.jqgrid.dirty_fields[d.key];jQuery.each(a.operations.buttons,function(o,l){if(l.type==="post_edit"){o=jQuery("#"+a.jqgrid.id+"_buttonOp_"+l.id);C(a.jqgrid.dirty_fields)?o.attr("disabled","disabled"):o.removeAttr("disabled")}})}var j=a.jqgrid.object.jqGrid("getGridParam","multiselect")?"selarrrow":"selrow",f=a.jqgrid.object.jqGrid("getGridParam",j);if(!f instanceof Array)f=[f];if(f.length===1)if(c&&c!==a.jqgrid.last_selected_row){jQuery("#"+a.jqgrid.id).restoreRow(a.jqgrid.last_selected_row);
jQuery("#"+a.jqgrid.id).jqGrid("editRow",c,true,null,null,"clientArray",null,h);a.jqgrid.last_selected_row=c}jQuery.each(a.operations.buttons,function(m,d){m=jQuery("#"+a.jqgrid.id+"_buttonOp_"+d.id);if(d.type!=="post_edit")if(f.length>=d.real_bounds[0]&&f.length<=d.real_bounds[1]){m.removeAttr("disabled");if(d.real_bounds[0]===1&&d.real_bounds[1]===1&&m.data("melange")!==undefined){var e=a.jqgrid.object.jqGrid("getRowData",f[0]);e=t.from(a.data.all_data).equals("columns.key",e.key).select()[0];var s=
m.data("melange").click;m.click(s(e.operations.buttons[d.id].link));m.attr("value",e.operations.buttons[d.id].caption)}}else m.attr("disabled","disabled")})}}(b),global_button_functions:{redirect_simple:function(a){return a.new_window?function(){window.open(a.link)}:function(){window.location.href=a.link}},redirect_custom:function(a){return function(c){return a.new_window?function(){window.open(c)}:function(){window.location.href=c}}},post:function(a){return function(){var c=k.get(a.idx).jqgrid.object.jqGrid("getGridParam",
"multiselect")?"selarrrow":"selrow";c=k.get(a.idx).jqgrid.object.jqGrid("getGridParam",c);c instanceof Array||(c=c===null?[]:[c]);var h=[];if(!(c.length<a.real_bounds[0]||c.length>a.real_bounds[1])){jQuery.each(c,function(j,f){var m=jQuery("#"+k.get(a.idx).jqgrid.id).jqGrid("getRowData",f);t.from(k.get(a.idx).all_data).equals("columns.key",m.key).select();var d={};jQuery.each(a.keys,function(e,s){e=m[s];if(jQuery(e).hasClass("listsnoul"))e=/^<a\b[^>]*>(.*?)<\/a>$/.exec(e)[1];d[s]=e});h.push(d)});
if(a.url==="")a.url=window.location.href;jQuery.post(a.url,{xsrf_token:window.xsrf_token,idx:a.idx,button_id:a.button_id,data:JSON.stringify(h)},function(j){if(a.redirect=="true")try{var f=JSON.parse(j);if(f.data.url!==undefined)window.location.href=f.data.url}catch(m){}j=parseInt(a.refresh,10);if(!isNaN(j)){k.get(j).refreshData();jQuery("#"+k.get(j).jqgrid.id).trigger("reloadGrid")}if(a.refresh=="current"){k.get(a.idx).refreshData();jQuery("#"+k.get(a.idx).jqgrid.id).trigger("reloadGrid")}else if(a.refresh==
"all"){j=k.getAll();jQuery.each(j,function(d,e){e.refreshData();jQuery("#"+k.get(d).jqgrid.id).trigger("reloadGrid")})}})}}},post_edit:function(a){return function(){var c=k.get(a.idx).jqgrid,h={};if(!(c.editable_columns.length===0&&C(c.dirty_fields))){for(var j=c.object.jqGrid("getGridParam","records"),f=1;f<=j;f++){var m=jQuery("#"+c.id).jqGrid("getRowData",f);if(c.dirty_fields[m.key]!==undefined){h[m.key]={};jQuery.each(c.dirty_fields[m.key],function(d,e){h[m.key][e]=m[e]})}}if(a.url==="")a.url=
window.location.href;jQuery.post(a.url,{xsrf_token:window.xsrf_token,idx:a.idx,button_id:a.button_id,data:JSON.stringify(h)},function(d){if(a.redirect=="true")try{var e=JSON.parse(d);if(e.data.url!==undefined)window.location.href=e.data.url}catch(s){}d=parseInt(a.refresh,10);if(!isNaN(d)){k.get(d).refreshData();jQuery("#"+k.get(d).jqgrid.id).trigger("reloadGrid")}if(a.refresh=="current"){k.get(a.idx).refreshData();jQuery("#"+k.get(a.idx).jqgrid.id).trigger("reloadGrid")}else if(a.refresh=="all"){d=
k.getAll();jQuery.each(d,function(q,o){o.refreshData();jQuery("#"+k.get(q).jqgrid.id).trigger("reloadGrid")})}})}}}},row_functions:{redirect_custom:function(a){return function(c,h){return a.new_window||h.which===2||h.which===1&&h.ctrlKey?function(){window.open(c)}:function(){window.location.href=c}}}}},B=function(){jQuery("#"+i).replaceWith(['<p id="temporary_list_placeholder_',g,'"></p>','<table id="'+b.jqgrid.id+'"',' cellpadding="0" cellspacing="0"></table>','<div id="'+b.jqgrid.pager.id+'"',' style="text-align:center"></div>'].join(""))},
z=function(){var a="",c=0;jQuery("#load_"+b.jqgrid.id).show();var h=function(){var j="?";if(window.location.href.indexOf("?")!==-1)j="&";jQuery.ajax({async:true,cache:false,url:[window.location.href,j,"fmt=json&limit=150",a===""?"":"&start="+a,"&idx=",g].join(""),timeout:6E4,tryCount:1,retryLimit:5,error:function(f){if(f.status==500){this.tryCount++;if(this.tryCount<=this.retryLimit)jQuery.ajax(this);else{jQuery("#temporary_list_placeholder_"+g).html('<span style="color:red">Error retrieving data: please refresh the list or the whole page to try again</span>');
jQuery("#load_"+b.jqgrid.id).hide()}}else{jQuery("#temporary_list_placeholder_"+g).html('<span style="color:red">Error retrieving data: please refresh the list or the whole page to try again</span>');jQuery("#load_"+b.jqgrid.id).hide()}},success:function(f){var m=f.next==="done";if(f.data[a]!==undefined){if(b.configuration===null)b.configuration=f.configuration;if(b.operations===null)b.operations=f.operations;jQuery.each(f.data[a],function(){b.data.data.push(this.columns);b.data.all_data.push(this)});
b.jqgrid.object===null?y():b.jqgrid.object.trigger("reloadGrid");if(m){jQuery("#temporary_list_placeholder_"+g).remove();jQuery("#load_"+b.jqgrid.id).hide()}else{a=f.next;setTimeout(h,100);c++}}if(m){jQuery("#temporary_list_placeholder_"+g).remove();jQuery("#load_"+b.jqgrid.id).hide();jQuery("#"+b.jqgrid.id)[0].triggerToolbar();jQuery.each(b.configuration.colModel,function(d,e){e.editable!==undefined&&e.editable===true&&b.jqgrid.editable_columns.push(e.name)});jQuery("#t_"+b.jqgrid.id).children().remove();
b.operations!==undefined&&b.operations.buttons!==undefined&&jQuery.each(b.operations.buttons,function(d,e){d=b.jqgrid.id+"_buttonOp_"+e.id;jQuery("#t_"+b.jqgrid.id).append("<input type='button' value='"+e.caption+"' style='float:left' id='"+d+"'/>");e.parameters.idx=g;if(e.type!=="post_edit"){e.real_bounds=e.bounds;var s=e.real_bounds.indexOf("all");if(s!==-1)e.real_bounds[s]=b.jqgrid.object.jqGrid("getGridParam","records");e.parameters.real_bounds=e.real_bounds}if(e.type==="post_edit"||e.real_bounds[0]>
0)jQuery("#"+d).attr("disabled","disabled");e.parameters.button_id=e.id;jQuery("#"+d).click(v.global_button_functions[e.type](e.parameters));e.type=="redirect_custom"&&jQuery("#"+d).data("melange",{click:v.global_button_functions[e.type](e.parameters)})});jQuery("#t_"+b.jqgrid.id).css("padding-bottom","3px");jQuery("#t_"+b.jqgrid.id).append("<input type='button' value='CSV Export' style='float:right;' id='csvexport_"+b.jqgrid.id+"'/>");jQuery("#csvexport_"+b.jqgrid.id).button();jQuery("#csvexport_"+
b.jqgrid.id).click(function(){var d=[];d[0]=[];if(b.data.data[0]!==undefined||b.data.filtered_data[0]!==undefined){var e=b.data.filtered_data||b.data.data;jQuery.each(b.configuration.colNames,function(q,o){q=o;q=q.replace(/\"|&quot;|&#34;/g,'""');if(q.indexOf(",")!==-1||q.indexOf('"')!==-1||q.indexOf("\r\n")!==-1)q='"'+q+'"';d[0].push(q)});d[0]=d[0].join(",");var s=[];jQuery.each(b.configuration.colModel,function(q,o){s.push(o.name)});jQuery.each(e,function(q,o){d[d.length]=[];jQuery.each(s,function(l,
A){l=o[A];if(l===null)l="";if(l===undefined)l="";l=l.toString();A=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(l);if(A!==null)l=A[1];l=l.replace(/\"|&quot;|&#34;/g,'""');if(l.indexOf(",")!==-1||l.indexOf('"')!==-1||l.indexOf("\r\n")!==-1)l='"'+l+'"';d[d.length-1].push(l)});d[d.length-1]=d[d.length-1].join(",")});d=d.join("\r\n");jQuery("#csv_dialog").remove();jQuery("body").append(["<div id='csv_dialog' style='display:none'>  <h3>Now you can copy and paste CSV data from the text area to a new file:</h3>  <textarea style='width:450px;height:250px'>",
d,"</textarea></div>"].join(""));jQuery("#csv_dialog").dialog({height:420,width:500,modal:true,buttons:{Close:function(){jQuery(this).dialog("close")}}})}});jQuery("#t_"+b.jqgrid.id).append("<div style='float:right;margin-right:4px;'><input type='checkbox' id='regexp_"+b.jqgrid.id+"'/>RegExp Search</div>");jQuery("#regexp_"+b.jqgrid.id).click(function(){jQuery("#"+b.jqgrid.id).jqGrid().trigger("reloadGrid")});f=jQuery.Event("melange_list_loaded");f.list_object=b;b.jqgrid.object.trigger(f);f=jQuery("#gview_"+
b.jqgrid.id+" .ui-jqgrid-bdiv");f.width(f.width()+1)}}})};setTimeout(h,100)};this.refreshData=function(){b.data={data:[],all_data:[],filtered_data:null};z()};var w=new (function(){var a=function(c){var h={hidden_columns:{}};jQuery.each(c,function(j,f){h.hidden_columns[f.name]=f.hidden});return h};this.saveCurrentTableConfiguration=function(){var c=r.cookie.getCookie(r.cookie.MELANGE_USER_PREFERENCES),h=b.jqgrid.object.jqGrid("getGridParam","colModel");h=a(h);var j={lists_configuration:{}};j.lists_configuration[g]=
h;j.lists_configuration=jQuery.extend(c.lists_configuration,j.lists_configuration);r.cookie.saveCookie(r.cookie.MELANGE_USER_PREFERENCES,j,14,window.location.pathname)};this.getPreviousTableConfiguration=function(c){var h=r.cookie.getCookie(r.cookie.MELANGE_USER_PREFERENCES),j=c.colModel;h.lists_configuration[g]&&jQuery.each(h.lists_configuration[g].hidden_columns,function(f,m){t.from(j).equals("name",f).select()[0].hidden=m});return c}}),y=function(){b.configuration=w.getPreviousTableConfiguration(b.configuration);
var a=jQuery.extend(b.configuration,{postData:{my_index:g},onSelectAll:v.enableDisableButtons,onSelectRow:v.enableDisableButtons}),c={caption:"",buttonicon:"ui-icon-calculator",onClickButton:function(){jQuery("#"+b.jqgrid.id).setColumns({colnameview:false,jqModal:true,ShrinkToFit:true,afterSubmitForm:w.saveCurrentTableConfiguration});return false},position:"last",title:"Show/Hide Columns",cursor:"pointer"};jQuery("#"+b.jqgrid.id).jqGrid(jQuery.extend(b.jqgrid.options,a)).jqGrid("navGrid","#"+b.jqgrid.pager.id,
b.jqgrid.pager.options,{},{},{},{closeAfterSearch:true,multipleSearch:true},{}).jqGrid("navButtonAdd","#"+b.jqgrid.pager.id,c);jQuery("#"+b.jqgrid.id).jqGrid("filterToolbar",{searchOnEnter:false});jQuery("#load_"+b.jqgrid.id).closest("div").css("line-height","100%");jQuery("#load_"+b.jqgrid.id).html("<img src='/soc/content/"+r.config.app_version+"/images/jqgrid_loading.gif'></img>");b.jqgrid.object=jQuery("#"+b.jqgrid.id)};this.getDiv=function(){return i};this.getIdx=function(){return g};(function(){jQuery(function(){if(jQuery("#"+
i).length===0)throw new r.error.divNotExistent("Div "+i+" is not existent");b.jqgrid.id="jqgrid_"+i;b.jqgrid.pager.id="jqgrid_pager_"+i;b.jqgrid.options=jQuery.extend(x,{pager:"#"+b.jqgrid.pager.id});b.jqgrid.pager.options=u;k.add(b);B();y();z()})})()}if(window.melange===undefined)throw new Error("Melange not loaded");var r=window.melange;if(window.jLinq===undefined)throw new Error("jLinq not loaded");var t=window.jLinq;r.list=window.melange.list=function(){return new r.list};var F=r.logging.debugDecorator(r.list);
r.error.createErrors(["listIndexNotValid","divNotExistent","indexAlreadyExistent"]);var C=function(i){for(var g in i)return false;return true},E=function(i){var g=i.my_index,p=k.get(g).data.data,n=p,b="",x={eq:{method:"equals",not:false},ne:{method:"equals",not:true},lt:{method:"less",not:false},le:{method:"lessEquals",not:false},gt:{method:"greater",not:false},ge:{method:"greaterEquals",not:false},bw:{method:"startsWith",not:false},bn:{method:"startsWith",not:true},ew:{method:"endsWith",not:false},
en:{method:"endsWith",not:true},cn:{method:"contains",not:false},nc:{method:"contains",not:true},"in":{method:"match",not:false},ni:{method:"match",not:true}};if(i._search&&i.filters){var u=JSON.parse(i.filters);if(u.rules[0].data!==""){b=u.groupOp;if(b==="OR")n={};jQuery.each(u.rules,function(a,c){if(c.op==="in"||c.op==="ni")c.data=c.data.split(",").join("|");n=x[c.op].not?b==="OR"?t.from(n).union(t.from(p).not()[x[c.op].method](c.field,c.data).select()).select():t.from(n).not()[x[c.op].method](c.field,
c.data).select():b==="OR"?t.from(n).union(t.from(p)[x[c.op].method](c.field,c.data).select()).select():t.from(n)[x[c.op].method](c.field,c.data).select()})}}else p[0]!==undefined&&jQuery.each(p[0],function(a){if(i[a]!==undefined){var c=jQuery("#regexp_"+k.get(g).jqgrid.id).is(":checked"),h=false;jQuery.each(k.get(g).configuration.colModel,function(j,f){if(f.editoptions!==undefined&&a===f.name)h=true});n=c||h?t.from(n).match(a,i[a]).select():t.from(n).contains(a,i[a]).select()}});var v=i.sidx;u=i.sord;
jQuery.each(k.get(g).configuration.colModel,function(a,c){if(c.name===v&&(c.sorttype==="integer"||c.sorttype==="int"))jQuery.each(n,function(h,j){h=parseInt(j[v],10);isNaN(h)||(j[v]=h)})});u=u==="asc"?"":"-";if(n.length>0)n=t.from(n).ignoreCase().orderBy(u+v).select();k.get(g).data.filtered_data=n;if(i.rows===-1)i.rows=k.get(g).data.filtered_data.length;u=(i.page-1)*i.rows;for(var B=i.page*i.rows-1,z={page:i.page,total:n.length===0?0:Math.ceil(n.length/i.rows),records:n.length,rows:[]},w=u;w<=B;w++)if(n[w]!==
undefined){var y=[];p[0]!==undefined&&jQuery.each(k.get(g).configuration.colModel,function(a,c){var h;a=k.get(g).data.all_data;for(var j=0;j<a.length;j++)if(a[j].columns.key===n[w].key){h=a[j];break}c=n[w][c.name];if(h.operations!==undefined&&h.operations.row!==undefined&&h.operations.row.link!==undefined)if(c!==null&&c!==undefined&&c.toString().match(/<a\b[^>]*>.*<\/a>/)===null)c='<a style="display:block;" href="'+h.operations.row.link+'" class="listsnoul">'+c+"</a>";y.push(c)});z.rows.push({key:n[w].key,
cell:y})}jQuery("#"+k.get(g).jqgrid.id)[0].addJSONData(z)},k=function(){var i=[];return{add:function(g){i[g.getIdx()]=g},get:function(g){return i[g]!==undefined?i[g]:null},getAll:function(){return jQuery.extend({},i)},isExistent:function(g){return i[g]!==undefined?true:false}}}();F.loadList=function(i,g,p){p=parseInt(p,10);g=JSON.parse(g);if(isNaN(p)||p<0)throw new r.error.listIndexNotValid("List index "+p+" is not valid");if(k.isExistent(p))throw new r.error.indexAlreadyExistent("Index "+p+" is already existent");
new D(i,p,g.configuration,g.operations)}})();
