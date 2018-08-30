# Django 笔记
## 常用命令
- python -m django --version 查看Django版本

- django-adimin startproject [projectname]: 创建项目

- python manage.py runserver：启动服务器
    - python manage.py runserver 8080：更改服务器端口，默认情况下为8000
    - python manage.py runserver 0.0.0.0:8000： ‘ 0.0.0.0 ’ 这个 IP 地址，告诉服务器去侦听任意的网络接口
    - 完成这些设置后，你本地网络中的其它计算机就可以在浏览器中访问你的 IP 地址了。比如：http://192.168.1.103:8000/

- python manage.py startapp polls：创建应用

- python -c "import django; print(django.__path__)" 查看django源文件路径

- python manage.py shell
    - 我们使用这个命令而不是简单的使用 "Python" 是因为 manage.py 会设置 DJANGO_SETTINGS_MODULE 环境变量，这个变量会让 Django 根据 mysite/settings.py 文件来设置 Python 包的导入路径。

- python manage.py makemigrations, python manage.py migrate 创建数据表

## 视图
- 视图函数和导入声明：
    ```
    from django.http import HttpResponse
    def hello(request):
        return HttpResponse("Hello world")
    ```
    - 其中，request是django.http.HttpRequest类的一个实例，视图函数的第一个参数必须是request。
    - 一个视图就是Python的一个函数。这个函数第一个参数的类型是HttpRequest；它返回一个HttpResponse实例。为了使一个Python的函数成为一个Django可识别的视图，它必须满足这两个条件。

- 每个视图必须要做的只有两件事：返回一个包含被请求页面内容的 HttpResponse 对象，或者抛出一个异常，比如 Http404 。 

## URLconf
- 我们需要通过一个详细描述的URL来显式的告诉项目并且激活这个视图。为了绑定视图函数和URL，我们使用URLconf。

- URLconf 就像是 Django 所支撑网站的目录。 它的本质是 URL 模式以及要为该 URL 模式调用的视图函数之间的映射表。 它就是以这种方式告诉 Django，对于这个 URL 调用这段代码，对于那个 URL 调用那
段代码。 例如，当用户访问/foo/时，调用视图函数foo_view()，这个视图函数存在于Python模块文件view.py中。
- urls.py
    ```
    from django.contrib import admin
    from django.urls import path
    from mysite.views import hello

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('hello/', hello),
    ]
    ```
    Django 2.0版本中django.urls.path不支持正则表达式，若url路径中包含正则，可使用django.urls.re_path代替

- 在Django的应用程序中，URL的定义和视图函数之间是松 耦合的，换句话说，决定URL返回哪个视图函数和实现这个视图函数是在两个不同的地方。 这使得 开发人员可以修改一块而不会影响另一块。
    ```
        from django.contrib import admin
        from django.urls import include, path

        urlpatterns = [
            path('polls/', include('polls.urls')),
            path('admin/', admin.site.urls),
        ]
    ```
- 函数 include() 允许引用其它 URLconfs。每当 Django 遇到 :func：~django.urls.include 时，它会截断与此项匹配的 URL 的部分，并将剩余的字符串发送到 URLconf 以供进一步处理。

- path函数
    - 函数 path() 具有四个参数，两个必须参数：route 和 view，两个可选参数：kwargs 和 name。现在，是时候来研究这些参数的含义了。

    - path() 参数： route，route 是一个匹配 URL 的准则（类似正则表达式）。当 Django 响应一个请求时，它会从 urlpatterns 的第一项开始，按顺序依次匹配列表中的项，直到找到匹配的项。

    - 这些准则不会匹配 GET 和 POST 参数或域名。例如，URLconf 在处理请求 https://www.example.com/myapp/ 时，它会尝试匹配 myapp/ 。处理请求 https://www.example.com/myapp/?page=3 时，也只会尝试匹配 myapp/。

    - path() 参数： view，当 Django 找到了一个匹配的准则，就会调用这个特定的视图函数，并传入一个 HttpRequest 对象作为第一个参数，被“捕获”的参数以关键字参数的形式传入。稍后，我们会给出一个例子。

    - path() 参数： kwargs，任意个关键字参数可以作为一个字典传递给目标视图函数。

    - path() 参数： name，为你的 URL 取名能使你在 Django 的任意地方唯一地引用它，尤其是在模板中。这个有用的特性允许你只改一个文件就能全局地修改某个 URL 模式。

## 数据库
- mysite/settings.py 。这是个包含了 Django 项目设置的 Python 模块。

- 通常，这个配置文件使用 SQLite 作为默认数据库。如果你不熟悉数据库，或者只是想尝试下 Django，这是最简单的选择。Python 内置 SQLite，所以你无需安装额外东西来使用它。当你开始一个真正的项目时，你可能更倾向使用一个更具扩展性的数据库，例如 PostgreSQL，避免中途切换数据库这个令人头疼的问题。

- python manage.py migrate
    - 这个 migrate 命令检查 INSTALLED_APPS 设置，为其中的每个应用创建需要的数据表，至于具体会创建什么，这取决于你的 mysite/settings.py 设置文件和每个应用的数据库迁移文件（我们稍后会介绍这个）。这个命令所执行的每个迁移操作都会在终端中显示出来。如果你感兴趣的话，运行你数据库的命令行工具，并输入 \dt (PostgreSQL)， SHOW TABLES; (MySQL)， .schema (SQLite)或者 SELECT TABLE_NAME FROM USER_TABLES; (Oracle) 来看看 Django 到底创建了哪些表。

