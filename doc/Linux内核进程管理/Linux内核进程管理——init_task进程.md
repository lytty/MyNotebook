# Linux内核进程管理——init_task进程

## 1. `init_task`进程

- `Linux`内核在启动时会有一个`init_task`进程，它是系统所有进程的“鼻祖”，称为 0 号进程或`idle`进程或`swapper`进程。当系统没有进程需要调度时，调度器就会去执行`idle`进程，`idle`进程在内核启动（`start_kernel()函数`）时静态创建，所有的核心数据结构都预先静态赋值。

- `init_task`进程的`task_struct`数据结构通过`INIT_TASK`宏来赋值。其实现如下：

  `kernel4.14/init/init_task.c`

  ```c
  /* Initial task structure */
  struct task_struct init_task = INIT_TASK(init_task);
  EXPORT_SYMBOL(init_task);
  
  ```

  `kernel4.14/include/linux/init_task.h`

  ```c
  /*
   *  INIT_TASK is used to set up the first task table, touch at
   * your own risk!. Base=0, limit=0x1fffff (=2MB)
   */
  #define INIT_TASK(tsk)	\
  {									\
  	INIT_TASK_TI(tsk)						\
  	.state		= 0,						\
  	.stack		= init_stack,					\
  	.usage		= ATOMIC_INIT(2),				\
  	.flags		= PF_KTHREAD,					\
  	.prio		= MAX_PRIO-20,					\
  	.static_prio	= MAX_PRIO-20,					\
  	.normal_prio	= MAX_PRIO-20,					\
  	.policy		= SCHED_NORMAL,					\
  	.cpus_allowed	= CPU_MASK_ALL,					\
  	.nr_cpus_allowed= NR_CPUS,					\
  	.mm		= NULL,						\
  	.active_mm	= &init_mm,					\
  	.restart_block = {						\
  		.fn = do_no_restart_syscall,				\
  	},								\
  	.se		= {						\
  		.group_node 	= LIST_HEAD_INIT(tsk.se.group_node),	\
  	},								\
  	.rt		= {						\
  		.run_list	= LIST_HEAD_INIT(tsk.rt.run_list),	\
  		.time_slice	= RR_TIMESLICE,				\
  	},								\
  	.tasks		= LIST_HEAD_INIT(tsk.tasks),			\
  	INIT_PUSHABLE_TASKS(tsk)					\
  	INIT_CGROUP_SCHED(tsk)						\
  	.ptraced	= LIST_HEAD_INIT(tsk.ptraced),			\
  	.ptrace_entry	= LIST_HEAD_INIT(tsk.ptrace_entry),		\
  	.real_parent	= &tsk,						\
  	.parent		= &tsk,						\
  	.children	= LIST_HEAD_INIT(tsk.children),			\
  	.sibling	= LIST_HEAD_INIT(tsk.sibling),			\
  	.group_leader	= &tsk,						\
  	RCU_POINTER_INITIALIZER(real_cred, &init_cred),			\
  	RCU_POINTER_INITIALIZER(cred, &init_cred),			\
  	.comm		= INIT_TASK_COMM,				\
  	.thread		= INIT_THREAD,					\
  	.fs		= &init_fs,					\
  	.files		= &init_files,					\
  	.signal		= &init_signals,				\
  	.sighand	= &init_sighand,				\
  	.nsproxy	= &init_nsproxy,				\
  	.pending	= {						\
  		.list = LIST_HEAD_INIT(tsk.pending.list),		\
  		.signal = {{0}}},					\
  	.blocked	= {{0}},					\
  	.alloc_lock	= __SPIN_LOCK_UNLOCKED(tsk.alloc_lock),		\
  	.journal_info	= NULL,						\
  	INIT_CPU_TIMERS(tsk)						\
  	.pi_lock	= __RAW_SPIN_LOCK_UNLOCKED(tsk.pi_lock),	\
  	.timer_slack_ns = 50000, /* 50 usec default slack */		\
  	.pids = {							\
  		[PIDTYPE_PID]  = INIT_PID_LINK(PIDTYPE_PID),		\
  		[PIDTYPE_PGID] = INIT_PID_LINK(PIDTYPE_PGID),		\
  		[PIDTYPE_SID]  = INIT_PID_LINK(PIDTYPE_SID),		\
  	},								\
  	.thread_group	= LIST_HEAD_INIT(tsk.thread_group),		\
  	.thread_node	= LIST_HEAD_INIT(init_signals.thread_head),	\
  	INIT_IDS							\
  	INIT_PERF_EVENTS(tsk)						\
  	INIT_TRACE_IRQFLAGS						\
  	INIT_LOCKDEP							\
  	INIT_FTRACE_GRAPH						\
  	INIT_TRACE_RECURSION						\
  	INIT_TASK_RCU_PREEMPT(tsk)					\
  	INIT_TASK_RCU_TASKS(tsk)					\
  	INIT_CPUSET_SEQ(tsk)						\
  	INIT_RT_MUTEXES(tsk)						\
  	INIT_PREV_CPUTIME(tsk)						\
  	INIT_VTIME(tsk)							\
  	INIT_NUMA_BALANCING(tsk)					\
  	INIT_KASAN(tsk)							\
  	INIT_LIVEPATCH(tsk)						\
  	INIT_TASK_SECURITY						\
  }
  
  ```



