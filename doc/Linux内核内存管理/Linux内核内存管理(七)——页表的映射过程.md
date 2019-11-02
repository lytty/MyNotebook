# Linux内核内存管理(七)——页表的映射过程

## 1. ARM32 页表映射

- 在 32bit 的Linux内核中一般采用3层的映射模型，第1层是页全局目录（Page Global Directory，PGD），第2层是页中间目录（Page Middle Directory，PMD），第3层是页面映射表（Page Table Entry，PTE）。
- ARM32系统中只用到两层映射，因此在实际代码中就要在3层的映射模型中合并1层。

### 1.1 段式映射

- 在ARM32架构中，可以按段（section）来映射，这时采用单层映射模式。在单层映射模式下，内存中有个段映射表，表中有4096个表项，每个表项的大小是4Byte，所以这个段映射表大小是16KB，而且其位置必须与16KB边界对齐。
- 当CPU访问内存时，32位虚拟地址的高12位 [31:20] 用作访问段映射表的索引，从表中找到相应的表项。每个表项提供了一个12位的物理地址，以及相应的标志位。将这12位物理地址和虚拟地址的低20位拼凑在一起，就得到32位的物理地址。
- 每个段表项可以寻址1MB大小的地址空间。在相同表项的情况下，虚拟地址的后20位恰好可以寻址 2^20，即1M大小的地址空间。

### 1.2 页表映射

![1562079955761](../picture/arm32处理器查询页表.png)

- 如上图，ARM32页表映射方式，MMU映射过程如上图所示。
- 在ARM32架构中，如果采用页表映射方式，段映射表就变成了一级映射表（First Level table，在Linux内核中成为PGD），其表项提供的不再是物理段地址，而是二级页表的基地址。32位虚拟地址的高 12 位（bit[31 : 20]）作为访问一级页表的索引值，找到相应的表项，每个表项指向一个二级页表的起始地址。以虚拟地址的次 8 位（bit[19 : 12]）作为访问二级页表的索引值，得到相应的页表项，从这个页表项中找到20位的物理页面地址。最后将这20位物理页面地址和虚拟地址的低 12 位拼凑在一起，得到最终的  32 位物理地址。这个过程在ARM32架构中由MMU应将完成，软件不需要介入。


### 1.3 页面映射的实现
- 相关宏设置

  ```c
  /* linux-4.14/arch/arm/include/asm/pgtable-2level.h */

  81  /*
  82   * PMD_SHIFT determines the size of the area a second-level page table can map
  83   * PGDIR_SHIFT determines what a third-level page table entry can map
  84   */
  85  #define PMD_SHIFT     21
  86  #define PGDIR_SHIFT       21
  87  
  88  #define PMD_SIZE      (1UL << PMD_SHIFT) //0x0020 0000
  89  #define PMD_MASK      (~(PMD_SIZE-1)) //0xFFE0 0000
  90  #define PGDIR_SIZE        (1UL << PGDIR_SHIFT) //0x0020 0000
  91  #define PGDIR_MASK        (~(PGDIR_SIZE-1)) //0xFFE0 0000
  ```

  PMD_SIZE 宏用于计算由页中间目录的一个单独表项所映射的区域大小;PGDIR_SIZE宏用于计算页全局目录中一个单独表项所能映射区域的大小。

  PGDIR_SHIFT和PMD_SHIFT都被设置成了21，而ARM32架构中一级页表PGD的偏移量应该是20，关于这个问题，后文会具体解释，此处暂时忽略。

