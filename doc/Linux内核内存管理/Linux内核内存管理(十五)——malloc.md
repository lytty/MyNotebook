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

- `brk(): CONFIG_COMPAT_BRK`, 内核中 `brk` 相关的变量很多指的都是堆（heap），这个配置选项 =y 指的是关闭堆地址空间随机化技术来支持一些老的`binary`（`COMPAT`选项一般都是向后兼容的选项）。 展锐的各项目中，该变量一般不配置。所以如下代码段，最终执行`min_brk = mm->start_brk`，如果 brk 请求的边界小于这个地址，那么请求无效。

  ```c
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
   
  ```

- 从`check_data_rlimit`继续分析：

  ```c
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
  
  ```

  `kernel4.14/include/linux/mm.h`：

  ```c
  static inline int check_data_rlimit(unsigned long rlim,
  				    unsigned long new,
  				    unsigned long start,
  				    unsigned long end_data,
  				    unsigned long start_data)
  {
  	if (rlim < RLIM_INFINITY) {
  		if (((new - start) + (end_data - start_data)) > rlim)
  			return -ENOSPC;
  	}
  
  	return 0;
  }
  
  ```

  - `check_data_rlimit()`: 如果`RLIMIT_DATA`不是`RLIM_INFINITY`，需要保证数据段加上 brk 区域不超过 `RLIMIT_DATA`, `RLIMIT_DATA`表示数据段的最大值，`RLIM_INFINITY`在32位系统，该值为`0x7fffffff`，该函数的作用其实就是检查用户进程要求分配的内存大小（`new - start`）加上 data 数据段大小后是否超过限制`RLIM_INFINITY`，超过的话，返回错误码`ENOSPC`。
  - `mm->brk`记录动态分配区的当前底端，参数 brk 表示所要求的新边界，是用户进程要求分配内存的大小与其当前动态分配区底部边界相加。
  - 如果新边界小于老边界，那么表示释放空间，调用`do_munmap()`来释放这一部分的内存。`do_munmap()`函数内部主要是一些`vma`相关操作，可具体解析请查阅第十四章节中对`vma`操作的详细叙述。
  
- 从`find_vma`继续分析：

  ```c
  	/* Check against existing mmap mappings. */
  	next = find_vma(mm, oldbrk);
  	if (next && newbrk + PAGE_SIZE > vm_start_gap(next))
  		goto out;
  
  ```

  - `find_vma()`函数以老边界 oldbrk 地址来查找当前用户进程中是否已经有一块 VMA 和 start_addr地址重叠。如果`find_vma()`函数找到一块包含start_addr 的VMA，说明老边界开始的地址空间已经在使用了，就不需要再寻找了。

