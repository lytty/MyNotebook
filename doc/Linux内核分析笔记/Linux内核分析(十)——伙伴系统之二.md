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

- 页分配器对高阶原子分配做了优化处理，增加了高阶原子类型（`MIGRATE_HIGHATOMIC`），在内存区域的结构体中增加1个成员`nr_reserved_highatomic`，用来记录高阶原子类型的总页数，并且限制其数量：

  `zone->nr_reserved_highatomic < (zone->managed_pages/100)+pageblock_nr_pages`，即必须小于（伙伴分配器管理的总页数/100 + 分组阶数对应的页数）。

  ```c
  [linux-4.14/include/linux/mmzone.h]
  
  359  struct zone {
  	 	...
  365  	unsigned long nr_reserved_highatomic;
  		...
  509  } ____cacheline_internodealigned_in_smp;
  
  ```

- 执行高阶原子分配时，先从高阶原子类型分配页，如果分配失败，从调用者指定的迁移类型分配页。分配成功以后，如果内存区域中高阶原子类型的总页数小于限制，并且页块的迁移类型不是高阶原子类型、隔离类型和CMA迁移类型，那么把页块的迁移类型转换为高阶原子类型，并且把页块中没有分配出去的页移到高阶原子类型的空闲链表中。

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

### 1. 函数`__alloc_pages_nodemask`

- 所有分配页的函数最终都会调用到函数`__alloc_pages_nodemask`，这个函数被称为分区的伙伴分配器心脏。其函数原型如下：
  ```c
  struct page *__alloc_pages_nodemask(gfp_t gfp_mask, unsigned int order, int preferred_nid, nodemask_t *nodemask)
      
  ```
  参数如下：
  
  >gfp_mask: 分配标志位。
  >
  >order： 阶数。
  >
  >preferred_nid： 指定内存节点，用于获取备用区域列表。
  >
  >nodemask: 允许从哪些内存节点分配页，如果调用者没有要求，可以传入空指针。
  
  算法如下：
  
  > 1. 根据分配标志位得到首选区域类型和迁移类型；
  > 2. 执行快速路径，使用低水线尝试第一次分配；
  > 3. 如果快速路径分配失败，那么执行慢速路径。

- 页分配器定义了一些内部分配标志位：

  ```c
  [linux-4.14/mm/internal.h]
  
  475  #define ALLOC_WMARK_MIN		WMARK_MIN /* 0x00,使用最低水位线 */
  476  #define ALLOC_WMARK_LOW		WMARK_LOW /* 0x01，使用低水线 */
  477  #define ALLOC_WMARK_HIGH	WMARK_HIGH /* 0x02，使用高水线 */
  478  #define ALLOC_NO_WATERMARKS	0x04 /* 完全不检查水线 */
  481  #define ALLOC_WMARK_MASK	(ALLOC_NO_WATERMARKS-1) /* 得到水线位的掩码 */
  
  494  #define ALLOC_HARDER		0x10 /* try to alloc harder 试图更努力分配 */
  495  #define ALLOC_HIGH		0x20 /* __GFP_HIGH set 设置了__GFP_HIGH，调用者是高优先级的 */
  496  #define ALLOC_CPUSET		0x40 /* check for correct cpuset 检查cpuset是否允许进程从某个内存节点分配 */
  497  #define ALLOC_CMA		0x80 /* allow allocations from CMA areas 允许从CMA（连续内存分配器）迁移类型分配 */
  
  ```

