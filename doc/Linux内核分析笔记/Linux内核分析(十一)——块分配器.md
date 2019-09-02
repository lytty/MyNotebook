# Linux内核分析(十一)——块分配器

## 11.1 概述

- 伙伴系统用于分配内存时是以`page`为单位的，而在实际中有很多内存需求是以`Byte`为单位的，为了解决小块内存的分配问题，Linux内核提供了块分配器，最早实现的块分配器是`slab`分配器。

- slab分配器的左右不仅仅是分配小块内存，更重要的作用是针对经常分配和释放的对象充当缓存，slab分配器的核心思想是：为每种对象类型创建一个内存缓存，每个内存缓存由多个大块（salb，原意是大块的混凝土）组成，一个大块是一个或多个连续的物理页，每个大块包含多个对象。slab采用了面向对象的思想，基于对象类型管理内存，每种对象被划分为一类，例如进程描述符（task_struct）是一个类，每个进程描述符实例是一个对象，内存缓存的组成如下图：          ![1567414992599](../picture/内存缓存的组成.png)

- slab分配器在某些情况下表现不太好，所有Linux内核提供了两个改进的块分配器：

  > 1. 在配备了大量物理内存的大型计算机上，slab分配器的管理数据结构的内存开销比较大，所以设计了`slub`分配器；
  > 2. 在小内存的嵌入式设备上，slab分配器的代码太多，太复杂，所以设计了一个精简的`slob`分配器，slob是`Simple List Of Blocks`的缩写，意思是简单的块链表。

  目前`slub`分配器已成为默认的块分配器。

- slab分配器最终还是由伙伴系统来分配出实际的物理页面，只不过slab分配器在这些连续的物理页面上实现了自己的算法，以此来对小内存块进行管理。



## 11.2 编程接口

- 3种块分配器（`slab`，`slub`，`slob`）提供了统一的编程接口。

- 为了方便使用，块分配器在初始化的时候创建了一些通用的内存缓存，对象的长度大多是 2^n 字节，从普通区域分配页的内存缓存的名称是`kmalloc-<size>`(size 是对象的长度)，从DMA区域分配页的内存缓存的名称是`dma-kmalloc-<size>`，执行命令`cat/proc/slabinfo`可以看到这些通用的内存缓存。

- 通用的内存缓存的编程接口：

  > 分配内存

  ```c
  void *kmalloc(size_t size, gfp_t flags);
  size: 需要的内存长度；
  flags: 传给页分配器的分配标志位，当内存缓存没有空闲对象，向页分配器请求分配页的时候使用这个分配标志位。
  页分配器找到一个合适的通用内存缓存：对象的长度刚好大于或等于请求的内存长度，然后从这个内存缓存分配对象。如果分配成功，返回对象的地址，否则返回空指针。
  
  ```

  > 重新分配内存

  ```c
  void *krealloc(const void *p, size_t new_size, gfp_t flags);
  p: 需要重新分配内存的对象。
  new_size: 新的长度。
  flags: 传给页分配器的分配标志位。
  根据新的长度为对象重新分配内存，如果分配成功，返回新的地址，否则返回空指针。
  
  ```

  > 释放内存

  ```c
  void kfree(const void *objp);
  objp: kmalloc()返回的对象的地址。
  
  ```

- 使用通用的内存缓存的缺点是：块分配器需要找到一个对象的长度刚好大于或等于请求的内存长度的通用内存缓存，如果请求的内存长度和内存缓存的对象长度相差很远，浪费比较大，例如申请36字节，实际分配的内存长度是64字节，浪费了28字节。所以有时候使用者需要创建专用的内存缓存，编程接口如下：

  > 创建内存缓存

  ```c
  struct kmem_cache *kmem_cache_create(const char *name, size_t size, size_t align, unsigned long flags, void (*ctor)(void *));
  name: 名称；
  size: 对象的长度；
  align: 对象徐娅对齐的数值；
  flags: slab标志位；
  ctor: 对象的构造函数；
  如果创建成功，返回内存缓存的地址，否则返回空指针。
  
  ```

  > 从指定的内存缓存分配对象

  ```c
  void *kmem_cache_alloc(struct kmem_cache *cachep, gfp_t flags)；
  cachep: 从指定的内存缓存分配；
  flags: 传给页分配器的分配标志位，当内存缓存没有空闲对象，向页分配器请求分配页的时候使用这个分配标志位。
  如果分配成功，返回对象的地址，否则返回空指针。
  
  ```

  > 释放对象

  ```c
  void kmem_cache_free(struct kmem_cache *cachep, void *objp)；
  cachep： 对象所属的内存缓存；
  objp： 对象的地址；
  
  ```

  > 销毁内存缓存

  ```c
  void kmem_cache_destroy(struct kmem_cache *s)；
  s： 内存缓存。
  
  ```



## 11.3 SLAB分配器

### 11.3.1 数据结构

