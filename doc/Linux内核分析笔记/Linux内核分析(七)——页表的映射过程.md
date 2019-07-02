# Linux内核分析(七)——页表的映射过程

![1562079955761](../picture/arm32处理器查询页表.png)

 

- 32位虚拟地址的高 12 位（bit[31 : 20]）作为访问一级页表的索引值，找到相应的表项，每个表项指向一个二级页表的起始地址。以虚拟地址的次 8 位（bit[19 : 12]）作为访问二级页表的索引值，得到相应的页表项，从这个页表项中找到20位的物理页面地址。最后将这20位物理页面地址和虚拟地址的低 12 位拼凑在一起，得到最终的  32 位物理地址。这个过程在ARM32架构中由MMU应将完成，软件不需要介入。

- 相关宏设置

  ```c
  /* linux-4.14/arch/arm/include/asm/pgtable-2level.h */
  
  81  /*
  82   * PMD_SHIFT determines the size of the area a second-level page table can map
  83   * PGDIR_SHIFT determines what a third-level page table entry can map
  84   */
  85  #define PMD_SHIFT		21
  86  #define PGDIR_SHIFT		21
  87  
  88  #define PMD_SIZE		(1UL << PMD_SHIFT)
  89  #define PMD_MASK		(~(PMD_SIZE-1))
  90  #define PGDIR_SIZE		(1UL << PGDIR_SHIFT)
  91  #define PGDIR_MASK		(~(PGDIR_SIZE-1))
  ```

  