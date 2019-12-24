# Linux C、C++常见知识

## 1. [linux C 中的volatile使用](https://www.cnblogs.com/Neddy/archive/2012/02/02/2335343.html)

- 一个定义为`volatile`的变量是说这变量可能会被意想不到地改变，这样，编译器就不会去假设这个变量的值了。精确地说就是，优化器在用到这个变量时必须每次都小心地重新读取这个变量的值，而不是使用保存在寄存器里的备份。下面是`volatile`变量的几个例子： 
  1.  并行设备的硬件寄存器（如：状态寄存器） 
  2.  一个中断服务子程序中会访问到的非自动变量(`Non-automatic variables`) 
  3.  多线程应用中被几个任务共享的变量 

- volatile关键字是一种类型修饰符，用它声明的类型变量表示可以被某些编译器未知的因素更改，比如：操作系统、硬件或者其它线程等。遇到这个关键字声明的变量，编译器对访问该变量的代码就不再进行优化，从而可以提供对特殊地址的稳定访问。

- volatile对应的变量可能在你的程序本身不知道的情况下发生改变，比如多线程的程序，共同访问的内存当中，多个程序都可以操纵这个变量 。你自己的程序，是无法判定合适这个变量会发生变化。还比如，他和一个外部设备的某个状态对应，当外部设备发生操作的时候，通过驱动程序和中断事件，系统改变了这个变量的数值，而你的程序并不知道。 对于volatile类型的变量，系统每次用到他的时候都是直接从对应的内存当中提取，而不会利用cache当中的原有数值，以适应它的未知何时会发生的变化，系统对这种变量的处理不会做优化——显然也是因为它的数值随时都可能变化的情况。

- 一般说来，volatile用在如下的几个地方： 

  1. 中断服务程序中修改的供其它程序检测的变量需要加volatile； 
  2. 多任务环境下各任务间共享的标志应该加volatile； 
  3. 存储器映射的硬件寄存器通常也要加volatile说明，因为每次对它的读写都可能由不同意义； 

  另外，以上这几种情况经常还要同时考虑数据的完整性（相互关联的几个标志读了一半被打断了重写），在1中可以通过关中断来实现，2中可以禁止任务调度，3中则只能依靠硬件的良好设计了。 

- Linux 代码示例：

  ```c
  struct task_struct {
    	...
    	/* -1 unrunnable, 0 runnable, >0 stopped: */
    	volatile long			state;
      ...
  }
  
  ```




## 2. [linux中__weak关键字](https://www.cnblogs.com/MR-White315/p/11175418.html)

- 在linux的驱动代码中经常可以看到__weak去修饰一个函数或者变量，大多是用来修饰函数。它的作用有两个：
  1.  weak 顾名思义是“弱”的意思，所以如果函数名称前面加上__weak 修饰符，我们一般称这个函数为**“弱函数”**。加上了__weak 修饰符的函数，用户可以在用户文件中重新定义一个同名函数，最终编译器编译的时候，会选择用户定义的函数，如果用户没有重新定义这个函数，那么编译器就会执行__weak 声明的函数，并且编译器不会报错。
  2.  __weak 在**回调函数**的时候经常用到。这样的好处是，系统默认定义了一个空的回调函数，保证编译器不会报错。同时，如果用户自己要定义用户回调函数，那么只需要重新定义即可，不需要考虑函数重复定义的问题，使用非常方便

- 在linux/init/main.c中有函数**smp_setup_processor_id**

```
void __init __weak smp_setup_processor_id(void)
{
}
```

- 2.6.30内核中ARM结构没有额外定义**smp_setup_processor_id()**,所以ARM结构不执行任何操作。

```
n-ubuntu05@nubuntu05:linux-2.6.30.4$ grep -rn smp_setup_processor_id ./*
./arch/sparc/kernel/smp_64.c:1182:void __init smp_setup_processor_id(void)
./include/linux/smp.h:188:void smp_setup_processor_id(void);
./init/main.c:528:void __init __weak smp_setup_processor_id(void)
./init/main.c:541:  smp_setup_processor_id();
```

- v4.9内核在*./arch/arm/kernel/setup.c*中定义了**smp_setup_processor_id（）**：

