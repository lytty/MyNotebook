# Linux内核内存管理(九)——伙伴系统之一

- 内核初始化完毕后，使用页分配器管理物理页，当前使用页分配器是伙伴分配器，伙伴分配器的特点是算法简单且效率高。

## 1 基本伙伴分配器

>   连续的物理页称为页块（page block）。

>   阶（order）是伙伴系统的一个术语，是页的数量单位，2^n个连续页称为n阶页块。

>   满足以下条件的两个n阶页块称为伙伴（buddy）：

1.  两个页块是相邻的，即物理地址是连续的；
2.  页块的第一页的物理页号必须是2^n的整数倍；
3.  如果合并成（n+1）阶页块，第一页的物理页号必须是2^(n+1)的整数倍。

这是伙伴分配器（buddy allocator）这个名字的来源。以单页为例说明，0号页和1号页是伙伴，2号页和3号页是伙伴，1号页和2号页不是伙伴，因为1号页和2号页合并组成一阶页块，第一页的物理页号不是2的整数倍。

>   物理分配器分配和释放物理页的数量单位是阶。分配n阶页块的过程如下：

1.  查看是否有空闲的n阶页块，如果有，直接分配；如果没有，继续执行下一步；
2.  查看是否有空闲的(n+1)阶页块，如果有，把（n+1）阶页块分裂为两个n阶页块，一个插入空闲n阶页块链表，另一个分配出去；如果没有，继续执行下一步；
3.  查看是否有空闲的(n+2)阶页块，如果有，把（n+2）阶页块分裂为两个（n+1）阶页块，一个插入空闲（n+1）阶页块链表，另一个分裂为两个n阶页块，一个插入空闲n阶页块链表，另一个分配出去；如果没有，继续查看更高阶是否存在空闲页块。

释放n阶页块时，查看它的伙伴释放空闲，如果伙伴不空闲，那么把n阶页块插入空闲的n阶页块链表；如果伙伴空闲，那么合并为（n+1）阶页块。

>   内核在基本的伙伴系统分配器的基础上做了一些扩展：

1.  支持内存节点和区域，称为分区的伙伴分配器（zoned buddy allocator）；
2.  为了预防内存碎片，把物理页根据可移动性分组；
3.  针对分配单页做了性能优化，为了减少处理器之间的锁竞争，在内存区域增加1个每处理器页集合。



## 2 分区伙伴分配器

### 2.1 数据结构

- 分区的伙伴分配器专注于某个内存节点的某个区域。内存区域（`struce zone`）的结构体定义，我们在第四章《内存结构》章节中有做过详细叙述，本节我们只关注伙伴分配器相关的数据成员。
- 内存区域（`struce zone`）的结构体成员`free_area`用来维护空闲页块，数组下标对应页块的阶数。结构体`free_area`的成员`free_list`是空闲页块的链表，`nr_free`是空闲页块的数量。内存区域的结构体成员`managed_pages`是伙伴分配器管理的物理页的数量，不包括引导内存分配器分配的物理页。

```c
/* linux-4.14/include/linux/mmzone.h */

359  struct zone {
		...
436  	unsigned long		managed_pages; /* 伙伴分配器管理的物理页的数量 */
		...
460  
461  	/* free areas of different sizes */
462  	struct free_area	free_area[MAX_ORDER]; /* 不同长度的空闲区域 */
		...
509  } ____cacheline_internodealigned_in_smp;

96  struct free_area {
97  	struct list_head	free_list[MIGRATE_TYPES];
98  	unsigned long		nr_free;
99  };
```

`MAX_ORDER`是最大阶数，实际上是可分配的最大阶数加1，默认值是11，意味着伙伴分配器一次最多可以分配 2^10 页。可以使用配置宏 `CONFIG_FORCE_MAX_ZONEORDER` 指定最大阶数。

```c
/* linux-4.14/include/linux/mmzone.h */

23  /* Free memory management - zoned buddy allocator. 空闲内存管理-分区的伙伴分配器 */
24  #ifndef CONFIG_FORCE_MAX_ZONEORDER
25  #define MAX_ORDER 11
26  #else
27  #define MAX_ORDER CONFIG_FORCE_MAX_ZONEORDER
28  #endif
29  #define MAX_ORDER_NR_PAGES (1 << (MAX_ORDER - 1))
```

### 2.2 根据分配标志得到首选区域类型

- 分配标志位，也叫分配掩码，其在内核代码中分成两类，一类叫`zone modifiers`，另一类叫`action modifiers`。`zone modifiers`指定从哪个`zone`中分配所需的页面。`zone modifiers`由分配掩码的最低4位来定义：

```c
[linux-4.14/include/linux/gfp.h]

19  #define ___GFP_DMA			0x01u
20  #define ___GFP_HIGHMEM		0x02u
21  #define ___GFP_DMA32		0x04u
22  #define ___GFP_MOVABLE		0x08u

```

