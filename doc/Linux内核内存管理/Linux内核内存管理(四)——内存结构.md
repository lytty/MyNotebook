# Linux内核内存管理(四)——内存结构

## 1. 物理地址空间

### 1.1 物理地址空间介绍

- 物理地址是处理器在系统总线上看到的地址。使用精简指令集（RISC）的处理器通常只实现一个物理地址空间，外围设备和物理内存使用统一的物理地址空间，处理器可以像访问内存单元一样访问外围设备。有些设备把分配给外围设备的物理地址区域成为设备内存。

- 处理器通过外围设备控制器的寄存器访问外围设备，寄存器分为控制寄存器、状态寄存器和数据寄存器三大类。外围设备的寄存器通常被连续地编址。处理器对外围设备寄存器的编址方式有两种：

1.  I/O映射方式（I/O-mapped）：英特尔的`x86`处理器为外围设备专门实现了一个单独的地址空间，称为“I/O地址空间”或“I/O端口空间”，处理器通过专门的I/O指令来访问这一空间中的地址单元。
2.  内存映射方式（memory-mapped）：使用精简指令集（RISC）的处理器对外围设备寄存器的编址通常使用这一方式。

- 程序只能通过虚拟地址访问外设寄存器。



### 1.2 ARM64架构实现

- ARM64架构定义了两种内存类型：

1.   正常内存（Normal Memory）：包括物理内存和只读存储器（ROM）。
2.   设备内存（Device Memory）：指分配给外围设备寄存器的物理地址区域。

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

1.  非一致内存访问（Non-Uniform Memory Access，NUMA）：只内存被划分成多个内存节点的多处理器系统，访问一个内存节点花费的时间取决于处理器和内存节点的距离。每个处理器有一个本地内存节点，处理器访问本地内存节点的速度比访问其他内存节点的速度快。NUMA是中高端服务器的主流体系结构。
2.  对称多处理器（Symmetry Multi-Processor，SMP）：即一致内存访问（Uniform Memory Access，UMA），所有处理器访问内存花费的时间是相同的。每个处理器的地位是平等的，仅在内核初始化的时候不平等：“0号处理器作为引导处理器负责初始化内核，其他处理器等待内核初始化完成。”

- 在实际应用中可以采用混合体系结构，在NUMA节点内部使用SMP体系结构。



### 2.2 内存模型

- 内存模型是从处理器的角度看到的物理内存分布情况，内核管理不同内存模型的方式存在差异。内存管理子系统支持3种内存模型：

1.  平坦内存（Flat Memory）：内存的物理地址空间是连续的，没有空洞。
2.  不连续内存（Discontiguous Memory）：内存的物理地址空间存在空洞，这种模型可以高效地处理空洞。
3.  稀疏内存（Sparse Memory）：内存的物理地址空间存在空洞。如果要支持内存插拔，只能选择稀疏内存模型。

- 当系统包含多块物理内存，两块物理内存之间就存在空洞。一块内存的物理地址空间也可能存在空洞，可以查看处理器的参考手册获取分配给内存的物理地址空间。
- 如果内存的物理地址空间是连续的，不连续的内存模型会产生额外的开销，降低性能，所以平坦内存模型是更好的选择。
- 如果内存的物理地址空间存在空洞，可选择不连续内存模型，因为平坦内存模型会为空洞分配page结构体，浪费内存；稀疏内存模型是实验性的，尽量不要选择稀疏内存模型，除非内存的物理地址空间很稀疏，或者要支持内存热插拔；相比于平坦内存模型和稀疏内存模型，不连续内存模型对空洞做了优化处理，不会为空洞分配page结构体。



### 2.3 三级结构

- 内存管理子系统使用节点（node）、区域（也有称为区块、管理区的）（zone）和页（page）三级结构描述物理内存。

#### 2.3.1 内存节点 node

- 内存节点分两种情况：

1.  NUMA系统的内存节点，根据处理器和内存的距离划分。
2.  在具有不连续内存的UMA系统中，表示比区域（zone）的级别更高的内存区域，根据物理地址是否连续划分，每块物理地址连续的内存是一个内存节点。

- 内存中的每个节点都由 pg_data_t 描述，而 pg_data_t 由 struct pglist_data 结构体定义。内核定义了宏NODE_DATA（nid），用它来获取节点的pglist_data实例。对于平坦内存模型，只有一个pglist_data实例：contig_page_data。

```c
// linux-4.14/arch/arm64/include/asm/mmzone.h

/* SPDX-License-Identifier: GPL-2.0 */
#ifndef __ASM_MMZONE_H
#define __ASM_MMZONE_H

#ifdef CONFIG_NUMA

#include <asm/numa.h>

extern struct pglist_data *node_data[];
#define NODE_DATA(nid)		(node_data[(nid)])

#endif /* CONFIG_NUMA */
#endif /* __ASM_MMZONE_H */

```

arm linux 属于UMA体系结构，以下是struct pglist_data的定义，从615--622行，可以看出，在UMA体系结构中描述整个内存布局的只有一个单独的pglist_data节点。

```c
// linux-4.14/include/linux/mmzone.h

/*
 * On NUMA machines, each NUMA node would have a pg_data_t to describe
 * it's memory layout. On UMA machines there is a single pglist_data which
 * describes the whole memory.
 *
 * Memory statistics and page replacement data structures are maintained on a
 * per-zone basis.
 */
struct bootmem_data;
typedef struct pglist_data {
	struct zone node_zones[MAX_NR_ZONES]; /*内存区域（zone）数组*/
	struct zonelist node_zonelists[MAX_ZONELISTS]; /*备用区域（zone）列表*/
	int nr_zones; /* 该节点包含的内存区域（zone）数量 */
#ifdef CONFIG_FLAT_NODE_MEM_MAP	/* means !SPARSEMEM 非稀疏性内存*/
	struct page *node_mem_map; /* 页描述符数组 */
#ifdef CONFIG_PAGE_EXTENSION
	struct page_ext *node_page_ext; /* 页的扩展属性 */
#endif
#endif
#ifndef CONFIG_NO_BOOTMEM
	struct bootmem_data *bdata; /* 包含引导内存分配器为节点分配内存的所有信息，每个节点都有 一个 struct bootmem_data 数据结构*/
#endif
#ifdef CONFIG_MEMORY_HOTPLUG
	/*
	 * Must be held any time you expect node_start_pfn, node_present_pages
	 * or node_spanned_pages stay constant.  Holding this will also
	 * guarantee that any pfn_valid() stays that way.
	 *
	 * pgdat_resize_lock() and pgdat_resize_unlock() are provided to
	 * manipulate node_size_lock without checking for CONFIG_MEMORY_HOTPLUG.
	 *
	 * Nests above zone->lock and zone->span_seqlock
	 */
	spinlock_t node_size_lock;
#endif
	unsigned long node_start_pfn; /* 该节点的起始物理页号 */
	unsigned long node_present_pages; /* 物理页总数  */
	unsigned long node_spanned_pages; /* 物理页范围的总长度，包括空洞 */
					     
	int node_id; /* 节点标识符，即从0开始的节点号（NID） */
	wait_queue_head_t kswapd_wait; /* 交换守护进程的等待队列 */
	wait_queue_head_t pfmemalloc_wait; /* 直接内存回收中的等待队列 */
	struct task_struct *kswapd;	/* Protected by mem_hotplug_begin/end()，指向该节点的
					               kswapd守护进程，该进程用于释放页面 */
	int kswapd_order;
	enum zone_type kswapd_classzone_idx;

	int kswapd_failures;		/* Number of 'reclaimed == 0' runs */

#ifdef CONFIG_COMPACTION
	int kcompactd_max_order;
	enum zone_type kcompactd_classzone_idx;
	wait_queue_head_t kcompactd_wait;
	struct task_struct *kcompactd;
#endif
#ifdef CONFIG_NUMA_BALANCING
	/* Lock serializing the migrate rate limiting window */
	spinlock_t numabalancing_migrate_lock;

	/* Rate limiting time interval */
	unsigned long numabalancing_migrate_next_window;

	/* Number of pages migrated during the rate limiting time interval */
	unsigned long numabalancing_migrate_nr_pages;
#endif
	/*
	 * This is a per-node reserve of pages that are not available
	 * to userspace allocations.
	 */
	unsigned long		totalreserve_pages;

#ifdef CONFIG_NUMA
	/*
	 * zone reclaim becomes active if more unmapped pages exist.
	 */
	unsigned long		min_unmapped_pages;
	unsigned long		min_slab_pages;
#endif /* CONFIG_NUMA */

	/* Write-intensive fields used by page reclaim */
	ZONE_PADDING(_pad1_)
	spinlock_t		lru_lock;

#ifdef CONFIG_DEFERRED_STRUCT_PAGE_INIT
	/*
	 * If memory initialisation on large machines is deferred then this
	 * is the first PFN that needs to be initialised.
	 */
	unsigned long first_deferred_pfn;
	/* Number of non-deferred pages */
	unsigned long static_init_pgcnt;
#endif /* CONFIG_DEFERRED_STRUCT_PAGE_INIT */

#ifdef CONFIG_TRANSPARENT_HUGEPAGE
	spinlock_t split_queue_lock;
	struct list_head split_queue;
	unsigned long split_queue_len;
#endif

	/* Fields commonly accessed by the page reclaim scanner */
	struct lruvec		lruvec;

	/*
	 * The target ratio of ACTIVE_ANON to INACTIVE_ANON pages on
	 * this node's LRU.  Maintained by the pageout code.
	 */
	unsigned int inactive_ratio;

	unsigned long		flags;

	ZONE_PADDING(_pad2_)

	/* Per-node vmstats */
	struct per_cpu_nodestat __percpu *per_cpu_nodestats;
	atomic_long_t		vm_stat[NR_VM_NODE_STAT_ITEMS];
} pg_data_t;
```

