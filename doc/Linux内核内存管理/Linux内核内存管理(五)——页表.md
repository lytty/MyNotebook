# Linux内核内存管理(五)——页表

## 1. 统一的页表框架

- 页表用来把虚拟页映射到物理页，并且存放页的保护位，即访问权限。在Linux 4.11版本之前，Liinux内核吧页表分为4级：

  > 1. 页全局目录（Page Global Directory，PGD）
  > 2. 页上层目录（Page Upper Directory，PUD）
  > 3. 页中间目录（Page Middle Directory，PMD）
  > 4. 直接页表（Page Table， PT）

  4.11 版本把页表扩展到五级，在页全局目录和页上层目录之间增加了页四级目录（Page 4th Directory，P4D）。

- 各种处理器架构可以选择使用五级、四级、三级或两极页表，同一种处理器架构在页长度不同的情况下可能选择不同的页表级数。可以使用配置宏 CONFIG_PGTABLE_LEVELS 配置页表级数，一般使用默认值。

- 如果选择四级页表，那么使用页全局目录、页上层目录、页中间目录和直接页表；如果选择三级页表，那么使用页全局目录、页中间目录和直接页表；如果选择两级页表，那么使用页全局目录和直接页表；

- 如果不使用页中间目录，那么内核在头文件“include/asm-generic/pgtable-nopmd.h”中模拟页中间目录，调用函数pmd_offset()根据页上层目录表项和虚拟地址获取页中间目录表项的时候，直接把页上层目录表项指针强制转换成页中间目录表项指针并返回，访问页中间目录表项实际上是访问页上层目录表项。

  ```c
  /* linux-4.14/include/asm-generic/pgtable-nopmd.h */

  18  typedef struct { pud_t pud; } pmd_t;
  ...
  44  static inline pmd_t * pmd_offset(pud_t * pud, unsigned long address)
  45  {
  46  	return (pmd_t *)pud;
  47  }
  ```

  ​        同样，如果不使用页上层目录，那么内核在头文件“include/asm-generic/pgtable-nopud.h”中模拟页上层目录。如果不使用页四级目录，那么内核在头文件“include/asm-generic/pgtable-nop4d.h”中模拟页四级目录。



## 2. 五级页表结构

![](../picture/五级页表结构.png)

- 每个进程有独立的页表，进程的mm_struct实例的成员pgd指向页全局目录，前面四级页表的表项存放下一级页表的起始地址，直接页表的表项存放页帧号（Page Frame Number，PFN）。

- 内核也有一个页表，0号内核线程的进程描述符 init_task 的成员 active_mm 指向内存描述符 init_mm，内存描述符 init_mm 的成员 pgd 指向内核的页全局目录 swapper_pg_dir。

- 虚拟地址被分解为6个部分：页全局目录索引、页四级目录索引、页上层目录索引、页中间目录索引、直接页表索引和业内偏移。

- 查询页表，把虚拟地址转换成物理地址的过程如下：

  > 1. 根据页全局目录的起始地址和页全局目录索引得到页全局目录表项的地址，然后从表项得到页四级目录的起始地址；
  > 2. 根据页四级目录的起始地址和页四级目录索引得到页四级目录表项的地址，然后从表项得到页上层目录的起始地址；
  > 3. 根据页上层目录的起始地址和页上层目录索引得到页上层目录表项的地址，然后从表项得到页中间目录的起始地址；
  > 4. 根据页中间目录的起始地址和页中间目录索引得到页中间目录表项的地址，然后从表项得到直接页表的起始地址；
  > 5. 根据直接页表的起始地址和直接页表索引得到直接页表表项的的地址，然后从表项得到页帧号；
  > 6. 把页帧号和页内偏移组合成物理地址。



## 3. 页表相关宏定义

- 内核定义了各级页表索引在*虚拟地址*中的偏移：

  > 1. PAGE_SHIFT：页内偏移的位数，也是直接页表索引的偏移；
  > 2. PMD_SHIFT：页中间目录索引的偏移；
  > 3. PUD_SHIFT：页上层目录索引的偏移；
  > 4. P4D_SHIFT：页四级目录索引的偏移；
  > 5. PGDIR_SHIFT：页全局目录索引的偏移