- 函数`__alloc_pages_nodemask`定义及解析如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  4149  /*
  4150   * This is the 'heart' of the zoned buddy allocator.
  4151   */
  4152  struct page *
  4153  __alloc_pages_nodemask(gfp_t gfp_mask, unsigned int order, int preferred_nid,
  4154  							nodemask_t *nodemask)
  4155  {
  4156  	struct page *page;
  4157  	unsigned int alloc_flags = ALLOC_WMARK_LOW;
  4158  	gfp_t alloc_mask; /* The gfp_t that was actually used for allocation */
  4159  	struct alloc_context ac = { };
  4160  
  4161  	/*
  4162  	 * There are several places where we assume that the order value is sane
  4163  	 * so bail out early if the request is out of bound.
  4164  	 */
  4165  	if (unlikely(order >= MAX_ORDER)) {
  4166  		WARN_ON_ONCE(!(gfp_mask & __GFP_NOWARN));
  4167  		return NULL;
  4168  	}
  4169  
  4170  	gfp_mask &= gfp_allowed_mask;
  4171  	alloc_mask = gfp_mask;
      	/*
      	 * prepare_alloc_pages()函数主要做一些分配钱的准备工作，下文有其定义和解析
      	 */
  4172  	if (!prepare_alloc_pages(gfp_mask, order, preferred_nid, nodemask, &ac, &alloc_mask, &alloc_flags))
  4173  		return NULL;
  4174  
  4175  	finalise_ac(gfp_mask, order, &ac);
  4176  
  4177  	/* First allocation attempt */
  4178  	page = get_page_from_freelist(alloc_mask, order, alloc_flags, &ac);
  4179  	if (likely(page))
  4180  		goto out;
  4181  
  4182  	/*
  4183  	 * Apply scoped allocation constraints. This is mainly about GFP_NOFS
  4184  	 * resp. GFP_NOIO which has to be inherited for all allocation requests
  4185  	 * from a particular context which has been marked by
  4186  	 * memalloc_no{fs,io}_{save,restore}.
  4187  	 */
  4188  	alloc_mask = current_gfp_context(gfp_mask);
  4189  	ac.spread_dirty_pages = false;
  4190  
  4191  	/*
  4192  	 * Restore the original nodemask if it was potentially replaced with
  4193  	 * &cpuset_current_mems_allowed to optimize the fast-path attempt.
  4194  	 */
  4195  	if (unlikely(ac.nodemask != nodemask))
  4196  		ac.nodemask = nodemask;
  4197  
  4198  	page = __alloc_pages_slowpath(alloc_mask, order, &ac);
  4199  
  4200  out:
  4201  	if (memcg_kmem_enabled() && (gfp_mask & __GFP_ACCOUNT) && page &&
  4202  	    unlikely(memcg_kmem_charge(page, gfp_mask, order) != 0)) {
  4203  		__free_pages(page, order);
  4204  		page = NULL;
  4205  	}
  4206  
  4207  	trace_mm_page_alloc(page, order, alloc_mask, ac.migratetype);
  4208  
  4209  	return page;
  4210  }
  
  ```

### 2. 函数`prepare_alloc_pages()`

- `__alloc_pages_nodemask() -> prepare_alloc_pages()`，`prepare_alloc_pages()`主要做一些分配前的准备工作，`struct alloc_context`数据结构是伙伴系统分配函数中用于保存相关参数的数据结构。，其函数定义及解析如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  4101  static inline bool prepare_alloc_pages(gfp_t gfp_mask, unsigned int order,
  4102  		int preferred_nid, nodemask_t *nodemask,
  4103  		struct alloc_context *ac, gfp_t *alloc_mask,
  4104  		unsigned int *alloc_flags)
  4105  {
      	/* 给ac赋值 */
  4106  	ac->high_zoneidx = gfp_zone(gfp_mask); /* gfp_zone函数从分配标志位中计算出zone的zoneidx，并存放在high_zoneidx中 */
  4107  	ac->zonelist = node_zonelist(preferred_nid, gfp_mask);
  4108  	ac->nodemask = nodemask;
  4109  	ac->migratetype = gfpflags_to_migratetype(gfp_mask);
  4110  
      	/* 检查cpuset */
  4111  	if (cpusets_enabled()) {
  4112  		*alloc_mask |= __GFP_HARDWALL;
  4113  		if (!ac->nodemask)
  4114  			ac->nodemask = &cpuset_current_mems_allowed;
  4115  		else
  4116  			*alloc_flags |= ALLOC_CPUSET;
  4117  	}
  4118  
      	/* fs检查 */
  4119  	fs_reclaim_acquire(gfp_mask);
  4120  	fs_reclaim_release(gfp_mask);
  4121  
  4122  	might_sleep_if(gfp_mask & __GFP_DIRECT_RECLAIM);
  4123  
  4124  	if (should_fail_alloc_page(gfp_mask, order))
  4125  		return false;
  4126  
      	/* 迁移类型检查 */
  4127  	if (IS_ENABLED(CONFIG_CMA) && ac->migratetype == MIGRATE_MOVABLE)
  4128  		*alloc_flags |= ALLOC_CMA;
  4129  
  4130  	return true;
  4131  }
  
  ```

  `prepare_alloc_pages()`函数分析完毕

### 3. 函数`finalise_ac()`

