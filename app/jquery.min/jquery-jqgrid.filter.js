(function(c){c.fn.jqFilter=function(k){if(typeof k==="string"){var w=c.fn.jqFilter[k];if(!w)throw"jqFilter - No such method: "+k;var B=c.makeArray(arguments).slice(1);return w.apply(this,B)}var o=c.extend(true,{filter:null,columns:[],onChange:null,afterRedraw:null,checkValues:null,error:false,errmsg:"",errorcheck:true,showQuery:true,sopt:null,ops:[{name:"eq",description:"equal",operator:"="},{name:"ne",description:"not equal",operator:"<>"},{name:"lt",description:"less",operator:"<"},{name:"le",description:"less or equal",
operator:"<="},{name:"gt",description:"greater",operator:">"},{name:"ge",description:"greater or equal",operator:">="},{name:"bw",description:"begins with",operator:"LIKE"},{name:"bn",description:"does not begin with",operator:"NOT LIKE"},{name:"in",description:"in",operator:"IN"},{name:"ni",description:"not in",operator:"NOT IN"},{name:"ew",description:"ends with",operator:"LIKE"},{name:"en",description:"does not end with",operator:"NOT LIKE"},{name:"cn",description:"contains",operator:"LIKE"},{name:"nc",
description:"does not contain",operator:"NOT LIKE"},{name:"nu",description:"is null",operator:"IS NULL"},{name:"nn",description:"is not null",operator:"IS NOT NULL"}],numopts:["eq","ne","lt","le","gt","ge","nu","nn","in","ni"],stropts:["eq","ne","bw","bn","ew","en","cn","nc","nu","nn","in","ni"],_gridsopt:[],groupOps:[{op:"AND",text:"AND"},{op:"OR",text:"OR"}],groupButton:true,ruleButtons:true,direction:"ltr"},k||{});return this.each(function(){if(!this.filter){this.p=o;if(this.p.filter===null||this.p.filter===
undefined)this.p.filter={groupOp:this.p.groupOps[0].op,rules:[],groups:[]};var q,x=this.p.columns.length,j,y=/msie/i.test(navigator.userAgent)&&!window.opera;if(this.p._gridsopt.length)for(q=0;q<this.p._gridsopt.length;q++)this.p.ops[q].description=this.p._gridsopt[q];this.p.initFilter=c.extend(true,{},this.p.filter);if(x){for(q=0;q<x;q++){j=this.p.columns[q];if(j.stype)j.inputtype=j.stype;else if(!j.inputtype)j.inputtype="text";if(j.sorttype)j.searchtype=j.sorttype;else if(!j.searchtype)j.searchtype=
"string";if(j.hidden===undefined)j.hidden=false;if(!j.label)j.label=j.name;if(j.index)j.name=j.index;if(!j.hasOwnProperty("searchoptions"))j.searchoptions={};if(!j.hasOwnProperty("searchrules"))j.searchrules={}}this.p.showQuery&&c(this).append("<table class='queryresult ui-widget ui-widget-content' style='display:block;max-width:440px;border:0px none;' dir='"+this.p.direction+"'><tbody><tr><td class='query'></td></tr></tbody></table>");var z=function(e,g){var a=[true,""];if(c.isFunction(g.searchrules))a=
g.searchrules(e,g);else if(c.jgrid&&c.jgrid.checkValues)try{a=c.jgrid.checkValues(e,-1,null,g.searchrules,g.label)}catch(b){}if(a&&a.length&&a[0]===false){o.error=!a[0];o.errmsg=a[1]}};this.onchange=function(){this.p.error=false;this.p.errmsg="";return c.isFunction(this.p.onChange)?this.p.onChange.call(this,this.p):false};this.reDraw=function(){c("table.group:first",this).remove();var e=this.createTableForGroup(o.filter,null);c(this).append(e);c.isFunction(this.p.afterRedraw)&&this.p.afterRedraw.call(this,
this.p)};this.createTableForGroup=function(e,g){var a=this,b,d=c("<table class='group ui-widget ui-widget-content' style='border:0px none;'><tbody></tbody></table>"),f="left";if(this.p.direction=="rtl"){f="right";d.attr("dir","rtl")}g===null&&d.append("<tr class='error' style='display:none;'><th colspan='5' class='ui-state-error' align='"+f+"'></th></tr>");var h=c("<tr></tr>");d.append(h);f=c("<th colspan='5' align='"+f+"'></th>");h.append(f);if(this.p.ruleButtons===true){var i=c("<select class='opsel'></select>");
f.append(i);h="";var l;for(b=0;b<o.groupOps.length;b++){l=e.groupOp===a.p.groupOps[b].op?" selected='selected'":"";h+="<option value='"+a.p.groupOps[b].op+"'"+l+">"+a.p.groupOps[b].text+"</option>"}i.append(h).bind("change",function(){e.groupOp=c(i).val();a.onchange()})}h="<span></span>";if(this.p.groupButton){h=c("<input type='button' value='+ {}' title='Add subgroup' class='add-group'/>");h.bind("click",function(){if(e.groups===undefined)e.groups=[];e.groups.push({groupOp:o.groupOps[0].op,rules:[],
groups:[]});a.reDraw();a.onchange();return false})}f.append(h);if(this.p.ruleButtons===true){h=c("<input type='button' value='+' title='Add rule' class='add-rule ui-add'/>");var m;h.bind("click",function(){if(e.rules===undefined)e.rules=[];for(b=0;b<a.p.columns.length;b++){var n=typeof a.p.columns[b].search==="undefined"?true:a.p.columns[b].search,s=a.p.columns[b].hidden===true;if(a.p.columns[b].searchoptions.searchhidden===true&&n||n&&!s){m=a.p.columns[b];break}}e.rules.push({field:m.name,op:(m.searchoptions.sopt?
m.searchoptions.sopt:a.p.sopt?a.p.sopt:m.searchtype==="string"?a.p.stropts:a.p.numopts)[0],data:""});a.reDraw();return false});f.append(h)}if(g!==null){h=c("<input type='button' value='-' title='Delete group' class='delete-group'/>");f.append(h);h.bind("click",function(){for(b=0;b<g.groups.length;b++)if(g.groups[b]===e){g.groups.splice(b,1);break}a.reDraw();a.onchange();return false})}if(e.groups!==undefined)for(b=0;b<e.groups.length;b++){f=c("<tr></tr>");d.append(f);h=c("<td class='first'></td>");
f.append(h);h=c("<td colspan='4'></td>");h.append(this.createTableForGroup(e.groups[b],e));f.append(h)}if(e.groupOp===undefined)e.groupOp=a.p.groupOps[0].op;if(e.rules!==undefined)for(b=0;b<e.rules.length;b++)d.append(this.createTableRowForRule(e.rules[b],e));return d};this.createTableRowForRule=function(e,g){var a=this,b=c("<tr></tr>"),d,f,h,i,l="",m;b.append("<td class='first'></td>");var n=c("<td class='columns'></td>");b.append(n);var s=c("<select></select>"),p,t=[];n.append(s);s.bind("change",
function(){e.field=c(s).val();h=c(this).parents("tr:first");for(d=0;d<a.p.columns.length;d++)if(a.p.columns[d].name===e.field){i=a.p.columns[d];break}if(i){i.searchoptions.id=c.jgrid.randId();if(y&&i.inputtype==="text")if(!i.searchoptions.size)i.searchoptions.size=10;var r=c.jgrid.createEl(i.inputtype,i.searchoptions,"",true,a.p.ajaxSelectOptions,true);c(r).addClass("input-elm");f=i.searchoptions.sopt?i.searchoptions.sopt:a.p.sopt?a.p.sopt:i.searchtype==="string"?a.p.stropts:a.p.numopts;var u="",
A=0;t=[];c.each(a.p.ops,function(){t.push(this.name)});for(d=0;d<f.length;d++){p=c.inArray(f[d],t);if(p!==-1){if(A===0)e.op=a.p.ops[p].name;u+="<option value='"+a.p.ops[p].name+"'>"+a.p.ops[p].description+"</option>";A++}}c(".selectopts",h).empty().append(u);c(".selectopts",h)[0].selectedIndex=0;if(c.browser.msie&&c.browser.version<9){u=parseInt(c("select.selectopts",h)[0].offsetWidth)+1;c(".selectopts",h).width(u);c(".selectopts",h).css("width","auto")}c(".data",h).empty().append(r);c(".input-elm",
h).bind("change",function(){e.data=c(this).val();a.onchange()});setTimeout(function(){e.data=c(r).val();a.onchange()},0)}});for(d=n=0;d<a.p.columns.length;d++){m=typeof a.p.columns[d].search==="undefined"?true:a.p.columns[d].search;var C=a.p.columns[d].hidden===true;if(a.p.columns[d].searchoptions.searchhidden===true&&m||m&&!C){m="";if(e.field===a.p.columns[d].name){m=" selected='selected'";n=d}l+="<option value='"+a.p.columns[d].name+"'"+m+">"+a.p.columns[d].label+"</option>"}}s.append(l);l=c("<td class='operators'></td>");
b.append(l);i=o.columns[n];i.searchoptions.id=c.jgrid.randId();if(y&&i.inputtype==="text")if(!i.searchoptions.size)i.searchoptions.size=10;n=c.jgrid.createEl(i.inputtype,i.searchoptions,e.data,true,a.p.ajaxSelectOptions,true);var v=c("<select class='selectopts'></select>");l.append(v);v.bind("change",function(){e.op=c(v).val();h=c(this).parents("tr:first");var r=c(".input-elm",h)[0];if(e.op==="nu"||e.op==="nn"){e.data="";r.value="";r.setAttribute("readonly","true");r.setAttribute("disabled","true")}else{r.removeAttribute("readonly");
r.removeAttribute("disabled")}a.onchange()});f=i.searchoptions.sopt?i.searchoptions.sopt:a.p.sopt?a.p.sopt:i.searchtype==="string"?o.stropts:a.p.numopts;l="";c.each(a.p.ops,function(){t.push(this.name)});for(d=0;d<f.length;d++){p=c.inArray(f[d],t);if(p!==-1){m=e.op===a.p.ops[p].name?" selected='selected'":"";l+="<option value='"+a.p.ops[p].name+"'"+m+">"+a.p.ops[p].description+"</option>"}}v.append(l);l=c("<td class='data'></td>");b.append(l);l.append(n);c(n).addClass("input-elm").bind("change",function(){e.data=
c(this).val();a.onchange()});l=c("<td></td>");b.append(l);if(this.p.ruleButtons===true){n=c("<input type='button' value='-' title='Delete rule' class='delete-rule ui-del'/>");l.append(n);n.bind("click",function(){for(d=0;d<g.rules.length;d++)if(g.rules[d]===e){g.rules.splice(d,1);break}a.reDraw();a.onchange();return false})}return b};this.getStringForGroup=function(e){var g="(",a;if(e.groups!==undefined)for(a=0;a<e.groups.length;a++){if(g.length>1)g+=" "+e.groupOp+" ";try{g+=this.getStringForGroup(e.groups[a])}catch(b){alert(b)}}if(e.rules!==
undefined)try{for(a=0;a<e.rules.length;a++){if(g.length>1)g+=" "+e.groupOp+" ";g+=this.getStringForRule(e.rules[a])}}catch(d){alert(d)}g+=")";return g==="()"?"":g};this.getStringForRule=function(e){var g="",a="",b,d;for(b=0;b<this.p.ops.length;b++)if(this.p.ops[b].name===e.op){g=this.p.ops[b].operator;a=this.p.ops[b].name;break}for(b=0;b<this.p.columns.length;b++)if(this.p.columns[b].name===e.field){d=this.p.columns[b];break}b=e.data;if(a==="bw"||a==="bn")b+="%";if(a==="ew"||a==="en")b="%"+b;if(a===
"cn"||a==="nc")b="%"+b+"%";if(a==="in"||a==="ni")b=" ("+b+")";o.errorcheck&&z(e.data,d);return c.inArray(d.searchtype,["int","integer","float","number","currency"])!==-1||a==="nn"||a==="nu"?e.field+" "+g+" "+b:e.field+" "+g+' "'+b+'"'};this.resetFilter=function(){this.p.filter=c.extend(true,{},this.p.initFilter);this.reDraw();this.onchange()};this.hideError=function(){c("th.ui-state-error",this).html("");c("tr.error",this).hide()};this.showError=function(){c("th.ui-state-error",this).html(this.p.errmsg);
c("tr.error",this).show()};this.toUserFriendlyString=function(){return this.getStringForGroup(o.filter)};this.toString=function(){function e(b){if(a.p.errorcheck){var d,f;for(d=0;d<a.p.columns.length;d++)if(a.p.columns[d].name===b.field){f=a.p.columns[d];break}f&&z(b.data,f)}return b.op+"(item."+b.field+",'"+b.data+"')"}function g(b){var d="(",f;if(b.groups!==undefined)for(f=0;f<b.groups.length;f++){if(d.length>1)d+=b.groupOp==="OR"?" || ":" && ";d+=g(b.groups[f])}if(b.rules!==undefined)for(f=0;f<
b.rules.length;f++){if(d.length>1)d+=b.groupOp==="OR"?" || ":" && ";d+=e(b.rules[f])}d+=")";return d==="()"?"":d}var a=this;return g(this.p.filter)};this.reDraw();this.p.showQuery&&this.onchange();this.filter=true}}})};c.extend(c.fn.jqFilter,{toSQLString:function(){var k="";this.each(function(){k=this.toUserFriendlyString()});return k},filterData:function(){var k;this.each(function(){k=this.p.filter});return k},getParameter:function(k){if(k!==undefined)if(this.p.hasOwnProperty(k))return this.p[k];
return this.p},resetFilter:function(){return this.each(function(){this.resetFilter()})},addFilter:function(k){if(typeof k==="string")k=jQuery.jgrid.parse(k);this.each(function(){this.p.filter=k;this.reDraw();this.onchange()})}})})(jQuery);
