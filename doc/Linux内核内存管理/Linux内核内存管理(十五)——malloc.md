# Linux内核内存管理(十四)——`malloc`

- `malloc()`函数是C语言中内存分配函数，同样也是C函数库封装的一个核心函数，C函数库会做一些处理后调用 Linux 内核系统去调用 brk，所以大家并不太熟悉 brk 的系统调用，原因在于很少有人会直接使用系统调用 brk 向系统申请内存，而总是通过`malloc()`之类的C函数库的API函数，如果把`malloc()`想象成零售，那么 brk 就是代理商，`malloc()`函数的实现为用户进程维护一个本地小仓库，当进程需要使用更多的内存时就向这个小仓库要货，小仓库存量不足时就通过代理商 brk 向内核批发。

## 1. brk 实现

- brk 系统调用主要实现在 [kernel4.14/mm/mmap.c](http://10.0.1.79:8081/xref/sprdroidq_trunk/bsp/kernel/kernel4.14/mm/mmap.c#183) 函数中：

  ```c
  SYSCALL_DEFINE1(brk, unsigned long, brk)
  {
  	unsigned long retval;
  	unsigned long newbrk, oldbrk;
  	struct mm_struct *mm = current->mm;
  	struct vm_area_struct *next;
  	unsigned long min_brk;
  	bool populate;
  	LIST_HEAD(uf);
  
  	if (down_write_killable(&mm->mmap_sem))
  		return -EINTR;
  
  #ifdef CONFIG_COMPAT_BRK
  	/*
  	 * CONFIG_COMPAT_BRK can still be overridden by setting
  	 * randomize_va_space to 2, which will still cause mm->start_brk
  	 * to be arbitrarily shifted
  	 */
  	if (current->brk_randomized)
  		min_brk = mm->start_brk;
  	else
  		min_brk = mm->end_data;
  #else
  	min_brk = mm->start_brk;
  #endif
  	if (brk < min_brk)
  		goto out;
  
  	/*
  	 * Check against rlimit here. If this check is done later after the test
  	 * of oldbrk with newbrk then it can escape the test and let the data
  	 * segment grow beyond its set limit the in case where the limit is
  	 * not page aligned -Ram Gupta
  	 */
  	if (check_data_rlimit(rlimit(RLIMIT_DATA), brk, mm->start_brk,
  			      mm->end_data, mm->start_data))
  		goto out;
  
  	newbrk = PAGE_ALIGN(brk);
  	oldbrk = PAGE_ALIGN(mm->brk);
  	if (oldbrk == newbrk)
  		goto set_brk;
  
  	/* Always allow shrinking brk. */
  	if (brk <= mm->brk) {
  		if (!do_munmap(mm, newbrk, oldbrk-newbrk, &uf))
  			goto set_brk;
  		goto out;
  	}
  
  	/* Check against existing mmap mappings. */
  	next = find_vma(mm, oldbrk);
  	if (next && newbrk + PAGE_SIZE > vm_start_gap(next))
  		goto out;
  
  	/* Ok, looks good - let it rip. */
  	if (do_brk_flags(oldbrk, newbrk-oldbrk, 0, &uf) < 0)
  		goto out;
  
  set_brk:
  	mm->brk = brk;
  	populate = newbrk > oldbrk && (mm->def_flags & VM_LOCKED) != 0;
  	up_write(&mm->mmap_sem);
  	userfaultfd_unmap_complete(mm, &uf);
  	if (populate)
  		mm_populate(oldbrk, newbrk - oldbrk);
  	return brk;
  
  out:
  	retval = mm->brk;
  	up_write(&mm->mmap_sem);
  	return retval;
  }
  
  ```

- 在32位 Linux 内核中，每个用户进程拥有 3GB 的虚拟空间，内核如何为用户空间来划分这 3GB 的虚拟空间呢？ 用户进程的可执行文件由代码段和数据段组成，数据段包括所有的静态分配的数据空间，例如全局变量和静态局部变量等。这些空间在可执行文件装载时，内核就为其分配好这些空间，包括虚拟地址和物理页面，并建立好二者的映射关系。如下图所示，用户进程的用户栈从 3GB 虚拟空间的顶部开始，由顶向下延伸，而 brk 分配的空间是从数据段的顶部 end_data 到用户栈的底部。所以动态分配空间是从进程的 end_data 开始，每次分配一块空间，就把这个边界往上推进一段，同时内核和进程都会记录当前的边界的位置。             ![1573389348441](/home/haibin.xu/haibin/doc/picture/图15.1-用户进程内存空间布局.png)

- 