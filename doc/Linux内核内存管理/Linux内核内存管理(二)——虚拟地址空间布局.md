# Linux内核内存管理（二）——虚拟地址空间布局

## 1. 虚拟地址空间划分

### 1.1 ARM32架构Linux内核

- 在32bit Linux中，一共能使用的虚拟地址空间是4GB（2^32），用户空间和内核空间的划分通常是按照3:1来划分的，也可以按照2:2来划分，调整内核空间和用户空间的大小划分的具体配置如下[linux-4.14/arch/arm/Kconfig]：                                                             ![1560428626924](../picture/32bits-空间划分配置.png)

- Arm32架构内存分布如下：                                               ![1560434346240](../picture/Arm32内存分布.png)

### 1.2 ARM64架构Linux内核

- 对于ARM64架构处理器来说，目前应用程序没有那么大的内存需求，所以不需要支持完全的64位虚拟地址， 实际支持情况如下：
    1. 目前基于ARMv8-A架构的处理器，虚拟地址的最大宽度是48位，如下图，内核虚拟地址在64位地址空间的顶部，高16位全部为1,范围是[0xFFFF 0000 0000 0000, 0xFFFF FFFF FFFF FFFF]，用户虚拟地址在64位地址空间的底部，高16位全部为0, 范围是[0x0000 0000 0000 0000, 0x0000 FFFF FFFF FFFF],高16位是全1或是全0的地址称为规范的地址，两者之间的是不规范的地址，不允许使用。                                                                ![avator](../picture/Arm64内存分布.png)
    2. 如果处理器实现了ARMv8.2标准的大虚拟地址（Large Virtual Address,LVA）支持，并且页长度是64KB，那么虚拟地址的最大宽度是52位。
    3. 可以为虚拟地址配置比最大宽度小的宽度，并且可以为内核虚拟地址和用户虚拟地址配置不同的宽度。转换控制寄存器（Translation Control Register）TCR——EL1的字段T0SZ定义了必须是全0的最高位的数量，字段T1SZ定义了必须是全1的最高位的数量。用户虚拟地址的宽度是（64-TCR_EL1.T0SZ），内核虚拟地址的宽度是（64-TCR_EL1.T1SZ）。
    4. 在ARM64架构的Linux内核中，内核虚拟地址和用户虚拟地址的宽度相同。所有进程共享内核虚拟地址空间，每个进程有独立的用户虚拟地址空间，同一个线程组的用户线程共享用户虚拟地址空间，内核线程没有用户虚拟地址空间。



## 2. 用户虚拟地址空间布局

### 2.1 相关宏解释