- 数据库查询
    - 新建对象
    ```
    1. Person.objects.create(name=name,age=age)
    2. p = Person(name="WZ", age=23)
       p.save()
    3. p = Person(name="TWZ")
       p.age = 23
       p.save()
    4. Person.objects.get_or_create(name="WZT", age=23) 这种方法是防止重复很好的方法，但是速度要相对慢些，返回一个元组，第一个为Person对象，第二个为True或False, 新建时返回的是True, 已经存在时返回False.
    ```
    - 获取对象
    ```
    1. Person.objects.all()
    2. Person.objects.all()[:10] 切片操作，获取10个人，不支持负索引，切片可以节约内存
    3. Person.objects.get(name=name)
    
    get是用来获取一个对象的，如果需要获取满足条件的一些人，就要用到filter
    4. Person.objects.filter(name="abc")  # 等于Person.objects.filter(name__exact="abc") 名称严格等于 "abc" 的人
    5. Person.objects.filter(name__iexact="abc")  # 名称为 abc 但是不区分大小写，可以找到 ABC, Abc, aBC，这些都符合条件
    6. Person.objects.filter(name__contains="abc")  # 名称中包含 "abc"的人
    7. Person.objects.filter(name__icontains="abc")  #名称中包含 "abc"，且abc不区分大小写
    8. Person.objects.filter(name__regex="^abc")  # 正则表达式查询
    9. Person.objects.filter(name__iregex="^abc")  # 正则表达式不区分大小写
    
    filter是找出满足条件的，当然也有排除符合某条件的
    10. Person.objects.exclude(name__contains="WZ")  # 排除包含 WZ 的Person对象
    11. Person.objects.filter(name__contains="abc").exclude(age=23)  # 找出名称含有abc, 但是排除年龄是23岁的
    ```
    - 注意：
    ```
    $ python manage.py shell
 
    >>> from people.models import Person
    >>> Person.objects.create(name="WeizhongTu", age=24)
    <Person: Person object>
    >>>
    ```
    我们新建了一个用户WeizhongTu 那么如何从数据库是查询到它呢？
    ```
    >>> Person.objects.get(name="WeizhongTu")
    <Person: Person object>
    >>>
    ```
    我们用了一个 .objects.get() 方法查询出来符合条件的对象，但是大家注意到了没有，查询结果中显示<Person: Person object>，这里并没有显示出与WeizhongTu的相关信息，如果用户多了就无法知道查询出来的到底是谁，查询结果是否正确，我们重新修改一下 people/models.py
    ```
    from django.db import models
 
    class Person(models.Model):
        name = models.CharField(max_length=30)
        age = models.IntegerField()
     
        def __unicode__(self):
        # 在Python3中使用 def __str__(self):
        return self.name
    ```
    - 当有一对多，多对一，或者多对多的关系的时候，先把相关的对象查询出来
    ```
    >>> from blog.models import Entry
    >>> entry = Entry.objects.get(pk=1)
    >>> cheese_blog = Blog.objects.get(name="Cheddar Talk")
    >>> entry.blog = cheese_blog
    >>> entry.save()
    ```
    - 删除符合条件的结果, 和上面类似，得到满足条件的结果，然后 delete 就可以(危险操作，正式场合操作务必谨慎)，比如：
    ```
    Person.objects.filter(name__contains="abc").delete() # 删除 名称中包含 "abc"的人
 
    如果写成 
    people = Person.objects.filter(name__contains="abc")
    people.delete()
    效果也是一样的，Django实际只执行一条 SQL 语句。
    ```
    - 更新某个内容
    1. 批量更新，适用于 .all()  .filter()  .exclude() 等后面 (危险操作，正式场合操作务必谨慎)
    ```
    Person.objects.filter(name__contains="abc").update(name='xxx') # 名称中包含 "abc"的人 都改成 xxx
    Person.objects.all().delete() # 删除所有 Person 记录
    ```
    2. 单个 object 更新，适合于 .get(), get_or_create(), update_or_create() 等得到的 obj，和新建很类似。
    ```
    twz = Author.objects.get(name="WeizhongTu")
    twz.name="WeizhongTu"
    twz.email="tuweizhong@163.com"
    twz.save()  # 最后不要忘了保存！！！
    ```
    - QuerySet（数据库接口相关的接口）是可迭代的
    ```
    es = Entry.objects.all()
    for e in es:
        print(e.headline)
    ```
    - 注意事项：
    1. 如果只是检查 Entry 中是否有对象，应该用 Entry.objects.all().exists()
    2. QuerySet 支持切片 Entry.objects.all()[:10] 取出10条，可以节省内存
    3. 用 len(es) 可以得到Entry的数量，但是推荐用 Entry.objects.count()来查询数量，后者用的是SQL：SELECT COUNT(*)
    4. list(es) 可以强行将 QuerySet 变成 列表

    - QuerySet 是可以用pickle序列化到硬盘再读取出来的
    ```
    >>> import pickle
    >>> query = pickle.loads(s)     # Assuming 's' is the pickled string.
    >>> qs = MyModel.objects.all()
    >>> qs.query = query            # Restore the original 'query'.
    ```

    - QuerySet查询结果排序，作者按照名称排序
    ```
    Author.objects.all().order_by('name')
    Author.objects.all().order_by('-name') # 在 column name 前加一个负号，可以实现倒序
    ```

    - QuerySet支持链式查询
    ```
    Author.objects.filter(name__contains="WeizhongTu").filter(email="tuweizhong@163.com")
    Author.objects.filter(name__contains="Wei").exclude(email="tuweizhong@163.com")
 
    # 找出名称含有abc, 但是排除年龄是23岁的
    Person.objects.filter(name__contains="abc").exclude(age=23)
    ```

    - QuerySet不支持负索引
    ```
    Person.objects.all()[:10] 切片操作，前10条
    Person.objects.all()[-10:] 会报错！！！
 
    # 1. 使用 reverse() 解决
    Person.objects.all().reverse()[:2] # 最后两条
    Person.objects.all().reverse()[0] # 最后一条
    
    # 2. 使用 order_by，在栏目名（column name）前加一个负号
    Author.objects.order_by('-id')[:20] # id最大的20条
    ```

    - QuerySet重复问题， 使用.distinct()去重，一般的情况下，QuerySet 中不会出来重复的，重复是很罕见的，但是当跨越多张表进行检索后，结果并到一起，可能会出来重复的值（我最近就遇到过这样的问题）
    ```
    qs1 = Pathway.objects.filter(label__name='x')
    qs2 = Pathway.objects.filter(reaction__name='A + B >> C')
    qs3 = Pathway.objects.filter(inputer__name='WeizhongTu')
    
    # 合并到一起
    qs = qs1 | qs2 | qs3
    这个时候就有可能出现重复的
    
    # 去重方法
    qs = qs.distinct()
    ```
    - 查看Django queryset 执行的 SQL
    ```
    In [1]: print str(Author.objects.all().query)
    SELECT "blog_author"."id", "blog_author"."name", "blog_author"."qq", "blog_author"."addr", "blog_author"."email" FROM "blog_author"
    简化一下，就是：SELECT id, name, qq, addr, email FROM blog_author;

    In [2]: print str(Author.objects.filter(name="WeizhongTu").query)
    SELECT "blog_author"."id", "blog_author"."name", "blog_author"."qq", "blog_author"."addr", "blog_author"."email" FROM "blog_author" WHERE "blog_author"."name" = WeizhongTu
    简化一下，就是：SELECT id, name, qq, addr, email FROM blog_author WHERE name=WeizhongTu;

    所以，当不知道Django做了什么时，你可以把执行的 SQL 打出来看看，也可以借助 django-debug-toolbar 等工具在页面上看到访问当前页面执行了哪些SQL，耗时等。
    还有一种办法就是修改一下 log 的设置，后面会讲到。
    ```
    - values_list 获取元组形式结果
    ```
    1 比如我们要获取作者的 name 和 qq

    In [6]: authors = Author.objects.values_list('name', 'qq')

    In [7]: authors
    Out[7]: <QuerySet [(u'WeizhongTu', u'336643078'), (u'twz915', u'915792575'), (u'wangdachui', u'353506297'), (u'xiaoming', u'004466315')]>

    In [8]: list(authors)
    Out[8]: 
    [(u'WeizhongTu', u'336643078'),
    (u'twz915', u'915792575'),
    (u'wangdachui', u'353506297'),
    (u'xiaoming', u'004466315')]

    如果只需要 1 个字段，可以指定 flat=True

    In [9]: Author.objects.values_list('name', flat=True)
    Out[9]: <QuerySet [u'WeizhongTu', u'twz915', u'wangdachui', u'xiaoming']>

    In [10]: list(Author.objects.values_list('name', flat=True))
    Out[10]: [u'WeizhongTu', u'twz915', u'wangdachui', u'xiaoming']

    2 查询 twz915 这个人的文章标题

    In [11]: Article.objects.filter(author__name='twz915').values_list('title', flat=True)
    Out[11]: <QuerySet [u'HTML \u6559\u7a0b_1', u'HTML \u6559\u7a0b_2', u'HTML \u6559\u7a0b_3', u'HTML \u6559\u7a0b_4', u'HTML \u6559\u7a0b_5', u'HTML \u6559\u7a0b_6', u'HTML \u6559\u7a0b_7', u'HTML \u6559\u7a0b_8', u'HTML \u6559\u7a0b_9', u'HTML \u6559\u7a0b_10', u'HTML \u6559\u7a0b_11', u'HTML \u6559\u7a0b_12', u'HTML \u6559\u7a0b_13', u'HTML \u6559\u7a0b_14', u'HTML \u6559\u7a0b_15', u'HTML \u6559\u7a0b_16', u'HTML \u6559\u7a0b_17', u'HTML \u6559\u7a0b_18', u'HTML \u6559\u7a0b_19', u'HTML \u6559\u7a0b_20']>
    ```
    - values 获取字典形式的结果
    ```
    1 比如我们要获取作者的 name 和 qq

    In [13]: Author.objects.values('name', 'qq')
    Out[13]: <QuerySet [{'qq': u'336643078', 'name': u'WeizhongTu'}, {'qq': u'915792575', 'name': u'twz915'}, {'qq': u'353506297', 'name': u'wangdachui'}, {'qq': u'004466315', 'name': u'xiaoming'}]>


    In [14]: list(Author.objects.values('name', 'qq'))
    Out[14]: 
    [{'name': u'WeizhongTu', 'qq': u'336643078'},
    {'name': u'twz915', 'qq': u'915792575'},
    {'name': u'wangdachui', 'qq': u'353506297'},
    {'name': u'xiaoming', 'qq': u'004466315'}]

    2 查询 twz915 这个人的文章标题

    In [23]: Article.objects.filter(author__name='twz915').values('title')
    Out[23]: <QuerySet [{'title': u'HTML \u6559\u7a0b_1'}, {'title': u'HTML \u6559\u7a0b_2'}, {'title': u'HTML \u6559\u7a0b_3'}, {'title': u'HTML \u6559\u7a0b_4'}, {'title': u'HTML \u6559\u7a0b_5'}, {'title': u'HTML \u6559\u7a0b_6'}, {'title': u'HTML \u6559\u7a0b_7'}, {'title': u'HTML \u6559\u7a0b_8'}, {'title': u'HTML \u6559\u7a0b_9'}, {'title': u'HTML \u6559\u7a0b_10'}, {'title': u'HTML \u6559\u7a0b_11'}, {'title': u'HTML \u6559\u7a0b_12'}, {'title': u'HTML \u6559\u7a0b_13'}, {'title': u'HTML \u6559\u7a0b_14'}, {'title': u'HTML \u6559\u7a0b_15'}, {'title': u'HTML \u6559\u7a0b_16'}, {'title': u'HTML \u6559\u7a0b_17'}, {'title': u'HTML \u6559\u7a0b_18'}, {'title': u'HTML \u6559\u7a0b_19'}, {'title': u'HTML \u6559\u7a0b_20'}]>
    ```
    
    - 注意：
        1. values_list 和 values 返回的并不是真正的 列表 或 字典，也是 queryset，他们也是 lazy evaluation 的（惰性评估，通俗地说，就是用的时候才真正的去数据库查）
        2. 如果查询后没有使用，在数据库更新后再使用，你发现得到在是新内容！！！如果想要旧内容保持着，数据库更新后不要变，可以 list 一下
        3. 如果只是遍历这些结果，没有必要 list 它们转成列表（浪费内存，数据量大的时候要更谨慎！！！）

    
    - extra 实现 别名，条件，排序等
    ```
    extra 中可实现别名，条件，排序等，后面两个用 filter, exclude 一般都能实现，排序用 order_by 也能实现。我们主要看一下别名这个
    比如 Author 中有 name， Tag 中有 name 我们想执行
    SELECT name AS tag_name FROM blog_tag;
    这样的语句，就可以用 select 来实现，如下：

    In [44]: tags = Tag.objects.all().extra(select={'tag_name': 'name'})

    In [45]: tags[0].name
    Out[45]: u'Django'

    In [46]: tags[0].tag_name
    Out[46]: u'Django'

    我们发现 name 和 tag_name 都可以使用，确认一下执行的 SQL


    In [47]: Tag.objects.all().extra(select={'tag_name': 'name'}).query.__str__()
    Out[47]: u'SELECT (name) AS "tag_name", "blog_tag"."id", "blog_tag"."name" FROM "blog_tag"'

    我们发现查询的时候弄了两次 (name) AS "tag_name" 和 "blog_tag"."name"
    如果我们只想其中一个能用，可以用 defer 排除掉原来的 name （后面有讲）


    In [49]: Tag.objects.all().extra(select={'tag_name': 'name'}).defer('name').query.__str__()
    Out[49]: u'SELECT (name) AS "tag_name", "blog_tag"."id" FROM "blog_tag"'
    也许你会说为什么要改个名称，最常见的需求就是数据转变成 list，然后可视化等，我们在下面一个里面讲
    ```
    - annotate 聚合 计数，求和，平均数等
    ```
    1 计数
    我们来计算一下每个作者的文章数（我们每个作者都导入的Article的篇数一样，所以下面的每个都一样）
    In [66]: from django.db.models import Count

    In [66]: Article.objects.all().values('author_id').annotate(count=Count('author')).values('author_id', 'count')
    Out[66]: <QuerySet [{'count': 20, 'author_id': 1}, {'count': 20, 'author_id': 2}, {'count': 20, 'author_id': 4}]>
    这是怎么工作的呢？

    In [67]: Article.objects.all().values('author_id').annotate(count=Count('author')).values('author_id', 'count').query.__str__()
    Out[67]: u'SELECT "blog_article"."author_id", COUNT("blog_article"."author_id") AS "count" FROM "blog_article" GROUP BY "blog_article"."author_id"'
    简化一下SQL: SELECT author_id, COUNT(author_id) AS count FROM blog_article GROUP BY author_id

    我们也可以获取作者的名称 及 作者的文章数

    In [72]: Article.objects.all().values('author__name').annotate(count=Count('author')).values('author__name', 'count')
    Out[72]: <QuerySet [{'count': 20, 'author__name': u'WeizhongTu'}, {'count': 20, 'author__name': u'twz915'}, {'count': 20, 'author__name': u'xiaoming'}]>
    细心的同学会发现，这时候实际上查询两张表，因为作者名称(author__name)在 blog_author 这张表中，而上一个例子中的 author_id 是 blog_article 表本身就有的字段

    2 求和 与 平均值
    2.1 求一个作者的所有文章的得分(score)平均值
    In [6]: from django.db.models import Avg

    In [7]: Article.objects.values('author_id').annotate(avg_score=Avg('score')).values('author_id', 'avg_score')
    Out[7]: <QuerySet [{'author_id': 1, 'avg_score': 86.05}, {'author_id': 2, 'avg_score': 83.75}, {'author_id': 5, 'avg_score': 85.65}]>

    执行的SQL

    In [8]: Article.objects.values('author_id').annotate(avg_score=Avg('score')).values('author_id', 'avg_score').qu
    ...: ery.__str__()
    Out[8]: u'SELECT "blog_article"."author_id", AVG("blog_article"."score") AS "avg_score" FROM "blog_article" GROUP BY "blog_article"."author_id"'

    2.2 求一个作者所有文章的总分

    In [12]: from django.db.models import Sum

    In [13]: Article.objects.values('author__name').annotate(sum_score=Sum('score')).values('author__name', 'sum_score')
    Out[13]: <QuerySet [{'author__name': u'WeizhongTu', 'sum_score': 1721}, {'author__name': u'twz915', 'sum_score': 1675}, {'author__name': u'zhen', 'sum_score': 1713}]>
    执行的SQL

    In [14]: Article.objects.values('author__name').annotate(sum_score=Sum('score')).values('author__name', 'sum_score').query.__str__()
    Out[14]: u'SELECT "blog_author"."name", SUM("blog_article"."score") AS "sum_score" FROM "blog_article" INNER JOIN "blog_author" ON ("blog_article"."author_id" = "blog_author"."id") GROUP BY "blog_author"."name"'
    ```

    - select_related 优化一对一，多对一查询
    ```
    开始之前我们修改一个 settings.py 让Django打印出在数据库中执行的语句
    settings.py 尾部加上
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG' if DEBUG else 'INFO',
            },
        },
    }

    这样当 DEBUG 为 True 的时候，我们可以看出 django 执行了什么 SQL 语句

    tu@pro ~/zqxt $ python manage.py shell

    In [1]: from blog.models import *

    In [2]: Author.objects.all()
    Out[2]: (0.001) SELECT "blog_author"."id", "blog_author"."name", "blog_author"."qq", "blog_author"."addr", "blog_author"."email" FROM "blog_author" LIMIT 21; args=()
    <QuerySet [<Author: WeizhongTu>, <Author: twz915>, <Author: dachui>, <Author: zhe>, <Author: zhen>]>
    标记背景为 黄色的部分就是打出的 log。
    假如，我们取出10篇Django相关的文章，并需要用到作者的姓名

    In [13]: articles = Article.objects.all()[:10]

    In [14]: a1 = articles[0]  # 取第一篇
    (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."content", "blog_article"."score" FROM "blog_article" LIMIT 1; args=()

    In [15]: a1.title
    Out[15]: u'Django \u6559\u7a0b_1'

    In [16]: a1.author_id
    Out[16]: 5

    In [17]: a1.author.name   # 再次查询了数据库，注意！！！
    (0.000) SELECT "blog_author"."id", "blog_author"."name", "blog_author"."qq", "blog_author"."addr", "blog_author"."email" FROM "blog_author" WHERE "blog_author"."id" = 5; args=(5,)
    Out[17]: u'zhen'
    这样的话我们遍历查询结果的时候就会查询很多次数据库，能不能只查询一次，把作者的信息也查出来呢？
    当然可以，这时就用到 select_related，我们的数据库设计的是一篇文章只能有一个作者，一个作者可以有多篇文章。
    现在要查询文章的时候连同作者一起查询出来，“文章”和“作者”的关系就是多对一，换句说说，就是一篇文章只可能有一个作者。

    In [18]: articles = Article.objects.all().select_related('author')[:10]

    In [19]: a1 = articles[0]  # 取第一篇
    (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."content", "blog_article"."score", "blog_author"."id", "blog_author"."name", "blog_author"."qq", "blog_author"."addr", "blog_author"."email" FROM "blog_article" INNER JOIN "blog_author" ON ("blog_article"."author_id" = "blog_author"."id") LIMIT 1; args=()

    In [20]: a1.title
    Out[20]: u'Django \u6559\u7a0b_1'

    In [21]: a1.author.name   # 嘻嘻，没有再次查询数据库！！
    Out[21]: u'zhen'
    ```

    - prefetch_related 优化一对多，多对多查询
    ```
    和 select_related 功能类似，但是实现不同。
    select_related 是使用 SQL JOIN 一次性取出相关的内容。
    prefetch_related 用于 一对多，多对多 的情况，这时 select_related 用不了，因为当前一条有好几条与之相关的内容。
    prefetch_related是通过再执行一条额外的SQL语句，然后用 Python 把两次SQL查询的内容关联（joining)到一起
    我们来看个例子，查询文章的同时，查询文章对应的标签。“文章”与“标签”是多对多的关系。

    In [24]: articles = Article.objects.all().prefetch_related('tags')[:10]

    In [25]: articles
    Out[25]: (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."content", "blog_article"."score" FROM "blog_article" LIMIT 10; args=()
    (0.001) SELECT ("blog_article_tags"."article_id") AS "_prefetch_related_val_article_id", "blog_tag"."id", "blog_tag"."name" FROM "blog_tag" INNER JOIN "blog_article_tags" ON ("blog_tag"."id" = "blog_article_tags"."tag_id") WHERE "blog_article_tags"."article_id" IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10); args=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    <QuerySet [<Article: Django 教程_1>, <Article: Django 教程_2>, <Article: Django 教程_3>, <Article: Django 教程_4>, <Article: Django 教程_5>, <Article: Django 教程_6>, <Article: Django 教程_7>, <Article: Django 教程_8>, <Article: Django 教程_9>, <Article: Django 教程_10>]>

    遍历查询的结果：
    不用 prefetch_related 时
    In [9]: articles = Article.objects.all()[:3]

    In [10]: for a in articles:
        ...:     print a.title, a.tags.all()
        ...:     
    (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."content", "blog_article"."score" FROM "blog_article" LIMIT 3; args=()

    (0.000) SELECT "blog_tag"."id", "blog_tag"."name" FROM "blog_tag" INNER JOIN "blog_article_tags" ON ("blog_tag"."id" = "blog_article_tags"."tag_id") WHERE "blog_article_tags"."article_id" = 1 LIMIT 21; args=(1,)

    Django 教程_1 <QuerySet [<Tag: Django>]>

    (0.000) SELECT "blog_tag"."id", "blog_tag"."name" FROM "blog_tag" INNER JOIN "blog_article_tags" ON ("blog_tag"."id" = "blog_article_tags"."tag_id") WHERE "blog_article_tags"."article_id" = 2 LIMIT 21; args=(2,)

    Django 教程_2 <QuerySet [<Tag: Django>]>

    (0.000) SELECT "blog_tag"."id", "blog_tag"."name" FROM "blog_tag" INNER JOIN "blog_article_tags" ON ("blog_tag"."id" = "blog_article_tags"."tag_id") WHERE "blog_article_tags"."article_id" = 3 LIMIT 21; args=(3,)

    Django 教程_3 <QuerySet [<Tag: Django>]>

    用 prefetch_related 我们看一下是什么样子



    In [11]: articles = Article.objects.all().prefetch_related('tags')[:3]

    In [12]: for a in articles:
    ...:     print a.title, a.tags.all()
    ...:     
    (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."content", "blog_article"."score" FROM "blog_article" LIMIT 3; args=()
    (0.000) SELECT ("blog_article_tags"."article_id") AS "_prefetch_related_val_article_id", "blog_tag"."id", "blog_tag"."name" FROM "blog_tag" INNER JOIN "blog_article_tags" ON ("blog_tag"."id" = "blog_article_tags"."tag_id") WHERE "blog_article_tags"."article_id" IN (1, 2, 3); args=(1, 2, 3)
    Django 教程_1 <QuerySet [<Tag: Django>]>
    Django 教程_2 <QuerySet [<Tag: Django>]>
    Django 教程_3 <QuerySet [<Tag: Django>]>
    我们可以看到第二条 SQL 语句，一次性查出了所有相关的内容。
    ```

    - defer 排除不需要的字段
    ```
    在复杂的情况下，表中可能有些字段内容非常多，取出来转化成 Python 对象会占用大量的资源。
    这时候可以用 defer 来排除这些字段，比如我们在文章列表页，只需要文章的标题和作者，没有必要把文章的内容也获取出来（因为会转换成python对象，浪费内存）

    In [13]: Article.objects.all()
    Out[13]: (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."content", "blog_article"."score" FROM "blog_article" LIMIT 21; args=()
    <QuerySet [<Article: Django 教程_1>, <Article: Django 教程_2>, <Article: Django 教程_3>, <Article: Django 教程_4>, <Article: Django 教程_5>, <Article: Django 教程_6>, <Article: Django 教程_7>, <Article: Django 教程_8>, <Article: Django 教程_9>, <Article: Django 教程_10>, <Article: Django 教程_11>, <Article: Django 教程_12>, <Article: Django 教程_13>, <Article: Django 教程_14>, <Article: Django 教程_15>, <Article: Django 教程_16>, <Article: Django 教程_17>, <Article: Django 教程_18>, <Article: Django 教程_19>, <Article: Django 教程_20>, '...(remaining elements truncated)...']>

    In [14]: Article.objects.all().defer('content')
    Out[14]: (0.000) SELECT "blog_article"."id", "blog_article"."title", "blog_article"."author_id", "blog_article"."score" FROM "blog_article" LIMIT 21; args=()  # 注意这里没有查 content 字段了
    <QuerySet [<Article: Django 教程_1>, <Article: Django 教程_2>, <Article: Django 教程_3>, <Article: Django 教程_4>, <Article: Django 教程_5>, <Article: Django 教程_6>, <Article: Django 教程_7>, <Article: Django 教程_8>, <Article: Django 教程_9>, <Article: Django 教程_10>, <Article: Django 教程_11>, <Article: Django 教程_12>, <Article: Django 教程_13>, <Article: Django 教程_14>, <Article: Django 教程_15>, <Article: Django 教程_16>, <Article: Django 教程_17>, <Article: Django 教程_18>, <Article: Django 教程_19>, <Article: Django 教程_20>, '...(remaining elements truncated)...']>
    ```

    - only 仅选择需要的字段
    ```
    和 defer 相反，only 用于取出需要的字段，假如我们只需要查出 作者的名称

    In [15]: Author.objects.all().only('name')
    Out[15]: (0.000) SELECT "blog_author"."id", "blog_author"."name" FROM "blog_author" LIMIT 21; args=()
    <QuerySet [<Author: WeizhongTu>, <Author: twz915>, <Author: dachui>, <Author: zhe>, <Author: zhen>]>
    细心的同学会发现，我们让查 name ， id 也查了，这个 id 是 主键，能不能没有这个 id 呢？
    试一下原生的 SQL 查询

    In [26]: authors =  Author.objects.raw('select name from blog_author limit 1')

    In [27]: author = authors[0]
    (0.000) select name from blog_author limit 1; args=()
    ---------------------------------------------------------------------------
    InvalidQuery                              Traceback (most recent call last)
    <ipython-input-27-51c5f914fff2> in <module>()
    ----> 1author = authors[0]

    /usr/local/lib/python2.7/site-packages/django/db/models/query.pyc in __getitem__(self, k)
    1275 
    1276     def __getitem__(self, k):
    -> 1277         return list(self)[k]
    1278 
    1279     @property

    /usr/local/lib/python2.7/site-packages/django/db/models/query.pyc in __iter__(self)
    1250             if skip:
    1251                 if self.model._meta.pk.attname in skip:
    -> 1252                     raise InvalidQuery('Raw query must include the primary key')
    1253             model_cls = self.model
    1254             fields =[self.model_fields.get(c)for c in self.columns]

    InvalidQuery: Raw query must include the primary key
    报错信息说 非法查询，原生SQL查询必须包含 主键！

    再试试直接执行 SQL

    tu@pro ~/zqxt $ python manage.py dbshell
    SQLite version 3.14.0 2016-07-26 15:17:14
    Enter ".help" for usage hints.
    sqlite> select name from blog_author limit 1;
    WeizhongTu       <---  成功！！！
    虽然直接执行SQL语句可以这样，但是 django queryset 不允许这样做，一般也不需要关心，反正 only 一定会取出你指定了的字段。
    ```

    - 自定义聚合功能
    ```
    我们前面看到了 django.db.models 中有 Count, Avg, Sum 等，但是有一些没有的，比如 GROUP_CONCAT，它用来聚合时将符合某分组条件(group by)的不同的值，连到一起，作为整体返回。
    我们来演示一下，如果实现 GROUP_CONCAT 功能。
    新建一个文件 比如 my_aggregate.py
    
    from django.db.models import Aggregate, CharField
    
    
    class GroupConcat(Aggregate):
        function = 'GROUP_CONCAT'
        template = '%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)'
    
        def __init__(self, expression, distinct=False, ordering=None, separator=',', **extra):
            super(GroupConcat, self).__init__(
                expression,
                distinct='DISTINCT ' if distinct else '',
                ordering=' ORDER BY %s' % ordering if ordering is not None else '',
                separator=' SEPARATOR "%s"' % separator,
                output_field=CharField(),
                **extra        )
    代码来自：http://stackoverflow.com/a/40478702/2714931（我根据一个回复改写的增强版本）

    使用时先引入 GroupConcat 这个类，比如聚合后的错误日志记录有这些字段 time, level, info
    我们想把 level, info 一样的 聚到到一起，按时间和发生次数倒序排列，并含有每次日志发生的时间。
    ErrorLogModel.objects.values('level', 'info').annotate(
        count=Count(1), time=GroupConcat('time', ordering='time DESC', separator=' | ')
    ).order_by('-time', '-count')
    ```