- 内核定义了各级页表表项描述的地址空间的大小：

  > 1. PGDIR_SIZE：页全局目录表项映射的地址空间的大小；
  > 2. P4D_SIZE：页四级目录表项映射的地址空间的大小；
  > 3. PUD_SIZE：页上层目录表项映射的地址空间的大小；
  > 4. PMD_SIZE：页中间目录表项映射的地址空间的大小；
  > 5. PAGE_SIZE：直接页表项映射的地址空间的大小，也是页长度；



- 内核定义了各级页表能存放的指针数量，即表项数量：

  > 1. PTRS_PER_PGD：页全局目录的表项数量；
  > 2. PTRS_PER_P4D：页四级目录的表项数量；
  > 3. PTRS_PER_PUD：页上层目录的表项数量；
  > 4. PTRS_PER_PMD：页中间目录的表项数量；
  > 5. PTRS_PER_PTE：直接页表的表项数量；



- 内核定义了各级页表占用的页的阶数：

  > 1. PGD_ORDER：页全局目录占用的页的阶数；
  > 2. P4D_ORDER：页四级目录占用的页的阶数；
  > 3. PUD_ORDER：页上层目录占用的页的阶数；
  > 4. PMD_ORDER：页中间目录占用的页的阶数；
  > 5. PTE_ORDER：直接页表占用的页的阶数；



- 内核定义了各级页表表项的的数据结构：

  > 1. pgd_t：页全局目录表项的数据结构；
  > 2. p4d_t：页四级目录表项的数据结构；
  > 3. pud_t：页上层目录表项的数据结构；
  > 4. pmd_t：页中间目录表项的数据结构；
  > 5. pte_t：直接页表项的数据结构；

  这些数据结构通常是只包含一个无符号长整型的结构体，例如页全局目录表项的数据结构定义如下：`typedef unsigned long pgd_t;`



- 以页全局目录为例，内核定义了以下宏和内联函数：

  > 1. 宏 pgd_val() 用来把 pgd_t 类型转换成无符号长整型：`#define pgd_val(x)	((x).pgd)`
  > 2. 宏 `__pgd()` 用来把无符号长整型转换成 pgd_t 类型：`#define __pgd(x) ((pgd_t) { (x) })`
  > 3. 宏 `pgd_index(address)` 用来从虚拟地址分解出页全局目录索引：`#define pgd_index(addr)	(((addr) >> PGDIR_SHIFT) & (PTRS_PER_PGD - 1))`
  > 4. 宏`pgd_offset(mm, addr)`用来返回指定进程的虚拟地址对应的页全局目录表项的地址。内核定义了宏`pgd_offset_k(addr)`，用来在内核的页全局目录找到虚拟地址对应的表项：`#define pgd_offset_k(addr)	pgd_offset(&init_mm, addr)`
  > 5. 内联函数`pgd_none(pgd)`用来判断页全局目录表项是空表项，空表项没有指向下一级页表，如果是空表项，那么返回非零值。
  > 6. 内联函数`pgd_present(pgd)`用来判断页全局目录是否存在，即是否指向下一级页表，如果表项指向下一级页表，那么返回非零值。



- 前四级页表的表项存放下一级页表的起始地址，直接页表的表项存放页帧号和标志位。大多数处理器支持的最小页长度是4KB，有些处理器支持1KB的页长度，可以使用页帧号以外的位作为标志位。

  ​        不同处理器架构的页表项的格式不同，为了屏蔽差异性，每种处理器架构自定义访问的宏或内联函数：宏 `pte_pfn(x)`从（直接页表）页表项取出页帧号，宏 `pfn_pte(pfn, prot)` 把页帧号和标志位组合成页表项。

  ​		有些标志位是要求每种处理器架构都必须实现的，每种处理器架构定义宏或内联函数来访问这些标志位，例如：

  > 1. `pte_present(pte)` 检查页是否在内存中，如果不在内存中，说明页被换出到交换区；
  > 2. `pte_write(pte)` 检查页是否可写；
  > 3. `pte_young(pte)` 检查页是否被访问过；
  > 4. `pte_dirty(pte)` 检查页是不是脏的，即页的数据是不是被修改过；

  ​		各种处理器架构也可以定义私有的标志位。



## 4. 页帧号

- 如果物理地址空间按4KB（4096字节）划分页，无论页是有效还是无效的，都把每一页按从低到高的顺序进行编号，我们称为页帧号。物理内存地址空间越大，页帧号也就越大。32位操作系统4GB 物理地址空间的页帧号范围是0—0xfffff。
- 由于页帧号范围是0—0xfffff，使用20 位便可以记录。编号的目的是什么呢？特定的页帧号代表特定的物理地址空间，空间大小是4096 字节。对于物理地址范围0x00003000—0x00003fff，我们直接用页帧号3 去表示就行。除此之外，我们可以对某页设定一些属性标志，比如这个页是否是有效的内存，是否可以写，是否被访问过等。页帧号加属性标志就能表明一个页大小的内存情况。



