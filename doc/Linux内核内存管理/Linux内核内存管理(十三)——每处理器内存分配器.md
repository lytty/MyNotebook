# Linux内核内存管理(十三)——每处理器内存分配器

- 在多处理器系统中，每处理器变量为每个处理器生成一个变量的副本，每个处理器访问自己的副本，从而避免了处理器之间的互斥和处理器缓存之间的同步，提高了程序的执行速度。



## 1 编程接口

- 每处理器变量分为静态和动态两种。



### 1.1 静态每处理器变量

- 使用宏`DEFINE_PER_CPU(type, name)`定义普通的静态每处理器变量，使用宏`DECLARE_PER_CPU(type, name)`声明普通的静态每处理器变量。

- 把宏`DEFINE_PER_CPU(type, name)`展开以后是：

  ```c
  __attribute__((section(".data..percpu"))) __typeof__(type) name

  ```

  可以看出，普通的静态每处理器变量存放在".data..percpu"节（每处理器数据节）中。

- 定义静态每处理器变量的其他变体如下：

  1. 使用宏`DEFINE_PER_CPU_FIRST(type, name)`定义必须在每处理器变量集合中最先出现的每处理器变量。
  2. 使用宏`DEFINE_PER_CPU_SHARED_ALIGNED(type, name)`定义和处理器缓存行对齐的每处理器变量，仅仅在SMP系统中需要和处理器缓存行对齐。
  3. 使用宏`DEFINE_PER_CPU_ALIGNED(type, name)`定义和处理器缓存行对齐的每处理器变量，不管是不是SMP系统，都需要和处理器缓存行对齐。
  4. 使用宏`DEFINE_PER_CPU_PAGE_ALIGNED(type, name)`定义和页长度对齐的每处理器变量。
  5. 使用宏`DEFINE_PER_CPU_READ_MOSTLY(type, name)`定义以读为主的每处理器变量。

- 如果想要静态每处理器变量可以被其他内核模块引用，需要导出到符号表，具体如下：

  1. 如果允许任何内核模块引用，使用宏`EXPORT_PER_CPU_SYMBOL(var)`把静态每处理器变量导出到符号表。

  2. 如果只允许使用GPL许可的内核模块引用，使用宏`EXPORT_PER_CPU_SYMBOL_GPL(var)`把静态每处理器变量导出到符号表。



### 1.2 动态每处理器变量

- 为动态每处理器变量分配内存的函数如下：

  1. 使用函数`__alloc_percpu_gfp`为动态每处理器变量分配内存。

     ```c
     [linux-4.14.130/mm/percpu.c]
     /*
      * size: 长度
      * align: 对齐值
      * gfp: 传给页分配器的分配标志位
      */
     void __percpu *__alloc_percpu_gfp(size_t size, size_t align, gfp_t gfp)
     {
     	return pcpu_alloc(size, align, false, gfp);
     }

     ```

  2. 宏`alloc_percpu_gfp(type, gfp)`是函数`__alloc_percpu_gfp`的简化形式，参数`size`取`sizeof(type)`,参数`align`取`__alignof__(type)`，即数据类型`type`的对齐值。

  3. 函数`__alloc_percpu`是函数`__alloc_percpu_gfp`的简化形式，参数`gfp`取`GFP_KERNEL`。

     ```c
     [linux-4.14.130/mm/percpu.c]
     void __percpu *__alloc_percpu(size_t size, size_t align)
     {
     	return pcpu_alloc(size, align, false, GFP_KERNEL);
     }

     ```

  4. 宏`alloc_percpu(type)`是函数`__alloc_percpu`的简化形式，参数`size`取`sizeof(type)`,参数`align`取`__alignof__(type)`

- 最常用的是宏`alloc_percpu(type)`

- 使用函数`free_percpu`释放动态每处理器变量的内存：

  ```c
  [linux-4.14.130/mm/percpu.c]
  void free_percpu(void __percpu *ptr)

  ```



### 1.3 访问每处理器变量

- 宏`this_cpu_ptr(ptr)`用来得到当前处理器的变量副本的地址，宏`get_cpu_var(var)`用来得到当前处理器的变量副本的值。

