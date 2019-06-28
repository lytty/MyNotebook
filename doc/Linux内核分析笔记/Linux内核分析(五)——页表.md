# Linux内核分析(五)——页表

## 1. 统一的页表框架

- 页表用来把虚拟页映射到物理页，并且存放页的保护位，即访问权限。在Linux 4.11版本之前，Liinux内核吧页表分为4级：

  > 1. 页全局目录（Page Global Directory，PGD）
  > 2. 页上层目录（Page Upper Directory，PUD）
  > 3. 页中间目录（Page Middle Directory，PMD）
  > 4. 直接页表（Page Table， PT）

  4.11 版本把页表扩展到五级，在页全局目录和页上层目录之间增加了页四级目录（Page 4th Directory，P4D）。

- 各种处理器架构可以选择使用五级、四级、三级或两极页表，同一种处理器架构在页长度不同的情况下可能选择不同的页表级数。可以使用配置宏 CONFIG_PGTABLE_LEVELS 配置页表级数，一般使用默认值。