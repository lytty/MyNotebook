# 初期内存分配器——memblock

## 1. memblock

- 系统初始化的时候`buddy`系统（伙伴系统），`slab`分配器等并没有被初始化，当需要执行一些内存管理、内存分配的任务，就引入了一种内存管理器`bootmem`分配器。

- 当`buddy`系统和`slab`分配器初始化结束后，在`mem_init()`中对`bootmem`分配器进行释放，内存管理与分配由`buddy`系统，`slab`分配器等进行接管。

- 而`memblock`是用来替代`bootmem`的新接口。`memblock`用于开机阶段的内存管理。
- 内存中的某些部分是永久的分配给内核的，比如内核代码段和数据段，`ramdisk`和`fdt`占用的空间等。它们是系统内存的一部分，但是不能被侵占，也不参与内存分配，称之为静态内存；还有，`GPU`、`Camera`等都需要预留大量连续内存，这部分内存平时不用，但是系统必须提前预留好，称之为预留内存；最后，内存的其余部分称之为动态内存，是需要内存管理的宝贵资源。
- 在开机阶段内存以内存区块来管理，`memblock`把物理内存划分为若干内存区块，内存区块由结构体`struct memblock_region`来描述，`Memblock`中有两种内存类型, `memory`和`reserved`，`memory`用于记录总的内存资源，`reserved`用于记录已经使用或者预留的内存资源。

  

1. `memblock`关键数据结构

   ```c
   [linux-4.14/include/linux/memblock.h]
   48  struct memblock {
   49  	bool bottom_up;  /* is bottom up direction? 内存分配从高地址到低地址，还是从低地址到高地址*/
   50  	phys_addr_t current_limit; // 可以使用的内存的上限
   51  	struct memblock_type memory; // 记录完整的内存资源
   52  	struct memblock_type reserved; // 记录已分配或者预留的内存资源
   53  #ifdef CONFIG_HAVE_MEMBLOCK_PHYS_MAP
   54  	struct memblock_type physmem; // 物理内存的集合
   55  #endif
   56  };
   
   ```

   `memblock_regin`结构体描述了内存区域

   ```c
   [linux-4.14/include/linux/memblock.h]
   20  #define INIT_MEMBLOCK_REGIONS	128 /* 数组最大容纳128个区块，如果超过这个限制将重新分配一个区块管理数组，并且是原来的两倍大小 */
   
   31  struct memblock_region { // 描述一个内存区块
   32  	phys_addr_t base; // 区块的起始地址
   33  	phys_addr_t size; // 区块大小
   34  	unsigned long flags; // 标记
   35  #ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
   36  	int nid; // 节点号
   37  #endif
   38  };

   [linux-4.14/mm/memblock.c]
28  static struct memblock_region memblock_memory_init_regions[INIT_MEMBLOCK_REGIONS] __initdata_memblock;
   29  static struct memblock_region memblock_reserved_init_regions[INIT_MEMBLOCK_REGIONS] __initdata_memblock;
   
   34  struct memblock memblock __initdata_memblock = {
   35  	.memory.regions		= memblock_memory_init_regions,
   36  	.memory.cnt		= 1,	/* empty dummy entry 表示内存块数量，还没有插入内存块时设置为1*/
   37  	.memory.max		= INIT_MEMBLOCK_REGIONS, /* 数组最大容纳区块数 */
   38  	.memory.name		= "memory", /* 内存数组名 */
   39  
   40  	.reserved.regions	= memblock_reserved_init_regions,
   41  	.reserved.cnt		= 1,	/* empty dummy entry */
   42  	.reserved.max		= INIT_MEMBLOCK_REGIONS,
   43  	.reserved.name		= "reserved",
   44  
   45  #ifdef CONFIG_HAVE_MEMBLOCK_PHYS_MAP
   46  	.physmem.regions	= memblock_physmem_init_regions,
   47  	.physmem.cnt		= 1,	/* empty dummy entry */
   48  	.physmem.max		= INIT_PHYSMEM_REGIONS,
   49  	.physmem.name		= "physmem",
   50  #endif
   51  
   52  	.bottom_up		= false,
   53  	.current_limit		= MEMBLOCK_ALLOC_ANYWHERE,
   54  };
   
   ```
   
   `memblock_type`结构体
   
   ```c
   40  struct memblock_type {
   41  	unsigned long cnt;	/* number of regions 总的内存资源有几个region */
   42  	unsigned long max;	/* size of the allocated array 最多有几个region */
   43  	phys_addr_t total_size;	/* size of all regions 总的容量 */
   44  	struct memblock_region *regions; // 内存区域结构指针
   45  	char *name;
   46  };
   
   ```



