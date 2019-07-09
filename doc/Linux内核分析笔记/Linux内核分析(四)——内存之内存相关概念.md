# Linux内核分析(四)——内存之相关概念

## 1. 物理地址空间

### 1.1 物理地址空间介绍

- 物理地址是处理器在系统总线上看到的地址。使用精简指令集（RISC）的处理器通常只实现一个物理地址空间，外围设备和物理内存使用统一的物理地址空间，处理器可以像访问内存单元一样访问外围设备。有些设备把分配给外围设备的物理地址区域成为设备内存。

- 处理器通过外围设备控制器的寄存器访问外围设备，寄存器分为控制寄存器、状态寄存器和数据寄存器三大类。外围设备的寄存器通常被连续地编址。处理器对外围设备寄存器的编址方式有两种：

  > 1. I/O映射方式（I/O-mapped）：英特尔的`x86`处理器为外围设备专门实现了一个单独的地址空间，称为“I/O地址空间”或“I/O端口空间”，处理器通过专门的I/O指令来访问这一空间中的地址单元。
  > 2. 内存映射方式（memory-mapped）：使用精简指令集（RISC）的处理器对外围设备寄存器的编址通常使用这一方式。

- 程序只能通过虚拟地址访问外设寄存器。

  

### 1.2 ARM64架构实现

- ARM64架构定义了两种内存类型：

  > 1. 正常内存（Normal Memory）：包括物理内存和只读存储器（ROM）。
  > 2. 设备内存（Device Memory）：指分配给外围设备寄存器的物理地址区域。

- 本节对正常内存和设备内存不做细述。


### 1.3 物理地址宽度

- 目前ARM64处理器支持的最大物理地址宽度是48位，如果实现了ARMv8.2标准的大物理地址（Large Physical Address，LPA）支持，并且页长度是64KB，那么物理地址的最大宽度是52位。

- 可以使用寄存器TCR_EL1（Translation Control Register for Exception Level 1，异常级别1的转换控制寄存器）的IPS（Intermediate Physical Address Size，中间物理地址长度）控制物理地址的宽度。IPS字段的长度是3位，IPS字段的值和物理地址宽度的对应关系如下表所示：

  | IPS字段 | 物理地址宽度 |
  | ------- | ------------ |
  | 000     | 32位         |
  | 001     | 36位         |
  | 010     | 40位         |
  | 011     | 42位         |
  | 100     | 44位         |
  | 101     | 48位         |
  | 110     | 52位         |



## 2. 物理内存组织

### 2.1 体系结构

- 目前多处理器系统有两种体系结构。

  > 1. 非一致内存访问（Non-Uniform Memory Access，NUMA）：只内存被划分成多个内存节点的多处理器系统，访问一个内存节点花费的时间取决于处理器和内存节点的距离。每个处理器有一个本地内存节点，处理器访问本地内存节点的速度比访问其他内存节点的速度快。NUMA是中高端服务器的主流体系结构。
  > 2. 对称多处理器（Symmetry Multi-Processor，SMP）：即一致内存访问（Uniform Memory Access，UMA），所有处理器访问内存花费的时间是相同的。每个处理器的地位是平等的，仅在内核初始化的时候不平等：“0号处理器作为引导处理器负责初始化内核，其他处理器等待内核初始化完成。”

- 在实际应用中可以采用混合体系结构，在NUMA节点内部使用SMP体系结构。

  

### 2.2 内存模型

- 内存模型是从处理器的角度看到的物理内存分布情况，内核管理不同内存模型的方式存在差异。内存管理子系统支持3种内存模型：

  > 1. 平坦内存（Flat Memory）：内存的物理地址空间是连续的，没有空洞。
  > 2. 不连续内存（Discontiguous Memory）：内存的物理地址空间存在空洞，这种模型可以高效地处理空洞。
  > 3. 稀疏内存（Sparse Memory）：内存的物理地址空间存在空洞。如果要支持内存插拔，只能选择稀疏内存模型。

- 当系统包含多块物理内存，两块物理内存之间就存在空洞。一块内存的物理地址空间也可能存在空洞，可以查看处理器的参考手册获取分配给内存的物理地址空间。
- 如果内存的物理地址空间是连续的，不连续的内存模型会产生额外的开销，降低性能，所以平坦内存模型是更好的选择。
- 如果内存的物理地址空间存在空洞，可选择不连续内存模型，因为平坦内存模型会为空洞分配page结构体，浪费内存；稀疏内存模型是实验性的，尽量不要选择稀疏内存模型，除非内存的物理地址空间很稀疏，或者要支持内存热插拔；相比于平坦内存模型和稀疏内存模型，不连续内存模型对空洞做了优化处理，不会为空洞分配page结构体。



### 2.3 三级结构

- 内存管理子系统使用节点（node）、区域（也有称为区块、管理区的）（zone）和页（page）三级结构描述物理内存。

#### 2.3.1 内存节点 node

- 内存节点分两种情况：

	> 1. NUMA系统的内存节点，根据处理器和内存的距离划分。
	> 2. 在具有不连续内存的UMA系统中，表示比区域（zone）的级别更高的内存区域，根据物理地址是否连续划分，每块物理地址连续的内存是一个内存节点。

