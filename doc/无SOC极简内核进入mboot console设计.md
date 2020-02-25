# 无Soc极简内核进入mboot console设计

## 1. 无Soc极简内核

- 在新建Board或是内核升级的情况下，特别是在不清楚dts配置的的情况下，此时，通过极简内核来进入mboot console模式，并在此模式下进行开发，这是极为需要，这一方面节省了等待各模块对dts配置的时间，另一方面，又不影响开发的进度，这在日常项目开发工作中，是极为有利的。

- 极简内核主要体现在dts配置上，我们以linux5.4版本下添加sharkl3最简dts配置来展示最简内核的dts配置情况。

  - `arch/arm64/boot/dts/sprd/sp9863a-1h10.dts`

    ```dts
    // SPDX-License-Identifier: (GPL-2.0+ OR MIT)
    /*
     * Spreadtrum Sharkl3 platform DTS file
     *
     * Copyright (C) 2018, Spreadtrum Communications Inc.
     */
     
    /dts-v1/;
     
    #include "sc9863a.dtsi"
     
    / {
        model = "Spreadtrum SC9863A-1H10 Board";
     
        compatible = "sprd,sp9863a-1h10", "sprd,sc9863a";
     
        sprd,sc-id = <9863 1 0x20000>;
     
        #address-cells = <2>;
        #size-cells = <2>;
     
        memory: memory {
            device_type = "memory";
            reg = <0x0 0x80000000 0x0 0x80000000>;
        };
     
        chosen {
            bootargs = "earlycon=sprd_serial,0x70100000,115200n8 keep_bootcon printk.devkmsg=on loglevel=8 init=/init root=/dev/ram0 rw";
            // bootargs = "earlycon=sprd_serial,0x70100000,115200n8 console=ttyS1,115200n8 printk.devkmsg=on loglevel=8 init=/init root=/dev/ram0 rw";
        };
    };
    ```

  - `arch/arm64/boot/dts/sprd/sc9863a.dtsi`

    ```dts
    // SPDX-License-Identifier: (GPL-2.0+ OR MIT)
    /*
     * Spreadtrum Sharkl3 platform DTS file
     *
     * Copyright (C) 2018, Spreadtrum Communications Inc.
     */
     
    #include <dt-bindings/interrupt-controller/arm-gic.h>
    #include "sharkl3.dtsi"
     
    / {
        cpuinfo_hardware = "Unisoc SC9863a";
     
        cpus {
            #address-cells = <2>;
            #size-cells = <0>;
     
            cpu-map {
                cluster0 {
                    core0 {
                        cpu = <&CPU0>;
                    };
                    core1 {
                        cpu = <&CPU1>;
                    };
                    core2 {
                        cpu = <&CPU2>;
                    };
                    core3 {
                        cpu = <&CPU3>;
                    };
                };
     
                cluster1 {
                    core0 {
                        cpu = <&CPU4>;
                    };
                    core1 {
                        cpu = <&CPU5>;
                    };
                    core2 {
                        cpu = <&CPU6>;
                    };
                    core3 {
                        cpu = <&CPU7>;
                    };
                };
            };
     
            CPU0: cpu@0 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x0>;
                enable-method = "psci";
            };
     
            CPU1: cpu@100 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x100>;
                enable-method = "psci";
            };
     
            CPU2: cpu@200 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x200>;
                enable-method = "psci";
            };
     
            CPU3: cpu@300 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x300>;
                enable-method = "psci";
            };
     
            CPU4: cpu@400 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x400>;
                enable-method = "psci";
            };
     
            CPU5: cpu@500 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x500>;
                enable-method = "psci";
            };
     
            CPU6: cpu@600 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x600>;
                enable-method = "psci";
            };
     
            CPU7: cpu@700 {
                device_type = "cpu";
                compatible = "arm,cortex-a55","arm,armv8";
                reg = <0x0 0x700>;
                enable-method = "psci";
            };
        };
     
        gic: interrupt-controller@14000000 {
            compatible = "arm,gic-v3";
            #interrupt-cells = <3>;
            #address-cells = <2>;
            #size-cells = <2>;
            ranges;
            redistributor-stride = <0x0 0x20000>;   /* 128KB stride */
            #redistributor-regions = <1>;
            interrupt-controller;
            reg = <0x0 0x14000000 0 0x20000>,   /* GICD */
                <0x0 0x14040000 0 0x100000>;    /* GICR */
            interrupts = <1 9 4>;
            v2m_0: v2m@0 {
                compatible = "arm,gic-v2m-frame";
                msi-controller;
                reg = <0 0 0 0x1000>;
            };
        };
     
        psci {
            compatible = "arm,psci-0.2";
            method = "smc";
        };
     
        timer {
            compatible = "arm,armv8-timer";
            interrupts = <GIC_PPI 13 IRQ_TYPE_LEVEL_HIGH>, /* Physical Secure PPI */
                     <GIC_PPI 14 IRQ_TYPE_LEVEL_HIGH>, /* Physical Non-Secure PPI */
                     <GIC_PPI 11 IRQ_TYPE_LEVEL_HIGH>, /* Virtual PPI */
                     <GIC_PPI 10 IRQ_TYPE_LEVEL_HIGH>; /* Hipervisor PPI */
            arm,no-tick-in-suspend;
        };
    };
    ```

  - `arch/arm64/boot/dts/sprd/sharkl3.dtsi`

    ```dts
    // SPDX-License-Identifier: (GPL-2.0+ OR MIT)
    /*
     * Spreadtrum Sharkl3 platform DTS file
     *
     * Copyright (C) 2018, Spreadtrum Communications Inc.
     */
    / {
        interrupt-parent = <&gic>;
        #address-cells = <2>;
        #size-cells = <2>;
    };
    ```