## 5. ARM64处理器的页表

- ARM64处理器把页表称为转换表（translation table），最多4级。ARM64处理器支持3中页长度：4KB、16KB、64KB。页长度和虚拟地址的宽度决定了转换表的级数，如果虚拟地址的宽度是48位，页长度和转换表级数的关系如下所示。

  > 1. 页长度是4KB：使用4级页表，转换表和内核的页表术语对应关系是：0级转换表对应页全局目录，1级转换表对应页上层目录，2级转换表对应页中间目录，3级转换表对应直接页表。48位虚拟地址分解如下图所示：![1561816796440](../picture/页长4KB-48位虚拟地址分解.png)
  >
  >    每级转换表占用一页，有512 (2^9)项，索引是48位地址的9个位。
  >
  > 2. 页长度是16KB：使用4级转换表，转换表和内核的页表术语对应关系是：0级转换表对应页全局目录，1级转换表对应页上层目录，2级转换表对应页中间目录，3级转换表对应直接页表。48位虚拟地址分解如下图所示：![1561817634541](../picture/页长16KB-48位虚拟地址分解.png)
  >
  >    0级转换表有2项，索引是48位虚拟地址的最高位；其他转换表占用一页，有2048（2^11）项，索引是48位虚拟地址的11个位。
  >
  > 3. 页长度是64KB：使用3级页表，转换表和内核的页表术语的对应关系是：1级转换表对应页全局目录，2级转换表对应页中间目录，3级转换表对应直接页表。48位虚拟地址分解如下图所示：![1561818421082](../picture/页长64KB-48位虚拟地址分解.png)
  >
  >    1级转换表有64（2^6）项，索引是48位虚拟地址的最高6位；其他转换表占用一页，有8192（2^13）项，索引是48位虚拟地址的13个位。



- ARM64处理器把表项称为描述符（descriptor），使用64位的长描述符格式。描述符的第0位指示描述符是不是有效的；0表示无效，1表示有效；第1位指定描述符类型，如下：

  > 1. 在第0~2级转换表中，0表示块（block）描述符，1表示表（table）描述符。块描述符存放一个内存块（即巨型页）的起始地址，表描述符存放下一级转换表的地址。
  > 2. 在第3级转换表中，0表示保留描述符，1表示页描述符。



- 第0~2级转换表的描述符分为3种：

  > 1. 无效描述符：无效描述符的第0位是0，格式如下图：![1561824177632](../picture/0~2级转换表的无效描述符.png)
  >
  > 2. 块描述符：块描述符的最低两位是 01，当虚拟地址的位数是48时，块描述符的格式如下图：![1561826044998](../picture/0~2级转换表的块描述符.png)
  >
  >    n的取值：如果页长度是4KB，那么1级描述符的n是30，2级描述符的n是21；如果页长度是16KB，那么2级描述符的n是25；如果页长度是64KB，那么2级描述符的n是29。
  >
  > 3. 表描述符：表描述符的最低两位是 11，当虚拟地址的位数是48时，表描述符的格式如下图：![1561830309849](../picture/0~2级转换表的表描述符.png)
  >
  >    m的取值：如果页长度是4KB，m是12；如果页长度是16KB，m是14；如果页长度是64KB，m是16。
  >
  >    注意 ”下一级表地址“是下一级转换表的物理地址。使用物理地址，而不使用虚拟地址，是因为ARM64处理器支持转换表遍历（translation table walk）：当ARM64处理器的内存管理单元需要把虚拟地址转换成物理地址时，首先在页表缓存中匹配虚拟地址，如果没有匹配，那么处理器访问内存中的转换表，把最后一级转换表项复制到页表缓存。使用物理地址，可以避免处理器访问内存中的转换表时需要把转换表的虚拟地址转换成物理地址。



- 第3级转换表的描述符分为3种

  > 1. 无效描述符：无效描述符的第0位是0，格式如下图：![1561832180943](../picture/第3级转换表的无效描述符.png)
  > 2. 保留描述符：保留描述符的最低两位是01，现在没有使用，保留给将来使用，格式如下图：![1561832479878](../picture/第3级转换表的保留描述符.png)
  > 3. 页描述符：页描述符最低两位是11，当虚拟地址的位数是48时，页长度分别为4KB、16KB和64KB的页描述符的格式如下图：![1561834088152](../picture/第3级转换表的页描述符.png)