- 宏`this_cpu_ptr(ptr)`展开以后：

  ```c
  unsigned long __ptr;

  __ptr = (unsigned long)(ptr);
  (typeof(ptr)) (__ptr + per_cpu_offset(raw_smp_processor_id()));

  ```

  可以看出，当前处理器的变量副本的地址 = 基准地址 + 当前处理器的偏移

- 宏`per_cpu_ptr(ptr, cpu)`用来得到指定处理器的变量副本的地址，宏`per_cpu(var,cpu)`用来得到指定处理器的变量副本的值。

- 宏`get_cpu_ptr(var)`禁止内核抢占并且返回当前处理器的变量副本的地址，宏`put_cpu_ptr(var)`开启内核抢占，这两个宏成对使用，确保当前进程在内核模式下访问当前处理器的变量副本的时候不会被其他进程抢占。



## 2 技术原理

- 每处理器区域是按块（`chunk`）分配的，每个块分为多个长度相同的单元（`unit`），每个处理器对应一个单元。在`NUMA`系统上，把单元按内存节点分组，同一个内存节点的所有处理器对应的单元属于同一个组。
- 分配块的方式有两种：
  1. 基于`vmalloc`区域的块分配。从`vmalloc`虚拟地址空间分配虚拟内存区域，然后映射到物理页。基于vmalloc区域的块分配，适合多处理器系统。多处理器系统默认使用基于vmalloc区域的快分配方式。
  2. 基于内核内存的块分配。直接从页分配器分配页，使用直接映射的内核虚拟地址空间。基于内核内存的块分配，适合单处理器系统或者处理器没有内存管理单元部件的情况，目前这种分配方式不支持NUMA系统，单处理器系统默认使用基于内核内存的块分配方式。



### 2.1 基于`vmalloc`区域的每处理器内存分配器

- 基于`vmalloc`区域的每处理器内存分配器的数据结构如下图所示　![1570851306118](/home/haibin.xu/haibin/doc/picture/图13.1-基于vmalloc区域的每处理器内存分配器.png)

- 每个块对应一个`pcpu_chunk`实例：

  > 1. 成员`data`指向`vm_struct`指针数组，`vm_struct`结构体是不连续页分配器的数据结构，每个组对应一个`vm_struct`实例，`vm_struct`实例的成员`addr`指向组的起始地址。块以组为单位分配虚拟内存区域，一个组的虚拟地址是连续的，不同组的虚拟地址不一定是连续的。
  > 2. 成员`populated`是填充位图，记录那些虚拟页已经映射到物理页：成员`nr_populated`是已填充页数，记录已经映射到物理页的虚拟页的数量。创建块时，只分配了虚拟内存区域，没有分配物理页，从块分配每处理器变量时，才分配物理页。物理页的`page`实例成员`index`指向`pcpu_chunk`实例。
  > 3. 成员`map`指向分配图，分配图是一个整数数组，用来存放每个小块（`block`）的偏移和分配状态，成员`map_used`记录分配图已使用的项数。
  > 4. 成员`free_size`记录空闲字节数，成员`contig_hint`记录最大的连续空闲字节数。
  > 5. 成员`base_size`是块的基准地址，一个块的每个组必须满足条件：组的起始地址 = （块的基准地址 + 组的偏移）。
  > 6. 成员`list`用来把块加入块插槽，插槽号是根据空闲字节数算出来的。



### 2.2 基于内核内存的每处理器内存分配器

- 基于内核内存的每处理器内存分配器的数据结构如下图所示![1571058000165](/home/haibin.xu/haibin/doc/picture/图13.2-基于内核内存的每处理器内存分配器.png)

- 和基于`vmalloc`区域的每处理器内存分配器的不同如下：

  > 1. `pcpu_trunk`实例的成员`data`指向`page`结构体数组；
  > 2. 创建块的时候，分配了物理页，虚拟页直接映射到物理页；
  > 3. 不支持`NUMA`系统，一个块只有一个组。



### 2.3

- 一个块中偏移为`offset`，长度为`size`的区域，是由每个单元中偏移为`offset`，长度为`size`的小块（`block`）组成的。从一个块分配偏移为`offset`，长度为`size`的区域，就是从每个单元分配偏移为`offset`，长度为`size`的小块。

