# 持久化 - pickle
- 序列化（持久化，落地）：把程序运行中的信息保存到磁盘上
- 反序列化： 序列化的逆过程
- pickle：python提供的的序列化模块
- pickle.dump: 序列化
- pickle.load: 反序列化

# 持久化 - shelve
- 持久化工具
- 类似字典，用key-value对保存数据，存取方式跟字典也类似
- open， close
# shelve 特性
- 不支持多个应用并行写入
    - 为了解决这个问题，open的时候可以使用flag=r
- 写回问题
    - shelve写会情况下不会等待持久化对象进行任何修改
    - 解决方法：强制写回：writeback=True

# 多线程
- python2： thread， python3：_thread
- threading: 通行的包
- 守护线程：如果将线程设置为守护线程，守护线程会在主线程结束时自动退出
    - 一般认为守护线程不重要或者不允许离开主线程独立运行
- 共享变量
    - 共享变量： 当多个线程同时访问一个变量的时候，会产生共享变量的问题
    - 解决方法：锁，信号灯
    - 锁（Lock） threading.Lock()
- 线程安全问题：
    - 如果一个资源/变量，它对于多线程来讲，不用加锁也不会引起任何问题，则称为线程安全
    - 线程不安全变量类型： list， set， dict
    - 线程安全变量类型： queue
- 死锁问题
- 锁的等待时间问题
- semphore
- threading.Timer
    - Timer是利用多线程，在指定时间后启动一个功能
- 可重入锁
    - 一个锁，可以被一个线程多次申请
    - 主要解决递归调用的时候，需要申请锁的情况

# 线程替代方案
- subprocess
    - 完全跳过线程，使用进程
    - 是派生进程的主要替代方案
- multiprocessiong
- concurrent.futures
    - 新的异步执行模块
    - 任务级别的操作

# 多进程
- 进程间通信（IPC）
- 进程之间无任何共享状态
- 进程的创建

# 迭代
- 可迭代
- 迭代器
- 使用isinstance判断

# 生成器
- generator： 一边循环一边计算下一个元素的机制/算法
- 需满足三个条件：
    - 每次调用都生产出for循环的下一个元素
    - 如果达到最后一个后，爆出stopiteration异常
    - 可以被next函数调用
- 如何生成一个生成器
    - 直接使用
    - 如果函数中包含yield，则这个函数就叫生成器
    - next调用函数，遇到yield返回

# 协程
- 协程是为非抢占式多任务产生子程序的计算机组件，协程允许不同入口点在不同位置暂停或开始执行程序
- 从技术角度讲，协程就是一个你可以暂停执行的函数，或者可以直接理解为生成器
- 协程的实现：
    - yield返回
    - send调用
- 协程的四个状态
- 协程终止
    - 协程中未被处理的一场会向上冒泡，传给next函数或send方法的调用方（即触发协程的对象）
    - 止协程的一种方式：发送某个哨符值，让协程退出。内置的None和Elliosis等常量经常用作哨符值==
- yield from
    - 调用协程为了得到返回值，协程必须正常终止
    - 生成器正常终止会发出StopIteration异常，异常对象的value属性保存返回值
    - yield from从内部捕获Stop Iteration异常

# asyncio
- asyncio 本身是一个消息循环
- 步骤：
    - 创建消息循环
    - 把协程导入
    - 关闭

# async and await
- 为了更好的表示异步io
- 让协程代码更简洁
- 在使用上，可以简单的进行替换

# aiohttp
- asyncio 实现单线程的并发io，在客户端用处不大
- 在服务器端可以asyncio+coroutine配合，因为HTTP是io操作
- asyncio实现了tcp，udp，ssl等协议
- aiohttp是给与asyncio实现HTTP框架

# concurrent.futures
- 类似其他语言的线程池概念
- 利用multiprocessiong实现真正的并行计算

# current中map函数
- map(fn, \*iterables, timeout=None)
    - 类似map函数
    - 函数需要异步执行
    - map 与submit使用一个就行

# Future