- 在块描述符和页描述符中，内存属性被拆分成一个高属性块和一个低属性块，如下图：![1561838017591](../picture/块-页描述符中的内存属性.png)

  > 1. 第59~62位：基于页的硬件属性（Page-Based Hardware Attributes，PBHA），如果有实现ARMv8.2-TTPBHA，忽略。
  > 2. 第55~58位：保留给软件使用。
  > 3. 第54位：在异常级别0，表示UXN（Unprivileged execute-Never），即不允许异常级别0执行内核代码；在其他异常级别，表示XN（execute-Never），不允许执行。
  > 4. 第53位：PXN（Privileged execute-Never），不允许在特权级别（即异常级别1/2/3）执行。
  > 5. 第52位：连续（Contiguous），指示这条转换表项属于一个连续表项集合，一个连续表项集合可以被缓存在一条TLB表项里面。
  > 6. 第51位：脏位修饰符（Dirty Bit Modifier，DBM），指示页或内存块是否被修改过。
  > 7. 第11位：非全局（not global，nG）。nG位是1，表示转换不是全局的，是进程私有的，有一个关联的地址空间标识符（Address Space Identifier，ASID）；nG位是0，表示转换时全局的，是所有进程共享的，内核的页或内存块是所有进程共享的。
  > 8. 第10位：访问标志（Access Flag，AF），指示页或内存块自从相应的转换表描述符中的访问标志被设置为0以后是否被访问过。
  > 9. 第8~9位：可共享性（SHareability，SH），00表示不共享，01是保留值，10表示外部共享，11表示内部共享。
  > 10. 第6~7位：AP[2 ：1]（Data Access Permission，数据访问权限），在阶段1 转换中，AP[2]用来选择只读或读写，1 表示只读，0 表示读写；AP[1] 用来选择是否允许异常级别 0 访问，1 表示允许异常级别 0 访问，0 表示不允许异常级别 0 访问。在非安全异常级别 1 和 0 转换机制的阶段 2 转换中， AP[2 ：1] 为 00 表示不允许访问，01 表示只读，10 表示只写， 11 表示读写。
  > 11. 第5位：非安全（Non-Secure，NS）。对于安全状态的内存访问，指定输出地址在安全地址映射还是非安全地址映射。
  > 12. 第2~4位：内存属性索引（memory attributes index，AttrIndex），指定及寄存器MAIR_ELx中内存属性字段的索引，内存属性间接寄存器（Memory Attribute Indirection Register，MAIR_ELx）有8个8位内存属性字段：`Attr<n>`，n等于 0~7。

## 6. 内核页表初始化

- 本章节基于arm32架构的Linux4.14内核展开分析。

- 在内核使用内存前，需要初始化内核的页表，初始化页表主要在`map_lowmem()`中，在映射页表之前，需要把页表的表项清零，主要在`prepare_page_table()`函数中实现。

- 函数调用关系：`start_kernel()->setup_arch()->paging_init()->prepare_page_table()`

