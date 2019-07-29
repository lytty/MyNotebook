# 初期内存分配器——memblock

## 1. memblock

- 系统初始化的时候`buddy`系统（伙伴系统），`slab`分配器等并没有被初始化，当需要执行一些内存管理、内存分配的任务，就引入了一种内存管理器`bootmem`分配器。

- 当`buddy`系统和`slab`分配器初始化结束后，在`mem_init()`中对`bootmem`分配器进行释放，内存管理与分配由`buddy`系统，`slab`分配器等进行接管。

- 而`memblock`是用来替代`bootmem`的新接口。`memblock`用于开机阶段的内存管理。
- 内存中的某些部分是永久的分配给内核的，比如内核代码段和数据段，`ramdisk`和`fdt`占用的空间等。它们是系统内存的一部分，但是不能被侵占，也不参与内存分配，称之为静态内存；还有，`GPU`、`Camera`等都需要预留大量连续内存，这部分内存平时不用，但是系统必须提前预留好，称之为预留内存；最后，内存的其余部分称之为动态内存，是需要内存管理的宝贵资源。
- 在开机阶段内存以内存区块来管理，`memblock`把物理内存划分为若干内存区块，内存区块由结构体`struct memblock_region`来描述，`Memblock`中有两种内存类型, `memory`和`reserved`，`memory`用于记录总的内存资源，`reserved`用于记录已经使用或者预留的内存资源。

  

## 2. memblock 相关数据结构

> `memblock`结构体

```c
[linux-4.14/include/linux/memblock.h]
48  struct memblock {
49  	bool bottom_up;  // 表示分配器分配内存的方式 true:从低地址向高地址分配  false:相反就是从高地址向地址分配内存
50  	phys_addr_t current_limit; // 可以使用的内存的上限
51  	struct memblock_type memory; // 可分配内存的集合，申请内存时，会从这些集合中分配内存
52  	struct memblock_type reserved; // 已分配内存（包括预留内存）的集合，分配出去的内存会放在这个集合里面管理
53  #ifdef CONFIG_HAVE_MEMBLOCK_PHYS_MAP
54  	struct memblock_type physmem; // 物理内存的集合
55  #endif
56  };

```

> `memblock_type`结构体

```c
[linux-4.14/include/linux/memblock.h]
40  struct memblock_type {
41  	unsigned long cnt;	/* number of regions 当前管理的集合中记录的内存区域个数 */
42  	unsigned long max;	/* size of the allocated array 当前管理的集合中可记录的内存区域的最大个数，最大值是INIT_PHYSMEM_REGIONS */
43  	phys_addr_t total_size;	/* size of all regions 集合记录的内存总和 */
44  	struct memblock_region *regions; // 执行内存区域结构（memblock_region）的指针
45  	char *name;
46  };

```

> `memblock_region`结构体描述了内存区域

```c
[linux-4.14/include/linux/memblock.h]
20  #define INIT_MEMBLOCK_REGIONS	128 /* 数组最大容纳128个区块，如果超过这个限制将重新分配一个区块管理数组，并且是原来的两倍大小 */

31  struct memblock_region { // 描述一个内存区域
32  	phys_addr_t base; // 内存区域的起始地址，是物理地址
33  	phys_addr_t size; // 内存区域大小，单位是字节
34  	unsigned long flags; // 该内存区域的标识，例如MEMBLOCK_NOMAP，在做映射的时候不要映射到内核中
35  #ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
36  	int nid; // 节点号，CPU被划分为多个节点(node)，每个node 有对应的内存簇bank，一个标识
37  #endif
38  };


```

> 结构体`memblock`、`memblock_type`、`memblock_region`之间的逻辑关系如下图：

![img](../picture/memblock数据结构.png) 

> 在memblock中，管理内存的数据结构（struct memblock）被定义为一个全局的变量，并且赋予了对应的初值。

```c
[linux-4.14/include/linux/memblock.h]
20  #define INIT_MEMBLOCK_REGIONS	128
21  #define INIT_PHYSMEM_REGIONS	4
299  #define MEMBLOCK_ALLOC_ANYWHERE	(~(phys_addr_t)0) //0xffffffff（32位）

[linux-4.14/mm/memblock.c]
/* 对于__init、__initdata和__exit、__exitdata的定义位于<linux/init.h>,这些宏定义的作用是告诉编译器将这些函数或者数据放入相应的section中，而在模块加载的阶段.ko文件中的代码和数据的加载区域是根据section来加载的。之所以要使用这个宏定义，其中一个原因是标记为初始化的函数和数据,表明该函数和数据仅在初始化期间使用。在模块装载之后，模块装载就会将初始化函数扔掉。这样可以将该函数占用的内存释放出来。 */
28  static struct memblock_region memblock_memory_init_regions[INIT_MEMBLOCK_REGIONS] __initdata_memblock;
29  static struct memblock_region memblock_reserved_init_regions[INIT_MEMBLOCK_REGIONS] __initdata_memblock;
30  #ifdef CONFIG_HAVE_MEMBLOCK_PHYS_MAP
31  static struct memblock_region memblock_physmem_init_regions[INIT_PHYSMEM_REGIONS] __initdata_memblock;
32  #endif
33
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
52  	.bottom_up		= false, //内存分配方式是从高地址往低地址分配
53  	.current_limit		= MEMBLOCK_ALLOC_ANYWHERE,
54  };
```

memblock.memory.regions 指向 memblock_memory_init_regions 数组，数组大小是128，memblock.reserved.regions 指向memblock_reserved_init_regions 数组，数组大小是128，memblock.physmem.regions 指向 memblock_physmem_init_regions 数组，数组大小是4。memblock 初始化后如下图：