- 为每处理器分配内存时，返回的虚拟地址是（`chunk->base_addr + offset - delta`），其中`chunk->base_addr`是块的基准地址，`offset`是单元内部的偏移，`delta`是（`pcpu_base_addr - __per_cpu_start`），`__per_cpu_start`是每处理器数据段的起始地址，内核把所有静态每处理器变量放在每处理器数据段，`pcpu_base_addr`是第一块的基准地址，每处理器内存分配器在初始化的时候把每处理器数据段复制到第一块的每个单元。

- 使用宏`this_cpu_ptr(ptr)`访问每处理器变量，`ptr`是为每处理器变量分配内存时返回的虚拟地址。

  ```c
  this_cpu_ptr(ptr)
  = ptr + __per_cpu_offset[cpu]
  = ptr + (delta + pcpu_unit_offsets[cpu])
  = (ptr + delta) + pcpu_unit_offsets[cpu]
  = (chunk->base_addr + offset) + pcpu_unit_offsets[cpu]
  = (chunk->base_addr + pcpu_unit_offsets[cpu]) + offset

  ```

  `pcpu_unit_offsets[cpu]`是处理器对应单元的偏移，`(chunk->base_addr + pcpu_unit_offsets[cpu])`是处理器对应单元的起始地址，加上单元内部的偏移`offset`，就是变量副本的地址。

- 为每处理器变量分配内存时，返回的虚拟地址需要减去`delta`，这是因为宏`this_cpu_ptr(ptr)`在计算变量副本的地址时加上了`delta`（主要是为了照顾内核的静态每处理器变量），所以分配内存时返回的虚拟地址要提前减去`delta`。

- 如下图所示，`__per_cpu_start`是每处理器数据段的起始地址，内核把所有静态每处理器变量放在每处理器数据段，`pcpu_base_addr`是第一块基准地址，每处理器内存分配器在初始化时把每处理器数据段复制到第一块的每个单元。                                         ![1571661166538](/home/haibin.xu/haibin/doc/picture/图13.3-内核的静态每处理器变量.png)

- 使用宏`this_cpu_ptr(ptr)`访问静态每处理器变量时，`ptr`是内核镜像的每处理器数据段中变量的虚拟地址，必须加上第一块的基准地址和每处理器数据段的起始地址的差值，才能得到第一块中变量副本的地址。



### 2.4 分配图

- 分配图是一个整数数组，存放每个小块的偏移和分配状态，每个小块的长度是偶数，偏移是偶数，使用最低位表示小块的分配状态，如果小块被分配，那么设置最低位。
- 假设系统有4个处理器，一个块分为4个单元，块的初始状态如下图所示，分配图使用了两项：第一项存放第一个小块的偏移0，空闲；第二项存放单元的结束标记，偏移是单元长度`pcpu_unit_size`,最低位被设置。                                                ![1571661795315](/home/haibin.xu/haibin/doc/picture/图13.4-块的初始状态.png)

- 分配一个长度是32字节的动态每处理器变量以后，块的状态如下图所示，每个单元中偏移为0、长度为32字节的小块被分配出去，分配图使用了三项：第一项存放第一个小块的偏移0，已分配；第二项存放第二个小块的偏移32，空闲；第三项存放单元的结束标记，偏移是单元长度`pcpi_unit_size`，最低位被设置。![1571662159334](/home/haibin.xu/haibin/doc/picture/图13.5-分配32字节以后块的状态.png)



### 2.5 块

- 分配器根据空闲长度把块组织成链表，把每条链表成为块插槽，插槽的数量是`pcpu_nr_slots`，根据空闲长度`n`计算插槽号的方法如下：

  1. 如果空闲长度小数整数长度，或者最大的连续空闲字节数小于整数长度，那么插槽号是0。

  2. 如果块全部空闲，即空闲长度等于单元长度，那么取最后一个插槽号，即`pcpu_nr_slots - 1`。

  3. 其他情况：插槽号 = `fls(n) - 3`，并且不能小于1。`fls(n)`是取n被设置的最高位，例如`fls(1) = 1`，`fls(0x80000000)=32`，相当于`(log2(n) + 1)`。减3的目的是让空闲长度是`1~15`字节的块共享插槽1。期待吗如下：

     ```c
     [linux-4.14.130/mm/percpu.c]

     #define PCPU_SLOT_BASE_SHIFT		5
     static int __pcpu_size_to_slot(int size)
     {
     	int highbit = fls(size);	/* size is in bytes */
     	return max(highbit - PCPU_SLOT_BASE_SHIFT + 2, 1);
     }

     ```