## 数据库表迁移
- 第三方app South
1. Django 1.7中已集成了South的功能
2. 使用方法
    - 把south加入到settings.py中的INSTALL_APPS中
    ```
    # Application definition
    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    
        'blog',
        'south',
    )
    ```
    修改好后运行一次 python manage.py syncdb，Django会新建一个 south_migrationhistory 表，用来记录数据表更改(Migration)的历史纪录。
    
    - 如果要把之前建好的比如 blog 这个 app 使用 South 来管理：
    `$ python manage.py convert_to_south blog`你会发现blog文件夹中多了一个 migrations 目录，里面有一个 0001_initial.py 文件。
    注：如果 blog 这个 app 之前就创建过相关的表，可以用下面的来“假装”用 South 创建（伪创建，在改动 models.py 之前运行这个）
    `python manage.py migrate blog --fake`意思是这个表我以前已经建好了，用 South 只是纪一下这个创建记录，下次 migrate 的时候不必再创建了。
    原理就是 south_migrationhistory 中记录下了 models.py 的修改的历史，下次再修改时会和最近一次记录比较，发现改变了什么，然后生成相应的对应文件，最终执行相应的 SQL 更改原有的数据表。

    - 接着，当你对 Blog.models 做任何修改后，只要执行：
    `$ python manage.py schemamigration blog --auto`South就会帮助我们找出哪些地方做了修改，如果你新增的数据表没有给default值，并且没有设置null=True, south会问你一些问题，因为新增的column对于原来的旧的数据不能为Null的话就得有一个值。顺利的话，在migrations文件夹下会产生一个0002_add_mobile_column.py，但是这一步并没有真正修改数据库的表，我们需要执行 python manage.py migrate：
    ```
    $ python manage.py migrate
    Running migrations for blog:
    - Migrating forwards to 0002_add_mobile_column.
    > blog:0002_add_mobile_column
    - Loading initial data for blog.
    No fixtures found.
    ```
    这样所做的更改就写入到了数据库中了。

    - 恢复到以前
    South好处就是可以随时恢复到之前的一个版本，比如我们想要回到最开始的那个版本：
    ```
    > python manage.py migrate blog 0001
    - Soft matched migration 0001 to 0001_initial.
    Running migrations for blog:
    - Migrating backwards to just after 0001_initial.
    < blog:0002_add_mobile_column
    ```
    这样就搞定了，数据库就恢复到以前了，比你手动更改要方便太多了。