- ARM Linux内核的也表映射是通过建立具体内存区间的页面映射来实现的。内存区间通过结构体 map_desc 来描述，具体定义如下：

    ```c
    /* linux-4.14/arch/arm/include/asm/mach/map.h */

    17  struct map_desc {
    18  	unsigned long virtual; // 虚拟地址的起始地址
    19  	unsigned long pfn; // 物理地址的起始地址的页帧号
    20  	unsigned long length; // 内存区间长度
    21  	unsigned int type; // 该内存区间的属性
    22  };
    ```

    1. 内存区间的属性通过一个全局的mem_type结构体数组来描述，struct mem_type 定义如下：

    ```c
    /* linux-4.14/arch/arm/mm/mm.h */
    42  struct mem_type {
    43  	pteval_t prot_pte; // 用于页面表项的控制位和标志位
    44  	pteval_t prot_pte_s2;
    45  	pmdval_t prot_l1; // 用于一级页面表的控制位和标志位
    46  	pmdval_t prot_sect;
    47  	unsigned int domain; //用于ARM中定义不同的域
    48  };
    ```

    全局 mem_type[] 数组描述所有的内存区间类型，其定义如下：

    ```c
    /* linux-4.14/arch/arm/mm/mmu.c */
    248  static struct mem_type mem_types[] __ro_after_init = {
    ...
    265  	[MT_DEVICE_CACHED] = {	  /* ioremap_cached */
    266  		.prot_pte	= PROT_PTE_DEVICE | L_PTE_MT_DEV_CACHED,
    267  		.prot_l1	= PMD_TYPE_TABLE,
    268  		.prot_sect	= PROT_SECT_DEVICE | PMD_SECT_WB,
    269  		.domain		= DOMAIN_IO,
    270  	},
    271  	[MT_DEVICE_WC] = {	/* ioremap_wc */
    272  		.prot_pte	= PROT_PTE_DEVICE | L_PTE_MT_DEV_WC,
    273  		.prot_l1	= PMD_TYPE_TABLE,
    274  		.prot_sect	= PROT_SECT_DEVICE,
    275  		.domain		= DOMAIN_IO,
    276  	},
    ...
    305  	[MT_MEMORY_RWX] = {
    306  		.prot_pte  = L_PTE_PRESENT | L_PTE_YOUNG | L_PTE_DIRTY,
    307  		.prot_l1   = PMD_TYPE_TABLE,
    308  		.prot_sect = PMD_TYPE_SECT | PMD_SECT_AP_WRITE,
    309  		.domain    = DOMAIN_KERNEL,
    310  	},
    311  	[MT_MEMORY_RW] = {
    312  		.prot_pte  = L_PTE_PRESENT | L_PTE_YOUNG | L_PTE_DIRTY |
    313  			     L_PTE_XN,
    314  		.prot_l1   = PMD_TYPE_TABLE,
    315  		.prot_sect = PMD_TYPE_SECT | PMD_SECT_AP_WRITE,
    316  		.domain    = DOMAIN_KERNEL,
    317  	},
    ...
    355  };
    ```



    2. ARM中允许使用16个不同的域，但在ARM Linux中只定义和使用3个。

    ```c
    /* linux-4.14/arch/arm/include/asm/domain.h */
    41  #define DOMAIN_KERNEL	2 // 用于系统空间
    42  #define DOMAIN_USER	1 // 用于用户空间
    43  #define DOMAIN_IO	0 // 用于I/O地址域，实际上也属于系统空间
    ```

    3. `prot_pte` 定义如下：

    ```c
    /* linux-4.14/arch/arm/include/asm/pgtable-2level.h */
    120  #define L_PTE_VALID		(_AT(pteval_t, 1) << 0)		/* Valid */
    121  #define L_PTE_PRESENT		(_AT(pteval_t, 1) << 0)
    122  #define L_PTE_YOUNG		(_AT(pteval_t, 1) << 1)
    123  #define L_PTE_DIRTY		(_AT(pteval_t, 1) << 6)
    124  #define L_PTE_RDONLY		(_AT(pteval_t, 1) << 7)
    125  #define L_PTE_USER		(_AT(pteval_t, 1) << 8)
    126  #define L_PTE_XN		(_AT(pteval_t, 1) << 9)
    127  #define L_PTE_SHARED		(_AT(pteval_t, 1) << 10)	/* shared(v6), coherent(xsc3) */
    128  #define L_PTE_NONE		(_AT(pteval_t, 1) << 11)

    /* linux-4.14/arch/arm/mm/mmu.c */
    244  #define PROT_PTE_DEVICE		L_PTE_PRESENT|L_PTE_YOUNG|L_PTE_DIRTY|L_PTE_XN
    245  #define PROT_PTE_S2_DEVICE	PROT_PTE_DEVICE
    246  #define PROT_SECT_DEVICE	PMD_TYPE_SECT|PMD_SECT_AP_WRITE
    ```

    4. `prot_l1`定义如下：

    ```c
    /* linux-4.0/arch/arm/include/asm/pgtable-2level-hwdef.h */
    19  #define PMD_TYPE_MASK		(_AT(pmdval_t, 3) << 0)
    20  #define PMD_TYPE_FAULT		(_AT(pmdval_t, 0) << 0)
    21  #define PMD_TYPE_TABLE		(_AT(pmdval_t, 1) << 0)
    22  #define PMD_TYPE_SECT		(_AT(pmdval_t, 2) << 0)
    23  #define PMD_PXNTABLE		(_AT(pmdval_t, 1) << 2)     /* v7 */
    24  #define PMD_BIT4		(_AT(pmdval_t, 1) << 4)
    25  #define PMD_DOMAIN(x)		(_AT(pmdval_t, (x)) << 5)
    26  #define PMD_PROTECTION		(_AT(pmdval_t, 1) << 9)		/* v5 */
    ```

    以上便是整个`map_desc`数据结构，其完整地描述了一个内存区间。

