<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" dir="ltr" lang="en-US">
<head profile="http://gmpg.org/xfn/11">

    <title>Google Code-In</title>
    
    <meta name="viewport" content="width=device-width,initial-scale=1">

    <link type="text/css" rel="stylesheet" href="../css/style.css" />
    <!--[if lte IE 7]>
    <link type="text/css" rel="stylesheet" href="../css/ie.css" />
    <![endif]-->
    <link type="text/css" rel="stylesheet" href="http://fonts.googleapis.com/css?family=Oswald" />
    
    <!-- 
    ////////////////////////
       BEGIN JAVASCRIPT
    ////////////////////////
    -->
    <script type="text/javascript" src="../js/jquery-1.6.2.min.js" type=""></script>
    <script type="text/javascript" src="../js/jquery-ui-1.8.16.custom.min.js"></script>
    
    <!--
        Tab interface (Dashboards)
    -->
    <script type="text/javascript">
        $(function() {
        	$( ".block-tabs" ).tabs();
        });
    </script>
    
    <!--
        Select all checkbox (Admin Dashboard)
    -->
    <script type="text/javascript">
    $(function(){
        $(".task-group-actions-select-all-checkbox").click(function () {
              $('.case').attr('checked', this.checked);
        });
        $(".task-group-actions-select-all-checkbox").click(function(){
            if($(".task-group-actions-select-all-checkbox").length == $(".task-group-actions-select-all-checkbox:checked").length) {
                $(".task-single-check .checker span").addClass('checked');
            } else {
                $(".task-single-check .checker span").removeClass('checked');
            }
        });
    });
    </script>
    
    <!--
        Skinning form elements with Uniform
        http://pixelmatrixdesign.com/uniform
    -->
    <link rel="stylesheet" type="text/css" media="screen" href="../css/uniform.default.css" />
    <script src="../js/jquery.uniform.min.js" type="text/javascript"></script>
    <script type="text/javascript">
      $(function(){
        $("select, input:checkbox, input:radio").uniform();
      });
    </script>
    
    <!-- Task pages: Hide/show reply box -->
    <script type="text/javascript">
    $(document).ready(function(){
    	$(".single-comment-reply").hide();
    	$(".task-btn-comment-reply").click(function(){
    		$(this).toggleClass("active").next().slideToggle("slow");
    	});
    });
    </script>
    <script type="text/javascript">
    $(document).ready(function(){
    	$(".block-comments-post-new").hide();
    	$(".task-btn-comment-new").click(function(){
    		$(this).toggleClass("active").next().slideToggle("slow");
    	});
    });
    </script>
    <!-- 
    ////////////////////////
       END JAVASCRIPT
    ////////////////////////
    -->
    
    <!-- 
    ////////////////////////
       SELECTIVIZR FOR IE
    ////////////////////////
    -->
    <!--[if (gte IE 6)&(lte IE 8)]>
    <script type="text/javascript" src="../js/selectivizr-min.js"></script>
    <![endif]--> 
    
    <!-- 
    ////////////////////////
       BEGIN JQUERY UI DEMO
    ////////////////////////
    -->
    <script type="text/javascript">
		$(function(){

			// Accordion
			$("#accordion").accordion({ header: "h3" });

			// Tabs
			$('#tabs').tabs();


			// Dialog			
			$('#dialog').dialog({
				autoOpen: false,
				width: 600,
				buttons: {
					"Ok": function() { 
						$(this).dialog("close"); 
					}, 
					"Cancel": function() { 
						$(this).dialog("close"); 
					} 
				}
			});
			
			// Dialog Link
			$('#dialog_link').click(function(){
				$('#dialog').dialog('open');
				return false;
			});

			// Datepicker
			$('#datepicker').datepicker({
				inline: true
			});
			
			// Slider
			$('#slider').slider({
				range: true,
				values: [17, 67]
			});
			
			// Progressbar
			$("#progressbar").progressbar({
				value: 20 
			});
			
			//hover states on the static widgets
			$('#dialog_link, ul#icons li').hover(
				function() { $(this).addClass('ui-state-hover'); }, 
				function() { $(this).removeClass('ui-state-hover'); }
			);
			
		});
	</script>
    <!-- 
    ////////////////////////
       END JQUERY UI DEMO
    ////////////////////////
    -->
    
</head>
<body>

<!-- 
////////////////////////
   BEGIN WRAPPER
////////////////////////
-->
<div id="wrap">
<div id="main">
<div class="container_12">
    <div class="grid_12 header">
        <h1 class="logo ir"><a href="/">Google Code-In</a></h1>
    </div>
    <!-- end .grid_12 -->
    <div class="clear"></div>