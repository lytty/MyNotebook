# Linux内核进程管理(八)——CFS调度器之三

本章节主要解析调度器的核心函数`__schedule()`，其作用是让调度器选择和切换到一个合适进程运行。

## 1. 调度时机

>   调度时机，即什么时候，会驱动调度器进入此函数，调度时机可以分为如下3种：

-   阻塞操作： 互斥量(mutex)、信号量(semaphore)、等待队列(waitqueue)等。

-   在中断返回前和系统调用返回用户空间时，去检查`TIF_NEED_RESCHED`标志位以判断是否需要调度。

-   将要被唤醒的进程(Wakeups)不会马上调用`schedule()`，而是会被添加到CFS就绪队列中，并且设置`TIF_NEED_RESCHED`标志位。那么唤醒进程什么时候被调度呢？这要根据内核是否具有可抢占功能(CONFIG_PREEMPT=y)分两种情况。

*   1) 如果内核可抢占，则：如果唤醒动作发生在系统调用或者异常处理上下文中，在下一次调用`preempt_enable()`时会检查是否需要抢占调度；如果唤醒动作发生在硬中断处理上下文中，硬件中断处理返回前夕会检查是否抢占当前进程。
*   2）如果内核不可抢占，则：当前进程调用cond_resched()时会检查是否要调度；主动调度调用schedule()；系统调用或者异常处理返回到用户空间；中断处理完成返回用户空间。

>   以上就是明确调度的时机，上面提到的硬件中断返回前夕和硬件中断返回用户空间前夕是两个不同的概念。前者是每次硬件中断返回前夕都会检查是否有进程需要被抢占调度，不管中断发生点是在内核空间还是用户空间；后者是只有中断发生点在用户空间才会检查。
>
>   从调度时机，我们可以看出来，调用路径很多，也说明了调度器的复杂性。



## 2. `__schedule()`函数解析

-   我们将从以下几个部分来拆解解析函数`__schedule()`：

*   1) 调度之前的初始化工作；
*   2) 根据preempt flag/当前进程的状态；
*   3) 挑选next进程来取代当前运行的进程;
*   4）prev与next进程上下文切换;
*   5) balance_callback调用。

-   `__schedule()`函数定义如下，`kernel4.14/kernel/sched/core.c`