- create_mapping

  1. `create_mapping()`函数就是为一个给定的内存区间建立页面映射，其被调用流程为：`start_kernel()->setup_arch()->paging_init()->map_lowmem()->create_mapping()`，具体调用细节，感兴趣的可以在代码中进行跟踪，此处不做详细阐述。

  2. create_mapping()函数调用流程：

     ![1562482144875](../picture/create_mapping函数调用流程.png)

     各函数定义及解析如下：

     ```c
     /* linux-4.14/arch/arm/mm/mmu.c */
     961  static void __init create_mapping(struct map_desc *md)
     962  {
         	/* 检查该内存区间（struct map_desc *md）是否属于用户空间，如果是，则返回，不再继续映射操作 */
     963  	if (md->virtual != vectors_base() && md->virtual < TASK_SIZE) {
     964  		pr_warn("BUG: not creating mapping for 0x%08llx at 0x%08lx in user region\n",
     965  			(long long)__pfn_to_phys((u64)md->pfn), md->virtual);
     966  		return;
     967  	}
     968  
         	/* 检查该内存区间的类型，以及该内存区间是否属于vmalloc（用来分配物理地址非连续空间，240M） */
     969  	if ((md->type == MT_DEVICE || md->type == MT_ROM) &&
     970  	    md->virtual >= PAGE_OFFSET && md->virtual < FIXADDR_START &&
     971  	    (md->virtual < VMALLOC_START || md->virtual >= VMALLOC_END)) {
     972  		pr_warn("BUG: mapping for 0x%08llx at 0x%08lx out of vmalloc space\n",
     973  			(long long)__pfn_to_phys((u64)md->pfn), md->virtual);
     974  	}
      975  
          	/* 调用__create_mapping，init_mm为全局变量，用于后续的查找PGD，early_alloc 是一个用于后续内存分配（当pte表项内容为0时，即该虚拟地址没有映射物理地址，需要分配物理内存）的指针函数*/
     976  	__create_mapping(&init_mm, md, early_alloc, false);
     977  }

     911  static void __init __create_mapping(struct mm_struct *mm, struct map_desc *md,
     912  				    void *(*alloc)(unsigned long sz),
     913  				    bool ng)
     914  {
     915  	unsigned long addr, length, end;
     916  	phys_addr_t phys;
     917  	const struct mem_type *type;
     918  	pgd_t *pgd;
     919  
         	/* 通过md->type来获取描述该内存区域属性的mem_type数据结构，然后只需要通过查表的方式获取mem_type数据结构里的具体内容。 */
     920  	type = &mem_types[md->type];
     921  
     922  #ifndef CONFIG_ARM_LPAE
     923  	/*
     924  	 * Catch 36-bit addresses
     925  	 */
     926  	if (md->pfn >= 0x100000) {
     927  		create_36bit_mapping(mm, md, type, ng);
     928  		return;
     929  	}
     930  #endif
     931  
     932  	addr = md->virtual & PAGE_MASK;
     933  	phys = __pfn_to_phys(md->pfn);
     934  	length = PAGE_ALIGN(md->length + (md->virtual & ~PAGE_MASK));
     935  
     936  	if (type->prot_l1 == 0 && ((addr | phys | length) & ~SECTION_MASK)) {
     937  		pr_warn("BUG: map for 0x%08llx at 0x%08lx can not be mapped using pages, ignoring.\n",
     938  			(long long)__pfn_to_phys(md->pfn), addr);
     939  		return;
     940  	}
     941  
         	/* 获取pgd表项 */
     942  	pgd = pgd_offset(mm, addr);
     943  	end = addr + length;
     944  	do {
      		/* 以PGDIR_SIZE为步长获取next值 */
     945  		unsigned long next = pgd_addr_end(addr, end);
     946  		/* 初始化PGD页表项内容和下一级页表PUD */
     947  		alloc_init_pud(pgd, addr, next, phys, type, alloc, ng);
     948  
     949  		phys += next - addr;
     950  		addr = next;
     951  	} while (pgd++, addr != end);
     952  }

     834  static void __init alloc_init_pud(pgd_t *pgd, unsigned long addr,
     835  				  unsigned long end, phys_addr_t phys,
     836  				  const struct mem_type *type,
     837  				  void *(*alloc)(unsigned long sz), bool ng)
     838  {
         	/* arm 平台支持两级页表映射，所以PUD设置成与PGD等同。 pud_offset直接返回pgd*/
     839  	pud_t *pud = pud_offset(pgd, addr);
     840  	unsigned long next;
     841  
     842  	do {
         		/* 两级页表映射中，pud与pgd等同，所以PUD_SIZE=PGDIR_SIZE,通过pud_addr_end函数获取到的next值应该与end值相等，即该do-while循环只循环一次 */
     843  		next = pud_addr_end(addr, end);
         		/*  初始化PUD页表项内容和下一级页表PMD */
     844  		alloc_init_pmd(pud, addr, next, phys, type, alloc, ng);
     845  		phys += next - addr;
     846  	} while (pud++, addr = next, addr != end);
     847  }

     802  static void __init alloc_init_pmd(pud_t *pud, unsigned long addr,
     803  				      unsigned long end, phys_addr_t phys,
     804  				      const struct mem_type *type,
     805  				      void *(*alloc)(unsigned long sz), bool ng)
     806  {
         	/* 与alloc_init_pud类似 */
     807  	pmd_t *pmd = pmd_offset(pud, addr);
     808  	unsigned long next;
     809  
     810  	do {
     811  		/*
     812  		 * With LPAE, we must loop over to map
     813  		 * all the pmds for the given range.
     814  		 */
     815  		next = pmd_addr_end(addr, end);
     816  
     817  		/*
     818  		 * Try a section mapping - addr, next and phys must all be
     819  		 * aligned to a section boundary.
     820  		 */
         		/* if语句做section mapping（段映射）检查，若不是段映射，则执行alloc_init_pte */
     821  		if (type->prot_sect &&
     822  				((addr | next | phys) & ~SECTION_MASK) == 0) {
     823  			__map_init_section(pmd, addr, next, phys, type, ng);
     824  		} else {
     825  			alloc_init_pte(pmd, addr, next,
     826  				       __phys_to_pfn(phys), type, alloc, ng);
     827  		}
     828  
     829  		phys += next - addr;
     830  
     831  	} while (pmd++, addr = next, addr != end);
     832  }

     761  static void __init alloc_init_pte(pmd_t *pmd, unsigned long addr,
     762  				  unsigned long end, unsigned long pfn,
     763  				  const struct mem_type *type,
     764  				  void *(*alloc)(unsigned long sz),
     765  				  bool ng)
     766  {
         	/* 判断相应的PTE页表项是否已经存在，如果不存在，那就新建PTE页表项 */
     767  	pte_t *pte = arm_pte_alloc(pmd, addr, type->prot_l1, alloc);
     768  	do {
         		/* 通过__pgprot() 和 pfn 组成 PTE entry，最后由set_pte_ext完成对硬件页表项的设置 */
     769  		set_pte_ext(pte, pfn_pte(pfn, __pgprot(type->prot_pte)),
     770  			    ng ? PTE_EXT_NG : 0);
     771  		pfn++;
     772  	} while (pte++, addr += PAGE_SIZE, addr != end);
     773  }

     743  static pte_t * __init arm_pte_alloc(pmd_t *pmd, unsigned long addr,
     744  				unsigned long prot,
     745  				void *(*alloc)(unsigned long sz))
     746  {
         	/* *pmd中存放的是pte页表的基地址，pmd_none(*pmd)判断该基地址是否选择，不存在的话，执行if语句，新建pte页表项 */
     747  	if (pmd_none(*pmd)) {
         		/* 此处的alloc函数便是create_mapping函数中调用__create_mapping时所传递的指针函数early_alloc，通过一层一层传递，最后在此处调用。early_alloc函数最终调用memblock_alloc函数，该函数可以向kernel申请一块可用的物理内存，此处已属于kernel内存分配的范畴，不做细讲。 这里分配了两个PTE_HWTABLE_OFF（512），也就是分配了两份页面表项。*/
     748  		pte_t *pte = alloc(PTE_HWTABLE_OFF + PTE_HWTABLE_SIZE);
         		/* 将新建的pte页面表的基地址设置到pmd页表项中,本节后续还要详细介绍 */
     749  		__pmd_populate(pmd, __pa(pte), prot);
     750  	}
     751  	BUG_ON(pmd_bad(*pmd));
         	/* pte_offset_kernel 返回相应的PTE页面表项 */
     752  	return pte_offset_kernel(pmd, addr);
     753  }
     ```

     第942行，通过pgd_offset()函数获取所属页面目录项PGD。内核的页表存放在swapper_pg_dir地址中，可以通过 init_mm 数据结构来获取，init_mm 定义如下：

     ```c
     /* linux-4.14/mm/init-mm.c */
     18  struct mm_struct init_mm = {
     19  	.mm_rb		= RB_ROOT,
     20  	.pgd		= swapper_pg_dir,
     21  	.mm_users	= ATOMIC_INIT(2),
     22  	.mm_count	= ATOMIC_INIT(1),
     23  	.mmap_sem	= __RWSEM_INITIALIZER(init_mm.mmap_sem),
     24  	.page_table_lock =  __SPIN_LOCK_UNLOCKED(init_mm.page_table_lock),
     25  	.mmlist		= LIST_HEAD_INIT(init_mm.mmlist),
     26  	.user_ns	= &init_user_ns,
     27  	INIT_MM_CONTEXT(init_mm)
     28  };
     ```

     内核页表的基地址定义如下：

     ```c
     /* linux-4.14/arch/arm/kernel/head.S */
     37  #define KERNEL_RAM_VADDR	(PAGE_OFFSET + TEXT_OFFSET)
     38  #if (KERNEL_RAM_VADDR & 0xffff) != 0x8000
     39  #error KERNEL_RAM_VADDR must start at 0xXXXX8000
     40  #endif
     41  
     42  #ifdef CONFIG_ARM_LPAE
     43  	/* LPAE requires an additional page for the PGD */
     44  #define PG_DIR_SIZE	0x5000
     45  #define PMD_ORDER	3
     46  #else
     47  #define PG_DIR_SIZE	0x4000
     48  #define PMD_ORDER	2
     49  #endif
     50  
     51  	.globl	swapper_pg_dir
     52  	.equ	swapper_pg_dir, KERNEL_RAM_VADDR - PG_DIR_SIZE

     /* linux-4.14/arch/arm/Makefile */
     143 textofs-y	:= 0x00008000
     250 TEXT_OFFSET := $(textofs-y)
     ```

     pgd_offset()宏可以从 init_mm 数据结构所指定的页面目录中找到地址addr所属的页面目录项指针 pgd。 首先 通过 init_mm 结构体得到页表的基地址，然后通过 addr 右移 PGDIR_SHIFT 得到 pgd 的索引值，最后在一级页表中找到相应的页表项 pgd 指针。PGD的定义如下：

     ```c
     typedef struct { pmdval_t pgd[2]; } pgd_t;
     #define pgd_index(addr)		((addr) >> PGDIR_SHIFT)
     #define pgd_offset(mm, addr)	((mm)->pgd + pgd_index(addr))
     ```

     第748行，因为Linux内核默认的PGD是从21位开始的，也就是 bit[31:21]，一共2048个一级页表项。而ARM32硬件结构中，PGD是从20位开始，页表数目是4096，比Linux内核的要多一倍。

     第749行 __pmd_populate()函数实现如下：

     ```c
     /* linux-4.14/arch/arm/include/asm/pgalloc.h */
     131  static inline void __pmd_populate(pmd_t *pmdp, phys_addr_t pte,
     132  				  pmdval_t prot)
     133  {
         	/* 这里把刚分配的1024个PTE页面表中的第512个页表项的地址作为基地址，再加上一些标志位信息 prot 作为页表项内容，写入上一级的 PMD 中。 */
     134  	pmdval_t pmdval = (pte + PTE_HWTABLE_OFF) | prot;
         	/* 相邻的两个二级页表的基地址分别写入PMD的页表项中的pmdp[0]和pmdp[1]指针中。 */
     135  	pmdp[0] = __pmd(pmdval);
     136  #ifndef CONFIG_ARM_LPAE
     137  	pmdp[1] = __pmd(pmdval + 256 * sizeof(pte_t));
     138  #endif
     139  	flush_pmd_entry(pmdp);
     140  }
     ```

     由pgd定义可知，pgd其实是pmdval_t pgd[2]，长度是两倍，也就是pgd包括两份相邻的PTE页表，所以pgd_offset在查找pgd表项时，是按照 pgd[2] 长度来进行计算的，因此查找相应的 pgd 表项时，其中 pgd[0] 指向第一份 PTE 页表，pgd[1] 指向第二份 PTE 页表。

     后续第3部分，回答“ARM32架构中一级页表PGD的偏移量 PGDIR_SHIFT设置为21”，以及“PGD 页表项为什么是两倍长度”的问题。



  3. ARM硬件页表映射过程如下图：                                  ![1562496066677](../picture/arm硬件页表映射过程.png)

     页表中每一项称为一个entry（也就是我们之前所说的表项），entry存放的是物理地址值，PGD entry值指向2级页表（PTE页表），PTE entry值指向物理页。

     由于以下两个原因，linux代码对上图的映射过程做了一些调整：

     > 1. PTE entry中的一些低bit位被硬件使用了，没有linux需要的“accessed”、“dirty”等标志位。参考内核代码注释： Hardware-wise, we have a two level page table structure, where the first level has 4096 entries, and the second level has 256 entries.  Each entry is one 32-bit word.  Most of the bits in the second level entry are used by hardware, and there aren't any "accessed" and "dirty" bits。
     >
     >    ![1562496586266](../picture/arm pte entry标记位.png)
     >
     > 2. linux 希望PTE页表本身也是一个页表大小。参考内核代码注释：However, Linux also expects one "PTE" table per page, and at least a "dirty" bit.，但本章1.2页面映射章节中的PTE页表只有256*4 Byte=1k大小。

     所以，针对以上两个问题，linux做了一些处理，使内核中实现的页表能够满足硬件要求，最终的arm页表如下图：                                           ![1562502291076](../picture/linux页表与硬件页表.png)

     如上表，解释如下：

     > 1. 软件实现必须符合硬件要求，ARM要求4096个PGD entry，256个PTE entry。解决：PGD每个entry为8 bytes，定义为pmdval_t pgd[2]，故共2048*2=4096 PGD entry。ARM MMU用va的bit[31,20]（本章1.2页面映射章节）在PGD 4096项中找到对应的entry，每个entry指向一个hw页表（上图）。每一个hw页表有256个entry，ARM MMU用va的bit[19,12]在hw页表中找到对应的entry。所以从硬件角度看，linux实现的arm页表，完全符合硬件要求。
     > 2. Linux需要 "accessed" and "dirty"位。解决：从图（arm pte entry标记位.png)中可以看出，PTE entry的低位已经被硬件占用，所以只能再复制出一份页表（称为linux页表或linux pt），上图的hw pt 0对应Linux pt 0，linux页表的低bit位被linux系统用来提供需要的 "accessed" and "dirty"位。hw pt由MMU使用，linux pt由操作系统使用。
     >
     > 3. Linux期望PTE页表占用1个page。解决：ARM的hw pt为256\*4 bytes=1k，不满一个page大小。内核代码在实现上采用了一个小技巧，让一个PGD entry映射2个连续的hw pt，同时将对应的2个linux pt也组织在一起，共1k*4=4k。

     因为linux代码让PGD一次映射2个hw pt，所以软件需要做一些处理来实现这个目的。软件定义PGD表项为pmdval_t pgd[2]，pgd[i]指向一个hw pt，所以PGD表项一共有4096/2=2048项，也就是说需要用bit[31,21]来寻址这2048项，所以pgtable-2level.h中定义了：#define PGDIR_SHIFT 21 (注意，本章1.2页面映射章节图中PGD偏移20bit，那是给硬件MMU用的，跟我们这里的软件偏移没有关系)。