1.  在Linux内核中，所有的物理内存都用`struct page`结构体来描述，这些对象以数组形式存放，而这个数组就是mem_map。内存以节点为单位，每个节点下的物理内存统一管理，也就是说，在表示内存节点的描述类型struct pglist_data中，有node_mem_map这个成员，其针对平坦内存（CONFIG_FLAT_NODE_MEM_MAP）进行描述。
2.  每个内存节点下，node_mem_map成员是此节点下所有内存以`struct page`描述后，所有这些对象的基地址，这些对象以数组形式存放。注意：成员node_mem_map可能不是指向数组的第一个元素，因为页描述符数组的大小必须对齐到2^(MAX_ORDER - 1)次方，(MAX_ORDER - 1)是页分配器可分配的最大阶数。
3.  如果系统只有一个pglist_data对象，那么此对象下的node_mem_map即为全局对象mem_map。函数`alloc_node_mem_map()`就是针对节点的node_mem_map的处理。函数`alloc_node_mem_map()`的解析可参考下文 `2.3.3 zone初始化`小节，此处不做详细解析。

#### 2.3.2 内存区域 zone

- 内存节点被划分为内存区域（zone），内核定义的区域类型如下：

```c
/* linux-4.14/include/linux/mmzone.h */

enum zone_type {
#ifdef CONFIG_ZONE_DMA
	/*
	 * ZONE_DMA is used when there are devices that are not able
	 * to do DMA to all of addressable memory (ZONE_NORMAL). Then we
	 * carve out the portion of memory that is needed for these devices.
	 * The range is arch specific.
	 *
	 * Some examples
	 *
	 * Architecture		Limit
	 * ---------------------------
	 * parisc, ia64, sparc	<4G
	 * s390			<2G
	 * arm			Various
	 * alpha		Unlimited or 0-16MB.
	 *
	 * i386, x86_64 and multiple other arches
	 * 			<16M.
	 */
	ZONE_DMA,
#endif
#ifdef CONFIG_ZONE_DMA32
	/*
	 * x86_64 needs two ZONE_DMAs because it supports devices that are
	 * only able to do DMA to the lower 16M but also 32 bit devices that
	 * can only do DMA areas below 4G.
	 */
	ZONE_DMA32,
#endif
	/*
	 * Normal addressable memory is in ZONE_NORMAL. DMA operations can be
	 * performed on pages in ZONE_NORMAL if the DMA devices support
	 * transfers to all addressable memory.
	 */
	ZONE_NORMAL,
#ifdef CONFIG_HIGHMEM
	/*
	 * A memory area that is only addressable by the kernel through
	 * mapping portions into its own address space. This is for example
	 * used by i386 to allow the kernel to address the memory beyond
	 * 900MB. The kernel will set up special mappings (page
	 * table entries on i386) for each page that the kernel needs to
	 * access.
	 */
	ZONE_HIGHMEM,
#endif
	ZONE_MOVABLE,
#ifdef CONFIG_ZONE_DEVICE
	ZONE_DEVICE,
#endif
	__MAX_NR_ZONES

};
```

1.  DMA区域（ZONE_DMA）：DMA是“Direct Memory Access”的缩写，意思是直接内存访问。如果有些设备不能直接访问所有内存，需要使用DMA区域。例如旧的工业标准体系结构（Industry Standard Architecture，ISA）总线只能直接访问16MB以下的内存。
2.  DMA32区域（ZONE_DMA32）：64位系统，如果既要支持只能直接访问16MB以下内存的设备，又要支持只能直接访问4GB以下的32位设备，那么必须使用DMA32区域。
3.  普通区域（ZONE_NORMAL）：直接映射到内核虚拟地址空间的内存区域，直译为“普通区域”，意译为“直接映射区域”或“线性映射区域”。内核虚拟地址和物理地址是线性映射关系，即虚拟地址 = （物理地址 + 常量）。是否需要使用页表映射？不同处理器的实现不同，例如ARM处理器需要使用页表映射，而MIPS处理器不需要使用页表映射。
4.  高端内存区域（ZONE_HIGHMEM）：这是32位时代的产物，内核和用户地址空间按1:3划分，内核地址空间只有1GB，不能把1GB以上的内存直接映射到内核地址空间，把不能直接映射的内存划分到高端内存区域。通常把DMA区域、DMA32区域和普通区域统称为低端内存区域。64位系统的内核虚拟地址空间非常大，不再需要高端内存区域。
5.  可移动区域（ZONE_MOVABLE）：它是一个伪内存区域，用来防止内存碎片，后面反碎片技术的章节会具体描述。
6.  设备区域（ZONE_DEVICE）：为支持持久内存（persistent memory）热插拔增加的内存区域。

- 每个内存区域用一个zone结构体描述，其定义如下，主要成员已在代码中做出解释：