```c
/*
 * __schedule() is the main scheduler function.
 *
 * The main means of driving the scheduler and thus entering this function are:
 *
 *   1. Explicit blocking: mutex, semaphore, waitqueue, etc.
 *
 *   2. TIF_NEED_RESCHED flag is checked on interrupt and userspace return
 *      paths. For example, see arch/x86/entry_64.S.
 *
 *      To drive preemption between tasks, the scheduler sets the flag in timer
 *      interrupt handler scheduler_tick().
 *
 *   3. Wakeups don't really cause entry into schedule(). They add a
 *      task to the run-queue and that's it.
 *
 *      Now, if the new task added to the run-queue preempts the current
 *      task, then the wakeup sets TIF_NEED_RESCHED and schedule() gets
 *      called on the nearest possible occasion:
 *
 *       - If the kernel is preemptible (CONFIG_PREEMPT=y):
 *
 *         - in syscall or exception context, at the next outmost
 *           preempt_enable(). (this might be as soon as the wake_up()'s
 *           spin_unlock()!)
 *
 *         - in IRQ context, return from interrupt-handler to
 *           preemptible context
 *
 *       - If the kernel is not preemptible (CONFIG_PREEMPT is not set)
 *         then at the next:
 *
 *          - cond_resched() call
 *          - explicit schedule() call
 *          - return from syscall or exception to user-space
 *          - return from interrupt-handler to user-space
 *
 * WARNING: must be called with preemption disabled!
 */
static void __sched notrace __schedule(bool preempt)
{
	struct task_struct *prev, *next;
	unsigned long *switch_count;
	struct rq_flags rf;
	struct rq *rq;
	int cpu;
	u64 wallclock;

	cpu = smp_processor_id();
	rq = cpu_rq(cpu);
	prev = rq->curr;

	schedule_debug(prev);

	if (sched_feat(HRTICK))
		hrtick_clear(rq);

	local_irq_disable();
	rcu_note_context_switch(preempt);

	/*
	 * Make sure that signal_pending_state()->signal_pending() below
	 * can't be reordered with __set_current_state(TASK_INTERRUPTIBLE)
	 * done by the caller to avoid the race with signal_wake_up().
	 */
	rq_lock(rq, &rf);
	smp_mb__after_spinlock();

	/* Promote REQ to ACT */
	rq->clock_update_flags <<= 1;
	update_rq_clock(rq);

	switch_count = &prev->nivcsw;
	if (!preempt && prev->state) {
		if (unlikely(signal_pending_state(prev->state, prev))) {
			prev->state = TASK_RUNNING;
		} else {
			deactivate_task(rq, prev, DEQUEUE_SLEEP | DEQUEUE_NOCLOCK);
			prev->on_rq = 0;

			if (prev->in_iowait) {
				atomic_inc(&rq->nr_iowait);
				delayacct_blkio_start();
			}

			/*
			 * If a worker went to sleep, notify and ask workqueue
			 * whether it wants to wake up a task to maintain
			 * concurrency.
			 */
			if (prev->flags & PF_WQ_WORKER) {
				struct task_struct *to_wakeup;

				to_wakeup = wq_worker_sleeping(prev);
				if (to_wakeup)
					try_to_wake_up_local(to_wakeup, &rf);
			}
		}
		switch_count = &prev->nvcsw;
	}

	next = pick_next_task(rq, prev, &rf);
	wallclock = walt_ktime_clock();
	walt_update_task_ravg(prev, rq, PUT_PREV_TASK, wallclock, 0);
	walt_update_task_ravg(next, rq, PICK_NEXT_TASK, wallclock, 0);
	clear_tsk_need_resched(prev);
	clear_preempt_need_resched();

	if (likely(prev != next)) {
#ifdef CONFIG_SCHED_WALT
		if (!prev->on_rq)
			prev->last_sleep_ts = wallclock;
#endif
		rq->nr_switches++;
		rq->curr = next;
		/*
		 * The membarrier system call requires each architecture
		 * to have a full memory barrier after updating
		 * rq->curr, before returning to user-space. For TSO
		 * (e.g. x86), the architecture must provide its own
		 * barrier in switch_mm(). For weakly ordered machines
		 * for which spin_unlock() acts as a full memory
		 * barrier, finish_lock_switch() in common code takes
		 * care of this barrier. For weakly ordered machines for
		 * which spin_unlock() acts as a RELEASE barrier (only
		 * arm64 and PowerPC), arm64 has a full barrier in
		 * switch_to(), and PowerPC has
		 * smp_mb__after_unlock_lock() before
		 * finish_lock_switch().
		 */
		++*switch_count;

		trace_sched_switch(preempt, prev, next);

		/* Also unlocks the rq: */
		rq = context_switch(rq, prev, next, &rf);
	} else {
		rq->clock_update_flags &= ~(RQCF_ACT_SKIP|RQCF_REQ_SKIP);
		rq_unlock_irq(rq, &rf);
	}

	balance_callback(rq);
}

```

下面分别按上述几个部分对函数`__schedule()`进行解析。



### 2.1 调度之前初始化工作

-   本部分分析下面的代码：

```c
static void __sched notrace __schedule(bool preempt)
{
	struct task_struct *prev, *next;
	unsigned long *switch_count;
	struct rq_flags rf;
	struct rq *rq;
	int cpu;
	u64 wallclock;
	/*__schedule函数运行所在的cpu id上*/
	cpu = smp_processor_id(); 
	rq = cpu_rq(cpu); /*获取此cpu的rq运行队列*/
	prev = rq->curr; /*获取当前在rq上运行的task*/
	/*基于时间调度检测和调度统计,debug使用*/
	schedule_debug(prev);
	/*在feature.h中SCHED_FEAT(HRTICK, false),不成立*/
	if (sched_feat(HRTICK))
		hrtick_clear(rq);/*取消rq成员变量 hrtick_timer hrtimer结构体变量*/

	local_irq_disable();
	rcu_note_context_switch(preempt);

	/*
	 * Make sure that signal_pending_state()->signal_pending() below
	 * can't be reordered with __set_current_state(TASK_INTERRUPTIBLE)
	 * done by the caller to avoid the race with signal_wake_up().
	 */
    /*对上面的理解如下:
      1. 当存在signal_pending_state()->signal_pending()时候,即后面有signal处于 
         pending状态
      2. 但是此时调用者设置了进程状态为TASK_INTERRUPTIBLE(可响应信号/中断)
      3. 确保他们响应signal的次序不会被重排,目的避免使用signal_wake_up引起竞争.*/
	rq_lock(rq, &rf);
	smp_mb__after_spinlock();

	/* Promote REQ to ACT */
	rq->clock_update_flags <<= 1;
	update_rq_clock(rq);
	/*获取当前进程上下文切换次数.*/
	switch_count = &prev->nivcsw;
    ...
}

```

