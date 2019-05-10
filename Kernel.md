# Kernel 笔记

## DTS（设备树）
- 如果要使用Device Tree，首先用户要了解自己的硬件配置和系统运行参数，并把这些信息组织成Device Tree source file。通过DTC（Device Tree Compiler），可以将这些适合人类阅读的Device Tree source file变成适合机器处理的Device Tree binary file（有一个更好听的名字，DTB，device tree blob）。在系统启动的时候，boot program（例如：firmware、bootloader）可以将保存在flash中的DTB copy到内存（当然也可以通过其他方式，例如可以通过bootloader的交互式命令加载DTB，或者firmware可以探测到device的信息，组织成DTB保存在内存中），并把DTB的起始地址传递给client program（例如OS kernel，bootloader或者其他特殊功能的程序）。对于计算机系统（computer system），一般是firmware->bootloader->OS，对于嵌入式系统，一般是bootloader->OS。

- .dts文件是一种ASCII 文本格式的Device Tree描述，此文本格式非常人性化，适合人类的阅读习惯。基本上，在ARM Linux在，一个.dts文件对应一个ARM的machine，一般放置在内核的arch/arm/boot/dts/目录。由于一个SoC可能对应多个machine（一个SoC可以对应多个产品和电路板），势必这些.dts文件需包含许多共同的部分，Linux内核为了简化，把SoC公用的部分或者多个machine共同的部分一般提炼为.dtsi，类似于C语言的头文件。其他的machine对应的.dts就include这个.dtsi。

- 技术文档：https://blog.csdn.net/radianceblau/article/details/70800076

## 内存大小
- 内存定义路径（unisoc）：sprdroid9.0_trunk/kernel4.14/arch/arm64/boot/dts/sprd/ums312-2h10.dts
    ‘’‘
    33	memory: memory {
    34		device_type = "memory";
    35		reg = <0x0 0x80000000 0x0 0x80000000>; #<base-addr size>
    36	};
    ’‘’
- 读取内存：
    1. sprdroid9.0_trunk/kernel4.14/init/main.c：
    ‘’‘
    534	setup_arch(&command_line);
    ’‘’
    2. sprdroid9.0_trunk/kernel4.14/arch/arm64/kernel/setup.c：
    ‘’‘
    245void __init setup_arch(char **cmdline_p)
    246{
    247	pr_info("Boot CPU: AArch64 Processor [%08x]\n", read_cpuid_id());
    248
    249	sprintf(init_utsname()->machine, UTS_MACHINE);
    250	init_mm.start_code = (unsigned long) _text;
    251	init_mm.end_code   = (unsigned long) _etext;
    252	init_mm.end_data   = (unsigned long) _edata;
    253	init_mm.brk	   = (unsigned long) _end;
    254
    255	*cmdline_p = boot_command_line; “boot_command_line是一个静态数组，在arm64的环境下是2048，也就是说bootloader传递给kernel的commandline超过2048就要修改kernel源代码加这个数组加大”
    256
    257	early_fixmap_init();
    258	early_ioremap_init();
    259
    260	setup_machine_fdt(__fdt_pointer); “__fdt_pointer 是bootloader传递过来的，代表devicetree在内存中的地址”
    ’‘’
    3. sprdroid9.0_trunk/kernel4.14/arch/arm64/kernel/setup.c：
    ‘’‘
    185 if (!dt_virt || !early_init_dt_scan(dt_virt))
    ’‘’
    4. sprdroid9.0_trunk/kernel4.14/drivers/of/fdt.c
    ‘’‘
    1322	early_init_dt_scan_nodes();
    ’‘’
    5. sprdroid9.0_trunk/kernel4.14/drivers/of/fdt.c
    ‘’‘
    1302void __init early_init_dt_scan_nodes(void)
    1303{
    1304	/* Retrieve various information from the /chosen node */
    1305	of_scan_flat_dt(early_init_dt_scan_chosen, boot_command_line); “获取命令行信息，即dts文件中chosen节点中bootargs，将commandline copy到boot_command_line中”
    1306
    1307	/* Initialize {size,address}-cells info */
    1308	of_scan_flat_dt(early_init_dt_scan_root, NULL);
    1309
    1310	/* Setup memory, calling early_init_dt_add_memory_arch */
    1311	of_scan_flat_dt(early_init_dt_scan_memory, NULL); "获取dts中memory节点信息， base-addr和size"
    1312}
    ’‘’

## 物理内存映射