- 最简dts配置情况下，内核启动效果：

  ```log
  [    0.000000] Booting Linux on physical CPU 0x0000000000 [0x411fd050]
  [    0.000000] Linux version 5.4.0-rc8-00024-gf838605 (xixin.liu@tjand03) 
  (Android (5484270 based on r353983c) 
  clang version 9.0.3 (https://android.googlesource.com/toolchain/clang 
  745b335211bb9eadfa6aa6301f84715cee4b37c5) 
  (https://android.googlesource.com/toolchain/llvm 
  60cf23e54e46c807513f7a36d0a7b777920b5881) 
  (based on LLVM 9.0.3svn)) #5 SMP PREEMPT Sun Dec 15 17:10:02 CST 2019
  [    0.000000] Machine model: Spreadtrum SC9863A-1H10 Board
  [    0.000000] earlycon: sprd_serial0 at MMIO 0x0000000070100000 (options '115200n8')
  [    0.000000] printk: bootconsole [sprd_serial0] enabled
  [    0.000000] printk: debug: skip boot console de-registration.
  [    0.000000] efi: Getting EFI parameters from FDT:
  [    0.000000] efi: UEFI not found.
  [    0.000000] On node 0 totalpages: 524288
  [    0.000000]   DMA32 zone: 8192 pages used for memmap
  [    0.000000]   DMA32 zone: 0 pages reserved
  [    0.000000]   DMA32 zone: 524288 pages, LIFO batch:63
  [    0.000000] psci: probing for conduit method from DT.
  [    0.000000] psci: PSCIv1.0 detected in firmware.
  [    0.000000] psci: Using standard PSCI v0.2 function IDs
  [    0.000000] psci: MIGRATE_INFO_TYPE not supported.
  [    0.000000] psci: SMC Calling Convention v1.0
  [    0.000000] percpu: Embedded 29 pages/cpu s81152 r8192 d29440 u118784
  [    0.000000] pcpu-alloc: s81152 r8192 d29440 u118784 alloc=29*4096
  [    0.000000] pcpu-alloc: [0] 0 [0] 1 [0] 2 [0] 3 [0] 4 [0] 5 [0] 6 [0] 7 
  [    0.000000] Detected VIPT I-cache on CPU0
  [    0.000000] CPU features: detected: GIC system register CPU interface
  [    0.000000] CPU features: detected: Virtualization Host Extensions
  [    0.000000] alternatives: patching kernel code
  [    0.000000] Built 1 zonelists, mobility grouping on.  Total pages: 516096
  [    0.000000] Kernel command line: earlycon=sprd_serial,0x70100000,115200n8 keep_bootcon 
  printk.devkmsg=on loglevel=8 init=/init root=/dev/ram0 rw
  [    0.000000] Dentry cache hash table entries: 262144 (order: 9, 2097152 bytes, linear)
  [    0.000000] Inode-cache hash table entries: 131072 (order: 8, 1048576 bytes, linear)
  [    0.000000] mem auto-init: stack:off, heap alloc:off, heap free:off
  [    0.000000] Memory: 2040524K/2097152K available 
  (5820K kernel code, 876K rwdata, 2232K rodata, 2496K init, 732K bss, 56628K reserved, 0K cma-reserved)
  [    0.000000] SLUB: HWalign=64, Order=0-3, MinObjects=0, CPUs=8, Nodes=1
  [    0.000000] ftrace: allocating 22286 entries in 88 pages
  [    0.000000] rcu: Preemptible hierarchical RCU implementation.
  [    0.000000] rcu:     RCU restricting CPUs from NR_CPUS=256 to nr_cpu_ids=8.
  [    0.000000]  Tasks RCU enabled.
  [    0.000000] rcu: RCU calculated value of scheduler-enlistment delay is 25 jiffies.
  [    0.000000] rcu: Adjusting geometry for rcu_fanout_leaf=16, nr_cpu_ids=8
  [    0.000000] NR_IRQS: 64, nr_irqs: 64, preallocated irqs: 0
  [    0.000000] GICv3: GIC: Using split EOI/Deactivate mode
  [    0.000000] GICv3: 192 SPIs implemented
  [    0.000000] GICv3: 0 Extended SPIs implemented
  [    0.000000] GICv3: Distributor has no Range Selector support
  [    0.000000] GICv3: 16 PPIs implemented
  [    0.000000] GICv3: no VLPI support, no direct LPI support
  [    0.000000] GICv3: CPU0: found redistributor 0 region 0:0x0000000014040000
  [    0.000000] random: get_random_bytes called from start_kernel+0x1e0/0x398 with crng_init=0
  [    0.000000] arch_timer: cp15 timer(s) running at 26.00MHz (phys).
  [    0.000000] clocksource: arch_sys_counter: mask: 0xffffffffffffff max_cycles: 0x5ff13d5a9, max_idle_ns: 440795202370 ns
  [    0.000004] sched_clock: 56 bits at 26MHz, resolution 38ns, wraps every 4398046511088ns
  [    0.008062] CPU0: Unknown IPI message 0xd
  [    0.012068] Console: colour dummy device 80x25
  [    0.016506] printk: console [tty0] enabled
  [    0.020609] Calibrating delay loop (skipped), value calculated using timer frequency.. 52.00 BogoMIPS (lpj=104000)
  [    0.030909] pid_max: default: 32768 minimum: 301
  [    0.035619] LSM: Security Framework initializing
  [    0.040228] Mount-cache hash table entries: 4096 (order: 3, 32768 bytes, linear)
  [    0.047565] Mountpoint-cache hash table entries: 4096 (order: 3, 32768 bytes, linear)
  [    0.079411] ASID allocator initialised with 32768 entries
  [    0.092783] rcu: Hierarchical SRCU implementation.
  [    0.106063] EFI services will not be available.
  [    0.122498] smp: Bringing up secondary CPUs ...
  [    0.159446] Detected VIPT I-cache on CPU1
  [    0.159486] GICv3: CPU1: found redistributor 100 region 0:0x0000000014060000
  [    0.159530] CPU1: Booted secondary processor 0x0000000100 [0x411fd050]
  [    0.191512] Detected VIPT I-cache on CPU2
  [    0.191537] GICv3: CPU2: found redistributor 200 region 0:0x0000000014080000
  [    0.191577] CPU2: Booted secondary processor 0x0000000200 [0x411fd050]
  [    0.223600] Detected VIPT I-cache on CPU3
  [    0.223625] GICv3: CPU3: found redistributor 300 region 0:0x00000000140a0000
  [    0.223662] CPU3: Booted secondary processor 0x0000000300 [0x411fd050]
  [    0.255694] Detected VIPT I-cache on CPU4
  [    0.255714] GICv3: CPU4: found redistributor 400 region 0:0x00000000140c0000
  [    0.255746] CPU4: Booted secondary processor 0x0000000400 [0x411fd050]
  [    0.287791] Detected VIPT I-cache on CPU5
  [    0.287810] GICv3: CPU5: found redistributor 500 region 0:0x00000000140e0000
  [    0.287842] CPU5: Booted secondary processor 0x0000000500 [0x411fd050]
  [    0.319880] Detected VIPT I-cache on CPU6
  [    0.319900] GICv3: CPU6: found redistributor 600 region 0:0x0000000014100000
  [    0.319931] CPU6: Booted secondary processor 0x0000000600 [0x411fd050]
  [    0.351982] Detected VIPT I-cache on CPU7
  [    0.352003] GICv3: CPU7: found redistributor 700 region 0:0x0000000014120000
  [    0.352034] CPU7: Booted secondary processor 0x0000000700 [0x411fd050]
  [    0.352164] smp: Brought up 1 node, 8 CPUs
  [    0.478911] SMP: Total of 8 processors activated.
  [    0.483513] CPU features: detected: Privileged Access Never
  [    0.489066] CPU features: detected: User Access Override
  [    0.494446] CPU features: detected: 32-bit EL0 Support
  [    0.499567] CPU features: detected: Common not Private translations
  [    0.505730] CPU features: detected: RAS Extension Support
  [    0.511110] CPU features: detected: Data cache clean to the PoU not required for I/D coherence
  [    0.519703] CPU features: detected: CRC32 instructions
  [    0.524912] CPU: All CPU(s) started at EL2
  [    0.530736] devtmpfs: initialized
  [    0.535758] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 7645041785100000 ns
  [    0.545371] futex hash table entries: 2048 (order: 5, 131072 bytes, linear)
  [    0.553108] DMI not present or invalid.
  [    0.557071] NET: Registered protocol family 16
  [    0.561981] DMA: preallocated 256 KiB pool for atomic allocations
  [    0.568288] cpuidle: using governor menu
  [    0.572272] hw-breakpoint: found 6 breakpoint and 4 watchpoint registers.
  [    0.579303] Serial: AMBA PL011 UART driver
  [    0.589145] HugeTLB registered 1.00 GiB page size, pre-allocated 0 pages
  [    0.595793] HugeTLB registered 32.0 MiB page size, pre-allocated 0 pages
  [    0.602463] HugeTLB registered 2.00 MiB page size, pre-allocated 0 pages
  [    0.609144] HugeTLB registered 64.0 KiB page size, pre-allocated 0 pages
  [    0.622324] cryptd: max_cpu_qlen set to 1000
  [    0.634978] SCSI subsystem initialized
  [    0.638850] EDAC MC: Ver: 3.0.0
  [    0.642971] clocksource: Switched to clocksource arch_sys_counter
  [    0.731296] VFS: Disk quotas dquot_6.6.0
  [    0.735229] VFS: Dquot-cache hash table entries: 512 (order 0, 4096 bytes)
  [    0.751409] Unpacking initramfs...
  [    0.898113] Freeing initrd memory: 3336K
  [    0.921075] Initialise system trusted keyrings
  [    0.925572] workingset: timestamp_bits=46 max_order=19 bucket_order=0
  [    0.938387] fuse: init (API version 7.31)
  [    0.960413] Key type asymmetric registered
  [    0.964452] Asymmetric key parser 'x509' registered
  [    0.969349] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 252)
  [    0.976608] io scheduler mq-deadline registered
  [    0.981111] io scheduler kyber registered
  [    0.989519] Serial: 8250/16550 driver, 4 ports, IRQ sharing enabled
  [    0.997286] cacheinfo: Unable to detect cache hierarchy for CPU 0
  [    1.012612] loop: module loaded
  [    1.016011] i2c /dev entries driver
  [    1.019551] device-mapper: uevent: version 1.0.3
  [    1.024314] device-mapper: ioctl: 4.41.0-ioctl (2019-09-16) initialised: dm-devel@redhat.com
  [    1.033003] sdhci: Secure Digital Host Controller Interface driver
  [    1.039118] sdhci: Copyright(c) Pierre Ossman
  [    1.043412] Synopsys Designware Multimedia Card Interface Driver
  [    1.049459] sdhci-pltfm: SDHCI platform and OF driver helper
  [    1.055453] ledtrig-cpu: registered to indicate activity on CPUs
  [    1.062129] Loading compiled-in X.509 certificates
  [    1.067062] hctosys: unable to open rtc device (rtc0)
  [    1.075149] Freeing unused kernel memory: 2496K
  [    1.079590] Run /init as init process
  [    1.089090] mboot: FirstStageMain mount overlay super.img soon ...
  [    1.196840] random: adbd: uninitialized urandom read (40 bytes read)
  [    3.228436] init: init first stage started!
  [    3.232884] init: [libfs_mgr]ReadFstabFromDt(): failed to read fstab from dt
  [    3.240091] init: [libfs_mgr]ReadDefaultFstab(): failed to find device default fstab
  [    3.247774] init: Failed to fstab for first stage mount
  [    3.252944] init: Using Android DT directory /proc/device-tree/firmware/android/
  [    3.260710] init: [libfs_mgr]ReadDefaultFstab(): failed to find device default fstab
  [    3.268456] init: First stage mount skipped (missing/incompatible/empty fstab in device tree)
  [    3.276975] init: Skipped setting INIT_AVB_VERSION (not in recovery mode)
  [    3.284201] mboot: Switch root to /system ...
  [    3.389177] random: adbd: uninitialized urandom read (40 bytes read)
  [    7.533575] EXT4-fs (loop0): mounted filesystem with ordered data mode. Opts: (null)
  [    7.573688] init: Switching root to '/system'
  [    7.579212] init: execv("/system/bin/init") failed: No such file or directory
  [    7.588633] init: #00 pc 00000000000e8a90  /init
  [    7.593215] init: #01 pc 000000000006cd68  /init
  [    7.597796] init: #02 pc 000000000006f2dc  /init
  [    7.602394] init: #03 pc 00000000000a3044  /init
  [    7.606992] init: #04 pc 0000000000064368  /init
  [    7.611591] init: #05 pc 00000000001455c8  /init
  [    7.616187] init: Reboot ending, jumping to kernel
  [    7.621505] reboot: Restarting system with command 'bootloader'
  ERROR:   SPRD System Reset: operation not handled.
  !exception @0x00000000940003c0
  ```

  