1. VA_BITS: 编译内核时选择的虚拟地址位数，一般只针对arm64。

   - VA_BITS 定义在 [linux-4.14/arch/arm64/include/asm/memory.h]:![avator](../picture/va_bits.png)

   - CONFIG_ARM64_VA_BITS定义在[linux-4.14/arch/arm64/configs/***_defconfig]，例如arch/arm64/configs/sprd_roc1_defconfig：![avator](../picture/config_arm64_va_bits.png)

     可见，在sprd_roc1_defconfig中，虚拟地址位数为39位。

2. CONFIG_COMPAT：支持执行32位用户空间程序，定义[arch/arm64/configs/sprd_roc1_defconfig]:	![1560416237325](../picture/config_compat.png)

3. TASK_SIZE: 进程的用户虚拟地址空间长度。

   - TASK_SIZE定义在 [arch/arm64/include/asm/processor.h]：![1560413481268](../picture/task_size.png)![avator](../picture/task_size-1.png)

   - test_thread_flag(TIF_32BIT)：判断用户空间程序是不是32位，TIF_32BIT定义在 [arch/arm64/include/asm/thread_info.h]：![1560416753731](../picture/tif_32bit.png)

### 2.2 用户虚拟地址空间区域

1. 进程的用户虚拟地址空间包含以下区域：

   > 代码段、数据段和未初始化数据段；
   >
   > 动态库的代码段、数据段和未初始化数据段；
   >
   > 存放动态生成的数据的堆；
   >
   > 存放局部变量和实现函数调用的栈；
   >
   > 存放在栈底部的环境变量和参数字符串；
   >
   > 把文件区间映射到虚拟地址空间的内存映射区域。

2. 用户虚拟地址空间布局:

   - 内核使用内存描述符mm_struct描述进程的用户虚拟地址空间，该结构体定义在`linux-4.14/include/linux/mm_types.h`， 其成员变量 `unsigned long mmap_base`指定了内存映射区域的起始地址。用户虚拟地址空间有两种布局，区别是内存映射区域的起始位置和增长方向不同。

   - 传统布局

     内存映射区域自底向上增长，起始地址是`TASK_UNMAPPED_BASE`，每种处理器架构都要定义这个宏，ARM64架构定义为TASK_SIZE/4。默认启用内存映射区域随机化，需要把起始地址加上一个随机值。传统布局的缺点是堆的最大长度受到限制，在32位系统中影响比较大，而64位系统中这不是问题。![1561554360500](../picture/传统布局.png)

   - 新布局

     内存映射区域自顶向下增长，起始地址是（STACK_TOP-栈的最大长度-间隙）。默认启用内存映射区域随机化，需要把起始地址减去一个随机值。![1561555016044](../picture/新布局.png)

## 3. 内核地址空间布局

- ARM64处理器架构的内核地址空间布局如下：                       ![1561605242653](../picture/ARM64架构的内核地址空间布局.png)

  内核地址空间中各区域如下：

  > 1. 线性映射区域的范围是[PAGE_OFFSET, 2^64 -1]，起始位置是PAGE_OFFSET = (0xFFFF FFFF FFFF FFFF << (VA_BITS-1))，长度是内核虚拟地址空间的一半。称为线性映射区域的原因是虚拟地址和物理地址是线性关系：`虚拟地址 = ((物理地址 - PHYS_OFFSET) + PAGE_OFFSET)`，其中PHYS_OFFSET是内存的其实物理地址。
  >2. vmemmap区域的范围是[VMEMMAP_START, PAGE_OFFSET]，长度是VMEMMAP_SIZE = (线性映射区域的长度/页长度 * page结构体的长度上限)。内核使用page结构体描述一个物理页，内存的所有物理页对应一个page结构体数组。如果内存的物理地址空间不连续，存在很多空洞，称为稀疏内存。vmemmap区域是稀疏内存的page结构体数组的虚拟地址空间。
  > 3. PCI I/O区域的范围是[PCI_IO_START, PCI_IO_END]，长度是16MB，结束地址是PCI_IO_END = (VMEMMAP_START - 2MB)。外围组件互联（Peripheral Component Interconnect, PCI）是一种总线标准，PCI I/O区域是PCI设备的I/O地址空间。
  >4. 固定映射区域的范围是[FIXADDR_START, FIXADDR_TOP]，长度是IXADDR_SIZE，结束地址是FIXADDR_TOP = (PCI_IO_START - 2MB)。固定地址是编译时的特殊虚拟地址，编译的时候是一个常量，在内核初始化的时候映射到物理地址。
  >    5. vmalloc区域的范围是[VMALLOC_START, VMALLOC_END]，起始地址VMALLOC_START，等于内核模块区域的结束地址MODULES_END，结束地址VMALLOC_END = (PAGE_OFFSET - PUD_SIZE - VMEMMAP_SIZE - 64KB)，其中PUD_SIZE是页上级目录表项映射的地址空间的长度。vmalloc区域是函数vmalloc使用的虚拟地址空间，内核使用vmalloc分配虚拟地址连续但物理地址不连续的内存。内核镜像在vmalloc区域，起始虚拟地址是(KIMAGE_VADDR + TEXT_OFFSET)，其中KIMAGE_VADDR是内核镜像的虚拟地址的基准值，等于内核模块区域的结束地址MODULES_END，TEXT_OFFSET是内存中的内核镜像相对内存其实位置的偏移。
  >6. 内核模块区域的范围是[MODULES_ADDR, MODULES_END]，长度是128M，起始地址MODULES_ADDR = (内核虚拟地址空间的其实地址 + KASAN影子区域的长度)。内核模块区域是内核模块使用的虚拟地址空间。
  > 7. KASAN影子区域的起始地址是内核虚拟地址空间的起始地址，长度是内核虚拟地址空间的1/8。内核地址消毒剂（Kernel Address SANitizer，KASAN）是一个动态的内存错误检查工具。它为发现释放后使用和越界访问这两类缺陷提供了快速和综合的解决方案。
  >