# 结构化文件存储
- xml，可扩展标记语言，描述的是数据本身，即数据的结构和语义
- 根元素（一个文件内只有一个根元素）
    - 在整个xml文件中，可以将其看作一个树形结构
    - 根元素有且只有一个
- 子元素
- 属性
- 内容
    - 表明标签所存储的信息
- 注释
    - 起到说明作用的信息
    - 注释不能嵌套在标签里
    - 只有在注释的开始和结尾使用双短横线
    - 三短横线只能出现在注释的开头而不能用在结尾
- 保留字符的处理
    - xml中使用的符号可能与实际符号相冲突，典型的就是左右尖括号
    - 使用实体引用来表示保留字符
    - 把含有保留字符的部分放在CDATA块内部，CDATA块把内部信息视为不需要转义
    - 常用的需要转义的保留字符和对应的实体引用
        - &: &amp;
        - <: &lt;
        - >: &gt;
        - ': &apos;
        - ": &quot;
        - 一共5个，每个实体引用都以&开头;结尾
- 标签命名规则
    - Pascal命名法
    - 用单词表示，第一个字母大写

- 命名空间
    - 为了防止命名冲突，在每一个冲突元素上添加命名空间
    - xmlns
## 读取
- xml读取主要分两个主要技术：SAX, DOM
- SAX （simple API for XML）:
    - 基于事件驱动的API
    - 利用SAX解析文档设计到解析器和事件处理两部分
    - 特点： 快；流式读取
- DOM
    - 是W3C规定的XML编程接口
    - 一个XML文件在缓存中以树形结构保存，读取
    - 用途：
        - 定位浏览XML任何一个节点信息
        - 添加删除相应内容
    - minidom
    - etree
- xml 文件写入
    - 更改
        - ele.set: 修改属性
        - ele.appent: 添加子元素
        - ele.remove: 删除元素
    - 生成创建
        - SubElement
        - minidom
        - etree创建
# json
- 在线工具
- JSON(JavaScriptObiectNotation)
- 轻量级的数据交换格式，基于ECMAScript
- json格式是一个键值对形式的数据集
    - key：字符串
    - value：字符串，数字，列表，json
    - json使用大括号包裹
    - 键值对直接用逗号隔开
- json和python格式的对应
    - 字符串：字符串
    - 数字：数字
    - 队列：list
    - 对象：dict
    - 布尔值：布尔值
- python for json
    - json包
    - json和python对象的转换
        - json.dumps()：对数据编码，把python格式表示成json格式
        - json.loads()：对数据解码，把json格式转化成python格式
    - python读取json文件
        - json.dump()：把内容写入文件
        - json.load()：把json文件内容读入python

# 正则表达式(RegularExpression，re)
- 为了解决不同设备之间信息交换

# XPath
- 在XML文件中查找信息的一套规则/语言，根据XML的元素或者属性进行遍历
- XPath 开发工具
    - 开源的XPath表达式编辑工具：XMLQuire
    - Chrome插件：XPath Helper
    - Firefox插件： XPath Checker

# 网络编程
- 网络
- 网络协议
- 网络模型：
    - 理论模型-七层
        - 物理层
        - 数据链路层
        - 网络层
        - 传输层
        - 会话层
        - 表示层
        - 应用层
    - 实际模型-四层
        - 链路层
        - 网络层
        - 传输层
        - 应用层
- 每一层都有相应的协议负责交换信息或者协同工作
- TCP/IP 协议族
- IP地址：负责在网络上唯一定位一个机器
    - IP地址
    - 由四个数字段组成，每个数字段的取值[0-255]
    - 192.168.xxx.xxx: 局域网ip
    - 127.0.0.1：本机ip
    - IPv4，IPv6
- 端口
    - 范围： 0-65535
    - 知名端口：0-1023
    - 非知名端口：1024-~

# TCP/UDP协议
- UDP：非安全的不面向链接的传输
    - 安全性差
    - 大小限制64kb
    - 没有顺序
    - 速度快

- TCP：基于链接的通信
    - 安全
    -速度慢

