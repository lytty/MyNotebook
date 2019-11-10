# Linux内核初始化(二)——函数解析之一

## 1. `set_task_stack_end_magic`函数

`kernel4.14/kernel/fork.c`

```c
void set_task_stack_end_magic(struct task_struct *tsk)
{
	unsigned long *stackend;

	stackend = end_of_stack(tsk);
	*stackend = STACK_END_MAGIC;	/* for overflow detection */
}

```

- `set_task_stack_end_magic(&init_task)`函数设置整个系统的第一个进程`init_task`。`init_task`进程相关知识可查阅《Linux内核进程管理(二)——init_task进程》章节，本文不再详细叙述。

- 在这个函数中，获取内核栈边界地址（`end_of_stack(tsk)`），然后把 `STACK_END_MAGIC`这个宏设置为栈溢出的标志。



## 2. `smp_setup_processor_id`函数

- smp模型指的是对称多处理模型（`Symmetric Multi-Processor`），指的是多个CPU之间是平等关系，共享全部总线，内存和IO等。但是这个结构扩展性不好，往往CPU数量多了之后，很容易遇到抢占资源的问题。`smp_setup_process_id`在普通情况下是空实现，在不同的体系，比如`arc/arm/kernel/setup.c`就有对应的逻辑。

`kernel4.14/arch/arm/kernel/setup.c`

```c
void __init smp_setup_processor_id(void)
{
	int i;
	u32 mpidr = is_smp() ? read_cpuid_mpidr() & MPIDR_HWID_BITMASK : 0; /* 判断是否是smp系统,如果是则从arm协处理器读取当前cpuid,否则为0 */
	u32 cpu = MPIDR_AFFINITY_LEVEL(mpidr, 0); /* 根据level确定cpu号，即cpu=(mpidr>>0)&0xff */

	cpu_logical_map(0) = cpu; /* 设置cpu的map数组 */
	for (i = 1; i < nr_cpu_ids; ++i) /* nr_cpu_ids表示系统中cpu总数 */
		cpu_logical_map(i) = i == cpu ? 0 : i;

	/*
	 * clear __my_cpu_offset on boot CPU to avoid hang caused by
	 * using percpu variable early, for example, lockdep will
	 * access percpu variable inside lock_release
	 */
	set_my_cpu_offset(0); /*  */

	pr_info("Booting Linux on physical CPU 0x%x\n", mpidr);
}

```

`kernel4.14/arch/arm/include/asm/smp_plat.h`

```c
/*
 * Return true if we are running on a SMP platform
 */
static inline bool is_smp(void)
{
#ifndef CONFIG_SMP
	return false;
#elif defined(CONFIG_SMP_ON_UP) /* CONFIG_SMP_ON_UP表示可以支援SMP Kernel运行在UniProcessor(單核心)的处理器上 */
	extern unsigned int smp_on_up;
	return !!smp_on_up; /* 两个感叹号可以保证返回值只能是0和1 */
#else
	return true;
#endif
}

```

`kernel4.14/arch/arm/include/asm/cputype.h`

```c
static inline unsigned int __attribute_const__ read_cpuid_mpidr(void)
{
	return read_cpuid(CPUID_MPIDR); /* 从arm协处理器CP15的c0中读取当前cpu id */
}

#define CPUID_MPIDR	5
#ifdef CONFIG_CPU_CP15
#define read_cpuid(reg)							\
	({								\
		unsigned int __val;					\
		asm("mrc	p15, 0, %0, c0, c0, " __stringify(reg)	\
		    : "=r" (__val)					\
		    :							\
		    : "cc");						\
		__val;							\
	})

#define MPIDR_AFFINITY_LEVEL(mpidr, level) \
	((mpidr >> MPIDR_LEVEL_SHIFT(level)) & MPIDR_LEVEL_MASK)

```

`kernel4.14/arch/arm/include/asm/percpu.h`

```c
#if defined(CONFIG_SMP) && !defined(CONFIG_CPU_V6)
static inline void set_my_cpu_offset(unsigned long off)
{
	/* Set TPIDRPRW */
	asm volatile("mcr p15, 0, %0, c13, c0, 4" : : "r" (off) : "memory");
}

```

