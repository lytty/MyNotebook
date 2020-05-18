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
    ......
}

```



### 2.2 根据preempt flag/当前进程的状态

```c
static void __sched notrace __schedule(bool preempt)
{
	......
	switch_count = &prev->nivcsw;
	if (!preempt && prev->state) {
		if (unlikely(signal_pending_state(prev->state, prev))) {
            /*如果preempt为false && prev进程状态存在,并且此进程有pending的signal发
           生,则将此进程状态设置为running状态*/
			prev->state = TASK_RUNNING;
		} else {
            /*其他情况,则直接将prev进程移出队列,同时设置on_rq=0,表示prev进程不在当前
            rq上*/
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
            /*对上面的解释如下:
            * 如果工作者线程已经休眠了,通知并且询问工作者队列是否需要唤醒进程来维持并发性
            * 如果当前进程的flags集配置了PF_WQ_WORKER则需要处理.
            */ 
			if (prev->flags & PF_WQ_WORKER) {
				struct task_struct *to_wakeup;
				/*获取线程池中第一个idle的worker,如果此worker不为空,则返回此
            worker相关联的进程.*/
				to_wakeup = wq_worker_sleeping(prev);
                /*将to_wakeup进程放入到运行队列中,开始被调度*/
				if (to_wakeup)
					try_to_wake_up_local(to_wakeup, &rf);/*入队,虚拟运行时间update*/ 
			}
		}
		switch_count = &prev->nvcsw;
	}

    ......
}

```

在`struct task_struct`结构体存有三个与上下文切换相关的计数器,如下所示，其中`nvcsw/nivcsw`是自愿（voluntary）/非自愿（involuntary）上下文切换计数。`last_switch_count`是`nvcsw`和`nivcsw`的总和。比如在fork,exit等操作的时候都会修改这几个参数数值。

```c
struct task_struct {
    ...
	/* Context switch counts: */
	unsigned long			nvcsw;
	unsigned long			nivcsw;
	...
#ifdef CONFIG_DETECT_HUNG_TASK
	unsigned long			last_switch_count;
#endif
    ...
}

```



### 2.3 挑选next进程取代当前运行的进程

需要解析的代码如下：

```c
static void __sched notrace __schedule(bool preempt)
{
	......
    /*根据prev信息,rq信息,rf信息,pick一个进程即next*/ 
	next = pick_next_task(rq, prev, &rf);
    /*update 使用WALT方式计算进程负载的真实时间,即当前窗口的时间*/
	wallclock = walt_ktime_clock();
    /*根据进程状态,分别更新prev和next两个进程的walt相关参数*/
	walt_update_task_ravg(prev, rq, PUT_PREV_TASK, wallclock, 0);
	walt_update_task_ravg(next, rq, PICK_NEXT_TASK, wallclock, 0);
    /*清除prev进程TIF_NEED_RESCHED flag*/
	clear_tsk_need_resched(prev);
    /*清除PREEMPT_NEED_RESCHED flag,ARM平台此函数为空*/
	clear_preempt_need_resched();
	......
}

```

下面来看下核心函数`pick_next_task`的实现方式，`kernel4.14/kernel/sched/core.c`:

```c
/*
 * Pick up the highest-prio task:
 */
