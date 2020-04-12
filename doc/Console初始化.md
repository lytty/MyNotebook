# Console初始化
## 1. earlycon机制实现原理

- *early console*，顾名思义，他表示的就是早期的*console*设备，主要用于在系统启动阶段的内核打印的输出，由于启动阶段*linux*内核实际设备驱动模型还没有加载完成，所以早期的启动信息需要一个特殊的*console*用于输出*log*。

- 在*ARM64 kernel*未建立*console*之前，使用*earlycon*，实现打印。在`kernel/kernel4.14/arch/arm64/boot/dts/sprd/sp9863a-1h10.dts`文件中*chosen*属性*bootargs*中，要加入如下选项：

  ```
  chosen {
  		...;
          bootargs = "earlycon=sprd_serial,0x70100000,115200n8 ...";
  	};
  
  ```

  > *sprd_serial*表示针对*sprd_serial*这个串口设备，*0x70100000*是串口的起始地址。

  

- 使用*sprd_serial*串口，在`kernel/kernel4.14/drivers/tty/serial/sprd_serial.c`中，有如下宏定义：

  ```c
  OF_EARLYCON_DECLARE(sprd_serial, "sprd,sc9836-uart",
  		    sprd_early_console_setup);
  
  ```

  `OF_EARLYCON_DECLARE`是一个宏，定义在`kernel/kernel4.14/include/linux/serial_core.h`，上述代码展开之后，

  ```
  static const struct earlycon_id _earlycon_sprd_serial			\
  	     __used __section(__earlycon_table)			\
  		= { .name = "sprd_serial",				\
  		    .compatible = "sprd,sc9836-uart",				\
  		    .setup = sprd_early_console_setup  };	
  
  ```

  定义了一个*earlycon_id*结构的变量`_earlycon_sprd_serial`。该变量中， `setup`函数指针指向*sprd_early_console_setup*函数。这些*earlycon_id*都放在*__earlycon_table*中。

  *struct earlycon_id*定义在`kernel/kernel4.14/include/linux/serial_core.h`，如下：

  ```c
  struct earlycon_id {
  	char	name[15];
  	char	name_term;	/* In case compiler didn't '\0' term name */
  	char	compatible[128];
  	int	(*setup)(struct earlycon_device *, const char *options);
  };
  
  ```



- 在 `kernel/kernel4.14/drivers/tty/serial/earlycon.c`中，有如下宏定义：

  ```c
  early_param("earlycon", param_setup_earlycon);
  
  ```

  *early_param*定义在`kernel/kernel4.14/include/linux/init.h`，上述代码展开如下，

  ```c
  static const char __setup_str_param_setup_earlycon \
          __section(.init.rodata) __aligned(1) = "earlycon";  \
  static struct obs_kernel_param __setup_param_setup_earlycon  \
      __used __setion(.init.setup)       \
      __attrubite__((aligned(sizeof(long))))  \
      = { "earlycon", param_setup_earlycon, 1 };
  
  ```

  定义一个变量*__setup_str_param_setup_earlycon*，和一个结构体变量*__setup_param_setup_earlycon*。结构体变量，放在了.init.setup段中。其中 `struct obs_kernel_param`原型：

  ```c
  struct obs_kernel_param {
  	const char *str;
  	int (*setup_func)(char *);
  	int early;
  };
  
  ```