## 2. ARM64 页表映射

- 理解了ARM32页表映射过程，对于ARM64页表映射过程的理解也就相对容易些了。

- 目前基于ARMv8-A架构的处理器最大可支持到48根地址线，也就是寻址2^48的虚拟地址空间。即虚拟地址空间范围为 0x0000 0000 0000 0000 ~ 0x0000 FFFF FFFF FFFF，共 256 TB。

- 基于 ARMv8-A架构的处理器可以通过配置 CONFIG_ARM64_VA_BITS 这个宏来设置虚拟地址的宽度。

  ```c
  /* linux-4.14/arch/arm64/Kconfig */
  621 config ARM64_VA_BITS
  622 	int
  623 	default 36 if ARM64_VA_BITS_36
  624 	default 39 if ARM64_VA_BITS_39
  625 	default 42 if ARM64_VA_BITS_42
  626 	default 47 if ARM64_VA_BITS_47
  627 	default 48 if ARM64_VA_BITS_48
  ```

- 另外基于ARMv8-A架构的处理器支持的最大物理地址宽度也是48位。

- Linux 内存空间布局与地址映射的粒度和地址映射的层级有关。基于ARMv8-A架构的处理器支持的页面大小可以是 4KB、16KB或者64KB。映射的层级可以是3级或者4级。