## Django 后台
- 其实就是admin管理窗口，只需要以下这三行代码，我们就可以拥有一个强大的后台
    ```
    from django.contrib import admin
    from .models import Article
    
    admin.site.register(Article)
    ```

- 如何兼容python2.x和python3.x
    ```
    # coding:utf-8
    from __future__ import unicode_literals
    
    from django.db import models
    from django.utils.encoding import python_2_unicode_compatible
    
    @python_2_unicode_compatible
    class Article(models.Model):
        title = models.CharField('标题', max_length=256)
        content = models.TextField('内容')
    
        pub_date = models.DateTimeField('发表时间', auto_now_add=True, editable = True)
        update_time = models.DateTimeField('更新时间',auto_now=True, null=True)
    
        def __str__(self):
            return self.title
    ```
    python_2_unicode_compatible 会自动做一些处理去适应python不同的版本，本例中的 unicode_literals 可以让python2.x 也像 python3 那样处理 unicode 字符，以便有更好地兼容性。

- 在列表显示与字段相关的其它内容
后台已经基本上做出来了，可是如果我们还需要显示一些其它的fields，如何做呢？
    ```
    from django.contrib import admin
    from .models import Article
    
    class ArticleAdmin(admin.ModelAdmin):
        list_display = ('title','pub_date','update_time',)
    
    admin.site.register(Article,ArticleAdmin)
    ```
    list_display 就是来配置要显示的字段的，当然也可以显示非字段内容，或者字段相关的内容，比如：
    ```
    class Person(models.Model):
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
    
        def my_property(self):
            return self.first_name + ' ' + self.last_name
        my_property.short_description = "Full name of the person"
    
        full_name = property(my_property)
    ```
    在admin.py中
    ```
    from django.contrib import admin
    from .models import Article, Person
 
 
    class ArticleAdmin(admin.ModelAdmin):
        list_display = ('title', 'pub_date', 'update_time',)
    
    
    class PersonAdmin(admin.ModelAdmin):
        list_display = ('full_name',)
    
    admin.site.register(Article, ArticleAdmin)
    admin.site.register(Person, PersonAdmin)
    ```

