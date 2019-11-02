# Linux内核进程管理(二)——init_task进程

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