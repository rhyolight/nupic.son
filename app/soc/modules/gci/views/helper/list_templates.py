
LIST_TASKS_TEMPLATE = """
<div class="task-single task-single-admin task-single-in-progress level-easy even clearfix">
  <div class="cog"></div>
  <div class="task-single-content clearfix">
    <div class="task-single-admin-btns clearfix">
      <form action="/gci/task/delete/{{ key }}" method="post">
      <input type="submit" class="task-btn task-btn-delete" value="Delete"/>
      </form>
    </div>
    <span class="task-single-title"><a href="javascript:void(0)">{{ title }}</a></span>
    <div class="task-single-content-bottom clearfix">
      <div class="task-single-content-col1">
        <span class="task-single-info task-single-student">Student: <a href="javascript:void(0)"></span>
        <span class="task-single-info task-single-difficulty">Difficulty: <span class="emph">Easy</span></span>
      </div>
    </div>
  </div>
</div>
"""