static inline struct task_struct *
pick_next_task(struct rq *rq, struct task_struct *prev, struct rq_flags *rf)
{
	const struct sched_class *class;
	struct task_struct *p;

	/*
	 * Optimization: we know that if all tasks are in the fair class we can
	 * call that function directly, but only if the @prev task wasn't of a
	 * higher scheduling class, because otherwise those loose the
	 * opportunity to pull in more work from other CPUs.
	 */
    /*当前调度类为fair类或者idle类,并且运行队列的nr_running数量=cfs队列h_nr_running数量
      即当前运行队列里面只有normal类型的进程,没有RT类的进程*/ 
	if (likely((prev->sched_class == &idle_sched_class ||
		    prev->sched_class == &fair_sched_class) &&
		   rq->nr_running == rq->cfs.h_nr_running)) {
		/*执行fair调度类的pick next函数*/
		p = fair_sched_class.pick_next_task(rq, prev, rf);
		if (unlikely(p == RETRY_TASK))
			goto again;

		/* Assumes fair_sched_class->next == idle_sched_class */
        /*如果pick到了idle进程,则修改调度类,执行idle调度类,使rq进入idle状态*/
		if (unlikely(!p))
			p = idle_sched_class.pick_next_task(rq, prev, rf);

		return p;
	}

again:
    /*按照class优先级的高低依次遍历各个class并执行对应的pick next task函数,直到失败为止*/
	for_each_class(class) {
		p = class->pick_next_task(rq, prev, rf);
		if (p) {
			if (unlikely(p == RETRY_TASK))
				goto again;
			return p;
		}
	}

	/* The idle class should always have a runnable task: */
	BUG();
}

```

仅仅分析fair调度类的pick_next_task函数,代码比较长,源码如下，`kernel4.14/kernel/sched/fair.c`:

```c
static struct task_struct *
pick_next_task_fair(struct rq *rq, struct task_struct *prev, struct rq_flags *rf)
{
	struct cfs_rq *cfs_rq = &rq->cfs;
	struct sched_entity *se;
	struct task_struct *p;
	int new_tasks;

again:
	if (!cfs_rq->nr_running)
		goto idle;

#ifdef CONFIG_FAIR_GROUP_SCHED
	if (prev->sched_class != &fair_sched_class)
		goto simple;

	/*
	 * Because of the set_next_buddy() in dequeue_task_fair() it is rather
	 * likely that a next task is from the same cgroup as the current.
	 *
	 * Therefore attempt to avoid putting and setting the entire cgroup
	 * hierarchy, only change the part that actually changes.
	 */

	do {
		struct sched_entity *curr = cfs_rq->curr;

		/*
		 * Since we got here without doing put_prev_entity() we also
		 * have to consider cfs_rq->curr. If it is still a runnable
		 * entity, update_curr() will update its vruntime, otherwise
		 * forget we've ever seen it.
		 */
		if (curr) {
			if (curr->on_rq)
				update_curr(cfs_rq);
			else
				curr = NULL;

			/*
			 * This call to check_cfs_rq_runtime() will do the
			 * throttle and dequeue its entity in the parent(s).
			 * Therefore the nr_running test will indeed
			 * be correct.
			 */
			if (unlikely(check_cfs_rq_runtime(cfs_rq))) {
				cfs_rq = &rq->cfs;

				if (!cfs_rq->nr_running)
					goto idle;

				goto simple;
			}
		}

		se = pick_next_entity(cfs_rq, curr);
		cfs_rq = group_cfs_rq(se);
	} while (cfs_rq);

	p = task_of(se);

	/*
	 * Since we haven't yet done put_prev_entity and if the selected task
	 * is a different task than we started out with, try and touch the
	 * least amount of cfs_rqs.
	 */
	if (prev != p) {
		struct sched_entity *pse = &prev->se;

		while (!(cfs_rq = is_same_group(se, pse))) {
			int se_depth = se->depth;
			int pse_depth = pse->depth;

			if (se_depth <= pse_depth) {
				put_prev_entity(cfs_rq_of(pse), pse);
				pse = parent_entity(pse);
			}
			if (se_depth >= pse_depth) {
				set_next_entity(cfs_rq_of(se), se);
				se = parent_entity(se);
			}
		}

		put_prev_entity(cfs_rq, pse);
		set_next_entity(cfs_rq, se);
	}

	if (hrtick_enabled(rq))
		hrtick_start_fair(rq, p);

	update_misfit_status(p, rq);

	return p;
simple:
#endif

	put_prev_task(rq, prev);

	do {
		se = pick_next_entity(cfs_rq, NULL);
		set_next_entity(cfs_rq, se);
		cfs_rq = group_cfs_rq(se);
	} while (cfs_rq);

	p = task_of(se);

	if (hrtick_enabled(rq))
		hrtick_start_fair(rq, p);

	update_misfit_status(p, rq);

	return p;

idle:
	update_misfit_status(NULL, rq);
	new_tasks = idle_balance(rq, rf);

	/*
	 * Because idle_balance() releases (and re-acquires) rq->lock, it is
	 * possible for any higher priority task to appear. In that case we
	 * must re-start the pick_next_entity() loop.
	 */
	if (new_tasks < 0)
		return RETRY_TASK;

	if (new_tasks > 0)
		goto again;

	return NULL;
}