## 2. earlycon实现流程

### 2.1 earlycon功能

- printk的log输出是由console实现，由于在kernel刚启动的过程中，还没有为串口等设备注册console（console的注册时在在device probe阶段实现），此时无法通过正常的console来输出log。

- 为此，Linux内核提供了early console机制，用于实现设备注册console之前早期log的输出，对应console也称为boot console，简称bcon。这个console在kernel启动的早期阶段就会被注册，主要通过输出设备（比如串口设备）的简单的write方法直接进行数据打印。而这个write方法也就是平台实现。

- early console机制目前主要通过earlycon的方式来实现。在earlycon中，其通过__earlycon_table维护所有的earlycon_id，通过dts中的正常console的compatible获取到所需要使用的earlycon_id，兼容性较好。并且dts获取正常console使用的uart寄存器地址来作为earlycon write实现中的uart寄存器基址，可移植性较好。

  

### 2.2 earlycon使用方法

- 打开对应宏，`arch/arm64/configs/sprd_sharkl3_defconfig`:

  ```c
  CONFIG_SERIAL_EARLYCON=y
  CONFIG_OF_EARLY_FLATTREE=y
  
  ```

  对应平台需要打开对应的earlycon_id实现的宏，我们以sharkl3平台为例，`arch/arm64/configs/sprd_sharkl3_defconfig`:

  ```c
  CONFIG_SERIAL_SPRD_CONSOLE=y
  
  ```