- 内存中的每个节点都由 pg_data_t 描述，而 pg_data_t 由 struct pglist_data 结构体定义。内核定义了宏NODE_DATA（nid），用它来获取节点的pglist_data实例。对于平坦内存模型，只有一个pglist_data实例：contig_page_data。

  ```c
  // linux-4.14/arch/arm64/include/asm/mmzone.h
  
  1  /* SPDX-License-Identifier: GPL-2.0 */
  2  #ifndef __ASM_MMZONE_H
  3  #define __ASM_MMZONE_H
  4  
  5  #ifdef CONFIG_NUMA
  6  
  7  #include <asm/numa.h>
  8  
  9  extern struct pglist_data *node_data[];
  10  #define NODE_DATA(nid)		(node_data[(nid)])
  11  
  12  #endif /* CONFIG_NUMA */
  13  #endif /* __ASM_MMZONE_H */
  14 
  ```

  arm linux 属于UMA体系结构，以下是struct pglist_data的定义，从615--622行，可以看出，在UMA体系结构中描述整个内存布局的只有一个单独的pglist_data节点。

  ```c
  // linux-4.14/include/linux/mmzone.h 
  
  615  /*
  616   * On NUMA machines, each NUMA node would have a pg_data_t to describe
  617   * it's memory layout. On UMA machines there is a single pglist_data which
  618   * describes the whole memory.
  619   *
  620   * Memory statistics and page replacement data structures are maintained on a
  621   * per-zone basis.
  622   */
  623  struct bootmem_data;
  624  typedef struct pglist_data {
  625  	struct zone node_zones[MAX_NR_ZONES]; /*内存区域（zone）数组*/
  626  	struct zonelist node_zonelists[MAX_ZONELISTS]; /*备用区域（zone）列表*/
  627  	int nr_zones; /* 该节点包含的内存区域（zone）数量 */
  628  #ifdef CONFIG_FLAT_NODE_MEM_MAP	/* means !SPARSEMEM 非稀疏性内存*/
  629  	struct page *node_mem_map; /* 页描述符数组 */
  630  #ifdef CONFIG_PAGE_EXTENSION
  631  	struct page_ext *node_page_ext; /* 页的扩展属性 */
  632  #endif
  633  #endif
  634  #ifndef CONFIG_NO_BOOTMEM
  635  	struct bootmem_data *bdata; /* 包含引导内存分配器为节点分配内存的所有信息，每个节点都有 一个 struct bootmem_data 数据结构*/
  636  #endif
  637  #ifdef CONFIG_MEMORY_HOTPLUG
  638  	/*
  639  	 * Must be held any time you expect node_start_pfn, node_present_pages
  640  	 * or node_spanned_pages stay constant.  Holding this will also
  641  	 * guarantee that any pfn_valid() stays that way.
  642  	 *
  643  	 * pgdat_resize_lock() and pgdat_resize_unlock() are provided to
  644  	 * manipulate node_size_lock without checking for CONFIG_MEMORY_HOTPLUG.
  645  	 *
  646  	 * Nests above zone->lock and zone->span_seqlock
  647  	 */
  648  	spinlock_t node_size_lock;
  649  #endif
  650  	unsigned long node_start_pfn; /* 该节点的起始物理页号 */
  651  	unsigned long node_present_pages; /* 物理页总数  */
  652  	unsigned long node_spanned_pages; /* 物理页范围的总长度，包括空洞 */
  653  					     
  654  	int node_id; /* 节点标识符，即从0开始的节点号（NID） */
  655  	wait_queue_head_t kswapd_wait; /* 交换守护进程的等待队列 */
  656  	wait_queue_head_t pfmemalloc_wait; /* 直接内存回收中的等待队列 */
  657  	struct task_struct *kswapd;	/* Protected by mem_hotplug_begin/end()，指向该节点的
  658  					               kswapd守护进程，该进程用于释放页面 */
  659  	int kswapd_order;
  660  	enum zone_type kswapd_classzone_idx;
  661  
  662  	int kswapd_failures;		/* Number of 'reclaimed == 0' runs */
  663  
  664  #ifdef CONFIG_COMPACTION
  665  	int kcompactd_max_order;
  666  	enum zone_type kcompactd_classzone_idx;
  667  	wait_queue_head_t kcompactd_wait;
  668  	struct task_struct *kcompactd;
  669  #endif
  670  #ifdef CONFIG_NUMA_BALANCING
  671  	/* Lock serializing the migrate rate limiting window */
  672  	spinlock_t numabalancing_migrate_lock;
  673  
  674  	/* Rate limiting time interval */
  675  	unsigned long numabalancing_migrate_next_window;
  676  
  677  	/* Number of pages migrated during the rate limiting time interval */
  678  	unsigned long numabalancing_migrate_nr_pages;
  679  #endif
  680  	/*
  681  	 * This is a per-node reserve of pages that are not available
  682  	 * to userspace allocations.
  683  	 */
  684  	unsigned long		totalreserve_pages;
  685  
  686  #ifdef CONFIG_NUMA
  687  	/*
  688  	 * zone reclaim becomes active if more unmapped pages exist.
  689  	 */
  690  	unsigned long		min_unmapped_pages;
  691  	unsigned long		min_slab_pages;
  692  #endif /* CONFIG_NUMA */
  693  
  694  	/* Write-intensive fields used by page reclaim */
  695  	ZONE_PADDING(_pad1_)
  696  	spinlock_t		lru_lock;
  697  
  698  #ifdef CONFIG_DEFERRED_STRUCT_PAGE_INIT
  699  	/*
  700  	 * If memory initialisation on large machines is deferred then this
  701  	 * is the first PFN that needs to be initialised.
  702  	 */
  703  	unsigned long first_deferred_pfn;
  704  	/* Number of non-deferred pages */
  705  	unsigned long static_init_pgcnt;
  706  #endif /* CONFIG_DEFERRED_STRUCT_PAGE_INIT */
  707  
  708  #ifdef CONFIG_TRANSPARENT_HUGEPAGE
  709  	spinlock_t split_queue_lock;
  710  	struct list_head split_queue;
  711  	unsigned long split_queue_len;
  712  #endif
  713  
  714  	/* Fields commonly accessed by the page reclaim scanner */
  715  	struct lruvec		lruvec;
  716  
  717  	/*
  718  	 * The target ratio of ACTIVE_ANON to INACTIVE_ANON pages on
  719  	 * this node's LRU.  Maintained by the pageout code.
  720  	 */
  721  	unsigned int inactive_ratio;
  722  
  723  	unsigned long		flags;
  724  
  725  	ZONE_PADDING(_pad2_)
  726  
  727  	/* Per-node vmstats */
  728  	struct per_cpu_nodestat __percpu *per_cpu_nodestats;
  729  	atomic_long_t		vm_stat[NR_VM_NODE_STAT_ITEMS];
  730  } pg_data_t;
  ```

  >   `628    #ifdef CONFIG_FLAT_NODE_MEM_MAP	/* means !SPARSEMEM 非稀疏性内存*/`
  >  `629    struct page *node_mem_map; /* 页描述符数组 */`
  >
  > 1. 在Linux内核中，所有的物理内存都用`struct page`结构体来描述，这些对象以数组形式存放，而这个数组就是mem_map。内存以节点为单位，每个节点下的物理内存统一管理，也就是说，在表示内存节点的描述类型struct pglist_data中，有node_mem_map这个成员，其针对平坦内存（CONFIG_FLAT_NODE_MEM_MAP）进行描述。
  > 2. 每个内存节点下，node_mem_map成员是此节点下所有内存以`struct page`描述后，所有这些对象的基地址，这些对象以数组形式存放。注意：成员node_mem_map可能不是指向数组的第一个元素，因为页描述符数组的大小必须对齐到2^(MAX_ORDER - 1)次方，(MAX_ORDER - 1)是页分配器可分配的最大阶数。
  > 3. 如果系统只有一个pglist_data对象，那么此对象下的node_mem_map即为全局对象mem_map。函数`alloc_node_mem_map()`就是针对节点的node_mem_map的处理。

#### 2.3.2 内存区域 zone

