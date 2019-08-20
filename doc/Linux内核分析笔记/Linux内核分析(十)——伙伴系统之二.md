# Linux内核分析(十)——伙伴系统之二

## 10.1 分配页

### 1. 分配接口

- 页分配器提供了以下分配页的接口：

  > 1. `alloc_pages(gfp_mask, order)`请求分配一个阶数位order的页块，返回一个page实例。
  > 2. `alloc_page(gfp_mask)`是函数`alloc_pages()`在阶数为0的情况下的简化形式，只分配一页。
  > 3. `__get_free_pages(gfp_mask, order)`对函数`alloc_pages()`做了封装，只能从低端内存区域分配页，并且返回虚拟地址。
  > 4. `__get_free_pages(gfp_mask)`是函数`__get_free_pages()`在阶数为0情况下的简化形式，只分配一页。
  > 5. `get_zeroed_page(gfp_mask)`是函数`__get_free_pages()`在位参数`gfp_mask`设置了标志位`__GFP_ZERO`且阶数为0情况下的简化形式，只分配一页，并用0初始化。

### 2. 分配标志位

- 分配页的函数都带一个分配标志位参数，分配标志位分为以下5类（标志位名称中的GFP是`Get Free Pages`的缩写）。

- 区域修饰符：指定从哪个区域类型分配页，我们在上一章节《伙伴系统之一》中已经描述了根据分配标志得到首选区域类型的方法。

  > `__GFP_DMA`: 从DMA区域分配页。
  >
  > `__GFP_HIGHMEM`: 从高端内存区域分配页。
  >
  > `__GFP_DMA32`: 从DMA32区域分配页。
  >
  > `__GFP_MOVABLE`: 从可移动区域分配页。

- 页移动性和位置提示：指定页的迁移类型和从哪些内存节点分配页。

  > `__GFP_MOVABLE`: 申请可移动页，也是区域修饰符。
  >
  > `__GFP_RECLAIMABLE`: 申请可回收页。
  >
  > `__GFP_WRITE`: 指明调用者打算写物理页。只要有可能，把这些页分布到本地节点的所有区域，避免所有脏页在一个内存区域。
  >
  > `__GFP_HARDWALL`: 实施`cpuset`内存分配策略。`cpuset`是控制组（`cgroup`）的一个子系统，提供了把处理器和内存节点的集合分配给一组进程的机制，即允许进程在哪些处理器上运行和从哪些内存节点申请页。
  >
  > `__GFP_THISNODE`: 强制从指定节点分配页。
  >
  > `__GFP_ACCOUNT`: 把分配的页记账到内核内存控制组。

- 水线修饰符

  > `__GFP_HIGH`: 指明调用者是高优先级的，为了使系统能向前推进，必须准许这个请求。例如，创建一个I/O上下文，把脏页回写到存储设备。
  >
  > `__GFP_ATOMIC`: 指明调用者是高优先级的，不能回收页或者睡眠。典型的例子是中断处理程序。
  >
  > `__GFP_MEMALLOC`: 允许访问所有内存。只能在调用者承若“给我少量紧急保留内存使用，我可以释放更多的内存”的时候使用。
  >
  > `__GFP_NOMEMALLOC`: 禁止访问紧急保留内存，如果这个标志位和`__GFP_MEMALLOC`同时设置，优先级比后者高。

- 回收修饰符

  > `__GFP_IO`: 允许使用写存储设备。 
  >
  > `__GFP_FS`: 允许向下调用到底层文件系统。当文件系统申请页的时候，如果内存严重不足，直接回收页，把脏页回写到存储设备，调用文件系统的函数，可能导致死锁，为了避免死锁，文件系统申请页的时候应该清除这个标志位。
  >
  > `__GFP_DIRECT_RECLAIM`: 调用者可以直接回收页。
  >
  > `__GFP_KSWAPD_RECLAIM`: 当空闲页数达到低水线的时候，调用者想要唤醒页回收线程`kswapd`，即异步回收页。
  >
  > `__GFP_RECLAIM`: 允许直接回收页和异步回收页。
  >
  > `__GFP_REPEAT`: 允许重试，重试多次以后放弃，分配可能失败。
  >
  > `__GFP_NOFAIL`: 必须无限次重试，因为调用者不能处理分配失败。
  >
  > `__GFP_NORETRY`: 不要重试，当直接回收页和内存碎片整理不能使分配成功的时候，应该放弃。

- 行动修饰符

  >`__GFP_COLD`: 调用者不期望分配的页很快被使用，尽可能分配缓存冷页（数据不在处理器的缓存中）。
  >
  >`__GFP_NOWARN`: 如果分配失败，不要打印警告信息。
  >
  >`__GFP_COMP`: 把分配的页块组成复合页（`compound page`）。
  >
  >`__GFP_ZERO`: 把页用零初始化。 



### 3. 组合标志位 

- 因为标志位总是组合使用，所以内核定义了一些标志位组合。常用的标志位组合有如下几种。