## Django表单
- 比如写一个计算 a和 b 之和的简单应用，网页上这么写
    ```
    <!DOCTYPE html>
    <html>
    <body>
    <p>请输入两个数字</p>
    
    
    <form action="/add/" method="get">
        a: <input type="text" name="a"> <br>
        b: <input type="text" name="b"> <br>
        
        <input type="submit" value="提交">
    </form>
    
    
    </body>
    </html>
    ```
    把这些代码保存成一个index.html，放在 templates 文件夹中。网页的值传到服务器是通过 `<input>` 或 `<textarea>`标签中的 name 属性来传递的，在服务器端这么接收：
    ```
    from django.http import HttpResponse
    from django.shortcuts import render
    
    def index(request):
        return render(request, 'index.html')
        
    def add(request):
        a = request.GET['a']
        b = request.GET['b']
        a = int(a)
        b = int(b)
        return HttpResponse(str(a+b))
    ```
    request.GET 可以看成一个字典，用GET方法传递的值都会保存到其中，可以用 request.GET.get('key', None)来取值，没有时不报错。再将函数和网址对应上，就可以访问了，详情参见源码。这样就完成了基本的功能，基本上可以用了。
    但是，比如用户输入的不是数字，而是字母，就出错了，还有就是提交后再回来已经输入的数据也会没了。当然如果我们手动将输入之后的数据在 views 中都获取到再传递到网页，这样是可行的，但是很不方便，所以 Django 提供了更简单易用的 forms 来解决验证等这一系列的问题。