```c
/* linux-4.14/include/linux/mmzone.h */

struct zone {
	/* Read-mostly fields */

	/* zone watermarks, access with *_wmark_pages(zone) macros */
	unsigned long watermark[NR_WMARK]; /* 页分配器使用的水位值。每个zone在系统启动时会计算出3个水位值，分别是WMARK_MIN、WMARK_LOW、WMARK_HIGH，这在页面分配器和kswapd页面回收中会用到。 */

	unsigned long nr_reserved_highatomic;

	/*
	 * We don't know if the memory that we're going to allocate will be
	 * freeable or/and it will be released eventually, so to avoid totally
	 * wasting several GB of ram we must reserve some of the lower zone
	 * memory (otherwise we risk to run OOM on the lower zones despite
	 * there being tons of freeable ram on the higher zones).  This array is
	 * recalculated at runtime if the sysctl_lowmem_reserve_ratio sysctl
	 * changes.
	 */
	long lowmem_reserve[MAX_NR_ZONES]; /* zone中预留的内存，页分配器使用，当前区域保留多少页不能借给高端内存区域类型 */

#ifdef CONFIG_NUMA
	int node;
#endif
	struct pglist_data	*zone_pgdat; /* 指向内存节点的pglist_data实例 */
	struct per_cpu_pageset __percpu *pageset; /* 用于维护每个CPU上的一系列页面，以减少自旋锁的争用 */

#ifndef CONFIG_SPARSEMEM
	/*
	 * Flags for a pageblock_nr_pages block. See pageblock-flags.h.
	 * In SPARSEMEM, this map is stored in struct mem_section
	 */
	unsigned long		*pageblock_flags;
#endif /* CONFIG_SPARSEMEM */

	/* zone_start_pfn == zone_start_paddr >> PAGE_SHIFT */
	unsigned long		zone_start_pfn; /* 当前区域的起始物理页号 */

	/*
	 * spanned_pages is the total pages spanned by the zone, including
	 * holes, which is calculated as:
	 * 	spanned_pages = zone_end_pfn - zone_start_pfn;
	 *
	 * present_pages is physical pages existing within the zone, which
	 * is calculated as:
	 *	present_pages = spanned_pages - absent_pages(pages in holes);
	 *
	 * managed_pages is present pages managed by the buddy system, which
	 * is calculated as (reserved_pages includes pages allocated by the
	 * bootmem allocator):
	 *	managed_pages = present_pages - reserved_pages;
	 *
	 * So present_pages may be used by memory hotplug or memory power
	 * management logic to figure out unmanaged pages by checking
	 * (present_pages - managed_pages). And managed_pages should be used
	 * by page allocator and vm scanner to calculate all kinds of watermarks
	 * and thresholds.
	 *
	 * Locking rules:
	 *
	 * zone_start_pfn and spanned_pages are protected by span_seqlock.
	 * It is a seqlock because it has to be read outside of zone->lock,
	 * and it is done in the main allocator path.  But, it is written
	 * quite infrequently.
	 *
	 * The span_seq lock is declared along with zone->lock because it is
	 * frequently read in proximity to zone->lock.  It's good to
	 * give them a chance of being in the same cacheline.
	 *
	 * Write access to present_pages at runtime should be protected by
	 * mem_hotplug_begin/end(). Any reader who can't tolerant drift of
	 * present_pages should get_online_mems() to get a stable value.
	 *
	 * Read access to managed_pages should be safe because it's unsigned
	 * long. Write access to zone->managed_pages and totalram_pages are
	 * protected by managed_page_count_lock at runtime. Idealy only
	 * adjust_managed_page_count() should be used instead of directly
	 * touching zone->managed_pages and totalram_pages.
	 */
	unsigned long		managed_pages; /* 伙伴分配器管理的物理页的数量 */
	unsigned long		spanned_pages; /* 当前区域跨越的总页数，包括空洞 */
	unsigned long		present_pages; /* 当前区域存在的物理页的数量，不包括空洞。对于一些体系结构来说，其值和spanned_pages相等 */

	const char		*name; /* 区域名称 */

#ifdef CONFIG_MEMORY_ISOLATION
	/*
	 * Number of isolated pageblock. It is used to solve incorrect
	 * freepage counting problem due to racy retrieving migratetype
	 * of pageblock. Protected by zone->lock.
	 */
	unsigned long		nr_isolate_pageblock;
#endif

#ifdef CONFIG_MEMORY_HOTPLUG
	/* see spanned/present_pages for more description */
	seqlock_t		span_seqlock;
#endif

	int initialized;

	/* Write-intensive fields used from the page allocator */
	ZONE_PADDING(_pad1_)

	/* free areas of different sizes */
	struct free_area	free_area[MAX_ORDER]; /* 不同长度的空闲区域 */

	/* zone flags, see below */
	unsigned long		flags;

	/* Primarily protects free_area */
	spinlock_t		lock; /* 并行访问时用于对当前区域保护的自旋锁 */

	/* Write-intensive fields used by compaction and vmstats. */
	ZONE_PADDING(_pad2_)

	/*
	 * When free pages are below this point, additional steps are taken
	 * when reading the number of free pages to avoid per-cpu counter
	 * drift allowing watermarks to be breached
	 */
	unsigned long percpu_drift_mark;

#if defined CONFIG_COMPACTION || defined CONFIG_CMA
	/* pfn where compaction free scanner should start */
	unsigned long		compact_cached_free_pfn;
	/* pfn where async and sync compaction migration scanner should start */
	unsigned long		compact_cached_migrate_pfn[2];
#endif

#ifdef CONFIG_COMPACTION
	/*
	 * On compaction failure, 1<<compact_defer_shift compactions
	 * are skipped before trying again. The number attempted since
	 * last failure is tracked with compact_considered.
	 */
	unsigned int		compact_considered;
	unsigned int		compact_defer_shift;
	int			compact_order_failed;
#endif

#if defined CONFIG_COMPACTION || defined CONFIG_CMA
	/* Set to true when the PG_migrate_skip bits should be cleared */
	bool			compact_blockskip_flush;
#endif

	bool			contiguous;

	ZONE_PADDING(_pad3_)
	/* Zone statistics */
	atomic_long_t		vm_stat[NR_VM_ZONE_STAT_ITEMS];
	atomic_long_t		vm_numa_stat[NR_VM_NUMA_STAT_ITEMS];
} ____cacheline_internodealigned_in_smp;
```

- 当页表的初始化（页表创建和映射）完成之后，内核就可以对内存进行管理了，但是内核并不是统一对待这些页面，而是采用区域（也有称为区块）zone 的方式来管理。
- struct zone 是经常会被访问到的，因此这个数据结构要求以 L1 cache 对齐。另外，这里的 ZONE_PADDING() 是让 zone -> lock 和 zone -> lru_lock 这两个很热门的锁可以分布在不同的 cache line 中。一个内存节点最多也就几个 zone，因此 zone 数据结构不需要像 struct page 一样关注数据结构的大小，因此这里 ZONE_PADDING() 可以为了性能而浪费空间。
- 在内存管理开发过程中，内核开发者逐步发现一些自旋锁会竞争的非常厉害，很难获取。像 zone -> lock 和 zone -> lru_lock 这两个锁有时需要同时获取锁，因此保证它们使用不同的 cache line 是内核常用的一种优化技巧。



#### 2.3.3 物理页 page

- 每个物理页对应一个page结构体，称为页描述符，内存节点的pglist_data实例的成员node_mem_map指向给内存节点包含的所有物理页的页描述符组成的数组。
- Linux内核内存管理的实现以struct page为核心，其他所有的内存管理设施都为之展开，例如VMA管理、缺页中断、反向映射、页面分配与回收等。
- 因为物理页的数量很大，所以咋page结构体中增加1个成员，可能导致所有的page实例占用的内存大幅增加。为了减少内存消耗，内核努力使page结构体尽可能小，对于不会同时生效的成员，使用联合体，这种做法带来的负面影响是page结构体的可读性差。
- struct page数据结构

```c
/* linux-4.14/include/linux/mm_types.h */

/*
 * Each physical page in the system has a struct page associated with
 * it to keep track of whatever it is we are using the page for at the
 * moment. Note that we have no way to track which tasks are using
 * a page, though if it is a pagecache page, rmap structures can tell us
 * who is mapping it.
 *
 * The objects in struct page are organized in double word blocks in
 * order to allows us to use atomic double word operations on portions
 * of struct page. That is currently only used by slub but the arrangement
 * allows the use of atomic double word operations on the flags/mapping
 * and lru list pointers also.
 */
struct page {
	/* First double word block */
	unsigned long flags;		/* Atomic flags, some possibly
					 * updated asynchronously */
	union {
		struct address_space *mapping;	/* If low bit clear, points to
						 * inode address_space, or NULL.
						 * If page mapped as anonymous
						 * memory, low bit is set, and
						 * it points to anon_vma object:
						 * see PAGE_MAPPING_ANON below.
						 */
		void *s_mem;			/* slab first object */
		atomic_t compound_mapcount;	/* first tail page */
		/* page_deferred_list().next	 -- second tail page */
	};

	/* Second double word */
	union {
		pgoff_t index;		/* Our offset within mapping. */
		void *freelist;		/* sl[aou]b first free object */
		/* page_deferred_list().prev	-- second tail page */
	};

	union {
#if defined(CONFIG_HAVE_CMPXCHG_DOUBLE) && \
	defined(CONFIG_HAVE_ALIGNED_STRUCT_PAGE)
		/* Used for cmpxchg_double in slub */
		unsigned long counters;
#else
		/*
		 * Keep _refcount separate from slub cmpxchg_double data.
		 * As the rest of the double word is protected by slab_lock
		 * but _refcount is not.
		 */
		unsigned counters;
#endif
		struct {

			union {
				/*
				 * Count of ptes mapped in mms, to show when
				 * page is mapped & limit reverse map searches.
				 *
				 * Extra information about page type may be
				 * stored here for pages that are never mapped,
				 * in which case the value MUST BE <= -2.
				 * See page-flags.h for more details.
				 */
				atomic_t _mapcount;

				unsigned int active;		/* SLAB */
				struct {			/* SLUB */
					unsigned inuse:16;
					unsigned objects:15;
					unsigned frozen:1;
				};
				int units;			/* SLOB */
			};
			/*
			 * Usage count, *USE WRAPPER FUNCTION* when manual
			 * accounting. See page_ref.h
			 */
			atomic_t _refcount;
		};
	};

	/*
	 * Third double word block
	 *
	 * WARNING: bit 0 of the first word encode PageTail(). That means
	 * the rest users of the storage space MUST NOT use the bit to
	 * avoid collision and false-positive PageTail().
	 */
	union {
		struct list_head lru;	/* Pageout list, eg. active_list
					 * protected by zone_lru_lock !
					 * Can be used as a generic list
					 * by the page owner.
					 */
		struct dev_pagemap *pgmap; /* ZONE_DEVICE pages are never on an
					    * lru or handled by a slab
					    * allocator, this points to the
					    * hosting device page map.
					    */
		struct {		/* slub per cpu partial pages */
			struct page *next;	/* Next partial slab */
#ifdef CONFIG_64BIT
			int pages;	/* Nr of partial slabs left */
			int pobjects;	/* Approximate # of objects */
#else
			short int pages;
			short int pobjects;
#endif
		};

		struct rcu_head rcu_head;	/* Used by SLAB
						 * when destroying via RCU
						 */
		/* Tail pages of compound page */
		struct {
			unsigned long compound_head; /* If bit zero is set */

			/* First tail page only */
#ifdef CONFIG_64BIT
			/*
			 * On 64 bit system we have enough space in struct page
			 * to encode compound_dtor and compound_order with
			 * unsigned int. It can help compiler generate better or
			 * smaller code on some archtectures.
			 */
			unsigned int compound_dtor;
			unsigned int compound_order;
#else
			unsigned short int compound_dtor;
			unsigned short int compound_order;
#endif
		};

#if defined(CONFIG_TRANSPARENT_HUGEPAGE) && USE_SPLIT_PMD_PTLOCKS
		struct {
			unsigned long __pad;	/* do not overlay pmd_huge_pte
						 * with compound_head to avoid
						 * possible bit 0 collision.
						 */
			pgtable_t pmd_huge_pte; /* protected by page->ptl */
		};
#endif
	};

	/* Remainder is not double word aligned */
	union {
		unsigned long private;		/* Mapping-private opaque data:
					 	 * usually used for buffer_heads
						 * if PagePrivate set; used for
						 * swp_entry_t if PageSwapCache;
						 * indicates order in the buddy
						 * system if PG_buddy is set.
						 */
#if USE_SPLIT_PTE_PTLOCKS
#if ALLOC_SPLIT_PTLOCKS
		spinlock_t *ptl;
#else
		spinlock_t ptl;
#endif
#endif
		struct kmem_cache *slab_cache;	/* SL[AU]B: Pointer to slab */
	};

#ifdef CONFIG_MEMCG
	struct mem_cgroup *mem_cgroup;
#endif

	/*
	 * On machines where all RAM is mapped into kernel address space,
	 * we can simply calculate the virtual address. On machines with
	 * highmem some memory is mapped into kernel virtual memory
	 * dynamically, so we need a place to store that address.
	 * Note that this field could be 16 bits on x86 ... ;)
	 *
	 * Architectures with slow multiplication can define
	 * WANT_PAGE_VIRTUAL in asm/page.h
	 */
#if defined(WANT_PAGE_VIRTUAL)
	void *virtual;			/* Kernel virtual address (NULL if
					   not kmapped, ie. highmem) */
#endif /* WANT_PAGE_VIRTUAL */

#ifdef LAST_CPUPID_NOT_IN_PAGE_FLAGS
	int _last_cpupid;
#endif
}
```