- `prepare_page_table()`函数定义及解析如下：

  ```c
  [linux-4.14/arch/arm/mm/mmu.c]

  1246  static inline void prepare_page_table(void)
  1247  {
  1248  	unsigned long addr;
  1249  	phys_addr_t end;
  1250  
  1251  	/*
  1252  	 * Clear out all the mappings below the kernel image.
  		 * 通过前两个 for 循环，将用户空间的所有页表项清零。
  1253  	 */
      	/* 第一个for循环，将 0~MODULES_VADDR-1 范围内的页表项清零，MODULES_VADDR 为用户空间modules 起始地址（arm32架构下其值一般为 0xbf00 0000）,可参考《虚拟地址空间布局》章节*/
  1254  	for (addr = 0; addr < MODULES_VADDR; addr += PMD_SIZE)
  1255  		pmd_clear(pmd_off_k(addr));
  1256  
  1257  #ifdef CONFIG_XIP_KERNEL
  1258  	/* The XIP kernel is mapped in the module area -- skip over it */
  1259  	addr = ((unsigned long)_exiprom + PMD_SIZE - 1) & PMD_MASK;
  1260  #endif
      	/* 第二个for循环，将 MODULES_VADDR-1 ~ PAGE_OFFSET-1 范围内的页表项清零， PAGE_OFFSET为内核空间起始地址。*/
  1261  	for ( ; addr < PAGE_OFFSET; addr += PMD_SIZE)
  1262  		pmd_clear(pmd_off_k(addr));
  1263  
  1264  	/*
  1265  	 * Find the end of the first block of lowmem.
  1266  	 */
      	/* 以ARM Vexpress平台为例，单步调试打印memblock.memory.regions[0].base值为0x60000000，memblock.memory.regions[0].size值为0x40000000,也就是说memblock.memory.regions[0]中存放的是内核内存的物理起始地址和大小。
          * arm_lowmem_limit 为低端地址空间的物理地址，ARM Vexpress平台下，该值为0x8f800000
          */
  1267  	end = memblock.memory.regions[0].base + memblock.memory.regions[0].size;
  1268  	if (end >= arm_lowmem_limit)
  1269  		end = arm_lowmem_limit;
  1270  
  1271  	/*
  1272  	 * Clear out all the kernel space mappings, except for the first
  1273  	 * memory bank, up to the vmalloc region.
  1274  	 */
	    	/* 将 arm_lowmem_limit（转化后的虚拟地址） ~ VMALLOC_START-1 范围内的页表项（参考《虚拟地址空间布局》章节，该部分虚拟地址范围 0xef800000 ~ 0xf0000000, 8M大小）清零*/
  1275  	for (addr = __phys_to_virt(end);
  1276  	     addr < VMALLOC_START; addr += PMD_SIZE)
  1277  		pmd_clear(pmd_off_k(addr));
  1278  }


  [linux-4.14/arch/arm/mm/mm.h]
  37  static inline pmd_t *pmd_off_k(unsigned long virt)
  38  {
      	/* 通过给定的虚拟地址，获取pmd页表目录页表项 */
  39  	return pmd_offset(pud_offset(pgd_offset_k(virt), virt), virt);
  40  }


  [linux-4.14/arch/arm/include/asm/pgtable-2level.h]
  205  #define pmd_clear(pmdp)			\
  206  	do {				\
  207  		pmdp[0] = __pmd(0);	\
  208  		pmdp[1] = __pmd(0);	\
  			/* clean_pmd_entry()函数 刷新页表对应的TLB */
  209  		clean_pmd_entry(pmdp);	\
  210  	} while (0)

  [linux-4.14/arch/arm/include/asm/tlbflush.h]
  /* 刷新页表缓存，此处不作细讲 */
  591  static inline void clean_pmd_entry(void *pmd)
  592  {
  593  	const unsigned int __tlb_flag = __cpu_tlb_flags;
  594  
  595  	tlb_op(TLB_DCLEAN, "c7, c10, 1	@ flush_pmd", pmd);
  596  	tlb_l2_op(TLB_L2CLEAN_FR, "c15, c9, 1  @ L2 flush_pmd", pmd);
  597  }

  ```



## 7. 内核页表创建

- map_lowmem() 函数定义及解析：