- 下面是页面大小为4KB，地址宽度为48位，4级映射的内存分布图：![1562510828595](../picture/arm64-4kb页面大小-48位地址宽度-4级映射-内存分布图.png)

  页面大小为4KB，地址宽度为48位，3级映射的内存分布图如下：![1562510989316](../picture/arm64-4kb页面大小-48位地址宽度-3级映射-内存分布图.png)

  Linux 内核的 documentation/arm64/memory.txt 文件中还有其他不同配置的内存分布图。

- 后续我们以页面大小为4KB，地址宽度为48位，4级映射的配置为基础介绍ARM64的地址映射过程。

### 2.1 ARM64虚拟地址转换

![1562511283560](../picture/基于ARMv8-A架构的处理器虚拟地址查找(4KB页).png)

> 1. 如果输入的虚拟地址最高位 bit[63]为 1，那么这个地址是用于内核空间的，页表的基地址寄存器用 TTBR1_EL1（Translation Table Base Register 1）。如果 bit[63]为 0，那么这个地址是用于用户空间的，页表的基地址寄存器用 TTBR0。
> 2. TTBRx 寄存器保存了第 0 级页表的基地址 （L0 Table base address，Linux内核中称为PGD），L0 页表中有512个表项 （Table Descriptor），以虚拟地址的 bit[47:39]作为索引值在L0页表中查找相应的表项。每个表项的内容含有下一级页表的基地址，即L1页表（Linux内核中称为PUD）的基地址。
> 3. PUD 页表中有512个表项，以虚拟地址的 bit[38:30]为索引值在PUD表中查找相应的表项，每个表项的内容含有下一级页表的基地址，即L2页表（Linux内核中称为PMD）的基地址。
> 4. PMD页表中有512个表项，以虚拟地址的 bit[29:21]为索引值在PMD表中查找相应的表项，每个表项的内容含有下一级页表的基地址，即L3页表（Linux内核中称为PTE）的基地址。
> 5. 在PTE页表中，以虚拟地址的 bit[20:12]为索引值在PTE表中查找相应的表项，每个PTE表项中含有最终物理地址的bit[47:12]，和虚拟地址中的[11:0] 合并成最终的物理地址，完成地址翻译过程。