下面分别解析其主要成员的意义：

**flags**

```c
/* linux-4.14/include/linux/mm_types.h */
 	unsigned long flags;		/* Atomic flags, some possibly
 					 * updated asynchronously */
```

结构体page的成员flags的布局如下：

```
| [SECTION] | [NODE] | ZONE | [LAST_CPUPID] | ... | FLAGS |
```

其中，SECTION是稀疏内存模型中的段编号，NODE是节点编号，ZONE是区域类型，FLAGS是该页面的标志位。

而具体存放的内容与内核配置相关，例如SECTION编号和NODE节点编号与CONFIG_SPARSEMEM / CONFIG_SPARSEMEM_VMEMMAP配置相关，LAST_CPUID与CONFIG_NUMA_BALANCING配置相关。

内联函数 page_to_nid 用来得到物理页所属的内存节点的编号，page_zonenum 用来得到物理页所属的内存区域的类型。两个函数内部具体的宏定义此处不再详述。

```c
/* linux-4.14/include/linux/mm.h */

static inline int page_to_nid(const struct page *page)
{
	return (page->flags >> NODES_PGSHIFT) & NODES_MASK;
}

static inline enum zone_type page_zonenum(const struct page *page)
{
	return (page->flags >> ZONES_PGSHIFT) & ZONES_MASK;
}

```

-   标志位是内存管理非常重要的部分，具体定义如下：

```c
/* linux-4.14/include/linux/page-flags.h */

enum pageflags {
	PG_locked, /* 表示该页面已经上锁。如果该比特位置位，说明页面已经被锁定，内存管理的其他模块不能访问这个页面，以防发生竞争 */
	PG_error, /* 表示页面操作过程中发生错误时会设置该位 */
	PG_referenced, /* 控制页面的活跃程度，该标志位用来实现LRU算法中的第二次机会法，详见后续页面回收章节 */
	PG_uptodate, /* 表示页面的内容是有效的，当该页面上的读操作完成后，设置该标志位 */
	PG_dirty, /* 表示该页面被修改过，为脏页，即页面的内容被改写后还没有和外部存储器进行过同步操作 */
	PG_lru, /* 表示该页加入了LRU链表中。LRU是最近最少使用链表（least recently used）的简称。内核使用LRU链表来管理活跃和不活跃页面。 */
	PG_active, /* 表示该页在活跃LRU链表中 */
	PG_waiters,		/* Page has waiters, check its waitqueue. Must be bit #7 and in the same byte as "PG_locked" */
	PG_slab, /* 表示该页用于slab分配器 */
	PG_owner_priv_1,	/* Owner use. If pagecache, fs may use*/
	PG_arch_1, /* 与体系结构相关的页面状态位 */
	PG_reserved, /* 表示该页不可被换出 */
	PG_private,		/* If pagecache, has fs-private data */
	PG_private_2,		/* If pagecache, has fs aux data */
	PG_writeback,		/* Page is under writeback，表示页面正在向块设备进行回写 */
	PG_head,		/* A head page */
	PG_mappedtodisk,	/* Has blocks allocated on-disk，在磁盘中分配了block */
	PG_reclaim,		/* To be reclaimed asap，马上要被回收了 */
	PG_swapbacked,		/* Page is backed by RAM/swap，表示页面处于交换缓存 */
	PG_unevictable,		/* Page is "unevictable"， 表示页面是不可回收的*/
#ifdef CONFIG_MMU
	PG_mlocked,		/* Page is vma mlocked，表示页面对应的VMA处于mlocked状态 */
#endif
#ifdef CONFIG_ARCH_USES_PG_UNCACHED
	PG_uncached,		/* Page has been mapped as uncached */
#endif
#ifdef CONFIG_MEMORY_FAILURE
	PG_hwpoison,		/* hardware poisoned page. Don't touch */
#endif
#if defined(CONFIG_IDLE_PAGE_TRACKING) && defined(CONFIG_64BIT)
	PG_young,
	PG_idle,
#endif
	__NR_PAGEFLAGS,

	/* Filesystems */
	PG_checked = PG_owner_priv_1,

	/* SwapBacked */
	PG_swapcache = PG_owner_priv_1,	/* Swap page: swp_entry_t in private */

	/* Two page bits are conscripted by FS-Cache to maintain local caching
	 * state.  These bits are set on pages belonging to the netfs's inodes
	 * when those inodes are being locally cached.
	 */
	PG_fscache = PG_private_2,	/* page backed by cache */

	/* XEN */
	/* Pinned in Xen as a read-only pagetable page. */
	PG_pinned = PG_owner_priv_1,
	/* Pinned as part of domain save (see xen_mm_pin_all()). */
	PG_savepinned = PG_dirty,
	/* Has a grant mapping of another (foreign) domain's page. */
	PG_foreign = PG_owner_priv_1,

	/* SLOB */
	PG_slob_free = PG_private,

	/* Compound pages. Stored in first tail page's flags */
	PG_double_map = PG_private_2,

	/* non-lru isolated movable page */
	PG_isolated = PG_reclaim,
};

```

-   内核定义了一些标准宏，用于检查页面是否设置了某个特定的标志位或者用于操作某些标志位。这些宏的名称都有一定的模式，具体如下：

1.  PageXXX()用于检查页面是否设置了 PG_XXX 标志位。例如，PageLRU(page)检查PG_lru标志位是否置位了，PageDirty(page)检查PG_dirty标志位是否置位了。
2.  SetPageXXX()设置页中的 PG_XXX 标志位。例如，SetPageLRU(page)用于设置PG_lru，SetPageDirty(page)用于设置PG_dirty标志位。
3.  ClearPageXXX()用于无条件地清楚某个特定的标志位。

-   宏的实现在`linux-4.14/include/linux/page-flags.h`文件中，如下：

```c
/* linux-4.14/include/linux/page-flags.h */

/*
 * Macros to create function definitions for page flags
 */
#define TESTPAGEFLAG(uname, lname, policy)				\
static __always_inline int Page##uname(struct page *page)		\
	{ return test_bit(PG_##lname, &policy(page, 0)->flags); }

#define SETPAGEFLAG(uname, lname, policy)				\
static __always_inline void SetPage##uname(struct page *page)		\
	{ set_bit(PG_##lname, &policy(page, 1)->flags); }

#define CLEARPAGEFLAG(uname, lname, policy)				\
static __always_inline void ClearPage##uname(struct page *page)		\
	{ clear_bit(PG_##lname, &policy(page, 1)->flags); }


```

**mapping**

```c
/* linux-4.14/include/linux/mm_types.h */

struct address_space *mapping;	/* If low bit clear, points to
				 * inode address_space, or NULL.
				 * If page mapped as anonymous
				 * memory, low bit is set, and
				 * it points to anon_vma object:
				 * see PAGE_MAPPING_ANON below.
				 */

```

