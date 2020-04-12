# native-antutu与geekbench在busybox中运行的环境配置

## 1. 可执行文件

### 1.1 native-antutu

- antutu-native-hook-v6.libs
- libabenchmark.so

### 1.2 geekbench

- geekbench_aarch64
- geekbench.plar



## 2. 查找依赖库——ldda

### 2.1 ldda工具介绍

- ldda 路径：tiny-formatter/tool。

- ldda 命令可以获取可执行文件或链接库直接依赖和间接依赖的所有库，并将这些库从手机相应的目录中pull到本地。如下所示：

  ```
  haibin.xu@tj03809pcu1:~/antutuv6-geekbench-v4.3-mboot/system.mboot-sharkl3$ ldda libabenchmark.so 
  	libabenchmark.so: libz.so
  	libabenchmark.so: liblog.so
  	libabenchmark.so: libandroid.so
  	libabenchmark.so: libGLESv2.so
  	libabenchmark.so: libc.so
  	libabenchmark.so: libm.so
  	libabenchmark.so: libstdc++.so
  	libabenchmark.so: libdl.so
  ---------------------------                                                                         
  	/system/lib64/libz.so
  	/system/lib64/liblog.so
  	/system/lib64/libandroid.so
  	/system/lib64/libGLESv2.so
  	/system/lib64/libc.so
  	...
  
  ```

- ldda 命令后面可同时获取多个文件的共同的依赖库，并将这些依赖库按照其在手机内部原有的路径保存在本地；

### 2.2 Android版本

- 如果我们从Android P版本的手机中获取linker64、依赖库，那么在busybox环境下运行，会有如下结果：

  ```
  mboot:/system.mboot/bin# ./run.antutu.sh 
  This is linker64, the helper program for dynamic executables.
  
  ```

- 这是由于Android P版本中的linker，不支持以**/system/bin/linker [可执行文件]**的形式来执行文件，所以这里请注意，务必使用AndroidQ版本下的linker64、依赖库等文件。



## 3. 自动化执行脚本

- 为方便使用native-antutu与geekbench，我们分别编写了两个小脚本：

  1. run.antutu.sh

     ```shell
     export LD_LIBRARY_PATH=/system.mboot/system/lib64:/system.mboot/apex/com.android.runtime/lib64:$LD_LIBRARY_PATH
     export PATH=/system.mboot/system/bin:$PATH
     cd /system.mboot/system/bin/
     linker64 /system.mboot/system/bin/antutu-native-hook-v6.libs $@
     
     ```

  2. run.geekbench.sh

     ```shell
     export LD_LIBRARY_PATH=/system.mboot/system/lib64:/system.mboot/apex/com.android.runtime/lib64:$LD_LIBRARY_PATH
     export PATH=/system.mboot/system/bin:$PATH
     cd /system.mboot/system/bin/
     linker64 /system.mboot/system/bin/geekbench_aarch64 $@
     
     ```

     

## 4. 应用依赖环境文件调整

- 根据 ldda 命令获取 antutu-native-hook-v6.libs、libabenchmark.so、geekbench_aarch64依赖的所有库和链接器，命令如下：

  ```shell
  ldda antutu-native-hook-v6.libs libabenchmark.so geekbench_aarch64
  
  ```

- 执行完 ldda 操作后，会在当前目录下生成 ldda-adb.files 目录，其框架如下：

  ```shell
  haibin.xu@tj03809pcu1:~/antutuv6-geekbench-v4.3-mboot/system.mboot-sharkl3$ tree ldda-adb.files/
  ldda-adb.files/
  |-- apex
  |   `-- com.android.runtime
  |       `-- lib64
  |           |-- libandroidicu.so
  |           |-- libicui18n.so
  |           |-- libicuuc.so
  |           `-- libnativehelper.so
  `-- system
      |-- bin
      |   `-- linker64
      `-- lib64
          |-- android.frameworks.bufferhub@1.0.so
          |-- android.hardware.configstore-utils.so
          |-- android.hardware.configstore@1.0.so
  		|-- ...
  
  ```

- 我们需要对 ldda-adb.files 目录进行相应调整，如下：

  ```shell
  mv dda-adb.files system.mboot
  cp run.antutu.sh un.geekbench.sh system.mboot/
  cp antutu-native-hook-v6.libs libabenchmark.so geekbench_aarch64 geekbench.plar system.mboot/system/bin/
  
  ```



## 5. mboot模式下运行

- 将 system.mboot 目录 push 到手机：

  ```shell
  sudo adb push system.mboot /
  sudo adb shell chmod 777 -R /system.mboot
  
  ```