- 内存节点被划分为内存区域（zone），内核定义的区域类型如下：

  ```c
  /* linux-4.14/include/linux/mmzone.h */
  
  302  enum zone_type {
  303  #ifdef CONFIG_ZONE_DMA
  304  	/*
  305  	 * ZONE_DMA is used when there are devices that are not able
  306  	 * to do DMA to all of addressable memory (ZONE_NORMAL). Then we
  307  	 * carve out the portion of memory that is needed for these devices.
  308  	 * The range is arch specific.
  309  	 *
  310  	 * Some examples
  311  	 *
  312  	 * Architecture		Limit
  313  	 * ---------------------------
  314  	 * parisc, ia64, sparc	<4G
  315  	 * s390			<2G
  316  	 * arm			Various
  317  	 * alpha		Unlimited or 0-16MB.
  318  	 *
  319  	 * i386, x86_64 and multiple other arches
  320  	 * 			<16M.
  321  	 */
  322  	ZONE_DMA,
  323  #endif
  324  #ifdef CONFIG_ZONE_DMA32
  325  	/*
  326  	 * x86_64 needs two ZONE_DMAs because it supports devices that are
  327  	 * only able to do DMA to the lower 16M but also 32 bit devices that
  328  	 * can only do DMA areas below 4G.
  329  	 */
  330  	ZONE_DMA32,
  331  #endif
  332  	/*
  333  	 * Normal addressable memory is in ZONE_NORMAL. DMA operations can be
  334  	 * performed on pages in ZONE_NORMAL if the DMA devices support
  335  	 * transfers to all addressable memory.
  336  	 */
  337  	ZONE_NORMAL,
  338  #ifdef CONFIG_HIGHMEM
  339  	/*
  340  	 * A memory area that is only addressable by the kernel through
  341  	 * mapping portions into its own address space. This is for example
  342  	 * used by i386 to allow the kernel to address the memory beyond
  343  	 * 900MB. The kernel will set up special mappings (page
  344  	 * table entries on i386) for each page that the kernel needs to
  345  	 * access.
  346  	 */
  347  	ZONE_HIGHMEM,
  348  #endif
  349  	ZONE_MOVABLE,
  350  #ifdef CONFIG_ZONE_DEVICE
  351  	ZONE_DEVICE,
  352  #endif
  353  	__MAX_NR_ZONES
  354  
  355  };
  ```

  > 1. DMA区域（ZONE_DMA）：DMA是“Direct Memory Access”的缩写，意思是直接内存访问。如果有些设备不能直接访问所有内存，需要使用DMA区域。例如旧的工业标准体系结构（Industry Standard Architecture，ISA）总线只能直接访问16MB以下的内存。
  >
  > 2. DMA32区域（ZONE_DMA32）：64位系统，如果既要支持只能直接访问16MB以下内存的设备，又要支持只能直接访问4GB以下的32位设备，那么必须使用DMA32区域。
  >
  > 3. 普通区域（ZONE_NORMAL）：直接映射到内核虚拟地址空间的内存区域，直译为“普通区域”，意译为“直接映射区域”或“线性映射区域”。内核虚拟地址和物理地址是线性映射关系，即虚拟地址 = （物理地址 + 常量）。是否需要使用页表映射？不同处理器的实现不同，例如ARM处理器需要使用页表映射，而MIPS处理器不需要使用页表映射。
  >
  > 4. 高端内存区域（ZONE_HIGHMEM）：这是32位时代的产物，内核和用户地址空间按1:3划分，内核地址空间只有1GB，不能把1GB以上的内存直接映射到内核地址空间，把不能直接映射的内存划分到高端内存区域。通常把DMA区域、DMA32区域和普通区域统称为低端内存区域。64位系统的内核虚拟地址空间非常大，不再需要高端内存区域。
  >
  > 5. 可移动区域（ZONE_MOVABLE）：它是一个伪内存区域，用来防止内存碎片，后面反碎片技术的章节会具体描述。
  >
  > 6. 设备区域（ZONE_DEVICE）：为支持持久内存（persistent memory）热插拔增加的内存区域。