-   struct page 数据结构中的mapping成员表示页面所指向的地址空间（address_space）。内核中的地址空间通常有两个不同的地址空间，一个用于文件映射页面，例如在读取文件时，地址空间用于将文件的内容数据与装载数据的存储介质区关联起来；另一个用于匿名映射。内核使用了一个简单直接的方式实现了“一个指针，两种用途”，mapping指针地址的最低位用于判断是否指向匿名映射或KSM页面的地址空间，如果是匿名映射，那么mapping指向匿名页面的地址空间数据结构struct anon_vma。

```c
#define PAGE_MAPPING_ANON	0x1
#define PAGE_MAPPING_MOVABLE	0x2
#define PAGE_MAPPING_KSM	(PAGE_MAPPING_ANON | PAGE_MAPPING_MOVABLE)
#define PAGE_MAPPING_FLAGS	(PAGE_MAPPING_ANON | PAGE_MAPPING_MOVABLE)

  ...

static __always_inline int PageAnon(struct page *page)
{
	page = compound_head(page);
	return ((unsigned long)page->mapping & PAGE_MAPPING_ANON) != 0;
}

```

**s_mem**

```c
/* linux-4.14/include/linux/mm_types.h */

	void *s_mem;			/* slab first object */
```

- struct page 数据结构中的s_mem用于slab分配器，slab中第一个对象的开始地址，s_mem和mapping共同占用一个字节的存储空间。

**Second double word**

```c
/* linux-4.14/include/linux/mm_types.h */

/* Second double word */
union {
	pgoff_t index;		/* Our offset within mapping. */
	void *freelist;		/* sl[aou]b first free object */
	/* page_deferred_list().prev	-- second tail page */
};

	union {
#if defined(CONFIG_HAVE_CMPXCHG_DOUBLE) && \
	defined(CONFIG_HAVE_ALIGNED_STRUCT_PAGE)
		/* Used for cmpxchg_double in slub */
		unsigned long counters;
#else
		/*
		 * Keep _refcount separate from slub cmpxchg_double data.
		 * As the rest of the double word is protected by slab_lock
		 * but _refcount is not.
		 */
		unsigned counters;
#endif
		struct {

			union {
				/*
				 * Count of ptes mapped in mms, to show when
				 * page is mapped & limit reverse map searches.
				 *
				 * Extra information about page type may be
				 * stored here for pages that are never mapped,
				 * in which case the value MUST BE <= -2.
				 * See page-flags.h for more details.
				 */
				atomic_t _mapcount;

				unsigned int active;		/* SLAB */
				struct {			/* SLUB */
					unsigned inuse:16;
					unsigned objects:15;
					unsigned frozen:1;
				};
				int units;			/* SLOB */
		};
		/*
		 * Usage count, *USE WRAPPER FUNCTION* when manual
		 * accounting. See page_ref.h
		 */
		atomic_t _refcount;
	};
};
```

- 第二个双字由两个联合体组成。index表示这个页面在一个映射中的序号和偏移量；freelist用于slab分配器；_mapcount和_refcount是两个非常重要的引用计数。

**Third double word block**

```c
/* linux-4.14/include/linux/mm_types.h */

	/*
	 * Third double word block
	 *
	 * WARNING: bit 0 of the first word encode PageTail(). That means
	 * the rest users of the storage space MUST NOT use the bit to
	 * avoid collision and false-positive PageTail().
	 */
	union {
		struct list_head lru;	/* Pageout list, eg. active_list
					 * protected by zone_lru_lock !
					 * Can be used as a generic list
					 * by the page owner.
					 */
		struct dev_pagemap *pgmap; /* ZONE_DEVICE pages are never on an
					    * lru or handled by a slab
					    * allocator, this points to the
					    * hosting device page map.
					    */
		struct {		/* slub per cpu partial pages */
			struct page *next;	/* Next partial slab */
#ifdef CONFIG_64BIT
			int pages;	/* Nr of partial slabs left */
			int pobjects;	/* Approximate # of objects */
#else
			short int pages;
			short int pobjects;
#endif
		};

		struct rcu_head rcu_head;	/* Used by SLAB
						 * when destroying via RCU
						 */
		/* Tail pages of compound page */
		struct {
			unsigned long compound_head; /* If bit zero is set */

			/* First tail page only */
#ifdef CONFIG_64BIT
			/*
			 * On 64 bit system we have enough space in struct page
			 * to encode compound_dtor and compound_order with
			 * unsigned int. It can help compiler generate better or
			 * smaller code on some archtectures.
			 */
			unsigned int compound_dtor;
			unsigned int compound_order;
#else
			unsigned short int compound_dtor;
			unsigned short int compound_order;
#endif
		};

#if defined(CONFIG_TRANSPARENT_HUGEPAGE) && USE_SPLIT_PMD_PTLOCKS
		struct {
			unsigned long __pad;	/* do not overlay pmd_huge_pte
						 * with compound_head to avoid
						 * possible bit 0 collision.
						 */
			pgtable_t pmd_huge_pte; /* protected by page->ptl */
		};
#endif
};
```

- lru用于页面加入和删除LRU链表，其余一些成员用于slab或slub分配器



## 3. 物理内存初始化

- 物理内存初始化包括 zone 初始化、node 初始化，以及内存的初始化这三部分，下面我们根据初始化前后的函数调用关系具体解析整个物理内存初始化的流程。

### 3.1  zone 、node 初始化

- zone 的初始化始于函数 `bootmem_init()`，需要确定每个 zone 的范围。函数调用关系：`start_kernel() -> setup_arch() -> paging_init() -> bootmem_init()`，我们从bootmem_init() 函数定义开始解析：

```c
[linux-4.14/arch/arm/mm/init.c]
static void __init find_limits(unsigned long *min, unsigned long *max_low,
			       unsigned long *max_high)
{
	*max_low = PFN_DOWN(memblock_get_current_limit());
	*min = PFN_UP(memblock_start_of_DRAM());
	*max_high = PFN_DOWN(memblock_end_of_DRAM());
}

[linux-4.14/arch/arm/mm/init.c]
void __init bootmem_init(void)
{
	unsigned long min, max_low, max_high;
	/* memblock_allow_resize 设置memblock_can_resize = 1 */
	memblock_allow_resize();
	max_low = max_high = 0;
	/* find_limits()函数计算出min、max_low、max_high，后面会将这三个值分布赋值给			
    * min_low_pfn、max_low_pfn、max_pfn，其中 min_low_pfn 是内存块的开始地址的页帧号
    * （arm32架构下，该值为 0x60000）, max_low_pfn（0x8f800）表示 normal 区域的结束页帧
    * 号，它由 arm_lowmem_init 这个变量得来，max_pfn（0xa0000）是内存块的结束地址的页帧号。
    */
	find_limits(&min, &max_low, &max_high);

	early_memtest((phys_addr_t)min << PAGE_SHIFT,
		      (phys_addr_t)max_low << PAGE_SHIFT);

	/*
	 * Sparsemem tries to allocate bootmem in memory_present(),
	 * so must be done after the fixed reservations
	 */
   /* arm 平台下，该函数什么也不做 */
	arm_memory_present();

	/*
	 * sparse_init() needs the bootmem allocator up and running.
	 */
   /* 对非线性内存的映射，这里与zone初始化关系不大，暂不做分析 */
	sparse_init();

	/*
	 * Now free the memory - free_area_init_node needs
	 * the sparse mem_map arrays initialized by sparse_init()
	 * for memmap_init_zone(), otherwise all PFNs are invalid.
	 */
    	/*
    	* zone 初始化主要在 zone_sizes_init() 函数内完成
    	*/
	zone_sizes_init(min, max_low, max_high);

	/*
	 * This doesn't seem to be used by the Linux memory manager any
	 * more, but is used by ll_rw_block.  If we can get rid of it, we
	 * also get rid of some of the stuff above as well.
	 */
	min_low_pfn = min;
	max_low_pfn = max_low;
	max_pfn = max_high;
}
```

- 接上文，bootmem_init() -> zone_sizes_init()，  zone_sizes_init() 函数定义及解析如下：