## 2. memblock初始化

- 系统初始化阶段，所有的内存资源，都会添加到memory类型内存中。我们在《设备树》章节中有讲到，设备树本身就是描述硬件资源信息的，理所当然，内存资源信息也应该挂在设备树上，即Linux中的内存资源信息，是以设备树的形式来告知内核。对于Linux内核如何从设备树上获取内存资源信息，《内存解析》章节有详细介绍，接下来我们基于《内存解析》章节着重分析一下，内核获取到内存资源信息后，以什么样的形式保存内存资源信息。
  
- 函数调用关系：
  
  `start_kernel() -> setup_machine_fdt() -> early_init_dt_scan_nodes() -> early_init_dt_scan_memory() -> early_init_dt_add_memory_arch() -> memblock_add()`

  我们从`early_init_dt_add_memory_arch()`函数开始解析，其上层的函数调用流程在《内存解析》章节中已有详细解析，此处不再赘述。`early_init_dt_add_memory_arch()`函数定义及解析如下：
  
  ```c
  [linux-4.14/drivers/of/fdt.c]
  
  1158  #ifdef CONFIG_HAVE_MEMBLOCK
  1159  #ifndef MIN_MEMBLOCK_ADDR
  1160  #define MIN_MEMBLOCK_ADDR	__pa(PAGE_OFFSET)
  1161  #endif
  1162  #ifndef MAX_MEMBLOCK_ADDR
  1163  #define MAX_MEMBLOCK_ADDR	((phys_addr_t)~0)
  1164  #endif
  /*	
  	base: 设备树内存节点中的起始地址值；
  	size: 该内存节点中包含内存的大小。
  	arm32 内存节点中reg属性一般格式：reg = <0x60000000 0x40000000>;对应 base=0x60000000，size=0x40000000 
  */
  1166  void __init __weak early_init_dt_add_memory_arch(u64 base, u64 size)
  1167  {
  1168  	const u64 phys_offset = MIN_MEMBLOCK_ADDR;/* 获取内核起始地址（PAGE_OFFSET）对应的物理地址 */
  1169  
  1170  	if (!PAGE_ALIGNED(base)) { /* 检查 base 是否页对齐 */
  1171  		if (size < PAGE_SIZE - (base & ~PAGE_MASK)) {
  1172  			pr_warn("Ignoring memory block 0x%llx - 0x%llx\n",
  1173  				base, base + size);
  1174  			return;
  1175  		}
  1176  		size -= PAGE_SIZE - (base & ~PAGE_MASK);
  1177  		base = PAGE_ALIGN(base);
  1178  	}
  1179  	size &= PAGE_MASK;
  1180  
  1181  	if (base > MAX_MEMBLOCK_ADDR) {
  1182  		pr_warning("Ignoring memory block 0x%llx - 0x%llx\n",
  1183  				base, base + size);
  1184  		return;
  1185  	}
  1186  
  1187  	if (base + size - 1 > MAX_MEMBLOCK_ADDR) {
  1188  		pr_warning("Ignoring memory range 0x%llx - 0x%llx\n",
  1189  				((u64)MAX_MEMBLOCK_ADDR) + 1, base + size);
  1190  		size = MAX_MEMBLOCK_ADDR - base + 1;
  1191  	}
  1192  
  1193  	if (base + size < phys_offset) {
  1194  		pr_warning("Ignoring memory block 0x%llx - 0x%llx\n",
  1195  			   base, base + size);
  1196  		return;
  1197  	}
  1198  	if (base < phys_offset) {
  1199  		pr_warning("Ignoring memory range 0x%llx - 0x%llx\n",
  1200  			   base, phys_offset);
  1201  		size -= phys_offset - base;
  1202  		base = phys_offset;
  1203  	}
  1204  	memblock_add(base, size);
  1205  }
  
  ```
  
  
  
   
  
  