- 在`kernel/kernel4.14/init/main.c`中， `start_kernel->setup_arch->parse_early_param`，通过`cmdline`传递的参数，进行`early`初始化。

  ```c
  /* Arch code calls this early on, or if not, just before other parsing. */
  void __init parse_early_param(void)
  {
  	static int done __initdata;
  	static char tmp_cmdline[COMMAND_LINE_SIZE] __initdata;
  
  	if (done)
  		return;
  
  	/* All fall through to do_early_param. */
  	strlcpy(tmp_cmdline, boot_command_line, COMMAND_LINE_SIZE);
  	parse_early_options(tmp_cmdline);
  	done = 1;
  }
  
  ```

  通过**parse_early_options**函数，分析 cmdline，也就是 bootargs，同样也在`kernel/kernel4.14/init/main.c`中实现：

  ```c
  void __init parse_early_options(char *cmdline)
  {
  	parse_args("early options", cmdline, NULL, 0, 0, 0, NULL,
  		   do_early_param);
  }
  
  ```

  调用 parse_args，从 cmdline中，分析 early options。关键是*do_early_param*函数。参数 param 是 cmdline 中的参数变量以及参数值。

  ```c
  /* Check for early params. */
  static int __init do_early_param(char *param, char *val,
  				 const char *unused, void *arg)
  {
  	const struct obs_kernel_param *p;
  
  	for (p = __setup_start; p < __setup_end; p++) {
  		if ((p->early && parameq(param, p->str)) ||
  		    (strcmp(param, "console") == 0 &&
  		     strcmp(p->str, "earlycon") == 0)
  		) {
  			if (p->setup_func(val) != 0)
  				pr_warn("Malformed early option '%s'\n", param);
  		}
  	}
  	/* We accept everything at this stage. */
  	return 0;
  }
  
  ```

  这里的*__setup_start*，是链接脚本中的变量，该变量是段*.init.setup*的起始地址，*__setup_end*是*.init.setup*段的结束地址，`out/s9863a1h10/obj/kernel/arch/arm64/kernel/vmlinux.lds`中定义如下：

  ```c
  . = ALIGN(16); __setup_start = .; KEEP(*(.init.setup)) __setup_end = .;
  
  ```

  *do_early_param*函数的 for 循环中，从*.init.setup*段中，依次将*obs_kernel_param*结构体变量取出来，如果变量中的 early 为 1，并且变量中的str，和函数的参数一致，那么调用结构体中的setup_func函数。

  在之前，*__setup_param_setup_earlycon*变量，是定义在*.init.setup*段。如下图所示。    ![image-20200108095113963](/home/haibin.xu/haibin/doc/picture/console初始化-1.png)

  因为*cmdline*中，传递了*earlycon*参数，匹配*__setup_param_setup_earlycon*中的*earlycon*,因此执行*param_setup_earlycon*函数。

  *param_setup_earlycon*函数定义在`kernel/kernel4.14/drivers/tty/serial/earlycon.c`中，如下：

  ```c
  /* early_param wrapper for setup_earlycon() */
  static int __init param_setup_earlycon(char *buf)
  {
  	int err;
  
  	/*
  	 * Just 'earlycon' is a valid param for devicetree earlycons;
  	 * don't generate a warning from parse_early_params() in that case
  	 */
  	pr_info("Haibin earlycon buf: %s. %lx.\n", buf, buf);
  	if (!buf || !buf[0]) {
  		if (IS_ENABLED(CONFIG_ACPI_SPCR_TABLE)) {
  			earlycon_init_is_deferred = true;
  			return 0;
  		} else if (!buf) {
  			return early_init_dt_scan_chosen_stdout();
  		}
  	}
  
  	err = setup_earlycon(buf);
  	if (err == -ENOENT || err == -EALREADY)
  		return 0;
  	return err;
  }
  
  ```

  该函数调用*setup_earlycon*函数，对于*setup_earlycon*函数，参数*buf*是*cmdline*的参数值。在这里是*earlycon=sprd_serial,0x70100000,115200n8*。实现如下：

  ```c
  int __init setup_earlycon(char *buf)
  {
  	const struct earlycon_id **p_match;
  
  	if (!buf || !buf[0])
  		return -EINVAL;
  
  	if (early_con.flags & CON_ENABLED)
  		return -EALREADY;
  
  	for (p_match = __earlycon_table; p_match < __earlycon_table_end;
  	     p_match++) {
  		const struct earlycon_id *match = *p_match;
  		size_t len = strlen(match->name);
  
  		if (strncmp(buf, match->name, len))
  			continue;
  
  		if (buf[len]) {
  			if (buf[len] != ',')
  				continue;
  			buf += len + 1;
  		} else
  			buf = NULL;
  
  		return register_earlycon(buf, match);
  	}
  
  	return -ENOENT;
  }
  
  ```

  遍历*__earlycon_table*开始的*earlycon_id*类型的变量。对于*_earlycon_table*，是定义在链接脚本中，保存*__early_table*段的起始地址。

  ```
  __early_table = .; *(__early_table) *(__earlycon_table_end) . = ALIGN(8)
  
  ```