```

对上面代码的分析,先解析若干个核心函数:

1.   `update_curr`
2.   `check_cfs_rq_runtime`
3.   `pick_next_entity`
4.   `group_cfs_rq`
5.   `is_same_group`
6.   `put_prev_entity`
7.   `set_next_entity`
8.   `parent_entity`
9.   `task_fits_max`
10.   `put_prev_task`
11.   `idle_balance`

#### 2.3.1 函数`update_curr`解析

>   `__schedule() -> pick_next_task_fair() -> update_curr()`定义如下，`kernel4.14/kernel/sched/fair.c`：

```c
/*
 * Update the current task's runtime statistics.
 */
static void update_curr(struct cfs_rq *cfs_rq)
{
    /*获取当前cfs_rq队列的调度实体*/
	struct sched_entity *curr = cfs_rq->curr;
	u64 now = rq_clock_task(rq_of(cfs_rq));/*当前cfs_rq的时间*/ 
	u64 delta_exec;
	int cpu = cpu_of(rq_of(cfs_rq));

	if (unlikely(!curr))
		return;
	/*当前调度实体已经分配的运行时间*/
	delta_exec = now - curr->exec_start;
	if (unlikely((s64)delta_exec <= 0))
		return;

	curr->exec_start = now;

	schedstat_set(curr->statistics.exec_max,
		      max(delta_exec, curr->statistics.exec_max));
	/*更新当前调度实体的总的运行时间*/ 
	curr->sum_exec_runtime += delta_exec;

	if (cpumask_test_cpu(cpu, &min_cap_cpu_mask))
		curr->s_sum_exec_runtime += delta_exec;
	else
		curr->b_sum_exec_runtime += delta_exec;

	schedstat_add(cfs_rq->exec_clock, delta_exec);
	/*根据分配的运行时间和调度实体的权重,增加当前调度实体的虚拟运行时间*/
	curr->vruntime += calc_delta_fair(delta_exec, curr);
    /*更新cfs_rq最小虚拟运行时间(这个是作为所有虚拟运行时间的base value).同时调整由各个
      调度实体的虚拟运行时间组成的红黑树(根据当前调度实体的虚拟运行时间调整当前调度实体在红
      黑树的节点位置)
     */
	update_min_vruntime(cfs_rq);

	if (entity_is_task(curr)) {
		struct task_struct *curtask = task_of(curr);

		trace_sched_stat_runtime(curtask, delta_exec, curr->vruntime);
        /*将此进程的运行时间添加到它的会话组内(即进程组中.)*/  
		cpuacct_charge(curtask, delta_exec);
        /*维护线程组执行运行时间,其实就是维护thread_group_cputimer这个结构体里面的
          成员变量(thread group interval timer counts)*/
		account_group_exec_runtime(curtask, delta_exec);
	}
	/*此函数涉及到throttle相关的feature,如果被throttle或者运行时间运行完毕,会重新分配
      一部分运行时间给当前进程,如果分配失败,则设置重新调度的条件,或者抢占调度*/
	account_cfs_rq_runtime(cfs_rq, delta_exec);
}

```

>   这个函数的最重要目的如下:

1.  更新当前调度实体的虚拟运行时间
2.  更新当前cfs_rq的最小虚拟运行时间
3.  统计调度相关信息和数据
4.  根据分配的运行时间来确定是否需要抢占调度

>   `update_curr() -> account_cfs_rq_runtime()`定义及调用流程如下，`kernel4.14/kernel/sched/fair.c`：

```c
static __always_inline
void account_cfs_rq_runtime(struct cfs_rq *cfs_rq, u64 delta_exec)
{
	if (!cfs_bandwidth_used() || !cfs_rq->runtime_enabled)
		return;

	__account_cfs_rq_runtime(cfs_rq, delta_exec);
}

