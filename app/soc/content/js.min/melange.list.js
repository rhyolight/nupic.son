(function(){function K(l,j,u,q){var a=this;l=l;j=j;var A={cookie_service:{enabled:true},column_search:{enabled:true,regexp:true},columns_show_hide:{enabled:true},search_dialog:{enabled:true},csv_export:{enabled:true},global_search:{enabled:false},global_sort:{enabled:false}};this.configuration=u;this.operations=q.operations!==undefined?q.operations:{};this.templates=q.templates!==undefined?q.templates:{};this.features=q.features!==undefined?jQuery.extend(A,q.features):A;var z={datatype:L,viewrecords:true},
D={edit:false,add:false,del:false,refreshtext:"Refresh",searchtext:"Filter",afterRefresh:function(){a.refreshData();a.jqgrid.object.trigger("reloadGrid")}};if(!a.features.search_dialog.enabled)D.search=false;this.jqgrid={id:null,object:null,options:null,last_selected_row:null,editable_columns:[],dirty_fields:{},pager:{id:null,options:null}};this.data={data:[],all_data:[],filtered_data:null};var F={enableDisableButtons:function(b){return function(f){function m(i){i=jQuery("#"+b.jqgrid.id).jqGrid("getRowData",
i);var c=i.key.toString(),e=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(c);if(e!==null)c=e[2];var h=v.from(b.data.all_data).equals("columns.key",c).select()[0];if(b.jqgrid.dirty_fields[c]===undefined)b.jqgrid.dirty_fields[c]=[];var p=[],w=[];jQuery.each(i,function(o,s){s=s.toString();var E=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(s);if(E!==null)s=E[2];E=h.columns[o];if(typeof E=="boolean")E=""+E;s!=E?p.push(o):w.push(o)});jQuery.each(p,function(o,s){jQuery.inArray(s,b.jqgrid.dirty_fields[c])===
-1&&b.jqgrid.dirty_fields[c].push(s)});jQuery.each(w,function(o,s){o=jQuery.inArray(s,b.jqgrid.dirty_fields[c]);o!==-1&&b.jqgrid.dirty_fields[c].splice(o,1)});b.jqgrid.dirty_fields[c].length===0&&delete b.jqgrid.dirty_fields[c];jQuery.each(b.operations.buttons,function(o,s){if(s.type==="post_edit"){o=jQuery("#"+b.jqgrid.id+"_buttonOp_"+s.id);if(J(b.jqgrid.dirty_fields))o.attr("disabled","disabled");else{o.click();o.removeAttr("disabled")}}});k()}var g=b.jqgrid.object.jqGrid("getGridParam","multiselect")?
"selarrrow":"selrow",d=b.jqgrid.object.jqGrid("getGridParam",g);d instanceof Array||(d=[d]);if(d.length===1)if(f&&f!==b.jqgrid.last_selected_row){jQuery("#"+b.jqgrid.id).restoreRow(b.jqgrid.last_selected_row);jQuery("#"+b.jqgrid.id).jqGrid("editRow",f,true,null,null,"clientArray",null,m);b.jqgrid.last_selected_row=f}jQuery.each(b.operations.buttons,function(i,c){i=jQuery("#"+b.jqgrid.id+"_buttonOp_"+c.id);if(c.type!=="post_edit")if(d.length>=c.real_bounds[0]&&d.length<=c.real_bounds[1]){i.removeAttr("disabled");
if(c.real_bounds[0]===1&&c.real_bounds[1]===1&&i.data("melange")!==undefined){var e=b.jqgrid.object.jqGrid("getRowData",d[0]);e=v.from(b.data.all_data).equals("columns.key",e.key).select()[0];var h=i.data("melange").click;i.click(h(e.operations.buttons[c.id].link));i.attr("value",e.operations.buttons[c.id].caption)}}else i.attr("disabled","disabled")})}}(a),global_button_functions:{redirect_simple:function(b){return b.new_window?function(){window.open(b.link)}:function(){window.location.href=b.link}},
redirect_custom:function(b){return function(f){return b.new_window?function(){window.open(f)}:function(){window.location.href=f}}},post:function(b){return function(){var f=r.get(b.idx).jqgrid.object.jqGrid("getGridParam","multiselect")?"selarrrow":"selrow";f=r.get(b.idx).jqgrid.object.jqGrid("getGridParam",f);f instanceof Array||(f=f===null?[]:[f]);var m=[];if(!(f.length<b.real_bounds[0]||f.length>b.real_bounds[1])){jQuery.each(f,function(g,d){var i=jQuery("#"+r.get(b.idx).jqgrid.id).jqGrid("getRowData",
d);v.from(r.get(b.idx).all_data).equals("columns.key",i.key).select();var c={};jQuery.each(b.keys,function(e,h){e=i[h];if(jQuery(e).hasClass("listsnoul"))e=/^<a\b[^>]*>(.*?)<\/a>$/.exec(e)[1];c[h]=e});m.push(c)});if(b.url==="")b.url=window.location.href;jQuery.post(b.url,{xsrf_token:window.xsrf_token,idx:b.idx,button_id:b.button_id,data:JSON.stringify(m)},function(g){if(b.redirect=="true")try{var d=JSON.parse(g);if(d.data.url!==undefined)window.location.href=d.data.url}catch(i){}g=parseInt(b.refresh,
10);if(!isNaN(g)){r.get(g).refreshData();jQuery("#"+r.get(g).jqgrid.id).trigger("reloadGrid")}if(b.refresh=="current"){r.get(b.idx).refreshData();jQuery("#"+r.get(b.idx).jqgrid.id).trigger("reloadGrid")}else if(b.refresh=="all"){g=r.getAll();jQuery.each(g,function(c,e){e.refreshData();jQuery("#"+r.get(c).jqgrid.id).trigger("reloadGrid")})}})}}},post_edit:function(b){return function(){var f=r.get(b.idx).jqgrid,m={};if(!(f.editable_columns.length===0&&J(f.dirty_fields))){f.object.jqGrid("getGridParam",
"records");for(var g=f.object.jqGrid("getGridParam","reccount"),d=1;d<=g;d++){var i=jQuery("#"+f.id).jqGrid("getRowData",d),c=i.key.toString(),e=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(c);if(e!==null)c=e[2];if(f.dirty_fields[c]!==undefined){m[c]={};jQuery.each(f.dirty_fields[c],function(h,p){h=i[p].toString();var w=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(h);if(w!==null)h=w[2];m[c][p]=h});b.keys!==undefined&&jQuery.each(b.keys,function(h,p){if(m[c][p]===undefined){h=i[p].toString();
var w=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(h);if(w!==null)h=w[2];m[c][p]=h}})}}if(b.url==="")b.url=window.location.href;jQuery.post(b.url,{xsrf_token:window.xsrf_token,idx:b.idx,button_id:b.button_id,data:JSON.stringify(m)},function(h){if(b.redirect=="true")try{var p=JSON.parse(h);if(p.data.url!==undefined)window.location.href=p.data.url}catch(w){}h=parseInt(b.refresh,10);if(!isNaN(h)){r.get(h).refreshData();jQuery("#"+r.get(h).jqgrid.id).trigger("reloadGrid")}if(b.refresh=="current"){r.get(b.idx).refreshData();
jQuery("#"+r.get(b.idx).jqgrid.id).trigger("reloadGrid")}else if(b.refresh=="all"){h=r.getAll();jQuery.each(h,function(o,s){s.refreshData();jQuery("#"+r.get(o).jqgrid.id).trigger("reloadGrid")})}})}}}},row_functions:{redirect_custom:function(b){return function(f,m){return b.new_window||m.which===2||m.which===1&&m.ctrlKey?function(){window.open(f)}:function(){window.location.href=f}}}}},H=function(){jQuery("#"+l).replaceWith(['<p id="temporary_list_placeholder_',j,'"></p>','<table id="'+a.jqgrid.id+
'"',' cellpadding="0" cellspacing="0"></table>','<div id="'+a.jqgrid.pager.id+'"',' style="text-align:center"></div>'].join(""))},B=function(b,f){f.columns=G(f.columns);I(b,f)},I=function(b,f){if(f.operations===undefined&&f.operations.row_buttons===undefined)return f;jQuery.each(f.operations.row_buttons,function(m,g){if(g.type==="redirect_simple"){m="row_button_"+a.getIdx()+"_"+b+"_"+m;m=['<input type="button" value="',g.caption,'" id="',m,'"></input>'].join("");f.columns[g.append_to_column]+=m}});
return f},G=function(b){if(a.templates===undefined)return b;b=b;jQuery.each(a.templates,function(f,m){for(var g,d=/\{\{([^\}]+)\}\}/g,i=m;g=d.exec(m);){var c=jQuery.trim(g[1]);if(b[c]!==undefined&&b[f]!==undefined)i=i.replace(g[0],b[c])}b[f]=i});return b},C=function(){var b="",f=0;jQuery("#load_"+a.jqgrid.id).show();var m=function(){var g="?";if(window.location.href.indexOf("?")!==-1)g="&";jQuery.ajax({async:true,cache:false,url:[window.location.href,g,"fmt=json&limit=150",b===""?"":"&start="+b,"&idx=",
j].join(""),timeout:6E4,tryCount:1,retryLimit:5,error:function(d){if(d.status==500){this.tryCount++;if(this.tryCount<=this.retryLimit)jQuery.ajax(this);else{jQuery("#temporary_list_placeholder_"+j).html('<span style="color:red">Error retrieving data: please refresh the list or the whole page to try again</span>');jQuery("#load_"+a.jqgrid.id).hide()}}else{jQuery("#temporary_list_placeholder_"+j).html('<span style="color:red">Error retrieving data: please refresh the list or the whole page to try again</span>');
jQuery("#load_"+a.jqgrid.id).hide()}},success:function(d){var i=d.next==="done";if(d.data[b]!==undefined){if(a.configuration===null)a.configuration=d.configuration;if(a.operations===null)a.operations=d.operations;jQuery.each(d.data[b],function(c,e){B(c,e);a.data.data.push(e.columns);a.data.all_data.push(e)});a.jqgrid.object===null?y():a.jqgrid.object.trigger("reloadGrid");jQuery.each(a.data.all_data,function(c,e){e.operations!==undefined&&e.operations.row_buttons!==undefined&&jQuery.each(e.operations.row_buttons,
function(h,p){h="row_button_"+a.getIdx()+"_"+c+"_"+h;p.type==="redirect_simple"&&jQuery("#"+h).click(F.global_button_functions[p.type](p.parameters))})});if(i){jQuery("#temporary_list_placeholder_"+j).remove();jQuery("#load_"+a.jqgrid.id).hide()}else{b=d.next;setTimeout(m,100);f++}}if(i){jQuery("#temporary_list_placeholder_"+j).remove();jQuery("#load_"+a.jqgrid.id).hide();a.jqgrid.object.triggerToolbar!==undefined&&a.jqgrid.object.triggerToolbar();jQuery.each(a.configuration.colModel,function(c,e){e.editable!==
undefined&&e.editable===true&&a.jqgrid.editable_columns.push(e.name)});jQuery("#t_"+a.jqgrid.id).children().remove();a.operations!==undefined&&a.operations.buttons!==undefined&&jQuery.each(a.operations.buttons,function(c,e){c=a.jqgrid.id+"_buttonOp_"+e.id;var h=jQuery("<input type='button' value='"+e.caption+"' style='float:left' id='"+c+"'/>").button();jQuery("#t_"+a.jqgrid.id).append(h);e.parameters.idx=j;if(e.type!=="post_edit"){e.real_bounds=e.bounds;h=e.real_bounds.indexOf("all");if(h!==-1)e.real_bounds[h]=
a.jqgrid.object.jqGrid("getGridParam","records");e.parameters.real_bounds=e.real_bounds}if(e.type==="post_edit"||e.real_bounds[0]>0)jQuery("#"+c).attr("disabled","disabled");e.parameters.button_id=e.id;jQuery("#"+c).click(F.global_button_functions[e.type](e.parameters));e.type=="redirect_custom"&&jQuery("#"+c).data("melange",{click:F.global_button_functions[e.type](e.parameters)})});jQuery("#t_"+a.jqgrid.id).css("padding-bottom","3px");if(a.features.csv_export.enabled){jQuery("#t_"+a.jqgrid.id).append("<input type='button' value='CSV Export' style='float:right;' id='csvexport_"+
a.jqgrid.id+"'/>");jQuery("#csvexport_"+a.jqgrid.id).button();jQuery("#csvexport_"+a.jqgrid.id).click(function(){var c=[];c[0]=[];if(a.data.data[0]!==undefined||a.data.filtered_data[0]!==undefined){var e=a.data.filtered_data||a.data.data;jQuery.each(a.configuration.colNames,function(p,w){p=w;p=p.replace(/\"|&quot;|&#34;/g,'""');if(p.indexOf(",")!==-1||p.indexOf('"')!==-1||p.indexOf("\r\n")!==-1)p='"'+p+'"';c[0].push(p)});c[0]=c[0].join(",");var h=[];jQuery.each(a.configuration.colModel,function(p,
w){h.push(w.name)});jQuery.each(e,function(p,w){c[c.length]=[];jQuery.each(h,function(o,s){o=w[s];if(o===null)o="";if(o===undefined)o="";o=o.toString();s=/^<a\b[^>]*href="(.*?)" \b[^>]*>(.*?)<\/a>$/.exec(o);if(s!==null)o=s[1];o=o.replace(/\"|&quot;|&#34;/g,'""');if(o.indexOf(",")!==-1||o.indexOf('"')!==-1||o.indexOf("\r\n")!==-1)o='"'+o+'"';c[c.length-1].push(o)});c[c.length-1]=c[c.length-1].join(",")});c=c.join("\r\n");jQuery("#csv_dialog").remove();jQuery("body").append(["<div id='csv_dialog' style='display:none'>  <h3>Now you can copy and paste CSV data from the text area to a new file:</h3>  <textarea style='width:450px;height:250px'>",
c,"</textarea></div>"].join(""));jQuery("#csv_dialog").dialog({height:420,width:500,modal:true,buttons:{Close:function(){jQuery(this).dialog("close")}}})}})}if(a.features.column_search.enabled&&a.features.column_search.regexp){jQuery("#t_"+a.jqgrid.id).append("<div style='float:right;margin-right:4px;'><input type='checkbox' id='regexp_"+a.jqgrid.id+"'/>RegExp Search</div>");jQuery("#regexp_"+a.jqgrid.id).click(function(){jQuery("#"+a.jqgrid.id).jqGrid().trigger("reloadGrid")})}d=jQuery.Event("melange_list_loaded");
d.list_object=a;a.jqgrid.object.trigger(d);d=jQuery("#gview_"+a.jqgrid.id+" .ui-jqgrid-bdiv");d.width(d.width()+1)}}})};setTimeout(m,100)};this.refreshData=function(){a.data={data:[],all_data:[],filtered_data:null};C()};var n=new (function(){var b=function(g){var d={hidden_columns:{}};jQuery.each(g,function(i,c){d.hidden_columns[c.name]=c.hidden});return d},f=function(g,d){return{sort_settings:{sortname:g,sortorder:d}}},m=function(g,d){var i={filters:{}};d._search===true&&jQuery.each(g,function(c,
e){if(d[e.name]!==undefined)i.filters[e.name]=d[e.name]});return i};this.saveCurrentTableConfiguration=function(){var g=x.cookie.getCookie(x.cookie.MELANGE_USER_PREFERENCES),d=a.jqgrid.object.jqGrid("getGridParam","colModel"),i=a.jqgrid.object.jqGrid("getGridParam","sortname"),c=a.jqgrid.object.jqGrid("getGridParam","sortorder"),e=a.jqgrid.object.jqGrid("getGridParam","postData"),h=b(d);h=jQuery.extend(f(i,c),h);h=jQuery.extend(m(d,e),h);d={lists_configuration:{}};d.lists_configuration[j]=h;d.lists_configuration=
jQuery.extend(g.lists_configuration,d.lists_configuration);x.cookie.saveCookie(x.cookie.MELANGE_USER_PREFERENCES,d,14,window.location.pathname)};this.getPreviousTableConfiguration=function(g){var d=x.cookie.getCookie(x.cookie.MELANGE_USER_PREFERENCES),i=g.colModel;if(d.lists_configuration[j]!==undefined){jQuery.each(d.lists_configuration[j].hidden_columns,function(h,p){h=v.from(i).equals("name",h).select()[0]||null;if(h!==null)h.hidden=p});if(d.lists_configuration[j].sort_settings!==undefined){var c=
d.lists_configuration[j].sort_settings.sortname,e=d.lists_configuration[j].sort_settings.sortorder;if(v.from(i).equals("name",c).select()[0]!==undefined?true:false){g.sortname=c;g.sortorder=e}}d.lists_configuration[j].filters!==undefined&&jQuery.each(d.lists_configuration[j].filters,function(h,p){h=v.from(i).equals("name",h).select()[0];if(h!==undefined)h.searchoptions={defaultValue:p}})}return g}}),k=function(){if(a.configuration.footerrow){var b={},f=a.jqgrid.object;jQuery.each(a.configuration.colModel,
function(m,g){if(g.summaryType!==undefined){m=f.jqGrid("getCol",g.name,false,g.summaryType);b[g.name]=g.summaryTpl.replace(/\{0\}/ig,m)}});f.jqGrid("footerData","set",b)}},t=function(){if(a.jqgrid.object){k();a.features.cookie_service.enabled&&n.saveCurrentTableConfiguration()}},y=function(){if(a.features.cookie_service.enabled)a.configuration=n.getPreviousTableConfiguration(a.configuration);var b=jQuery.extend(a.configuration,{postData:{my_index:j},onSelectAll:F.enableDisableButtons,onSelectRow:F.enableDisableButtons,
gridComplete:t}),f={caption:"Columns",buttonicon:"ui-icon-calculator",onClickButton:function(){jQuery("#"+a.jqgrid.id).setColumns({colnameview:false,jqModal:true,ShrinkToFit:true,afterSubmitForm:n.saveCurrentTableConfiguration,recreateForm:true});return false},position:"last",title:"Show/Hide Columns",cursor:"pointer"},m={};if(a.features.column_search.enabled)m={closeAfterSearch:true,multipleSearch:true};jQuery("#"+a.jqgrid.id).jqGrid(jQuery.extend(a.jqgrid.options,b)).jqGrid("navGrid","#"+a.jqgrid.pager.id,
a.jqgrid.pager.options,{},{},{},m,{});a.features.columns_show_hide.enabled&&jQuery("#"+a.jqgrid.id).jqGrid("navButtonAdd","#"+a.jqgrid.pager.id,f);a.features.column_search.enabled&&jQuery("#"+a.jqgrid.id).jqGrid("filterToolbar",{beforeSearch:n.saveCurrentTableConfiguration,searchOnEnter:false,autosearch:true});jQuery("#load_"+a.jqgrid.id).closest("div").css("line-height","100%");jQuery("#load_"+a.jqgrid.id).html("<img src='/soc/content/"+x.config.app_version+"/images/jqgrid_loading.gif'></img>");
a.jqgrid.object=jQuery("#"+a.jqgrid.id);a.features.global_search.enabled&&jQuery(a.features.global_search.element_path).bind("keyup",function(){var d=jQuery(a.features.global_search.element_path).val(),i=a.jqgrid.object.jqGrid("getGridParam","postData");i._search=true;i.filters={groupOp:"OR",rules:[]};jQuery.each(a.configuration.colModel,function(c,e){i.filters.rules.push({field:e.name,op:"cn",data:d})});i.filters=JSON.stringify(i.filters);a.jqgrid.object.jqGrid("setGridParam",{search:true,postData:i});
a.jqgrid.object.trigger("reloadGrid")});b=a.features.global_sort;if(b.enabled&&a.getIdx()===6){if(b.element_paths.column!==undefined){var g=jQuery(b.element_paths.column);jQuery(" option",g).remove();jQuery.each(a.configuration.colModel,function(d,i){g.append(jQuery("<option></option>").val(i.name).html(a.configuration.colNames[d]))});f=a.jqgrid.object.jqGrid("getGridParam","postData").sidx;g.val(f);g.bind("change",function(){var d=jQuery(this).val();a.jqgrid.object.jqGrid("setGridParam",{sortname:d});
a.jqgrid.object.trigger("reloadGrid")})}if(b.element_paths.asc_desc!==undefined){g=jQuery(b.element_paths.asc_desc);jQuery(" option",g).remove();g.append(jQuery("<option></option>").val("asc").html("Ascending"));g.append(jQuery("<option></option>").val("desc").html("Descending"));f=a.jqgrid.object.jqGrid("getGridParam","postData").sord;g.val(f);g.bind("change",function(){var d=jQuery(this).val();a.jqgrid.object.jqGrid("setGridParam",{sortorder:d});a.jqgrid.object.trigger("reloadGrid")})}}};this.getDiv=
function(){return l};this.getIdx=function(){return j};(function(){jQuery(function(){if(jQuery("#"+l).length===0)throw new x.error.divNotExistent("Div "+l+" is not existent");a.jqgrid.id="jqgrid_"+l;a.jqgrid.pager.id="jqgrid_pager_"+l;a.jqgrid.options=jQuery.extend(z,{pager:"#"+a.jqgrid.pager.id});a.jqgrid.pager.options=D;r.add(a);H();y();C()})})()}if(window.melange===undefined)throw new Error("Melange not loaded");var x=window.melange;if(window.jLinq===undefined)throw new Error("jLinq not loaded");
var v=window.jLinq;x.list=window.melange.list=function(){return new x.list};var M=x.logging.debugDecorator(x.list);x.error.createErrors(["listIndexNotValid","divNotExistent","indexAlreadyExistent"]);var J=function(l){for(var j in l)return false;return true},L=function(l){var j=l.my_index,u=r.get(j).data.data,q=u,a="",A={eq:{method:"equals",not:false},ne:{method:"equals",not:true},lt:{method:"less",not:false},le:{method:"lessEquals",not:false},gt:{method:"greater",not:false},ge:{method:"greaterEquals",
not:false},bw:{method:"startsWith",not:false},bn:{method:"startsWith",not:true},ew:{method:"endsWith",not:false},en:{method:"endsWith",not:true},cn:{method:"contains",not:false},nc:{method:"contains",not:true},"in":{method:"match",not:false},ni:{method:"match",not:true}};if(l._search&&l.filters){var z=JSON.parse(l.filters);if(z.rules[0].data!==""){a=z.groupOp;if(a==="OR")q={};jQuery.each(z.rules,function(n,k){if(k.op==="in"||k.op==="ni")k.data=k.data.split(",").join("|");q=A[k.op].not?a==="OR"?v.from(q).union(v.from(u).not()[A[k.op].method](k.field,
k.data).select()).select():v.from(q).not()[A[k.op].method](k.field,k.data).select():a==="OR"?v.from(q).union(v.from(u)[A[k.op].method](k.field,k.data).select()).select():v.from(q)[A[k.op].method](k.field,k.data).select()})}}else u[0]!==undefined&&jQuery.each(u[0],function(n){if(l[n]!==undefined){var k=false;if(jQuery("#regexp_"+r.get(j).jqgrid.id)!==undefined&&jQuery("#regexp_"+r.get(j).jqgrid.id).is(":checked"))k=true;var t=false;jQuery.each(r.get(j).configuration.colModel,function(y,b){if(b.editoptions!==
undefined&&n===b.name)t=true});q=k||t?v.from(q).match(n,l[n]).select():v.from(q).contains(n,l[n]).select()}});q=q.filter(function(n,k,t){return k==t.indexOf(n)&&!J(n)});var D=l.sidx;z=l.sord;jQuery.each(r.get(j).configuration.colModel,function(n,k){if(k.name===D&&(k.sorttype==="integer"||k.sorttype==="int"))jQuery.each(q,function(t,y){t=parseInt(y[D],10);isNaN(t)||(y[D]=t)})});z=z==="asc"?"":"-";if(q.length>0)q=v.from(q).ignoreCase().orderBy(z+D).select();r.get(j).data.filtered_data=q;if(l.rows===
-1)l.rows=r.get(j).data.filtered_data.length;z=(l.page-1)*l.rows;for(var F=l.page*l.rows-1,H={page:l.page,total:q.length===0?0:Math.ceil(q.length/l.rows),records:q.length,rows:[]},B=z;B<=F;B++)if(q[B]!==undefined){var I=[];u[0]!==undefined&&jQuery.each(r.get(j).configuration.colModel,function(n,k){var t;n=r.get(j).data.all_data;for(var y=0;y<n.length;y++)if(n[y].columns.key===q[B].key){t=n[y];break}n=q[B][k.name];if(t&&t.operations!==undefined&&t.operations.row!==undefined&&t.operations.row.link!==
undefined){k=k.editable||false;if(n!==null&&n!==undefined&&!k&&n.toString().match(/<a\b[^>]*>.*<\/a>/)===null)n='<a style="display:block;" href="'+t.operations.row.link+'" class="listsnoul">'+n+"</a>"}n!==null&&I.push(n)});H.rows.push({key:q[B].key,cell:I})}var G=jQuery("#"+r.get(j).jqgrid.id);G[0].addJSONData(H);var C=r.get(j).configuration.colModel;jQuery.each(C,function(n,k){if(k.extra!==undefined){var t=0,y=0;jQuery.each(k.extra,function(b,f){l[b]===f&&t++;y++});if(t!==y){C[n].hidden=true;C[n].hidedlg=
true;G.jqGrid("getColProp",k.name).hidedlg=true;G.jqGrid("hideCol",k.name)}else{C[n].hidden=false;C[n].hidedlg=false;G.jqGrid("getColProp",k.name).hidedlg=false;G.jqGrid("showCol",k.name)}}})},r=function(){var l=[];return{add:function(j){l[j.getIdx()]=j},get:function(j){return l[j]!==undefined?l[j]:null},getAll:function(){return jQuery.extend({},l)},isExistent:function(j){return l[j]!==undefined?true:false}}}();M.loadList=function(l,j,u){u=parseInt(u,10);j=JSON.parse(j);if(isNaN(u)||u<0)throw new x.error.listIndexNotValid("List index "+
u+" is not valid");if(r.isExistent(u))throw new x.error.indexAlreadyExistent("Index "+u+" is already existent");new K(l,u,j.configuration,j)}})();