- 在之前，有定义*_earlycon_sprd_serial*变量，并且，放在了*__early_table*段中。*cmdline*传的参数是*earlycon=sprd_serial,0x70100000,115200n8*，逗号之前的*sprd_serial*和*_earlycon_sprd_serial*变量中的*sprd_serial*匹配，因此执行*register_earlycon*函数。该函数的2个参数，buf，是*0x70100000,115200n8*，match是*_earlycon_sprd_serial*变量的指针。

  ```c
  static int __init register_earlycon(char *buf, const struct earlycon_id *match)
  {
  	int err;
  	struct uart_port *port = &early_console_dev.port;
  
      /* On parsing error, pass the options buf to the setup function */
  	if (buf && !parse_options(&early_console_dev, buf))
  		buf = NULL;
  
  	spin_lock_init(&port->lock);
  	port->uartclk = BASE_BAUD * 16;
  	if (port->mapbase)
  		port->membase = earlycon_map(port->mapbase, 64);
  
  	earlycon_init(&early_console_dev, match->name);
  	err = match->setup(&early_console_dev, buf);
  	if (err < 0)
  		return err;
  	if (!early_console_dev.con->write)
  		return -ENODEV;
  
  	register_console(early_console_dev.con);
  	return 0;
  }
  
  ```

  最终，调用`match->setup`函数，建立`earlycon`，其实就是调用*sprd_early_console_setup*，其在`kernel/kernel4.14/drivers/tty/serial/sprd_serial.c`定义如下：

  ```c
  static int __init sprd_early_console_setup(struct earlycon_device *device,
  					   const char *opt)
  {
  	if (!device->port.membase)
  		return -ENODEV;
  
  	device->con->write = sprd_early_write;
  
  	return 0;
  }
  
  ```

  其实就是将设置*write*函数指针为*sprd_early_write*。这样，在*kernel*未建立*console*之前，使用*printk*打印的信息，最终是调用*sprd_early_write*函数输出了。



## 2. printk的实现过程

- 通过*earlycon*机制，我们了解到在*kernel*未建立*console*之前，*printk*打印的信息是通过earlycon机制输出。

- 而在未初始化*earlycon*之前，*printk*打印的信息，其实是没有打印出来的，打印信息保存在内部的缓冲区，等待*earlycon*建立好后，缓冲区的信息才被打印出来。

- 技术文章参考：

  https://blog.csdn.net/qq_16777851/article/details/89715519

  https://blog.csdn.net/W1107101310/article/details/80526039

  https://blog.csdn.net/databuser/article/details/78885715

  

### 2.1 printk函数原型

- `bsp/kernel/kernel4.14/kernel/printk/printk.c`：

  ```c
  /**
   * printk - print a kernel message
   * @fmt: format string
   *
   * This is printk(). It can be called from any context. We want it to work.
   *
   * We try to grab the console_lock. If we succeed, it's easy - we log the
   * output and call the console drivers.  If we fail to get the semaphore, we
   * place the output into the log buffer and return. The current holder of
   * the console_sem will notice the new output in console_unlock(); and will
   * send it to the consoles before releasing the lock.
   *
   * One effect of this deferred printing is that code which calls printk() and
   * then changes console_loglevel may break. This is because console_loglevel
   * is inspected when the actual printing occurs.
   *
   * See also:
   * printf(3)
   *
   * See the vsnprintf() documentation for format string extensions over C99.
   */
  asmlinkage __visible int printk(const char *fmt, ...)
  {
  	va_list args;
  	int r;
  
  	va_start(args, fmt);
  	r = vprintk_func(fmt, args);
  	va_end(args);
  
  	return r;
  }
  EXPORT_SYMBOL(printk);
  
  ```

- 通过*printk*的注释我们可以看到以下几个特点：

  > 它可以从任何上下文中调用。
  >
  > 首先尝试获取*console_lock*。 如果成功，则记录输出并调用控制台驱动程序。
  >
  > 如果无法获得信号量，我们将输出放入日志缓冲区并返回。
  >
  > 控制台信号量的当前持有者*console_sem*会注意到*console_unlock*中的新输出;
  >
  > 还会在释放锁之前将其发送到控制台。
  
