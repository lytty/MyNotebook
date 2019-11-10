# Linux内核初始化(一)——`start_kernel`函数

- 内核的初始化过程由start_kernel函数（\init\main.c）开始，至第一个用户进程init结束，调用了一系列的初始化函数对所有的内核组件进行初始化。其中，start_kernel、rest_init、kernel_init、init_post4个函数构成了整个初始化过程的主线。下面先来分析start_kernel函数。

  `kernel4.14/init/main.c`

  ```c
  asmlinkage __visible void __init start_kernel(void)
  {
  	char *command_line;
  	char *after_dashes;
  
  	set_task_stack_end_magic(&init_task); /* 设置整个系统的第一个进程 */
  	smp_setup_processor_id(); /* 设置smp模型的处理器id */
  	debug_objects_early_init(); /* 用来对obj_hash，obj_static_pool这两个全局变量进行初始化设置。这两个全局变量在进行调试的时候会使用到 */
  
  	cgroup_init_early(); /* cgroup的初始化 */
  
  	local_irq_disable(); /* 屏蔽当前CPU上的所有中断，通过操作arm核心中的寄存器来屏蔽到达CPU上的中断，此时中断控制器中所有送往该CPU上的中断信号都将被忽略 */
  	early_boot_irqs_disabled = true; /* 中断禁止，在‘early bootup code’阶段，boot processor只能运行在中断禁止模式。只有当这个标志位为false的时候，才能运行一些被禁的操作 */
  
  	/*
  	 * Interrupts are still disabled. Do necessary setups, then
  	 * enable them.
  	 */
  	boot_cpu_init(); /* 激活第一个CPU */
  	page_address_init(); /* 初始化高端内存（High Memory）线性地址空间中永久映射相关的全局变量。所以在不支持高端内存即在没有配置CONFIG_HIGHMEM这个宏的时候，该函数是个空函数什么也不做，在ARM系统中，是没有高端内存相关的代码的，所以这个函数就是个空函数 */
  	pr_notice("%s", linux_banner); /* linux内核启动时打印的版本信息 */
  	setup_arch(&command_line); /* 内核参数的解析 */
  	/*
  	 * Set up the the initial canary and entropy after arch
  	 * and after adding latent and command line entropy.
  	 */
  	add_latent_entropy();
  	add_device_randomness(command_line, strlen(command_line));
  	boot_init_stack_canary(); /* 初始化栈canary值，canary值用于防止栈溢出攻击的堆栈的保护字 */
  	mm_init_cpumask(&init_mm); /* 初始化cpu屏蔽字 */
  	setup_command_line(command_line); /* 对command_line进行备份和保存 */
  	setup_nr_cpu_ids(); /* 针对SMP处理器的内存初始化函数，如果不是SMP系统都为空函数 */
  	setup_per_cpu_areas(); /* 若为SMP多核处理器，则给每个cpu分配内存，并拷贝.data.percpu段的数据。为系统中的每个CPU的per_cpu变量申请空间并为boot CPU设置一些数据。 */
  	smp_prepare_boot_cpu();	/* arch-specific boot-cpu hooks 初始化多核处理器系统中的处理器位码表*/
  	boot_cpu_hotplug_init();
  
  	build_all_zonelists(NULL); /* 建立系统内存页区(zone)链表 */
  	page_alloc_init(); /* 内存页初始化 */
  
  	pr_notice("Kernel command line: %s\n", boot_command_line);
  	/* parameters may set static keys */
  	jump_label_init(); /* 初始化所有的__jump_table段 */
  	parse_early_param(); /* 解析早期的内核参数 */
  	after_dashes = parse_args("Booting kernel",
  				  static_command_line, __start___param,
  				  __stop___param - __start___param,
  				  -1, -1, NULL, &unknown_bootoption); /* 对传入内核参数进行解释，如果不能识别的命令就调用最后参数的函数 */
  	if (!IS_ERR_OR_NULL(after_dashes))
  		parse_args("Setting init args", after_dashes, NULL, 0, -1, -1,
  			   NULL, set_init_arg);
  
  	/*
  	 * These use large bootmem allocations and must precede
  	 * kmem_cache_init()
  	 */
  	setup_log_buf(0); /* 使用bootmem分配一个启动信息的缓冲区 */
  	pidhash_init(); /* 使用bootmem分配并初始化PID散列表 */
  	vfs_caches_init_early(); /* 前期VFS缓存初始化 */
  	sort_main_extable(); /* 对内核异常表进行排序 */
  	trap_init(); /* 初始化中断向量 */
  	mm_init(); /* 内存管理模块初始化 */
  
  	ftrace_init(); /* ftrace 初始化 */
  
  	/* trace_printk can be enabled here */
  	early_trace_init();
  
  	/*
  	 * Set up the scheduler prior starting any interrupts (such as the
  	 * timer interrupt). Full topology setup happens at smp_init()
  	 * time - but meanwhile we still have a functioning scheduler.
  	 */
  	sched_init(); /* 调度模块初始化 */
  	/*
  	 * Disable preemption - early bootup scheduling is extremely
  	 * fragile until we cpu_idle() for the first time.
  	 */
  	preempt_disable(); /* 禁用抢占和中断，早期启动时期，调度是极其脆弱的 */
  	if (WARN(!irqs_disabled(),/* 确认是否中断关闭（irqs_disabled），若没有关闭则再local_irq_disable */
  		 "Interrupts were enabled *very* early, fixing it\n"))
  		local_irq_disable();
  	radix_tree_init(); /* 内核radix树算法初始化 */
  
  	/*
  	 * Allow workqueue creation and work item queueing/cancelling
  	 * early.  Work item execution depends on kthreads and starts after
  	 * workqueue_init().
  	 */
  	workqueue_init_early(); /* 工作队列初始化 */
  
  	rcu_init(); /* 内核RCU机制初始化 */
  
  	/* Trace events are available after this */
  	trace_init(); /* trace初始化 */
  
  	context_tracking_init(); 
  	/* init some links before init_ISA_irqs() */
  	early_irq_init(); /* 前期外部中断描述符初始化 */
  	init_IRQ(); /* 架构相关中断初始化 */
  	tick_init(); /* 内核通知链机制的初始化 */
  	rcu_init_nohz(); 
  	init_timers(); /* 定时器初始化 */
  	hrtimers_init(); /* 高精度时钟初始化 */
  	softirq_init(); /* 软中断初始化 */
  	timekeeping_init(); /* 初始化资源和普通计时器 */
  	time_init(); /* 时间、定时器初始化（包括读取CMOS时钟、估测主频、初始化定时器中断等） */
  	sched_clock_postinit(); /* 初始化sched_clock */
  	printk_safe_init(); /* 安全打印初始化 */
  	perf_event_init(); /* CPU性能监视机制初始化 */
  	profile_init(); /* 对内核的一个性能测试工具profile进行初始化。 */
  	call_function_init(); /* 初始化所有CPU的call_single_queue */
  	WARN(!irqs_disabled(), "Interrupts were enabled early\n");
  	early_boot_irqs_disabled = false;
  	local_irq_enable(); /* 使能中断 */
  
  	kmem_cache_init_late(); /* 完善slab分配器的缓存机制 */
  
  	/*
  	 * HACK ALERT! This is early. We're enabling the console before
  	 * we've done PCI setups etc, and console_init() must be aware of
  	 * this. But we do want output early, in case something goes wrong.
  	 */
  	console_init(); /* 初始化控制台以显示printk的内容 */
  	if (panic_later)
  		panic("Too many boot %s vars at `%s'", panic_later,
  		      panic_param);
  
  	lockdep_info(); /* 如果定义了CONFIG_LOCKDEP宏，那么就打印锁依赖信息，否则什么也不做 */
  
  	/*
  	 * Need to run this when irqs are enabled, because it wants
  	 * to self-test [hard/soft]-irqs on/off lock inversion bugs
  	 * too:
  	 */
  	locking_selftest(); /* 测试锁的API是否使用正常 */
  
  	/*
  	 * This needs to be called before any devices perform DMA
  	 * operations that might use the SWIOTLB bounce buffers. It will
  	 * mark the bounce buffers as decrypted so that their usage will
  	 * not cause "plain-text" data to be decrypted when accessed.
  	 */
  	mem_encrypt_init(); 
  
  #ifdef CONFIG_BLK_DEV_INITRD /* 配置CONFIG_BLK_DEV_INITRD选项 – 支持initrd */
  	if (initrd_start && !initrd_below_start_ok && /* 检查initrd的位置是否符合要求 */
  	    page_to_pfn(virt_to_page((void *)initrd_start)) < min_low_pfn) {
  		pr_crit("initrd overwritten (0x%08lx < 0x%08lx) - disabling it.\n",
  		    page_to_pfn(virt_to_page((void *)initrd_start)),
  		    min_low_pfn);
  		initrd_start = 0;
  	}
  #endif
  	kmemleak_init(); /* 内存泄漏检测机制的初始化 */
  	debug_objects_mem_init(); /* 创建调试对象内存缓存，空函数 */
  	setup_per_cpu_pageset(); /* 创建每个CPU的高速缓存集合数组 */
  	numa_policy_init(); /* 初始化NUMA的内存访问策略 */
  	if (late_time_init) 
  		late_time_init();
  	calibrate_delay(); /* 一个cpu性能测试函数 */
  	pidmap_init(); /* PID分配映射初始化 */
  	anon_vma_init(); /* 匿名虚拟内存域初始化 */
  	acpi_early_init(); /* 初始化ACPI电源管理 */
  #ifdef CONFIG_X86
  	if (efi_enabled(EFI_RUNTIME_SERVICES))
  		efi_enter_virtual_mode();
  #endif
  	thread_stack_cache_init(); /* 获取thread_info缓存空间，大部分构架为空函数（包括ARM ） */
  	cred_init(); /* 任务信用系统初始化 */
  	fork_init(); /* 进程创建机制初始化。为内核"task_struct"分配空间，计算最大任务数 */
  	proc_caches_init(); /* 初始化进程创建机制所需的其他数据结构，为其申请空间 */
  	buffer_init(); /* 块设备读写缓冲区初始化（同时创建"buffer_head"cache用户加速访问） */
  	key_init(); /* 内核密钥管理系统初始化 */
  	security_init(); /* 内核安全框架初始化 */
  	dbg_late_init(); /* 内核调试系统后期初始化 */
  	vfs_caches_init(); /* 虚拟文件系统缓存初始化 */
  	pagecache_init();
  	signals_init(); /* 信号管理系统初始化 */
  	proc_root_init(); /* proc文件系统初始化 */
  	nsfs_init(); /* nsfs文件系统初始化 */
  	cpuset_init(); /* CPUSET初始化 */
  	cgroup_init(); /* control group正式初始化 */
  	taskstats_init_early(); /* 任务状态早期初始化函数：为结构体获取高速缓存，并初始化互斥机制 */
  	delayacct_init(); /* 任务延迟初始化 */
  
  	check_bugs(); /* 检查CPU BUG的函数，通过软件规避BUG */
  
  	acpi_subsystem_init(); 
  	arch_post_acpi_subsys_init();
  	sfi_init_late(); /* 功能跟踪调试机制初始化，ftrace 是 function trace 的简称 */
  
  	if (efi_enabled(EFI_RUNTIME_SERVICES)) {
  		efi_free_boot_services();
  	}
  
  	/* Do the rest non-__init'ed, we're now alive */
  	rest_init(); /* rest_init()一旦启动就会创建0号进程作为idle进程，然后由0号进程创建一号进程（第一个用户态进程）并创建一个内核线程来管理系统资源及创建其他进程 */
  }
  
  ```

  