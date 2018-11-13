# 知识点精华

1. 列表字符串反转
    - a = [3, 5, 1, 6], b = 'haibin'
    - list1[::-1], str1[::-1]
    - list(reversed(list1))
    - 

2. django.db.utils.IntegrityError: UNIQUE constraint failed: course_course.slug
    - sqlite 唯一约束失败
    - 定位于某个表字段上，该字段是表的主键。
    - 原因：插入的数据中该主键字段值在表中已有存在的记录。
    - 解决方案：重新调整插入语句中该主键字段的值，保证约束唯一性。
    - 参考：https://www.cnblogs.com/MakeView660/p/8488759.html

3. http://127.0.0.1:8000/course/manage-course/ 中没有显示课程列表
    - 列表显示代码（manage_course_list.html）：
        ```
        {% for course in courses %}
            <tr id={{ forloop.counter }}>
                ...
            </tr>
        ```
    - 原因：`/mysite/course/views.py`中context_object_name赋值出错，导致manage_course_list.html中{% for course in courses %}找不到courses
        ```
        class ManageCourseListView(UserCourseMixin, ListView):
            context_object_name = "course"
            template_name = 'course/manage/manage_course_list.html'
       ```
    - 解决：`context_object_name = "courses"`

4. django urls.py中使用path中参数调研view的as_view()函数时，不能省去其（）