- 可变参数函数原型

  从*printk*函数原型可知，*printk*除了接收一个固定参数*fmt*外，后面的参数用*...*表示。在*C/C++*语言中，*...*表示可以接收可变数量的参数（0或0个以上参数）。

- 函数参数传递方式

  `Printk`的参数通过栈来传递，在`C/C++`中，函数默认调用方式是`_cdecl`，表示由调用者管理参数入栈操作，且入栈顺序为从右至左，入栈方向为从高地址到低地址。因此，从第n个到第1个参数被放在地址递减的栈中。假设现在有一段代码如下所示：

  ```c
  int a = 0x12345678;
  char b = 2;
  char *c = "hello";
  
  printk("print %d, %d, %s\n", a, b, c); 
  
  ```

  那么调用`printk`时参数在栈中的分布如下图所示，这里假设"print  %d,  %d,   %s\n"字符串的首地址是`0x20000000`，"hello"字符串的首地址是`0x10000000`。从图中还能看出一个有意思的地方，那就是参数b虽然是1个字节，但是压栈时被扩展为4字节数据，高位补0。也就是说每次压栈的数据最少为4字节，不足4字节的数据补0。                       ![image-20200121101950270](/home/haibin.xu/haibin/doc/picture/图1.1 Printk参数在栈中的分布.png)

- 可变参数操作宏

  *printk*函数中，*va_list*定义如下，其实就是一个char型指针：

  ```c
  typedef char *va_list; 
  
  ```

  *va_start*宏定义如下，*AP*表示*argument pointer*，是参数指针的意思，其实就是*va_list*类型变量；*LASTARG*表示*last argument*，其实就是*printk*的第一个参数*fmt*，之所以叫*last argument*，是因为这个参数是最后一个压栈的。*__va_rounded_size*的作用是按*int*类型的倍数计算*TYPE*变量在栈中的大小，假设*TYPE*变量是5字节大小，则*__va_rounded_size(TYPE)*值为8，因为每次压栈的数据大小都是*int*类型数据大小的倍数。

  ```c
  #define __va_rounded_size(TYPE) \
  (((sizeof (TYPE) + sizeof (int) - 1) / sizeof (int)) * sizeof (int))
  
  #define va_start(AP, LASTARG) \
  (AP = ((char *) &(LASTARG) + __va_rounded_size (LASTARG))) 
  
  ```

  `(char *) &(LASTARG)`表示将fmt变量的地址转为`char *`指针，这样加上`__va_rounded_size (LASTARG)`后的值就是第一个可变参数的地址。如下图所示：![image-20200121110432658](/home/haibin.xu/haibin/doc/picture/图1.2 va_list args移动示意图.png)

  由此可见，`va_start`宏的作用就是将指针`args`跳过`fmt`参数，指向第一个要解析的可变参数。

- `va_end`是一个空的宏。

### 2.2 vprintk_func函数

- `bsp/kernel/kernel4.14/kernel/printk/printk_safe.c`，*printk()->vprintk_func()*

  ```c
  __printf(1, 0) int vprintk_func(const char *fmt, va_list args)
  {
  	/*
  	 * Try to use the main logbuf even in NMI. But avoid calling console
  	 * drivers that might have their own locks.
  	 */
  	if ((this_cpu_read(printk_context) & PRINTK_NMI_DIRECT_CONTEXT_MASK) &&
  	    raw_spin_trylock(&logbuf_lock)) {
  		int len;
  
  		len = vprintk_store(0, LOGLEVEL_DEFAULT, NULL, 0, fmt, args);
  		raw_spin_unlock(&logbuf_lock);
  		defer_console_output();
  		return len;
  	}
  
  	/* Use extra buffer in NMI when logbuf_lock is taken or in safe mode. */
  	if (this_cpu_read(printk_context) & PRINTK_NMI_CONTEXT_MASK)
  		return vprintk_nmi(fmt, args);
  
  	/* Use extra buffer to prevent a recursion deadlock in safe mode. */
  	if (this_cpu_read(printk_context) & PRINTK_SAFE_CONTEXT_MASK)
  		return vprintk_safe(fmt, args);
  
  	/* No obstacles. */
  	return vprintk_default(fmt, args);
  }
  
  ```