- SOCKET编程
    - socket（套接字）：是一个网络通信的端点，能实现不同主机的进程通信。
    - 通过IP+端口定位对方并发送消息的通信机制
    - 分为UDP和TCP

- UDP编程
    - Server端流程
        - 1. 建立socket，socket是负责具体通信的一个实例
        - 2. 绑定，为创建的socket指派固定的端口和ip地址
        - 3. 接受对方发送的内容
        - 4. 给对方发送反馈，此步骤为非必须步骤 
    - Client端流程
        - 1. 建立通信的socket
        - 2. 发送内容到指定服务器
        - 3. 接受服务器给定的反馈内容

- TCP编程
    - 面向链接的传输，即每次传输之前需要先建立一个链接
    - 客户端和服务器端两个程序需要编写
    - Server端的编写流程
        - 1. 建立socket负责具体通信，这个socket其实只负责接受对方的请求
        - 2. 绑定端口和地址
        - 3. 监听接入的访问socket
        - 4. 接受访问的socket，可以理解接受访问即建立了一个通讯的链接通路
        - 5. 接受对方发送的内容，利用接收到的socket接收内容
        - 6. 如果有必要，给对方发送反馈信息
        - 7. 关闭链接通路
    - Client端流程
        - 1. 建立通信socket
        - 2. 链接对方，请求跟对方建立通路
        - 3. 发送内容到对方服务器
        - 4. 接受对方的反馈
        - 5. 关闭链接通路

# FTP编程
- FTP（FileTransferProtocal）文件传输协议
- 用途： 定制一些特殊的上传下载文件的服务
- 用户分类：登录FTP服务器必须有一个账号
    - Real账户：注册账户
    - Guest账户：可能临时对某一类人的行为进行授权
    - Anonymous账户：匿名账户，允许任何人
- FTP工作流程
    - 1. 客户端链接远程主机上ftp服务器
    - 2. 客户端输入用户名和密码（或者“anonymous”和电子邮件地址）
    - 3. 客户端和服务器进行各种文件传输和信息查询操作
    - 4. 客户端从远程ftp服务器退出，结束传输
- FTP文件表示
    - 分三段表示ftp服务器上的文件
    - HOST：主机地址，类似于ftp.mozilla.org，以ftp开头
    - DIR: 目录，表示文件所在本地的路径，例如 pub/android/focus/1.1-file
    - File：文件名称， 例如 a.apk
    - 如果想完整精确表示ftp上某一个文件，需要以上三部分组合在一起

# Mail编程

# 网络爬虫
## urllib
- 包含模块
    - urllib.request:打开和读取urls
    - urllib.error: 包含urllib.request产生的常见的错误，使用try捕获
    - urllib.parse：包含解析url的方法
    - urllib.rebotparse: 解析robots.txt文件
- 网页编码问题解决
    - chardet：可以自动检测页面文件的编码格式，但是，可能有误
    - 需要安装
- urlopen 的返回对象
    - geturl：返回请求的url
    - info：请求反馈对象的meta信息
    - getcode：返回http code
- request.date 的使用
    - 访问网络的两种方法
        - get
            - 利用参数给服务器传递信息
            - 参数为dict，然后用parse编码
        - post
            - 一般向服务器传递参数使用
            - post把信息自动加密处理
            - 我们如果想使用post信息，需要用到data参数
            - 使用post，意味着Http的请求头可能需要更改
                - Content-Type：application/x-www.form-urlencode
                - Content-Length: 数据长度
                - 简而言之，一旦更改请求方法，请注意其他请求头部信息相适应
            - urllib.parse.urlencode可以将字符串自动转换成上面的
            - 为了更多的设置请求信息，单纯的通过urlopen已经不行，需要使用request.Request类

- urllib.error
    - URLError产生的原因：
        - 没网
        - 服务器链接失败
        - 不知道指定服务器
        - OSError子类
    - HTTPError，是URLError的一个子类
    - 两者区别：
        - HTTPError是对应的HTTP请求的返回码错误，如果返回错误码是400以上的，则引发HTTPError
        - URLError对应的一般是网络出现问题，包括url问题
