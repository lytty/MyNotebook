# 初期内存分配器——memblock

## 1. memblock

- 系统初始化的时候`buddy`系统（伙伴系统），`slab`分配器等并没有被初始化，当需要执行一些内存管理、内存分配的任务，就引入了一种内存管理器`bootmem`分配器。

- 当`buddy`系统和`slab`分配器初始化结束后，在`mem_init()`中对`bootmem`分配器进行释放，内存管理与分配由`buddy`系统，`slab`分配器等进行接管。

- 而`memblock`是用来替代`bootmem`的新接口。用`__alloc_memory_core_early()`取代了`bootmem`的`__alloc_bootmem_core()`来完成内存分配。
- 内存中的某些部分是永久的分配给内核的，比如内核代码段和数据段，`ramdisk`和`fdt`占用的空间等。它们是系统内存的一部分，但是不能被侵占，也不参与内存分配，称之为静态内存；还有，`GPU`、`Camera`等都需要预留大量连续内存，这部分内存平时不用，但是系统必须提前预留好，称之为预留内存；最后，内存的其余部分称之为动态内存，是需要内存管理的宝贵资源。
- `memblock`把物理内存划分为若干内存区，按使用类型分别放在`memory`和`reserved`两个集合（数组）中，`memory`即动态内存的和，`reserved`集合包括静态内存和预留内存。
- 

1. `memblock`关键数据结构

   ```c
   [linux-4.14/include/linux/memblock.h]
   48  struct memblock {
   49  	bool bottom_up;  /* is bottom up direction? 是否允许从下往上分配内存*/
   50  	phys_addr_t current_limit; // 内存块限制，限制memblock_alloc内存申请
   51  	struct memblock_type memory; // 可用内存的集合
   52  	struct memblock_type reserved; // 已分配内存的集合
   53  #ifdef CONFIG_HAVE_MEMBLOCK_PHYS_MAP
   54  	struct memblock_type physmem; // 物理内存的集合
   55  #endif
   56  };
   
   ```

   `memblock_regin`结构体描述了内存区域

   ```c
   [linux-4.14/include/linux/memblock.h]
   31  struct memblock_region {
   32  	phys_addr_t base; // 内存区域的起始地址
   33  	phys_addr_t size; // 内存区域大小
   34  	unsigned long flags; // 标记
   35  #ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
   36  	int nid; // 节点号
   37  #endif
   38  };
   
   ```

   `memblock_type`结构体

   ```c
   40  struct memblock_type {
   41  	unsigned long cnt;	/* number of regions 当前集合记录的内存区域个数 */
   42  	unsigned long max;	/* size of the allocated array 当前集合记录内存区域最大个数 */
   43  	phys_addr_t total_size;	/* size of all regions 集合记录区域信息大小 */
   44  	struct memblock_region *regions; // 内存区域结构指针
   45  	char *name;
   46  };
   
   ```



## 2. memblock初始化

