<?php include '../includes/header.php'?>

    <div class="grid_3 side">
        <div class="block block-main-nav">
            <ul class="menu">
                <li><a href="javascript:void(0)">My Dashboard</a>
                    <ul>
                        <li><a href="javascript:void(0)">Create a new task</a></li>
                        <li class="active"><a href="javascript:void(0)">Update profile</a></li>
                    </ul>
                </li>
                <li><a href="javascript:void(0)">About Us</a></li>
                <li><a href="javascript:void(0)">Get Started</a></li>
                <li><a href="javascript:void(0)">Participating Organizations</a></li>
                <li><a href="javascript:void(0)">Blog</a></li>
            </ul>
        </div>
        <!-- end .block.block-main-nav -->
        
        <div class="block block-status block-status-sm">
            <div class="block-status-user">
                You are logged in as: <a href="javascript:void(0)">eric_schmidt@gmail.com</a> <a href="javascript:void(0)">(change)</a>
            </div>
            <div class="block-status-action block-status-action-single clearfix">
                <a href="javascript:void(0)" class="block-status-action-dashboard"><span>My Dashboard</span></a>
            </div>
        </div>
        <!-- end .block.block-status.block-status-sm -->
    </div>
    <!-- end .grid_3.side -->
    <div class="grid_9 main">
        <div class="block block-form">
            <div class="block-form-title">
                <span class="title">Update profile</span>
                <span class="req">* fields required</span>
            </div>
            
        	<form action="#" method="post" class="form-create-task clearfix">
    			<fieldset id="fieldset-task-short-description">
	        		<div class="form-row">
	    			    <label for="test-name" class="form-label">Full name</label>
	    			    <input name="test-name" value="" type="text">
	        		</div>
	        	</fieldset>
	        	<fieldset id="fieldset-task-type-tags">
	        	    <div class="form-row grid_4 alpha form-row-task-type">
	        	        <label for="type" class="form-label">Avatar</label>
	        	        <span class="note">The icon to represent you on various pages on this site</span>
	        	        
	        	        <select id="user-avatar" class="mydds">
	        	              <option value="calendar" selected="selected">Calendar</option>
	        	              <option value="shopping_cart" title="../images/avatar-test2.png">Shopping Cart</option>
	        	              <option value="cd" title="../images/avatar-test.png">CD</option>
	        	              <option value="email" title="../images/avatar-test2.png">Email</option>
	        	         </select>
	        	         
	        	    	<div id="preview"><img src="../images/avatar-test.png" width="80" height="80"></div>
	        	    </div>
	
	        	    <div class="form-row grid_4 omega form-row-task-tags">
	        	        <label for="tags" class="form-label">Something else<em>*</em></label>
	        	        <input name="tags" value="" type="text">
	        	    </div>
        	    </fieldset>

        	    <div class="form-row form-row-buttons">
        	    	<input value="Submit" class="button" type="submit">
        	    </div>
        	</form>
        	
        </div>
        <!-- end .block.block-user-message -->
    </div>
    <!-- end .grid_9.main -->

<?php include '../includes/footer.php'?>