### 2.6 确定块的参数

- 创建一个块时，需要知道以下参数：

  > 块分为多少个组？
  >
  > 每个组的偏移是多少？
  >
  > 每个组的长度是多少？
  >
  > 原子长度是多少？原子长度是对齐值，即组的长度必须是原子长度的整数倍。
  >
  > 单元长度是多少？

- 块的各种参数是在创建第一个块的时候确定的，一个块包含了内核的静态每处理器变量。

- 函数`pcpu_build_alloc_info`计算分组信息和单元长度，其算法如下：

  ```c
  start_kernel -> setup_per_cpu_areas -> pcpu_embed_first_chunk -> pcpu_build_alloc_info

  静态长度： 内核中所有静态每处理器变量的长度总和，等于每处理器数据段的结束地址减去起始地址，即 (__per_cpu_end - __per_cpu_start)。
  保留长度： 为内核静态每处理器变量保留，使用宏 PERCPU_MODULE_RESERVE 定义，值是 8KB 。
  动态长度： 为动态每处理器变量准备，使用宏 PERCPU_DYNAMIC_RESERVE 定义，在64位系统中的值是 28KB 。
size_num = 静态长度 + 保留长度 + 动态长度

  最小单元长度 min_unit_size = size_num，并且不允许小于宏 PCPU_MIN_UNIT_SIZE（值是32KB）。
  分配长度 alloc_size = min_unit_size 向上对齐到原子长度的整数倍，目前原子长度是页长度。
  最大倍数 max = alloc_size / min_unit_size。

  根据距离把处理器分组，计算每个处理器的组编号和每个组的处理器数量，实际上是每个内存节点的所有处理器属于同一个组。
  单元长度 = alloc_size / 倍数n，现在需要从最大倍数max到最小倍数1中找到一个最优的倍数n：
  1. 块以组为单位分配虚拟内存区域，必须保证每个组的长度是原子长度的整数倍。
  2. 浪费的比例必须小于或等于25%，并且浪费的比例是最小的。
  倍数n从最大倍数max递减到最小倍数1 {
  	如果alloc_size不能整除倍数n，或者alloc_size/n不是页长度的整数倍，那么倍数n不合适；
  	把每个组的单元数量向上对齐到n，计算单元总数 units；
  	如果（因为对齐增加的单元数量 / 对齐前的单元总数）大于 1/3，即浪费的比例超过 25% ，那么倍数n不合适；
  	如果单元总数比以前算出的单元总数 last_units 大，那么退出循环；
  	记录单元总数 last_units = units;
  	记录最优倍数 best = n;
  }

  best 是最优倍数，单元长度 = alloc_size / best

  设置组的参数如下：
  1. 每个组的单元数量：向上对齐到best的整数倍，确保每个组的虚拟内存区域对齐到原子长度。
  2. 计算每个组的偏移： 第n组的偏移等于（第 0 到 n-1 组的单元总数 × 单元长度），单元数量包括把组长度和原子长度对齐而增加的单元。

  ```

- 函数`pcpu_setup_first_chunk`根据传入的结构体`pcpu_alloc_info`和基准地址初始化第一块，并且设置块的参数：

  > 全局变量`pcpu_nr_groups`存放组的数量；
  >
  > 全局数组`pcpu_group_offsets`存放每个组的偏移，`pcpu_group_offsets[n]`是第n组的偏移；
  >
  > 全局数组`pcpu_group_sizes`存放每个组的长度，`pcpu_group_sizes[n]`是第n组的长度；
  >
  > 全局数组`pcpu_unit_map`存放每处理器编号到单元编号的映射关系，`pcpu_unit_map[n]`是处理器n的单元编号；
  >
  > 全局数组`pcpu_unit_offsets`存放每个单元的偏移，`pcpu_unit_offsets[n]`是单元n的偏移；
  >
  > 全局变量`pcpu_nr_units`是块的单元数量，不包括因为把组长度和原子长度对齐而增加的单元；
  >
  > 全局变量`pcpu_unit_pages`是单元长度，单位是页；
  >
  > 全局变量`pcpu_unit_size`是单元长度，单位是字节；
  >
  > 全局变量`pcpu_atom_size`是原子长度，即对齐值，每个组的长度必须是原子长度的整数倍；
  >
  > 全局变量`pcpu_base_addr`是基准地址，取第一块的基准地址；

