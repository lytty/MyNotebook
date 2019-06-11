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