- `__alloc_pages_nodemask() -> finalise_ac()`,

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  4133  /* Determine whether to spread dirty pages and what the first usable zone */
  4134  static inline void finalise_ac(gfp_t gfp_mask,
  4135  		unsigned int order, struct alloc_context *ac)
  4136  {
  4137  	/* Dirty zone balancing only done in the fast path 根据__GFP_WRITE定义，将对物理页进行写操作的脏页均衡的分布在各个内存区域内，以避免这些脏页分布在同一个zone中*/
  4138  	ac->spread_dirty_pages = (gfp_mask & __GFP_WRITE);
  4139  
  4140  	/*
  4141  	 * The preferred zone is used for statistics but crucially it is
  4142  	 * also used as the starting point for the zonelist iterator. It
  4143  	 * may get reset for allocations that ignore memory policies.
  		 * 获取首选的zone
  4144  	 */
  4145  	ac->preferred_zoneref = first_zones_zonelist(ac->zonelist,
  4146  					ac->high_zoneidx, ac->nodemask);
  4147  }
  
  ```

  `finalise_ac() -> first_zones_zonelist() -> next_zones_zonelist() -> __next_zones_zonelist()`, 函数`finalise_ac()`最终调用`__next_zones_zonelist()`，函数`__next_zones_zonelist()`返回合适的内存区域zone，以供后续分配。其定义及解析如下：

  ```c
  
  [linux-4.14/mm/mmzone.c]
  
  55  /* Returns the next zone at or below highest_zoneidx in a zonelist */
  56  struct zoneref *__next_zones_zonelist(struct zoneref *z,
  57  					enum zone_type highest_zoneidx,
  58  					nodemask_t *nodes)
  59  {
  60  	/*
  61  	 * Find the next suitable zone to use for the allocation.
  62  	 * Only filter based on nodemask if it's set
  		 * zonelist_zone_idx 返回 z->zone_idx
  63  	 */
  64  	if (unlikely(nodes == NULL))
  65  		while (zonelist_zone_idx(z) > highest_zoneidx)
  66  			z++;
  67  	else
  68  		while (zonelist_zone_idx(z) > highest_zoneidx ||
  69  				(z->zone && !zref_in_nodemask(z, nodes)))
  70  			z++;
  71  
  72  	return z;
  73  }
  
  [linux-4.14/include/linux/mmzone.h]
  587  struct zoneref {
  588  	struct zone *zone;	/* Pointer to actual zone */
  589  	int zone_idx;		/* zone_idx(zoneref->zone) */
  590  };
  
  606  struct zonelist {
  607  	struct zoneref _zonerefs[MAX_ZONES_PER_ZONELIST + 1];
  608  };
  
  ```

  函数`__next_zones_zonelist()`是计算zone的核心函数，这里highest_zoneidx是通过`gfp_zone()`函数计算分配标志位`gfp_mask`而来。数据结构`struct zonelist`有一个`zonerefs`数组（`struct zoneref`类型），而`zoneref`数据结构里有一个成员`zone`（`struct zone`类型）指针会指向zone数据结构，还有一个`zone_idx`成员指向zone的编号。zone在系统处理时会初始化这个数组，具体函数在`build_zonelists_node()`中。

  在ARM Vexpress平台中，zone类型、zoneref[]数组、zoneidx关系如下：

  | ZONE_HIGHMEM | _zonerefs[0] -> zone_index=1 |
  | -----------: | ---------------------------- |
  |  ZONE_NORMAL | _zonerefs[1] -> zone_index=0 |

  `zonerefs[0]`表示`ZONE_HIGHMEM`，其zone的编号`zone_index`值为1；`zonerefs[1]`表示`ZONE_NORMAL`，其zone的编号`zone_index`值为0。也就是说，基于zone的设计思想是：分配物理页面时会优先考虑`ZONE_HIGHMEM`，因为`ZONE_HIGHMEM`在zonelist中排在`ZONE_NORMAL`前面。

  如果分配标志位`gfp_mask`为`GFP_KERNEL`，则`gfp_zone(GFP_KERNEL)`函数返回0，即`highest_zoneidx`为0，而这个内存节点的第一个zone是`ZONE_HIGHMEM`，其zone编号`zone_index`的值为1。因此在`__next_zones_zonelist()`中，z++，最终`first_zones_zonelist()`函数会返回`ZONE_NORMAL`。

  `finalise_ac()`函数分析完毕。

### 4. 函数`get_page_from_freelist()`

- 我们看算法的第二阶段，即“执行快速路径，使用低水线尝试第一次分配”。本阶段主要调用函数`get_page_from_freelist()`，其代码及解析如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  3079  /*
  3080   * get_page_from_freelist goes through the zonelist trying to allocate
  3081   * a page.
  3082   */
  3083  static struct page *
  3084  get_page_from_freelist(gfp_t gfp_mask, unsigned int order, int alloc_flags,
  3085  						const struct alloc_context *ac)
  3086  {
  3087  	struct zoneref *z = ac->preferred_zoneref;
  3088  	struct zone *zone;
  3089  	struct pglist_data *last_pgdat_dirty_limit = NULL;
  3090  
  3091  	/*
  3092  	 * Scan zonelist, looking for a zone with enough free.
  3093  	 * See also __cpuset_node_allowed() comment in kernel/cpuset.c.
  		 * for_next_zone_zonelist_nodemask宏扫描备用区域列表中每个满足条件的区域：“区域类型小于或等于首先区域类型，并且内存节点在节点掩码中的相应位置被设置”
  3094  	 */
  3095  	for_next_zone_zonelist_nodemask(zone, z, ac->zonelist, ac->high_zoneidx,
  3096  								ac->nodemask) {
  3097  		struct page *page;
  3098  		unsigned long mark;
  3099  
      		/* 如果编译了 cpuset 功能，调用者设置 ALLOC_CPUSET 要求使用 cpuset 检查，并且 cpuset 不允许当前进程从这个内存节点分配页，那么不能从这个内存区域分配页。 */
  3100  		if (cpusets_enabled() &&
  3101  			(alloc_flags & ALLOC_CPUSET) &&
  3102  			!__cpuset_zone_allowed(zone, gfp_mask))
  3103  				continue;
  3104  		/*
  3105  		 * When allocating a page cache page for writing, we
  3106  		 * want to get it from a node that is within its dirty
  3107  		 * limit, such that no single node holds more than its
  3108  		 * proportional share of globally allowed dirty pages.
  3109  		 * The dirty limits take into account the node's
  3110  		 * lowmem reserves and high watermark so that kswapd
  3111  		 * should be able to balance it without having to
  3112  		 * write pages from its LRU list.
  3113  		 *
  3114  		 * XXX: For now, allow allocations to potentially
  3115  		 * exceed the per-node dirty limit in the slowpath
  3116  		 * (spread_dirty_pages unset) before going into reclaim,
  3117  		 * which is important when on a NUMA setup the allowed
  3118  		 * nodes are together not big enough to reach the
  3119  		 * global limit.  The proper fix for these situations
  3120  		 * will require awareness of nodes in the
  3121  		 * dirty-throttling and the flusher threads.
  			 * 如果调用者设置标志位 __GFP_ERITE，表示文件系统申请分配一个页缓存页用于写文件，那么检查内存节点的脏页数量是否超过限制，如果超过限制，那么不能从这个区域分配页。
  3122  		 */
  3123  		if (ac->spread_dirty_pages) {
  3124  			if (last_pgdat_dirty_limit == zone->zone_pgdat)
  3125  				continue;
  3126  
  3127  			if (!node_dirty_ok(zone->zone_pgdat)) {
  3128  				last_pgdat_dirty_limit = zone->zone_pgdat;
  3129  				continue;
  3130  			}
  3131  		}
  3132  
  3133  		mark = zone->watermark[alloc_flags & ALLOC_WMARK_MASK];//获取水线
  3134  		if (!zone_watermark_fast(zone, order, mark,
  3135  				       ac_classzone_idx(ac), alloc_flags)) { //检查水线，如果（区域的空闲页数 - 申请的页数） 小于水线，处理如下：
  3136  			int ret;
  3137  
  3138  			/* Checked here to keep the fast path fast */
  3139  			BUILD_BUG_ON(ALLOC_NO_WATERMARKS < NR_WMARK);
  3140  			if (alloc_flags & ALLOC_NO_WATERMARKS) //如果调用者要求不检查水线，那么可以从这个区域分配页
  3141  				goto try_this_zone;
  3142  
  3143  			if (node_reclaim_mode == 0 ||
  3144  			    !zone_allows_reclaim(ac->preferred_zoneref->zone, zone)) //如果没有开启节点回收功能，或者当前节点和首选节点之间的距离大于回收距离，那么不能从这个区域分配页
  3145  				continue;
  3146  
  3147  			ret = node_reclaim(zone->zone_pgdat, gfp_mask, order); //从节点回收没有映射到进程虚拟地址空间的文件页和块分配器申请的页，然后重新检查水线，如果（区域的空闲页数 - 申请的页数） 还是小于水线，那么不能从这个区域分配页。
  3148  			switch (ret) {
  3149  			case NODE_RECLAIM_NOSCAN:
  3150  				/* did not scan */
  3151  				continue;
  3152  			case NODE_RECLAIM_FULL:
  3153  				/* scanned but unreclaimable */
  3154  				continue;
  3155  			default:
  3156  				/* did we reclaim enough */
  3157  				if (zone_watermark_ok(zone, order, mark,
  3158  						ac_classzone_idx(ac), alloc_flags))
  3159  					goto try_this_zone;
  3160  
  3161  				continue;
  3162  			}
  3163  		}
  3164  
  3165  try_this_zone:
  3166  		page = rmqueue(ac->preferred_zoneref->zone, zone, order,
  3167  				gfp_mask, alloc_flags, ac->migratetype); // 从当前区域分配页
  3168  		if (page) { //如果分配成功，调用 prep_new_page 以初始化页，如果是高阶原子分配，并且区域中高阶原子类型的页数没有超过限制，那么把分配的页所属的页块转换为高阶原子类型。
  3169  			prep_new_page(page, order, gfp_mask, alloc_flags);
  3170  
  3171  			/*
  3172  			 * If this is a high-order atomic allocation then check
  3173  			 * if the pageblock should be reserved for the future
  3174  			 */
  3175  			if (unlikely(order && (alloc_flags & ALLOC_HARDER)))
  3176  				reserve_highatomic_pageblock(page, zone, order);
  3177  
  3178  			return page;
  3179  		}
  3180  	}
  3181  
  3182  	return NULL;
  3183  }
  
  ```