``` c
[linux-4.14/include/generated/bounds.h]
#define MAX_NR_ZONES 3 /* __MAX_NR_ZONES */

[linux-4.14/arch/arm/mm/init.c]
static void __init zone_sizes_init(unsigned long min, unsigned long max_low,
	unsigned long max_high)
{
   	/* MAX_NR_ZONES指定节点包含的zone数量，如前面定义，此处 MAX_NR_ZONES 值为3 */
	unsigned long zone_size[MAX_NR_ZONES], zhole_size[MAX_NR_ZONES];
	struct memblock_region *reg;

	/*
	 * initialise the zones.
	 */
	memset(zone_size, 0, sizeof(zone_size));

	/*
	 * The memory size has already been determined.  If we need
	 * to do anything fancy with the allocation of this memory
	 * to the zones, now is the time to do it.
	 */
   	/* 由 bootmem_init() 函数中传递的参数（max_low=0x8f800，min=0x60000）, 可以计算出zone_size[0]=0x2f800, 即194560, 也就是说从 [内核空间的起始地址 ~ 低端地址空间的结束地址(arm_lowmem_limit)]这个范围（zone_size[0]），共包含194560个页面 */
	zone_size[0] = max_low - min;
#ifdef CONFIG_HIGHMEM
   	/* 由 bootmem_init() 函数中传递的参数（max_low=0x8f800，min=0x60000， max_high=0xa0000）, 可以计算出zone_size[ZONE_HIGHMEM]=0x10800, 即67584， 也就是说内核高端地址空间（zone_size[ZONE_HIGHMEM]）中包含67584个页面, 此处 ZONE_HIGHMEM 为 1 */
	zone_size[ZONE_HIGHMEM] = max_high - max_low;
#endif

	/*
	 * Calculate the size of the holes.
	 *  holes = node_size - sum(bank_sizes)
	 */
   	/* 计算zone_size中是否有洞，即未映射页的地址空间 */
	memcpy(zhole_size, zone_size, sizeof(zhole_size));
	for_each_memblock(memory, reg) {
		unsigned long start = memblock_region_memory_base_pfn(reg);
		unsigned long end = memblock_region_memory_end_pfn(reg);

		if (start < max_low) {
			unsigned long low_end = min(end, max_low);
			zhole_size[0] -= low_end - start;
		}
#ifdef CONFIG_HIGHMEM
		if (end > max_low) {
			unsigned long high_start = max(start, max_low);
			zhole_size[ZONE_HIGHMEM] -= end - high_start;
		}
#endif
	}
/* arm平台未定义CONFIG_ZONE_DMA，所以此#ifdef内不再解析 */
#ifdef CONFIG_ZONE_DMA
	/*
	 * Adjust the sizes according to any special requirements for
	 * this machine type.
	 */
	if (arm_dma_zone_size)
		arm_adjust_dma_zone(zone_size, zhole_size,
			arm_dma_zone_size >> PAGE_SHIFT);
#endif
	/* zone 初始化函数在 free_area_init_node，下文继续该函数解析  */
	free_area_init_node(0, zone_size, min, zhole_size);
}
```

- 接上文，zone_sizes_init() -> free_area_init_node()，内存节点 node 的初始化始于 free_area_init_node() 函数，同时 ，zone 的初始化过程通过调用函数 free_area_init_core() 来完成，函数free_area_init_node() 定义及解析如下:

```c
[linux-4.14/mm/page_alloc.c]
/*
 * nid: 节点编号，arm架构下只有一个节点，即0
 */
void __paginginit free_area_init_node(int nid, unsigned long *zones_size,
		unsigned long node_start_pfn, unsigned long *zholes_size)
{
	pg_data_t *pgdat = NODE_DATA(nid);
	unsigned long start_pfn = 0;
	unsigned long end_pfn = 0;

	/* pg_data_t should be reset to zero when it's allocated */
	WARN_ON(pgdat->nr_zones || pgdat->kswapd_classzone_idx);
	/* 对 pgdat 节点相关成员赋值， 6168~6172可忽略 */
	pgdat->node_id = nid;
	pgdat->node_start_pfn = node_start_pfn;
	pgdat->per_cpu_nodestats = NULL;
#ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
	get_pfn_range_for_nid(nid, &start_pfn, &end_pfn);
	pr_info("Initmem setup node %d [mem %#018Lx-%#018Lx]\n", nid,
		(u64)start_pfn << PAGE_SHIFT,
		end_pfn ? ((u64)end_pfn << PAGE_SHIFT) - 1 : 0);
#else
	start_pfn = node_start_pfn;
#endif
  	/* 计算当前节点下包含的页面总数，函数实现比较简单，此处不再解析 */
	calculate_node_totalpages(pgdat, start_pfn, end_pfn,
				  zones_size, zholes_size);
	/* 为当前节点pgdat 的成员 node_mem_map 赋值，即将当前节点下所有页的基地址保存在 node_mem_map数组中，node_mem_map的含义可参考前文 内存节点node相关论述, 该函数我们下文会稍作简要叙述 */
	alloc_node_mem_map(pgdat);
#ifdef CONFIG_FLAT_NODE_MEM_MAP
	printk(KERN_DEBUG "free_area_init_node: node %d, pgdat %08lx, node_mem_map %08lx\n",
		nid, (unsigned long)pgdat,
		(unsigned long)pgdat->node_mem_map);
#endif
	/* 当 CONFIG_DEFERRED_STRUCT_PAGE_INIT 定义时， reset_deferred_meminit() 函数给 pgdat 成员变量 static_init_pgcnt 、first_deferred_pfn赋值，当CONFIG_DEFERRED_STRUCT_PAGE_INIT 未定义时，该函数什么也不做。 */
	reset_deferred_meminit(pgdat);
  	/* zone 初始化过程 在 free_area_init_core() 函数内执行， 下文详细解析该函数。*/
	free_area_init_core(pgdat);
}

/*alloc_node_mem_map() 具体来说应该属于 `2.3.1 内存节点node` 小节范围， 但为了函数上下调用关系的解析，以及理解的连贯性，我们放在此处解析 */
static void __ref alloc_node_mem_map(struct pglist_data *pgdat)
{
	unsigned long __maybe_unused start = 0;
	unsigned long __maybe_unused offset = 0;

	/* Skip empty nodes */
  	/* 如此内存节点内无有效的内存，直接略过 */
	if (!pgdat->node_spanned_pages)
		return;

#ifdef CONFIG_FLAT_NODE_MEM_MAP /* 只处理平坦型内存 */
  	/* 起始地址必须对齐，这个一般按照MB级别对齐即可。 */
	start = pgdat->node_start_pfn & ~(MAX_ORDER_NR_PAGES - 1);
  	/* 计算偏移地址，即对齐后地址与真正开始地址之间的偏移大小 */
	offset = pgdat->node_start_pfn - start;
	/* ia64 gets its own node_mem_map, before this, without bootmem */
  	/* 如果pgdat目前没有设置node_mem_map则对其设置 */
	if (!pgdat->node_mem_map) {
		unsigned long size, end;
		struct page *map;

		/*
		 * The zone's endpoints aren't required to be MAX_ORDER
		 * aligned but the node_mem_map endpoints must be in order
		 * for the buddy allocator to function correctly.
		 */
		end = pgdat_end_pfn(pgdat); /* 获取节点内结束页帧号pfn */
		end = ALIGN(end, MAX_ORDER_NR_PAGES); /* 考虑对齐影响，注意这个需要向前舍入。 */
   		/* 计算需要的数组大小，需要注意end-start是页帧个数，每个页需要一个struct page对象，
所以，这里是乘关系，这样得到整个node内所有以page为单位描述需要占据的内存。 */
		size =  (end - start) * sizeof(struct page);
		map = alloc_remap(pgdat->node_id, size); /* alloc_remap已经废弃，不再使用 */
		if (!map)
  		/* 通过memblock管理算法分配内存，具体分配细则，此处不再进行解析 */
			map = memblock_virt_alloc_node_nopanic(size,
							       pgdat->node_id);
		pgdat->node_mem_map = map + offset; /* 这里对最终的node_mem_map修正偏移位置。一般这个offset为0. */
	}
#ifndef CONFIG_NEED_MULTIPLE_NODES
	/*
	 * With no DISCONTIG, the global mem_map is just set as node 0's
	 */
	if (pgdat == NODE_DATA(0)) {
  	/* 如果系统只有一个pglist_data对象，那么此对象下的node_mem_map即为全局对象mem_map */
		mem_map = NODE_DATA(0)->node_mem_map;
#if defined(CONFIG_HAVE_MEMBLOCK_NODE_MAP) || defined(CONFIG_FLATMEM)
		if (page_to_pfn(mem_map) != pgdat->node_start_pfn)
			mem_map -= offset;
#endif /* CONFIG_HAVE_MEMBLOCK_NODE_MAP */
	}
#endif
#endif /* CONFIG_FLAT_NODE_MEM_MAP */
}
```

- 接上文，free_area_init_node() -> free_area_init_core() 函数定义及解析，  free_area_init_core()是 zone 初始化的核心函数，并且 物理内存的初始化过程也始于此函数，其定义和解析如下：