该过程与 《Linux 内核分析(五)——页表》章节中介绍页表结构内容相似。



### 2.2 页面映射的函数实现

在内核初始化阶段会对内核空间的页表进行一一映射，实现的函数从\__create_pgd_mapping()开始，前面调用关系是：`start_kernel()->setup_arch()->paging_init()->map_mem()->__map_memblock()-> __create_pgd_mapping()`，具体调用细节，感兴趣的可以在代码中进行跟踪，此处不做详细阐述。

虚拟地址的一些前期检查在 map_mem() 函数中实现，此处不再详述。

- __create_pgd_mapping

```c
/* linux-4.14/arch/arm64/mm/mmu.c */
315  static void __create_pgd_mapping(pgd_t *pgdir, phys_addr_t phys,
316  				 unsigned long virt, phys_addr_t size,
317  				 pgprot_t prot,
318  				 phys_addr_t (*pgtable_alloc)(void),
319  				 int flags)
320  {
321  	unsigned long addr, length, end, next;
    	/* 通过pgd_offset_raw 函数获取pgd页面目录表项 */
322  	pgd_t *pgd = pgd_offset_raw(pgdir, virt);
323  
324  	/*
325  	 * If the virtual and physical address don't have the same offset
326  	 * within a page, we cannot map the region as the caller expects.
327  	 */
328  	if (WARN_ON((phys ^ virt) & ~PAGE_MASK))
329  		return;
330  
331  	phys &= PAGE_MASK;
332  	addr = virt & PAGE_MASK;
333  	length = PAGE_ALIGN(size + (virt & ~PAGE_MASK));
334  
335  	end = addr + length;
    	/* 以PGDIR_SIZE为步长遍历内存区域[addr, end],然后调用alloc_init_pud（）来初始化PGD页表项内容和下一级页表PUD。pgd_addr_end以PGDIR_SIZE为步长。 */
336  	do {
337  		next = pgd_addr_end(addr, end);
338  		alloc_init_pud(pgd, addr, next, phys, prot, pgtable_alloc,
339  			       flags);
340  		phys += next - addr;
341  	} while (pgd++, addr = next, addr != end);
342  }
```

第322行，ARM64 PGD 的表项通过 pgd_offset_raw() 宏来获取，其定义：

```c
/* linux-4.14/arch/arm64/include/asm/pgtable.h */
557  /* to find an entry in a page-table-directory */
558  #define pgd_index(addr)	(((addr) >> PGDIR_SHIFT) & (PTRS_PER_PGD - 1))
559  
560  #define pgd_offset_raw(pgd, addr)	((pgd) + pgd_index(addr))
```

相关宏定义如下：

```c
[linux-4.14/arch/arm64/include/asm/pgtable-hwdef.h]

35  #define ARM64_HW_PGTABLE_LEVELS(va_bits) (((va_bits) - 4) / (PAGE_SHIFT - 3))
50  #define ARM64_HW_PGTABLE_LEVEL_SHIFT(n)	((PAGE_SHIFT - 3) * (4 - (n)) + 3)
51  
52  #define PTRS_PER_PTE		(1 << (PAGE_SHIFT - 3))
53  
54  /*
55   * PMD_SHIFT determines the size a level 2 page table entry can map.
56   */
57  #if CONFIG_PGTABLE_LEVELS > 2
58  #define PMD_SHIFT		ARM64_HW_PGTABLE_LEVEL_SHIFT(2)
59  #define PMD_SIZE		(_AC(1, UL) << PMD_SHIFT)
60  #define PMD_MASK		(~(PMD_SIZE-1))
61  #define PTRS_PER_PMD		PTRS_PER_PTE
62  #endif
63  
64  /*
65   * PUD_SHIFT determines the size a level 1 page table entry can map.
66   */
67  #if CONFIG_PGTABLE_LEVELS > 3
68  #define PUD_SHIFT		ARM64_HW_PGTABLE_LEVEL_SHIFT(1)
69  #define PUD_SIZE		(_AC(1, UL) << PUD_SHIFT)
70  #define PUD_MASK		(~(PUD_SIZE-1))
71  #define PTRS_PER_PUD		PTRS_PER_PTE
72  #endif
73  
74  /*
75   * PGDIR_SHIFT determines the size a top-level page table entry can map
76   * (depending on the configuration, this level can be 0, 1 or 2).
77   */
78  #define PGDIR_SHIFT		ARM64_HW_PGTABLE_LEVEL_SHIFT(4 - CONFIG_PGTABLE_LEVELS)
79  #define PGDIR_SIZE		(_AC(1, UL) << PGDIR_SHIFT)
80  #define PGDIR_MASK		(~(PGDIR_SIZE-1))
81  #define PTRS_PER_PGD		(1 << (VA_BITS - PGDIR_SHIFT))
```