- `get_page_from_freelist() -> zone_watermark_fast()`,`zone_watermark_fast()`函数负责检查区域的空闲页数是否大于水线，其代码如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  3028  static inline bool zone_watermark_fast(struct zone *z, unsigned int order,
  3029  		unsigned long mark, int classzone_idx, unsigned int alloc_flags)
  3030  {
  3031  	long free_pages = zone_page_state(z, NR_FREE_PAGES);
  3032  	long cma_pages = 0;
  3033  
  3034  #ifdef CONFIG_CMA
  3035  	/* If allocation can't use CMA areas don't use free CMA pages */
  3036  	if (!(alloc_flags & ALLOC_CMA))
  3037  		cma_pages = zone_page_state(z, NR_FREE_CMA_PAGES);
  3038  #endif
  3039  
  3040  	/*
  3041  	 * Fast check for order-0 only. If this fails then the reserves
  3042  	 * need to be calculated. There is a corner case where the check
  3043  	 * passes but only the high-order atomic reserve are free. If
  3044  	 * the caller is !atomic then it'll uselessly search the free
  3045  	 * list. That corner case is then slower but it is harmless.
  3046  	 */
  3047  	if (!order && (free_pages - cma_pages) > mark + z->lowmem_reserve[classzone_idx])
  3048  		return true;
  3049  
  3050  	return __zone_watermark_ok(z, order, mark, classzone_idx, alloc_flags,
  3051  					free_pages);
  3052  }
  
  ```

  第`3034~3048`行代码，针对0阶执行快速检查：

  > 1. 第3036、3037行，如果不允许从CMA迁移类型分配，那么不要使用空闲的CMA页，必须把空闲页数减去空闲的CMA页数；
  > 2. 第3047行，如果空闲页数大于（水线+低端内存保留页数），即（空闲页数 - 申请的一页）大于等于（水线+低端内存保留页数），并且阶数为0， 那么允许从这个区域分配页；
  > 3. 第3050行，如果是其他情况，那么调用函数`__zone_watermark_ok`进行检查。

- `zone_watermark_fast() -> __zone_watermark_ok()`，函数`__zone_watermark_ok()`更加仔细地检查区域的空闲页数是否大于水线，其代码如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  2936  /*
  2937   * Return true if free base pages are above 'mark'. For high-order checks it
  2938   * will return true of the order-0 watermark is reached and there is at least
  2939   * one free page of a suitable size. Checking now avoids taking the zone lock
  2940   * to check in the allocation paths if no pages are free.
  2941   */
  2942  bool __zone_watermark_ok(struct zone *z, unsigned int order, unsigned long mark,
  2943  			 int classzone_idx, unsigned int alloc_flags,
  2944  			 long free_pages)
  2945  {
  2946  	long min = mark;
  2947  	int o;
  2948  	const bool alloc_harder = (alloc_flags & (ALLOC_HARDER|ALLOC_OOM));
  2949  
  2950  	/* free_pages may go negative - that's OK 把空闲页数减去申请页数。然后减1*/
  2951  	free_pages -= (1 << order) - 1;
  2952  
  2953  	if (alloc_flags & ALLOC_HIGH) //如果调用者是高优先级的，把水线减半。
  2954  		min -= min / 2;
  2955  
  2956  	/*
  2957  	 * If the caller does not have rights to ALLOC_HARDER then subtract
  2958  	 * the high-atomic reserves. This will over-estimate the size of the
  2959  	 * atomic reserve but it avoids a search.
  		 * 如果调用者没有要求更努力分配，那么减去为高阶原子分配保留的页数
  2960  	 */
  2961  	if (likely(!alloc_harder)) {
  2962  		free_pages -= z->nr_reserved_highatomic;
  2963  	} else {
  2964  		/*
  2965  		 * OOM victims can try even harder than normal ALLOC_HARDER
  2966  		 * users on the grounds that it's definitely going to be in
  2967  		 * the exit path shortly and free memory. Any allocation it
  2968  		 * makes during the free path will be small and short-lived.
  			 * 如果调用者要求更努力分配，把水线减去1/4，如果同时定义了ALLOC_OOM，把水线减去一半
  2969  		 */
  2970  		if (alloc_flags & ALLOC_OOM)
  2971  			min -= min / 2;
  2972  		else
  2973  			min -= min / 4;
  2974  	}
  2975  
  2976  
  2977  #ifdef CONFIG_CMA
  2978  	/* If allocation can't use CMA areas don't use free CMA pages */
  2979  	if (!(alloc_flags & ALLOC_CMA)) //如果不允许从CMA迁移类型分配，那么不能使用空闲的CMA页，就需要把空闲页数减去空闲的CMA页数
  2980  		free_pages -= zone_page_state(z, NR_FREE_CMA_PAGES);
  2981  #endif
  2982  
  2983  	/*
  2984  	 * Check watermarks for an order-0 allocation request. If these
  2985  	 * are not met, then a high-order request also cannot go ahead
  2986  	 * even if a suitable page happened to be free.
  		 * 如果(空闲页数-申请页数+1)<= (水线+低端内存保留页数)，即(空闲页数-申请页数)<(水线+低端内存保留页数)，那么不能从这个区域分配页。
  2987  	 */
  2988  	if (free_pages <= min + z->lowmem_reserve[classzone_idx])
  2989  		return false;
  2990  
  2991  	/* If this is an order-0 request then the watermark is fine 
  		 * 如果只申请一页，那么允许从这个区域分配页。
  		 */
  2992  	if (!order)
  2993  		return true;
  2994  
  2995  	/* For a high-order request, check at least one suitable page is free 
  		 * 如果申请阶数大于0
  		 */
  2996  	for (o = order; o < MAX_ORDER; o++) {
  2997  		struct free_area *area = &z->free_area[o];
  2998  		int mt;
  2999  
  3000  		if (!area->nr_free)
  3001  			continue;
  3002  
  3003  		for (mt = 0; mt < MIGRATE_PCPTYPES; mt++) { //不可移动、可移动和可回收任何一种迁移类型，只要有一个阶数大于或等于申请阶数的空闲页块，就允许从这个区域分配页。
  3004  			if (!list_empty(&area->free_list[mt]))
  3005  				return true;
  3006  		}
  3007  
  3008  #ifdef CONFIG_CMA
  3009  		if ((alloc_flags & ALLOC_CMA) &&
  3010  		    !list_empty(&area->free_list[MIGRATE_CMA])) { //如果调用者指定从CMA迁移类型分配，CMA迁移类型只要有一个阶数大于或等于申请阶数的空闲页块，就允许从这个区域分配页。
  3011  			return true;
  3012  		}
  3013  #endif
  3014  		if (alloc_harder &&
  3015  			!list_empty(&area->free_list[MIGRATE_HIGHATOMIC])) // 如果调用者要求更努力分配，只要有一个阶数大于或等于申请阶数的空闲页块，就允许从这个区域分配页。
  3016  			return true;
  3017  	}
  3018  	return false;
  3019  }
  
  ```