static void __account_cfs_rq_runtime(struct cfs_rq *cfs_rq, u64 delta_exec)
{
	/* dock delta_exec before expiring quota (as it could span periods) */
    /*runtime_remaining是一个配额,这次分配了delta_exec运行时间,则配额自然会减少*/
	cfs_rq->runtime_remaining -= delta_exec;

	if (likely(cfs_rq->runtime_remaining > 0))
		return;

	if (cfs_rq->throttled)
		return;
	/*
	 * if we're unable to extend our runtime we resched so that the active
	 * hierarchy can be throttled
	 */
	if (!assign_cfs_rq_runtime(cfs_rq) && likely(cfs_rq->curr))
		resched_curr(rq_of(cfs_rq));
}

/* returns 0 on failure to allocate runtime */
static int assign_cfs_rq_runtime(struct cfs_rq *cfs_rq)
{
	struct task_group *tg = cfs_rq->tg;
	struct cfs_bandwidth *cfs_b = tg_cfs_bandwidth(tg);
	u64 amount = 0, min_amount;

	/* note: this is a positive sum as runtime_remaining <= 0 */
	min_amount = sched_cfs_bandwidth_slice() - cfs_rq->runtime_remaining;

	raw_spin_lock(&cfs_b->lock);
	if (cfs_b->quota == RUNTIME_INF)
		amount = min_amount;
	else {
        /*重新激活throttle/unthrottle的定时器*/
		start_cfs_bandwidth(cfs_b);
		/*runtime是可以运行的运行时间限额,是cfs_rq在启动时候申请的.*/
		if (cfs_b->runtime > 0) {
			amount = min(cfs_b->runtime, min_amount);
            /*增加了amount运行时间,则限额需要减去新分配的运行时间*/
			cfs_b->runtime -= amount;
			cfs_b->idle = 0;
		}
	}
	raw_spin_unlock(&cfs_b->lock);
	/*增加运行时间配额,也即是增加了进程的运行时间*/
	cfs_rq->runtime_remaining += amount;

	return cfs_rq->runtime_remaining > 0;
}

```

>   至此`update_curr`更新当前调度实体的虚拟运行时间,调整其红黑树节点位置,同时处理其运行时间使用完毕之后的逻辑流程.

#### 2.3.2 函数`check_cfs_rq_runtime`解析

>   `__schedule() -> pick_next_task_fair() -> check_cfs_rq_runtime()`，这个函数的功能是检测当前是否做`throttle`操作.如果`throttle`操作,则直接将`prev`进程重新入队,重新选择新的调度实体。后面的函数会讲解到`put_prev_entity`函数的原理，定义如下，`kernel4.14/kernel/sched/fair.c`

```c
/* conditionally throttle active cfs_rq's from put_prev_entity() */
static bool check_cfs_rq_runtime(struct cfs_rq *cfs_rq)
{
	if (!cfs_bandwidth_used())
		return false;

	if (likely(!cfs_rq->runtime_enabled || cfs_rq->runtime_remaining > 0))
		return false;

	/*
	 * it's possible for a throttled entity to be forced into a running
	 * state (e.g. set_curr_task), in this case we're finished.
	 */
	if (cfs_rq_throttled(cfs_rq))
		return true;
	/*对cfs_rq做throttle操作*/
	throttle_cfs_rq(cfs_rq);
	return true;
}

```



#### 2.3.3 函数`pick_next_entity`解析

>   `__schedule() -> pick_next_task_fair() -> pick_next_entity()`，定义如下，`kernel4.14/kernel/sched/fair.c`

```c
/*
 * Pick the next process, keeping these things in mind, in this order:
 * 1) keep things fair between processes/task groups
 * 2) pick the "next" process, since someone really wants that to run
 * 3) pick the "last" process, for cache locality
 * 4) do not run the "skip" process, if something else is available
 */