- 可以看到，这个实现中判断了多种上下文（*PRINTK_NMI_DIRECT_CONTEXT_MASK、PRINTK_NMI_CONTEXT_MASK、PRINTK_SAFE_CONTEXT_MASK*），就像*printk*注释中所述，能够获取*console_lock*，表示现在可以直接打印，如果不能获取，那就放入缓冲区，待上一次的*console_unlock*的时候会输出缓冲区的内容。

- 这里我们以最常见的默认情况来分析, 即*vprintk_default*。

### 2.3 vprintk_default函数

- `bsp/kernel/kernel4.14/kernel/printk/printk.c`，*vprintk_func()->vprintk_default()*

  ```c
  int vprintk_default(const char *fmt, va_list args)
  {
  	int r;
  
  #ifdef CONFIG_KGDB_KDB
  	/* Allow to pass printk() to kdb but avoid a recursion. */
  	if (unlikely(kdb_trap_printk && kdb_printf_cpu < 0)) {
  		r = vkdb_printf(KDB_MSGSRC_PRINTK, fmt, args);
  		return r;
  	}
  #endif
  	r = vprintk_emit(0, LOGLEVEL_DEFAULT, NULL, 0, fmt, args);
  
  	return r;
  }
  EXPORT_SYMBOL_GPL(vprintk_default);
  
  ```

### 2.3.1 printk日志级别

- *vprintk_default*函数中有提到*LOGLEVEL_DEFAULT*，这是日志级别，所以我们需要讲一下*printk*打印等级。

  `bsp/kernel/kernel4.14/include/linux/kern_levels.h`

  ```c
  /* integer equivalents of KERN_<LEVEL> */
  #define LOGLEVEL_SCHED		-2	/* Deferred messages from sched code
  					 * are set to this special level */
  #define LOGLEVEL_DEFAULT	-1	/* default (or last) loglevel */
  #define LOGLEVEL_EMERG		0	/* system is unusable */
  #define LOGLEVEL_ALERT		1	/* action must be taken immediately */
  #define LOGLEVEL_CRIT		2	/* critical conditions */
  #define LOGLEVEL_ERR		3	/* error conditions */
  #define LOGLEVEL_WARNING	4	/* warning conditions */
  #define LOGLEVEL_NOTICE		5	/* normal but significant condition */
  #define LOGLEVEL_INFO		6	/* informational */
  #define LOGLEVEL_DEBUG		7	/* debug-level messages */
  
  ```

  使用时，我们通常使用下面这几个，内核中一共有8种级别，`bsp/kernel/kernel4.14/include/linux/kern_levels.h`：

  ```c
  #define KERN_EMERG	KERN_SOH "0"	/* system is unusable */
  #define KERN_ALERT	KERN_SOH "1"	/* action must be taken immediately */
  #define KERN_CRIT	KERN_SOH "2"	/* critical conditions */
  #define KERN_ERR	KERN_SOH "3"	/* error conditions */
  #define KERN_WARNING	KERN_SOH "4"	/* warning conditions */
  #define KERN_NOTICE	KERN_SOH "5"	/* normal but significant condition */
  #define KERN_INFO	KERN_SOH "6"	/* informational */
  #define KERN_DEBUG	KERN_SOH "7"	/* debug-level messages */
  
  #define KERN_DEFAULT	KERN_SOH "d"	/* the default kernel loglevel */
  
  ```

  *printk*日志级别使用方法如下：

  ```c
  printk(KERN_INFO "Serial: 21285 driver\n");
  printk(KERN_ERR "CRC mismatch\n");
  
  ```

  首先是打印的日志级别，其后是我们要输出的日志信息，*printk*与*printf*的一个很大的区别，那就是*printk*有日志级别，而我们会在后面根据日志的级别来判断他的日志信息是否可以输出。当然这要在之后的代码分析中介绍。