- Django 表单（forms）
    ```
    新建一个 zqxt_form2 项目
    django-admin.py startproject zqxt_form2
    # 进入到 zqxt_form2 文件夹，新建一个 tools APP
    python manage.py startapp tools
    ```
    在tools文件夹中新建一个 forms.py 文件
    ```
    from django import forms
    
    class AddForm(forms.Form):
        a = forms.IntegerField()
        b = forms.IntegerField()
    ```
    我们的视图函数 views.py 中
    ```
    # coding:utf-8
    from django.shortcuts import render
    from django.http import HttpResponse
    
    # 引入我们创建的表单类
    from .forms import AddForm
    
    def index(request):
        if request.method == 'POST':# 当提交表单时
        
            form = AddForm(request.POST) # form 包含提交的数据
            
            if form.is_valid():# 如果提交的数据合法
                a = form.cleaned_data['a']
                b = form.cleaned_data['b']
                return HttpResponse(str(int(a) + int(b)))
        
        else:# 当正常访问时
            form = AddForm()
        return render(request, 'index.html', {'form': form})
    ```
    对应的模板文件 index.html
    ```
    <form method='post'>
    {% csrf_token %}
    {{ form }}
    <input type="submit" value="提交">
    </form>
    ```
    再在 urls.py 中对应写上这个函数
    ```
    from django.conf.urls import patterns, include, url
    
    from django.contrib import admin
    admin.autodiscover()
    
    urlpatterns = patterns('',
        # 注意下面这一行
        url(r'^$', 'tools.views.index', name='home'),
        url(r'^admin/', include(admin.site.urls)),
    )
    ```
    Django 的 forms 提供了：
    1. 模板中表单的渲染
    2. 数据的验证工作，某一些输入不合法也不会丢失已经输入的数据。
    3. 还可以定制更复杂的验证工作，如果提供了10个输入框，必须必须要输入其中两个以上，在 forms.py 中都很容易实现

    也有一些将 Django forms 渲染成 Bootstrap 的插件，也很好用，很方便。