PAGE_SHIFT 根据页的大小来定的，如4K（2^12）大小的页，其PAGE_SHIFT 为12，va_bits 为48，ARM64_HW_PGTABLE_LEVELS 为映射页表的级数，通过以上计算，该值为4，即4级页表，那么通过计算可以得到 PGDIR_SHIFT = 39，PUD_SHIFT = 30，PMD_SHIFT = 21。每级页表的页表项数目分别用PTRS_PER_PGD、PTRS_PER_PUD、PTRS_PER_PMD 和 PTRS_PER_PTE 来表示，都等于 512。PGDIR_SIZE 宏表示一个PGD页表项能覆盖的内存范围大小为512GB。PUD_SIZE 等于 1GB，PMD_SIZE 等于 2MB， PAGE_SIZE等于 4KB。



继续分析 __create_pgd_mapping() 函数第322行，调用pgd_offset_raw 的参数 pgdir 是从 paging_init() 函数中传递下来的，如下：

```c
/* linux-4.14/arch/arm64/mm/mmu.c */
622  void __init paging_init(void)
623  {
624  	phys_addr_t pgd_phys = early_pgtable_alloc();
625  	pgd_t *pgd = pgd_set_fixmap(pgd_phys);
626  
627  	map_kernel(pgd);
628  	map_mem(pgd);
    	...
	 }
```



- alloc_init_pud

```c
[linux-4.14/arch/arm64/mm/mmu.c]

267  static void alloc_init_pud(pgd_t *pgd, unsigned long addr, unsigned long end,
268  				  phys_addr_t phys, pgprot_t prot,
269  				  phys_addr_t (*pgtable_alloc)(void),
270  				  int flags)
271  {
272  	pud_t *pud;
273  	unsigned long next;
274  
275  	if (pgd_none(*pgd)) {
276  		phys_addr_t pud_phys;
277  		BUG_ON(!pgtable_alloc);
278  		pud_phys = pgtable_alloc();
279  		__pgd_populate(pgd, pud_phys, PUD_TYPE_TABLE);
280  	}
281  	BUG_ON(pgd_bad(*pgd));
282  
283  	pud = pud_set_fixmap_offset(pgd, addr);
284  	do {
285  		pud_t old_pud = *pud;
286  
287  		next = pud_addr_end(addr, end);
288  
289  		/*
290  		 * For 4K granule only, attempt to put down a 1GB block
291  		 */
292  		if (use_1G_block(addr, next, phys) &&
293  		    (flags & NO_BLOCK_MAPPINGS) == 0) {
294  			pud_set_huge(pud, phys, prot);
295  
296  			/*
297  			 * After the PUD entry has been populated once, we
298  			 * only allow updates to the permission attributes.
299  			 */
300  			BUG_ON(!pgattr_change_is_safe(pud_val(old_pud),
301  						      pud_val(*pud)));
302  		} else {
303  			alloc_init_cont_pmd(pud, addr, next, phys, prot,
304  					    pgtable_alloc, flags);
305  
306  			BUG_ON(pud_val(old_pud) != 0 &&
307  			       pud_val(old_pud) != pud_val(*pud));
308  		}
309  		phys += next - addr;
310  	} while (pud++, addr = next, addr != end);
311  
312  	pud_clear_fixmap();
313  }
```

> 1. 通过 pgd_none() 判断当前 PGD 表项内容是否为空。如果 PGD 表项内容为空，说明下一级页表为空，那么需要动态分配下一级页表。下一级页表 PUD 一共有 PTRS_PER_PUD 个页表项，即 512 个表项，然后通过 __pgd_populate() 把刚分配的 PUD 页表设置到相应的PGD 页表项中。
> 2. 通过 pud_set_fixmap_offset() 来获取相应的 PUD 表项。最终使用虚拟地址的 bit[38~30]位来做索引值。
> 3. 接下来以 PUD_SIZE （即 1 << 30, 1GB）为步长，通过while循环来设置下一级页表。
> 4. use_1G_block() 函数会判断是否使用 1GB 大小的 block 来映射，当这里要映射的内存块大小正好是 PUD_SIZE ，那么只需要映射到 PUD 就好了，接下来的 PMD 和 PTE 页表等到真正需要使用时再映射，通过 pud_set_huge() 函数来设置相应的 PUD 表项。
> 5. 如果 use_1G_block() 函数判断不能通过 1GB 大小来映射，那么就需要调用 alloc_init_cont_pmd() 函数来进行下一级页表的映射。



- alloc_init_cont_pmd

```c
[linux-4.14/arch/arm64/mm/mmu.c]

220  static void alloc_init_cont_pmd(pud_t *pud, unsigned long addr,
221  				unsigned long end, phys_addr_t phys,
222  				pgprot_t prot,
223  				phys_addr_t (*pgtable_alloc)(void), int flags)
224  {
225  	unsigned long next;
226  
227  	/*
228  	 * Check for initial section mappings in the pgd/pud.
229  	 */
230  	BUG_ON(pud_sect(*pud));
231  	if (pud_none(*pud)) {
232  		phys_addr_t pmd_phys;
233  		BUG_ON(!pgtable_alloc);
234  		pmd_phys = pgtable_alloc();
235  		__pud_populate(pud, pmd_phys, PUD_TYPE_TABLE);
236  	}
237  	BUG_ON(pud_bad(*pud));
238  
239  	do {
240  		pgprot_t __prot = prot;
241  
242  		next = pmd_cont_addr_end(addr, end);
243  
244  		/* use a contiguous mapping if the range is suitably aligned */
245  		if ((((addr | next | phys) & ~CONT_PMD_MASK) == 0) &&
246  		    (flags & NO_CONT_MAPPINGS) == 0)
247  			__prot = __pgprot(pgprot_val(prot) | PTE_CONT);
248  
249  		init_pmd(pud, addr, next, phys, __prot, pgtable_alloc, flags);
250  
251  		phys += next - addr;
252  	} while (addr = next, addr != end);
253  }

183  static void init_pmd(pud_t *pud, unsigned long addr, unsigned long end,
184  		     phys_addr_t phys, pgprot_t prot,
185  		     phys_addr_t (*pgtable_alloc)(void), int flags)
186  {
187  	unsigned long next;
188  	pmd_t *pmd;
189  
190  	pmd = pmd_set_fixmap_offset(pud, addr);
191  	do {
192  		pmd_t old_pmd = *pmd;
193  
194  		next = pmd_addr_end(addr, end);
195  
196  		/* try section mapping first */
197  		if (((addr | next | phys) & ~SECTION_MASK) == 0 &&
198  		    (flags & NO_BLOCK_MAPPINGS) == 0) {
199  			pmd_set_huge(pmd, phys, prot);
200  
201  			/*
202  			 * After the PMD entry has been populated once, we
203  			 * only allow updates to the permission attributes.
204  			 */
205  			BUG_ON(!pgattr_change_is_safe(pmd_val(old_pmd),
206  						      pmd_val(*pmd)));
207  		} else {
208  			alloc_init_cont_pte(pmd, addr, next, phys, prot,
209  					    pgtable_alloc, flags);
210  
211  			BUG_ON(pmd_val(old_pmd) != 0 &&
212  			       pmd_val(old_pmd) != pmd_val(*pmd));
213  		}
214  		phys += next - addr;
215  	} while (pmd++, addr = next, addr != end);
216  
217  	pmd_clear_fixmap();
218  }
```