- `get_page_from_freelist() -> rmqueue()`，函数`rmqueue()`辅助分配页，其代码如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  2804  /*
  2805   * Allocate a page from the given zone. Use pcplists for order-0 allocations.
  2806   */
  2807  static inline
  2808  struct page *rmqueue(struct zone *preferred_zone,
  2809  			struct zone *zone, unsigned int order,
  2810  			gfp_t gfp_flags, unsigned int alloc_flags,
  2811  			int migratetype)
  2812  {
  2813  	unsigned long flags;
  2814  	struct page *page;
  2815  
  2816  	if (likely(order == 0)) {//申请阶数为0时，从每处理器页集合分配页
  2817  		page = rmqueue_pcplist(preferred_zone, zone, order,
  2818  				gfp_flags, migratetype);
  2819  		goto out;
  2820  	}
  2821  
  2822  	/*
  2823  	 * We most definitely don't want callers attempting to
  2824  	 * allocate greater than order-1 page units with __GFP_NOFAIL.
  		 * 申请阶数大于0
  2825  	 */
  2826  	WARN_ON_ONCE((gfp_flags & __GFP_NOFAIL) && (order > 1));
  2827  	spin_lock_irqsave(&zone->lock, flags);
  2828  
  2829  	do {
  2830  		page = NULL;
  2831  		if (alloc_flags & ALLOC_HARDER) { //如果调用者要求更努力分配，先尝试从高阶原子类型分配页
  2832  			page = __rmqueue_smallest(zone, order, MIGRATE_HIGHATOMIC);
  2833  			if (page)
  2834  				trace_mm_page_alloc_zone_locked(page, order, migratetype);
  2835  		}
  2836  		if (!page)
  2837  			page = __rmqueue(zone, order, migratetype); // 从指定迁移类型分配页
  2838  	} while (page && check_new_pages(page, order));
  2839  	spin_unlock(&zone->lock);
  2840  	if (!page)
  2841  		goto failed;
  2842  	__mod_zone_freepage_state(zone, -(1 << order),
  2843  				  get_pcppage_migratetype(page));
  2844  
  2845  	__count_zid_vm_events(PGALLOC, page_zonenum(page), 1 << order);
  2846  	zone_statistics(preferred_zone, zone);
  2847  	local_irq_restore(flags);
  2848  
  2849  out:
  2850  	VM_BUG_ON_PAGE(page && bad_range(zone, page), page);
  2851  	return page;
  2852  
  2853  failed:
  2854  	local_irq_restore(flags);
  2855  	return NULL;
  2856  }
  
  ```

- 当申请阶数为0时，则从每处理器页集合分配页，调用函数`rmqueue_pcplist()`，即`rmqueue() -> rmqueue_pcplist()`， 该函数负责从内存区域的每处理器页集合分配页，其把主要工作委托给函数`__rmqueue_pcplist()`,函数`__rmqueue_pcplist()`定义如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  2754  static struct page *__rmqueue_pcplist(struct zone *zone, int migratetype,
  2755  			bool cold, struct per_cpu_pages *pcp,
  2756  			struct list_head *list)
  2757  {
  2758  	struct page *page;
  2759  
  2760  	do {
  2761  		if (list_empty(list)) {// 如果每处理器页集合中指定迁移类型的链表是空的，那么批量申请页加入链表
  2762  			pcp->count += rmqueue_bulk(zone, 0,
  2763  					pcp->batch, list,
  2764  					migratetype, cold);
  2765  			if (unlikely(list_empty(list)))
  2766  				return NULL;
  2767  		}
  2768  
  2769  		if (cold) //如果调用者指定标志位__GFP_COLD要求分配缓存冷页，就从链表尾部分配一页，否则从链表首部分配一页
  2770  			page = list_last_entry(list, struct page, lru);
  2771  		else
  2772  			page = list_first_entry(list, struct page, lru);
  2773  
  2774  		list_del(&page->lru);
  2775  		pcp->count--;
  2776  	} while (check_new_pcp(page));
  2777  
  2778  	return page;
  2779  }
  
  ```