- 分配掩码的不同组合对应不同的内存区域类型，其对应关系如下：

|           分配掩码组合            |     区域类型     |
| :-------------------------------: | :--------------: |
|                 0                 |   ZONE_NORMAL    |
|             __GFP_DMA             |   OPT_ZONE_DMA   |
|           __GFP_HIGHMEM           | OPT_ZONE_HIGHMEM |
|            __GFP_DMA32            |  OPT_ZONE_DMA32  |
|           __GFP_MOVABLE           |   ZONE_NORMAL    |
|   (`__GFP_MOVABLE | __GFP_DMA`)   |   OPT_ZONE_DMA   |
| (`__GFP_MOVABLE | __GFP_HIGHMEM`) |  ZONE_MOVEABLE   |
|  (`__GFP_MOVABLE | __GFP_DMA32`)  |  OPT_ZONE_DMA32  |

为什么要使用`OPT_ZONE_DMA`，而不使用`ZONE_DMA`？

这是因为`DMA`区域是可选的，如果不存在只能访问16MB以下物理内存的外围设备，那么不需要定义`DMA`区域，`OPT_ZONE_DMA`就是`ZONE_NORMAL`，从普通区域申请页。高端内存区域`HIGHMEM`和`DMA32`区域也是可选的。

```c
[linux-4.14/include/linux/gfp.h]
316  #ifdef CONFIG_HIGHMEM
317  #define OPT_ZONE_HIGHMEM ZONE_HIGHMEM
318  #else
319  #define OPT_ZONE_HIGHMEM ZONE_NORMAL
320  #endif
321  
322  #ifdef CONFIG_ZONE_DMA
323  #define OPT_ZONE_DMA ZONE_DMA
324  #else
325  #define OPT_ZONE_DMA ZONE_NORMAL
326  #endif
327  
328  #ifdef CONFIG_ZONE_DMA32
329  #define OPT_ZONE_DMA32 ZONE_DMA32
330  #else
331  #define OPT_ZONE_DMA32 ZONE_NORMAL
332  #endif

```

- 内核使用宏`GFP_ZONE_TABLE`定义了分配标志（分配掩码）组合到区域类型的映射表，其中`GFP_ZONES_SHIFT`是区域类型占用的位数，`GFP_ZONE_TABLE`把每种标志组合映射到32位整数的某个位置，偏移是（标志组合 * 区域类型位数），从这个偏移开始的`GFP_ZONES_SHIFT`个二进制位存放区域类型。宏`GFP_ZONE_TABLE`是一个常量，编译器在编译时会进行优化，直接计算出结果，不会等到运行程序的时候才计算数值。

```c
[linux-4.14/include/linux/gfp.h]
378  #define GFP_ZONE_TABLE ( \
379  	(ZONE_NORMAL << 0 * GFP_ZONES_SHIFT)				      				 \
380  	| (OPT_ZONE_DMA << ___GFP_DMA * GFP_ZONES_SHIFT)		       			 \
381  	| (OPT_ZONE_HIGHMEM << ___GFP_HIGHMEM * GFP_ZONES_SHIFT)	       		 \
382  	| (OPT_ZONE_DMA32 << ___GFP_DMA32 * GFP_ZONES_SHIFT)		       		 \
383  	| (ZONE_NORMAL << ___GFP_MOVABLE * GFP_ZONES_SHIFT)		       			 \
384  	| (OPT_ZONE_DMA << (___GFP_MOVABLE | ___GFP_DMA) * GFP_ZONES_SHIFT)      \
385  	| (ZONE_MOVABLE << (___GFP_MOVABLE | ___GFP_HIGHMEM) * GFP_ZONES_SHIFT)  \
386  	| (OPT_ZONE_DMA32 << (___GFP_MOVABLE | ___GFP_DMA32) * GFP_ZONES_SHIFT)  \
387  )

```

- 内核使用函数`gfp_zone()`根据分配标志得到首选的区域类型：先分离出区域标志位，然后算出在映射表（`GFP_ZONE_TABLE`）中的偏移（标志组合 * 区域类型位数），接着把映射表右移偏移值，最后取出最低的区域类型位数。

