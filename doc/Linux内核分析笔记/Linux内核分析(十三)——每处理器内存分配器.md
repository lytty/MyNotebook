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