- 当申请阶数大于0，且从指定迁移类型分配页时，调用函数`__rmqueue()`，即`rmqueue() -> __rmqueue()`，函数`__rmqueue()`的处理流程如下：

  > 1. 从指定迁移类型分配页，如果分配成功，那么处理结束；
  > 2. 如果指定迁移类型为可移动类型，那么从CMA类型盗用页；
  > 3. 从备用迁移类型盗用页。

  所需求的页面分配成功后，函数`__rmqueue()`返回这个页块的起始页面的`struct page`数据结构。
  ```c
  [linux-4.14/mm/page_alloc.c]
  2299  static struct page *__rmqueue(struct zone *zone, unsigned int order,
  2300  				int migratetype)
  2301  {
  2302  	struct page *page;
  2303  
  2304  retry:
  2305  	page = __rmqueue_smallest(zone, order, migratetype);
  2306  	if (unlikely(!page)) {
  2307  		if (migratetype == MIGRATE_MOVABLE)
  2308  			page = __rmqueue_cma_fallback(zone, order);
  2309  
  2310  		if (!page && __rmqueue_fallback(zone, order, migratetype))
  2311  			goto retry;
  2312  	}
  2313  
  2314  	trace_mm_page_alloc_zone_locked(page, order, migratetype);
  2315  	return page;
  2316  }
  
  ```