```c
[linux-4.14/include/linux/gfp.h]

61  #define GFP_ZONEMASK	(__GFP_DMA|__GFP_HIGHMEM|__GFP_DMA32|__GFP_MOVABLE)

  334  /*
  335   * GFP_ZONE_TABLE is a word size bitstring that is used for looking up the
  336   * zone to use given the lowest 4 bits of gfp_t. Entries are GFP_ZONES_SHIFT
  337   * bits long and there are 16 of them to cover all possible combinations of
  338   * __GFP_DMA, __GFP_DMA32, __GFP_MOVABLE and __GFP_HIGHMEM.
  339   *
  340   * The zone fallback order is MOVABLE=>HIGHMEM=>NORMAL=>DMA32=>DMA.
  341   * But GFP_MOVABLE is not only a zone specifier but also an allocation
  342   * policy. Therefore __GFP_MOVABLE plus another zone selector is valid.
  343   * Only 1 bit of the lowest 3 bits (DMA,DMA32,HIGHMEM) can be set to "1".
  344   *
  345   *       bit       result
  346   *       =================
  347   *       0x0    => NORMAL
  348   *       0x1    => DMA or NORMAL
  349   *       0x2    => HIGHMEM or NORMAL
  350   *       0x3    => BAD (DMA+HIGHMEM)
  351   *       0x4    => DMA32 or DMA or NORMAL
  352   *       0x5    => BAD (DMA+DMA32)
  353   *       0x6    => BAD (HIGHMEM+DMA32)
  354   *       0x7    => BAD (HIGHMEM+DMA32+DMA)
  355   *       0x8    => NORMAL (MOVABLE+0)
  356   *       0x9    => DMA or NORMAL (MOVABLE+DMA)
  357   *       0xa    => MOVABLE (Movable is valid only if HIGHMEM is set too)
  358   *       0xb    => BAD (MOVABLE+HIGHMEM+DMA)
  359   *       0xc    => DMA32 (MOVABLE+DMA32)
  360   *       0xd    => BAD (MOVABLE+DMA32+DMA)
  361   *       0xe    => BAD (MOVABLE+DMA32+HIGHMEM)
  362   *       0xf    => BAD (MOVABLE+DMA32+HIGHMEM+DMA)
  363   *
  364   * GFP_ZONES_SHIFT must be <= 2 on 32 bit platforms.
  365   */
  366  
  367  #if defined(CONFIG_ZONE_DEVICE) && (MAX_NR_ZONES-1) <= 4
  368  /* ZONE_DEVICE is not a valid GFP zone specifier */
  369  #define GFP_ZONES_SHIFT 2
  370  #else
  371  #define GFP_ZONES_SHIFT ZONES_SHIFT
  372  #endif    

  389  /*
  390   * GFP_ZONE_BAD is a bitmap for all combinations of __GFP_DMA, __GFP_DMA32
  391   * __GFP_HIGHMEM and __GFP_MOVABLE that are not permitted. One flag per
  392   * entry starting with bit 0. Bit is set if the combination is not
  393   * allowed.
  394   */
  395  #define GFP_ZONE_BAD ( \
  396  	1 << (___GFP_DMA | ___GFP_HIGHMEM)				      \
  397  	| 1 << (___GFP_DMA | ___GFP_DMA32)				      \
  398  	| 1 << (___GFP_DMA32 | ___GFP_HIGHMEM)				      \
  399  	| 1 << (___GFP_DMA | ___GFP_DMA32 | ___GFP_HIGHMEM)		      \
  400  	| 1 << (___GFP_MOVABLE | ___GFP_HIGHMEM | ___GFP_DMA)		      \
  401  	| 1 << (___GFP_MOVABLE | ___GFP_DMA32 | ___GFP_DMA)		      \
  402  	| 1 << (___GFP_MOVABLE | ___GFP_DMA32 | ___GFP_HIGHMEM)		      \
  403  	| 1 << (___GFP_MOVABLE | ___GFP_DMA32 | ___GFP_DMA | ___GFP_HIGHMEM)  \
  404  )

  406  static inline enum zone_type gfp_zone(gfp_t flags)
  407  {
  408  	enum zone_type z;
  409  	int bit = (__force int) (flags & GFP_ZONEMASK); // 获取区域标志位
  410  
  411  	z = (GFP_ZONE_TABLE >> (bit * GFP_ZONES_SHIFT)) &
  412  					 ((1 << GFP_ZONES_SHIFT) - 1);
  413  	VM_BUG_ON((GFP_ZONE_BAD >> bit) & 1);
  414  	return z;
  415  }
```



## 3 备用区域列表

>   如果首选的内存节点和区域（zone）不能满足页分配请求，可以从备用的内存区域借用物理页，借用必须遵守以下原则。

1.  一个内存节点的某个区域类型可以从另一个内存节点的相同区域类型借用物理页，例如节点0的普通区域可以从节点1的普通区域借用物理页。
2.  高区域类型可以从低区域类型借用物理页，例如普通区域类型可以从DMA区域借用物理页。
3.  低区域类型不能从高区域类型借用物理页，例如DMA区域不能从普通区域借用物理页。

>   内存节点的`pg_data_t`实例定义了备用区域列表，其代码如下：