```
 584 void __init smp_setup_processor_id(void)                                        
 585 {                                                                               
 586         int i;                                                                  
 587         u32 mpidr = is_smp() ? read_cpuid_mpidr() & MPIDR_HWID_BITMASK : 0;     
 588         u32 cpu = MPIDR_AFFINITY_LEVEL(mpidr, 0);                               
 589                                                                                 
 590         cpu_logical_map(0) = cpu;                                               
 591         for (i = 1; i < nr_cpu_ids; ++i)                                        
 592                 cpu_logical_map(i) = i == cpu ? 0 : i;                          
 593                                                                                 
 594         /*                                                                      
 595          * clear __my_cpu_offset on boot CPU to avoid hang caused by            
 596          * using percpu variable early, for example, lockdep will               
 597          * access percpu variable inside lock_release                           
 598          */                                                                     
 599         set_my_cpu_offset(0);                                                   
 600                                                                                 
 601         pr_info("Booting Linux on physical CPU 0x%x\n", mpidr);                 
 602 }
```

- 由于*linux/init/main.c*中定义的函数有__weak属性，所以ARM使用的是*./arch/arm/kernel/setup.c*中定义的**smp_setup_processor_id**



## 3. linux中的`__init` 宏

- 在内核里经常可以看到`__init`, `__devinit`这样的语句，这都是在`init.h`中定义的宏，`gcc`在编译时会将被修饰的内容放到这些宏所代表的`section`。

- 其典型的定义如下：

  ```c
  #define __init        __section(.init.text) __cold notrace
  #define __initdata    __section(.init.data)
  #define __initconst    __section(.init.rodata)
  #define __exitdata    __section(.exit.data)
  #define __exit_call    __used __section(.exitcall.exit)
  
  ```

- 其典型用法如下：

  ```c
  static int __init xxx_drv_init(void)
  {
       return pci_register_driver(&xxx_driver);
  }
  
  ```

- 根据上面的定义与用法，`xxx_drv_init()`函数将会被`link`到`.init.text`段。
- 之所以加入这样的宏，原因有2：
  1. 一部分内核初始化机制依赖与它。如`kernel`将初始化要执行的`init`函数，分为7个级别，`core_initcall, postcore_initcall, arch_initcall, subsys_initcall, fs_iitcall, device_initcall, late_initcall`。这7个级别优先级递减，即先执行`core_initcall`，最后执行`late_initcall`。通过使用文中提到的宏，`gcc`会将初始化代码按下面的结构安排：在内核初始化时，从`__initcall_start`到`__initcall_end`之间的`initcall`被一次执行。
  2. 提高系统效率。初始化代码的特点是，在系统启动时运行，且一旦运行后马上退出内存，不再占用内存。

- 常用的宏：

  > `__init`，标记内核启动时所用的初始化代码，内核启动完成后就不再使用。其所修饰的内容被放到.init.text section中。
  > `__exit`，标记模块退出代码，对非模块无效
  > `__initdata`，标记内核启动时所用的初始化数据结构，内核启动完成后不再使用。其所修饰的内容被放到.init.data section中。
  > `__devinit`，标记设备初始化所用的代码
  > `__devinitdata`，标记设备初始化所用的数据结构
  > `__devexit`，标记设备移除时所用的代码
  >
  > `xxx_initcall`，7个级别的初始化函数



## 4. linux中C嵌arm汇编`__asm__ __volatile__`

1. 带有C/C++表达式的内联汇编格式：

   `__asm__ __volatile__(“Instructionlist”:Output:Input:Clobber/Modify) `

2.  `__asm__`, 是`GCC`关键字`asm`的宏定义：

   `#define __asm__ asm`

   `__asm__`或`asm`用来声明一个内联汇编表达式，所以任何一个内联汇编表达式都以它开头，是必不可少的。

3.  `__volatile__`，是GCC关键字volatile的宏定义：

   `#define __volatile__ volatile`

   `__volatile__`或`volatile`是可选的，如果用了它，则向`GCC`声明不允许对该内联汇编优化，否则，当使用优化选项（-o）进行编译时`GCC`会根据字自己的判断决定是否将内联汇编表达式的指令优化掉。