static struct sched_entity *
pick_next_entity(struct cfs_rq *cfs_rq, struct sched_entity *curr)
{
    /*挑选红黑树最左边的叶子节点,即虚拟运行时间最小的节点,也是优先被调度的节点*/
	struct sched_entity *left = __pick_first_entity(cfs_rq);
	struct sched_entity *se;

	/*
	 * If curr is set we have to see if its left of the leftmost entity
	 * still in the tree, provided there was anything in the tree at all.
	 */
    /*根据当前调度实体的虚拟运行时间来修改left调度实体的指向*/
	if (!left || (curr && entity_before(curr, left)))
		left = curr;
	/*理想情况下,我们需要调度最小虚拟运行时间的调度实体*/
	se = left; /* ideally we run the leftmost entity */

	/*
	 * Avoid running the skip buddy, if running something else can
	 * be done without getting too unfair.
	 */
    /*skip buddy是不应该被选择的调度实体,但是最小的虚拟运行时间的调度实体与
      skip_buddy是同一个,则需要重现选择候选者.*/ 
	if (cfs_rq->skip == se) {
		struct sched_entity *second;

		if (se == curr) {
            /*rb tree的最左边的节点,与当前调度实体是同一个调度实体,则直接选择当前调度
          实体的下一个节点作为候选调度实体*/
			second = __pick_first_entity(cfs_rq);
		} else {
            /*否则选最小虚拟运行时间的调度实体的下一个节点作为候选的调度实体*/
			second = __pick_next_entity(se);
            /*根据系统状态变化修正候选者,比如选择的候选者为空或者候选者的虚拟运行时间
            大于当前调度实体*/ 
			if (!second || (curr && entity_before(curr, second)))
				second = curr;
		}
		/*统一决策:目的只有一个,在选择next调度实体的时候,不要选择之后导致抢占的发生,否则
        浪费系统资源还影响系统性能.具体在后面分析wakeup_preempt_entity函数*/
		if (second && wakeup_preempt_entity(second, left) < 1)
			se = second;
	}

	/*
	 * Prefer last buddy, try to return the CPU to a preempted task.
	 */
    /*如果cfs_rq的last成员不为空,并且last调度实体的虚拟运行时间等因素比left更需要被
     调度,则重新设置选择的调度实体为last*/  
	if (cfs_rq->last && wakeup_preempt_entity(cfs_rq->last, left) < 1)
		se = cfs_rq->last;

	/*
	 * Someone really wants this to run. If it's not unfair, run it.
	 */
    /*再次检测对应的调度环境,正如这条语句所说的,某些进程想要本次运行,并且也符合抢占
     的条件,那么修改选择的调度实体*/ 
	if (cfs_rq->next && wakeup_preempt_entity(cfs_rq->next, left) < 1)
		se = cfs_rq->next;
	/*对cfs_rq队列的三个成员变量,last,skip,next分别进行清空操作.即只要任一个等于
    se,则将其设置为NULL*/
	clear_buddies(cfs_rq, se);

	return se;
}

static inline int entity_before(struct sched_entity *a,
				struct sched_entity *b)
{
	return (s64)(a->vruntime - b->vruntime) < 0;
}

struct sched_entity *__pick_first_entity(struct cfs_rq *cfs_rq)
{
	struct rb_node *left = rb_first_cached(&cfs_rq->tasks_timeline);

	if (!left)
		return NULL;

	return rb_entry(left, struct sched_entity, run_node);
}

static struct sched_entity *__pick_next_entity(struct sched_entity *se)
{
	struct rb_node *next = rb_next(&se->run_node);

	if (!next)
		return NULL;

	return rb_entry(next, struct sched_entity, run_node);
}

/*
 * Should 'se' preempt 'curr'.
 *
 *             |s1
 *        |s2
 *   |s3
 *         g
 *      |<--->|c
 *
 *  w(c, s1) = -1
 *  w(c, s2) =  0
 *  w(c, s3) =  1
 *
 */