```c
// linux-4.14/include/linux/mmzone.h

624  typedef struct pglist_data {
	...
626  	struct zonelist node_zonelists[MAX_ZONELISTS]; /*备用区域（zone）列表*/
		...
730  } pg_data_t;

568  /* Maximum number of zones on a zonelist */
569  #define MAX_ZONES_PER_ZONELIST (MAX_NUMNODES * MAX_NR_ZONES)
570  
571  enum {
572  	ZONELIST_FALLBACK,	/* zonelist with fallback 包含所有内存节点的备用区域列表*/
573  #ifdef CONFIG_NUMA
574  	/*
575  	 * The NUMA zonelists are doubled because we need zonelists that
576  	 * restrict the allocations to a single node for __GFP_THISNODE.
577  	 */
578  	ZONELIST_NOFALLBACK,	/* zonelist without fallback (__GFP_THISNODE) 只包含当前内存节点的备用区域列表*/
579  #endif
580  	MAX_ZONELISTS
581  };

606  struct zonelist {
607  	struct zoneref _zonerefs[MAX_ZONES_PER_ZONELIST + 1];
608  };

583  /*
584   * This struct contains information about a zone in a zonelist. It is stored
585   * here to avoid dereferences into large structures and lookups of tables
586   */
587  struct zoneref {
588  	struct zone *zone;	/* Pointer to actual zone 指向内存区域的数据结构*/
589  	int zone_idx;		/* zone_idx(zoneref->zone) 内存区域zone的类型*/
590  };

```

UMA系统只有一个备用区域列表，按区域类型从高到底排序。假设UMA系统包含普通区域类型和DMA区域类型，那么备用区域列表是：{普通区域，DMA区域}。

NUMA系统的每个内存节点有两个备用区域列表：一个包含所有内存节点的备用区域列表，另一个只包含当前内存节点的备用区域列表。如果申请页时指定标志`__GFP_THISNODE`，要求只能从指定内存节点分配物理页，就需要使用指定内存节点的第二个备用区域列表。

>   包含所有内存节点的备用区域列表有两种排序方法：

1.  节点优先排序：先根据节点距离从小到大排序，然后在每个节点里面根据区域类型从高到底排序。
2.  区域优先排序：先根据区域类型从高到底排序，然后在每个区域类型里面根据节点距离从小到大排序。

节点优先排序的优点是优先选择距离近的内存，缺点是在高区域耗尽以前就使用低区域，例如DMA区域一般比较小，节点优选顺序会增大DMA区域耗尽的概率。

区域优选排序的优点是减小低区域耗尽的概率，缺点是不能保证优先选择距离近的内存。

>   默认的排序方法是自动选择最优的排序方法：如果是64位系统，因为需要DMA和DMA32区域的设备相对少，所以选择节点优先顺序；如果是32位系统，选择区域优选顺序。

可以使用内核参数`numa_zonelist_order`指定排序方法：`d`表示默认排序方法，`n`表示节点优选顺序，`z`表示区域优先顺序，大小写字母都可以。在运行中可以使用文件`/proc/sys/numa_zonelist_order`修改排序方法。



## 4 区域水线

>   首先的内存区域在什么情况下从备用区域借用物理页？这个问题要从区域水线开始说起。每个内存区域有3个水线。

1.  高水线（high）：如果内存区域的空闲页数大于高水线，说明该内存区域的内存充足。
2.  低水线（low）：如果内存区域的空闲页数小于低水线，说明该内存区域的内存轻微不足。
3.  最低水线（min）：如果内存区域的空闲页数小于最低水线，说明该内存区域的内存严重不足。

```c
[linux-4.14/include/linux/mmzone.h]

263  enum zone_watermarks {
264  	WMARK_MIN,
265  	WMARK_LOW,
266  	WMARK_HIGH,
267  	NR_WMARK
268  };

359  struct zone {
		...
362  	/* zone watermarks, access with *_wmark_pages(zone) macros 区域水线，使用*_wmark_pages(zone) 宏访问 */
363  	unsigned long watermark[NR_WMARK];
		...
509  } ____cacheline_internodealigned_in_smp;

```

>   最低水线以下的内存称为紧急保留内存，在内存严重不足的紧急情况下，给承诺“给我少量紧急保留内存使用，我可以释放更多的内存”的进程使用。

>   设置了进程标志位`PF_MEMALLOC`的进程可以使用紧急保留内存，标志位`PF_MEMALLOC`表示承诺“给我少量紧急保留内存使用，我可以释放更多的内存”。内存管理子系统以外的子系统不应该使用这个标志位，典型的例子是页回收内核线程`kswapd`，在回收页的过程中可能需要申请内存。

>   如果申请页时设置了标志位`__GFP_MEMALLOC`，即调用者承诺“给我少量紧急保留内存使用，我可以释放更多的内存”，那么可以使用紧急保留内存。

>   申请页时，第一次尝试使用低水线，如果首选的内存区域的空闲页数小于低水线，就从备用的内存区域借用物理页。如果第一次分配失败，那么唤醒所有目标内存节点的页回收内核线程`kswapd`以异步回收页，然后尝试使用最低水线。如果首选的内存区域的空闲页数小于最低水线，就从备用的内存区域借用物理页。

>   计算水线时，有两个重要的参数：