- antutu 运行：

  ```shell
  mboot:/system.mboot# ./run.antutu.sh 30
  ========RAM========
  RAM:  5660  (Ram_Speed: 28239, Random_Access: 59835)
  ========CPU_MATH========
  CPU_MATH:  3910  (FFT: 22827, GEMM: 46360)
  ========CPU_APP========
  CPU_APP:  138  (MAP: 64291, PNG: 0, 2D_Physics: 108548)
  ========CPU_MultiCore========
  CPU_MultiCore:  3717  (MultiTask: 180803, MultiThread: 254977, 3D_physX: 2549)
  ========Other test case========
  HASH:  8644
  Chess:  21833
  Storage:  194069
  Random_IO:  16809412
  
  ```

- geekbench 运行：

  ```shell
  mboot:/system.mboot# ./run.geekbench.sh 
  Geekbench 4.3.0-RC1 Source : http://www.geekbench.com/
  
  System Information
    Operating System              Android
    Governor                      schedutil
    Memory                        1.78 GB 
  
  Processor Information
    Name                          ARM Unisoc
    Topology                      1 Processor, 8 Cores
    Identifier                    ARM implementer 65 architecture 8 variant 1 part 3333 revision 0
    Cluster 1                     4 Cores @ 1.20 GHz
    Cluster 2                     4 Cores @ 1.60 GHz
  
  
  Single-Core
    AES                             499             384.9 MB/sec
    LZMA                            861              1.35 MB/sec
    JPEG                            911         7.34 Mpixels/sec
    Canny                           824         11.4 Mpixels/sec
    Lua                             753             793.4 KB/sec
    Dijkstra                       1181            799.3 KTE/sec
    SQLite                          703           19.5 Krows/sec
    HTML5 Parse                     877              3.98 MB/sec
    HTML5 DOM                       732      663.6 KElements/sec
    Histogram Equalization          774         24.2 Mpixels/sec
    PDF Rendering                   842         22.4 Mpixels/sec
    LLVM                           1475      101.5 functions/sec
    Camera                          835          2.32 images/sec
    SGEMM                           211              4.48 Gflops
    SFFT                            507              1.27 Gflops
    N-Body Physics                  475         355.3 Kpairs/sec
    Ray Tracing                     504         73.7 Kpixels/sec
    Rigid Body Physics              894               2617.4 FPS
    HDR                             910         3.30 Mpixels/sec
    Gaussian Blur                   509         8.92 Mpixels/sec
    Speech Recognition              605           5.18 Words/sec
    Face Detection                  648    189.4 Ksubwindows/sec
    Memory Copy                     783              2.17 GB/sec
    Memory Latency                 2796                 154.8 ns
    Memory Bandwidth               1019              5.44 GB/sec
  
  Multi-Core
    AES                            2951              2.22 GB/sec
    LZMA                           4447              6.95 MB/sec
    JPEG                           5684         45.7 Mpixels/sec
    Canny                          4444         61.6 Mpixels/sec
    Lua                            4561              4.69 MB/sec
    Dijkstra                       3807             2.58 MTE/sec
    SQLite                         4189          116.1 Krows/sec
    HTML5 Parse                    5368              24.4 MB/sec
    HTML5 DOM                      2079       1.88 MElements/sec
    Histogram Equalization         4800        150.0 Mpixels/sec
    PDF Rendering                  4421        117.5 Mpixels/sec
    LLVM                           7383      507.6 functions/sec
    Camera                         5152          14.3 images/sec
    SGEMM                          1166              24.7 Gflops
    SFFT                           3193              7.96 Gflops
    N-Body Physics                 2703          2.02 Mpairs/sec
    Ray Tracing                    2994        437.2 Kpixels/sec
    Rigid Body Physics             5555              16264.2 FPS
    HDR                            5087         18.4 Mpixels/sec
    Gaussian Blur                  2168         38.0 Mpixels/sec
    Speech Recognition             2481           21.2 Words/sec
    Face Detection                 3997     1.17 Msubwindows/sec
    Memory Copy                    1096              3.04 GB/sec
    Memory Latency                 2673                 161.9 ns
    Memory Bandwidth               1013              5.41 GB/sec
  
  Benchmark Summary
    Single-Core Score              844
      Crypto Score                   499
      Integer Score                  877
      Floating Point Score           543
      Memory Score                  1306
    Multi-Core Score              3363
      Crypto Score                  2951
      Integer Score                 4524
      Floating Point Score          2975
      Memory Score                  1437
  
  Upload results to the Geekbench Browser? [Y/n]n
  
  ```

  

  

  

  

  

  

  