## 模板
- 模板是一个文本，用于分离文档的表现形式和内容。 模板定义了占位符以及各种用于规范文档该如何显示的各部分基本逻辑（模板标签）。 模板通常用于产生HTML，但是Django的模板也能产生任何基于文本格式的文档。

- 在 Django 里写一个数据库驱动的 Web 应用的第一步是定义模型 - 也就是数据库结构设计和附加的其它元数据。

- 设计哲学：模型是真实数据的简单明确的描述。它包含了储存的数据所必要的字段和行为。Django 遵循 DRY Principle 。它的目标是你只需要定义数据模型，然后其它的杂七杂八代码你都不用关心，它们会自动从模型生成。

- 模型创建：通过模型创建信息，Django 可以：
    1. 为这个应用创建数据库 schema（生成 CREATE TABLE 语句）。
    2. 创建可以与 Question 和 Choice 对象进行交互的 Python 数据库 API。
    - 但是首先得把 polls 应用安装到我们的项目里。Django 应用是“可插拔”的。你可以在多个项目中使用同一个应用。除此之外，你还可以发布自己的应用，因为它们并不会被绑定到当前安装的 Django 上。
    - 为了在我们的工程中包含这个应用，我们需要在配置类 INSTALLED_APPS 中添加设置。因为 PollsConfig 类写在文件 polls/apps.py 中，所以它的点式路径是 'polls.apps.PollsConfig'。在文件 mysite/settings.py 中 INSTALLED_APPS 子项添加点式路径后，它看起来像这样：
        ```
            INSTALLED_APPS = [
                'polls.apps.PollsConfig',
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
                'django.contrib.staticfiles',
            ]
        ```

- python manage.py makemigrations polls
    - 你将会看到类似于下面这样的输出：

        ```
        Migrations for 'polls':
        polls/migrations/0001_initial.py:
            - Create model Choice
            - Create model Question
            - Add field question to choice
        ```

    - 通过运行 makemigrations 命令，Django 会检测你对模型文件的修改（在这种情况下，你已经取得了新的），并且把修改的部分储存为一次 迁移。

    - 迁移是 Django 对于模型定义（也就是你的数据库结构）的变化的储存形式 - 没那么玄乎，它们其实也只是一些你磁盘上的文件。如果你想的话，你可以阅读一下你模型的迁移数据，它被储存在 polls/migrations/0001_initial.py 里。别担心，你不需要每次都阅读迁移文件，但是它们被设计成人类可读的形式，这是为了便于你手动修改它们。

    - Django 有一个自动执行数据库迁移并同步管理你的数据库结构的命令 - 这个命令是 migrate。

    - python manage.py check ;这个命令帮助你检查项目中的问题，并且在检查过程中不会对数据库进行任何操作。

    - 改变模型需要这三步：
        1. 编辑 models.py 文件，改变模型。
        2. 运行 python manage.py makemigrations 为模型的改变生成迁移文件。
        3. 运行 python manage.py migrate 来应用数据库迁移。