1.  `min_free_kbytes`是最小空闲字节数。默认值 = 4*sqrt{lowmem_kbytes}, 并且限制在范围[128,65536]以内。其中`lowmem_kbytes`是低端内存大小，单位是KB。参考文件`mm/page_alloc.c`中的函数`init_per_zone_wmark_min`。可以通过文件`/proc/sys/vm/min_free_kbytes`设置最小空闲字节数。
2.  `watermark_scale_factor`是水线缩放因子。默认值是10，可以通过文件`/proc/sys/vm/watermark_scale_factor`修改水线缩放因子，取值范围[1, 1000]。

>   文件`mm/page_alloc.c`中的函数`__setup_per_zone_wmarks()`负责计算每个内存区域的最低水线、低水线、高水线。计算最低水线的方法如下：

1.  `min_free_pages` = `min_free_kbytes`对应的页数。
2.  `lowmem_pages` = 所有低端内存区域中伙伴系统分配器管理的页数总和。
3.  高端内存区域的最低水线 = `zone->managed_pages/1024`，并且限制在范围[32, 128]以内（`zone->managed_pages`是该内存区域中伙伴分配器管理的页数，在内核初始化的过程中引导内存分配器分配出去的物理页，不收伙伴分配器管理）。
4.  低端内存区域的最低水线 = `min_free_pages * zone->managed_pages/lowmem_pages`,即把`min_free_pages`按比例分配到每个低端内存区域。

>   计算低水线和高水线的方法如下：

1.  增量 = （最低水线/4, `zone->managed_pages * watermark_scale_factor/10000`）取最大值。
2.  低水线 = 最低水线 + 增量。
3.  高水线 = 最低水线 + 增量 * 2。

>   如果（最低水线/4）比较大，那么计算公式简化如下：

1.  低水线 = 最低水线 * 5/4。
2.  高水线 = 最低水线 * 3/2。



## 5 防止过度借用

- 和高区域类型相比，低区域类型的内存相对少，是稀缺资源，而且有特殊用途，例如DMA区域用于外围设备和内存之间的数据传输。为了防止高区域类型过度借用低区域类型的物理页，低区域类型需要采取防卫措施，保留一定数量的物理页。
- 一个内存节点的某个区域类型从另一个内存节点的相同区域类型借用物理页，后者应该毫无保留地借用。
- 内存区域有一个数组用于存放保留页数：

```c
[linux-4.14/include/linux/mmzone.h]

359  struct zone {
		...
376  	long lowmem_reserve[MAX_NR_ZONES];
		...
509  } ____cacheline_internodealigned_in_smp;

```

`zone[i]->lowmen_reserve[j]`表示区域类型 i 应该保留多少页不能借给区域类型 j，仅当j大于i时有意义。

`zone[i]->lowmen_reserve[j]`的计算规则如下：

```
(i < j):
zone[i]->lowmen_reserve[j]
= (当前内存节点上从zone[i+1] 到zone[j]伙伴分配器管理的页数总和) / sysctl_lowmem_reserve_ratio[i]
(i = j):
zone[i]->lowmen_reserve[j] = 0 (相同的区域类型不应该保留)
(i < j):
zone[i]->lowmen_reserve[j] = 0 (没意义，不会出现地区与类型从高区域类型借用物理页的情况)

```

数组`sysctl_lowmem_reserve_ratio`存放各种区域类型的保留比例，因为内核不允许使用浮点数，所以使用倒数值。DMA区域和DMA32区域的默认保留比例都是256，普通区域和高端内存区域的默认保留比例都是32.

```c
[linux-4.14/mm/page_alloc.c]

205  int sysctl_lowmem_reserve_ratio[MAX_NR_ZONES-1] = {
206  #ifdef CONFIG_ZONE_DMA
207  	 256,
208  #endif
209  #ifdef CONFIG_ZONE_DMA32
210  	 256,
211  #endif
212  #ifdef CONFIG_HIGHMEM
213  	 32,
214  #endif
215  	 32,
216  };

```

可以通过文件`/proc/sys/vm/lowmem_reserve_ratio`修改各种区域类型的保留比例。



## 6 根据可移动性分组

- 在系统长时间运行后，物理内存可能出现很多碎片，可用物理页很多，但是最大的连续物理内存可能只有一页，内存碎片对用户程序不是问题，因为用户程序可以通过页表把连续的虚拟页映射到不连续的物理页。但是内存碎片对内核是一个问题，因为内核使用直接映射的虚拟地址空间，连续的虚拟页必须映射到连续的物理页。内存碎片是伙伴分配器的一个弱点。
- 为了预防内存碎片，内核根据可移动性把物理页分为3种类型：

1.  不可移动页：位置必须固定，不能移动，直接映射到内核虚拟地址空间的页属于这一类。
2.  可移动页：使用页表映射的页属于这一类，可移动到其他位置，然后修改页表映射。
3.  可回收页：不能移动，但可以回收，需要数据的时候可以重新从数据源获取，后备存储设备支持的页属于这一类。

