# Arm Linux 内核
---
## 1. 内核构建
### 1.1 内核初始化
- make mrproper; 清除包括.config文件在内的，为内核编译及链接而生成的诸多设置文件
- make distclean; 清除内核编译后生成的所有对象文件、备份文件等。
---
### 1.2 内核配置
- make menuconfig; 图形用户界面形式的内核配置前端。具体配置可参考《奔跑吧Linux内核》第六章节
- make ***_defconfig; 在arch/$(ARCH)/configs目录下，有与各个SoC相符的自定义配置文件。
- 通过make menuconfig和make ***_defconfig后，生成.config文件
---
### 1.3 内核构建
- 构建内核是指，编译内核并链接二进制文件，由此生成一个二进制文件zImage的一系列过程。
- make bzImage -j4 ARCH=arm CROSS_COMPILE=arm-linux-gnueabi-
- make dtbs
---
---
## 2. 内核的启动
- 内核的实际起始函数是start_kernel()函数，调用start_kernel()函数之前，必须先将编译内核获得的zImage进行解压，完成目录构建等基本任务。
- 调用start_kernel的过程大体分为3个阶段：
    1. 解压内核映像zImage前的准备阶段，通过与处理器版本相符的处理器类型列表，执行打开/关闭/清除缓存等任务，为MMU构建16KB的页目录；
    2. 对zImage执行解压缩；
    3. 检查处理器及机器信息、通过启动加载项获得的atag信息的有效性，然后激活MMU调用内核起始函数——start_kernel()函数。
---
### 2.1 内核解压
- 通过启动加载项完成对软硬件的默认初始化任务后，最先执行的是arch/arm/boot/compressed/head.S的start标签中的代码。
    - 启动加载项必须提供5种功能：RAM初始化、串行端口初始化、查找机器类别、构建tagged list内核、将控制移交到内核镜像。
- BSS系统域初始化——not_relocated标签
    - 解压zImage这一压缩内核的准备工作有：初始化BSS区域、激活缓存以及设置动态内存区域，这些设置是解压内核时必不可少的事项。
    - BSS初始化代码：arch/arm/boot/compressed/head.S的not_relocated标签处。
- 激活缓存——cache_on标签
    - arch/arm/boot/compressed/head.S的cache_on标签处
- 页目录项初始化——__setup_mmu标签
    - arch/arm/boot/compressed/head.S的__setup_mmu标签
    - __setup_mmu标签在cache_on标签内调用，用于初始化解压内核所需的页目录项。特别是对内存的256MB区域设置cacheable、bufferable，这是因为解压内核时，使用缓存和写缓冲以提高解压性能。
- 指令缓存激活及缓存策略适用——__common_mmu_cache_on标签
    - arch/arm/boot/compressed/head.S的__common_mmu_cache_on标签
    - __common_mmu_cache_on标签在cache_on标签内调用
---
### 2.2 从压缩的内核zImage还原内核映像
- 压缩的内核zImage是通过gunzip执行解压：gunzip的内核源代码 arch/arm/boot/compressed/misc.c
- 解压内核并避免覆写——wont_overwrite、decompress_kernel标签
    - wont_overwrite标签在cache_on标签后执行。在完成对压缩内核zImage执行解压的所有准备工作后，内核会解压到ZRELADDR地址，利用decompress_kernel函数完成解压工作。
    - decompress_kernel函数位置：arch/arm/boot/compressed/misc.c， 该函数是对压缩内核执行解压的实际子程序。
- 调用已解压内核——call_kernel标签
    