- 没存缓存的数据结构如下图：![1567418444054](../picture/内存缓存的数据结构.png)

  1.  每个内存缓存对应一个`kmem_cache`实例。`struct kmem_cache`结构体定义如下：

     ```c
     [linux-4.14/include/linux/slab_def.h]
     
     11  struct kmem_cache {
     12  	struct array_cache __percpu *cpu_cache;
     13  
     14  /* 1) Cache tunables. Protected by slab_mutex */
     15  	unsigned int batchcount;
     16  	unsigned int limit;
     17  	unsigned int shared;
     18  
     19  	unsigned int size;
     20  	struct reciprocal_value reciprocal_buffer_size;
     21  /* 2) touched by every alloc & free from the backend */
     22  
     23  	unsigned int flags;		/* constant flags */
     24  	unsigned int num;		/* # of objs per slab */
     25  
     26  /* 3) cache_grow/shrink */
     27  	/* order of pgs per slab (2^n) */
     28  	unsigned int gfporder;
     29  
     30  	/* force GFP flags, e.g. GFP_DMA */
     31  	gfp_t allocflags;
     32  
     33  	size_t colour;			/* cache colouring range */
     34  	unsigned int colour_off;	/* colour offset */
     35  	struct kmem_cache *freelist_cache;
     36  	unsigned int freelist_size;
     37  
     38  	/* constructor func */
     39  	void (*ctor)(void *obj);
     40  
     41  /* 4) cache creation/removal */
     42  	const char *name;
     43  	struct list_head list;
     44  	int refcount;
     45  	int object_size;
     46  	int align;
     47  
     48  /* 5) statistics */
     49  #ifdef CONFIG_DEBUG_SLAB
     50  	unsigned long num_active;
     51  	unsigned long num_allocations;
     52  	unsigned long high_mark;
     53  	unsigned long grown;
     54  	unsigned long reaped;
     55  	unsigned long errors;
     56  	unsigned long max_freeable;
     57  	unsigned long node_allocs;
     58  	unsigned long node_frees;
     59  	unsigned long node_overflow;
     60  	atomic_t allochit;
     61  	atomic_t allocmiss;
     62  	atomic_t freehit;
     63  	atomic_t freemiss;
     64  #ifdef CONFIG_DEBUG_SLAB_LEAK
     65  	atomic_t store_user_clean;
     66  #endif
     67  
     68  	/*
     69  	 * If debugging is enabled, then the allocator can add additional
     70  	 * fields and/or padding to every object. size contains the total
     71  	 * object size including these internal fields, the following two
     72  	 * variables contain the offset to the user object and its size.
     73  	 */
     74  	int obj_offset;
     75  #endif /* CONFIG_DEBUG_SLAB */
     76  
     77  #ifdef CONFIG_MEMCG
     78  	struct memcg_cache_params memcg_params;
     79  #endif
     80  #ifdef CONFIG_KASAN
     81  	struct kasan_cache kasan_info;
     82  #endif
     83  
     84  #ifdef CONFIG_SLAB_FREELIST_RANDOM
     85  	unsigned int *random_seq;
     86  #endif
     87  
     88  	struct kmem_cache_node *node[MAX_NUMNODES];
     89  };
     
     ```

     成员`gfporder`是slab的阶数，成员`num`是每个slab包含的对象数量，成员`object_size`是对象的原始长度，成员`size`是包括填充的对象长度。

  2.  每个内存节点对应一个`kmem_cache_node`实例。该实例包含3个slab链表：链表`slabs_partial`把部分对象空闲的slab链接起来，链表`slabs_full`把没有空闲对象的slab链接起来，链表`slabs_free`把所有对象空闲的slab链接起来。成员`total_slabs`是slab数量。

     ```c
     [linux-4.14/mm/slab.h]
     
     453  struct kmem_cache_node {
     454  	spinlock_t list_lock;
     455  
     456  #ifdef CONFIG_SLAB
     457  	struct list_head slabs_partial;	/* partial list first, better asm code */
     458  	struct list_head slabs_full;
     459  	struct list_head slabs_free;
     460  	unsigned long total_slabs;	/* length of all slab lists */
     461  	unsigned long free_slabs;	/* length of free slab list only */
     462  	unsigned long free_objects;
     463  	unsigned int free_limit;
     464  	unsigned int colour_next;	/* Per-node cache coloring */
     465  	struct array_cache *shared;	/* shared per node */
     466  	struct alien_cache **alien;	/* on other nodes */
     467  	unsigned long next_reap;	/* updated without locking */
     468  	int free_touched;		/* updated without locking */
     469  #endif
     470  
     471  #ifdef CONFIG_SLUB
     472  	unsigned long nr_partial;
     473  	struct list_head partial;
     474  #ifdef CONFIG_SLUB_DEBUG
     475  	atomic_long_t nr_slabs;
     476  	atomic_long_t total_objects;
     477  	struct list_head full;
     478  #endif
     479  #endif
     480  
     481  };
     
     ```

     

  3. 对对对