- 内核把具有相同可移动性的页分组。为什么这种方法可以减少碎片？试想：如果不可移动页出现在可移动内存区域的中间，会阻止可移动内存区域合并。这种方法把不可移动页聚集在一起，可以防止不可移动页出现在可移动内存区域的中间。
- 内核定义了以下迁移类型：

```c
[linux-4.14/include/linux/mmzone.h]

39  enum migratetype {
40  	MIGRATE_UNMOVABLE, /* 不可移动 */
41  	MIGRATE_MOVABLE,   /* 可移动 */
42  	MIGRATE_RECLAIMABLE,	/* 可回收 */
43  	MIGRATE_PCPTYPES,	/* the number of types on the pcp lists 定义内存区域的每处理器页集合中链表的数量*/
44  	MIGRATE_HIGHATOMIC = MIGRATE_PCPTYPES,	/* 高阶原子分配，即阶数大于0，并且分配时不能睡眠等待 */
45  #ifdef CONFIG_CMA
59  	MIGRATE_CMA,	/* 连续内存分配器 */
60  #endif
61  #ifdef CONFIG_MEMORY_ISOLATION
62  	MIGRATE_ISOLATE,	/* can't allocate from here， 隔离，不能从这里分配 */
63  #endif
64  	MIGRATE_TYPES
65  };

```

前面3种是真正的迁移类型，后面的迁移类型有特殊用途：`MIGRATE_HIGHATOMIC`用于高阶原子分配，`MIGRATE_CMA`用于连续内存分配器，`MIGRATE_ISOLATE`用来隔离物理页（由连续内存分配器、内存热插拔和从内存硬件错误恢复等功能使用）。

- 对伙伴分配器的数据结构的主要调整是把空闲链表拆分成每种迁移类型一条空闲链表。

```c
[linux-4.14/include/linux/mmzone.h]
96  struct free_area {
97  	struct list_head	free_list[MIGRATE_TYPES];
98  	unsigned long		nr_free;
99  };

```

- 只有当物理内存足够大且每种迁移类型有足够多的物理页时，根据可移动性分组才有意义。全局变量`page_group_by_mobility_disabled`表示是否禁用根据可移动性分组。`vm_total_pages`是所有内存区域里面高水线以上的物理页总数，`pageblock_order`是按可移动性分组的阶数，`pageblock_nr_pages`是`pageblock_order`对应的页数。如果所有内存区域里面高水线以上物理页总数小于（`pageblock_nr_pages` * 迁移类型数量），那么禁用根据可移动性分组。

```c
[linux-4.14/mm/page_alloc.c]

5234  void __ref build_all_zonelists(pg_data_t *pgdat)
5235  {
		...
5243  	/*
5244  	 * Disable grouping by mobility if the number of pages in the
5245  	 * system is too low to allow the mechanism to work. It would be
5246  	 * more accurate, but expensive to check per-zone. This check is
5247  	 * made on memory-hotadd so a system can start with mobility
5248  	 * disabled and enable it later
5249  	 */
5250  	if (vm_total_pages < (pageblock_nr_pages * MIGRATE_TYPES))
5251  		page_group_by_mobility_disabled = 1;
5252  	else
5253  		page_group_by_mobility_disabled = 0;
		...
5262  }

```

- `pageblock_order`是按可移动性分组的阶数，简称分组阶数，可以理解为一种迁移类型的一个页块的最小长度。如果内核支持巨型页，那么`pageblock_order`是巨型页的阶数，否则`pageblock_order`是伙伴分配器的最大分配阶。

```c
[linux-4.14/include/linux/pageblock-flags.h]

42  #ifdef CONFIG_HUGETLB_PAGE
44  #ifdef CONFIG_HUGETLB_PAGE_SIZE_VARIABLE
45  
46  /* Huge page sizes are variable 巨型页长度是可变的*/
47  extern unsigned int pageblock_order;
49  #else /* CONFIG_HUGETLB_PAGE_SIZE_VARIABLE */
51  /* Huge pages are a constant size 巨型页长度是固定的*/
52  #define pageblock_order		HUGETLB_PAGE_ORDER
54  #endif /* CONFIG_HUGETLB_PAGE_SIZE_VARIABLE */
55  
56  #else /* CONFIG_HUGETLB_PAGE */
58  /* If huge pages are not used, group by MAX_ORDER_NR_PAGES 如果编译内核时没有开启巨型页，按伙伴分配器的最大分配阶分组*/
59  #define pageblock_order		(MAX_ORDER-1)
61  #endif /* CONFIG_HUGETLB_PAGE */
62  
63  #define pageblock_nr_pages	(1UL << pageblock_order)

```