static int
wakeup_preempt_entity(struct sched_entity *curr, struct sched_entity *se)
{
	s64 gran, vdiff = curr->vruntime - se->vruntime;
	/*如果vdiff<=0,表示curr应该优先调度*/
	if (vdiff <= 0)
		return -1;
	/*惩罚优先级低的进程,即增加优先级低的虚拟运行时间.如果vdiff差值大于惩罚值,则se可
    以抢占curr调度实体,也即是说,在pick next entity的时候会选择se而不会选择curr调度
    实体*/
	gran = wakeup_gran(curr, se);
	if (vdiff > gran)
		return 1;

	return 0;
}

/*保证调度实体se的最少运行时间为sysctl_sched_wakeup_granularity,转化为se虚拟运行 
  时间增益*/
static unsigned long
wakeup_gran(struct sched_entity *curr, struct sched_entity *se)
{	/*最小运行时间颗粒度,是必须保证的,否则进程运行时间过短没有多大意义*/
	unsigned long gran = sysctl_sched_wakeup_granularity;

	/*
	 * Since its curr running now, convert the gran from real-time
	 * to virtual-time in his units.
	 *
	 * By using 'se' instead of 'curr' we penalize light tasks, so
	 * they get preempted easier. That is, if 'se' < 'curr' then
	 * the resulting gran will be larger, therefore penalizing the
	 * lighter, if otoh 'se' > 'curr' then the resulting gran will
	 * be smaller, again penalizing the lighter task.
	 *
	 * This is especially important for buddies when the leftmost
	 * task is higher priority than the buddy.
	 */
	return calc_delta_fair(gran, se);
}

static void clear_buddies(struct cfs_rq *cfs_rq, struct sched_entity *se)
{
	if (cfs_rq->last == se)
		__clear_buddies_last(se);

	if (cfs_rq->next == se)
		__clear_buddies_next(se);

	if (cfs_rq->skip == se)
		__clear_buddies_skip(se);
}

static void __clear_buddies_last(struct sched_entity *se)
{
	for_each_sched_entity(se) {
		struct cfs_rq *cfs_rq = cfs_rq_of(se);
		if (cfs_rq->last != se)
			break;

		cfs_rq->last = NULL;
	}
}

static void __clear_buddies_next(struct sched_entity *se)
{
	for_each_sched_entity(se) {
		struct cfs_rq *cfs_rq = cfs_rq_of(se);
		if (cfs_rq->next != se)
			break;

		cfs_rq->next = NULL;
	}
}

static void __clear_buddies_skip(struct sched_entity *se)
{
	for_each_sched_entity(se) {
		struct cfs_rq *cfs_rq = cfs_rq_of(se);
		if (cfs_rq->skip != se)
			break;

		cfs_rq->skip = NULL;
	}
}

```

>   从上面的代码可以清晰的知道,`pick_next_entity`目的是从`rb tree`中选择最左边的节点作为`next entity`.  重点是需要考虑与当前调度实体,`cfs_rq`队列中`last/next/skip`调度实体参数的关系,最后确定`next  entity`.最重要的目的就是选择`next entity`之后,尽可能的减少被抢占的可能性.

#### 2.3.4 函数`group_cfs_rq`解析

>   `__schedule() -> pick_next_task_fair() -> group_cfs_rq()`，定义如下，`kernel4.14/kernel/sched/fair.c`

```c
/* runqueue "owned" by this group */
static inline struct cfs_rq *group_cfs_rq(struct sched_entity *grp)
{
	return grp->my_q;
}

```

>   表示调度实体`grp`是一个进程组内的一个进程,进程组有自己的`cfs_rq`运行队列.进程组内的调度实体都放到`my_q`运行队列,而不会放到其他`cfs_rq`队列。

#### 2.3.5 函数`is_same_group`解析



### 2.4



```c
static void __sched notrace __schedule(bool preempt)
{
	......
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