```c
[linux-4.14/mm/page_alloc.c]
/*
 * Set up the zone data structures:
 *   - mark all pages reserved
 *   - mark all memory queues empty
 *   - clear the memory bitmaps
 *
 * NOTE: pgdat should get zeroed by caller.
 */
static void __paginginit free_area_init_core(struct pglist_data *pgdat)
{
	enum zone_type j;
	int nid = pgdat->node_id;
	/* 初始化 pgdat->node_size_lock */
	pgdat_resize_init(pgdat);
#ifdef CONFIG_NUMA_BALANCING
	spin_lock_init(&pgdat->numabalancing_migrate_lock);
	pgdat->numabalancing_migrate_nr_pages = 0;
	pgdat->numabalancing_migrate_next_window = jiffies;
#endif
#ifdef CONFIG_TRANSPARENT_HUGEPAGE
	spin_lock_init(&pgdat->split_queue_lock);
	INIT_LIST_HEAD(&pgdat->split_queue);
	pgdat->split_queue_len = 0;
#endif
  /* 初始化 pgdat->kswapd_wait、pgdat->pfmemalloc_wait */
	init_waitqueue_head(&pgdat->kswapd_wait);
	init_waitqueue_head(&pgdat->pfmemalloc_wait);
#ifdef CONFIG_COMPACTION
	init_waitqueue_head(&pgdat->kcompactd_wait);
#endif
	pgdat_page_ext_init(pgdat);
	spin_lock_init(&pgdat->lru_lock);
	lruvec_init(node_lruvec(pgdat));

	pgdat->per_cpu_nodestats = &boot_nodestats;

	for (j = 0; j < MAX_NR_ZONES; j++) {
		struct zone *zone = pgdat->node_zones + j;
		unsigned long size, realsize, freesize, memmap_pages;
		unsigned long zone_start_pfn = zone->zone_start_pfn;

		size = zone->spanned_pages;
		realsize = freesize = zone->present_pages;

		/*
		 * Adjust freesize so that it accounts for how much memory
		 * is used by this zone for memmap. This affects the watermark
		 * and per-cpu initialisations
		 */
		memmap_pages = calc_memmap_size(size, realsize);
		if (!is_highmem_idx(j)) {
			if (freesize >= memmap_pages) {
				freesize -= memmap_pages;
				if (memmap_pages)
					printk(KERN_DEBUG
					       "  %s zone: %lu pages used for memmap\n",
					       zone_names[j], memmap_pages);
			} else
				pr_warn("  %s zone: %lu pages exceeds freesize %lu\n",
					zone_names[j], memmap_pages, freesize);
		}

		/* Account for reserved pages */
		if (j == 0 && freesize > dma_reserve) {
			freesize -= dma_reserve;
			printk(KERN_DEBUG "  %s zone: %lu pages reserved\n",
					zone_names[0], dma_reserve);
		}

		if (!is_highmem_idx(j))
			nr_kernel_pages += freesize;
		/* Charge for highmem memmap if there are enough kernel pages */
		else if (nr_kernel_pages > memmap_pages * 2)
			nr_kernel_pages -= memmap_pages;
		nr_all_pages += freesize;

		/*
		 * Set an approximate value for lowmem here, it will be adjusted
		 * when the bootmem allocator frees pages into the buddy system.
		 * And all highmem pages will be managed by the buddy system.
		 */
		zone->managed_pages = is_highmem_idx(j) ? realsize : freesize;
#ifdef CONFIG_NUMA
		zone->node = nid;
#endif
		zone->name = zone_names[j];
		zone->zone_pgdat = pgdat;
		spin_lock_init(&zone->lock);
		zone_seqlock_init(zone);
  		/* 配置 成员变量pageset */
		zone_pcp_init(zone);

		if (!size)
			continue;

  		/* 当 CONFIG_HUGETLB_PAGE_SIZE_VARIABLE 被定义时，设置pageblock_order，否则函set_pageblock_order()数什么也不执行, setup_usemap()函数来计算和分配 pageblock_flags 所需要的大小，并且分配相应的内存。memmap_init()函数是物理内存初始化的核心函数， 与pageblock、setup_usemap()函数等相关介绍请看下文相关解析 */
		set_pageblock_order();
		setup_usemap(pgdat, zone, zone_start_pfn, size);
		init_currently_empty_zone(zone, zone_start_pfn, size);
		memmap_init(size, nid, j, zone_start_pfn);
	}
}
```



### 3.2 内存初始化

- 在内核启动时，内核知道物理内存DDR的大小并且计算出高端内存的起始地址和内核空间的布局后，物理内存页面 page 就要加入到伙伴系统中。

- 伙伴（Buddy System）是操作系统中最常用的一种动态存储管理方法，在用户提出申请时，分配一块大小合适的内存块给用户，反之，在用户释放内存块时回收。在伙伴系统中，内存块是 2 的 order 次幂。Linux内核中，order 的最大值用 MAX_ORDER 来表示，通常是 11，也就是把所有的空闲页面分组长11个内存块链表，每个内存块链表分别包括1、2、4、8、16、32、... 、1024个连续的页面。1024 个页面对应4MB 大小的连续物理内存。

- 物理内存在Linux内核中分出几个zone来管理，zone根据内核的配置来划分，例如在ARM Vexpress 平台中，zone分为ZONE_NORMAL和ZONE_HIGHMEM。

- 伙伴系统的空闲页块的管理如下图：

  zone 的数据结构中有一个 free_area 数组，数组大小是 MAX_ORDER， free_area 数据结构中包含了 MIGRATE_TYPES 个链表，这里相当于 zone 中根据 order 的大小有 0 到 MAX_ORDER-1 个 free_area，每个 free_area 根据 MIGRATE_TYPES 类型有几个相应的链表。

```c
[linux-4.14/include/linux/mmzone.h]
struct zone {
	...
 	/* free areas of different sizes */
 	struct free_area	free_area[MAX_ORDER]; /* 不同长度的空闲区域 */
	...
}

struct free_area {
	struct list_head	free_list[MIGRATE_TYPES];
	unsigned long		nr_free;
};

enum migratetype {
	MIGRATE_UNMOVABLE,
	MIGRATE_MOVABLE,
	MIGRATE_RECLAIMABLE,
	MIGRATE_PCPTYPES,	/* the number of types on the pcp lists */
	MIGRATE_HIGHATOMIC = MIGRATE_PCPTYPES,
#ifdef CONFIG_CMA
	/*
	 * MIGRATE_CMA migration type is designed to mimic the way
	 * ZONE_MOVABLE works.  Only movable pages can be allocated
	 * from MIGRATE_CMA pageblocks and page allocator never
	 * implicitly change migration type of MIGRATE_CMA pageblock.
	 *
	 * The way to use it is to change migratetype of a range of
	 * pageblocks to MIGRATE_CMA which can be done by
	 * __free_pageblock_cma() function.  What is important though
	 * is that a range of pageblocks must be aligned to
	 * MAX_ORDER_NR_PAGES should biggest page be bigger then
	 * a single pageblock.
	 */
	MIGRATE_CMA,
#endif
#ifdef CONFIG_MEMORY_ISOLATION
	MIGRATE_ISOLATE,	/* can't allocate from here */
#endif
	MIGRATE_TYPES
};
```

如上，MIGRATE_TYPES 类型包含 MIGRATE_UNMOVABLE、MIGRATE_RECLAIMABLE、MIGRATE_MOVABLE等几种类型，当前页面分配的状态可以从 /proc/pagetypeinfo 中获取到。

- 内存管理中有一个 pageblock 的概念，一个 pageblock 的大小通常是 (MAX_ORDER-1) 个页面。如果体系结构中提供了 HUGETLB_PAGE 特性，那么pageblock_order 定义为 HUGETLB_PAGE_ORDER。

```c
[linux-4.14/include/linux/pageblock-flags.h]
#ifdef CONFIG_HUGETLB_PAGE

#ifdef CONFIG_HUGETLB_PAGE_SIZE_VARIABLE

/* Huge page sizes are variable */
extern unsigned int pageblock_order;

#else /* CONFIG_HUGETLB_PAGE_SIZE_VARIABLE */

/* Huge pages are a constant size */
#define pageblock_order		HUGETLB_PAGE_ORDER

#endif /* CONFIG_HUGETLB_PAGE_SIZE_VARIABLE */

#else /* CONFIG_HUGETLB_PAGE */

/* If huge pages are not used, group by MAX_ORDER_NR_PAGES */
#define pageblock_order		(MAX_ORDER-1)
```

每个 pageblock 有一个相应的 MIGRATE_TYPES 类型。 zone 数据结构中有一个成员指针 pageblock_flags，它指向用于存放每个 pageblock 的 MIGRATE_TYPES 类型的内存空间。 pageblock_flags 指向的内存空间的大小通过 usemap_size() 函数来计算，每个 pageblock 用4个bit为来存放 MIGRATE_TYPES 类型。

zone 初始化函数 free_area_init_core() 在最后会调用 setup_usemap() 函数，setup_usemap() 函数用于计算和分配 pageblock_flags 所需要的大小，并且分配相应的内存。其定义及解析如下：