- 在cmdline中添加earlycon，以sharkl3为例，使用bootargs来传递cmdline，在bootargs中添加earlycon, `arch/arm64/boot/dts/sprd/sp9863a-1h10.dts`:

  ```c
  chosen {
      	stdout-path = &uart1;
          bootargs = "earlycon=sprd_serial,0x70100000,115200n8 ...";
  };
  
  ```

- 在dts中为chosen节点添加stdout-path属性，这个属性指定用作标准输入输出的dts节点路径。

- 调用printk进行打印。



### 2.3 earlycon定义

- 每个earlycon都对应一个earlycon_id，所有的earlycon_id都被维护__earlycon_table中，定义方法如下，`drivers/tty/serial/sprd_serial.c`：

  ```c
  OF_EARLYCON_DECLARE(sprd_serial, "sprd,sc9836-uart",
     		            sprd_early_console_setup);
  
  ```

  `OF_EARLYCON_DECLARE`展开如下，`include/linux/serial_core.h`：

  ```c
  #define _OF_EARLYCON_DECLARE(_name, compat, fn, unique_id)		\
    	static const struct earlycon_id unique_id			\
    	     EARLYCON_USED_OR_UNUSED __initconst			\
    		= { .name = __stringify(_name),				\
    		    .compatible = compat,				\
    		    .setup = fn  };					\
    	static const struct earlycon_id EARLYCON_USED_OR_UNUSED		\
    		__section(__earlycon_table)				\
    		* const __PASTE(__p, unique_id) = &unique_id
    
  #define OF_EARLYCON_DECLARE(_name, compat, fn)				\
    	_OF_EARLYCON_DECLARE(_name, compat, fn,				\
    			     __UNIQUE_ID(__earlycon_##_name))
  
  ```

  `sprd_serial`对应如下：

  ```c
  static const struct earlycon_id __UNIQUE_ID(earlycon_sprd_serial)			\
    	     __used __initconst			\
    		= { .name = sprd_serial,				\
    		    .compatible = "sprd,sc9836_uart",				\
    		    .setup =  sprd_early_console_setup };					\
  static const struct earlycon_id __used		\
    		__section(__earlycon_table)				\
    		* const __PASTE(__p, unique_id) = &unique_id
  
  ```

  这些`earlycon_id`都放在`__earlycon_table`中。