- `GFP_ATOMIC`: 原子分配，分配内核使用的页，不能睡眠，调用者是高优先级的，允许异步回收页。

  ```c
  #define GFP_ATOMIC	(__GFP_HIGH|__GFP_ATOMIC|__GFP_KSWAPD_RECLAIM)
  
  ```

- `GFP_KERNEL`: 分配内核使用的页，可能睡眠。从低端内存区域分配页，允许异步回收页和直接回收页，允许读写存储设备，允许调用到底层文件系统。

  ```c
  #define GFP_KERNEL	(__GFP_RECLAIM | __GFP_IO | __GFP_FS)
  
  ```

- `GFP_NOWAIT`: 分配内核使用的页，不能等待。允许异步回收页，不允许直接回收页，不允许读写存储设备，不允许调用到底层文件系统。

  ```c
  #define GFP_NOWAIT	(__GFP_KSWAPD_RECLAIM)
  
  ```

- `GFP_NOIO`: 不允许读写存储设备，允许异步回收页和直接回收页。请尽量避免直接使用这个标志位，应该使用函数`memalloc_noio_save`和`memalloc_noio_restore`标记一个不能读写存储设备的范围，前者设置进程标志位`PF_MEMALLOC_NOIO`，后者清除进程标志位`PF_MEMALLOC_NOIO`。

  ```c
  #define GFP_NOIO	(__GFP_RECLAIM)
  
  ```

- `GFP_NOFS`: 不允许调用到底层文件系统，允许异步回收页和直接回收页，允许读写存储设备。请尽量避免使用这个标志位，应该使用函数`memalloc_nofs_save`和`memalloc_nofs_restore`标记一个不能调用到文件系统的范围，前者设置进程标志位`PF_MEMALLOC_NOFS`，后者清除进程标志位`PF_MEMALLOC_NOFS`。

  ```c
  #define GFP_NOFS	(__GFP_RECLAIM | __GFP_IO)
  
  ```

- `GFP_USER`: 分配用户空间使用的页，内核或硬件页可以直接访问，从普通区域分配，允许异步回收页和直接回收页，允许读写存储设备，允许调用到文件系统，允许实施`cpuset`内存分配策略。

  ```c
  #define GFP_USER	(__GFP_RECLAIM | __GFP_IO | __GFP_FS | __GFP_HARDWALL)
  
  ```

- `GFP_HIGHUSER`: 分配用户空间使用的页，内核不需要直接访问，从高端内存区域分配，物理页在使用的过程中不可移动。

  ```c
  #define GFP_HIGHUSER	(GFP_USER | __GFP_HIGHMEM)
  
  ```

- `GFP_HIGHUSER_MOVABLE`: 分配用户空间使用的页，内核不需要直接访问，物理页可以通过页回收或页迁移技术移动。

  ```c
  #define GFP_HIGHUSER_MOVABLE	(GFP_HIGHUSER | __GFP_MOVABLE)
  
  ```

- `GFP_TRANSHUGE_LIGHT`: 分配用户空间使用的巨型页，把分配的页块组成复合页，禁止使用紧急保留内存，禁止打印警告信息，不允许异步回收页和直接回收页。

  ```c
  #define GFP_TRANSHUGE_LIGHT	((GFP_HIGHUSER_MOVABLE | __GFP_COMP | \
    			 __GFP_NOMEMALLOC | __GFP_NOWARN) & ~__GFP_RECLAIM)
  
  ```

- `GFP_TRANSHUGE`: 分配用户空间使用的巨型页，和`GFP_TRANSHUGE_LIGHT`的区别是允许直接回收页。

  ```c
  #define GFP_TRANSHUGE	(GFP_TRANSHUGE_LIGHT | __GFP_DIRECT_RECLAIM)
  
  ```



### 4. 复合页

- 如果设置了标志位`__GFP_COMP`并且分配了一个阶数大于0的页块，页分配器会把页块组成复合页（compound page）。复合页最常见的用处是创建巨型页。

- 复合页的第一页叫首页（`head page`），其他页都叫尾页（`tail page`）。

  > 1.  首页设置标志`PG_head`。
  > 2.  第一个尾页的成员`compound_mapcount`表示复合页的映射计数，即多少个虚拟页映射到这个物理页，初始值是 -1。这个成员和成员`mapping`组成一个联合体，占用相同的位置，其他尾页把成员`mapping`设置为一个有毒的地址。
  > 3.  第一个尾页的成员`compound_dtor`存放复合页释放函数数组的索引，成员`compound_order`存放复合页的阶数 n。这两个成员和成员`lrn.prev`占用相同的位置。
  > 4.  所有尾页的成员`compound_head`存放首页的地址，并且把最低位设置为 1。这个成员和成员`lrn.next`占用相同的位置。

- 判断一个页是复合页的成员的方法是： 页设置了标志位`PG_head`（针对首页），或者页的成员`compound_head`的最低位是1（针对尾页）。