- `__rmqueue() -> __rmqueue_smallest()`， `__rmqueue_smallest()`函数从申请阶数到最大阶数逐个尝试：

  > 1. 如果指定迁移类型的空闲链表不是空的，从链表中取出第一个页块；
  > 2. 如果页块阶数比申请阶数大，那么重复分裂页块，把后一半插入低一阶的空闲链表，直到获得一个大小为申请阶数的页块。

  为什么`zone`当前`order`对应的空闲区域`free_area`中相应的`migratetype`类型的链表里会没有空闲对象？这是因为在系统刚启动时，空闲页面会尽可能地都分配到`MAX_ORDER - 1`的链表中，这个可以在系统刚起来之后，通过`cat /proc/pagetypeinfo`命令看出。
  ```c
  [linux-4.14/mm/page_alloc.c]
  
  1802  static inline
  1803  struct page *__rmqueue_smallest(struct zone *zone, unsigned int order,
  1804  						int migratetype)
  1805  {
  1806  	unsigned int current_order;
  1807  	struct free_area *area;
  1808  	struct page *page;
  1809  
  1810  	/* Find a page of the appropriate size in the preferred list 在首选迁移类型的空闲链表中查找长度合适的页块*/
  1811  	for (current_order = order; current_order < MAX_ORDER; ++current_order) {
  1812  		area = &(zone->free_area[current_order]);
  1813  		page = list_first_entry_or_null(&area->free_list[migratetype],
  1814  							struct page, lru);
  1815  		if (!page)
  1816  			continue;
  1817  		list_del(&page->lru);
  1818  		rmv_page_order(page);
  1819  		area->nr_free--;
  1820  		expand(zone, page, order, current_order, area, migratetype);//切割页块，一般来说current_order要大于申请阶数order
  1821  		set_pcppage_migratetype(page, migratetype);
  1822  		return page;
  1823  	}
  1824  
  1825  	return NULL;
  1826  }
  
  ```