- 申请页时，可以使用标志`__GFP_MOVABLE`指定申请可移动页，使用`__GFP_RECLAIMABLE`指定申请可回收页，如果没有指定这两个标志，表示申请不可移动页。函数`gfpflags_to_migratetype`用来把分配标志转换成迁移类型：

```c
[linux-4.14/include/linux/gfp.h]

292  /* Convert GFP flags to their corresponding migrate type 把分配标志转换成迁移类型*/
293  #define GFP_MOVABLE_MASK (__GFP_RECLAIMABLE|__GFP_MOVABLE)
294  #define GFP_MOVABLE_SHIFT 3
295  
296  static inline int gfpflags_to_migratetype(const gfp_t gfp_flags)
297  {
		...
302  	if (unlikely(page_group_by_mobility_disabled))
303  		return MIGRATE_UNMOVABLE;
304  
305  	/* Group based on mobility 根据可移动性分组*/
306  	return (gfp_flags & GFP_MOVABLE_MASK) >> GFP_MOVABLE_SHIFT;
307  }

```

如果禁用根据可移动性分组，那么总是申请不可移动页。

- 申请某种迁移类型的页时，如果这种迁移类型的页用完了，可以从其他迁移类型盗用（steal）物理页。内核定义了每种迁移类型的备用类型优先级列表：

```c
[linux-4.14/mm/page_alloc.c]

1829  /*
1830   * This array describes the order lists are fallen back to when
1831   * the free lists for the desirable migrate type are depleted
1832   */
1833  static int fallbacks[MIGRATE_TYPES][4] = {
1834  	[MIGRATE_UNMOVABLE]   = { MIGRATE_RECLAIMABLE, MIGRATE_MOVABLE,   MIGRATE_TYPES },
1835  	[MIGRATE_RECLAIMABLE] = { MIGRATE_UNMOVABLE,   MIGRATE_MOVABLE,   MIGRATE_TYPES },
1836  	[MIGRATE_MOVABLE]     = { MIGRATE_RECLAIMABLE, MIGRATE_UNMOVABLE, MIGRATE_TYPES },
1837  #ifdef CONFIG_CMA
1838  	[MIGRATE_CMA]         = { MIGRATE_TYPES }, /* Never used */
1839  #endif
1840  #ifdef CONFIG_MEMORY_ISOLATION
1841  	[MIGRATE_ISOLATE]     = { MIGRATE_TYPES }, /* Never used */
1842  #endif
1843  };

```

不可移动类型的备用类型按优先级从高到低是：可回收类型、可移动类型；可回收类型的备用类型按优先级从高到低是：不可移动类型、可移动类型；可移动类型的备用类型按优先级从高到低是：可回收类型、不可移动类型。

- 如果需要从备用类型盗用物理页，那么从最大的页块开始盗用，以避免产生碎片。

```c
[linux-4.14/mm/page_alloc.c]

  2217  /*
  2218   * Try finding a free buddy page on the fallback list and put it on the free
  2219   * list of requested migratetype, possibly along with other pages from the same
  2220   * block, depending on fragmentation avoidance heuristics. Returns true if
  2221   * fallback was found so that __rmqueue_smallest() can grab it.
  2222   *
  2223   * The use of signed ints for order and current_order is a deliberate
  2224   * deviation from the rest of this file, to make the for loop
  2225   * condition simpler.
  2226   */
  2227  static inline bool
  2228  __rmqueue_fallback(struct zone *zone, int order, int start_migratetype)
  2229  {
  		...
  2236  	/*
  2237  	 * Find the largest available free page in the other list. This roughly
  2238  	 * approximates finding the pageblock with the most free pages, which
  2239  	 * would be too costly to do exactly.
  		 * 在备用类型的页块链表中查找最大的页块

    2240  	 */
    2241  	for (current_order = MAX_ORDER - 1; current_order >= order;
    2242  				--current_order) {
    2243  		area = &(zone->free_area[current_order]);
    2244  		fallback_mt = find_suitable_fallback(area, current_order,
    2245  				start_migratetype, false, &can_steal);
    	 		...
    2262  	}
    
      	...
  2293  }

```

- 释放物理页的时候，需要把物理页插入物理页所属迁移类型的空闲链表，内核怎么知道物理页的迁移类型？内存区域的`zone`结构体成员`pageblock_flags`指向页块标志位图，页块的大小是分组阶数`pageblock_order`，我们把这种页块称为分组页块。

```c
[linux-4.14/include/linux/mmzone.h]

359  struct zone {
	 ...
384  #ifndef CONFIG_SPARSEMEM
385  	/*
386  	 * Flags for a pageblock_nr_pages block. See pageblock-flags.h.
387  	 * In SPARSEMEM, this map is stored in struct mem_section
		 * 分组页块的标志参考文件pageblock-flags.h
		 * 如果使用稀疏内存模型，这个位图在结构体 mem_section 中。
388  	 */
389  	unsigned long		*pageblock_flags;
390  #endif /* CONFIG_SPARSEMEM */
	 ...
509  } ____cacheline_internodealigned_in_smp;

```