- 每个内存区域用一个zone结构体描述，其定义如下，主要成员已在代码中做出解释：

  ```c
  /* linux-4.14/include/linux/mmzone.h */
  
  359  struct zone {
  360  	/* Read-mostly fields */
  361  
  362  	/* zone watermarks, access with *_wmark_pages(zone) macros */
  363  	unsigned long watermark[NR_WMARK]; /* 页分配器使用的水位值。每个zone在系统启动时会计算出3个水位值，分别是WMARK_MIN、WMARK_LOW、WMARK_HIGH，这在页面分配器和kswapd页面回收中会用到。 */
  364  
  365  	unsigned long nr_reserved_highatomic;
  366  
  367  	/*
  368  	 * We don't know if the memory that we're going to allocate will be
  369  	 * freeable or/and it will be released eventually, so to avoid totally
  370  	 * wasting several GB of ram we must reserve some of the lower zone
  371  	 * memory (otherwise we risk to run OOM on the lower zones despite
  372  	 * there being tons of freeable ram on the higher zones).  This array is
  373  	 * recalculated at runtime if the sysctl_lowmem_reserve_ratio sysctl
  374  	 * changes.
  375  	 */
  376  	long lowmem_reserve[MAX_NR_ZONES]; /* zone中预留的内存，页分配器使用，当前区域保留多少页不能借给高端内存区域类型 */
  377  
  378  #ifdef CONFIG_NUMA
  379  	int node;
  380  #endif
  381  	struct pglist_data	*zone_pgdat; /* 指向内存节点的pglist_data实例 */
  382  	struct per_cpu_pageset __percpu *pageset; /* 用于维护每个CPU上的一系列页面，以减少自旋锁的争用 */
  383  
  384  #ifndef CONFIG_SPARSEMEM
  385  	/*
  386  	 * Flags for a pageblock_nr_pages block. See pageblock-flags.h.
  387  	 * In SPARSEMEM, this map is stored in struct mem_section
  388  	 */
  389  	unsigned long		*pageblock_flags;
  390  #endif /* CONFIG_SPARSEMEM */
  391  
  392  	/* zone_start_pfn == zone_start_paddr >> PAGE_SHIFT */
  393  	unsigned long		zone_start_pfn; /* 当前区域的起始物理页号 */
  394  
  395  	/*
  396  	 * spanned_pages is the total pages spanned by the zone, including
  397  	 * holes, which is calculated as:
  398  	 * 	spanned_pages = zone_end_pfn - zone_start_pfn;
  399  	 *
  400  	 * present_pages is physical pages existing within the zone, which
  401  	 * is calculated as:
  402  	 *	present_pages = spanned_pages - absent_pages(pages in holes);
  403  	 *
  404  	 * managed_pages is present pages managed by the buddy system, which
  405  	 * is calculated as (reserved_pages includes pages allocated by the
  406  	 * bootmem allocator):
  407  	 *	managed_pages = present_pages - reserved_pages;
  408  	 *
  409  	 * So present_pages may be used by memory hotplug or memory power
  410  	 * management logic to figure out unmanaged pages by checking
  411  	 * (present_pages - managed_pages). And managed_pages should be used
  412  	 * by page allocator and vm scanner to calculate all kinds of watermarks
  413  	 * and thresholds.
  414  	 *
  415  	 * Locking rules:
  416  	 *
  417  	 * zone_start_pfn and spanned_pages are protected by span_seqlock.
  418  	 * It is a seqlock because it has to be read outside of zone->lock,
  419  	 * and it is done in the main allocator path.  But, it is written
  420  	 * quite infrequently.
  421  	 *
  422  	 * The span_seq lock is declared along with zone->lock because it is
  423  	 * frequently read in proximity to zone->lock.  It's good to
  424  	 * give them a chance of being in the same cacheline.
  425  	 *
  426  	 * Write access to present_pages at runtime should be protected by
  427  	 * mem_hotplug_begin/end(). Any reader who can't tolerant drift of
  428  	 * present_pages should get_online_mems() to get a stable value.
  429  	 *
  430  	 * Read access to managed_pages should be safe because it's unsigned
  431  	 * long. Write access to zone->managed_pages and totalram_pages are
  432  	 * protected by managed_page_count_lock at runtime. Idealy only
  433  	 * adjust_managed_page_count() should be used instead of directly
  434  	 * touching zone->managed_pages and totalram_pages.
  435  	 */
  436  	unsigned long		managed_pages; /* 伙伴分配器管理的物理页的数量 */
  437  	unsigned long		spanned_pages; /* 当前区域跨越的总页数，包括空洞 */
  438  	unsigned long		present_pages; /* 当前区域存在的物理页的数量，不包括空洞。对于一些体系结构来说，其值和spanned_pages相等 */
  439  
  440  	const char		*name; /* 区域名称 */
  441  
  442  #ifdef CONFIG_MEMORY_ISOLATION
  443  	/*
  444  	 * Number of isolated pageblock. It is used to solve incorrect
  445  	 * freepage counting problem due to racy retrieving migratetype
  446  	 * of pageblock. Protected by zone->lock.
  447  	 */
  448  	unsigned long		nr_isolate_pageblock;
  449  #endif
  450  
  451  #ifdef CONFIG_MEMORY_HOTPLUG
  452  	/* see spanned/present_pages for more description */
  453  	seqlock_t		span_seqlock;
  454  #endif
  455  
  456  	int initialized;
  457  
  458  	/* Write-intensive fields used from the page allocator */
  459  	ZONE_PADDING(_pad1_)
  460  
  461  	/* free areas of different sizes */
  462  	struct free_area	free_area[MAX_ORDER]; /* 不同长度的空闲区域 */
  463  
  464  	/* zone flags, see below */
  465  	unsigned long		flags;
  466  
  467  	/* Primarily protects free_area */
  468  	spinlock_t		lock; /* 并行访问时用于对当前区域保护的自旋锁 */
  469  
  470  	/* Write-intensive fields used by compaction and vmstats. */
  471  	ZONE_PADDING(_pad2_)
  472  
  473  	/*
  474  	 * When free pages are below this point, additional steps are taken
  475  	 * when reading the number of free pages to avoid per-cpu counter
  476  	 * drift allowing watermarks to be breached
  477  	 */
  478  	unsigned long percpu_drift_mark;
  479  
  480  #if defined CONFIG_COMPACTION || defined CONFIG_CMA
  481  	/* pfn where compaction free scanner should start */
  482  	unsigned long		compact_cached_free_pfn;
  483  	/* pfn where async and sync compaction migration scanner should start */
  484  	unsigned long		compact_cached_migrate_pfn[2];
  485  #endif
  486  
  487  #ifdef CONFIG_COMPACTION
  488  	/*
  489  	 * On compaction failure, 1<<compact_defer_shift compactions
  490  	 * are skipped before trying again. The number attempted since
  491  	 * last failure is tracked with compact_considered.
  492  	 */
  493  	unsigned int		compact_considered;
  494  	unsigned int		compact_defer_shift;
  495  	int			compact_order_failed;
  496  #endif
  497  
  498  #if defined CONFIG_COMPACTION || defined CONFIG_CMA
  499  	/* Set to true when the PG_migrate_skip bits should be cleared */
  500  	bool			compact_blockskip_flush;
  501  #endif
  502  
  503  	bool			contiguous;
  504  
  505  	ZONE_PADDING(_pad3_)
  506  	/* Zone statistics */
  507  	atomic_long_t		vm_stat[NR_VM_ZONE_STAT_ITEMS];
  508  	atomic_long_t		vm_numa_stat[NR_VM_NUMA_STAT_ITEMS];
  509  } ____cacheline_internodealigned_in_smp;
  ```

- 当页表的初始化（页表创建和映射）完成之后，内核就可以对内存进行管理了，但是内核并不是统一对待这些页面，而是采用区域（也有称为区块）zone 的方式来管理。

- struct zone 是经常会被访问到的，因此这个数据结构要求以 L1 cache 对齐。另外，这里的 ZONE_PADDING() 是让 zone -> lock 和 zone -> lru_lock 这两个很热门的锁可以分布在不同的 cache line 中。一个内存节点最多也就几个 zone，因此 zone 数据结构不需要像 struct page 一样关注数据结构的大小，因此这里 ZONE_PADDING() 可以为了性能而浪费空间。

- 在内存管理开发过程中，内核开发者逐步发现一些自旋锁会竞争的非常厉害，很难获取。像 zone -> lock 和 zone -> lru_lock 这两个锁有时需要同时获取锁，因此保证它们使用不同的 cache line 是内核常用的一种优化技巧。




#### 2.3.3 zone初始化

- zone 的初始化函数集中在 `bootmem_init()`中完成，所以需要确定每个 zone 的范围。函数调用关系：`start_kernel() -> setup_arch() -> paging_init() -> bootmem_init()`，我们从bootmem_init() 函数定义开始解析：