- 核心函数**do_brk_flags**

  ```c
  	/* Ok, looks good - let it rip. */
  	if (do_brk_flags(oldbrk, newbrk-oldbrk, 0, &uf) < 0)
  		goto out;
  
  ```

  - **do_brk_flags**定义如下： http://10.0.1.79:8081/xref/sprdroidq_trunk/bsp/kernel/kernel4.14/mm/mmap.c#2904

  ```c
  /*
   *  this is really a simplified "do_mmap".  it only handles
   *  anonymous maps.  eventually we may be able to do some
   *  brk-specific accounting here.
   */
  static int do_brk_flags(unsigned long addr, unsigned long len, unsigned long flags, struct list_head *uf)
  {
  	struct mm_struct *mm = current->mm;
  	struct vm_area_struct *vma, *prev;
  	struct rb_node **rb_link, *rb_parent;
  	pgoff_t pgoff = addr >> PAGE_SHIFT;
  	int error;
  
  	/* Until we need other flags, refuse anything except VM_EXEC. */
  	if ((flags & (~VM_EXEC)) != 0)
  		return -EINVAL;
  	flags |= VM_DATA_DEFAULT_FLAGS | VM_ACCOUNT | mm->def_flags;
  
      /* get_unmapped_area()函数用来判断虚拟内存空间是否有足够的空间，返回一段没有映射过的空间的起始地址，flag参数是MAP_FIXED，表示使用指定的虚拟地址对应的空间 */
  	error = get_unmapped_area(NULL, addr, len, 0, MAP_FIXED);
  	if (offset_in_page(error))
  		return error;
  
  	error = mlock_future_check(mm, mm->def_flags, len);
  	if (error)
  		return error;
  
  	/*
  	 * mm->mmap_sem is required to protect against another thread
  	 * changing the mappings in case we sleep.
  	 */
  	verify_mm_writelocked(mm);
  
  	/*
  	 * Clear old maps.  this also does some error checking for us
  	 */
  	while (find_vma_links(mm, addr, addr + len, &prev, &rb_link,
  			      &rb_parent)) {
  		if (do_munmap(mm, addr, len, uf))
  			return -ENOMEM;
  	}
  
  	/* Check against address space limits *after* clearing old maps... */
  	if (!may_expand_vm(mm, flags, len >> PAGE_SHIFT))
  		return -ENOMEM;
  
  	if (mm->map_count > sysctl_max_map_count)
  		return -ENOMEM;
  
  	if (security_vm_enough_memory_mm(mm, len >> PAGE_SHIFT))
  		return -ENOMEM;
  
  	/* Can we just expand an old private anonymous mapping? */
  	vma = vma_merge(mm, prev, addr, addr + len, flags,
  			NULL, NULL, pgoff, NULL, NULL_VM_UFFD_CTX, NULL);
  	if (vma)
  		goto out;
  
  	/*
  	 * create a vma struct for an anonymous mapping
  	 */
  	vma = kmem_cache_zalloc(vm_area_cachep, GFP_KERNEL);
  	if (!vma) {
  		vm_unacct_memory(len >> PAGE_SHIFT);
  		return -ENOMEM;
  	}
  
  	INIT_LIST_HEAD(&vma->anon_vma_chain);
  	vma->vm_mm = mm;
  	vma->vm_start = addr;
  	vma->vm_end = addr + len;
  	vma->vm_pgoff = pgoff;
  	vma->vm_flags = flags;
  	vma->vm_page_prot = vm_get_page_prot(flags);
  	vma_link(mm, vma, prev, rb_link, rb_parent);
  out:
  	perf_event_mmap(vma);
  	mm->total_vm += len >> PAGE_SHIFT;
  	mm->data_vm += len >> PAGE_SHIFT;
  	if (flags & VM_LOCKED)
  		mm->locked_vm += (len >> PAGE_SHIFT);
  	vma->vm_flags |= VM_SOFTDIRTY;
  	return 0;
  }
  
unsigned long
  get_unmapped_area(struct file *file, unsigned long addr, unsigned long len,
  		unsigned long pgoff, unsigned long flags)
  {
  	unsigned long (*get_area)(struct file *, unsigned long,
  				  unsigned long, unsigned long, unsigned long);
  	/* 针对特定平台的检查，目前arm64中arch_mmap_check是一个空函数 */
  	unsigned long error = arch_mmap_check(addr, len, flags);
  	if (error)
  		return error;
  
  	/* Careful about overflows.. */
      /* 申请虚拟空间的地址不能超过最大值，这里可以知道虚拟空间size的最大值就是TASK_SIZE */
  	if (len > TASK_SIZE)
  		return -ENOMEM;
  	
      /* 指向当前进程的unmap空间的分配函数 */
  	get_area = current->mm->get_unmapped_area;
      /* file不为空的话，则unmap空间的分配函数执行file中指定的函数 */
  	if (file) {
  		if (file->f_op->get_unmapped_area)
  			get_area = file->f_op->get_unmapped_area;
  	} else if (flags & MAP_SHARED) {
          /* 如果file为空，说明可能申请的是匿名空间，这里检查如果是共享内存的话，则分配函数执行共享内存的分配函数 */
  		/*
  		 * mmap_region() will call shmem_zero_setup() to create a file,
  		 * so use shmem's get_unmapped_area in case it can be huge.
  		 * do_mmap_pgoff() will clear pgoff, so match alignment.
  		 */
  		pgoff = 0;
  		get_area = shmem_get_unmapped_area;
  	}
  
      /* 使用前面已经指定的分配函数来在未映射的虚拟空间中映射的空间中申请 */
  	addr = get_area(file, addr, len, pgoff, flags);
  	if (IS_ERR_VALUE(addr))
  		return addr;
  
      /* addr+len 不能大于TASK_SIZE  */
  	if (addr > TASK_SIZE - len)
  		return -ENOMEM;
      /* 检查分配到的地址是否已经被映射，如果已经被映射则返回error，毕竟我们这里要分配的是进程未映射的空间 */
  	if (offset_in_page(addr))
  		return -EINVAL;
  
      /* security检查 */
  	error = security_mmap_addr(addr);
  	return error ? error : addr;
  }
  
  ```
  
  