alloc_init_cont_pmd() 函数用于配置 PMD 页表：

> 1. 首先通过 pud_none() 判断当前 PUD 表项内容是否为空。如果 PUD 表项内容为空，说明下一级页表为空，那么需要动态分配下一级页表。下一级页表 PMD 一共有 PTRS_PER_PMD 个页表项，即 512 个表项，然后通过 __pud_populate() 把刚分配的 PMD 页表设置到相应的PUD 页表项中。
> 2. 调用 init_pmd() 函数，在  init_pmd() 函数中， 通过 pmd_set_fixmap_offset() 来获取相应的 PMD 表项。最终使用虚拟地址的 bit[29~21]位来做索引值。
> 3. 接下来以 PMD_SIZE （即 1 << 21,  2MB）为步长，通过while循环来设置下一级页表。
> 4. 如果虚拟区间的开始地址addr和结束地址next，以及物理地址 phys 都与 SECTION_SIZE (2MB) 大小对齐，那么直接设置PMD页表项，不需要映射下一级页表。下一级页表等到需要用时再映射也来得及，所以这里直接通过 pmd_set_huge() 设置 PMD 页表项。
> 5. 如果映射的内存不是和 SECTION_SIZE  对齐的，那么需要通过 alloc_init_cont_pte() 函数来映射下一级 PTE 页表。



- alloc_init_cont_pte

```c
[linux-4.14/arch/arm64/mm/mmu.c]

150  static void alloc_init_cont_pte(pmd_t *pmd, unsigned long addr,
151  				unsigned long end, phys_addr_t phys,
152  				pgprot_t prot,
153  				phys_addr_t (*pgtable_alloc)(void),
154  				int flags)
155  {
156  	unsigned long next;
157  
158  	BUG_ON(pmd_sect(*pmd));
159  	if (pmd_none(*pmd)) {
160  		phys_addr_t pte_phys;
161  		BUG_ON(!pgtable_alloc);
162  		pte_phys = pgtable_alloc();
163  		__pmd_populate(pmd, pte_phys, PMD_TYPE_TABLE);
164  	}
165  	BUG_ON(pmd_bad(*pmd));
166  
167  	do {
168  		pgprot_t __prot = prot;
169  
170  		next = pte_cont_addr_end(addr, end);
171  
172  		/* use a contiguous mapping if the range is suitably aligned */
173  		if ((((addr | next | phys) & ~CONT_PTE_MASK) == 0) &&
174  		    (flags & NO_CONT_MAPPINGS) == 0)
175  			__prot = __pgprot(pgprot_val(prot) | PTE_CONT);
176  
177  		init_pte(pmd, addr, next, phys, __prot);
178  
179  		phys += next - addr;
180  	} while (addr = next, addr != end);
181  }

127  static void init_pte(pmd_t *pmd, unsigned long addr, unsigned long end,
128  		     phys_addr_t phys, pgprot_t prot)
129  {
130  	pte_t *pte;
131  
132  	pte = pte_set_fixmap_offset(pmd, addr);
133  	do {
134  		pte_t old_pte = *pte;
135  
136  		set_pte(pte, pfn_pte(__phys_to_pfn(phys), prot));
137  
138  		/*
139  		 * After the PTE entry has been populated once, we
140  		 * only allow updates to the permission attributes.
141  		 */
142  		BUG_ON(!pgattr_change_is_safe(pte_val(old_pte), pte_val(*pte)));
143  
144  		phys += PAGE_SIZE;
145  	} while (pte++, addr += PAGE_SIZE, addr != end);
146  
147  	pte_clear_fixmap();
148  }
```

PTE 页表是 4 级页表的最后一级， alloc_init_cont_pte() 配置 PTE 页表项。

> 1. 首先通过 pmd_none() 判断当前 PMD 表项内容是否为空。如果 PMD 表项内容为空，说明下一级页表为空，那么需要动态分配 PTRS_PER_PTE 个页表项，即 512 个表项，然后通过 __pmd_populate() 把刚分配的 PTE 页表设置到相应的PMD 页表项中。
> 2. 调用 init_pte() 函数，在  init_pte() 函数中， 通过 pte_set_fixmap_offset() 来获取相应的 PTE 表项。最终使用虚拟地址的 bit[20~12]位来做索引值。
> 3. 接下来以 PAG_SIZE （即 1 << 12,  4kB）为步长，通过while循环来设置PTE页表项。