## 2. 内核栈`thread_info`

- `init_task`进程的`task_struct`数据结构中`stack`成员指向`thread_info`数据结构。通常内核栈大小是`8KB`，即两个物理页面的大小（内核栈大小通常和体系结构相关，`ARM32` 架构中内核栈大小是 `8KB`，`ARM64`架构中内核栈大小是 `16KB`。），它存放在内核映像文件中的`data`段中，在编译链接时预先分配好，具体可见`kernel4.14/arch/arm/kernel/vmlinux.lds.S`:

  ```
  SECTIONS
  {
  	.data : AT(__data_loc) {
  		_data = .;		/* address in memory */
  		_sdata = .;
  
  		/*
  		 * first, the init task union, aligned
  		 * to an 8192 byte boundary.
  		 */
  		INIT_TASK_DATA(THREAD_SIZE)
  
  		...
  
  		_edata = .;
  	}
  }
  
  ```

  `kernel4.14/arch/arm/include/asm/thread_info.h`:

  ```c
  #define THREAD_SIZE_ORDER	1
  #define THREAD_SIZE		(PAGE_SIZE << THREAD_SIZE_ORDER)
  #define THREAD_START_SP		(THREAD_SIZE - 8)
  
  ```

  `kernel4.14/include/asm-generic/vmlinux.lds.h`:

  ```c
  #define INIT_TASK_DATA(align)						\
  	. = ALIGN(align);						\
  	VMLINUX_SYMBOL(__start_init_task) = .;				\
  	*(.data..init_task)						\
  	VMLINUX_SYMBOL(__end_init_task) = .;
  
  ```

- 由链接文件可以看出`data`段预留了 8KB 的空间用于内核栈，存放在 data 段的 `.data..init_task`中。`__init_task_data`宏会直接读取`.data..init_task`段内存，并且存放了一个`thread_union`联合数据结构，从联合数据结构可以看出其分布情况：开始的地方存放了`struct thread_info`数据结构，顶部往下的空间用于内核栈空间。

  `kernel4.14/include/linux/init_task.h`

  ```c
  /* Attach to the init_task data structure for proper alignment */
  #define __init_task_data __attribute__((__section__(".data..init_task")))
  
  ```

  `kernel4.14/init/init_task.c`

  ```c
  /*
   * Initial thread structure. Alignment of this is handled by a special
   * linker map entry.
   */
  union thread_union init_thread_union __init_task_data = {
  #ifndef CONFIG_THREAD_INFO_IN_TASK
  	INIT_THREAD_INFO(init_task)
  #endif
  };
  
  ```

  `kernel4.14/include/linux/sched.h`

  ```c
  union thread_union {
  #ifndef CONFIG_THREAD_INFO_IN_TASK
  	struct thread_info thread_info;
  #endif
  	unsigned long stack[THREAD_SIZE/sizeof(long)];
  };
  
  ```

  `kernel4.14/arch/arm/include/asm/thread_info.h`

  ```c
  #define INIT_THREAD_INFO(tsk)						\
  {									\
  	.task		= &tsk,						\
  	.flags		= 0,						\
  	.preempt_count	= INIT_PREEMPT_COUNT,				\
  	.addr_limit	= KERNEL_DS,					\
  }
  
  ```

- `__init_task_data`存放在`.data..init_task`段中，`__init_task_data`声明为`thread_union`类型，`thread_union`类型描述了整个内核栈`stack[]`，栈的最下面存放`struct thread_info`数据结构，因此，`__init_task_data`也通过宏`INIT_THREAD_INFO`来初始化`struct thread_info`数据结构。`init`进程的`task_struct`数据结构通过宏`INIT_TASK`来初始化。

