# 细说Cache-L1/L2/L3/TLB



## 1. 概述

-   cache是一种又小又快的存储器。它存在的意义是弥合`Memory`与`CPU`之间的速度差距。

![img](https://pic3.zhimg.com/80/v2-1e2882cdeaafacac9ead8df35078d062_720w.jpg)

-   现在的`CPU`中有好几个等级的缓存。通常`L1`和`L2`缓存都是每个`CPU`一个的, `L1`缓存又分为`L1i`和`L1d`，分别用来存储指令和数据。`L2`缓存是不区分指令和数据的。`L3`缓存多个核心共用一个，通常也不区分指令和数据。还有一种缓存叫`TLB`，它主要用来缓存`MMU`使用的页表，通常我们讲缓存（`cache`)的时候是不算它的。下图所示（`Cache hierarchy of the K8 core in the AMD Athlon 64 CPU`）：

![img](https://pic3.zhimg.com/80/v2-0e77de9fe46e80c179204da1bf9ad6b2_720w.jpg)







## 2. Cache Line

-   `Cache`存储数据是以固定大小为单位的，称为一个`Cache entry`，这个单位称为`Cache line`或`Cache block`。给定`Cache`容量大小和`Cache line size`的情况下，它能存储的条目个数(`number of cache entries`)就是固定的。因为`Cache`是固定大小的，所以它从`DRAM`获取数据也是固定大小。对于`X86`来讲，它的`Cache line`大小与`DDR3、4`一次访存能得到的数据大小是一致的，即`64Bytes`。对于ARM来讲，较旧的架构(新的不知道有没有改）的`Cache  line`是`32Bytes`，但一次内存访存只访问一半的数据也不太合适，所以它经常是一次填两个`Cache line`，叫做`double fill`。

-   `CPU`从`Cache`获取数据的最小单位是字节，`Cache`从`Memory`拿数据的最小单位（这里不讲嵌入式系统）是`64Bytes`，`Memory`从硬盘拿数据通常最小是`4092Bytes`。

![img](https://pic1.zhimg.com/80/v2-28fb374594327b62cbec40f75181bc30_720w.jpg)

## 3. 替换策略

-   `Cache`里存的数据是`Memory`中的**常用数据**一个拷贝，`Cache`比较小，不可以缓存`Memory`中的所有数据。当`Cache`存满后，再需要存入一个新的条目时，就需要把一个旧的条目从缓存中拿掉，这个过程称为`evict`，一个被`evict`的条目称为`victim`。缓存管理单元通过一定的算法决定哪些数据有资格留在`Cache`里，哪些数据需要从`Cache`里移出去。这个策略称为**替换策略（replacement policy)**。最简单的替换策略称为`LRU(least recently used)`，即`Cache`管理单元记录每个`Cache  line`最近被访问的时间，每次需要`evict`时，选最近一次访问时间最久远的那一条做为`victim`。在实际使用中，`LRU`并不一定是最好的替换策略，在`CPU`设计的过程中，通常会不段对替换策略进行改进，每一款芯片几乎都使用了不同的替换策略。

## 4. 写入策略与一致性

-   `CPU`需要读写一个地址的时候，先去`Cache`中查找，如果数据不在`Cache`中，称为`Cache miss`，就需要从`Memory`中把这个地址所在的那个`Cache  line`上的数据加载到`Cache`中。然后再把数返回给`CPU`。这时会伴随着另一个`Cache` 条目成为`victim`被替换出去。

-   如果`CPU`需要访问的数据在`Cache`中，则称为`Cache hit`。

-   针对写操作，有两种写入策略，分别为`write back`和`write through`。`write through`策略下，数据直接同时被写入到`Memory`中，在`write  back`策略中，数据仅写到`Cache`中，此时`Cache`中的数据与`Memory`中的数据不一致，`Cache`中的数据就变成了脏数据(`dirty`)。如果其他部件（`DMA`， 另一个核）访问这段数据的时候，就需要通过**Cache一致性协议**(`Cache coherency protocol`)保证取到的是最新的数据。另外这个`Cache`被替换出去的时候就需要写回到内存中。

## 5. Cache Miss 与CPU stall

-   如果发生了`Cache  Miss`，就需要从`Memory`中取数据，这个取数据的过程中，`CPU`可以执行几十上百条指令的，如果等待数据时什么也不做时间就浪费了。可以在这个时候提高`CPU`使用效率的有两种方法，一个是乱序执行（`out of order  execution`)，即把当前线程中后面的、不依赖于当前指令执行结果的指令拿过来提前执行，另一个是超线程技术，即把另一个线程的指令拿过来执行。



## 6. L1/L2 Cache速度差别

```
L1 cache: 3 cycles
L2 cache: 11 cycles
L3 cache: 25 cycles
Main Memory: 100 cycles

```

`L1/L2 Cache`都是用`SRAM`做为存储介质，为什么说`L1`比`L2`快呢？这里面有三方面的原因：

>   **1. 存储容量不同导致的速度差异**

-   `L1`的容量通常比`L2`小，容量大的`SRAM`访问时间就越长，同样制程和设计的情况下，访问延时与容量的开方大致是成正比的。

>   **2. 离`CPU`远近导致的速度差异**

-   通常`L1 Cache`离`CPU`核心需要数据的地方更近，而`L2 Cache`则处于边缓位置，访问数据时，`L2 Cache`需要通过更远的铜线，甚至更多的电路，从而增加了延时。
-   `L1  Cache`分为`ICache`（指令缓存）和`DCache`(数据缓存）,指令缓存`ICache`通常是放在`CPU`核心的指令预取单远附近的，数据缓存`DCache`通常是放在`CPU`核心的`load/store`单元附近。而`L2 Cache`是放在`CPU pipeline`之外的。

-   为什么不把`L2 Cache`也放在很近的地方呢？由于`Cache`的容量越大，面积越大，相应的边长的就越长（假设是正方形的话），总有离核远的。

-   下面的图并不是物理上的图，只是为大家回顾一下`CPU`的`pipe line`。另外需要注意的是这张图里展示了一个二级的`DTLB`结构，和一级的`ITLB`。

![img](https://pic3.zhimg.com/80/v2-1e8837a8f62f04f87a92c279e762276e_720w.jpg)

>   **3. 制程不同的造成的速度差异**

-   在实际设计制造时，针对`L1/L2`的不同角色，`L1`更加注重速度， `L2`更加注重节能和容量。在制程上这方面有体现，（但我不懂，。。。。）。在设计时，这方面的有体现： 首先， `L1 Cache`都是`N`路组相联的，N路组相联的意思时，给定一个地址，`N`个`Cache`单元同时工作，取出`N`份`tag`和`N`份数据，然后再比较`tag`，从中选出`hit`的那一个采用，其它的丢弃不用。这种方式一听就很浪费，很不节能。另外，`L2 Cache`即便也是`N`路组相联的，但它是先取`N`个`tag`，然后比对`tag`后发现`cache hit`之后再把对应的数据取出来。由于`L2`是在`L1  miss`之后才会访问，所以`L2 cache  hit`的概率并不高，访问的频率也不高，而且有前面`L1`抵挡一下，所以它的延迟高点也无所谓，`L2`容量比较大，如果数据和`tag`一起取出来，也比较耗能。
-   通常专家都将`L1`称为`latency filter`, `L2`称为`bandwidth filter`。



## 7. L3 Cache

-   `L1/L2  Cache`通常都是每个`CPU`核心一个（`x86`而言，`ARM`一般`L2`是为一个簇即4个核心共享的），这意味着每增加一个CPU核心都要增加相同大小的面积，即使各个`CPU`核心的`L2 Cache`有很多相同的数据也只能各保存一份，因而一个所有核心共享的`L3 Cache`也就有必要了。

-   `L3 Cache`通常都是各个核心共享的，而且`DMA`之类的设备也可以用。

![img](https://pic4.zhimg.com/80/v2-3b8ccfe67eeaeead00af5581befca86b_720w.jpg)

-   由于`L3 Cache`的时延要求没有那么高，现在大家也要考虑不使用`SRAM`，转而使用`STT-MRAM`，或是`eDRAM`来做`L3 Cache`。



## 8. 逻辑Cache和物理Cache

-   `Cache`在系统中的位置根据与`MMU`的相对位置不同，分别称为`logical Cache`和`physical cache`。

-   `Logical Cache`接受的是逻辑地址，物理`Cache`接受的是物理地址。

![img](https://pic4.zhimg.com/80/v2-84c36ace1abda5c13282091b4d95aacb_720w.jpg)

-   `logical cache`有一个优势就是可以在完成虚拟地址到物理地址的翻译之前就可以开始比对`cache`，但是有一个问题就是`Cache 一致性`还有`cache  eviction`必须通过物理地址来做，因为多个虚拟地址可能对应同一个物理地址，不能保证不同的虚拟地址所对应的`cache`就一定不是同一份数据。为了解决这个问题，就不得不把物理地址也保存在为`tag`。这样`tag`要存的内容就增加了一倍。
-   相对而言，`physical cache`由于一开始就是物理地址，所以只需要存物理地址为`tag`，而不需要再保存虚拟地址为`tag`，看起来简单了很多。
-   其实总结起来，`Cache`的`tag`有两种作用：（1）对于`N`路组相联`cache`中，通过`tag`比对选择使用哪一路的数据，（2）决定`cache  hit`还是`miss`。前者配合操作系统的情况下，虚拟地址就可以做到，比如说给虚拟地址和物理页配对的时候总是保证根据两者的某些位来选`way`的时候是一样的，而且前者不需要完全的正确，偶尔错一些是可以接受的，你可以先选出数据，默认是`cache hit`，然后拿着数据是计算，但后来通过物理`tag`比对时发现是`miss`的情况下，再无效掉这次计算，反正`cache  miss`的情况下`cpu`本来也需要`stall`好多个`cycle`。后者则必须依靠物理地址才可以做到。这样一来，很多设计都把虚拟地址`tag`弱化为`hint`, 仅用于选哪个`way`。



以参考的资料，大家也可以自己看看。

[CPU cache - Wikipedia](https://link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/CPU_cache)

[https://faculty.tarleton.edu/agapie/documents/cs_343_arch/04_CacheMemory.pdf](https://link.zhihu.com/?target=https%3A//faculty.tarleton.edu/agapie/documents/cs_343_arch/04_CacheMemory.pdf)

[http://www.ecs.csun.edu/~cputnam/Comp546/Putnam/Cache%20Memory.pdf](https://link.zhihu.com/?target=http%3A//www.ecs.csun.edu/~cputnam/Comp546/Putnam/Cache%20Memory.pdf)



进一步阅读：

[https://cseweb.ucsd.edu/classes/fa14/cse240A-a/pdf/08/CSE240A-MBT-L15-Cache.ppt.pdf](https://link.zhihu.com/?target=https%3A//cseweb.ucsd.edu/classes/fa14/cse240A-a/pdf/08/CSE240A-MBT-L15-Cache.ppt.pdf)

[http://www.ecs.csun.edu/~cputnam/Comp546/Putnam/Cache%20Memory.pdf](https://link.zhihu.com/?target=http%3A//www.ecs.csun.edu/~cputnam/Comp546/Putnam/Cache%20Memory.pdf)

[https://ece752.ece.wisc.edu/lect11-cache-replacement.pdf](https://link.zhihu.com/?target=https%3A//ece752.ece.wisc.edu/lect11-cache-replacement.pdf)

[http://www.ipdps.org/ipdps2010/ipdps2010-slides/session-22/2010IPDPS.pdf](https://link.zhihu.com/?target=http%3A//www.ipdps.org/ipdps2010/ipdps2010-slides/session-22/2010IPDPS.pdf)