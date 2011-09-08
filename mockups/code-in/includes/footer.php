</div>
<!-- end .container_12 -->

<div class="footer">
    <div class="container_12">
        <div class="grid_12">
            <ul class="menu menu-center-inline menu-footer">
                <li><a href="javascript:void(0)">About</a></li>
                <li><a href="javascript:void(0)">Contact</a></li>
                <li class="social"><a href="javascript:void(0)"><img src="../images/icon-fb.gif" height="17" width="9" alt="Facebook" /></a></li>
                <li class="social"><a href="javascript:void(0)"><img src="../images/icon-tw.gif" height="17" width="12" alt="Twitter" /></a></li>
                <li class="social"><a href="javascript:void(0)"><img src="../images/icon-bl.gif" height="17" width="16" alt="Blogger" /></a></li>
                <li class="social"><a href="javascript:void(0)"><img src="../images/icon-em.gif" height="17" width="17" alt="Email" /></a></li>
                <li class="social"><a href="javascript:void(0)"><img src="../images/icon-irc.gif" height="17" width="17" alt="IRC" /></a></li>
                <li><a href="javascript:void(0)">Privacy Policy</a></li>
            </ul>
            <ul class="menu menu-center-inline menu-credit">
                <li class="menu-credit-melange">Powered by <a href="javascript:void(0)" target="_blank"><img src="../images/credit-melange.png" height="17" width="69" alt="Melange" /></a></li>
                <li class="menu-credit-echoditto">Empowered by <a href="http://www.echoditto.com/" target="_blank"><img src="../images/credit-echoditto.png" height="17" width="71" alt="EchoDitto" /></a></li>
            </ul>
        </div>
        <!-- end .grid_12 -->
    </div>
    <!-- end .container_12 -->
</div>
<!--end .footer-->

<script type="text/javascript" src="../js/jquery-1.6.2.min.js" type=""></script>
<script type="text/javascript" src="../js/jquery-ui-1.8.16.custom.min.js"></script>
<script type="text/javascript">
    $(function() {
    	$( ".block-tabs" ).tabs();
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

<!--[if (gte IE 6)&(lte IE 8)]>
<script type="text/javascript" src="../js/selectivizr-min.js"></script>
<![endif]--> 

</body>
</html>