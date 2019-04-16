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

# python第三方库：
1. from collections import deque
    - 使用 deque(maxlen=N) 构造函数会新建一个固定大小的队列。当新的元素加入并且这个队列已满的时候,最老的元素会自动被移除掉。

2. import heapq
    - heapq 模块有两个函数:nlargest() 和 nsmallest() 可以完美解决"怎样从一个集合中获得最大或者最小的 N 个元素列表"的问题
        ```
        import heapq
        nums = [1, 8, 2, 23, 7, -4, 18, 23, 42, 37, 2]
        print(heapq.nlargest(3, nums)) # Prints [42, 37, 23]
        print(heapq.nsmallest(3, nums)) # Prints [-4, 1, 2]
        ```
    - heapq 模块实现了一个简单的优先级队列
        ```
        import heapq
        class PriorityQueue:
            def __init__(self):
                self._queue = []
                self._index = 0
            
            def push(self, item, priority):
                heapq.heappush(self._queue, (-priority, self._index, item))
                self._index += 1
            
            def pop(self):
                return heapq.heappop(self._queue)[-1]
        
        class Item:
            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return 'Item({!r})'.format(self.name)
        
        >>> q = PriorityQueue()
        >>> q.push(Item('foo'), 1)
        >>> q.push(Item('bar'), 5)
        >>> q.push(Item('spam'), 4)
        >>> q.push(Item('grok'), 1)
        >>> q.pop()
        Item('bar')
        >>> q.pop()
        Item('spam')
        >>> q.pop()
        Item('foo')
        >>> q.pop()
        Item('grok')            
        ```
    
3. 字典中的键映射多个值
    - 一个字典就是一个键对应一个单值的映射。如果你想要一个键映射多个值,那么你就需要将这多个值放到另外的容器中,比如列表或者集合里面。
        ```
        d = {
            'a' : [1, 2, 3],
            'b' : [4, 5]
        }
        e = {
            'a': {1, 2, 3},
            'b': {4, 5}
        }
        ```
    - from collections import defaultdict, 可以使用 collections 模块中的 defaultdict 来构造这样的字典。defaultdict 的一个特征是它会自动初始化每个 key 刚开始对应的值,所以你只需要关注添加元素操作了。
        ```
        d = defaultdict(list)
        d['a'].append(1)
        d['a'].append(2)
        d['b'].append(4)

        d = defaultdict(set)
        d['a'].add(1)
        d['a'].add(2)
        d['b'].add(4)

        d = defaultdict(list)
        for key, value in pairs:
            d[key].append(value)
        ```

4. 字典排序
    - from collections import OrderedDict，　为 了 能 控 制 一 个 字 典 中 元 素 的 顺 序, 你 可 以 使 用 collections 模 块 中 的OrderedDict 类。在迭代操作的时候它会保持元素被插入时的顺序。当你想要构建一个将来需要序列化或编码成其他格式的映射的时候, OrderedDict是非常有用的。比如,你想精确控制以 JSON 编码后字段的顺序,你可以先使用OrderedDict 来构建这样的数据:
        ```
        def ordered_dict():
            d = OrderedDict()
            d['foo'] = 1
            d['bar'] = 2
            d['spam'] = 3
            d['grok'] = 4
            # Outputs "foo 1", "bar 2", "spam 3", "grok 4"
            for key in d:
                print(key, d[key])
        
        >>> import json
        >>> json.dumps(d)
        '{"foo": 1, "bar": 2, "spam": 3, "grok": 4}'
        ```
    - OrderedDict 内部维护着一个根据键插入顺序排序的双向链表。每次当一个新的元素插入进来的时候,它会被放到链表的尾部。对于一个已经存在的键的重复赋值不会改变键的顺序。需要注意的是,一个 OrderedDict 的大小是一个普通字典的两倍,因为它内部维护着另外一个链表。所以如果你要构建一个需要大量 OrderedDict 实例的数据结构的时候 (比如读取 100,000 行 CSV 数据到一个 OrderedDict 列表中去),那么你就得仔细权衡一下是否使用 OrderedDict 带来的好处要大过额外内存消耗的影响。

5. 在数据字典中执行一些计算操作 (比如求最小值、最大值、排序等等)
    - 为了对字典值执行计算操作,通常需要使用 zip() 函数先将键和值反转过来。
        ```
        prices = {
            'ACME': 45.23,
            'AAPL': 612.78,
            'IBM': 205.55,
            'HPQ': 37.20,
            'FB': 10.75
        }

        min_price = min(zip(prices.values(), prices.keys()))
        # min_price is (10.75, 'FB')
        max_price = max(zip(prices.values(), prices.keys()))
        # max_price is (612.78, 'AAPL')
        prices_sorted = sorted(zip(prices.values(), prices.keys()))
        # prices_sorted is [(10.75, 'FB'), (37.2, 'HPQ'),
        #                   (45.23, 'ACME'), (205.55, 'IBM'),
        #                   (612.78, 'AAPL')]
        ```
    - 执行这些计算的时候,需要注意的是 zip() 函数创建的是一个只能访问一次的迭代器。
        ```
        prices_and_names = zip(prices.values(), prices.keys())
        print(min(prices_and_names)) # OK
        print(max(prices_and_names)) # ValueError: max() arg is an empty sequence
        ```
    - 需要注意的是在计算操作中使用到了 (值,键) 对。当多个实体拥有相同的值的时候,键会决定返回结果。比如,在执行 min() 和 max() 操作的时候,如果恰巧最小或最大值有重复的,那么拥有最小或最大键的实体会返回:
        ```
        >>> prices = { 'AAA' : 45.23, 'ZZZ': 45.23 }
        >>> min(zip(prices.values(), prices.keys()))
        (45.23, 'AAA')
        >>> max(zip(prices.values(), prices.keys()))
        (45.23, 'ZZZ')
        ```
6. 在两个字典中寻找相同点 (比如相同的键、相同的值等等)
    - 为了寻找两个字典的相同点,可以简单的在两字典的 keys() 或者 items() 方法返回结果上执行集合操作。
        ```
        a = {
            'x' : 1,
            'y' : 2,
            'z' : 3
        }
        b = {
            'w' : 10,
            'x' : 11,
            'y' : 2
        }

        # Find keys in common
        a.keys() & b.keys() # { 'x', 'y' }
        # Find keys in a that are not in b
        a.keys() - b.keys() # { 'z' }
        # Find (key,value) pairs in common
        a.items() & b.items() # { ('y', 2) }
        
        ```