- `earlycon_id`定义如下,`include/linux/serial_core.h`：

  ```c
  struct earlycon_id {
    	char	name[15]; /* earlycon的名字，最终会作为相应的console的名称 */
    	char	name_term;	/* In case compiler didn't '\0' term name */
    	char	compatible[128]; /* 用于匹配uart对应的dts node */
    	int	(*setup)(struct earlycon_device *, const char *options); /* 用来为earlycon设置write函数 */
  };
  
  ```

  

### 2.4 earlycon安装

- 结构体说明

  1.  earlycon_device，`include/linux/serial_core.h`:

     ```c
     struct earlycon_device {
       	struct console *con; /* 用来网console子系统中注册console */
       	struct uart_port port; /* 对应的串口的uart_port，需要在解析earlycon的过程中设置 */
       	char options[16];		/* earlycon的参数，选项，e.g., 115200n8 */
       	unsigned int baud; /* 波特率 */
     };
     
     ```

- 解析cmdline中earlycon参数

  在`drivers/tty/serial/earlycon.c`中有如下定义：

  ```c
  early_param("earlycon", param_setup_earlycon);
  
  ```

  展开如下，定义一个变量，和一个结构体变量。结构体变量，放在.init.setup段中：

  ```c
  static const char __setup_str_param_setup_earlycon \
          __initconst	__aligned(1) = "earlycon"; 					\
  static struct obs_kernel_param __setup_param_setup_earlycon		\
    		__used __section(.init.setup)				\
    		__attribute__((aligned((sizeof(long)))))		\
    		= { "earlycon", param_setup_earlycon, 1 };
  
  ```

  `struct obs_kernel_param`定义如下：

  ```c
  struct obs_kernel_param {
    	const char *str;
    	int (*setup_func)(char *);
    	int early;
  };
  
  ```

  在init/main.c中，`start_kernel->setup_arch->parse_early_param`，通过cmdline传递的参数，进行early初始化:

  ```c
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
  
  void __init parse_early_options(char *cmdline)
  {
    	parse_args("early options", cmdline, NULL, 0, 0, 0, NULL,
    		   do_early_param);
  }
  
  ```

  调用parse_args，从cmdline中，分析early options。关键是do_early_param函数。参数param是cmdline中的参数变量以及参数值。

  ```c
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

  这里的`__setup_start`，是链接脚本中的变量，定义如下，该变量是段`.init.setup`的起始地址，`__setup_end`是`.init.setup`段的结束地址。

  ```c
  .= ALIGN(16); __setup_start = .; *(.init.setup) __setup_end = .;
  
  ```

  `do_early_param`函数的for循环中，从`.init.setup`段中，依次将`obs_kernel_param`结构体变量取出来，如果变量中的early为1，并且变量中的str和函数的参数一致，那么调用结构体中的`setup_func`函数。

  在之前，`__setup_param_setup_earlycon`变量，是定义在`.init.setup`段。如下图所示:                       ![image-20200224212426734](F:\MyNotebook\doc\picture\init_setup.png)

  因为`cmdline`中，传递了`earlycon`参数，匹配`__setup_param_setup_earlycon`中的`earlycon`,因此执行`param_setup_earlycon`函数。

- `param_setup_earlycon`函数定义，`drivers/tty/serial/earlycon.c`:

  ```c
  /* early_param wrapper for setup_earlycon() */
  static int __init param_setup_earlycon(char *buf)
  {
    	int err;
    
    	/*
    	 * Just 'earlycon' is a valid param for devicetree earlycons;
    	 * don't generate a warning from parse_early_params() in that case
    	 */
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
  early_param("earlycon", param_setup_earlycon);
  
  ```

  `param_setup_earlycon`函数调用`setup_earlycon`函数，参数buf是cmdline的参数值，在这里是`earlycon=sprd_serial,0x70100000,115200n8`：

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

  遍历`__earlycon_table`开始的`earlycon_id`类型的变量。对于`_earlycon_table`，是定义在链接脚本中，保存`__early_table`段的起始地址:

  ```c
  __early_table = .; *(__early_table) *(__earlycon_table_end) . = ALIGN(8)
  
  ```

  在之前，有定义`_earlycon_pl011`变量，并且，放在了`__early_table`段中(没有找到对应配图，此处以pl011为例):   ![image-20200224214235943](F:\MyNotebook\doc\picture\earlycon_table.png)

  `cmdline`传的参数是`earlycon=sprd_serial,0x70100000,115200n8`，参数值为`sprd_serial,0x70000000,115200n8`，逗号之前的sprd_serial和`_earlycon_sprd_serial`变量中的`sprd_serial`匹配，因此执行`register_earlycon`函数。

- `register_earlycon`函数定义如下，函数的2个参数，buf是0x70100000，match是`_earlycon_sprd_serial`变量的指针。`drivers/tty/serial/earlycon.c`:

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

  最终，调用match->setup函数，建立`earlycon`，其实就是调用`sprd_early_console_setup`。

- `sprd_early_console_setup`函数，`drivers/tty/serial/sprd_serial.c`:

  ```c
  static int __init sprd_early_console_setup(struct earlycon_device *device,
    					   const char *opt)
  {
    	if (!device->port.membase)
   		return -ENODEV;
    
    	device->con->write = sprd_early_write;
    	return 0;
  }
  OF_EARLYCON_DECLARE(sprd_serial, "sprd,sc9836-uart",
    		    sprd_early_console_setup);
  
  ```

  其实就是将设置`write`函数指针为`sprd_early_write`。这样，在`kernel`未建立`console`之前，使用`printk`打印的信息，最终是调用`sprd_early_write`函数输出了。

### 2.5 earlycon相关问题

- 在kernel未建立console之前，printk打印的信息是怎么输出？

  对于ARM64，通过earlycon机制输出。

- 在kernel未初始化earlycon之前，printk打印的信息是怎么输出？

  在未初始化earlycon之前，printk打印的信息，其实是没有打印出来的，打印信息保存在内部的缓冲区，等待earlycon建立好后，缓冲区的信息才被打印出来。

 	

## 3. console实现流程

- 上一章节介绍了early console，它是一种启动阶段前期的console，启动到后期会切换为real console。这两者都属于console，那么到底什么才是console呢？我们这里从内核的实现开始。



### 3.1 指定kernel调试console

- kernel启动时，通过解析cmdline，cmdline中包含有`console=xxx`，获取和处理指定的console参数。start_kernel中`parse_args`遍历`.init.setup`段全部`obs_kernel_param`。

- kernel通过console_setup解析console参数，参数是console=的值字符串，如“ttyS0,115200”，console_setup对console=參数值做解析，以ttyS0,115200为例，最后buf=“ttyS”，idx=0,options="115200",brl_options=NULL，`kernel/printk/printk.c`：

  ```c
    /*
     * Set up a console.  Called via do_early_param() in init/main.c
     * for each "console=" parameter in the boot command line.
     */
    static int __init console_setup(char *str)
    {
    	char buf[sizeof(console_cmdline[0].name) + 4]; /* 4 for "ttyS" */
    	char *s, *options, *brl_options = NULL;
    	int idx;
    
    	if (_braille_console_setup(&str, &brl_options))
    		return 1;
    
    	/*
    	 * Decode str into name, index, options.
    	 */
    	if (str[0] >= '0' && str[0] <= '9') {
    		strcpy(buf, "ttyS");
    		strncpy(buf + 4, str, sizeof(buf) - 5);
    	} else {
    		strncpy(buf, str, sizeof(buf) - 1);
    	}
    	buf[sizeof(buf) - 1] = 0;
    	options = strchr(str, ',');
    	if (options)
    		*(options++) = 0;
    #ifdef __sparc__
    	if (!strcmp(str, "ttya"))
    		strcpy(buf, "ttyS0");
    	if (!strcmp(str, "ttyb"))
    		strcpy(buf, "ttyS1");
    #endif
    	for (s = buf; *s; s++)
    		if (isdigit(*s) || *s == ',')
    			break;
    	idx = simple_strtoul(s, NULL, 10);
    	*s = 0;
    
    	__add_preferred_console(buf, idx, options, brl_options);
    	console_set_on_cmdline = 1;
    	return 1;
    }
    __setup("console=", console_setup);
  
  ```

- `console_setup->__add_preferred_console`，`kernel/printk/printk.c`，`https://www.cnblogs.com/brucemengbm/p/6707111.html`:

  ```C
  static int __add_preferred_console(char *name, int idx, char *options,
    				   char *brl_options)
  {
    	struct console_cmdline *c;
    	int i;
    
    	/*
    	 *	See if this tty is not yet registered, and
    	 *	if we have a slot free.
    	 */
    	for (i = 0, c = console_cmdline;
    	     i < MAX_CMDLINECONSOLES && c->name[0];
    	     i++, c++) {
    		if (strcmp(c->name, name) == 0 && c->index == idx) {
    			if (!brl_options)
    				preferred_console = i;
    			return 0;
    		}
    	}
    	if (i == MAX_CMDLINECONSOLES)
    		return -E2BIG;
    	if (!brl_options)
    		preferred_console = i;
    	strlcpy(c->name, name, sizeof(c->name));
    	c->options = options;
    	braille_set_options(c, brl_options);
    
    	c->index = idx;
    	return 0;
    }
  
  ```

  



### 3.1 register_console函数解析

- register_console，`kernel/printk/printk.c`:

  ```c
  void register_console(struct console *newcon)
  {
    	int i;
    	unsigned long flags;
    	struct console *bcon = NULL;
    	struct console_cmdline *c;
    	static bool has_preferred;
    
    	if (console_drivers) //内核注册的所有console drivers，如果发现要注册的console已经被注册过了，直接return
    		for_each_console(bcon)
    			if (WARN(bcon == newcon,
    					"console '%s%d' already registered\n",
    					bcon->name, bcon->index))
    				return;
    
    	/*
    	 * before we register a new CON_BOOT console, make sure we don't
    	 * already have a valid console
    	 */
    	if (console_drivers && newcon->flags & CON_BOOT) { //如果real console已经注册过，那么boot console就不允许再被注册了
    		/* find the last or real console */
    		for_each_console(bcon) {
    			if (!(bcon->flags & CON_BOOT)) {
    				pr_info("Too late to register bootconsole %s%d\n",
    					newcon->name, newcon->index);
    				return;
    			}
    		}
    	}
    
    	if (console_drivers && console_drivers->flags & CON_BOOT)  //是否已经注册过boot console
    		bcon = console_drivers;
    
    	if (!has_preferred || bcon || !console_drivers) //如果real console还没有注册过，那么判断是否存在prefer console
    		has_preferred = preferred_console >= 0;
    
    	/*
    	 *	See if we want to use this console driver. If we
    	 *	didn't select a console we take the first one
    	 *	that registers here.
    	 */
    	if (!has_preferred) { //如果不存在prefer console，那么把当前这个作为preferred console
    		if (newcon->index < 0)
    			newcon->index = 0;
    		if (newcon->setup == NULL ||
    		    newcon->setup(newcon, NULL) == 0) {
    			newcon->flags |= CON_ENABLED;
    			if (newcon->device) {
    				newcon->flags |= CON_CONSDEV;
    				has_preferred = true;
    			}
    		}
    	}
    
    	/*
    	 *	See if this console matches one we selected on
    	 *	the command line.
    	 */
    	for (i = 0, c = console_cmdline;
    	     i < MAX_CMDLINECONSOLES && c->name[0];
    	     i++, c++) { //查找cmdline中传递的console配置项，如果发现匹配项，就根据cmdline传入的options执行setup操作（可能包含波特率等配置）
    		if (!newcon->match ||
    		    newcon->match(newcon, c->name, c->index, c->options) != 0) { //match函数为空或者match函数不匹配，那么执行默认match操作
    			/* default matching */
    			BUILD_BUG_ON(sizeof(c->name) != sizeof(newcon->name));
    			if (strcmp(c->name, newcon->name) != 0) //默认的match操作其实就是比较name字符串是否相同
    				continue;
    			if (newcon->index >= 0 &&
    			    newcon->index != c->index)
    				continue;
    			if (newcon->index < 0)
    				newcon->index = c->index;
    
    			if (_braille_register_console(newcon, c))
    				return;
    
    			if (newcon->setup &&
    			    newcon->setup(newcon, c->options) != 0)
    				break;
    		}
    
          //执行到这里，说明match都已经成功了，直接enable console，并且把prefer设置为它
    		newcon->flags |= CON_ENABLED;
    		if (i == preferred_console) {
    			newcon->flags |= CON_CONSDEV;
    			has_preferred = true;
    		}
    		break;
    	}
      
      //执行到此，其逻辑：
  	//1.如果real console，只有match了cmdline中的配置，才会enable它，否则直接return。
  	//2.如果是boot console，此时也是enable状态，那么也会继续运行到下面
    	if (!(newcon->flags & CON_ENABLED))
    		return;
    
    	/*
    	 * If we have a bootconsole, and are switching to a real console,
    	 * don't print everything out again, since when the boot console, and
    	 * the real console are the same physical device, it's annoying to
    	 * see the beginning boot messages twice
    	 */
    	if (bcon && ((newcon->flags & (CON_CONSDEV | CON_BOOT)) == CON_CONSDEV)) //运行到此说明是从boot console到real console的切换，那么要注销所有的boot console
    		newcon->flags &= ~CON_PRINTBUFFER;
    
    	/*
    	 *	Put this console in the list - keep the
    	 *	preferred driver at the head of the list.
    	 */
    	console_lock();
    	if ((newcon->flags & CON_CONSDEV) || console_drivers == NULL) { //把对应的console driver加入到链表中，此链表在printk时会使用到
    		newcon->next = console_drivers;
    		console_drivers = newcon;
    		if (newcon->next)
    			newcon->next->flags &= ~CON_CONSDEV;
    	} else {
    		newcon->next = console_drivers->next;
    		console_drivers->next = newcon;
    	}
    
    	if (newcon->flags & CON_EXTENDED)
    		if (!nr_ext_console_drivers++)
    			pr_info("printk: continuation disabled due to ext consoles, expect more fragments in /dev/kmsg\n");
    
    	if (newcon->flags & CON_PRINTBUFFER) {
    		/*
    		 * console_unlock(); will print out the buffered messages
    		 * for us.
    		 */
    		logbuf_lock_irqsave(flags);
    		console_seq = syslog_seq;
    		console_idx = syslog_idx;
    		logbuf_unlock_irqrestore(flags);
    		/*
    		 * We're about to replay the log buffer.  Only do this to the
    		 * just-registered console to avoid excessive message spam to
    		 * the already-registered consoles.
    		 */
    		exclusive_console = newcon;
    	}
    	console_unlock();
    	console_sysfs_notify();
    
    	/*
    	 * By unregistering the bootconsoles after we enable the real console
    	 * we get the "console xxx enabled" message on all the consoles -
    	 * boot consoles, real consoles, etc - this is to ensure that end
    	 * users know there might be something in the kernel's log buffer that
    	 * went to the bootconsole (that they do not see on the real console)
    	 */
    	pr_info("%sconsole [%s%d] enabled\n",
    		(newcon->flags & CON_BOOT) ? "boot" : "" ,
    		newcon->name, newcon->index);
    	if (bcon &&
    	    ((newcon->flags & (CON_CONSDEV | CON_BOOT)) == CON_CONSDEV) &&
    	    !keep_bootcon) {
    		/* We need to iterate through all boot consoles, to make
    		 * sure we print everything out, before we unregister them.
    		 */
    		for_each_console(bcon)
    			if (bcon->flags & CON_BOOT)
    				unregister_console(bcon);
    	}
  }
    EXPORT_SYMBOL(register_console);
  
  ```
  
  