4.  `Instruction list`

   - `Instruction list`是汇编指令序列，它可以是空，比如：

     `__asm__ __volatile__（“”）`；或`__asm__ （“”）`；是合法的内联汇编表达式，但是它们没有意义。

   - 但是`__asm__ __volatile__（“” ：：: ”memory”）`,它向`GCC`声明，内存做了改动，`GCC`在编译的时候，会将此因素考虑进去。在访问`IO`端口和`IO`内存时；会用到内存屏障：

     ```c
     include/linux/compiler-gcc.h:
     
     #define barrier() __asm____volatile__("": : :"memory")
     
     ```

     它就是防止编译器对读写IO端口和IO内存指令的优化而设计的错误。

   - `Instructionlist`中有多条指令的时候，可以在一对引号中列出全部指令；也可以将一条或几条指令放在一对引号中，所有指令放在多对引号中。如果是前者，可以将所有指令放在一行，则必须用分号（;）或换行符（/n）将它们分开：

     ```c
     static inline int atomic_add_return(int i, atomic_t *v) 
     
     __asm__ __volatile__("@ atomic_add_return\n"     // @开始的内容是注释
     
     "1: ldrex %0, [%2]\n"            // 1：是代码中的局部标签 
     
     " add %0, %0, %3\n" 
     
     " strex %1, %0, [%2]\n"  
     
     " teq %1, #0\n" 
     
     " bne 1b"                    //向后跳转到1处执行，b表示backward; bne 1f,表示向前跳转到1
     
     : "=&r" (result), "=&r" (tmp)             // %0, %1
     
     : "r" (&v->counter), "Ir" (i)              //%2, %3
     
     : "cc");
     
     ```

5.  Output

   - 用来指定当前内联汇编的输出

6.  Input

   - 用来指定当前内联汇编的输入。

7.  Output和Input中，格式为形如”constraint”(variable)的列表,用逗号分隔。如：

   ```
   : "=&r" (result), "=&r" (tmp) 
   
   : "r" (&v->counter), "Ir" (i)
   
   ```

8.  Clobber/Modify

   - 有时候，当你想通知GCC当前内联汇编语句可能对某些寄存器和内存进行修改，希望GCC将这一点考虑进去，此时就可以在Clobber/Modify域中进行声明这些寄存器和内存。这种情况一般发生在一个寄存器出现在Instructionlist，但不是有Output/Input操作表达式所指 定的，也不是在一些Output/Input操作表达式使用“r”约束时有GCC为其选择的，同时此寄存器被Instructionlist修改，而这个寄存器只是供当前内联汇编使用的情况。
- 例如：`__asm__ (“mov R0, #0x34” ::: “R0”)` 寄存器R0出现在Instructionlist中，且被mov指令修改，但却未被任何Output/Input操作表达式指定，所以需要在Clobber/Modify域中指定“R0”，让GCC知道这一点。
   - 因为你在Output/Input操作表达式所指定的寄存器，或当你为一些Output/Input表达式使用“r”约束，上GCC为你选择一个寄存器，寄存器对这些寄存器是非常清楚的， 它知道这些寄存器是被修改的，不需要在Clobber/Modify域中在声明它们。除此之外，GCC对剩下的寄存器中那些会被当前内联汇编修改一无所知。所以，如果当前内联汇编修改了这些寄存器，就最好在Clobber/Modify域中声明，让GCC针对这些寄存器做相应的处理，否则可能会造成寄存器 的不一致，造成程序执行错误。
   - **如果一个内联汇编语句的****Clobber/Modify****域存在****"memory"****，那么****GCC****会保证在此内联汇编之前，如果某个内存的内容被装入了寄存器，那么在这个内联汇编之后，如果需要使用这个内存处的内容，就会直接到这个内存处重新读取，而不是使用被存放在寄存器中的拷贝。因为这个时候寄存器中的拷贝已经很可能和内存处的内容不一致了。**
   - **这只是使用****"memory"****时，****GCC****会保证做到的一点，但这并不是全部。因为使用****"memory"****是向****GCC****声明内存发生了变化，而内存发生变化带来的影响并不止这一点。**
   - **intmain(int __argc, char\* __argv[])  {  int\* __p =(int\*)__argc;  (\*__p) =9999;  __asm__("":::"memory");  if((\*__p)== 9999)  return 5;  return (\*__p);  }**
   
9. **本例中，如果没有那条内联汇编语句，那个****if****语句的判断条件就完全是一句废话。****GCC****在优化时会意识到这一点，而直接只生成****return5****的汇编代码，而不会再生成****if****语句的相关代码，而不会生成****return(\*__p)****的相关代码。但你加上了这条内联汇编语句，它除了声明内存变化之外，什么都没有做。但****GCC****此时就不能简单的认为它不需要判断都知道****(\*__p)****一定与****9999****相等，它只有老老实实生成这条****if****语句的汇编代码，一起相关的两个****return****语句相关代码。**

10.  **另外在****linux****内核中内存屏障也是基于它实现的****include/asm/system.h****中** **#define barrier() _asm__volatile_("": : :"memory")** **主要是保证程序的执行遵循顺序一致性。呵呵，有的时候你写代码的顺序，不一定是最终执行的顺序，这个是处理器有关的。**