- *logbuff_printk*函数，`bsp/bootloader/u-boot15/common/cmd_log.c`

  ```c
  static int logbuff_printk(const char *line)
  {
  	...
  	for (p = buf + 3; p < buf_end; p++) {
  		msg = p;
  		if (msg_level < 0) {
  			if (
  				p[0] != '<' ||
  				p[1] < '0' ||
  				p[1] > '7' ||
  				p[2] != '>'
  			) {
  				p -= 3;
  				p[0] = '<';
  				p[1] = default_message_loglevel + '0';
  				p[2] = '>';
  			} else {
  				msg += 3;
  			}
  			msg_level = p[1] - '0';
  		}
  		...
  	}
  	return i;
  }
  
  ```

  当包含日志信息的级别时，我们会将这个级别记录，而当没有日志信息级别时，会为该信息设一个默认的日志级别：*default_message_loglevel*，`bsp/kernel/kernel4.14/include/linux/printk.h`

  ```c
  #define default_message_loglevel (console_printk[1])
  
  ```

  `bsp/kernel/kernel4.14/kernel/printk/printk.c`

  ```c
  int console_printk[4] = {
    	CONSOLE_LOGLEVEL_DEFAULT,	/* console_loglevel */
    	MESSAGE_LOGLEVEL_DEFAULT,	/* default_message_loglevel */
    	CONSOLE_LOGLEVEL_MIN,		/* minimum_console_loglevel */
    	CONSOLE_LOGLEVEL_DEFAULT,	/* default_console_loglevel */
  };
  
  ```

  `bsp/kernel/kernel4.14/include/linux/printk.h`

  ```c
  #define MESSAGE_LOGLEVEL_DEFAULT CONFIG_MESSAGE_LOGLEVEL_DEFAULT
  
  ```

  `bsp/kernel/kernel4.14/arch/arm64/configs/sprd_sharkl3_defconfig`

  ```c
  CONFIG_MESSAGE_LOGLEVEL_DEFAULT=4
  
  ```

  从上面我们可以看出，默认的日志级别为4。

### 2.3.2 vprintk_emit函数

- 我们继续分析*vprintk_default*函数, *vprintk_default()->vprintk_emit()*，`bsp/kernel/kernel4.14/kernel/printk/printk.c`

  ```c
  asmlinkage int vprintk_emit(int facility, int level,
  			    const char *dict, size_t dictlen,
  			    const char *fmt, va_list args)
  {
  	int printed_len;
  	bool in_sched = false;
  	unsigned long flags;
  
      /*
       * 默认打印等级处理
       */
  	if (level == LOGLEVEL_SCHED) {
  		level = LOGLEVEL_DEFAULT;
  		in_sched = true;
  	}
  
      /*
       * 有些console打印比较慢，所以要延迟等前一个打印完再继续打印
       */
  	boot_delay_msec(level);
  	printk_delay();
  
  	/* This stops the holder of console_sem just where we want him */
  	logbuf_lock_irqsave(flags);
      /*
       * 格式化处理数据
       */
  	printed_len = vprintk_store(facility, level, dict, dictlen, fmt, args);
  	logbuf_unlock_irqrestore(flags);
  
  	/* If called from the scheduler, we can not call up(). */
      /*
       * 如果不是在调度函数，那就可以直接打印，否则就其他时候打印
       */
  	if (!in_sched) {
  		/*
  		 * Disable preemption to avoid being preempted while holding
  		 * console_sem which would prevent anyone from printing to
  		 * console
  		 */
          /* 禁止内核抢占 */
  		preempt_disable();
  		/*
  		 * Try to acquire and then immediately release the console
		 * semaphore.  The release will print out buffers and wake up
  		 * /dev/kmsg and syslog() users.
  		 */
  		if (console_trylock_spinning())
  			console_unlock();
  		preempt_enable();
  	}
  
  	return printed_len;
  }
  EXPORT_SYMBOL(vprintk_emit);
  
  ```

