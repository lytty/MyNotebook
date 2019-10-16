# Linux内核分析(十三)——每处理器内存分配器

- 在多处理器系统中，每处理器变量为每个处理器生成一个变量的副本，每个处理器访问自己的副本，从而避免了处理器之间的互斥和处理器缓存之间的同步，提高了程序的执行速度。

  

## 13.1 编程接口

- 每处理器变量分为静态和动态两种。

  

### 13.1.1 静态每处理器变量

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

     

### 13.1.2 动态每处理器变量

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



### 13.1.3 访问每处理器变量

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



## 13.2 技术原理

- 每处理器区域是按块（chunk）分配的，每个块分为多个长度相同的单元（unit），每个处理器对应一个单元。
- 分配块的方式有两种：
  - 基于`vmalloc`区域的块分配。从`vmalloc`虚拟地址空间分配虚拟内存区域，然后映射到物理页。该分配方式适合多处理器系统。
  - 基于内核内存的的块分配。直接从页分配器分配页，使用直接映射的内核虚拟地址空间。该分配方式适合单处理器系统或者处理器没有内存管理单元部件的情况，目前这种分配方式不支持ＮＵＭＡ系统。
- 多处理器系统默认使用基于`vmalloc`区域的块分配方式，单处理器系统默认使用基于内核内存的的块分配方式。



### 13.2.1 基于`vmalloc`区域的每处理器内存分配器

- 基于`vmalloc`区域的每处理器内存分配器的数据结构如下图所示　![1570851306118](/home/haibin.xu/haibin/doc/picture/图13.1-基于vmalloc区域的每处理器内存分配器.png)

- 每个块对应一个`pcpu_chunk`实例：

  > 1. 成员`data`指向`vm_struct`指针数组，`vm_struct`结构体是不连续页分配器的数据结构，每个组对应一个`vm_struct`实例，`vm_struct`实例的成员`addr`指向组的起始地址。块以组为单位分配虚拟内存区域，一个组的虚拟地址是连续的，不同组的虚拟地址不一定是连续的。
  > 2. 成员`populated`是填充位图，记录那些虚拟页已经映射到物理页：成员`nr_populated`是已填充页数，记录已经映射到物理页的虚拟页的数量。创建块时，只分配了虚拟内存区域，没有分配物理页，从块分配每处理器变量时，才分配物理页。物理页的`page`实例成员`index`指向`pcpu_chunk`实例。
  > 3. 成员`map`指向分配图，分配图是一个整数数组，用来存放每个小块（`block`）的偏移和分配状态，成员`map_used`记录分配图已使用的项数。
  > 4. 成员`free_size`记录空闲字节数，成员`contig_hint`记录最大的连续空闲字节数。
  > 5. 成员`base_size`是块的基准地址，一个块的每个组必须满足条件：组的起始地址 = （块的基准地址 + 组的偏移）。
  > 6. 成员`list`用来把块加入块插槽，插槽号是根据空闲字节数算出来的。



### 13.2.2 基于内核内存的每处理器内存分配器

- 基于内核内存的每处理器内存分配器的数据结构如下图所示![1571058000165](/home/haibin.xu/haibin/doc/picture/图13.2-基于内核内存的每处理器内存分配器.png)

- 和基于`vmalloc`区域的每处理器内存分配器的不同如下：

  > 1. `pcpu_trunk`实例的成员`data`指向`page`结构体数组；
  > 2. 创建块的时候，分配了物理页，虚拟页直接映射到物理页；
  > 3. 不支持`NUMA`系统，一个块只有一个组。



### 13.2.3 

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