- `__rmqueue_smallest() -> expand()`，当找到某一个`order`的空闲区中对应的`migratetype`类型的链表中有空闲内存块时， 就会从中把一个内存块取出来，然后调用函数`expand()`来切割，因为通常取出来的页块要比申请的内存页块大，切完之后需要把剩下的内存块重新放回伙伴系统中。其定义如下：

  ```c
  [linux-4.14/mm/page_alloc.c]
  
  1650  static inline void expand(struct zone *zone, struct page *page,
  1651  	int low, int high, struct free_area *area,
  1652  	int migratetype)
  1653  {
  1654  	unsigned long size = 1 << high;
  1655  
  1656  	while (high > low) {
  1657  		area--;
  1658  		high--;
  1659  		size >>= 1;
  1660  		VM_BUG_ON_PAGE(bad_range(zone, &page[size]), &page[size]);
  1661  
  1662  		/*
  1663  		 * Mark as guard pages (or page), that will allow to
  1664  		 * merge back to allocator when buddy will be freed.
  1665  		 * Corresponding page table entries will not be touched,
  1666  		 * pages will stay not present in virtual address space
  1667  		 */
  1668  		if (set_page_guard(zone, &page[size], high, migratetype))
  1669  			continue;
  1670  
  1671  		list_add(&page[size].lru, &area->free_list[migratetype]);
  1672  		area->nr_free++;
  1673  		set_page_order(&page[size], high);
  1674  	}
  1675  }
  
  ```

  这里参数`high`就是`current_order`，通常要大于申请阶数order，即参数`low`，每比较一次，`area`减1，相当于退了一级order，最后通过`list_add()`把剩下的内存块添加到低一级的空闲链表中。

### 5. 函数`__alloc_pages_nodemask()`新旧版本差异

- 至此，算法中的第一阶段“根据分配标志位得到首选区域类型和迁移类型”，我们已经解析完毕，另外在liunx4.14版本中`__alloc_pages_nodemask()`函数相比于之前版本（如liunx4.12内核版本）有所改变，具体如下：

  > 1. 函数定义中第三个参数，从旧版本的`struct zonelist *zonelist`修正为`int preferred_nid`，相应的，在代码中就多了通过preferred_nid、gfp_mask获取zonelist的相关代码；
  > 2. liunx4.14版本中将分配之前的准备部分封装在了函数`prepare_alloc_pages()`中；
  > 3. liunx4.14版本中将获取首选区域的代码封装在了函数`finalise_ac()`中。