- *vprintk_emit()->vprintk_store()*，`bsp/kernel/kernel4.14/kernel/printk/printk.c`，内核定义了992个字节的缓冲区，用来保存*printk*的打印字符。

  ```c
  #define PREFIX_MAX		32
  #define LOG_LINE_MAX		(1024 - PREFIX_MAX)
  
  /* Must be called under logbuf_lock. */
  int vprintk_store(int facility, int level,
  		  const char *dict, size_t dictlen,
  		  const char *fmt, va_list args)
  {
  	static char textbuf[LOG_LINE_MAX];
  	char *text = textbuf;
  	size_t text_len;
  	enum log_flags lflags = 0;
  
  	/*
  	 * The printf needs to come first; we need the syslog
  	 * prefix which might be passed-in as a parameter.
  	 */
      /*处理前面的syslog信息，将输出信息放到textbuf中，并返回放入字符的个数*/
  	text_len = vscnprintf(text, sizeof(textbuf), fmt, args);
  
  	/* mark and strip a trailing newline */
      /* 标记并删除换行符 */
  	if (text_len && text[text_len-1] == '\n') {
  		text_len--;
  		lflags |= LOG_NEWLINE;
  	}
  
  	/* strip kernel syslog prefix and extract log level or control flags */
      /* 剥离内核syslog前缀，并提取日志级别或控制标志 */
  	if (facility == 0) {
  		int kern_level;
  
  		while ((kern_level = printk_get_level(text)) != 0) {
  			switch (kern_level) {
  			case '0' ... '7':
  				if (level == LOGLEVEL_DEFAULT) /* 将打印等级转换成数字 */
  					level = kern_level - '0';
  				/* fallthrough */
  			case 'd':	/* KERN_DEFAULT */
  				lflags |= LOG_PREFIX; /* 默认等级，即printk后面直接跟着要打印的东西 */
  				break;
  			case 'c':	/* KERN_CONT */
  				lflags |= LOG_CONT; /* 分段标志 */
  			}
  
  			text_len -= 2;
  			text += 2;
  		}
  	}
  
  	if (level == LOGLEVEL_DEFAULT)
  		level = default_message_loglevel; /* 默认等级,使用默认处理函数 */
  
  	if (dict)
  		lflags |= LOG_PREFIX|LOG_NEWLINE; /* 打印标志 */
  
  	return log_output(facility, level, lflags,
  			  dict, dictlen, text, text_len);
  }
  
  ```

- *vprintk_store()->log_output()*，`bsp/kernel/kernel4.14/kernel/printk/printk.c`，

  ```c
  /*
   * Continuation lines are buffered, and not committed to the record buffer
   * until the line is complete, or a race forces it. The line fragments
   * though, are printed immediately to the consoles to ensure everything has
   * reached the console in case of a kernel crash.
   */
  static struct cont {
  	char buf[LOG_LINE_MAX];
  	size_t len;			/* length == 0 means unused buffer */
  	struct task_struct *owner;	/* task of first print*/
  	u64 ts_nsec;			/* time of first print */
  	u8 level;			/* log level of first message */
  	u8 facility;			/* log facility of first message */
  	enum log_flags flags;		/* prefix, newline flags */
  	u32 cpu;			/* the print cpu */
  } cont;
  
  static size_t log_output(int facility, int level, enum log_flags lflags, const char *dict, size_t dictlen, char *text, size_t text_len)
  {
  	/*
  	 * If an earlier line was buffered, and we're a continuation
  	 * write from the same process, try to add it to the buffer.
  	 */
      /* 如果缓冲了较早的行，并且是来自同一进程的继续写入，则尝试将其添加到缓冲区。 */
  	if (cont.len) {
  		if (cont.owner == current && (lflags & LOG_CONT)) {
  			if (cont_add(facility, level, lflags, text, text_len))
  				return text_len;
  		}
  		/* Otherwise, make sure it's flushed */
  		cont_flush();
  	}
  
  	/* Skip empty continuation lines that couldn't be added - they just flush */
  	if (!text_len && (lflags & LOG_CONT))
  		return 0;
  
  	/* If it doesn't end in a newline, try to buffer the current line */
  	if (!(lflags & LOG_NEWLINE)) {
  		if (cont_add(facility, level, lflags, text, text_len))
  			return text_len;
  	}
  
  	/* Store it in the record log */
  	return log_store(facility, level, lflags, 0, dict, dictlen, text, text_len, smp_processor_id());
  }
  
  ```

  *log_output()*函数主要是对一些标志位处理，以及待缓冲区接近溢出时，把打印信息放到其他缓冲区或者把该缓冲区等待刷新完再继续执行。刷新函数