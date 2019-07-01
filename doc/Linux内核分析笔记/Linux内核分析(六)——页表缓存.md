# Linux内核分析(六)——页表缓存

- 处理器的内存管理单元（Memory Management Unit，MMU）负责把虚拟地址转换成物理地址，为了改进虚拟地址转换成物理地址的转换速度，避免每次转换都需要查询内存中的页表，处理器厂商在内存管理单元里面增加了一个称为TLB（Translation Lookaside Buffer）的高速缓存，TLB直译为转换后备缓冲区，意译为页表缓存。

- 页表缓存用来缓存最近使用过的页表项，有些处理器使用两级页表缓存；第一级TLB分为指令TLB和数据TLB，优点是取指令和取数据可以并行执行；第二级TLB是统一TLB（Unified TLB），即指令和数据共用的TLB。

  

## 1.  TLB表项格式

- 不同处理器架构的TLB表项的格式不同。ARM64处理器的每条TLB表项不仅包含虚拟地址和物理地址，也包含属性；内存类型、缓存策略、访问权限、地址空间标识符（Address Space Identifier，ASID）和虚拟机标识符（Virtual Machine Identifier，VMID）。地址空间标识符区分不同进程的页表项，虚拟机标识符区分不同虚拟机的页表项。

  

## 2. TLB管理

- 如果内核修改了可能缓存在TLB里面的页表项，那么内核必须负责使旧的TLB表项失效，内核定义了每种处理器架构必须实现的函数。

  ```c
  void flush_tlb_all(void);
  ```

  使所有TLB表项失效。

  ```c
  void flush_tlb_mm(struct mm_struct *mm);
  ```

  使指定用户地址空间的所有TLB表项失效，参数 mm 是进程的内存描述符。

  ```c
  void flush_tlb_range(struct vm_area_struct *vma,
       unsigned long start, unsigned long end);
  ```

  使指定用户地址空间的某个范围的TLB表项失效，参数 vma 是虚拟内存区域，start是起始地址，end是结束地址（不包括）。

  ```c
  void flush_tlb_page(struct vm_area_struct *vma,
     				    unsigned long uaddr);
  ```

  使指定用户地址空间里面的指定虚拟页的TLB表项失效，参数 vma 是虚拟内存区域，uaddr 是一个虚拟页中的任意虚拟地址。

  ```c
  void flush_tlb_kernel_range(unsigned long start, unsigned long end);
  ```

  使内核的某个虚拟地址范围的TLB失效，start是起始地址，end是结束地址（不包括）。

  ```c
  void update_mmu_cache(struct vm_area_struct *vma,
    				   unsigned long addr, pte_t *ptep);
  ```

  修改页表项以后把页表项设置到页表缓存，由软件管理页表缓存的处理器必须实现该函数，例如MIPS处理器。

  ARM64处理器的内存管理单元可以访问内存中的页表，把页表项复制到页表缓存，所以ARM64架构的该函数什么都不用做。

  ```c
  void tlb_migrate_finish(struct mm_struct *mm);
  ```

  内核把进程从一个处理器迁移到另一个处理器以后，调用该函数以更新页表缓存或上下文特定信息。

- 当TLB没有命中的时候，ARM64处理器的内存管理单元自动遍历内存中的页表，把页表复制到TLB，不需要软件把页表项写到TLB，所以ARM64架构没有提供些TLB的指令。 

  ARM64架构提供了一条TLB失效指令：

  ```
  TLBI <type><level>{IS} {, <Xt>}
  ```

  > 1. 字段<type>的常见选项如下：
  >    - ALL：所有表项。
  >    - VMALL：当前虚拟机的阶段1的所有表项，即表项的VMID是当前虚拟机的VMID。虚拟机里面运行的客户操作系统的虚拟地址转换成物理地址分两个阶段：第一个阶段把虚拟地址转换成中间物理地址，第2阶段把中间物理地址转换成物理地址。
  >    - VMALLS12：当前虚拟机的阶段1和阶段2的所有表项。
  >    - ASID：匹配寄存器Xt指定的ASID的表项。
  >    - VA：匹配寄存器Xt指定的虚拟地址和ASID的表项。
  >    - VAA：匹配寄存器Xt指定的虚拟地址并且ASID可以是任意值的表项。
  > 2. 字段<level>指定异常级别，取值如下：
  >    - E1：异常级别1。
  >    - E2：异常级别2。
  >    - E3：异常级别3。
  >
  > 3. 字段IS表示内部共享（Inner Shareable），即多个核共享。如果不使用IS，表示非共享，只被一个核使用。在SMP系统中，如果指令TLBI不携带字段IS，仅仅使当前核的TLB表项失效；如果指令TLBI携带字段IS，表示使所有核的TLB表项失效
  >
  > 4. 字段Xt是X0~X31中任何一个寄存器。例如ARM64内核实现了函数 flush_tlb_all ，用来使所有核的所有TLB表项失效，其代码如下：
  >
  >    ```c
  >    /* linux-4.14/arch/arm64/include/asm/tlbflush.h */
  >    110  static inline void flush_tlb_all(void)
  >    111  {
  >    112  	dsb(ishst);
  >    113  	__tlbi(vmalle1is);
  >    114  	dsb(ish);
  >    115  	isb();
  >    116  }
  >    ```
  >
  >    把宏展开以后是：
  >
  >    ```c
  >    static inline void flush_tlb_all(void)
  >    {
  >        asm volatile("dsb ishst" : : : "memory");
  >        asm ("tlbi vmallelis" : :);
  >        asm volatile("dsb ish" : : : "memory");
  >        asm volatile("isb" : : : "memory");
  >    }
  >    ```
  >
  >    ​        dsb ishst：确保屏障前面的存储指令执行完。dsb 是数据同步屏障（Data Synchronization Barrier），ishst中的ish表示共享域是内部共享（inner shareable），st表示存储（store），ishst表示数据同步屏障指令对所有核的存储指令起作用。
  >
  >    ​        tlbi vmallelis：使所有核上匹配当前VMID、阶段1和异常级别1的所有TLB表项失效。
  >
  >    ​         dsb ish：确保前面的TLB失效指令执行完。ish表示数据同步屏障指令对所有核起作用。
  >
  >    ​          ish：isb是指令同步屏障（Instruction Synchronization Barrier），这条指令冲刷处理器的流水线，重新读取屏障指令后面的所有指令。
  >
  >    ​         可以对比一下，ARM64内核实现了函数local_flush_tlb_all，用来使当前核的所有TLB表项失效，其代码如下：
  >
  >    ```c
  >    /* linux-4.14/arch/arm64/include/asm/tlbflush.h */
  >    102  static inline void local_flush_tlb_all(void)
  >    103  {
  >    104  	dsb(nshst);
  >    105  	__tlbi(vmalle1);
  >    106  	dsb(nsh);
  >    107  	isb();
  >    108  }
  >    ```
  >
  >    和 flush_tlb_all 如下：
  >
  >    > 1. 指令dsb中的字段ish换成了nsh，nsh是非共享（non-shareable），表示数据同步屏障指令仅仅在当前核起作用。
  >    > 2. 指令tlbi没有携带is，表示仅仅使当前核的TLB表示失效。
  >
  >    