![img](/home/haibin.xu/haibin/doc/picture/memblock初始化图.png) 

## 3. memblock初始化

- 系统初始化阶段，所有的内存资源，都会添加到memory类型内存中。我们在《设备树》章节中有讲到，设备树本身就是描述硬件资源信息的，理所当然，内存资源信息也应该挂在设备树上，即Linux中的内存资源信息，是以设备树的形式来告知内核。对于Linux内核如何从设备树上获取内存资源信息，《内存解析》章节有详细介绍，接下来我们基于《内存解析》章节着重分析一下，内核获取到内存资源信息后，以什么样的形式保存内存资源信息。

> memblock_add() 添加内存区域

- 函数调用关系：
  
  `start_kernel() -> setup_arch() -> setup_machine_fdt() -> early_init_dt_scan_nodes() -> early_init_dt_scan_memory() -> early_init_dt_add_memory_arch() -> memblock_add()`

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
  
  下面我们继续分析`memblock_add()`函数，其定义和解析如下：
  
  ```c
  [linux-4.14/mm/memblock.c]
  /* base: 物理内存的起始地址
   * size: 物理内存的大小
   * base,size表示出物理内存区间
  */
  596  int __init_memblock memblock_add(phys_addr_t base, phys_addr_t size)
  597  {
  598  	phys_addr_t end = base + size - 1;
  599  
  600  	memblock_dbg("memblock_add: [%pa-%pa] %pF\n",
  601  		     &base, &end, (void *)_RET_IP_);
  602  	/* 调用memblock_add_range(),
  		 * memblock.memory: memblock 即上面介绍的全局变量，memblock.memory就是可用内存集合。 
  		 */
  603  	return memblock_add_range(&memblock.memory, base, size, MAX_NUMNODES, 0);
  604  }
  
  
  488  /**
  489   * memblock_add_range - add new memblock region
  490   * @type: memblock type to add new region into
  491   * @base: base address of the new region
  492   * @size: size of the new region
  493   * @nid: nid of the new region
  494   * @flags: flags of the new region
  495   *
  496   * Add new memblock region [@base,@base+@size) into @type.  The new region
  497   * is allowed to overlap with existing ones - overlaps don't affect already
  498   * existing regions.  @type is guaranteed to be minimal (all neighbouring
  499   * compatible regions are merged) after the addition.
  500   *
  501   * RETURNS:
  502   * 0 on success, -errno on failure.
  503   */
  504  int __init_memblock memblock_add_range(struct memblock_type *type,
  505  				phys_addr_t base, phys_addr_t size,
  506  				int nid, unsigned long flags)
  507  {
  508  	bool insert = false;
  509  	phys_addr_t obase = base;
  510  	phys_addr_t end = base + memblock_cap_size(base, &size);
  511  	int idx, nr_new;
  512  	struct memblock_region *rgn;
  513  
  514  	if (!size)
  515  		return 0;
  516  
  517  	/* special case for empty array */
      	/* 刚开始还没有空余的memory加入到 memblock 管理的数组中，所以type->regions[0].size == 0成立，跑完if 里面的代码后就返回了 		  */
  518  	if (type->regions[0].size == 0) {
  519  		WARN_ON(type->cnt != 1 || type->total_size);
  520  		type->regions[0].base = base;
  521  		type->regions[0].size = size;
  522  		type->regions[0].flags = flags;
  523  		memblock_set_region_node(&type->regions[0], nid);
  524  		type->total_size = size;
  525  		return 0;
  526  	}
  527  repeat:
  528  	/*
  529  	 * The following is executed twice.  Once with %false @insert and
  530  	 * then with %true.  The first counts the number of regions needed
  531  	 * to accommodate the new area.  The second actually inserts them.
  532  	 */
  533  	base = obase;
  534  	nr_new = 0;
  535  
  536  	for_each_memblock_type(type, rgn) {
  537  		phys_addr_t rbase = rgn->base;
  538  		phys_addr_t rend = rbase + rgn->size;
  539  
  540  		if (rbase >= end)
  541  			break;
  542  		if (rend <= base)
  543  			continue;
  544  		/*
  545  		 * @rgn overlaps.  If it separates the lower part of new
  546  		 * area, insert that portion.
  547  		 */
  548  		if (rbase > base) {
  549  #ifdef CONFIG_HAVE_MEMBLOCK_NODE_MAP
  550  			WARN_ON(nid != memblock_get_region_node(rgn));
  551  #endif
  552  			WARN_ON(flags != rgn->flags);
  553  			nr_new++;
  554  			if (insert)
  555  				memblock_insert_region(type, idx++, base,
  556  						       rbase - base, nid,
  557  						       flags);
  558  		}
  559  		/* area below @rend is dealt with, forget about it */
  560  		base = min(rend, end);
  561  	}
  562  
  563  	/* insert the remaining portion */
  564  	if (base < end) {
  565  		nr_new++;
  566  		if (insert)
  567  			memblock_insert_region(type, idx, base, end - base,
  568  					       nid, flags);
  569  	}
  570  
  571  	if (!nr_new)
  572  		return 0;
  573  
  574  	/*
  575  	 * If this was the first round, resize array and repeat for actual
  576  	 * insertions; otherwise, merge and return.
  577  	 */
  578  	if (!insert) {
  579  		while (type->cnt + nr_new > type->max)
  580  			if (memblock_double_array(type, obase, size) < 0)
  581  				return -ENOMEM;
  582  		insert = true;
  583  		goto repeat;
  584  	} else {
  585  		memblock_merge_regions(type);
  586  		return 0;
  587  	}
  588  }
  
  ```
  
  
  
   
  
  

