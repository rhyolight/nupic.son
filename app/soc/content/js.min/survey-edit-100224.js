(function(a){a(function(){function k(){c.find("td.twolineformfieldlabel > label").prepend(i).end();a("ol").find("li").each(function(){a(this).prepend(l.join(a(this).attr("id"))).end()});c.find(".short_answer").each(function(){a(this).attr("name",g+a(this).getPosition()+"short_answer__"+a(this).attr("name"))});c.find("[name=create-option-button]").each(function(){a("#index_for_"+a(this).attr("value")).val(a(this).getPosition())});c.find(".long_answer").each(function(){a(this).attr("name",g+a(this).getPosition()+
"long_answer__"+a(this).attr("name")).attr("overflow","auto")})}var c=a("div#survey_widget");c.parents("td.formfieldvalue:first").css({"float":"left",width:200});a("input#id_title").val()===""&&a(".formfielderror").length<1&&c.find("tr").remove();c.find("table:first").show();var g="survey__",i="<a class='delete'><img src='/soc/content/images/minus.gif'/></a>",l=["<a class='delete_item' id='del_","' ><img src='/soc/content/images/minus.gif'/></a> "],b=a("form").find("#id_survey_html").attr("value");
if(b&&b.length>1){c.html(b);c.find(".long_answer,input").each(function(){a(this).val(a(this).attr("val"))})}else k();var f=c.find("tbody:first"),j=c.find("#survey_options");a("form input, form button, form select").keypress(function(d){if(d.which&&d.which===13||d.keyCode&&d.keyCode===13){a(this).parents(".ui-dialog:first").find(":button:first").click();return false}});a("a.fetch_answers").click(function(){var d=this.id.replace("results_for_",""),h=window.location.pathname;h=h.replace("/edit/","/show/").replace("/results/",
"/show/");var m="?read_only=true&user_results="+d;a('<div style="overflow-y: auto; margin-bottom: 100px;"></div>').load(h+m+" #survey_widget").dialog({title:d,height:500,width:700})});f.bind("init",function(){c.find("input").each(function(){if((a(this).val().length<1||a(this).val()==="Write a Custom Prompt...")&&a(this).attr("type")!=="hidden")a(this).preserveDefaultText("Write a Custom Prompt...")});c.find(".long_answer, .tooltip_entry").each(function(){if(a(this).val().length<1||a(this).val()===
"Write a Custom Prompt For This Question...")a(this).preserveDefaultText("Write a Custom Prompt For This Question...");a(this).TextAreaExpander(100,500)});c.find("a.delete img").click(function(){var d=a(this).parents("tr:first"),h=a(d).find("label").attr("for");if(confirm("Deleting this field will remove all answers submitted for this field. Continue?")){var m=a("#EditForm"),n=a("#__deleted__");if(n.val())n.val(n.val()+","+h.replace("id_","")).end();else{h=a("<input type='hidden' value='"+h.replace("id_",
"")+"' />");h.attr({id:"__deleted__"}).attr({name:"__deleted__"});m.append(h)}d.next("tr").remove().end().remove()}});a("[name=create-option-button]").each(function(){a(this).click(function(){var d=a("#new_item_field_ul_id"),h=a("#new_item_dialog");d.val(a(this).parents("fieldset").children("ol").attr("id"));h.dialog("open").find("input:first").focus()}).hover(function(){a(this).addClass("ui-state-hover")},function(){a(this).removeClass("ui-state-hover")}).mousedown(function(){a(this).addClass("ui-state-active")}).mouseup(function(){a(this).removeClass("ui-state-active")})});
j.find(".AddQuestion").click(function(){a("#new_question_button_id").val(a(this).attr("id"));var d=a("#question_options_div");a(this).attr("id")==="choice"?d.show():d.hide();a("#new_question_dialog").dialog("open").find("input:first").focus()})}).trigger("init").bind("option_init",function(){c.find("a.delete_item").click(function(){var d=this.id.replace("del_","");a("#delete_item_field").val(d);a("#delete_item_dialog").dialog("open")}).end()}).trigger("option_init");b=a("select#id_taking_access");
var e=function(d){f.find("tr.role-specific").remove();switch(d){case "mentor evaluation":f.prepend('<tr class="role-specific"><th><label>Choose Project:</label></th><td> <select disabled=TRUE id="id_survey__NA__selection__project" name="survey__1__selection__see"><option>Survey Taker\'s ProjectsFor This Program</option></select> </td></tr>');f.append('<tr class="role-specific"><th><label>Assign Grade:</label></th><td><select disabled=TRUE id="id_survey__NA__selection__grade"name="survey__1__selection__see"><option>Pass/Fail</option></select></td></tr>');
break;case "student evaluation":f.prepend('<tr class="role-specific"><th><label>Choose Project:</label></th><td> <select disabled=TRUE id="id_survey__NA__selection__project" name="survey__1__selection__see"><option>Survey Taker\'s ProjectsFor This Program</option></select> </td></tr>');break}};b.change(function(){var d=a(this).val();e(d)});e(b.val());a("form").bind("submit",function(){f.find("tr.role-specific").remove();c.find(".long_answer,input").each(function(){a(this).attr("val",a(this).val())});
a(this).find("#id_survey_html").attr("value",c.html());c.find("input").each(function(){a(this).val()==="Write a Custom Prompt..."&&a(this).val("")});c.find(".long_answer, .tooltip_entry").each(function(){a(this).val()==="Write a Custom Prompt For This Question..."&&a(this).val("")});a("input#id_s_html").val(c.find("div#survey_options").remove().end().html());f.find(".sortable").each(function(){a("#order_for_"+this.id).val(a(this).sortable("serialize"))})})})})(jQuery);
(function(a){jQuery.fn.extend({getPosition:function(){var k=a(this).parents("fieldset:first");return k.parents("table:first").find("fieldset").index(k)+"__"}})})(jQuery);(function(a){a(function(){a(".sortable").each(function(k,c){a(c).sortable().disableSelection().end()})})})(jQuery);(function(a){a(function(){function k(c){var g=a(this).parent().attr("id").replace("-li-","_");g+="__field";a("#"+g).val(c.current)}a(".editable_option").editable({editBy:"dblclick",submit:"change",cancel:"cancel",onSubmit:k})})})(jQuery);
(function(a){a(function(){var k=["<a class='delete_item' id='del_","' ><img src='/soc/content/images/minus.gif'/></a> "];a("#delete_item_dialog").dialog({autoOpen:false,bgiframe:true,resizable:false,height:300,modal:true,overlay:{backgroundColor:"#000",opacity:0.5},buttons:{"Delete this item":function(){a("#"+a("#delete_item_field").val()).remove();a("#delete_item_field").val("");a(this).dialog("close")},Cancel:function(){a("#delete_item_field").val("");a(this).dialog("close")}}});a("#new_item_dialog").dialog({bgiframe:true,
autoOpen:false,height:300,width:300,modal:true,buttons:{"Add option":function(){var c=a("#new_item_field_ul_id").val(),g=a("#"+c),i=a("#new_item_name").val(),l=g.find("li").length,b="id_"+c+"_"+l;c=a(['<li id="id-li-',c,"_",l,'" class="ui-state-defaolt sortable_li"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><span id="',b,'" class="editable_option" name="',b,'__field">',i,'</span><input type="hidden" id="',b,'__field" name="',b,'__field" value="',i.replace(/\"/g,"&quot;"),'" ></li>'].join(""));
g.append(c.prepend(k.join(c.attr("id"))));g.sortable().disableSelection();a("#new_item_name").val("");a("#new_item_field_ol_id").val("");a(this).dialog("close")},Cancel:function(){a("#new_item_name").val("");a("#new_item_field_ul_id").val("");a(this).dialog("close")}}})})})(jQuery);
(function(a){a(function(){var k=["<a class='delete_item' id='del_","' ><img src='/soc/content/images/minus.gif'/></a> "],c=a("div#survey_widget").find("tbody:first");a("#new_question_dialog").dialog({bgiframe:true,autoOpen:false,height:400,width:300,modal:true,buttons:{"Add question":function(){var g=a("#new_question_button_id").val(),i=a("div#survey_widget").find("tbody:first");a("#new_question_button_id").val("");var l=a("<tr><th><label><a class='delete'><img src='/soc/content/images/minus.gif'/></a></label></th><td>  </td></tr>"),
b=a("#new_question_name").val(),f=a("#new_question_content").val(),j=a("#new_question_options").val();if(b!==""){a("#new_question_name").val("");a("#new_question_content").val("");a("#new_question_options").val("");var e=false,d=g+"__",h=i.find("fieldset").length,m=h+1+"__";switch(g){case "short_answer":e=['<fieldset>\n<label for="required_for_',b,'">Required</label><select id="required_for_',b,'" name="required_for_',b,'"><option value="True" selected="selected">True</option><option value="False">False</option></select><label for="comment_for_',
b,'">Allow Comments</label><select id="comment_for_',b,'" name="comment_for_',b,'"><option value="True" selected="selected">True</option><option value="False">False</option></select><input type=\'text\' class=\'short_answer\'></fieldset>'].join("");break;case "long_answer":i.find("fieldset");e=['<fieldset>\n<label for="required_for_',b,'">Required</label><select id="required_for_',b,'" name="required_for_',b,'"><option value="True" selected="selected">True</option><option value="False">False</option></select><label for="comment_for_',
b,'">Allow Comments</label><select id="comment_for_',b,'" name="comment_for_',b,"\"><option value=\"True\" selected=\"selected\">True</option><option value=\"False\">False</option></select><textarea wrap='hard' cols='40' rows='10' class='long_answer'/></fieldset>"].join("");break;case "selection":e="<select><option></option><option>Add A New Option...</option></select>";break;case "pick_multi":e="<fieldset class='fieldset'><input type='button'value='Add A New Option...' /></fieldset>";break;case "choice":e=
"<fieldset class='fieldset'><input type='button'value='Add A New Option...' /></fieldset>";break}if(e){var n=['\n  <input type="hidden" name="NEW_',b,'" id="NEW_',b,'" value="',f,'"/>'].join("");h=i.find("fieldset").length;m=h+1+"__";d="survey__"+m+d+b;if(g==="choice"){e=a(['<fieldset>\n<label for="required_for_',b,'">Required</label><select id="required_for_',b,'" name="required_for_',b,'"><option value="True" selected="selected">True</option><option value="False">False</option></select><label for="comment_for_',
b,'">Allow Comments</label><select id="comment_for_',b,'" name="comment_for_',b,'"><option value="True" selected="selected">True</option><option value="False">False</option></select><label for="render_for_',b,'">Render as</label>\n  <select id="render_for_',b,'" name="render_for_',b,'">\n    <optionselected="selected" value="select">select</option>\n    <option value="checkboxes">checkboxes</option>\n    <option value="radio_buttons">radio_buttons</option>\n  </select>\n  <input type="hidden" id="order_for_',
b,'\n  " name="order_for_',b,'" value=""/>\n  <input type="hidden" id="index_for_',b,'\n  " name="index_for_',b,'" value="',h+1,'"/>\n  <ol id="',b,'" class="sortable"></ol>',n,'\n  <button name="create-option-button"id="create-option-button__',b,'" class="ui-button ui-state-default ui-corner-all" value="',b,'" onClick="return false;">Create new option</button>\n</fieldset>'].join(""));a(e).attr({id:"id_"+d,name:d});l.find("label").attr("for","NEW_"+b).append(f).end().find("td").append(e);i.append(l).end();
if(j){g=j.split("\n");i=a("#"+b);l=g.length;j=e=j="";for(f=0;f<l;f+=1){e="id_"+b+"_"+f;j=g[f];j=a(['<li id="id-li-',b,"_",f,'" class="ui-state-defaolt sortable_li"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span>','<span id="'+e+'" class="editable_option" name="',e,'__field">',j,'</span><input type="hidden" id="',e,'__field" name="',e,'__field" value="',j.replace(/\"/g,"&quot;"),'" ></li>'].join(""));i.append(j.prepend(k.join(j.attr("id"))));i.sortable().disableSelection()}c.trigger("option_init")}}else{e=
a(e);a(e).find(".long_answer, .short_answer").attr({id:"id_"+d,name:d});l.find("label").attr("for","id_"+d).append(f).end().find("td").append(e).append(a(n));i.append(l)}c.trigger("init")}}a("#new_question_name").val("");a("#new_question_content").val("");a("#new_question_options").val("");a(this).dialog("close")},Cancel:function(){a("#new_question_name").val("");a("#new_question_button_id").val("");a("#new_question_content").val("");a("#new_question_options").val("");a(this).dialog("close")}}})})})(jQuery);