```c
[linux-4.14/arch/arm/include/asm/pgtable-2level.h]
96  #define SECTION_SHIFT		20
97  #define SECTION_SIZE		(1UL << SECTION_SHIFT)
98  #define SECTION_MASK		(~(SECTION_SIZE-1))

[linux-4.14/arch/arm/include/asm/memory.h]
121  #ifdef CONFIG_XIP_KERNEL
122  #define KERNEL_START		_sdata
123  #else
124  #define KERNEL_START		_stext
125  #endif
126  #define KERNEL_END		_end
127  

[linux-4.14/include/linux/kernel.h]
86  #define __round_mask(x, y) ((__typeof__(x))((y)-1))
87  #define round_up(x, y) ((((x)-1) | __round_mask(x, y))+1)
88  #define round_down(x, y) ((x) & ~__round_mask(x, y))

[linux-4.14/include/linux/memblock.h]    
386  #define for_each_memblock(memblock_type, region)					\
387  	for (region = memblock.memblock_type.regions;					\
388  	     region < (memblock.memblock_type.regions + memblock.memblock_type.cnt);	\
389  	     region++)

[linux-4.14/arch/arm/mm/mmu.c]
1429  static void __init map_lowmem(void)
1430  {
1431  	struct memblock_region *reg;
    	/* KERNEL_START 为 _stext， ARM Vexpress平台下值为0xc0008280，SECTION_SIZE为2^20, 通过round_down宏计算，kernel_x_start值为0x60000000（物理地址）;
        *  __init_end 值为 0xc10d8000（虚拟地址，转成物理地址：0x610d8000）,SECTION_SIZE为2^20, 通过round_up宏计算，kernel_x_end值为0x61100000（物理地址）;
        round_down、round_up两个宏的定义上面已给出，请自行揣摩其实现的功能
        */
1432  	phys_addr_t kernel_x_start = round_down(__pa(KERNEL_START), SECTION_SIZE);
1433  	phys_addr_t kernel_x_end = round_up(__pa(__init_end), SECTION_SIZE);
1434  
1435  	/* Map all the lowmem memory banks. */
    	/* for_each_memblock()是一个宏，其展开式如 386~389行，此处for循环遍历memblock下memory类型 下所有的region。关于memblock相关介绍，此处不细讲，读者只需了解memblock 内存管理机制主要用于Linux Kernel 启动阶段(kernel启动 -> kernel 通用内存管理初始化完成.) 的一个临时内存分配器，其基于静态数组, 采用的逆向最先适配的分配策略.
  		*/
1436  	for_each_memblock(memory, reg) {
1437  		phys_addr_t start = reg->base;
1438  		phys_addr_t end = start + reg->size;
1439  		struct map_desc map;
1440  
1441  		if (memblock_is_nomap(reg))
1442  			continue;
1443  
1444  		if (end > arm_lowmem_limit)
1445  			end = arm_lowmem_limit;
1446  		if (start >= end)
1447  			break;
1448  
1449  		if (end < kernel_x_start) {
    			/* 用户空间的内存区间创建 */
1450  			map.pfn = __phys_to_pfn(start);
1451  			map.virtual = __phys_to_virt(start);
1452  			map.length = end - start;
1453  			map.type = MT_MEMORY_RWX;
1454  			/* 创建映射，create_mapping()函数在《页表的映射过程》章节中有详细解析 */
1455  			create_mapping(&map);
1456  		} else if (start >= kernel_x_end) {
    			/* 内核空间（去除kernel代码段和高端地址空间）的内存区间创建 */
1457  			map.pfn = __phys_to_pfn(start);
1458  			map.virtual = __phys_to_virt(start);
1459  			map.length = end - start;
1460  			map.type = MT_MEMORY_RW;
1461  			/* 同上 */
1462  			create_mapping(&map);
1463  		} else {
1464  			/* This better cover the entire kernel */
1465  			if (start < kernel_x_start) {
    				/* start ~ kernel_x_start 内存区间创建 */
1466  				map.pfn = __phys_to_pfn(start);
1467  				map.virtual = __phys_to_virt(start);
1468  				map.length = kernel_x_start - start;
1469  				map.type = MT_MEMORY_RW;
1470  				/* 同上 */
1471  				create_mapping(&map);
1472  			}
1473  			/* kernel_x_start ~ kernel_x_end，即kernel image 内存区间创建 */
1474  			map.pfn = __phys_to_pfn(kernel_x_start);
1475  			map.virtual = __phys_to_virt(kernel_x_start);
1476  			map.length = kernel_x_end - kernel_x_start;
1477  			map.type = MT_MEMORY_RWX;
1478  			/* 同上 */
1479  			create_mapping(&map);
1480  
1481  			if (kernel_x_end < end) {
    				/* kernel_x_end ~ arm_lowmem_limit 内存区间创建 */
1482  				map.pfn = __phys_to_pfn(kernel_x_end);
1483  				map.virtual = __phys_to_virt(kernel_x_end);
1484  				map.length = end - kernel_x_end;
1485  				map.type = MT_MEMORY_RW;
1486  				/* 同上 */
1487  				create_mapping(&map);
1488  			}
1489  		}
1490  	}
1491  }
```

- 页表的创建和映射是在`map_lowmem()`函数中，会从内存开始的地方覆盖到`arm_lowmem_limit`处。即映射整个低端地址空间。
- MT_MEMORY_RW 和 MT_MEMORY_RWX 的区别在于 ARM 页表项有一个 XN 比特位， XN 比特位置为 1, 表示这段内存区域不允许执行。从上面代码中可以知道，只有 kernel image 内存区间的 map.type = MT_MEMORY_RWX。
- create_mapping() 实现内存区间的映射，这里创建的映射就是物理内存直接映射，或者叫做线性映射。