```c
[linux-4.14/mm/page_alloc.c]
static void __init setup_usemap(struct pglist_data *pgdat,
				struct zone *zone,
				unsigned long zone_start_pfn,
				unsigned long zonesize)
{
  	/* 调用usemap_size计算pageblock_flags指向的内存空间所需要的大小 */
	unsigned long usemapsize = usemap_size(zone_start_pfn, zonesize);
	zone->pageblock_flags = NULL;
	if (usemapsize)
  	/* 通过memblock内存分配机制分配内存 */
		zone->pageblock_flags =
			memblock_virt_alloc_node_nopanic(usemapsize,
							 pgdat->node_id);
}

static unsigned long __init usemap_size(unsigned long zone_start_pfn, unsigned long zonesize)
{
	unsigned long usemapsize;

	zonesize += zone_start_pfn & (pageblock_nr_pages-1);
	usemapsize = roundup(zonesize, pageblock_nr_pages);
	usemapsize = usemapsize >> pageblock_order;
	usemapsize *= NR_PAGEBLOCK_BITS;
	usemapsize = roundup(usemapsize, 8 * sizeof(unsigned long));

	return usemapsize / 8;
}
```

usemap_size() 函数首先计算 zone 有多少个 pageblock，每个 pageblock 需要 4bit (NR_PAGEBLOCK_BITS) 来存储 MIGRATE_TYPES 类型，最后可以计算出需要多少 Byte。然后通过 memblock_virt_alloc_node_nopanic() 函数来分配内存，并且 zone->pageblock_flags 成员指向这段内存。

- 内核有两个函数来管理这些迁移类型：get_pageblock_migratetype() 和 set_pageblock_migratetype()。内核初始化时所有的页面最初都标记为 MIGRATE_MOVABLE 类型，具体操作在 free_area_init_core() -> memmap_init() 函数，free_area_init_core() 函数memmap_init() 函数的调用，上文已解析过，此处不再赘述，以下只对 memmap_init() 函数进行解析，如下：

```c
[linux-4.14/mm/page_alloc.c]
#define memmap_init(size, nid, zone, start_pfn) \
	memmap_init_zone((size), (nid), (zone), (start_pfn), MEMMAP_EARLY)

/*
 * Initially all pages are reserved - free ones are freed
 * up by free_all_bootmem() once the early boot process is
 * done. Non-atomic initialization, single-pass.
 */
void __meminit memmap_init_zone(unsigned long size, int nid, unsigned long zone,
		unsigned long start_pfn, enum memmap_context context)
{
  	/* 获取altmap，根据struct vmem_altmap定义介绍，该结构体主要是为驱动预留出一块内存，所以此处获取到altmap，第5288行就需要更新start_pfn值，to_vmem_altmap()函数可自行解析。 */
	struct vmem_altmap *altmap = to_vmem_altmap(__pfn_to_phys(start_pfn));
	unsigned long end_pfn = start_pfn + size;
	pg_data_t *pgdat = NODE_DATA(nid);
	unsigned long pfn;
	unsigned long nr_initialised = 0;
#ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
	struct memblock_region *r = NULL, *tmp;
#endif

	if (highest_memmap_pfn < end_pfn - 1)
		highest_memmap_pfn = end_pfn - 1;

	/*
	 * Honor reservation requested by the driver for this ZONE_DEVICE
	 * memory
	 */
	if (altmap && start_pfn == altmap->base_pfn)
		start_pfn += altmap->reserve;/* 更新start_pfn，保留[old start_pfn ~ altmap->reserve] 范围的页面供驱动使用。 */

	for (pfn = start_pfn; pfn < end_pfn; pfn++) {
		/*
		 * There can be holes in boot-time mem_map[]s handed to this
		 * function.  They do not exist on hotplugged memory.
		 */
		if (context != MEMMAP_EARLY)
			goto not_early;

		if (!early_pfn_valid(pfn))
			continue;
		if (!early_pfn_in_nid(pfn, nid))
			continue;
		if (!update_defer_init(pgdat, pfn, end_pfn, &nr_initialised))
			break;

#ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
		/*
		 * Check given memblock attribute by firmware which can affect
		 * kernel memory layout.  If zone==ZONE_MOVABLE but memory is
		 * mirrored, it's an overlapped memmap init. skip it.
		 */
		if (mirrored_kernelcore && zone == ZONE_MOVABLE) {
			if (!r || pfn >= memblock_region_memory_end_pfn(r)) {
				for_each_memblock(memory, tmp)
					if (pfn < memblock_region_memory_end_pfn(tmp))
						break;
				r = tmp;
			}
			if (pfn >= memblock_region_memory_base_pfn(r) &&
			    memblock_is_mirror(r)) {
				/* already initialized as NORMAL */
				pfn = memblock_region_memory_end_pfn(r);
				continue;
			}
		}
#endif

not_early:
		/*
		 * Mark the block movable so that blocks are reserved for
		 * movable at startup. This will force kernel allocations
		 * to reserve their blocks rather than leaking throughout
		 * the address space during boot when many long-lived
		 * kernel allocations are made.
		 *
		 * bitmap is created for zone's valid pfn range. but memmap
		 * can be created for invalid pages (for alignment)
		 * check here not to call set_pageblock_migratetype() against
		 * pfn out of zone.
		 */
  		/* 每间隔 pageblock_nr_pages（1024）个页，设置一次migratetype */
		if (!(pfn & (pageblock_nr_pages - 1))) {
			struct page *page = pfn_to_page(pfn);
			/* __init_single_page() 函数对当前页（page）初始化，即对struct page数据成员（page->flags、page->_refcount、page->_mapcount、page->_last_cpupid、page->lru）初始化 */
			__init_single_page(page, pfn, zone, nid);
  		/* 指定pageblock的类型为MIGRATE_MOVABLE */
			set_pageblock_migratetype(page, MIGRATE_MOVABLE);
			cond_resched();
		} else {
  		/* __init_single_pfn() 函数内部调用了__init_single_page（），同5344行实现功能一致 */
			__init_single_pfn(pfn, zone, nid);
		}
	}
}
```

下面着重解析 第5345行 set_pageblock_migratetype() 函数，该函数用于设定 pageblock 的MIGRATE_TYPES 类型，该函数最后调用 set_pfnblock_flags_mask() 来设置 pageblock 的迁移类型，相关函数定义、调用关系及解析如下：

```c
[linux-4.14/include/linux/pageblock-flags.h]
#define set_pageblock_flags_group(page, flags, start_bitidx, end_bitidx) \
	set_pfnblock_flags_mask(page, flags, page_to_pfn(page),		\
			end_bitidx,					\
			(1 << (end_bitidx - start_bitidx + 1)) - 1)

[linux-4.14/mm/page_alloc.c]
/**
 * set_pfnblock_flags_mask - Set the requested group of flags for a pageblock_nr_pages block of pages
 * @page: The page within the block of interest
 * @flags: The flags to set
 * @pfn: The target page frame number
 * @end_bitidx: The last bit of interest
 * @mask: mask of bits that the caller is interested in
 */
void set_pfnblock_flags_mask(struct page *page, unsigned long flags,
					unsigned long pfn,
					unsigned long end_bitidx,
					unsigned long mask)
{
	unsigned long *bitmap;
	unsigned long bitidx, word_bitidx;
	unsigned long old_word, word;

	BUILD_BUG_ON(NR_PAGEBLOCK_BITS != 4);
	/* get_pageblock_bitmap() 函数获取 page 所属内存区域zone的pageblock_flags */
	bitmap = get_pageblock_bitmap(page, pfn);
	bitidx = pfn_to_bitidx(page, pfn);
	word_bitidx = bitidx / BITS_PER_LONG;
	bitidx &= (BITS_PER_LONG-1);

	VM_BUG_ON_PAGE(!zone_spans_pfn(page_zone(page), pfn), page);

	bitidx += end_bitidx;
	mask <<= (BITS_PER_LONG - bitidx - 1);
	flags <<= (BITS_PER_LONG - bitidx - 1);

	word = READ_ONCE(bitmap[word_bitidx]);
	for (;;) {
		old_word = cmpxchg(&bitmap[word_bitidx], word, (word & ~mask) | flags);
		if (word == old_word)
			break;
		word = old_word;
	}
}

void set_pageblock_migratetype(struct page *page, int migratetype)
{
	if (unlikely(page_group_by_mobility_disabled &&
		     migratetype < MIGRATE_PCPTYPES))
		migratetype = MIGRATE_UNMOVABLE;
	/* 调用宏set_pageblock_flags_group， 该宏定义为函数set_pfnblock_flags_mask */
	set_pageblock_flags_group(page, (unsigned long)migratetype,
					PB_migrate, PB_migrate_end);
}
```