- `ARM32`处理器从汇编代码跳转到 C 语言的入口点在`start_kernel()`函数之前，设置了 SP 寄存器指向 8KB 内核栈顶部区域（要预留 8Byte 的空洞）。

  `kernel4.14/arch/arm/kernel/head-common.S`

  ```
  __mmap_switched:
  	adr	r3, __mmap_switched_data
  
  	ldmia	r3!, {r4, r5, r6, r7}
  	cmp	r4, r5				@ Copy data segment if needed
  1:	cmpne	r5, r6
  	ldrne	fp, [r4], #4
  	strne	fp, [r5], #4
  	bne	1b
  
  	mov	fp, #0				@ Clear BSS (and zero fp)
  1:	cmp	r6, r7
  	strcc	fp, [r6],#4
  	bcc	1b
  
   ARM(	ldmia	r3, {r4, r5, r6, r7, sp})
   THUMB(	ldmia	r3, {r4, r5, r6, r7}	)
   THUMB(	ldr	sp, [r3, #16]		)
  	str	r9, [r4]			@ Save processor ID
  	str	r1, [r5]			@ Save machine type
  	str	r2, [r6]			@ Save atags pointer
  	cmp	r7, #0
  	strne	r0, [r7]			@ Save control register values
  	b	start_kernel
  ENDPROC(__mmap_switched)
  
  	.align	2
  	.type	__mmap_switched_data, %object
  __mmap_switched_data:
  	.long	__data_loc			@ r4
  	.long	_sdata				@ r5
  	.long	__bss_start			@ r6
  	.long	_end				@ r7
  	.long	processor_id			@ r4
  	.long	__machine_arch_type		@ r5
  	.long	__atags_pointer			@ r6
  #ifdef CONFIG_CPU_CP15
  	.long	cr_alignment			@ r7
  #else
  	.long	0				@ r7
  #endif
  	.long	init_thread_union + THREAD_START_SP @ sp
  	.size	__mmap_switched_data, . - __mmap_switched_data
  
  ```

  `kernel4.14/arch/arm/include/asm/thread_info.h`

  ```c
  #define THREAD_START_SP		(THREAD_SIZE - 8)
  
  ```

  在汇编代码`__mmap_switched`标签处设置相关的`r3 ~ r7`以及`SP`寄存器，其中，`SP`寄存器指向 `data` 段预留的 `8KB` 空间的顶部`（8KB - 8）`，然后跳转到`start_kernel()`。`__mmap_switched_data`标签处定义了`r4 ~ sp`寄存器的值，相当于一个表，通过`adr`指令把这表督导 `r3` 寄存器中，然后再通过 `ldmia` 指令写入相应的寄存器中。

- 内核有一个常用的变量`current`用于获取当前进程`task_struct`数据结构，它利用了内核栈的特性。首先通过`SP`寄存器获取当前内核栈的地址，对齐后可以获取`struct thread_info`数据结构的指针，最后通过`thread_info->task`成员获取`task_struct`数据结构。如下图所示：![1572837563169](/home/haibin.xu/haibin/doc/picture/进程2.1 内核栈.png)

  `kernel4.14/include/asm-generic/current.h`

  ```c
  #define get_current() (current_thread_info()->task)
  #define current get_current()
  
  ```

  `kernel4.14/arch/arm/include/asm/thread_info.h`

  ```c
  /*
   * how to get the current stack pointer in C
   */
  register unsigned long current_stack_pointer asm ("sp");
  
  /*
   * how to get the thread information struct from C
   */
  static inline struct thread_info *current_thread_info(void) __attribute_const__;
  
  static inline struct thread_info *current_thread_info(void)
  {
  	return (struct thread_info *)
  		(current_stack_pointer & ~(THREAD_SIZE - 1));
  }
  
  ```

- `struct thread_info`数据结构的定义：`kernel4.14/arch/arm/include/asm/thread_info.h`

  ```c
  struct thread_info {
  	unsigned long		flags;		/* low level flags */
  	int			preempt_count;	/* 0 => preemptable, <0 => bug */
  	mm_segment_t		addr_limit;	/* address limit */
  	struct task_struct	*task;		/* main task structure */
  	__u32			cpu;		/* cpu */
  	__u32			cpu_domain;	/* cpu domain */
  	struct cpu_context_save	cpu_context;	/* cpu context */
  	__u32			syscall;	/* syscall number */
  	__u8			used_cp[16];	/* thread used copro */
  	unsigned long		tp_value[2];	/* TLS registers */
  #ifdef CONFIG_CRUNCH
  	struct crunch_state	crunchstate;
  #endif
  	union fp_state		fpstate __attribute__((aligned(8)));
  	union vfp_state		vfpstate;
  #ifdef CONFIG_ARM_THUMBEE
  	unsigned long		thumbee_state;	/* ThumbEE Handler Base register */
  #endif
  };
  
  ```

  