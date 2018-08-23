# Django 笔记
- python -m django --version 查看Django版本

- django-adimin startproject [projectname]: 创建项目

- python manage.py runserver：启动服务器
    - python manage.py runserver 8080：更改服务器端口，默认情况下为8000
    - python manage.py runserver 0.0.0.0:8000： ‘ 0.0.0.0 ’ 这个 IP 地址，告诉服务器去侦听任意的网络接口
    - 完成这些设置后，你本地网络中的其它计算机就可以在浏览器中访问你的 IP 地址了。比如：http://192.168.1.103:8000/

- python manage.py startapp polls：创建应用

## View
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

## 数据库配置
- mysite/settings.py 。这是个包含了 Django 项目设置的 Python 模块。

- 通常，这个配置文件使用 SQLite 作为默认数据库。如果你不熟悉数据库，或者只是想尝试下 Django，这是最简单的选择。Python 内置 SQLite，所以你无需安装额外东西来使用它。当你开始一个真正的项目时，你可能更倾向使用一个更具扩展性的数据库，例如 PostgreSQL，避免中途切换数据库这个令人头疼的问题。

- python manage.py migrate
    - 这个 migrate 命令检查 INSTALLED_APPS 设置，为其中的每个应用创建需要的数据表，至于具体会创建什么，这取决于你的 mysite/settings.py 设置文件和每个应用的数据库迁移文件（我们稍后会介绍这个）。这个命令所执行的每个迁移操作都会在终端中显示出来。如果你感兴趣的话，运行你数据库的命令行工具，并输入 \dt (PostgreSQL)， SHOW TABLES; (MySQL)， .schema (SQLite)或者 SELECT TABLE_NAME FROM USER_TABLES; (Oracle) 来看看 Django 到底创建了哪些表。

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

- python manage.py shell
    - 我们使用这个命令而不是简单的使用 "Python" 是因为 manage.py 会设置 DJANGO_SETTINGS_MODULE 环境变量，这个变量会让 Django 根据 mysite/settings.py 文件来设置 Python 包的导入路径。

- 页面的设计若写死在视图函数的代码里，如果你想改变页面的样子，你需要编辑 Python 代码。让我们使用 Django 的模板系统，只要创建一个视图，就可以将页面的设计从代码中分离出来。

- 首先，在你的 polls 目录里创建一个 templates 目录。Django 将会在这个目录里查找模板文件。

- 你项目的 TEMPLATES 配置项描述了 Django 如何载入和渲染模板。默认的设置文件设置了 DjangoTemplates 后端，并将 APP_DIRS 设置成了 True。这一选项将会让 DjangoTemplates 在每个 INSTALLED_APPS 文件夹中寻找 "templates" 子目录。这就是为什么尽管我们没有像在第二部分中那样修改 DIRS 设置，Django 也能正确找到 polls 的模板位置的原因。

- 模板命名空间

    虽然我们现在可以将模板文件直接放在 polls/templates 文件夹中（而不是再建立一个 polls 子文件夹），但是这样做不太好。Django 将会选择第一个匹配的模板文件，如果你有一个模板文件正好和另一个应用中的某个模板文件重名，Django 没有办法 区分 它们。我们需要帮助 Django 选择正确的模板，最简单的方法就是把他们放入各自的 命名空间 中，也就是把这些模板放入一个和 自身 应用重名的子文件夹里

- 「载入模板，填充上下文，再返回由它生成的 HttpResponse 对象」是一个非常常用的操作流程。于是 Django 提供了一个快捷函数，render()

- 模板系统统一使用点符号来访问变量的属性

- 模板标签
    - {% static %} 模板标签会生成静态文件的绝对路径

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