- 函数`setup_per_cpu_areas`设置全局数组`__per_cpu_offset`，该数组存放每个处理器对应的单元的偏移：

  ```c
  delta = (unsigned long)pcpu_base_addr - (unsigned long)__per_cpu_start;
  __per_cpu_offset[cpu] = delta + pcpu_unit_offsets[cpu];

  pcpu_base_addr 是第一块的基准地址，__per_cpu_start 是内核中每处理器数据段的起始地址，delta是这两个地址的差值。
  pcpu_unit_offsets 是相对基准地址的偏移， 而 __per_cpu_offset 是相对内核中每处理器数据段的起始地址的偏移。

  已经有全局数组 pcpu_unit_offsets ，为什么还要定义全局数组 __per_cpu_offset，主要是为了照顾静态每处理器变量：使用宏`this_cpu_ptr(ptr)`访问静态每处理器变量时，this_cpu_ptr(ptr)= ptr + __per_cpu_offset[cpu]（cpu是当前处理器变量的编号）， `ptr`是内核镜像的每处理器数据段中变量的虚拟地址，必须加上 delta 以转换成第一块中的变量副本的地址。

  为每处理器变量分配内存的时候，返回的地址是（chunk->base_addr + offset - delta），提前减去了 delta ，其中 chunk->base_addr 是块的基准地址， offset 是单元内部的偏移。

  ```



### 2.7 创建块

- 函数`pcpu_creat_chunk`负责创建块，以基于`vmalloc`区域的块分配方式为例说明执行过程：
  1. 调用函数`pcpu_alloc_chunk`，分配`pcpu_chunk`实例并且初始化；
  2. 调研函数`pcpu_get_vm_areas`，负责从`vmalloc`虚拟地址空间分配虚拟内存区域；
  3. 块的基准地址等于（第 0 组的起始地址 - 第 0 组的偏移）。

- 函数`pcpu_get_vm_areas`的输入参数是以下4个参数：
  1. `pcpu_group_offsets`: 每个组的偏移；
  2. `pcpu_group_sizes`: 每个组的长度；
  3. `pcpu_nr_groups`: 组的数量；
  4. `pcpu_atom_size`: 原子长度。

- 需要找到一个基准值`base`，第 n 组的虚拟内存区域是`(base + pcpu_group_offsets[n], base + pcpu_group_offsets[n] + pcpu_group_sizes[n])`，基准值必须满足条件：基准值和原子长度对齐，并且每个组的虚拟内存区域是空闲的。



### 2.8 分配内存

- 每处理器内存分配器分配内存的算法如下：

  ```
  把申请长度向上对齐到偶数
  根据申请长度计算出插槽号 n

  遍历从插槽号 n 到最大插槽号 pcpu_nr_slots 的每个插槽 {
  	遍历插槽中的每个块 {
  		如果申请长度大于块的最大连续空间字节数，那么不能从这个块分配内存。
  		遍历块的分配图，如果有一个空闲小块的长度大于或等于申请长度，处理如下：
  		如果小块的长度大于申请长度，先把这个小块分裂为两个小块。
  		更新分配图。
  		更新空闲字节数和最大连续空闲字节数
  		根据空闲字节数计算新的插槽号，把块移到新的插槽中
  	}
  }

  如果分配失败，处理如下：
  如果是原子分配 {
  	向全局工作队列添加1各工作项 pcpu_balance_work，异步创建新的块。
  } 否则 {
  	如果最后一个插槽是空的，那么创建新的块，然后重新分配内存。
  }

  如果分配成功，处理如下：
  如果是原子分配 {
  	如果空闲的已映射到物理页的虚拟页的数量小于 PCPU_EMPTY_POP_PAGES_LOW（值为2），那么向全局工作队列添加1个工作项 pcpu_balance_work，异步分配物理页 。
  } 否则 {
  	在分配出去的区域中，对于没有映射到物理页的虚拟页，分配物理页，在内核的页表中把虚拟页页映射到物理页。
  }
  把分配出去的区域清零。
  返回地址（chunk -> base_addr + offset - delta），其中 chunk -> base_addr是块的基准地址，offset是单元内部的偏移，delta是（pcpu_base_addr - __per_cpu_start），即第一块的基准地址和内核中每处理器数据段的起始地址的差值。

  ```