```c
[linux-4.14/arch/arm/mm/init.c]
93  static void __init find_limits(unsigned long *min, unsigned long *max_low,
94  			       unsigned long *max_high)
95  {
96  	*max_low = PFN_DOWN(memblock_get_current_limit());
97  	*min = PFN_UP(memblock_start_of_DRAM());
98  	*max_high = PFN_DOWN(memblock_end_of_DRAM());
99  }

[linux-4.14/arch/arm/mm/init.c]
303  void __init bootmem_init(void)
304  {
305  	unsigned long min, max_low, max_high;
306  	/* memblock_allow_resize 设置memblock_can_resize = 1 */
307  	memblock_allow_resize();
308  	max_low = max_high = 0;
309  	/* find_limits()函数计算出min、max_low、max_high，后面会将这三个值分布赋值给			
		 * min_low_pfn、max_low_pfn、max_pfn，其中 min_low_pfn 是内存块的开始地址的页帧号
		 * （arm32架构下，该值为 0x60000）, max_low_pfn（0x8f800）表示 normal 区域的结束页帧
		 * 号，它由 arm_lowmem_init 这个变量得来，max_pfn（0xa0000）是内存块的结束地址的页帧号。
		 */
310  	find_limits(&min, &max_low, &max_high);
311  
312  	early_memtest((phys_addr_t)min << PAGE_SHIFT,
313  		      (phys_addr_t)max_low << PAGE_SHIFT);
314  
315  	/*
316  	 * Sparsemem tries to allocate bootmem in memory_present(),
317  	 * so must be done after the fixed reservations
318  	 */
    	/* arm 平台下，该函数什么也不做 */
319  	arm_memory_present();
320  
321  	/*
322  	 * sparse_init() needs the bootmem allocator up and running.
323  	 */
    	/* 对非线性内存的映射，这里与zone初始化关系不大，暂不做分析 */
324  	sparse_init();
325  
326  	/*
327  	 * Now free the memory - free_area_init_node needs
328  	 * the sparse mem_map arrays initialized by sparse_init()
329  	 * for memmap_init_zone(), otherwise all PFNs are invalid.
330  	 */
    	/*
    	* zone 初始化主要在 zone_sizes_init() 函数内完成
    	*/
331  	zone_sizes_init(min, max_low, max_high);
332  
333  	/*
334  	 * This doesn't seem to be used by the Linux memory manager any
335  	 * more, but is used by ll_rw_block.  If we can get rid of it, we
336  	 * also get rid of some of the stuff above as well.
337  	 */
338  	min_low_pfn = min;
339  	max_low_pfn = max_low;
340  	max_pfn = max_high;
341  }
```

- zone_sizes_init() 函数定义及解析如下：

``` c
[linux-4.14/include/generated/bounds.h]
10  #define MAX_NR_ZONES 3 /* __MAX_NR_ZONES */

[linux-4.14/arch/arm/mm/init.c]
140  static void __init zone_sizes_init(unsigned long min, unsigned long max_low,
141  	unsigned long max_high)
142  {
    	/* MAX_NR_ZONES指定节点包含的zone数量，如前面定义，此处 MAX_NR_ZONES 值为3 */
143  	unsigned long zone_size[MAX_NR_ZONES], zhole_size[MAX_NR_ZONES];
144  	struct memblock_region *reg;
145  
146  	/*
147  	 * initialise the zones.
148  	 */
149  	memset(zone_size, 0, sizeof(zone_size));
150  
151  	/*
152  	 * The memory size has already been determined.  If we need
153  	 * to do anything fancy with the allocation of this memory
154  	 * to the zones, now is the time to do it.
155  	 */
156  	zone_size[0] = max_low - min;
157  #ifdef CONFIG_HIGHMEM
158  	zone_size[ZONE_HIGHMEM] = max_high - max_low;
159  #endif
160  
161  	/*
162  	 * Calculate the size of the holes.
163  	 *  holes = node_size - sum(bank_sizes)
164  	 */
165  	memcpy(zhole_size, zone_size, sizeof(zhole_size));
166  	for_each_memblock(memory, reg) {
167  		unsigned long start = memblock_region_memory_base_pfn(reg);
168  		unsigned long end = memblock_region_memory_end_pfn(reg);
169  
170  		if (start < max_low) {
171  			unsigned long low_end = min(end, max_low);
172  			zhole_size[0] -= low_end - start;
173  		}
174  #ifdef CONFIG_HIGHMEM
175  		if (end > max_low) {
176  			unsigned long high_start = max(start, max_low);
177  			zhole_size[ZONE_HIGHMEM] -= end - high_start;
178  		}
179  #endif
180  	}
181  
182  #ifdef CONFIG_ZONE_DMA
183  	/*
184  	 * Adjust the sizes according to any special requirements for
185  	 * this machine type.
186  	 */
187  	if (arm_dma_zone_size)
188  		arm_adjust_dma_zone(zone_size, zhole_size,
189  			arm_dma_zone_size >> PAGE_SHIFT);
190  #endif
191  
192  	free_area_init_node(0, zone_size, min, zhole_size);
193  }
```





#### 2.3.4 物理页 page

- 每个物理页对应一个page结构体，称为页描述符，内存节点的pglist_data实例的成员node_mem_map指向给内存节点包含的所有物理页的页描述符组成的数组。

- Linux内核内存管理的实现以struct page为核心，其他所有的内存管理设施都为之展开，例如VMA管理、缺页中断、反向映射、页面分配与回收等。

- 因为物理页的数量很大，所以咋page结构体中增加1个成员，可能导致所有的page实例占用的内存大幅增加。为了减少内存消耗，内核努力使page结构体尽可能小，对于不会同时生效的成员，使用联合体，这种做法带来的负面影响是page结构体的可读性差。