每个分组页块在位图中占用4位，其中3位用来存放页块的迁移类型。

```c
[linux-4.14/include/linux/pageblock-flags.h]

28  /* Bit indices that affect a whole block of pages 影响一个页块的位索引*/
29  enum pageblock_bits {
30  	PB_migrate,
31  	PB_migrate_end = PB_migrate + 3 - 1,
32  			/* 3 bits required for migrate types 迁移类型需要3位 */
33  	PB_migrate_skip,/* If set the block is skipped by compaction 如果被设置，内存碎片整理跳过这个页块 */
34  
35  	/*
36  	 * Assume the bits will always align on a word. If this assumption
37  	 * changes then get/set pageblock needs updating.
38  	 */
39  	NR_PAGEBLOCK_BITS
40  };

```

- 函数`set_pageblock_migratetype()`用来在页块标志位图中设置页块的迁移类型，函数`get_pageblock_migratetype()`用来获取页块的迁移类型。

-   内核在初始化时，把所有的页块初始化位可移动类型，其他迁移类型的页是盗用产生的。

```c
free_area_init_core() -> free_area_init_core() -> memmap_init() -> memmap_init_zone()
[linux-4.14/mm/page_alloc.c]

5269  void __meminit memmap_init_zone(unsigned long size, int nid, unsigned long zone,
5270  		unsigned long start_pfn, enum memmap_context context)
5271  {
		...
5291  	for (pfn = start_pfn; pfn < end_pfn; pfn++) {
			...
5341  		if (!(pfn & (pageblock_nr_pages - 1))) { /* 如果是分组页块的第一页 */
5342  			struct page *page = pfn_to_page(pfn);
5343  
5344  			__init_single_page(page, pfn, zone, nid);
5345  			set_pageblock_migratetype(page, MIGRATE_MOVABLE);
5346  			cond_resched();
5347  		} else {
5348  			__init_single_pfn(pfn, zone, nid);
5349  		}
5350  	}
5351  }

```

可以通过文件`/proc/pagetypeinfo`查看各种迁移类型的页的分布情况。



## 7 每处理器页集合

- 内核针对分配单页做了性能优化，为了减少处理器之间的锁竞争，在内存区域增加1个每处理器页集合。

```c
[linux-4.14/include/linux/mmzone.h]

359  struct zone {
		...
382  	struct per_cpu_pageset __percpu *pageset;/* 在每个处理器上有一个页集合 */
		...
509  } ____cacheline_internodealigned_in_smp;

274  struct per_cpu_pages {
275  	int count;		/* number of pages in the list 链表里页的数量 */
276  	int high;		/* high watermark, emptying needed 如果页的数量达到高水线，需要返还给伙伴分配器 */
277  	int batch;		/* chunk size for buddy add/remove 批量添加或删除的页数量 */
278  
279  	/* Lists of pages, one per migrate type stored on the pcp-lists 每种迁移类型一个页链表 */
280  	struct list_head lists[MIGRATE_PCPTYPES];
281  };
282  
283  struct per_cpu_pageset {
284  	struct per_cpu_pages pcp;
		...
293  };

```

内存区域在每个处理器上有一个页集合，页集合中每种迁移类型有一个页链表，页集合有高水线和批量值，页集合中页数量不能超过高水线。申请单页加入页链表，或者从页链表返还给伙伴分配器，都是采用批量操作，一次操作的页数量是批量值。

默认的批量值`batch`的计算方法如下：

1.  batch = zone->managed_pages/1024, 其中zone->managed_pages是内存区域中由伙伴分配器管理的页数量。
2.  如果batch超过`(512*1024)/PAGE_SIZE`，那么把batch设置为 (512*1024）/PAGE_SIZE，其中PAGE_SIZE是页长度。
3.  batch = batch/4
4.  batch = rounddown_pow_of_two(batch * 1.5) - 1，其中 rounddown_pow_of_two() 用于把数值向下对齐到2的n次幂

默认的高水线是批量值的6倍。

可以通过文件`/proc/sys/vm/percpu_pagelist_fraction`修改比例值，最小值是8，默认值是0。高水线等于（伙伴分配器管理的页数量/比例值），同时把批量值被设置位高水线的1/4。

- 从某个内存区域申请某种迁移类型的单页时，从当前处理器的页集合中该迁移类型的页链表分配页，如果页链表是空的，先批量申请页加入页链表，然后分配一页。
- 缓存热页是指刚刚访问过的物理页，物理页的数据还在处理器的缓存中，如果要申请缓存热页，从页链表首部分配页；如果要申请缓存冷页，从页链表尾部分配页。
- 释放单页时，把页加入当前处理器的页集合中。如果释放缓存热页，加入页链表首部；如果释放缓存冷页，加入页链表尾部。如果页集合中的页数量大于或高于高水线，那么批量返还给伙伴分配器。