- 页面的设计若写死在视图函数的代码里，如果你想改变页面的样子，你需要编辑 Python 代码。让我们使用 Django 的模板系统，只要创建一个视图，就可以将页面的设计从代码中分离出来。

- 首先，在你的 polls 目录里创建一个 templates 目录。Django 将会在这个目录里查找模板文件。

- 你项目的 TEMPLATES 配置项描述了 Django 如何载入和渲染模板。默认的设置文件设置了 DjangoTemplates 后端，并将 APP_DIRS 设置成了 True。这一选项将会让 DjangoTemplates 在每个 INSTALLED_APPS 文件夹中寻找 "templates" 子目录。这就是为什么尽管我们没有像在第二部分中那样修改 DIRS 设置，Django 也能正确找到 polls 的模板位置的原因。

- 模板命名空间

    虽然我们现在可以将模板文件直接放在 polls/templates 文件夹中（而不是再建立一个 polls 子文件夹），但是这样做不太好。Django 将会选择第一个匹配的模板文件，如果你有一个模板文件正好和另一个应用中的某个模板文件重名，Django 没有办法 区分 它们。我们需要帮助 Django 选择正确的模板，最简单的方法就是把他们放入各自的 命名空间 中，也就是把这些模板放入一个和 自身 应用重名的子文件夹里

- 「载入模板，填充上下文，再返回由它生成的 HttpResponse 对象」是一个非常常用的操作流程。于是 Django 提供了一个快捷函数，render()

- 模板系统统一使用点符号来访问变量的属性

- 模板标签
    - {% static %} 模板标签会生成静态文件的绝对路径
    - 一般的变量之类的用 {{ }}（变量），功能类的，比如循环，条件判断是用 {%  %}（标签）

        - 显示一个基本的字符串在网页上
        ```
        views.py
        # -*- coding: utf-8 -*-
        from django.shortcuts import render

        def home(request):
            string u = u'i am haibin'
            return render(request, 'home.html', {'string': string})
        
        home.html:
        {{ string }}
        ```
        - 基本的 for 循环 和 List内容的显示
        ```
        views.py
        def home(request):
            TutorialList = ["HTML", "CSS", "jQuery", "Python", "Django"]
            return render(request, 'home.html', {'TutorialList': TutorialList})

        home.html
        教程列表：
        {% for i in TutorialList %}
        {{ i }}
        {% endfor %}
        ```
        - 显示字典中内容, 在模板中取字典的键是用点info_dict.site，而不是Python中的 info_dict['site']，效果如下：

        ```
        views.py
        def home(request):
            info_dict = {'site': u'自强学堂', 'content': u'各种IT技术教程'}
            return render(request, 'home.html', {'info_dict': info_dict})

        home.html
        站点：{{ info_dict.site }} 内容：{{ info_dict.content }}
        还可以这样遍历字典：
        {% for key, value in info_dict.items %}
            {{ key }}: {{ value }}
        {% endfor %}
        ```
        - 在模板进行 条件判断和 for 循环的详细操作
        ```
        views.py
        def home(request):
            List = map(str, range(100))# 一个长度为100的 List
            return render(request, 'home.html', {'List': List})
        
        home.html
        {% for item in List %}
            {{ item }}{% if not forloop.last %},{% endif %} 
        {% endfor %}
        ```
        - for循环：
        ```
        变量                      描述
        forloop.counter        索引从 1 开始算
        forloop.counter0       索引从 0 开始算
        forloop.revcounter     索引从最大长度到 1
        forloop.revcounter0    索引从最大长度到 0
        forloop.first          当遍历的元素为第一项时为真
        forloop.last           当遍历的元素为最后一项时为真
        forloop.parentloop     用在嵌套的 for 循环中，获取上一层 for 循环的forloop
        ```
        - 当列表中可能为空值时用for empty
        ```
        <ul>
        {% for athlete in athlete_list %}
            <li>{{ athlete.name }}</li>
        {% empty %}
            <li>抱歉，列表为空</li>
        {% endfor %}
        </ul>
        ```
        - 模板上得到视图对应的网址
        ```
        # views.py
        def add(request, a, b):
            c = int(a) + int(b)
            return HttpResponse(str(c))
        
        # urls.py
        urlpatterns = patterns('',
            url(r'^add/(\d+)/(\d+)/$', 'app.views.add', name='add'),
        )

        # template html
        {% url 'add' 4 5 %}
        ```
        - 可以使用 as 语句将内容取别名（相当于定义一个变量），多次使用（但视图名称到网址转换只进行了一次）
        ```
        {% url 'some-url-name' arg arg2 as the_url %}
        <a href="{{ the_url }}">链接到：{{ the_url }}</a>
        ```
        - 模板中的逻辑操作
            - ==, !=, >=, <=, >, < 这些比较都可以在模板中使用,比较符号前后必须有至少一个空格
            ```
            {% if var >= 90 %}
            成绩优秀，自强学堂你没少去吧！学得不错
            {% elif var >= 80 %}
            成绩良好
            {% elif var >= 70 %}
            成绩一般
            {% elif var >= 60 %}
            需要努力
            {% else %}
            不及格啊，大哥！多去自强学堂学习啊！
            {% endif %}
            ```
            - and, or, not, in, not in
            ```
            {% if num <= 100 and num >= 0 %}
            num在0到100之间
            {% else %}
            数值不在范围之内！
            {% endif %}
            ```
        - 模板中 获取当前网址，当前用户等
        `{{ request.user }}`, `{{ request.path }}`,`{{ request.GET.urlencode }}`

## 
## Django管理页面
- python manage.py createsuperuser 创建管理员用户
- 向管理页面中加入投票应用
    - 但是我们的投票应用在哪呢？它没在索引页面里显示。
只需要做一件事：我们得告诉管理页面，问题 Question 对象需要被管理。打开 polls/admin.py 文件，把它编辑成下面这样：
        ```
        polls/admin.py

        from django.contrib import admin

        from .models import Question

        admin.site.register(Question)
        ```