- UserAgent 
    - 用户代理，简称UA，属于heads的一部分，服务器通过UA来判断访问者身份
    - 设置UA有两种方式
        - header
        - add_header

- ProxyHandler处理（代理服务器）
    - 使用代理IP，是爬虫的常用手段
    - 获取代理服务器地址：
        - www.xicidaili.com
        - www.goubanjia.com
    - 代理用来隐藏真实访问中，代理也不允许频繁访问某一个固定网站，所以，代理一定要很多很多
    - 基本使用步骤：
        - 设置代理地址
        - 创建ProxyHandler
        - 创建opener
        - 安装opener

- cookie & session
    - 由于HTTP协议的无记忆性，人们为了弥补这个缺憾，所采用的一个补充协议
    - cookie是发给用户（http浏览器）的一段信息，session是保存在服务器上的对应的另一半信息，用来记录用户信息

- cookie和session的区别
    - 存放位置不同
    - cookie不安全
    - session会保存在服务器上一定时间，会过期
    - 半个cookie保存数据不超过4K，很多浏览器限制一个站点最多保存20个
- session的存放位置
    - 存放服务器端
    - 一般情况，session是放在内存中或者数据库中
- 使用cookie登录
    - 直接把cookie复制下来，然后收到放入请求头
    - http模块包含一些关于cookie的模块，通过他们我们可以自动使用cookie
        - CookieJar
            - 管理存储cookie，想传出的http请求添加cookie
            - cookie存储在内存中，CookieJar实例回收后cookie将消失
        - FileCookieJar（filename， delayload=None，policy=None）
            - 使用文件管理cookie
            - filename是保存cookie的文件
        - MozillaCookieJar（filename， delayload=None，policy=None）
            - 创建与mocilla浏览器cookie.txt兼容的FileCookieJar实例
        - LwpCookieJar（filename， delayload=None，policy=None）
            - 创建于libwww-perl标准兼容的Set-Cookie3格式的FileCookieJar实例
    - 利用cookie登录流程
        - 打开登录页面后自动通过用户名密码登录
        - 自动提取反馈回来的cookie
        - 利用提取的cookie登录隐私页面
    
    - handler是Handler的实例，常用的有
        - 用来处理复杂请求
    
    - 创立handler后，使用opener打开，打开后相应的业务由相应的handler处理

- SSL
    - SSL证书就是指遵守SSL安全套阶层协议的服务器数字证书（SercureSocketLayer）
    - 美国网景公司开发
    - CA（CertificateAuthority）是数字证书认证中心，是发放，管理，废除数字证书的收信人的第三方机构
    - 遇到不信任的SSL证书，需要单独处理

- js加密
    - 有的反爬虫策略采用js对需要传输的数据进行加密处理（通常是取md5值）
    - 经过加密，传输的就是密文，但是
    - 加密函数或者过程一定是在浏览器上完成

- ajax
    - 异步请求
    - 一定会有url，请求方法，可能有数据
    - 一般使用json格式

# Requests
- HTTP for Humans，更简洁更友好
- 继承了urllib的所有特征
- 底层使用的是urllib3
- 开源地址：https://github.com/requests/requests
- 中文文档：http://docs.python-requests.org/zh_CN/latest/index.html
- 安装：conda install requests
- get请求
    - request.get(url)
    - requests.request("get", url)
    - 可以带有headers和parmas参数
- get返回

- post
    - rsp = requests.post(url, data=data)
- proxy
    - proxied = {
        "http": address of proxy,
        "https": address of proxy
    }

- 用户验证
    - 代理验证

- web客户端验证

- cookie
    - requests可以自动处理cookie信息

- session
    - 跟服务器端session不是一个东东
    - 模拟一次回话，从客户端浏览器链接服务器开始，到客户端浏览器断开
    - 能让我们跨请求时保持某些参数，比如在同一个session案例发出的，所有请求之间保持cookie

- https请求ssl证书
    - 参数verify负责表示是否需要验证ssl证书，默认是True
    - 如果不需要验证ssl证书，则设置为False表示关闭