- 结构体page中复合页的成员如下：

  ```c
  /* linux-4.14/include/linux/mm_types.h */
  
  42  struct page {
44  	unsigned long flags;
  46  	union {
  47  		struct address_space *mapping;	
  54  		void *s_mem;			
  55  		atomic_t compound_mapcount;	/* 映射计数，第一个尾页 */
  56  		/* page_deferred_list().next	 -- 第二个尾页 */
  57  	};
  		...
  116  	union {
  117  		struct list_head lru;
              ...
              /* 复合页的尾页 */
  142  		struct {
  143  			unsigned long compound_head; /* 首页的地址，并且设置最低位 */
  144  
  145  			/* 第一个尾页 */
  146  #ifdef CONFIG_64BIT
  153  			unsigned int compound_dtor; /* 复合页释放函数数组的索引 */
  154  			unsigned int compound_order; /* 复合页的阶数 */
  155  #else
  156  			unsigned short int compound_dtor;
  157  			unsigned short int compound_order;
  158  #endif
  159  		};
  170  	};
      	...
  213  }
  
  ```



### 5. 对高阶原子分配的优化处理

- 高阶原子分配：阶数大于0，并且调用者设置了分配标志位`__GFP_ATOMIC`，要求不能睡眠。

- 也分配器对高阶原子分配做了优化处理，增加了高阶原子类型（`MIGRATE_HIGHATOMIC`），在内存区域的结构体中增加1个成员`nr_reserved_highatomic`，用来记录高阶原子类型的总页数，并且限制其数量：

  `zone->nr_reserved_highatomic < (zone->managed_pages/100)+pageblock_nr_pages`，即必须小于（伙伴分配器管理的总页数/100 + 分组阶数对应的页数）。

  ```c
  [linux-4.14/include/linux/mmzone.h]
  
  359  struct zone {
  	 	...
  365  	unsigned long nr_reserved_highatomic;
  		...
  509  } ____cacheline_internodealigned_in_smp;
  
  ```

- 执行高阶原子分配时，先从高阶原子类型分配页，如果分配失败，从调用者指定的迁移类型分配页。分配成功以后，如果内存区域中高阶原子类型的总页数小于限制，并且页块的迁移类型不是高阶原子类型、隔离类型和CMA迁移类型，那么把页块的迁移类型转换位高阶原子类型，并且把页块中没有分配出去的页移到高阶原子类型的空闲链表中。

- 当内存严重不足时，直接回收页以后仍然分配失败，针对高阶原子类型的页数超过`pageblock_nr_pages`的目标区域，把高阶原子类型的页块转换成申请的迁移类型，然后重试分配，其代码如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  3594  static inline struct page *
  3595  __alloc_pages_direct_reclaim(gfp_t gfp_mask, unsigned int order,
  3596  		unsigned int alloc_flags, const struct alloc_context *ac,
  3597  		unsigned long *did_some_progress)
  3598  {
  3599  	struct page *page = NULL;
  3600  	bool drained = false;
  3601  
  3602  	*did_some_progress = __perform_reclaim(gfp_mask, order, ac); /* 直接回收页 */
  3603  	if (unlikely(!(*did_some_progress)))
  3604  		return NULL;
  3605  
  3606  retry:
  3607  	page = get_page_from_freelist(gfp_mask, order, alloc_flags, ac);
  3608  
  3609  	/*
  3610  	 * If an allocation failed after direct reclaim, it could be because
  3611  	 * pages are pinned on the per-cpu lists or in high alloc reserves.
  3612  	 * Shrink them them and try again
  3613  	 */
  3614  	if (!page && !drained) {
      		/* 把高阶原子类型的页块转换成申请的迁移类型 */
  3615  		unreserve_highatomic_pageblock(ac, false);
  3616  		drain_all_pages(NULL);
  3617  		drained = true;
  3618  		goto retry;
  3619  	}
  3620  
  3621  	return page;
  3622  }
  
  ```

- 如果直接回收页没有进展超过16次，那么针对目标区域，不再为高阶原子分配保留页，把高阶原子类型的页块转换成申请的迁移类型，其代码如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  3728  static inline bool
  3729  should_reclaim_retry(gfp_t gfp_mask, unsigned order,
  3730  		     struct alloc_context *ac, int alloc_flags,
  3731  		     bool did_some_progress, int *no_progress_loops)
  3732  {
  		...
  3741  	if (did_some_progress && order <= PAGE_ALLOC_COSTLY_ORDER)
  3742  		*no_progress_loops = 0;
  3743  	else
  3744  		(*no_progress_loops)++;
  3745  
  3746  	/*
  3747  	 * Make sure we converge to OOM if we cannot make any progress
  3748  	 * several times in the row.
  3749  	 */
  3750  	if (*no_progress_loops > MAX_RECLAIM_RETRIES) {
  3751  		/* Before OOM, exhaust highatomic_reserve 在调用内存耗尽之前，用完为高阶原子分配保留的页*/
  3752  		return unreserve_highatomic_pageblock(ac, true);
  3753  	}
  		...
  3817  }
  
  ```



## 10.2 核心函数的实现