- struct page数据结构

    ```c
    /* linux-4.14/include/linux/mm_types.h */
    
    29  /*
    30   * Each physical page in the system has a struct page associated with
    31   * it to keep track of whatever it is we are using the page for at the
    32   * moment. Note that we have no way to track which tasks are using
    33   * a page, though if it is a pagecache page, rmap structures can tell us
    34   * who is mapping it.
    35   *
    36   * The objects in struct page are organized in double word blocks in
    37   * order to allows us to use atomic double word operations on portions
    38   * of struct page. That is currently only used by slub but the arrangement
    39   * allows the use of atomic double word operations on the flags/mapping
    40   * and lru list pointers also.
    41   */
    42  struct page {
    43  	/* First double word block */
    44  	unsigned long flags;		/* Atomic flags, some possibly
    45  					 * updated asynchronously */
    46  	union {
    47  		struct address_space *mapping;	/* If low bit clear, points to
    48  						 * inode address_space, or NULL.
    49  						 * If page mapped as anonymous
    50  						 * memory, low bit is set, and
    51  						 * it points to anon_vma object:
    52  						 * see PAGE_MAPPING_ANON below.
    53  						 */
    54  		void *s_mem;			/* slab first object */
    55  		atomic_t compound_mapcount;	/* first tail page */
    56  		/* page_deferred_list().next	 -- second tail page */
    57  	};
    58  
    59  	/* Second double word */
    60  	union {
    61  		pgoff_t index;		/* Our offset within mapping. */
    62  		void *freelist;		/* sl[aou]b first free object */
    63  		/* page_deferred_list().prev	-- second tail page */
    64  	};
    65  
    66  	union {
    67  #if defined(CONFIG_HAVE_CMPXCHG_DOUBLE) && \
    68  	defined(CONFIG_HAVE_ALIGNED_STRUCT_PAGE)
    69  		/* Used for cmpxchg_double in slub */
    70  		unsigned long counters;
    71  #else
    72  		/*
    73  		 * Keep _refcount separate from slub cmpxchg_double data.
    74  		 * As the rest of the double word is protected by slab_lock
    75  		 * but _refcount is not.
    76  		 */
    77  		unsigned counters;
    78  #endif
    79  		struct {
    80  
    81  			union {
    82  				/*
    83  				 * Count of ptes mapped in mms, to show when
    84  				 * page is mapped & limit reverse map searches.
    85  				 *
    86  				 * Extra information about page type may be
    87  				 * stored here for pages that are never mapped,
    88  				 * in which case the value MUST BE <= -2.
    89  				 * See page-flags.h for more details.
    90  				 */
    91  				atomic_t _mapcount;
    92  
    93  				unsigned int active;		/* SLAB */
    94  				struct {			/* SLUB */
    95  					unsigned inuse:16;
    96  					unsigned objects:15;
    97  					unsigned frozen:1;
    98  				};
    99  				int units;			/* SLOB */
    100  			};
    101  			/*
    102  			 * Usage count, *USE WRAPPER FUNCTION* when manual
    103  			 * accounting. See page_ref.h
    104  			 */
    105  			atomic_t _refcount;
    106  		};
    107  	};
    108  
    109  	/*
    110  	 * Third double word block
    111  	 *
    112  	 * WARNING: bit 0 of the first word encode PageTail(). That means
    113  	 * the rest users of the storage space MUST NOT use the bit to
    114  	 * avoid collision and false-positive PageTail().
    115  	 */
    116  	union {
    117  		struct list_head lru;	/* Pageout list, eg. active_list
    118  					 * protected by zone_lru_lock !
    119  					 * Can be used as a generic list
    120  					 * by the page owner.
    121  					 */
    122  		struct dev_pagemap *pgmap; /* ZONE_DEVICE pages are never on an
    123  					    * lru or handled by a slab
    124  					    * allocator, this points to the
    125  					    * hosting device page map.
    126  					    */
    127  		struct {		/* slub per cpu partial pages */
    128  			struct page *next;	/* Next partial slab */
    129  #ifdef CONFIG_64BIT
    130  			int pages;	/* Nr of partial slabs left */
    131  			int pobjects;	/* Approximate # of objects */
    132  #else
    133  			short int pages;
    134  			short int pobjects;
    135  #endif
    136  		};
    137  
    138  		struct rcu_head rcu_head;	/* Used by SLAB
    139  						 * when destroying via RCU
    140  						 */
    141  		/* Tail pages of compound page */
    142  		struct {
    143  			unsigned long compound_head; /* If bit zero is set */
    144  
    145  			/* First tail page only */
    146  #ifdef CONFIG_64BIT
    147  			/*
    148  			 * On 64 bit system we have enough space in struct page
    149  			 * to encode compound_dtor and compound_order with
    150  			 * unsigned int. It can help compiler generate better or
    151  			 * smaller code on some archtectures.
    152  			 */
    153  			unsigned int compound_dtor;
    154  			unsigned int compound_order;
    155  #else
    156  			unsigned short int compound_dtor;
    157  			unsigned short int compound_order;
    158  #endif
    159  		};
    160  
    161  #if defined(CONFIG_TRANSPARENT_HUGEPAGE) && USE_SPLIT_PMD_PTLOCKS
    162  		struct {
    163  			unsigned long __pad;	/* do not overlay pmd_huge_pte
    164  						 * with compound_head to avoid
    165  						 * possible bit 0 collision.
    166  						 */
    167  			pgtable_t pmd_huge_pte; /* protected by page->ptl */
    168  		};
    169  #endif
    170  	};
    171  
    172  	/* Remainder is not double word aligned */
    173  	union {
    174  		unsigned long private;		/* Mapping-private opaque data:
    175  					 	 * usually used for buffer_heads
    176  						 * if PagePrivate set; used for
    177  						 * swp_entry_t if PageSwapCache;
    178  						 * indicates order in the buddy
    179  						 * system if PG_buddy is set.
    180  						 */
    181  #if USE_SPLIT_PTE_PTLOCKS
    182  #if ALLOC_SPLIT_PTLOCKS
    183  		spinlock_t *ptl;
    184  #else
    185  		spinlock_t ptl;
    186  #endif
    187  #endif
    188  		struct kmem_cache *slab_cache;	/* SL[AU]B: Pointer to slab */
    189  	};
    190  
    191  #ifdef CONFIG_MEMCG
    192  	struct mem_cgroup *mem_cgroup;
    193  #endif
    194  
    195  	/*
    196  	 * On machines where all RAM is mapped into kernel address space,
    197  	 * we can simply calculate the virtual address. On machines with
    198  	 * highmem some memory is mapped into kernel virtual memory
    199  	 * dynamically, so we need a place to store that address.
    200  	 * Note that this field could be 16 bits on x86 ... ;)
    201  	 *
    202  	 * Architectures with slow multiplication can define
    203  	 * WANT_PAGE_VIRTUAL in asm/page.h
    204  	 */
    205  #if defined(WANT_PAGE_VIRTUAL)
    206  	void *virtual;			/* Kernel virtual address (NULL if
    207  					   not kmapped, ie. highmem) */
    208  #endif /* WANT_PAGE_VIRTUAL */
    209  
    210  #ifdef LAST_CPUPID_NOT_IN_PAGE_FLAGS
    211  	int _last_cpupid;
    212  #endif
    213  }
    ```

    下面分别解析其主要成员的意义：
    
    > flags
    
    ```c
    /* linux-4.14/include/linux/mm_types.h */
    44  	unsigned long flags;		/* Atomic flags, some possibly
    45  					 * updated asynchronously */
    ```

    1. 结构体page的成员flags的布局如下：
    
       ```
       | [SECTION] | [NODE] | ZONE | [LAST_CPUPID] | ... | FLAGS |
       ```
    
       ​       其中，SECTION是稀疏内存模型中的段编号，NODE是节点编号，ZONE是区域类型，FLAGS是该页面的标志位。
    
       ​       而具体存放的内容与内核配置相关，例如SECTION编号和NODE节点编号与CONFIG_SPARSEMEM / CONFIG_SPARSEMEM_VMEMMAP配置相关，LAST_CPUID与CONFIG_NUMA_BALANCING配置相关。
    
       ​       内联函数 page_to_nid 用来得到物理页所属的内存节点的编号，page_zonenum 用来得到物理页所属的内存区域的类型。两个函数内部具体的宏定义此处不再详述。
    
       ```c
       /* linux-4.14/include/linux/mm.h */
   
       900  static inline int page_to_nid(const struct page *page)
       901  {
       902  	return (page->flags >> NODES_PGSHIFT) & NODES_MASK;
       903  }
   
       788  static inline enum zone_type page_zonenum(const struct page *page)
       789  {
       790  	return (page->flags >> ZONES_PGSHIFT) & ZONES_MASK;
       791  }
   
       ```
    
       
    
    2. 标志位是内存管理非常重要的部分，具体定义如下：
    
       ```c
       /* linux-4.14/include/linux/page-flags.h */
       
       75  enum pageflags {
       76  	PG_locked, /* 表示该页面已经上锁。如果该比特位置位，说明页面已经被锁定，内存管理的其他模块不能访问这个页面，以防发生竞争 */
       77  	PG_error, /* 表示页面操作过程中发生错误时会设置该位 */
       78  	PG_referenced, /* 控制页面的活跃程度，该标志位用来实现LRU算法中的第二次机会法，详见后续页面回收章节 */
       79  	PG_uptodate, /* 表示页面的内容是有效的，当该页面上的读操作完成后，设置该标志位 */
       80  	PG_dirty, /* 表示该页面被修改过，为脏页，即页面的内容被改写后还没有和外部存储器进行过同步操作 */
       81  	PG_lru, /* 表示该页加入了LRU链表中。LRU是最近最少使用链表（least recently used）的简称。内核使用LRU链表来管理活跃和不活跃页面。 */
       82  	PG_active, /* 表示该页在活跃LRU链表中 */
       83  	PG_waiters,		/* Page has waiters, check its waitqueue. Must be bit #7 and in the same byte as "PG_locked" */
       84  	PG_slab, /* 表示该页用于slab分配器 */
       85  	PG_owner_priv_1,	/* Owner use. If pagecache, fs may use*/
       86  	PG_arch_1, /* 与体系结构相关的页面状态位 */
       87  	PG_reserved, /* 表示该页不可被换出 */
       88  	PG_private,		/* If pagecache, has fs-private data */
       89  	PG_private_2,		/* If pagecache, has fs aux data */
       90  	PG_writeback,		/* Page is under writeback，表示页面正在向块设备进行回写 */
       91  	PG_head,		/* A head page */
       92  	PG_mappedtodisk,	/* Has blocks allocated on-disk，在磁盘中分配了block */
       93  	PG_reclaim,		/* To be reclaimed asap，马上要被回收了 */
       94  	PG_swapbacked,		/* Page is backed by RAM/swap，表示页面处于交换缓存 */
       95  	PG_unevictable,		/* Page is "unevictable"， 表示页面是不可回收的*/
       96  #ifdef CONFIG_MMU
       97  	PG_mlocked,		/* Page is vma mlocked，表示页面对应的VMA处于mlocked状态 */
       98  #endif
       99  #ifdef CONFIG_ARCH_USES_PG_UNCACHED
       100  	PG_uncached,		/* Page has been mapped as uncached */
       101  #endif
       102  #ifdef CONFIG_MEMORY_FAILURE
       103  	PG_hwpoison,		/* hardware poisoned page. Don't touch */
       104  #endif
       105  #if defined(CONFIG_IDLE_PAGE_TRACKING) && defined(CONFIG_64BIT)
       106  	PG_young,
       107  	PG_idle,
       108  #endif
       109  	__NR_PAGEFLAGS,
       110  
       111  	/* Filesystems */
       112  	PG_checked = PG_owner_priv_1,
       113  
       114  	/* SwapBacked */
       115  	PG_swapcache = PG_owner_priv_1,	/* Swap page: swp_entry_t in private */
       116  
       117  	/* Two page bits are conscripted by FS-Cache to maintain local caching
       118  	 * state.  These bits are set on pages belonging to the netfs's inodes
       119  	 * when those inodes are being locally cached.
       120  	 */
       121  	PG_fscache = PG_private_2,	/* page backed by cache */
       122  
       123  	/* XEN */
       124  	/* Pinned in Xen as a read-only pagetable page. */
       125  	PG_pinned = PG_owner_priv_1,
       126  	/* Pinned as part of domain save (see xen_mm_pin_all()). */
       127  	PG_savepinned = PG_dirty,
       128  	/* Has a grant mapping of another (foreign) domain's page. */
       129  	PG_foreign = PG_owner_priv_1,
       130  
       131  	/* SLOB */
       132  	PG_slob_free = PG_private,
       133  
       134  	/* Compound pages. Stored in first tail page's flags */
       135  	PG_double_map = PG_private_2,
       136  
       137  	/* non-lru isolated movable page */
       138  	PG_isolated = PG_reclaim,
       139  };
       ```
    
       ​       内核定义了一些标准宏，用于检查页面是否设置了某个特定的标志位或者用于操作某些标志位。这些宏的名称都有一定的模式，具体如下：
       
       > - PageXXX()用于检查页面是否设置了 PG_XXX 标志位。例如，PageLRU(page)检查PG_lru标志位是否置位了，PageDirty(page)检查PG_dirty标志位是否置位了。
       >
       > - SetPageXXX()设置页中的 PG_XXX 标志位。例如，SetPageLRU(page)用于设置PG_lru，SetPageDirty(page)用于设置PG_dirty标志位。
       > - ClearPageXXX()用于无条件地清楚某个特定的标志位。
       >
       
       ​        
       
       宏的实现在`linux-4.14/include/linux/page-flags.h`文件中，如下：
       
       ```c
       /* linux-4.14/include/linux/page-flags.h */
       
       196  /*
       197   * Macros to create function definitions for page flags
       198   */
       199  #define TESTPAGEFLAG(uname, lname, policy)				\
       200  static __always_inline int Page##uname(struct page *page)		\
       201  	{ return test_bit(PG_##lname, &policy(page, 0)->flags); }
       202  
       203  #define SETPAGEFLAG(uname, lname, policy)				\
       204  static __always_inline void SetPage##uname(struct page *page)		\
       205  	{ set_bit(PG_##lname, &policy(page, 1)->flags); }
       206  
       207  #define CLEARPAGEFLAG(uname, lname, policy)				\
       208  static __always_inline void ClearPage##uname(struct page *page)		\
       209  	{ clear_bit(PG_##lname, &policy(page, 1)->flags); }
       210  
       ```
       
       
    > mapping
    
    ```c
    /* linux-4.14/include/linux/mm_types.h */
    
    47  		struct address_space *mapping;	/* If low bit clear, points to
    48  						 * inode address_space, or NULL.
    49  						 * If page mapped as anonymous
    50  						 * memory, low bit is set, and
    51  						 * it points to anon_vma object:
    52  						 * see PAGE_MAPPING_ANON below.
    53  						 */
    ```
    
    - struct page 数据结构中的mapping成员表示页面所指向的地址空间（address_space）。内核中的地址空间通常有两个不同的地址空间，一个用于文件映射页面，例如在读取文件时，地址空间用于将文件的内容数据与装载数据的存储介质区关联起来；另一个用于匿名映射。内核使用了一个简单直接的方式实现了“一个指针，两种用途”，mapping指针地址的最低位用于判断是否指向匿名映射或KSM页面的地址空间，如果是匿名映射，那么mapping指向匿名页面的地址空间数据结构struct anon_vma。
    
      ```c
      394  #define PAGE_MAPPING_ANON	0x1
      395  #define PAGE_MAPPING_MOVABLE	0x2
      396  #define PAGE_MAPPING_KSM	(PAGE_MAPPING_ANON | PAGE_MAPPING_MOVABLE)
      397  #define PAGE_MAPPING_FLAGS	(PAGE_MAPPING_ANON | PAGE_MAPPING_MOVABLE)
      398  
      ...
      403  
      404  static __always_inline int PageAnon(struct page *page)
      405  {
      406  	page = compound_head(page);
      407  	return ((unsigned long)page->mapping & PAGE_MAPPING_ANON) != 0;
      408  }
      ```
    
    > s_mem
    
    ```c
    /* linux-4.14/include/linux/mm_types.h */
    
    54  		void *s_mem;			/* slab first object */
    ```
    
    - struct page 数据结构中的s_mem用于slab分配器，slab中第一个对象的开始地址，s_mem和mapping共同占用一个字节的存储空间。
    
    > Second double word
    
    ```c
    /* linux-4.14/include/linux/mm_types.h */
    
    59  	/* Second double word */
    60  	union {
    61  		pgoff_t index;		/* Our offset within mapping. */
    62  		void *freelist;		/* sl[aou]b first free object */
    63  		/* page_deferred_list().prev	-- second tail page */
    64  	};
    65  
    66  	union {
    67  #if defined(CONFIG_HAVE_CMPXCHG_DOUBLE) && \
    68  	defined(CONFIG_HAVE_ALIGNED_STRUCT_PAGE)
    69  		/* Used for cmpxchg_double in slub */
    70  		unsigned long counters;
    71  #else
    72  		/*
    73  		 * Keep _refcount separate from slub cmpxchg_double data.
    74  		 * As the rest of the double word is protected by slab_lock
    75  		 * but _refcount is not.
    76  		 */
    77  		unsigned counters;
    78  #endif
    79  		struct {
    80  
    81  			union {
    82  				/*
    83  				 * Count of ptes mapped in mms, to show when
    84  				 * page is mapped & limit reverse map searches.
    85  				 *
    86  				 * Extra information about page type may be
    87  				 * stored here for pages that are never mapped,
    88  				 * in which case the value MUST BE <= -2.
    89  				 * See page-flags.h for more details.
    90  				 */
    91  				atomic_t _mapcount;
    92  
    93  				unsigned int active;		/* SLAB */
    94  				struct {			/* SLUB */
    95  					unsigned inuse:16;
    96  					unsigned objects:15;
    97  					unsigned frozen:1;
    98  				};
    99  				int units;			/* SLOB */
    100  			};
    101  			/*
    102  			 * Usage count, *USE WRAPPER FUNCTION* when manual
    103  			 * accounting. See page_ref.h
    104  			 */
    105  			atomic_t _refcount;
    106  		};
    107  	};
    ```
    
    - 第二个双字由两个联合体组成。index表示这个页面在一个映射中的序号和偏移量；freelist用于slab分配器；_mapcount和_refcount是两个非常重要的引用计数。
    
    > Third double word block
    
    ```c
    /* linux-4.14/include/linux/mm_types.h */
    
    109  	/*
    110  	 * Third double word block
    111  	 *
    112  	 * WARNING: bit 0 of the first word encode PageTail(). That means
    113  	 * the rest users of the storage space MUST NOT use the bit to
    114  	 * avoid collision and false-positive PageTail().
    115  	 */
    116  	union {
    117  		struct list_head lru;	/* Pageout list, eg. active_list
    118  					 * protected by zone_lru_lock !
    119  					 * Can be used as a generic list
    120  					 * by the page owner.
    121  					 */
    122  		struct dev_pagemap *pgmap; /* ZONE_DEVICE pages are never on an
    123  					    * lru or handled by a slab
    124  					    * allocator, this points to the
    125  					    * hosting device page map.
    126  					    */
    127  		struct {		/* slub per cpu partial pages */
    128  			struct page *next;	/* Next partial slab */
    129  #ifdef CONFIG_64BIT
    130  			int pages;	/* Nr of partial slabs left */
    131  			int pobjects;	/* Approximate # of objects */
    132  #else
    133  			short int pages;
    134  			short int pobjects;
    135  #endif
    136  		};
    137  
    138  		struct rcu_head rcu_head;	/* Used by SLAB
    139  						 * when destroying via RCU
    140  						 */
    141  		/* Tail pages of compound page */
    142  		struct {
    143  			unsigned long compound_head; /* If bit zero is set */
    144  
    145  			/* First tail page only */
    146  #ifdef CONFIG_64BIT
    147  			/*
    148  			 * On 64 bit system we have enough space in struct page
    149  			 * to encode compound_dtor and compound_order with
    150  			 * unsigned int. It can help compiler generate better or
    151  			 * smaller code on some archtectures.
    152  			 */
    153  			unsigned int compound_dtor;
    154  			unsigned int compound_order;
    155  #else
    156  			unsigned short int compound_dtor;
    157  			unsigned short int compound_order;
    158  #endif
    159  		};
    160  
    161  #if defined(CONFIG_TRANSPARENT_HUGEPAGE) && USE_SPLIT_PMD_PTLOCKS
    162  		struct {
    163  			unsigned long __pad;	/* do not overlay pmd_huge_pte
    164  						 * with compound_head to avoid
    165  						 * possible bit 0 collision.
    166  						 */
    167  			pgtable_t pmd_huge_pte; /* protected by page->ptl */
    168  		};
    169  #endif
    170  	};
    ```
    
    - lru用于页面加入和删除LRU链表，其余一些成员用于slab或slub分配器

