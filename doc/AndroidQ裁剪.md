# AndroidQ裁剪

## 开机启动优化

- 查看系统启动时间的命令

  `sudo adb logcat -b events | grep boot`

- 启动阶段主要事件

  |                                name | description                                                  |
  | ----------------------------------: | ------------------------------------------------------------ |
  |                 boot_progress_start | 代表着Android屏幕点亮，开始显示启动动画. 系统进入用户空间，标志着kernel启动完成 |
  |         boot_progress_preload_start | Zygote启动                                                   |
  |           boot_progress_preload_end | Zygote结束                                                   |
  |            boot_progress_system_run | SystemServer ready,开始启动Android系统服务，如PMS，APMS等    |
  |             boot_progress_pms_start | PMS开始扫描安装的应用                                        |
  | boot_progress_pms_system_scan_start | PMS先行扫描/system目录下的安装包                             |
  |   boot_progress_pms_data_scan_start | PMS扫描/data目录下的安装包                                   |
  |          boot_progress_pms_scan_end | PMS扫描结束                                                  |
  |             boot_progress_pms_ready | PMS就绪                                                      |
  |             boot_progress_ams_ready | AMS就绪                                                      |
  |         boot_progress_enable_screen | AMS启动完成后开始激活屏幕，从此以后屏幕才能响应用户的触摸，它在WindowManagerService发出退出开机动画的时间节点之前，而真正退出开机动画还会花费少许时间，具体依赖animation zip 包中的desc.txt。wm_boot_animation_done才是用户感知到的动画结束时间节点 |
  |                    sf_stop_bootanim | SF设置service.bootanim.exit属性值为1，标志系统要结束开机动画了，可以用来跟踪开机动画结尾部分消耗的时间 |
  |              wm_boot_animation_done | 开机动画结束，这一步用户能直观感受到开机结束                 |

  > 1. Kernel part : boot_progress_start
  > 2. Zygote time : boot_progress_preload_end - boot_progress_preload_start
  > 3. /system Scan time : boot_progress_pms_data_scan_start - boot_progress_pms_system_scan_start
  > 4. /data Scan time : boot_progress_pms_scan_end- boot_progress_pms_data_scan_start
  > 5. Home activity start time : boot_progress_enable_screen- boot_progress_ams_ready



- 各阶段分析

  | 启动阶段主要事件                    | 时间（ms） | 描述                                                         | 时间差值 |
  | ----------------------------------- | ---------- | ------------------------------------------------------------ | -------- |
  | boot_progress_start                 | 9185       | 代表着Android屏幕点亮，开始显示启动动画. 系统进入用户空间，标志着kernel启动完成 | 0        |
  | boot_progress_preload_start         | 11344      | Zygote preload启动                                           | 2159     |
  | boot_progress_preload_end           | 14350      | Zygote preload结束                                           | 3006     |
  | boot_progress_system_run            | 14847      | SystemServer ready,开始启动Android系统服务，如PMS，APMS等    | 497      |
  | boot_progress_pms_start             | 15804      | PMS开始扫描安装的应用                                        | 957      |
  | boot_progress_pms_system_scan_start | 15909      | PMS先行扫描/system目录下的安装包                             | 105      |
  | boot_progress_pms_data_scan_start   | 18870      | PMS扫描/data目录下的安装包                                   | 2961     |
  | boot_progress_pms_scan_end          | 18889      | PMS扫描结束                                                  | 19       |
  | boot_progress_pms_ready             | 19283      | PMS就绪                                                      | 394      |
  | boot_progress_ams_ready             | 23368      | AMS就绪                                                      | 4085     |
  | boot_progress_enable_screen         | 23698      | AMS启动完成后开始激活屏幕，从此以后屏幕才能响应用户的触摸，它在WindowManagerService发出退出开机动画的时间节点之前，而真正退出开机动画还会花费少许时间，具体依赖animation zip 包中的desc.txt。wm_boot_animation_done才是用户感知到的动画结束时间节点 | 330      |
  | sf_stop_bootanim                    | 26607      | SF设置service.bootanim.exit属性值为1，标志系统要结束开机动画了，可以用来跟踪开机动画结尾部分消耗的时间 | 2909     |
  | wm_boot_animation_done              | 26609      | 开机动画结束，这一步用户能直观感受到开机结束                 | 2        |

- 从kernel启动完成到Zygote启动耗时2159ms，期间有如下相关进程：

  ![1566784614111](./picture/AndroidQ优化-1.png)
  
- 共有ueventd、logd、servicemanager、hwservicemanager、vold、keymaster、apexd、netd，主要耗时是在logd、keymaster、netd三个进程相比于其前一个进程启动较晚。

- 在ueventd、logd之间，我们从init.rc可以看出，两者之间只有一个`exec_start apexd-bootstrap`，其他的都是文件（夹）操作，我们从kmsg图中也能看出来，期间主要是`exec_start apexd-bootstrap`和`wait_for_coldboot_done`最耗时：

  ![1566785453859](./picture/AndroidQ优化-2.png)

- 在vold、keymaster之间，keymaster在vold启动大概1s后才启动，我们从下图中可以看出，这期间主要是fs相关的进程：libfs_mgr、fs、vdc、post-fs

  ![1566800184591](./picture/AndroidQ优化-3.png)

- apexd、netd之间，netd在apexd启动大概0.5s后才启动，我们从下图中可以看出，这期间主要耗时在：apexd、vdc

  ![1566801154605](./picture/AndroidQ优化-4.png)

- boot_progress_preload_start 到 boot_progress_preload_end，即zygote启动到结束共耗时3006ms，我们从抓取的logcat中分析，这期间主要是PreloadClasses、PreloadResources，我们通过合入http://review.source.unisoc.com/gerrit/#/c/613405/提交， 可以将这段时间缩短到0.8s， 而在这缩短的0.8s中，我们通过在frameworks/base/graphics/java/android/graphics/fonts/SystemFonts.java 添加log：

  ```c
  102     private static @Nullable ByteBuffer mmap(@NonNull String fullPath) {
  103         try (FileInputStream file = new FileInputStream(fullPath)) {
  104             final FileChannel fileChannel = file.getChannel();
  105             final long fontSize = fileChannel.size();
  106             Log.e(TAG, "Haibin: mapping font file " + fullPath);
  107             return fileChannel.map(FileChannel.MapMode.READ_ONLY, 0, fontSize);
  108         } catch (IOException e) {
  109             Log.e(TAG, "Error mapping font file " + fullPath);
  110             return null;
  111         }
  112     }
  
  ```
  
  发现有0.65s时间是SystemFonts在解析字体，这部分可以做进一步优化，字体配置文件在/system/etc/fonts.xml，我们可以在tiny-formatter中将筛选后的配置文件替换原始文件，这样boot_progress_preload_start 到 boot_progress_preload_end这个阶段基本上能优化到最佳。
  
  ```c
  01-01 00:07:08.409 I/boot_progress_preload_start(  391): 11722
  01-01 00:07:08.421 I/zygote  (  392): Explicit concurrent copying GC freed 298(39KB) AllocSpace objects, 0(0B) LOS objects, 98% free, 24KB/1560KB, paused 143us total 13.696ms
  01-01 00:07:08.431 I/zygote  (  392): Explicit concurrent copying GC freed 5(32KB) AllocSpace objects, 0(0B) LOS objects, 98% free, 24KB/1560KB, paused 65us total 8.760ms
  01-01 00:07:08.431 D/Zygote32Timing(  392): PostZygoteInitGC took to complete: 23ms
  01-01 00:07:08.431 D/Zygote32Timing(  392): ZygoteInit took to complete: 26ms
  01-01 00:07:08.497 I/Zygote  (  392): Accepting command socket connections
  01-01 00:07:08.503 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:08.516 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-Thin.ttf
  01-01 00:07:08.535 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-ThinItalic.ttf
  01-01 00:07:08.539 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-Light.ttf
  01-01 00:07:08.543 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-LightItalic.ttf
  01-01 00:07:08.547 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-Regular.ttf
  01-01 00:07:08.551 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-Italic.ttf
  01-01 00:07:08.554 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-Medium.ttf
  01-01 00:07:08.558 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/Roboto-MediumItalic.ttf
  ......
  01-01 00:07:09.176 E/SystemFonts(  391): Haibin: mapping font file /system/fonts/NotoSansSoraSompeng-Regular.otf
  
  01-01 00:07:09.198 I/boot_progress_preload_end(  391): 12512
  
  ```
  
- boot_progress_preload_end 到 boot_progress_system_run 耗时498ms，从logcat中分析，此0.5s内主要是zygote创建、启动system server进程，可优化空间不大：

  ```
  01-01 00:07:09.198 I/boot_progress_preload_end(  391): 12512
  
  01-01 00:07:09.199 D/Zygote64Timing(  391): ZygotePreload took to complete: 790ms
  01-01 00:07:09.207 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:09.214 I/zygote64(  391): Explicit concurrent copying GC freed 15400(910KB) AllocSpace objects, 1(20KB) LOS objects, 84% free, 273KB/1809KB, paused 64us total 14.685ms
  01-01 00:07:09.231 I/zygote64(  391): Explicit concurrent copying GC freed 4257(136KB) AllocSpace objects, 0(0B) LOS objects, 90% free, 169KB/1705KB, paused 34us total 10.202ms
  01-01 00:07:09.231 D/Zygote64Timing(  391): PostZygoteInitGC took to complete: 33ms
  01-01 00:07:09.232 D/Zygote64Timing(  391): ZygoteInit took to complete: 825ms
  01-01 00:07:09.233 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:09.234 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:09.308 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:09.351 D/Zygote  (  391): Forked child process 743
  01-01 00:07:09.351 I/Zygote  (  391): System server process 743 has been created
  01-01 00:07:09.355 I/Zygote  (  391): Accepting command socket connections
  01-01 00:07:09.392 I/system_server(  743): The ClassLoaderContext is a special shared library.
  01-01 00:07:09.409 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:09.436 I/system_server(  743): The ClassLoaderContext is a special shared library.
  01-01 00:07:09.467 I/chatty  (  743): uid=1000 system_server identical 1 line
  01-01 00:07:09.481 I/system_server(  743): The ClassLoaderContext is a special shared library.
  01-01 00:07:09.509 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:09.575 I/service_manager_slow(  743): [19,installd]
  01-01 00:07:09.680 I/SystemServer(  743): InitBeforeStartServices
  01-01 00:07:09.684 I/system_server_start(  743): [1,12992,12992]
  01-01 00:07:09.684 W/SystemServer(  743): System clock is before 1970; setting to 1970.
  01-01 00:07:09.687 W/SystemServer(  743): Timezone not set; setting to GMT.
  01-01 00:07:09.697 I/SystemServer(  743): Entered the Android system server!
  
  01-01 00:07:09.697 I/boot_progress_system_run(  743): 13010
  
  ```

- boot_progress_system_run 到 boot_progress_pms_start 耗时1519ms，从logcat中分析此期间主要是启动一些主要的service：Installer、DeviceIdentifiersPolicyService、ActivityManager、PowerManager、RecoverySystemService、LightsService、SunLightService、DisplayManagerService、PackageManagerService。

  ```
  01-01 00:07:09.697 I/boot_progress_system_run(  743): 13010
  
  01-01 00:07:09.697 I/sysui_multi_action(  743): [757,804,799,boot_system_server_init,801,13010,802,1]
  01-01 00:07:09.610 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 1 line
  01-01 00:07:09.711 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:09.750 I/ServiceManagement(  410): Registered android.hardware.sensors@1.0::ISensors/default (start delay of 5224ms)
  01-01 00:07:09.750 I/ServiceManagement(  410): Removing namespace from process name android.hardware.sensors@1.0-service to sensors@1.0-service.
  01-01 00:07:09.751 I/android.hardware.sensors@1.0-service(  410): Registration complete for android.hardware.sensors@1.0::ISensors/default.
  01-01 00:07:09.811 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:09.912 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.004 E/UsbAlsaJackDetectorJNI(  743): Can't register UsbAlsaJackDetector native methods
  01-01 00:07:10.013 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.113 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 1 line
  01-01 00:07:10.214 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.224 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:10.225 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:10.235 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:10.235 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:10.315 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.415 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.474 E/libtrusty(  419): tipc_connect: can't connect to tipc service "com.android.trusty.faceid" (err=110)
  01-01 00:07:10.474 E/Face-CA (  419): tipc_connect() failed! 
  01-01 00:07:10.474 E/Face-CA (  419): open_tee_faceid: connect faceid ta error(-110).
  01-01 00:07:10.474 E/FaceIdHal(  419): open tee fail.
  01-01 00:07:10.474 E/vendor.sprd.hardware.face@1.0-service(  419): Can't open face methods, error: -1
  01-01 00:07:10.474 E/vendor.sprd.hardware.face@1.0-service(  419): Can't open HAL module
  01-01 00:07:10.478 I/ServiceManagement(  419): Registered vendor.sprd.hardware.face@1.0::IExtBiometricsFace/default (start delay of 5882ms)
  01-01 00:07:10.479 I/ServiceManagement(  419): Removing namespace from process name vendor.sprd.hardware.face@1.0-service to face@1.0-service.
  01-01 00:07:10.516 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.542 W/asset   (  743): unable to execute idmap2: Permission denied
  01-01 00:07:10.542 W/AssetManager(  743): 'idmap2 --scan' failed: no static="true" overlays targeting "android" will be loaded
  01-01 00:07:10.614 D/SystemServerTiming(  743): InitBeforeStartServices took to complete: 934ms
  01-01 00:07:10.614 I/SystemServer(  743): StartServices
  01-01 00:07:10.614 I/SystemServer(  743): StartWatchdog
  01-01 00:07:10.617 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.656 D/SystemServerTiming(  743): StartWatchdog took to complete: 42ms
  01-01 00:07:10.657 I/SystemServer(  743): Reading configuration...
  01-01 00:07:10.657 I/SystemServer(  743): ReadingSystemConfig
  01-01 00:07:10.660 D/SystemServerTiming(  743): ReadingSystemConfig took to complete: 3ms
  01-01 00:07:10.660 I/SystemServer(  743): StartInstaller
  01-01 00:07:10.660 D/SystemServerInitThreadPool(  743): Started executing ReadingSystemConfig
  01-01 00:07:10.662 I/SystemServiceManager(  743): Starting com.android.server.pm.InstallerEx
  01-01 00:07:10.681 D/SystemServerTiming(  743): StartInstaller took to complete: 22ms
  01-01 00:07:10.681 I/SystemServer(  743): DeviceIdentifiersPolicyService
  01-01 00:07:10.681 I/SystemServiceManager(  743): Starting com.android.server.os.DeviceIdentifiersPolicyService
  01-01 00:07:10.689 D/SystemServerTiming(  743): DeviceIdentifiersPolicyService took to complete: 8ms
  01-01 00:07:10.689 I/SystemServer(  743): UriGrantsManagerService
  01-01 00:07:10.689 I/SystemServiceManager(  743): Starting com.android.server.uri.UriGrantsManagerService$Lifecycle
  01-01 00:07:10.709 D/SystemServerTiming(  743): UriGrantsManagerService took to complete: 19ms
  01-01 00:07:10.709 I/SystemServer(  743): StartActivityManager
  01-01 00:07:10.709 I/SystemServiceManager(  743): Starting com.android.server.wm.ActivityTaskManagerService$Lifecycle
  01-01 00:07:10.729 W/SystemConfig(  743): No directory /product/etc/sysconfig, skipping
  01-01 00:07:10.738 I/SystemServiceManager(  743): Starting com.android.server.am.ActivityManagerService$Lifecycle
  01-01 00:07:10.746 W/SystemConfig(  743): No directory /product_services/etc/sysconfig, skipping
  01-01 00:07:10.746 W/SystemConfig(  743): No directory /product_services/etc/permissions, skipping
  01-01 00:07:10.746 D/SystemServerInitThreadPool(  743): Finished executing ReadingSystemConfig
  01-01 00:07:10.805 I/ActivityManager(  743): Memory class: 192
  01-01 00:07:10.718 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.818 W/ServiceManager(  470): Service package_native didn't start. Returning NULL
  01-01 00:07:10.819 E/storaged(  470): getService package_native failed
  01-01 00:07:10.825 I/storaged(  470): storaged: Start
  01-01 00:07:10.827 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.880 D/BatteryStatsImpl(  743): Reading daily items from /data/system/batterystats-daily.xml
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): Error reading battery statistics
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): java.io.FileNotFoundException: /data/system/batterystats.bin: open failed: ENOENT (No such file or directory)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at libcore.io.IoBridge.open(IoBridge.java:496)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at java.io.FileInputStream.<init>(FileInputStream.java:159)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.internal.os.AtomicFile.openRead(AtomicFile.java:157)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.internal.os.AtomicFile.readFully(AtomicFile.java:162)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.internal.os.BatteryStatsImpl.readLocked(BatteryStatsImpl.java:13375)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerService.<init>(ActivityManagerService.java:2525)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerServiceEx.<init>(ActivityManagerServiceEx.java:91)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerService$Lifecycle.<init>(ActivityManagerService.java:2239)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at java.lang.reflect.Constructor.newInstance0(Native Method)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at java.lang.reflect.Constructor.newInstance(Constructor.java:343)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServiceManager.startService(SystemServiceManager.java:101)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerService$Lifecycle.startService(ActivityManagerService.java:2245)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServer.startBootstrapServices(SystemServer.java:674)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServer.run(SystemServer.java:524)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): Caused by: android.system.ErrnoException: open failed: ENOENT (No such file or directory)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at libcore.io.Linux.open(Native Method)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at libcore.io.ForwardingOs.open(ForwardingOs.java:167)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at libcore.io.BlockGuardOs.open(BlockGuardOs.java:252)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	at libcore.io.IoBridge.open(IoBridge.java:482)
  01-01 00:07:10.889 E/BatteryStatsImpl(  743): 	... 17 more
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): Error reading battery history
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): java.io.FileNotFoundException: /data/system/battery-history/0.bin: open failed: ENOENT (No such file or directory)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at libcore.io.IoBridge.open(IoBridge.java:496)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at java.io.FileInputStream.<init>(FileInputStream.java:159)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.internal.os.AtomicFile.openRead(AtomicFile.java:157)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.internal.os.AtomicFile.readFully(AtomicFile.java:162)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.internal.os.BatteryStatsImpl.readLocked(BatteryStatsImpl.java:13394)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerService.<init>(ActivityManagerService.java:2525)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerServiceEx.<init>(ActivityManagerServiceEx.java:91)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerService$Lifecycle.<init>(ActivityManagerService.java:2239)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at java.lang.reflect.Constructor.newInstance0(Native Method)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at java.lang.reflect.Constructor.newInstance(Constructor.java:343)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServiceManager.startService(SystemServiceManager.java:101)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.am.ActivityManagerService$Lifecycle.startService(ActivityManagerService.java:2245)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServer.startBootstrapServices(SystemServer.java:674)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServer.run(SystemServer.java:524)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): Caused by: android.system.ErrnoException: open failed: ENOENT (No such file or directory)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at libcore.io.Linux.open(Native Method)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at libcore.io.ForwardingOs.open(ForwardingOs.java:167)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at libcore.io.BlockGuardOs.open(BlockGuardOs.java:252)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	at libcore.io.IoBridge.open(IoBridge.java:482)
  01-01 00:07:10.890 E/BatteryStatsImpl(  743): 	... 17 more
  01-01 00:07:10.900 I/BatteryStatsService(  743): Using power.stats HAL
  01-01 00:07:10.903 W/BatteryStatsService(  743): Rail information is not available
  01-01 00:07:10.903 W/BatteryStatsService(  743): Rail energy data is not available
  01-01 00:07:10.908 E/BluetoothAdapter(  743): Bluetooth binder is null
  --------- beginning of radio
  01-01 00:07:10.921 D/TelephonyManager(  743): No /proc/cmdline exception=java.io.FileNotFoundException: /proc/cmdline: open failed: EACCES (Permission denied)
  01-01 00:07:10.921 D/TelephonyManager(  743): /proc/cmdline=
  01-01 00:07:10.928 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:10.935 E/BatteryExternalStatsWorker(  743): no controller energy info supplied for telephony
  01-01 00:07:10.943 I/KernelCpuUidFreqTimeReader(  743): mPerClusterTimesAvailable=false
  01-01 00:07:10.977 I/commit_sys_config_file(  743): [batterystats,10]
  01-01 00:07:10.982 I/commit_sys_config_file(  743): [batterystats,4]
  01-01 00:07:10.999 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.memtrack@1.0::IMemtrack/default in either framework or device manifest.
  01-01 00:07:10.999 E/memtrack(  743): Couldn't load memtrack module
  01-01 00:07:10.999 W/android.os.Debug(  743): failed to get memory consumption info: -1
  01-01 00:07:11.009 I/AppOps  (  743): No existing app ops /data/system/appops.xml; starting empty
  01-01 00:07:11.024 I/IntentFirewall(  743): Read new rules (A:0 B:0 S:0)
  01-01 00:07:11.028 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:11.074 D/AppOps  (  743): AppOpsService published
  01-01 00:07:11.091 D/SystemServerTiming(  743): StartActivityManager took to complete: 382ms
  01-01 00:07:11.092 I/SystemServer(  743): StartPowerManager
  01-01 00:07:11.092 I/SystemServiceManager(  743): Starting com.android.server.power.PowerManagerService
  01-01 00:07:11.120 D/PowerManagerService(  743): Acquiring suspend blocker "PowerManagerService.Display".
  01-01 00:07:11.125 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.power@1.0::IPower/default in either framework or device manifest.
  01-01 00:07:11.126 I/PowerManagerService-JNI(  743): Couldn't load power HAL service
  01-01 00:07:11.129 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:11.131 D/SystemServerTiming(  743): StartPowerManager took to complete: 39ms
  01-01 00:07:11.131 I/SystemServer(  743): StartThermalManager
  01-01 00:07:11.131 I/SystemServiceManager(  743): Starting com.android.server.power.ThermalManagerService
  01-01 00:07:11.137 D/SystemServerTiming(  743): StartThermalManager took to complete: 6ms
  01-01 00:07:11.137 I/SystemServer(  743): InitPowerManagement
  01-01 00:07:11.140 D/SystemServerTiming(  743): InitPowerManagement took to complete: 3ms
  01-01 00:07:11.140 I/SystemServer(  743): StartRecoverySystemService
  01-01 00:07:11.140 I/SystemServiceManager(  743): Starting com.android.server.RecoverySystemService
  01-01 00:07:11.143 D/SystemServerTiming(  743): StartRecoverySystemService took to complete: 3ms
  01-01 00:07:11.144 V/RescueParty(  743): Disabled because of active USB connection
  01-01 00:07:11.144 I/SystemServer(  743): StartLightsService
  01-01 00:07:11.145 I/SystemServiceManager(  743): Starting com.android.server.lights.LightsService
  01-01 00:07:11.157 D/SystemServerTiming(  743): StartLightsService took to complete: 13ms
  01-01 00:07:11.157 I/SystemServer(  743): StartSidekickService
  01-01 00:07:11.157 D/SystemServerTiming(  743): StartSidekickService took to complete: 0ms
  01-01 00:07:11.160 I/SystemServiceManager(  743): Starting com.android.server.display.SunLightService
  01-01 00:07:11.160 I/SystemServer(  743): StartDisplayManager
  01-01 00:07:11.160 I/SystemServiceManager(  743): Starting com.android.server.display.DisplayManagerService
  01-01 00:07:11.174 D/SystemServerTiming(  743): StartDisplayManager took to complete: 13ms
  01-01 00:07:11.174 I/SystemServer(  743): isCCSASupport = false
  01-01 00:07:11.174 I/sysui_multi_action(  743): [757,804,799,boot_package_manager_init_start,801,14487,802,1]
  01-01 00:07:11.175 I/SystemServer(  743): StartPackageManagerService
  01-01 00:07:11.175 I/Watchdog(  743): Pausing HandlerChecker: main thread for reason: packagemanagermain. Pause count: 1
  01-01 00:07:11.191 I/DisplayManagerService(  743): Display device added: DisplayDeviceInfo{"Built-in Screen": uniqueId="local:0", 1080 x 1920, modeId 2, defaultModeId 2, supportedModes [{id=1, width=720, height=1280, fps=60.0024}, {id=2, width=1080, height=1920, fps=60.0024}], colorMode 0, supportedColorModes [0], HdrCapabilities android.view.Display$HdrCapabilities@40f16308, density 480, 403.411 x 403.041 dpi, appVsyncOff 2000000, presDeadline 16666000, touch INTERNAL, rotation 0, type BUILT_IN, address {port=0}, state UNKNOWN, FLAG_DEFAULT_DISPLAY, FLAG_ROTATES_WITH_CONTENT, FLAG_SECURE, FLAG_SUPPORTS_PROTECTED_BUFFERS}
  01-01 00:07:11.204 I/commit_sys_config_file(  743): [display-state,10]
  01-01 00:07:11.205 D/SurfaceFlinger(  437): Setting power mode 2 on display 0
  01-01 00:07:11.206 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.light@2.0::ILight/default in either framework or device manifest.
  01-01 00:07:11.207 W/StrictMode(  743): No activity manager; failed to Dropbox violation.
  01-01 00:07:11.208 I/chatty  (  743): uid=1000(system) android.display identical 2 lines
  01-01 00:07:11.208 W/StrictMode(  743): No activity manager; failed to Dropbox violation.
  01-01 00:07:11.209 D/PackageManagerServiceExUtils(  743): CPU core number: 8
  01-01 00:07:11.209 W/StrictMode(  743): No activity manager; failed to Dropbox violation.
  01-01 00:07:11.210 I/DisplayManagerService(  743): Display device changed state: "Built-in Screen", ON
  01-01 00:07:11.209 W/StrictMode(  743): No activity manager; failed to Dropbox violation.
  01-01 00:07:11.211 D/PackageManagerServiceExUtils(  743): CPU core number: 8
  
  01-01 00:07:11.215 I/boot_progress_pms_start(  743): 14529
  
  ```

- boot_progress_pms_start到boot_progress_pms_system_scan_start，耗时73ms, 不需要优化

  ```c
  01-01 00:07:11.215 I/boot_progress_pms_start(  743): 14529
      
  01-01 00:07:11.227 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:11.227 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:11.229 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:11.236 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:11.236 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:11.259 W/FileUtils(  743): Failed to chmod(/data/system/packages.list): android.system.ErrnoException: chmod failed: ENOENT (No such file or directory)
  01-01 00:07:11.273 D/SELinuxMMAC(  743): Using policy file /system/etc/selinux/plat_mac_permissions.xml
  01-01 00:07:11.277 D/SELinuxMMAC(  743): Using policy file /vendor/etc/selinux/vendor_mac_permissions.xml
  01-01 00:07:11.284 D/FallbackCategoryProvider(  743): Found 1 fallback categories
  01-01 00:07:11.285 I/PackageManager(  743): No settings file; creating initial state
  01-01 00:07:11.285 I/pm_critical_info(  743): No settings file; creating initial state
  
  01-01 00:07:11.288 I/boot_progress_pms_system_scan_start(  743): 14602
  
  ```

- boot_progress_pms_system_scan_start到boot_progress_pms_data_scan_start，耗时3403ms

  ```c
  01-01 00:07:11.288 I/boot_progress_pms_system_scan_start(  743): 14602
      
  01-01 00:07:11.330 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:11.403 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /vendor/overlay , fileCount = 1
  01-01 00:07:11.421 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /vendor/overlay/framework-res__auto_generated_rro_vendor.apk
  01-01 00:07:11.421 I/PackageManager(  743): /vendor/overlay/framework-res__auto_generated_rro_vendor.apk changed; collecting certs
  01-01 00:07:11.430 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:11.461 I/PackageBackwardCompatibility(  743): Could not find android.content.pm.AndroidTestBaseUpdater, ignoring
  01-01 00:07:11.463 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.conscrypt.apex
  01-01 00:07:11.464 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.apex
  01-01 00:07:11.465 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.swcodec.apex
  01-01 00:07:11.465 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.resolv.apex
  01-01 00:07:11.466 V/apexd   (  371): Found bundled key in package /system/apex/com.android.runtime.debug.apex
  01-01 00:07:11.467 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.tzdata.apex
  01-01 00:07:11.468 V/apexd   (  371): Found bundled key in package /system/apex/com.android.runtime.debug.apex
  01-01 00:07:11.469 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.resolv.apex
  01-01 00:07:11.469 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.apex
  01-01 00:07:11.470 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.tzdata.apex
  01-01 00:07:11.471 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.swcodec.apex
  01-01 00:07:11.472 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.conscrypt.apex
  01-01 00:07:11.472 E/apexd   (  371): Can't open /product/apex for reading : No such file or directory
  01-01 00:07:11.531 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:12.035 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 5 lines
  01-01 00:07:12.136 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:12.228 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:12.229 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:12.236 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:12.238 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:12.238 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:12.337 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:13.043 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 7 lines
  01-01 00:07:13.143 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:13.230 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:13.231 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:13.240 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:13.241 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:13.244 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.055 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:13.950 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 7 lines
  01-01 00:07:14.051 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.056 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /product/overlay , fileCount = 1
  01-01 00:07:14.076 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /product/overlay/framework-res__auto_generated_rro_product.apk
  01-01 00:07:14.076 I/PackageManager(  743): /product/overlay/framework-res__auto_generated_rro_product.apk changed; collecting certs
  01-01 00:07:14.083 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:14.083 D/PackageManager(  743): No files in app dir /product_services/overlay
  01-01 00:07:14.083 D/PackageManager(  743): No files in app dir /odm/overlay
  01-01 00:07:14.083 D/PackageManager(  743): No files in app dir /oem/overlay
  01-01 00:07:14.089 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /system/framework , fileCount = 4
  01-01 00:07:14.093 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/framework/arm
  01-01 00:07:14.093 W/PackageManager(  743): Failed to parse /system/framework/arm: Missing base APK in /system/framework/arm
  01-01 00:07:14.093 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/framework/arm64
  01-01 00:07:14.093 W/PackageManager(  743): Failed to parse /system/framework/arm64: Missing base APK in /system/framework/arm64
  01-01 00:07:14.095 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/framework/oat
  01-01 00:07:14.095 W/PackageManager(  743): Failed to parse /system/framework/oat: Missing base APK in /system/framework/oat
  01-01 00:07:14.151 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.162 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/framework/framework-res.apk
  01-01 00:07:14.162 I/PackageManager(  743): /system/framework/framework-res.apk changed; collecting certs
  01-01 00:07:14.171 E/PackageManager(  743): Adding duplicate shared id: 1000 name=android
  01-01 00:07:14.172 I/pm_critical_info(  743): Adding duplicate shared id: 1000 name=android
  01-01 00:07:14.186 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:14.192 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /system/priv-app , fileCount = 8
  01-01 00:07:14.208 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/PlatformNetworkPermissionConfig
  01-01 00:07:14.208 I/PackageManager(  743): /system/priv-app/PlatformNetworkPermissionConfig changed; collecting certs
  01-01 00:07:14.210 W/PackageParser(  743): Ignoring duplicate uses-permissions/uses-permissions-sdk-m: android.permission.INSTALL_GRANT_RUNTIME_PERMISSIONS in package: com.android.shell at: Binary XML file line #127
  01-01 00:07:14.215 E/PackageManager(  743): Adding duplicate shared id: 1073 name=com.android.networkstack.permissionconfig
  01-01 00:07:14.215 I/pm_critical_info(  743): Adding duplicate shared id: 1073 name=com.android.networkstack.permissionconfig
  01-01 00:07:14.217 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/Shell
  01-01 00:07:14.217 I/PackageManager(  743): /system/priv-app/Shell changed; collecting certs
  01-01 00:07:14.220 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/GoogleExtServicesPrebuilt
  01-01 00:07:14.221 I/PackageManager(  743): /system/priv-app/GoogleExtServicesPrebuilt changed; collecting certs
  01-01 00:07:14.223 E/PackageManager(  743): Adding duplicate shared id: 2000 name=com.android.shell
  01-01 00:07:14.223 I/pm_critical_info(  743): Adding duplicate shared id: 2000 name=com.android.shell
  01-01 00:07:14.233 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/SettingsProvider
  01-01 00:07:14.233 I/PackageManager(  743): /system/priv-app/SettingsProvider changed; collecting certs
  01-01 00:07:14.234 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:14.234 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:14.234 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/ims
  01-01 00:07:14.235 I/PackageManager(  743): /system/priv-app/ims changed; collecting certs
  01-01 00:07:14.242 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:14.242 E/PackageManager(  743): Adding duplicate shared id: 1001 name=com.spreadtrum.ims
  01-01 00:07:14.242 I/pm_critical_info(  743): Adding duplicate shared id: 1001 name=com.spreadtrum.ims
  01-01 00:07:14.242 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:14.248 E/PackageManager(  743): Adding duplicate shared id: 1000 name=com.android.providers.settings
  01-01 00:07:14.248 I/pm_critical_info(  743): Adding duplicate shared id: 1000 name=com.android.providers.settings
  01-01 00:07:14.252 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.253 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/GooglePermissionControllerPrebuilt
  01-01 00:07:14.253 I/PackageManager(  743): /system/priv-app/GooglePermissionControllerPrebuilt changed; collecting certs
  01-01 00:07:14.257 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/PackageInstaller
  01-01 00:07:14.257 I/PackageManager(  743): /system/priv-app/PackageInstaller changed; collecting certs
  01-01 00:07:14.284 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/priv-app/TeleService
  01-01 00:07:14.284 I/PackageManager(  743): /system/priv-app/TeleService changed; collecting certs
  01-01 00:07:14.292 E/PackageManager(  743): Adding duplicate shared id: 1001 name=com.android.phone
  01-01 00:07:14.293 I/pm_critical_info(  743): Adding duplicate shared id: 1001 name=com.android.phone
  01-01 00:07:14.295 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:14.299 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /system/app , fileCount = 2
  01-01 00:07:14.313 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/app/ExtShared
  01-01 00:07:14.314 I/PackageManager(  743): /system/app/ExtShared changed; collecting certs
  01-01 00:07:14.323 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /system/app/PlatformCaptivePortalLogin
  01-01 00:07:14.323 I/PackageManager(  743): /system/app/PlatformCaptivePortalLogin changed; collecting certs
  01-01 00:07:14.330 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:14.331 D/PackageManager(  743): No files in app dir /vendor/priv-app
  01-01 00:07:14.331 D/PackageManager(  743): No files in app dir /vendor/app
  01-01 00:07:14.332 D/PackageManager(  743): No files in app dir /odm/priv-app
  01-01 00:07:14.332 D/PackageManager(  743): No files in app dir /odm/app
  01-01 00:07:14.332 D/PackageManager(  743): No files in app dir /oem/app
  01-01 00:07:14.335 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /product/priv-app , fileCount = 3
  01-01 00:07:14.352 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.367 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /product/priv-app/Launcher3QuickStep
  01-01 00:07:14.367 I/PackageManager(  743): /product/priv-app/Launcher3QuickStep changed; collecting certs
  01-01 00:07:14.372 I/PackageManager(  743): Permission com.android.launcher.permission.INSTALL_SHORTCUT from package com.android.launcher3 in an unknown group android.permission-group.SYSTEM_TOOLS
  01-01 00:07:14.372 I/PackageManager(  743): Permission com.android.launcher3.permission.READ_SETTINGS from package com.android.launcher3 in an unknown group android.permission-group.SYSTEM_TOOLS
  01-01 00:07:14.372 I/PackageManager(  743): Permission com.android.launcher3.permission.WRITE_SETTINGS from package com.android.launcher3 in an unknown group android.permission-group.SYSTEM_TOOLS
  01-01 00:07:14.448 W/PackageParser(  743): Ignoring duplicate uses-permissions/uses-permissions-sdk-m: android.permission.CONFIGURE_WIFI_DISPLAY in package: com.android.systemui at: Binary XML file line #152
  01-01 00:07:14.457 I/PackageParser(  743): Parse times for '/product/priv-app/SystemUI': parse=118ms, update_cache=2 ms
  01-01 00:07:14.457 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /product/priv-app/SystemUI
  01-01 00:07:14.453 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.457 I/PackageManager(  743): New shared user android.uid.systemui: id=10008
  01-01 00:07:14.458 I/PackageManager(  743): /product/priv-app/SystemUI changed; collecting certs
  01-01 00:07:14.463 E/PackageManager(  743): Adding duplicate app id: 10008 name=com.android.systemui
  01-01 00:07:14.463 I/pm_critical_info(  743): Adding duplicate app id: 10008 name=com.android.systemui
  01-01 00:07:14.554 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.636 I/PackageParser(  743): Parse times for '/product/priv-app/Settings': parse=291ms, update_cache=10 ms
  01-01 00:07:14.636 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /product/priv-app/Settings
  01-01 00:07:14.637 I/PackageManager(  743): /product/priv-app/Settings changed; collecting certs
  01-01 00:07:14.642 E/PackageManager(  743): Adding duplicate shared id: 1000 name=com.android.settings
  01-01 00:07:14.642 I/pm_critical_info(  743): Adding duplicate shared id: 1000 name=com.android.settings
  01-01 00:07:14.646 W/PackageManager(  743): Skipping provider name androidx.lifecycle.process.lifecycle-process (in package com.android.settings): name already used by com.android.systemui
  01-01 00:07:14.647 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:14.649 D/PackageManagerServiceExUtils(  743): parallelTakeAndScanPackageLI: /product/app , fileCount = 1
  01-01 00:07:14.654 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.681 D/PackageManager(  743): SPRD : takeAndScanPackageLI: /product/app/webview
  01-01 00:07:14.682 I/PackageManager(  743): /product/app/webview changed; collecting certs
  01-01 00:07:14.689 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:14.690 D/PackageManager(  743): No files in app dir /product_services/priv-app
  01-01 00:07:14.691 D/PackageManager(  743): No files in app dir /product_services/app
  01-01 00:07:14.691 I/PackageManager(  743): Finished scanning system apps. Time: 3403 ms, packageCount: 17 , timePerPackage: 200 , cached: 0
      
  01-01 00:07:14.691 I/boot_progress_pms_data_scan_start(  743): 18005
  
  ```

  我们从以上log中可以看出，boot_progress_pms_system_scan_start到boot_progress_pms_data_scan_start这一时间段的3403ms中，仅以下log就占去2588ms，所以这部分应该考虑是否可以优化。
  
  ```c
  01-01 00:07:11.463 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.conscrypt.apex
  01-01 00:07:11.464 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.apex
  01-01 00:07:11.465 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.swcodec.apex
  01-01 00:07:11.465 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.resolv.apex
  01-01 00:07:11.466 V/apexd   (  371): Found bundled key in package /system/apex/com.android.runtime.debug.apex
  01-01 00:07:11.467 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.tzdata.apex
  01-01 00:07:11.468 V/apexd   (  371): Found bundled key in package /system/apex/com.android.runtime.debug.apex
  01-01 00:07:11.469 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.resolv.apex
  01-01 00:07:11.469 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.apex
  01-01 00:07:11.470 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.tzdata.apex
  01-01 00:07:11.471 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.media.swcodec.apex
  01-01 00:07:11.472 V/apexd   (  371): Found bundled key in package /system/apex/com.google.android.conscrypt.apex
  01-01 00:07:11.472 E/apexd   (  371): Can't open /product/apex for reading : No such file or directory
  01-01 00:07:11.531 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:12.035 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 5 lines
  01-01 00:07:12.136 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:12.228 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:12.229 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:12.236 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:12.238 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:12.238 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:12.337 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:13.043 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 7 lines
  01-01 00:07:13.143 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:13.230 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.network@1.0::INetworkControl/default in either framework or device manifest.
  01-01 00:07:13.231 E/NetworkHAL(  469): INetworkControl getService failed !!!
  01-01 00:07:13.240 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.cplog_connmgr@1.0::IConnectControl/default in either framework or device manifest.
  01-01 00:07:13.241 E/CPLOG_CONNMGR(  468): main: IConnectControl getService failed [0(Success)]
  01-01 00:07:13.244 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.055 E/PackageManagerServiceExUtils(  743): waitForLatch done!
  01-01 00:07:13.950 I/chatty  (  470): uid=0(root) /system/bin/storaged identical 7 lines
  01-01 00:07:14.051 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  
  ```

- boot_progress_pms_data_scan_start到boot_progress_pms_scan_end耗时7ms，不再优化

  ```c
  01-01 00:07:14.691 I/boot_progress_pms_data_scan_start(  743): 18005
      
  01-01 00:07:14.692 D/PackageManager(  743): No files in app dir /data/app
  01-01 00:07:14.692 D/PackageManager(  743): No files in app dir /system/preloadapp
  01-01 00:07:14.692 D/PackageManager(  743): No files in app dir /product/preloadapp
  01-01 00:07:14.693 I/PackageManager(  743): Finished scanning non-system apps. Time: 1 ms, packageCount: 0 , timePerPackage: 0 , cached: 0
  01-01 00:07:14.693 E/PackageManager(  743): There should probably be exactly one storage manager; found 0: matches=[]
  01-01 00:07:14.694 E/PackageManager(  743): There should probably be exactly one setup wizard; found 0: matches=[]
  01-01 00:07:14.696 E/PackageManager(  743): There should probably be exactly one documenter; found 0: matches=[]
  
  01-01 00:07:14.698 I/boot_progress_pms_scan_end(  743): 18012
  
  ```

- boot_progress_pms_scan_end 到 boot_progress_pms_ready 耗时399ms，这期间主要是PackageManager做的一些权限检测和授权操作，可考虑验证这一步骤是否必须。

  ```c
  01-01 00:07:14.698 I/boot_progress_pms_scan_end(  743): 18012
      
  01-01 00:07:14.699 I/PackageManager(  743): Time to scan packages: 3.41 seconds
  01-01 00:07:14.699 I/PackageManager(  743): Package com.google.android.ext.services checking android.permission.PROVIDE_RESOLVER_RANKER_SERVICE: BasePermission{238dd1f android.permission.PROVIDE_RESOLVER_RANKER_SERVICE}
  01-01 00:07:14.700 I/PackageManager(  743): Considering granting permission android.permission.PROVIDE_RESOLVER_RANKER_SERVICE to package com.google.android.ext.services grant 2
  01-01 00:07:14.700 I/PackageManager(  743): Package com.google.android.ext.services checking android.permission.READ_DEVICE_CONFIG: BasePermission{a8fc86c android.permission.READ_DEVICE_CONFIG}
  01-01 00:07:14.700 I/PackageManager(  743): Considering granting permission android.permission.READ_DEVICE_CONFIG to package com.google.android.ext.services grant 2
  01-01 00:07:14.700 I/PackageManager(  743): Package com.google.android.ext.services checking android.permission.MONITOR_DEFAULT_SMS_PACKAGE: BasePermission{dd16e35 android.permission.MONITOR_DEFAULT_SMS_PACKAGE}
  01-01 00:07:14.700 I/PackageManager(  743): Considering granting permission android.permission.MONITOR_DEFAULT_SMS_PACKAGE to package com.google.android.ext.services grant 2
  01-01 00:07:14.700 I/PackageManager(  743): Package com.google.android.ext.services checking android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE: BasePermission{3be42ca android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE}
  01-01 00:07:14.700 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE to package com.google.android.ext.services grant 2
  01-01 00:07:14.700 I/PackageManager(  743): Package com.google.android.ext.services checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.701 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.google.android.ext.services grant 2
  01-01 00:07:14.701 I/PackageManager(  743): Package android checking android.permission.LOCATION_HARDWARE: BasePermission{8e6ff58 android.permission.LOCATION_HARDWARE}
  01-01 00:07:14.701 I/PackageManager(  743): Considering granting permission android.permission.LOCATION_HARDWARE to package android grant 2
  01-01 00:07:14.701 I/PackageManager(  743): Package android checking android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS: BasePermission{237b8b1 android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS}
  01-01 00:07:14.701 I/PackageManager(  743): Considering granting permission android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS to package android grant 2
  01-01 00:07:14.701 I/PackageManager(  743): Package android checking android.permission.GET_ACCOUNTS: BasePermission{5e5c196 android.permission.GET_ACCOUNTS}
  01-01 00:07:14.701 I/PackageManager(  743): Considering granting permission android.permission.GET_ACCOUNTS to package android grant 3
  01-01 00:07:14.701 I/PackageManager(  743): Package android checking android.permission.SEND_SHOW_SUSPENDED_APP_DETAILS: BasePermission{3d35117 android.permission.SEND_SHOW_SUSPENDED_APP_DETAILS}
  01-01 00:07:14.701 I/PackageManager(  743): Considering granting permission android.permission.SEND_SHOW_SUSPENDED_APP_DETAILS to package android grant 2
  01-01 00:07:14.701 I/PackageManager(  743): Package android checking android.permission.BIND_JOB_SERVICE: BasePermission{278b904 android.permission.BIND_JOB_SERVICE}
  01-01 00:07:14.702 I/PackageManager(  743): Considering granting permission android.permission.BIND_JOB_SERVICE to package android grant 2
  01-01 00:07:14.702 I/PackageManager(  743): Package android checking android.permission.TRIGGER_TIME_ZONE_RULES_CHECK: BasePermission{2de2eed android.permission.TRIGGER_TIME_ZONE_RULES_CHECK}
  01-01 00:07:14.702 I/PackageManager(  743): Considering granting permission android.permission.TRIGGER_TIME_ZONE_RULES_CHECK to package android grant 2
  01-01 00:07:14.702 I/PackageManager(  743): Package android checking android.permission.BIND_NETWORK_RECOMMENDATION_SERVICE: BasePermission{3346122 android.permission.BIND_NETWORK_RECOMMENDATION_SERVICE}
  01-01 00:07:14.702 I/PackageManager(  743): Considering granting permission android.permission.BIND_NETWORK_RECOMMENDATION_SERVICE to package android grant 2
  01-01 00:07:14.702 I/PackageManager(  743): Package android checking android.permission.BIND_ATTENTION_SERVICE: BasePermission{531e7b3 android.permission.BIND_ATTENTION_SERVICE}
  01-01 00:07:14.702 I/PackageManager(  743): Considering granting permission android.permission.BIND_ATTENTION_SERVICE to package android grant 2
  01-01 00:07:14.702 I/PackageManager(  743): Package android checking android.permission.CONTROL_VPN: BasePermission{24a6170 android.permission.CONTROL_VPN}
  01-01 00:07:14.702 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_VPN to package android grant 2
  01-01 00:07:14.702 I/PackageManager(  743): Package android checking android.permission.PACKAGE_USAGE_STATS: BasePermission{ffbcce9 android.permission.PACKAGE_USAGE_STATS}
  01-01 00:07:14.702 I/PackageManager(  743): Considering granting permission android.permission.PACKAGE_USAGE_STATS to package android grant 2
  01-01 00:07:14.703 I/PackageManager(  743): Package android checking android.intent.category.MASTER_CLEAR.permission.C2D_MESSAGE: BasePermission{bdb6d6e android.intent.category.MASTER_CLEAR.permission.C2D_MESSAGE}
  01-01 00:07:14.703 I/PackageManager(  743): Considering granting permission android.intent.category.MASTER_CLEAR.permission.C2D_MESSAGE to package android grant 2
  01-01 00:07:14.703 I/PackageManager(  743): Package android checking android.permission.LOCAL_MAC_ADDRESS: BasePermission{8d94c0f android.permission.LOCAL_MAC_ADDRESS}
  01-01 00:07:14.703 I/PackageManager(  743): Considering granting permission android.permission.LOCAL_MAC_ADDRESS to package android grant 2
  01-01 00:07:14.703 I/PackageManager(  743): Package android checking android.permission.CONFIRM_FULL_BACKUP: BasePermission{c4c249c android.permission.CONFIRM_FULL_BACKUP}
  01-01 00:07:14.703 I/PackageManager(  743): Considering granting permission android.permission.CONFIRM_FULL_BACKUP to package android grant 2
  01-01 00:07:14.703 I/PackageManager(  743): Package android checking android.permission.ACCESS_INSTANT_APPS: BasePermission{c3b4ea5 android.permission.ACCESS_INSTANT_APPS}
  01-01 00:07:14.703 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_INSTANT_APPS to package android grant 2
  01-01 00:07:14.703 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS: BasePermission{fd4f27a android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS}
  01-01 00:07:14.703 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS to package com.android.launcher3 grant 2
  01-01 00:07:14.703 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.CALL_PHONE: BasePermission{3e89a2b android.permission.CALL_PHONE}
  01-01 00:07:14.704 I/PackageManager(  743): Considering granting permission android.permission.CALL_PHONE to package com.android.launcher3 grant 3
  01-01 00:07:14.704 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.SET_WALLPAPER: BasePermission{144ee88 android.permission.SET_WALLPAPER}
  01-01 00:07:14.704 I/PackageManager(  743): Considering granting permission android.permission.SET_WALLPAPER to package com.android.launcher3 grant 2
  01-01 00:07:14.704 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.SET_WALLPAPER_HINTS: BasePermission{373021 android.permission.SET_WALLPAPER_HINTS}
  01-01 00:07:14.704 I/PackageManager(  743): Considering granting permission android.permission.SET_WALLPAPER_HINTS to package com.android.launcher3 grant 2
  01-01 00:07:14.704 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.BIND_APPWIDGET: BasePermission{2afbc46 android.permission.BIND_APPWIDGET}
  01-01 00:07:14.704 I/PackageManager(  743): Considering granting permission android.permission.BIND_APPWIDGET to package com.android.launcher3 grant 2
  01-01 00:07:14.704 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.READ_EXTERNAL_STORAGE: BasePermission{454ae07 android.permission.READ_EXTERNAL_STORAGE}
  01-01 00:07:14.704 I/PackageManager(  743): Considering granting permission android.permission.READ_EXTERNAL_STORAGE to package com.android.launcher3 grant 3
  01-01 00:07:14.704 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.RECEIVE_BOOT_COMPLETED: BasePermission{57e6b34 android.permission.RECEIVE_BOOT_COMPLETED}
  01-01 00:07:14.704 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_BOOT_COMPLETED to package com.android.launcher3 grant 2
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.REQUEST_DELETE_PACKAGES: BasePermission{9b5ad5d android.permission.REQUEST_DELETE_PACKAGES}
  01-01 00:07:14.705 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_DELETE_PACKAGES to package com.android.launcher3 grant 2
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.READ_CALL_LOG: BasePermission{1b56d2 android.permission.READ_CALL_LOG}
  01-01 00:07:14.705 I/PackageManager(  743): Considering granting permission android.permission.READ_CALL_LOG to package com.android.launcher3 grant 3
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.READ_SMS: BasePermission{88423a3 android.permission.READ_SMS}
  01-01 00:07:14.705 I/PackageManager(  743): Considering granting permission android.permission.READ_SMS to package com.android.launcher3 grant 3
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking com.android.email.permission.ACCESS_PROVIDER: null
  01-01 00:07:14.705 I/PackageManager(  743): Unknown permission com.android.email.permission.ACCESS_PROVIDER in package com.android.launcher3
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.READ_CALENDAR: BasePermission{63106a0 android.permission.READ_CALENDAR}
  01-01 00:07:14.705 I/PackageManager(  743): Considering granting permission android.permission.READ_CALENDAR to package com.android.launcher3 grant 3
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking com.android.launcher3.permission.READ_SETTINGS: BasePermission{2a4c259 com.android.launcher3.permission.READ_SETTINGS}
  01-01 00:07:14.705 I/PackageManager(  743): Considering granting permission com.android.launcher3.permission.READ_SETTINGS to package com.android.launcher3 grant 2
  01-01 00:07:14.705 I/PackageManager(  743): Package com.android.launcher3 checking com.android.launcher3.permission.WRITE_SETTINGS: BasePermission{d340e1e com.android.launcher3.permission.WRITE_SETTINGS}
  01-01 00:07:14.705 I/PackageManager(  743): Considering granting permission com.android.launcher3.permission.WRITE_SETTINGS to package com.android.launcher3 grant 2
  01-01 00:07:14.706 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.WRITE_EXTERNAL_STORAGE: BasePermission{4ab56ff android.permission.WRITE_EXTERNAL_STORAGE}
  01-01 00:07:14.706 I/PackageManager(  743): Considering granting permission android.permission.WRITE_EXTERNAL_STORAGE to package com.android.launcher3 grant 3
  01-01 00:07:14.706 I/PackageManager(  743): Package com.android.launcher3 checking android.permission.READ_PHONE_STATE: BasePermission{9afeccc android.permission.READ_PHONE_STATE}
  01-01 00:07:14.706 I/PackageManager(  743): Considering granting permission android.permission.READ_PHONE_STATE to package com.android.launcher3 grant 3
  01-01 00:07:14.706 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.MANAGE_USERS: BasePermission{bd62b15 android.permission.MANAGE_USERS}
  01-01 00:07:14.706 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USERS to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.706 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.GRANT_RUNTIME_PERMISSIONS: BasePermission{28eee2a android.permission.GRANT_RUNTIME_PERMISSIONS}
  01-01 00:07:14.706 I/PackageManager(  743): Considering granting permission android.permission.GRANT_RUNTIME_PERMISSIONS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.707 I/PackageManager(  743): Un-granting permission android.permission.GRANT_RUNTIME_PERMISSIONS from package com.google.android.permissioncontroller (protectionLevel=770 flags=0x30483e05)
  01-01 00:07:14.707 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.REVOKE_RUNTIME_PERMISSIONS: BasePermission{1e8641b android.permission.REVOKE_RUNTIME_PERMISSIONS}
  01-01 00:07:14.707 I/PackageManager(  743): Considering granting permission android.permission.REVOKE_RUNTIME_PERMISSIONS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.707 I/PackageManager(  743): Un-granting permission android.permission.REVOKE_RUNTIME_PERMISSIONS from package com.google.android.permissioncontroller (protectionLevel=770 flags=0x30483e05)
  01-01 00:07:14.707 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.ADJUST_RUNTIME_PERMISSIONS_POLICY: BasePermission{65509b8 android.permission.ADJUST_RUNTIME_PERMISSIONS_POLICY}
  01-01 00:07:14.707 I/PackageManager(  743): Considering granting permission android.permission.ADJUST_RUNTIME_PERMISSIONS_POLICY to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.707 I/PackageManager(  743): Un-granting permission android.permission.ADJUST_RUNTIME_PERMISSIONS_POLICY from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.707 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.WHITELIST_RESTRICTED_PERMISSIONS: BasePermission{77b6391 android.permission.WHITELIST_RESTRICTED_PERMISSIONS}
  01-01 00:07:14.707 I/PackageManager(  743): Considering granting permission android.permission.WHITELIST_RESTRICTED_PERMISSIONS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.707 I/PackageManager(  743): Un-granting permission android.permission.WHITELIST_RESTRICTED_PERMISSIONS from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.707 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.INTERACT_ACROSS_USERS_FULL: BasePermission{b05c2f6 android.permission.INTERACT_ACROSS_USERS_FULL}
  01-01 00:07:14.707 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS_FULL to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.707 I/PackageManager(  743): Un-granting permission android.permission.INTERACT_ACROSS_USERS_FULL from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.708 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.OBSERVE_GRANT_REVOKE_PERMISSIONS: BasePermission{31f26f7 android.permission.OBSERVE_GRANT_REVOKE_PERMISSIONS}
  01-01 00:07:14.708 I/PackageManager(  743): Considering granting permission android.permission.OBSERVE_GRANT_REVOKE_PERMISSIONS to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.708 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.UPDATE_APP_OPS_STATS: BasePermission{c2d0964 android.permission.UPDATE_APP_OPS_STATS}
  01-01 00:07:14.708 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_APP_OPS_STATS to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.708 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.MANAGE_APP_OPS_MODES: BasePermission{f61a7cd android.permission.MANAGE_APP_OPS_MODES}
  01-01 00:07:14.708 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_MODES to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.708 I/PackageManager(  743): Un-granting permission android.permission.MANAGE_APP_OPS_MODES from package com.google.android.permissioncontroller (protectionLevel=770 flags=0x30483e05)
  01-01 00:07:14.708 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.GET_APP_OPS_STATS: BasePermission{3431882 android.permission.GET_APP_OPS_STATS}
  01-01 00:07:14.708 I/PackageManager(  743): Considering granting permission android.permission.GET_APP_OPS_STATS to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.708 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.KILL_UID: BasePermission{b953b93 android.permission.KILL_UID}
  01-01 00:07:14.708 I/PackageManager(  743): Considering granting permission android.permission.KILL_UID to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.708 I/PackageManager(  743): Un-granting permission android.permission.KILL_UID from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.709 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.MANAGE_APP_OPS_RESTRICTIONS: BasePermission{d6357d0 android.permission.MANAGE_APP_OPS_RESTRICTIONS}
  01-01 00:07:14.709 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_RESTRICTIONS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.709 I/PackageManager(  743): Un-granting permission android.permission.MANAGE_APP_OPS_RESTRICTIONS from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.709 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.RECEIVE_BOOT_COMPLETED: BasePermission{57e6b34 android.permission.RECEIVE_BOOT_COMPLETED}
  01-01 00:07:14.709 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_BOOT_COMPLETED to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.709 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS: BasePermission{2edf3c9 android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS}
  01-01 00:07:14.709 I/PackageManager(  743): Considering granting permission android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.709 I/PackageManager(  743): Un-granting permission android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.709 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.MANAGE_ROLE_HOLDERS: BasePermission{60e3ace android.permission.MANAGE_ROLE_HOLDERS}
  01-01 00:07:14.709 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ROLE_HOLDERS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.709 I/PackageManager(  743): Un-granting permission android.permission.MANAGE_ROLE_HOLDERS from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.709 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.OBSERVE_ROLE_HOLDERS: BasePermission{34dfdef android.permission.OBSERVE_ROLE_HOLDERS}
  01-01 00:07:14.709 I/PackageManager(  743): Considering granting permission android.permission.OBSERVE_ROLE_HOLDERS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.709 I/PackageManager(  743): Un-granting permission android.permission.OBSERVE_ROLE_HOLDERS from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.710 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.SET_PREFERRED_APPLICATIONS: BasePermission{16e20fc android.permission.SET_PREFERRED_APPLICATIONS}
  01-01 00:07:14.710 I/PackageManager(  743): Considering granting permission android.permission.SET_PREFERRED_APPLICATIONS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.710 I/PackageManager(  743): Un-granting permission android.permission.SET_PREFERRED_APPLICATIONS from package com.google.android.permissioncontroller (protectionLevel=770 flags=0x30483e05)
  01-01 00:07:14.710 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.ACCESS_SHARED_LIBRARIES: BasePermission{8d90385 android.permission.ACCESS_SHARED_LIBRARIES}
  01-01 00:07:14.710 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_SHARED_LIBRARIES to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.710 I/PackageManager(  743): Un-granting permission android.permission.ACCESS_SHARED_LIBRARIES from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.710 I/PackageManager(  743): Package com.google.android.permissioncontroller checking com.android.permissioncontroller.permission.MANAGE_ROLES_FROM_CONTROLLER: BasePermission{15735da com.android.permissioncontroller.permission.MANAGE_ROLES_FROM_CONTROLLER}
  01-01 00:07:14.710 I/PackageManager(  743): Considering granting permission com.android.permissioncontroller.permission.MANAGE_ROLES_FROM_CONTROLLER to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.710 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.ACCESS_INSTANT_APPS: BasePermission{c3b4ea5 android.permission.ACCESS_INSTANT_APPS}
  01-01 00:07:14.710 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_INSTANT_APPS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.710 I/PackageManager(  743): Un-granting permission android.permission.ACCESS_INSTANT_APPS from package com.google.android.permissioncontroller (protectionLevel=131842 flags=0x30483e05)
  01-01 00:07:14.710 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.REQUEST_INCIDENT_REPORT_APPROVAL: BasePermission{5268a0b android.permission.REQUEST_INCIDENT_REPORT_APPROVAL}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_INCIDENT_REPORT_APPROVAL to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.711 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.APPROVE_INCIDENT_REPORTS: BasePermission{efa50e8 android.permission.APPROVE_INCIDENT_REPORTS}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.APPROVE_INCIDENT_REPORTS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.711 I/PackageManager(  743): Un-granting permission android.permission.APPROVE_INCIDENT_REPORTS from package com.google.android.permissioncontroller (protectionLevel=1048578 flags=0x30483e05)
  01-01 00:07:14.711 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.READ_DEVICE_CONFIG: BasePermission{a8fc86c android.permission.READ_DEVICE_CONFIG}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.READ_DEVICE_CONFIG to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.711 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.OPEN_ACCESSIBILITY_DETAILS_SETTINGS: BasePermission{ab5301 android.permission.OPEN_ACCESSIBILITY_DETAILS_SETTINGS}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.OPEN_ACCESSIBILITY_DETAILS_SETTINGS to package com.google.android.permissioncontroller grant 1
  01-01 00:07:14.711 I/PackageManager(  743): Un-granting permission android.permission.OPEN_ACCESSIBILITY_DETAILS_SETTINGS from package com.google.android.permissioncontroller (protectionLevel=258 flags=0x30483e05)
  01-01 00:07:14.711 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.READ_PRIVILEGED_PHONE_STATE: BasePermission{2d5a6 android.permission.READ_PRIVILEGED_PHONE_STATE}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.READ_PRIVILEGED_PHONE_STATE to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.711 I/PackageManager(  743): Package com.google.android.permissioncontroller checking android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME: BasePermission{2b1bbe7 android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME to package com.google.android.permissioncontroller grant 2
  01-01 00:07:14.711 I/PackageManager(  743): Package com.android.webview checking android.permission.INTERNET: BasePermission{8979394 android.permission.INTERNET}
  01-01 00:07:14.711 I/PackageManager(  743): Considering granting permission android.permission.INTERNET to package com.android.webview grant 2
  01-01 00:07:14.712 I/PackageManager(  743): Package com.android.webview checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.712 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.android.webview grant 2
  01-01 00:07:14.712 I/PackageManager(  743): Package com.spreadtrum.ims checking android.permission.BROADCAST_STICKY: BasePermission{ff91e3d android.permission.BROADCAST_STICKY}
  01-01 00:07:14.712 I/PackageManager(  743): Considering granting permission android.permission.BROADCAST_STICKY to package com.spreadtrum.ims grant 2
  01-01 00:07:14.712 I/PackageManager(  743): Package com.spreadtrum.ims checking android.permission.ACCESS_FINE_LOCATION: BasePermission{476a632 android.permission.ACCESS_FINE_LOCATION}
  01-01 00:07:14.712 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_FINE_LOCATION to package com.spreadtrum.ims grant 3
  01-01 00:07:14.712 I/PackageManager(  743): Package com.spreadtrum.ims checking com.spreadtrum.vowifi.permission.ACCESS_CONFIGURATION: null
  01-01 00:07:14.712 I/PackageManager(  743): Unknown permission com.spreadtrum.vowifi.permission.ACCESS_CONFIGURATION in package com.spreadtrum.ims
  01-01 00:07:14.712 I/PackageManager(  743): Package com.spreadtrum.ims checking android.permission.READ_PRECISE_PHONE_STATE: BasePermission{9d42f83 android.permission.READ_PRECISE_PHONE_STATE}
  01-01 00:07:14.712 I/PackageManager(  743): Considering granting permission android.permission.READ_PRECISE_PHONE_STATE to package com.spreadtrum.ims grant 2
  01-01 00:07:14.712 I/PackageManager(  743): Package com.spreadtrum.ims checking android.permission.ACCESS_COARSE_LOCATION: BasePermission{8245500 android.permission.ACCESS_COARSE_LOCATION}
  01-01 00:07:14.712 I/PackageManager(  743): android.permission.ACCESS_COARSE_LOCATION is newly added for com.spreadtrum.ims
  01-01 00:07:14.712 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_COARSE_LOCATION to package com.spreadtrum.ims grant 3
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.MANAGE_USERS: BasePermission{bd62b15 android.permission.MANAGE_USERS}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USERS to package com.android.packageinstaller grant 2
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.INSTALL_PACKAGES: BasePermission{75e6139 android.permission.INSTALL_PACKAGES}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.INSTALL_PACKAGES to package com.android.packageinstaller grant 2
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.DELETE_PACKAGES: BasePermission{fe4f37e android.permission.DELETE_PACKAGES}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.DELETE_PACKAGES to package com.android.packageinstaller grant 2
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.READ_INSTALL_SESSIONS: BasePermission{82040df android.permission.READ_INSTALL_SESSIONS}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.READ_INSTALL_SESSIONS to package com.android.packageinstaller grant 2
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.RECEIVE_BOOT_COMPLETED: BasePermission{57e6b34 android.permission.RECEIVE_BOOT_COMPLETED}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_BOOT_COMPLETED to package com.android.packageinstaller grant 2
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS: BasePermission{2edf3c9 android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS to package com.android.packageinstaller grant 2
  01-01 00:07:14.715 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.USE_RESERVED_DISK: BasePermission{4f9c12c android.permission.USE_RESERVED_DISK}
  01-01 00:07:14.715 I/PackageManager(  743): Considering granting permission android.permission.USE_RESERVED_DISK to package com.android.packageinstaller grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.UPDATE_APP_OPS_STATS: BasePermission{c2d0964 android.permission.UPDATE_APP_OPS_STATS}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_APP_OPS_STATS to package com.android.packageinstaller grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.MANAGE_APP_OPS_MODES: BasePermission{f61a7cd android.permission.MANAGE_APP_OPS_MODES}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_MODES to package com.android.packageinstaller grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.INTERACT_ACROSS_USERS_FULL: BasePermission{b05c2f6 android.permission.INTERACT_ACROSS_USERS_FULL}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS_FULL to package com.android.packageinstaller grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME: BasePermission{2b1bbe7 android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME to package com.android.packageinstaller grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.packageinstaller checking android.permission.PACKAGE_USAGE_STATS: BasePermission{ffbcce9 android.permission.PACKAGE_USAGE_STATS}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.PACKAGE_USAGE_STATS to package com.android.packageinstaller grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.packageinstaller checking com.google.android.permission.INSTALL_WEARABLE_PACKAGES: null
  01-01 00:07:14.716 I/PackageManager(  743): Unknown permission com.google.android.permission.INSTALL_WEARABLE_PACKAGES in package com.android.packageinstaller
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.settings checking android.permission.REQUEST_NETWORK_SCORES: BasePermission{b3ad7f5 android.permission.REQUEST_NETWORK_SCORES}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_NETWORK_SCORES to package com.android.settings grant 2
  01-01 00:07:14.716 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_MEDIA_STORAGE: BasePermission{258c98a android.permission.WRITE_MEDIA_STORAGE}
  01-01 00:07:14.716 I/PackageManager(  743): Considering granting permission android.permission.WRITE_MEDIA_STORAGE to package com.android.settings grant 2
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_EXTERNAL_STORAGE: BasePermission{4ab56ff android.permission.WRITE_EXTERNAL_STORAGE}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.WRITE_EXTERNAL_STORAGE to package com.android.settings grant 3
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_EXTERNAL_STORAGE: BasePermission{454ae07 android.permission.READ_EXTERNAL_STORAGE}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.READ_EXTERNAL_STORAGE to package com.android.settings grant 3
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_SETTINGS: BasePermission{7f20bfb android.permission.WRITE_SETTINGS}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_SECURE_SETTINGS: BasePermission{d7c418 android.permission.WRITE_SECURE_SETTINGS}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SECURE_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.DEVICE_POWER: BasePermission{c2dfe71 android.permission.DEVICE_POWER}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.DEVICE_POWER to package com.android.settings grant 2
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.CHANGE_CONFIGURATION: BasePermission{f81f456 android.permission.CHANGE_CONFIGURATION}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_CONFIGURATION to package com.android.settings grant 2
  01-01 00:07:14.717 I/PackageManager(  743): Package com.android.settings checking android.permission.MOUNT_UNMOUNT_FILESYSTEMS: BasePermission{34b6cd7 android.permission.MOUNT_UNMOUNT_FILESYSTEMS}
  01-01 00:07:14.717 I/PackageManager(  743): Considering granting permission android.permission.MOUNT_UNMOUNT_FILESYSTEMS to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.VIBRATE: BasePermission{79109c4 android.permission.VIBRATE}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.VIBRATE to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.BLUETOOTH: BasePermission{b5310ad android.permission.BLUETOOTH}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.BLUETOOTH_ADMIN: BasePermission{440ffe2 android.permission.BLUETOOTH_ADMIN}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH_ADMIN to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.BLUETOOTH_PRIVILEGED: BasePermission{86fff73 android.permission.BLUETOOTH_PRIVILEGED}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH_PRIVILEGED to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.NFC: BasePermission{d76fe30 android.permission.NFC}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.NFC to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.HARDWARE_TEST: BasePermission{63d0aa9 android.permission.HARDWARE_TEST}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.HARDWARE_TEST to package com.android.settings grant 2
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.CALL_PHONE: BasePermission{3e89a2b android.permission.CALL_PHONE}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.CALL_PHONE to package com.android.settings grant 3
  01-01 00:07:14.718 I/PackageManager(  743): Package com.android.settings checking android.permission.MODIFY_AUDIO_SETTINGS: BasePermission{8f3382e android.permission.MODIFY_AUDIO_SETTINGS}
  01-01 00:07:14.718 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_AUDIO_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.MASTER_CLEAR: BasePermission{c411fcf android.permission.MASTER_CLEAR}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.MASTER_CLEAR to package com.android.settings grant 2
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking com.google.android.googleapps.permission.GOOGLE_AUTH: null
  01-01 00:07:14.719 I/PackageManager(  743): Unknown permission com.google.android.googleapps.permission.GOOGLE_AUTH in package com.android.settings
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_DOWNLOAD_MANAGER: null
  01-01 00:07:14.719 I/PackageManager(  743): Unknown permission android.permission.ACCESS_DOWNLOAD_MANAGER in package com.android.settings
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_CONTACTS: BasePermission{885cd5c android.permission.READ_CONTACTS}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.READ_CONTACTS to package com.android.settings grant 3
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_CONTACTS: BasePermission{6b2a865 android.permission.WRITE_CONTACTS}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.WRITE_CONTACTS to package com.android.settings grant 3
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.android.settings grant 2
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.LOCAL_MAC_ADDRESS: BasePermission{8d94c0f android.permission.LOCAL_MAC_ADDRESS}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.LOCAL_MAC_ADDRESS to package com.android.settings grant 2
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_WIMAX_STATE: BasePermission{c7ea93a android.permission.ACCESS_WIMAX_STATE}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_WIMAX_STATE to package com.android.settings grant 2
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.CHANGE_WIMAX_STATE: BasePermission{659e9eb android.permission.CHANGE_WIMAX_STATE}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_WIMAX_STATE to package com.android.settings grant 2
  01-01 00:07:14.719 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_WIFI_STATE: BasePermission{506348 android.permission.ACCESS_WIFI_STATE}
  01-01 00:07:14.719 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_WIFI_STATE to package com.android.settings grant 2
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking com.android.certinstaller.INSTALL_AS_USER: null
  01-01 00:07:14.720 I/PackageManager(  743): Unknown permission com.android.certinstaller.INSTALL_AS_USER in package com.android.settings
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.CHANGE_WIFI_STATE: BasePermission{22a65e1 android.permission.CHANGE_WIFI_STATE}
  01-01 00:07:14.720 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_WIFI_STATE to package com.android.settings grant 2
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.TETHER_PRIVILEGED: BasePermission{41e1f06 android.permission.TETHER_PRIVILEGED}
  01-01 00:07:14.720 I/PackageManager(  743): Considering granting permission android.permission.TETHER_PRIVILEGED to package com.android.settings grant 2
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.FOREGROUND_SERVICE: BasePermission{2eb39c7 android.permission.FOREGROUND_SERVICE}
  01-01 00:07:14.720 I/PackageManager(  743): Considering granting permission android.permission.FOREGROUND_SERVICE to package com.android.settings grant 2
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.INTERNET: BasePermission{8979394 android.permission.INTERNET}
  01-01 00:07:14.720 I/PackageManager(  743): Considering granting permission android.permission.INTERNET to package com.android.settings grant 2
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.CLEAR_APP_USER_DATA: BasePermission{ac6bf4 android.permission.CLEAR_APP_USER_DATA}
  01-01 00:07:14.720 I/PackageManager(  743): Considering granting permission android.permission.CLEAR_APP_USER_DATA to package com.android.settings grant 2
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_PHONE_STATE: BasePermission{9afeccc android.permission.READ_PHONE_STATE}
  01-01 00:07:14.720 I/PackageManager(  743): Considering granting permission android.permission.READ_PHONE_STATE to package com.android.settings grant 3
  01-01 00:07:14.720 I/PackageManager(  743): Package com.android.settings checking android.permission.MODIFY_PHONE_STATE: BasePermission{5067f1d android.permission.MODIFY_PHONE_STATE}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_PHONE_STATE to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_FINE_LOCATION: BasePermission{476a632 android.permission.ACCESS_FINE_LOCATION}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_FINE_LOCATION to package com.android.settings grant 3
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_APN_SETTINGS: BasePermission{bed2592 android.permission.WRITE_APN_SETTINGS}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.WRITE_APN_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_CHECKIN_PROPERTIES: BasePermission{657ab63 android.permission.ACCESS_CHECKIN_PROPERTIES}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_CHECKIN_PROPERTIES to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_USER_DICTIONARY: BasePermission{b1e5360 android.permission.READ_USER_DICTIONARY}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.READ_USER_DICTIONARY to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_USER_DICTIONARY: BasePermission{590f019 android.permission.WRITE_USER_DICTIONARY}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.WRITE_USER_DICTIONARY to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.FORCE_STOP_PACKAGES: BasePermission{43408de android.permission.FORCE_STOP_PACKAGES}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.FORCE_STOP_PACKAGES to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.PACKAGE_USAGE_STATS: BasePermission{ffbcce9 android.permission.PACKAGE_USAGE_STATS}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.PACKAGE_USAGE_STATS to package com.android.settings grant 2
  01-01 00:07:14.721 I/PackageManager(  743): Package com.android.settings checking android.permission.BATTERY_STATS: BasePermission{e8f9abf android.permission.BATTERY_STATS}
  01-01 00:07:14.721 I/PackageManager(  743): Considering granting permission android.permission.BATTERY_STATS to package com.android.settings grant 2
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking com.android.launcher.permission.READ_SETTINGS: null
  01-01 00:07:14.722 I/PackageManager(  743): Unknown permission com.android.launcher.permission.READ_SETTINGS in package com.android.settings
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking com.android.launcher.permission.WRITE_SETTINGS: null
  01-01 00:07:14.722 I/PackageManager(  743): Unknown permission com.android.launcher.permission.WRITE_SETTINGS in package com.android.settings
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking android.permission.MOVE_PACKAGE: BasePermission{305458c android.permission.MOVE_PACKAGE}
  01-01 00:07:14.722 I/PackageManager(  743): Considering granting permission android.permission.MOVE_PACKAGE to package com.android.settings grant 2
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking android.permission.USE_CREDENTIALS: BasePermission{ab774d5 android.permission.USE_CREDENTIALS}
  01-01 00:07:14.722 I/PackageManager(  743): Considering granting permission android.permission.USE_CREDENTIALS to package com.android.settings grant 2
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking android.permission.BACKUP: BasePermission{773d4ea android.permission.BACKUP}
  01-01 00:07:14.722 I/PackageManager(  743): Considering granting permission android.permission.BACKUP to package com.android.settings grant 2
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_SYNC_STATS: BasePermission{e2d23db android.permission.READ_SYNC_STATS}
  01-01 00:07:14.722 I/PackageManager(  743): Considering granting permission android.permission.READ_SYNC_STATS to package com.android.settings grant 2
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_SYNC_SETTINGS: BasePermission{872e78 android.permission.READ_SYNC_SETTINGS}
  01-01 00:07:14.722 I/PackageManager(  743): Considering granting permission android.permission.READ_SYNC_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.722 I/PackageManager(  743): Package com.android.settings checking android.permission.WRITE_SYNC_SETTINGS: BasePermission{2878951 android.permission.WRITE_SYNC_SETTINGS}
  01-01 00:07:14.722 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SYNC_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_DEVICE_CONFIG: BasePermission{a8fc86c android.permission.READ_DEVICE_CONFIG}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.READ_DEVICE_CONFIG to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.STATUS_BAR: BasePermission{53255b6 android.permission.STATUS_BAR}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_USB: BasePermission{d5022b7 android.permission.MANAGE_USB}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USB to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_DEBUGGING: BasePermission{63cba24 android.permission.MANAGE_DEBUGGING}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_DEBUGGING to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.SET_POINTER_SPEED: BasePermission{46a698d android.permission.SET_POINTER_SPEED}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.SET_POINTER_SPEED to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.SET_KEYBOARD_LAYOUT: BasePermission{d861742 android.permission.SET_KEYBOARD_LAYOUT}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.SET_KEYBOARD_LAYOUT to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.INTERACT_ACROSS_USERS_FULL: BasePermission{b05c2f6 android.permission.INTERACT_ACROSS_USERS_FULL}
  01-01 00:07:14.723 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS_FULL to package com.android.settings grant 2
  01-01 00:07:14.723 I/PackageManager(  743): Package com.android.settings checking android.permission.COPY_PROTECTED_DATA: BasePermission{c3a3353 android.permission.COPY_PROTECTED_DATA}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.COPY_PROTECTED_DATA to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_USERS: BasePermission{bd62b15 android.permission.MANAGE_USERS}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USERS to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS: BasePermission{59d5490 android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_PROFILE: BasePermission{b211189 android.permission.READ_PROFILE}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.READ_PROFILE to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.CONFIGURE_WIFI_DISPLAY: BasePermission{962658e android.permission.CONFIGURE_WIFI_DISPLAY}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.CONFIGURE_WIFI_DISPLAY to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.CONFIGURE_DISPLAY_COLOR_MODE: BasePermission{3aab1af android.permission.CONFIGURE_DISPLAY_COLOR_MODE}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.CONFIGURE_DISPLAY_COLOR_MODE to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS: BasePermission{e2b29bc android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS to package com.android.settings grant 2
  01-01 00:07:14.724 I/PackageManager(  743): Package com.android.settings checking android.permission.SET_TIME: BasePermission{2803d45 android.permission.SET_TIME}
  01-01 00:07:14.724 I/PackageManager(  743): Considering granting permission android.permission.SET_TIME to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_NOTIFICATIONS: BasePermission{ba34c9a android.permission.ACCESS_NOTIFICATIONS}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NOTIFICATIONS to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.REBOOT: BasePermission{efab9cb android.permission.REBOOT}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.REBOOT to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.RECEIVE_BOOT_COMPLETED: BasePermission{57e6b34 android.permission.RECEIVE_BOOT_COMPLETED}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_BOOT_COMPLETED to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_DEVICE_ADMINS: BasePermission{35f25a8 android.permission.MANAGE_DEVICE_ADMINS}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_DEVICE_ADMINS to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_SEARCH_INDEXABLES: BasePermission{4ec68c1 android.permission.READ_SEARCH_INDEXABLES}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.READ_SEARCH_INDEXABLES to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.BIND_SETTINGS_SUGGESTIONS_SERVICE: BasePermission{6d99866 android.permission.BIND_SETTINGS_SUGGESTIONS_SERVICE}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.BIND_SETTINGS_SUGGESTIONS_SERVICE to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.OEM_UNLOCK_STATE: BasePermission{bf927a7 android.permission.OEM_UNLOCK_STATE}
  01-01 00:07:14.725 I/PackageManager(  743): Considering granting permission android.permission.OEM_UNLOCK_STATE to package com.android.settings grant 2
  01-01 00:07:14.725 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_USER_OEM_UNLOCK_STATE: BasePermission{554f454 android.permission.MANAGE_USER_OEM_UNLOCK_STATE}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USER_OEM_UNLOCK_STATE to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.OVERRIDE_WIFI_CONFIG: BasePermission{495cffd android.permission.OVERRIDE_WIFI_CONFIG}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.OVERRIDE_WIFI_CONFIG to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.USE_FINGERPRINT: BasePermission{3d6d4f2 android.permission.USE_FINGERPRINT}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.USE_FINGERPRINT to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_FINGERPRINT: BasePermission{c869743 android.permission.MANAGE_FINGERPRINT}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_FINGERPRINT to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.USE_BIOMETRIC: BasePermission{83701c0 android.permission.USE_BIOMETRIC}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.USE_BIOMETRIC to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.USE_BIOMETRIC_INTERNAL: BasePermission{c746ef9 android.permission.USE_BIOMETRIC_INTERNAL}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.USE_BIOMETRIC_INTERNAL to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.USER_ACTIVITY: BasePermission{4f94e3e android.permission.USER_ACTIVITY}
  01-01 00:07:14.726 I/PackageManager(  743): Considering granting permission android.permission.USER_ACTIVITY to package com.android.settings grant 2
  01-01 00:07:14.726 I/PackageManager(  743): Package com.android.settings checking android.permission.CHANGE_APP_IDLE_STATE: BasePermission{5f1649f android.permission.CHANGE_APP_IDLE_STATE}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_APP_IDLE_STATE to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.PEERS_MAC_ADDRESS: BasePermission{66a79ec android.permission.PEERS_MAC_ADDRESS}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.PEERS_MAC_ADDRESS to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_NOTIFICATIONS: BasePermission{50401b5 android.permission.MANAGE_NOTIFICATIONS}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_NOTIFICATIONS to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.DELETE_PACKAGES: BasePermission{fe4f37e android.permission.DELETE_PACKAGES}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.DELETE_PACKAGES to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.REQUEST_DELETE_PACKAGES: BasePermission{9b5ad5d android.permission.REQUEST_DELETE_PACKAGES}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_DELETE_PACKAGES to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_APP_OPS_RESTRICTIONS: BasePermission{d6357d0 android.permission.MANAGE_APP_OPS_RESTRICTIONS}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_RESTRICTIONS to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_APP_OPS_MODES: BasePermission{f61a7cd android.permission.MANAGE_APP_OPS_MODES}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_MODES to package com.android.settings grant 2
  01-01 00:07:14.727 I/PackageManager(  743): Package com.android.settings checking android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS: BasePermission{2edf3c9 android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS}
  01-01 00:07:14.727 I/PackageManager(  743): Considering granting permission android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS to package com.android.settings grant 2
  01-01 00:07:14.728 I/PackageManager(  743): Package com.android.settings checking android.permission.READ_PRINT_SERVICES: BasePermission{238104a android.permission.READ_PRINT_SERVICES}
  01-01 00:07:14.728 I/PackageManager(  743): Considering granting permission android.permission.READ_PRINT_SERVICES to package com.android.settings grant 2
  01-01 00:07:14.728 I/PackageManager(  743): Package com.android.settings checking android.permission.NETWORK_SETTINGS: BasePermission{a11abbb android.permission.NETWORK_SETTINGS}
  01-01 00:07:14.728 I/PackageManager(  743): Considering granting permission android.permission.NETWORK_SETTINGS to package com.android.settings grant 2
  01-01 00:07:14.728 I/PackageManager(  743): Package com.android.settings checking android.permission.TEST_BLACKLISTED_PASSWORD: BasePermission{97b48d8 android.permission.TEST_BLACKLISTED_PASSWORD}
  01-01 00:07:14.728 I/PackageManager(  743): Considering granting permission android.permission.TEST_BLACKLISTED_PASSWORD to package com.android.settings grant 2
  01-01 00:07:14.728 I/PackageManager(  743): Package com.android.settings checking android.permission.USE_RESERVED_DISK: BasePermission{4f9c12c android.permission.USE_RESERVED_DISK}
  01-01 00:07:14.728 I/PackageManager(  743): Considering granting permission android.permission.USE_RESERVED_DISK to package com.android.settings grant 2
  01-01 00:07:14.728 I/PackageManager(  743): Package com.android.settings checking android.permission.MANAGE_SCOPED_ACCESS_DIRECTORY_PERMISSIONS: BasePermission{8c00431 android.permission.MANAGE_SCOPED_ACCESS_DIRECTORY_PERMISSIONS}
  01-01 00:07:14.728 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_SCOPED_ACCESS_DIRECTORY_PERMISSIONS to package com.android.settings grant 2
  01-01 00:07:14.728 I/PackageManager(  743): Package com.android.settings checking android.permission.CAMERA: BasePermission{9eee716 android.permission.CAMERA}
  01-01 00:07:14.729 I/PackageManager(  743): Considering granting permission android.permission.CAMERA to package com.android.settings grant 3
  01-01 00:07:14.729 I/PackageManager(  743): Package com.android.settings checking android.permission.MEDIA_CONTENT_CONTROL: BasePermission{6254897 android.permission.MEDIA_CONTENT_CONTROL}
  01-01 00:07:14.729 I/PackageManager(  743): Considering granting permission android.permission.MEDIA_CONTENT_CONTROL to package com.android.settings grant 2
  01-01 00:07:14.729 I/PackageManager(  743): Package com.android.settings checking android.permission.ACCESS_COARSE_LOCATION: BasePermission{8245500 android.permission.ACCESS_COARSE_LOCATION}
  01-01 00:07:14.729 I/PackageManager(  743): android.permission.ACCESS_COARSE_LOCATION is newly added for com.android.settings
  01-01 00:07:14.729 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_COARSE_LOCATION to package com.android.settings grant 3
  01-01 00:07:14.729 I/PackageManager(  743): Package com.android.phone checking android.permission.BROADCAST_STICKY: BasePermission{ff91e3d android.permission.BROADCAST_STICKY}
  01-01 00:07:14.729 I/PackageManager(  743): Considering granting permission android.permission.BROADCAST_STICKY to package com.android.phone grant 2
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.CALL_PHONE: BasePermission{3e89a2b android.permission.CALL_PHONE}
  01-01 00:07:14.730 I/PackageManager(  743): Considering granting permission android.permission.CALL_PHONE to package com.android.phone grant 3
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.CALL_PRIVILEGED: BasePermission{5c81a84 android.permission.CALL_PRIVILEGED}
  01-01 00:07:14.730 I/PackageManager(  743): Considering granting permission android.permission.CALL_PRIVILEGED to package com.android.phone grant 2
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.CONTROL_INCALL_EXPERIENCE: BasePermission{45fb26d android.permission.CONTROL_INCALL_EXPERIENCE}
  01-01 00:07:14.730 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_INCALL_EXPERIENCE to package com.android.phone grant 2
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.DOWNLOAD_WITHOUT_NOTIFICATION: null
  01-01 00:07:14.730 I/PackageManager(  743): Unknown permission android.permission.DOWNLOAD_WITHOUT_NOTIFICATION in package com.android.phone
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_SETTINGS: BasePermission{7f20bfb android.permission.WRITE_SETTINGS}
  01-01 00:07:14.730 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_SECURE_SETTINGS: BasePermission{d7c418 android.permission.WRITE_SECURE_SETTINGS}
  01-01 00:07:14.730 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SECURE_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_CONTACTS: BasePermission{885cd5c android.permission.READ_CONTACTS}
  01-01 00:07:14.730 I/PackageManager(  743): Considering granting permission android.permission.READ_CONTACTS to package com.android.phone grant 3
  01-01 00:07:14.730 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_CALL_LOG: BasePermission{1b56d2 android.permission.READ_CALL_LOG}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.READ_CALL_LOG to package com.android.phone grant 3
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_CONTACTS: BasePermission{6b2a865 android.permission.WRITE_CONTACTS}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.WRITE_CONTACTS to package com.android.phone grant 3
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_CALL_LOG: BasePermission{26a5ea2 android.permission.WRITE_CALL_LOG}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.WRITE_CALL_LOG to package com.android.phone grant 3
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.SYSTEM_ALERT_WINDOW: BasePermission{36bd733 android.permission.SYSTEM_ALERT_WINDOW}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.SYSTEM_ALERT_WINDOW to package com.android.phone grant 2
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.INTERNAL_SYSTEM_WINDOW: BasePermission{4ee5af0 android.permission.INTERNAL_SYSTEM_WINDOW}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.INTERNAL_SYSTEM_WINDOW to package com.android.phone grant 2
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.VIBRATE: BasePermission{79109c4 android.permission.VIBRATE}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.VIBRATE to package com.android.phone grant 2
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.BLUETOOTH: BasePermission{b5310ad android.permission.BLUETOOTH}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH to package com.android.phone grant 2
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.BLUETOOTH_ADMIN: BasePermission{440ffe2 android.permission.BLUETOOTH_ADMIN}
  01-01 00:07:14.731 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH_ADMIN to package com.android.phone grant 2
  01-01 00:07:14.731 I/PackageManager(  743): Package com.android.phone checking android.permission.REORDER_TASKS: BasePermission{ed20869 android.permission.REORDER_TASKS}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.REORDER_TASKS to package com.android.phone grant 2
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.CHANGE_CONFIGURATION: BasePermission{f81f456 android.permission.CHANGE_CONFIGURATION}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_CONFIGURATION to package com.android.phone grant 2
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.WAKE_LOCK: BasePermission{833c2ee android.permission.WAKE_LOCK}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.WAKE_LOCK to package com.android.phone grant 2
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.MODIFY_AUDIO_SETTINGS: BasePermission{8f3382e android.permission.MODIFY_AUDIO_SETTINGS}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_AUDIO_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.STATUS_BAR: BasePermission{53255b6 android.permission.STATUS_BAR}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR to package com.android.phone grant 2
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.STATUS_BAR_SERVICE: BasePermission{582b38f android.permission.STATUS_BAR_SERVICE}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.RECEIVE_SMS: BasePermission{af6361c android.permission.RECEIVE_SMS}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_SMS to package com.android.phone grant 3
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_SMS: BasePermission{88423a3 android.permission.READ_SMS}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.READ_SMS to package com.android.phone grant 3
  01-01 00:07:14.732 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_SMS: BasePermission{4f9c225 android.permission.WRITE_SMS}
  01-01 00:07:14.732 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SMS to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.SEND_SMS: BasePermission{51d1ffa android.permission.SEND_SMS}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.SEND_SMS to package com.android.phone grant 3
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.SEND_RESPOND_VIA_MESSAGE: BasePermission{280f9ab android.permission.SEND_RESPOND_VIA_MESSAGE}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.SEND_RESPOND_VIA_MESSAGE to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.SET_TIME: BasePermission{2803d45 android.permission.SET_TIME}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.SET_TIME to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.SET_TIME_ZONE: BasePermission{23e9808 android.permission.SET_TIME_ZONE}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.SET_TIME_ZONE to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.ACCESS_WIFI_STATE: BasePermission{506348 android.permission.ACCESS_WIFI_STATE}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_WIFI_STATE to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_PRIVILEGED_PHONE_STATE: BasePermission{2d5a6 android.permission.READ_PRIVILEGED_PHONE_STATE}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.READ_PRIVILEGED_PHONE_STATE to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.MODIFY_PHONE_STATE: BasePermission{5067f1d android.permission.MODIFY_PHONE_STATE}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_PHONE_STATE to package com.android.phone grant 2
  01-01 00:07:14.733 I/PackageManager(  743): Package com.android.phone checking android.permission.ACCESS_IMS_CALL_SERVICE: BasePermission{5295ba1 android.permission.ACCESS_IMS_CALL_SERVICE}
  01-01 00:07:14.733 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_IMS_CALL_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.DEVICE_POWER: BasePermission{c2dfe71 android.permission.DEVICE_POWER}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.DEVICE_POWER to package com.android.phone grant 2
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.DISABLE_KEYGUARD: BasePermission{c0d41c6 android.permission.DISABLE_KEYGUARD}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.DISABLE_KEYGUARD to package com.android.phone grant 2
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.INTERNET: BasePermission{8979394 android.permission.INTERNET}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.INTERNET to package com.android.phone grant 2
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.PROCESS_OUTGOING_CALLS: BasePermission{d38587 android.permission.PROCESS_OUTGOING_CALLS}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.PROCESS_OUTGOING_CALLS to package com.android.phone grant 3
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.ACCESS_COARSE_LOCATION: BasePermission{8245500 android.permission.ACCESS_COARSE_LOCATION}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_COARSE_LOCATION to package com.android.phone grant 3
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_APN_SETTINGS: BasePermission{bed2592 android.permission.WRITE_APN_SETTINGS}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.WRITE_APN_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.734 I/PackageManager(  743): Package com.android.phone checking android.permission.BROADCAST_SMS: BasePermission{a292cb4 android.permission.BROADCAST_SMS}
  01-01 00:07:14.734 I/PackageManager(  743): Considering granting permission android.permission.BROADCAST_SMS to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.BROADCAST_WAP_PUSH: BasePermission{65f10dd android.permission.BROADCAST_WAP_PUSH}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.BROADCAST_WAP_PUSH to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.CHANGE_WIFI_STATE: BasePermission{22a65e1 android.permission.CHANGE_WIFI_STATE}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_WIFI_STATE to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.CHANGE_NETWORK_STATE: BasePermission{58bb452 android.permission.CHANGE_NETWORK_STATE}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_NETWORK_STATE to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.RECEIVE_BOOT_COMPLETED: BasePermission{57e6b34 android.permission.RECEIVE_BOOT_COMPLETED}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_BOOT_COMPLETED to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.SHUTDOWN: BasePermission{6d8f323 android.permission.SHUTDOWN}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.SHUTDOWN to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.RECORD_AUDIO: BasePermission{4866020 android.permission.RECORD_AUDIO}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.RECORD_AUDIO to package com.android.phone grant 3
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.PERFORM_CDMA_PROVISIONING: BasePermission{740ddd9 android.permission.PERFORM_CDMA_PROVISIONING}
  01-01 00:07:14.735 I/PackageManager(  743): Considering granting permission android.permission.PERFORM_CDMA_PROVISIONING to package com.android.phone grant 2
  01-01 00:07:14.735 I/PackageManager(  743): Package com.android.phone checking android.permission.USE_SIP: BasePermission{90cc39e android.permission.USE_SIP}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.USE_SIP to package com.android.phone grant 3
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.REBOOT: BasePermission{efab9cb android.permission.REBOOT}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.REBOOT to package com.android.phone grant 2
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.UPDATE_LOCK: BasePermission{83d9e7f android.permission.UPDATE_LOCK}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_LOCK to package com.android.phone grant 2
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.INTERACT_ACROSS_USERS: BasePermission{dc15e4c android.permission.INTERACT_ACROSS_USERS}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS to package com.android.phone grant 2
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.INTERACT_ACROSS_USERS_FULL: BasePermission{b05c2f6 android.permission.INTERACT_ACROSS_USERS_FULL}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS_FULL to package com.android.phone grant 2
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking com.android.smspush.WAPPUSH_MANAGER_BIND: null
  01-01 00:07:14.736 I/PackageManager(  743): Unknown permission com.android.smspush.WAPPUSH_MANAGER_BIND in package com.android.phone
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.MANAGE_USERS: BasePermission{bd62b15 android.permission.MANAGE_USERS}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USERS to package com.android.phone grant 2
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.UPDATE_APP_OPS_STATS: BasePermission{c2d0964 android.permission.UPDATE_APP_OPS_STATS}
  01-01 00:07:14.736 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_APP_OPS_STATS to package com.android.phone grant 2
  01-01 00:07:14.736 I/PackageManager(  743): Package com.android.phone checking android.permission.MANAGE_APP_OPS_MODES: BasePermission{f61a7cd android.permission.MANAGE_APP_OPS_MODES}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_MODES to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.CONNECTIVITY_INTERNAL: BasePermission{d87e95 android.permission.CONNECTIVITY_INTERNAL}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.CONNECTIVITY_INTERNAL to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.SET_PREFERRED_APPLICATIONS: BasePermission{16e20fc android.permission.SET_PREFERRED_APPLICATIONS}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.SET_PREFERRED_APPLICATIONS to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_SEARCH_INDEXABLES: BasePermission{4ec68c1 android.permission.READ_SEARCH_INDEXABLES}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.READ_SEARCH_INDEXABLES to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.DUMP: BasePermission{efd7baa android.permission.DUMP}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.DUMP to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.REGISTER_CALL_PROVIDER: BasePermission{d17a39b android.permission.REGISTER_CALL_PROVIDER}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.REGISTER_CALL_PROVIDER to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.REGISTER_SIM_SUBSCRIPTION: BasePermission{bcc1338 android.permission.REGISTER_SIM_SUBSCRIPTION}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.REGISTER_SIM_SUBSCRIPTION to package com.android.phone grant 2
  01-01 00:07:14.737 I/PackageManager(  743): Package com.android.phone checking android.permission.BIND_IMS_SERVICE: BasePermission{90f6f11 android.permission.BIND_IMS_SERVICE}
  01-01 00:07:14.737 I/PackageManager(  743): Considering granting permission android.permission.BIND_IMS_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.BIND_CARRIER_SERVICES: BasePermission{78fa876 android.permission.BIND_CARRIER_SERVICES}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.BIND_CARRIER_SERVICES to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.BIND_CARRIER_MESSAGING_SERVICE: BasePermission{ec2de77 android.permission.BIND_CARRIER_MESSAGING_SERVICE}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.BIND_CARRIER_MESSAGING_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.BIND_EUICC_SERVICE: BasePermission{fcb2ae4 android.permission.BIND_EUICC_SERVICE}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.BIND_EUICC_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking com.android.permission.BIND_TELEPHONY_NETWORK_SERVICE: null
  01-01 00:07:14.738 I/PackageManager(  743): Unknown permission com.android.permission.BIND_TELEPHONY_NETWORK_SERVICE in package com.android.phone
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS: BasePermission{eaeb4d android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_SYNC_SETTINGS: BasePermission{872e78 android.permission.READ_SYNC_SETTINGS}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.READ_SYNC_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_SYNC_SETTINGS: BasePermission{2878951 android.permission.WRITE_SYNC_SETTINGS}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SYNC_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.738 I/PackageManager(  743): Package com.android.phone checking android.permission.AUTHENTICATE_ACCOUNTS: BasePermission{245d602 android.permission.AUTHENTICATE_ACCOUNTS}
  01-01 00:07:14.738 I/PackageManager(  743): Considering granting permission android.permission.AUTHENTICATE_ACCOUNTS to package com.android.phone grant 2
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking android.permission.MANAGE_ACCOUNTS: BasePermission{67ceb13 android.permission.MANAGE_ACCOUNTS}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ACCOUNTS to package com.android.phone grant 2
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking android.permission.GET_ACCOUNTS: BasePermission{5e5c196 android.permission.GET_ACCOUNTS}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission android.permission.GET_ACCOUNTS to package com.android.phone grant 3
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking com.android.voicemail.permission.ADD_VOICEMAIL: BasePermission{6821150 com.android.voicemail.permission.ADD_VOICEMAIL}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission com.android.voicemail.permission.ADD_VOICEMAIL to package com.android.phone grant 3
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking com.android.voicemail.permission.WRITE_VOICEMAIL: BasePermission{a87ef49 com.android.voicemail.permission.WRITE_VOICEMAIL}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission com.android.voicemail.permission.WRITE_VOICEMAIL to package com.android.phone grant 2
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking com.android.voicemail.permission.READ_VOICEMAIL: BasePermission{23f504e com.android.voicemail.permission.READ_VOICEMAIL}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission com.android.voicemail.permission.READ_VOICEMAIL to package com.android.phone grant 2
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking android.permission.BIND_VISUAL_VOICEMAIL_SERVICE: BasePermission{9c1256f android.permission.BIND_VISUAL_VOICEMAIL_SERVICE}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission android.permission.BIND_VISUAL_VOICEMAIL_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking android.permission.LOCAL_MAC_ADDRESS: BasePermission{8d94c0f android.permission.LOCAL_MAC_ADDRESS}
  01-01 00:07:14.739 I/PackageManager(  743): Considering granting permission android.permission.LOCAL_MAC_ADDRESS to package com.android.phone grant 2
  01-01 00:07:14.739 I/PackageManager(  743): Package com.android.phone checking android.permission.CHANGE_COMPONENT_ENABLED_STATE: BasePermission{37ef27c android.permission.CHANGE_COMPONENT_ENABLED_STATE}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_COMPONENT_ENABLED_STATE to package com.android.phone grant 2
  01-01 00:07:14.740 I/PackageManager(  743): Package com.android.phone checking android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST: BasePermission{2d73705 android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST to package com.android.phone grant 2
  01-01 00:07:14.740 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_BLOCKED_NUMBERS: BasePermission{b44235a android.permission.READ_BLOCKED_NUMBERS}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.READ_BLOCKED_NUMBERS to package com.android.phone grant 2
  01-01 00:07:14.740 I/PackageManager(  743): Package com.android.phone checking android.permission.WRITE_BLOCKED_NUMBERS: BasePermission{64a98b android.permission.WRITE_BLOCKED_NUMBERS}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.WRITE_BLOCKED_NUMBERS to package com.android.phone grant 2
  01-01 00:07:14.740 I/PackageManager(  743): Package com.android.phone checking android.permission.NETWORK_SETTINGS: BasePermission{a11abbb android.permission.NETWORK_SETTINGS}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.NETWORK_SETTINGS to package com.android.phone grant 2
  01-01 00:07:14.740 I/PackageManager(  743): Package com.android.phone checking android.permission.STOP_APP_SWITCHES: BasePermission{306ba68 android.permission.STOP_APP_SWITCHES}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.STOP_APP_SWITCHES to package com.android.phone grant 2
  01-01 00:07:14.740 I/PackageManager(  743): Package com.android.phone checking android.permission.UPDATE_DEVICE_STATS: BasePermission{b193e81 android.permission.UPDATE_DEVICE_STATS}
  01-01 00:07:14.740 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_DEVICE_STATS to package com.android.phone grant 2
  01-01 00:07:14.741 I/PackageManager(  743): Package com.android.phone checking android.permission.MANAGE_NETWORK_POLICY: BasePermission{3911b26 android.permission.MANAGE_NETWORK_POLICY}
  01-01 00:07:14.741 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_NETWORK_POLICY to package com.android.phone grant 2
  01-01 00:07:14.741 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_NETWORK_USAGE_HISTORY: BasePermission{725367 android.permission.READ_NETWORK_USAGE_HISTORY}
  01-01 00:07:14.741 I/PackageManager(  743): Considering granting permission android.permission.READ_NETWORK_USAGE_HISTORY to package com.android.phone grant 2
  01-01 00:07:14.741 I/PackageManager(  743): Package com.android.phone checking android.permission.BIND_TELEPHONY_DATA_SERVICE: BasePermission{ec11514 android.permission.BIND_TELEPHONY_DATA_SERVICE}
  01-01 00:07:14.741 I/PackageManager(  743): Considering granting permission android.permission.BIND_TELEPHONY_DATA_SERVICE to package com.android.phone grant 2
  01-01 00:07:14.741 I/PackageManager(  743): Package com.android.phone checking android.permission.PACKAGE_USAGE_STATS: BasePermission{ffbcce9 android.permission.PACKAGE_USAGE_STATS}
  01-01 00:07:14.741 I/PackageManager(  743): Considering granting permission android.permission.PACKAGE_USAGE_STATS to package com.android.phone grant 2
  01-01 00:07:14.741 I/PackageManager(  743): Package com.android.phone checking android.permission.READ_PRECISE_PHONE_STATE: BasePermission{9d42f83 android.permission.READ_PRECISE_PHONE_STATE}
  01-01 00:07:14.741 I/PackageManager(  743): Considering granting permission android.permission.READ_PRECISE_PHONE_STATE to package com.android.phone grant 2
  01-01 00:07:14.741 I/PackageManager(  743): Package com.android.phone checking android.permission.MANAGE_ROLE_HOLDERS: BasePermission{60e3ace android.permission.MANAGE_ROLE_HOLDERS}
  01-01 00:07:14.741 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ROLE_HOLDERS to package com.android.phone grant 2
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.phone checking android.permission.CAMERA: BasePermission{9eee716 android.permission.CAMERA}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.CAMERA to package com.android.phone grant 3
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.shell checking android.permission.GET_RUNTIME_PERMISSIONS: BasePermission{e1a41bd android.permission.GET_RUNTIME_PERMISSIONS}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.GET_RUNTIME_PERMISSIONS to package com.android.shell grant 2
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.shell checking android.permission.SEND_SMS: BasePermission{51d1ffa android.permission.SEND_SMS}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.SEND_SMS to package com.android.shell grant 3
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_SMS: BasePermission{88423a3 android.permission.READ_SMS}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.READ_SMS to package com.android.shell grant 3
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.shell checking android.permission.CALL_PHONE: BasePermission{3e89a2b android.permission.CALL_PHONE}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.CALL_PHONE to package com.android.shell grant 3
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_PHONE_STATE: BasePermission{9afeccc android.permission.READ_PHONE_STATE}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.READ_PHONE_STATE to package com.android.shell grant 3
  01-01 00:07:14.742 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_PRECISE_PHONE_STATE: BasePermission{9d42f83 android.permission.READ_PRECISE_PHONE_STATE}
  01-01 00:07:14.742 I/PackageManager(  743): Considering granting permission android.permission.READ_PRECISE_PHONE_STATE to package com.android.shell grant 2
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_PRIVILEGED_PHONE_STATE: BasePermission{2d5a6 android.permission.READ_PRIVILEGED_PHONE_STATE}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.READ_PRIVILEGED_PHONE_STATE to package com.android.shell grant 2
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_CONTACTS: BasePermission{885cd5c android.permission.READ_CONTACTS}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.READ_CONTACTS to package com.android.shell grant 3
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_CONTACTS: BasePermission{6b2a865 android.permission.WRITE_CONTACTS}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.WRITE_CONTACTS to package com.android.shell grant 3
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_CALENDAR: BasePermission{63106a0 android.permission.READ_CALENDAR}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.READ_CALENDAR to package com.android.shell grant 3
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_CALENDAR: BasePermission{663c3b2 android.permission.WRITE_CALENDAR}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.WRITE_CALENDAR to package com.android.shell grant 3
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_USER_DICTIONARY: BasePermission{b1e5360 android.permission.READ_USER_DICTIONARY}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.READ_USER_DICTIONARY to package com.android.shell grant 2
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_USER_DICTIONARY: BasePermission{590f019 android.permission.WRITE_USER_DICTIONARY}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.WRITE_USER_DICTIONARY to package com.android.shell grant 2
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_FINE_LOCATION: BasePermission{476a632 android.permission.ACCESS_FINE_LOCATION}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_FINE_LOCATION to package com.android.shell grant 3
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_COARSE_LOCATION: BasePermission{8245500 android.permission.ACCESS_COARSE_LOCATION}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_COARSE_LOCATION to package com.android.shell grant 3
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_LOCATION_EXTRA_COMMANDS: BasePermission{bc6bf03 android.permission.ACCESS_LOCATION_EXTRA_COMMANDS}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_LOCATION_EXTRA_COMMANDS to package com.android.shell grant 2
  01-01 00:07:14.743 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.743 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_WIFI_STATE: BasePermission{506348 android.permission.ACCESS_WIFI_STATE}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_WIFI_STATE to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.BLUETOOTH: BasePermission{b5310ad android.permission.BLUETOOTH}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.LOCAL_MAC_ADDRESS: BasePermission{8d94c0f android.permission.LOCAL_MAC_ADDRESS}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.LOCAL_MAC_ADDRESS to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.EXPAND_STATUS_BAR: BasePermission{1246e80 android.permission.EXPAND_STATUS_BAR}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.EXPAND_STATUS_BAR to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.DISABLE_KEYGUARD: BasePermission{c0d41c6 android.permission.DISABLE_KEYGUARD}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.DISABLE_KEYGUARD to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_NETWORK_POLICY: BasePermission{3911b26 android.permission.MANAGE_NETWORK_POLICY}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_NETWORK_POLICY to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_USB: BasePermission{d5022b7 android.permission.MANAGE_USB}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USB to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.USE_RESERVED_DISK: BasePermission{4f9c12c android.permission.USE_RESERVED_DISK}
  01-01 00:07:14.744 I/PackageManager(  743): Considering granting permission android.permission.USE_RESERVED_DISK to package com.android.shell grant 2
  01-01 00:07:14.744 I/PackageManager(  743): Package com.android.shell checking android.permission.FOREGROUND_SERVICE: BasePermission{2eb39c7 android.permission.FOREGROUND_SERVICE}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.FOREGROUND_SERVICE to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.REAL_GET_TASKS: BasePermission{d2e3cb9 android.permission.REAL_GET_TASKS}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.REAL_GET_TASKS to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_CONFIGURATION: BasePermission{f81f456 android.permission.CHANGE_CONFIGURATION}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_CONFIGURATION to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.REORDER_TASKS: BasePermission{ed20869 android.permission.REORDER_TASKS}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.REORDER_TASKS to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.REMOVE_TASKS: BasePermission{34668fe android.permission.REMOVE_TASKS}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.REMOVE_TASKS to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_ANIMATION_SCALE: BasePermission{b6c485f android.permission.SET_ANIMATION_SCALE}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.SET_ANIMATION_SCALE to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_PREFERRED_APPLICATIONS: BasePermission{16e20fc android.permission.SET_PREFERRED_APPLICATIONS}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.SET_PREFERRED_APPLICATIONS to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_SETTINGS: BasePermission{7f20bfb android.permission.WRITE_SETTINGS}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SETTINGS to package com.android.shell grant 2
  01-01 00:07:14.745 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_SECURE_SETTINGS: BasePermission{d7c418 android.permission.WRITE_SECURE_SETTINGS}
  01-01 00:07:14.745 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SECURE_SETTINGS to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_DEVICE_CONFIG: BasePermission{a8fc86c android.permission.READ_DEVICE_CONFIG}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.READ_DEVICE_CONFIG to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_DEVICE_CONFIG: BasePermission{3a1f2ac android.permission.WRITE_DEVICE_CONFIG}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.WRITE_DEVICE_CONFIG to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.BROADCAST_STICKY: BasePermission{ff91e3d android.permission.BROADCAST_STICKY}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.BROADCAST_STICKY to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_ACCESSIBILITY: BasePermission{eceb75 android.permission.MANAGE_ACCESSIBILITY}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ACCESSIBILITY to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_DEBUG_APP: BasePermission{61c170a android.permission.SET_DEBUG_APP}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.SET_DEBUG_APP to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_PROCESS_LIMIT: BasePermission{4b70b7b android.permission.SET_PROCESS_LIMIT}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.SET_PROCESS_LIMIT to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_ALWAYS_FINISH: BasePermission{3918d98 android.permission.SET_ALWAYS_FINISH}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.SET_ALWAYS_FINISH to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.DUMP: BasePermission{efd7baa android.permission.DUMP}
  01-01 00:07:14.746 I/PackageManager(  743): Considering granting permission android.permission.DUMP to package com.android.shell grant 2
  01-01 00:07:14.746 I/PackageManager(  743): Package com.android.shell checking android.permission.SIGNAL_PERSISTENT_PROCESSES: BasePermission{9adc9f1 android.permission.SIGNAL_PERSISTENT_PROCESSES}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.SIGNAL_PERSISTENT_PROCESSES to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.KILL_BACKGROUND_PROCESSES: BasePermission{3ec99d6 android.permission.KILL_BACKGROUND_PROCESSES}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.KILL_BACKGROUND_PROCESSES to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.FORCE_BACK: BasePermission{420e457 android.permission.FORCE_BACK}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.FORCE_BACK to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.BATTERY_STATS: BasePermission{e8f9abf android.permission.BATTERY_STATS}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.BATTERY_STATS to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.PACKAGE_USAGE_STATS: BasePermission{ffbcce9 android.permission.PACKAGE_USAGE_STATS}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.PACKAGE_USAGE_STATS to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.INTERNAL_SYSTEM_WINDOW: BasePermission{4ee5af0 android.permission.INTERNAL_SYSTEM_WINDOW}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.INTERNAL_SYSTEM_WINDOW to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.INJECT_EVENTS: BasePermission{9ddeb44 android.permission.INJECT_EVENTS}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.INJECT_EVENTS to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.RETRIEVE_WINDOW_CONTENT: BasePermission{bc4142d android.permission.RETRIEVE_WINDOW_CONTENT}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.RETRIEVE_WINDOW_CONTENT to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_ACTIVITY_WATCHER: BasePermission{8707d62 android.permission.SET_ACTIVITY_WATCHER}
  01-01 00:07:14.747 I/PackageManager(  743): Considering granting permission android.permission.SET_ACTIVITY_WATCHER to package com.android.shell grant 2
  01-01 00:07:14.747 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_INPUT_STATE: BasePermission{9e56ef3 android.permission.READ_INPUT_STATE}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.READ_INPUT_STATE to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_ORIENTATION: BasePermission{17077b0 android.permission.SET_ORIENTATION}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.SET_ORIENTATION to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.INSTALL_PACKAGES: BasePermission{75e6139 android.permission.INSTALL_PACKAGES}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.INSTALL_PACKAGES to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.MOVE_PACKAGE: BasePermission{305458c android.permission.MOVE_PACKAGE}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.MOVE_PACKAGE to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.CLEAR_APP_USER_DATA: BasePermission{ac6bf4 android.permission.CLEAR_APP_USER_DATA}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.CLEAR_APP_USER_DATA to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.CLEAR_APP_CACHE: BasePermission{37ac629 android.permission.CLEAR_APP_CACHE}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.CLEAR_APP_CACHE to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_INSTANT_APPS: BasePermission{c3b4ea5 android.permission.ACCESS_INSTANT_APPS}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_INSTANT_APPS to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.DELETE_CACHE_FILES: BasePermission{5d0dae android.permission.DELETE_CACHE_FILES}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.DELETE_CACHE_FILES to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.DELETE_PACKAGES: BasePermission{fe4f37e android.permission.DELETE_PACKAGES}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.DELETE_PACKAGES to package com.android.shell grant 2
  01-01 00:07:14.748 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_ROLLBACKS: BasePermission{45e074f android.permission.MANAGE_ROLLBACKS}
  01-01 00:07:14.748 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ROLLBACKS to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.TEST_MANAGE_ROLLBACKS: BasePermission{85d5edc android.permission.TEST_MANAGE_ROLLBACKS}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.TEST_MANAGE_ROLLBACKS to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_SURFACE_FLINGER: BasePermission{cd09be5 android.permission.ACCESS_SURFACE_FLINGER}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_SURFACE_FLINGER to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_FRAME_BUFFER: BasePermission{c7056ba android.permission.READ_FRAME_BUFFER}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.READ_FRAME_BUFFER to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.DEVICE_POWER: BasePermission{c2dfe71 android.permission.DEVICE_POWER}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.DEVICE_POWER to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.POWER_SAVER: BasePermission{41dc96b android.permission.POWER_SAVER}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.POWER_SAVER to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.INSTALL_LOCATION_PROVIDER: BasePermission{7cf8cc8 android.permission.INSTALL_LOCATION_PROVIDER}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.INSTALL_LOCATION_PROVIDER to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.BACKUP: BasePermission{773d4ea android.permission.BACKUP}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.BACKUP to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.FORCE_STOP_PACKAGES: BasePermission{43408de android.permission.FORCE_STOP_PACKAGES}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.FORCE_STOP_PACKAGES to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.STOP_APP_SWITCHES: BasePermission{306ba68 android.permission.STOP_APP_SWITCHES}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.STOP_APP_SWITCHES to package com.android.shell grant 2
  01-01 00:07:14.749 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY: BasePermission{af41161 android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY}
  01-01 00:07:14.749 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.GRANT_RUNTIME_PERMISSIONS: BasePermission{28eee2a android.permission.GRANT_RUNTIME_PERMISSIONS}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.GRANT_RUNTIME_PERMISSIONS to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.REVOKE_RUNTIME_PERMISSIONS: BasePermission{1e8641b android.permission.REVOKE_RUNTIME_PERMISSIONS}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.REVOKE_RUNTIME_PERMISSIONS to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.INSTALL_GRANT_RUNTIME_PERMISSIONS: BasePermission{93d2486 android.permission.INSTALL_GRANT_RUNTIME_PERMISSIONS}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.INSTALL_GRANT_RUNTIME_PERMISSIONS to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.WHITELIST_RESTRICTED_PERMISSIONS: BasePermission{77b6391 android.permission.WHITELIST_RESTRICTED_PERMISSIONS}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.WHITELIST_RESTRICTED_PERMISSIONS to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_KEYBOARD_LAYOUT: BasePermission{d861742 android.permission.SET_KEYBOARD_LAYOUT}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.SET_KEYBOARD_LAYOUT to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.GET_DETAILED_TASKS: BasePermission{5cd9147 android.permission.GET_DETAILED_TASKS}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.GET_DETAILED_TASKS to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_SCREEN_COMPATIBILITY: BasePermission{eb4ad74 android.permission.SET_SCREEN_COMPATIBILITY}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.SET_SCREEN_COMPATIBILITY to package com.android.shell grant 2
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_EXTERNAL_STORAGE: BasePermission{454ae07 android.permission.READ_EXTERNAL_STORAGE}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.READ_EXTERNAL_STORAGE to package com.android.shell grant 3
  01-01 00:07:14.750 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_EXTERNAL_STORAGE: BasePermission{4ab56ff android.permission.WRITE_EXTERNAL_STORAGE}
  01-01 00:07:14.750 I/PackageManager(  743): Considering granting permission android.permission.WRITE_EXTERNAL_STORAGE to package com.android.shell grant 3
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.WRITE_MEDIA_STORAGE: BasePermission{258c98a android.permission.WRITE_MEDIA_STORAGE}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.WRITE_MEDIA_STORAGE to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.INTERACT_ACROSS_USERS: BasePermission{dc15e4c android.permission.INTERACT_ACROSS_USERS}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.INTERACT_ACROSS_USERS_FULL: BasePermission{b05c2f6 android.permission.INTERACT_ACROSS_USERS_FULL}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS_FULL to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.CREATE_USERS: BasePermission{b7f629d android.permission.CREATE_USERS}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.CREATE_USERS to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_DEVICE_ADMINS: BasePermission{35f25a8 android.permission.MANAGE_DEVICE_ADMINS}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_DEVICE_ADMINS to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.ACCESS_LOWPAN_STATE: BasePermission{7b70312 android.permission.ACCESS_LOWPAN_STATE}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_LOWPAN_STATE to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_LOWPAN_STATE: BasePermission{dc7fae3 android.permission.CHANGE_LOWPAN_STATE}
  01-01 00:07:14.751 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_LOWPAN_STATE to package com.android.shell grant 2
  01-01 00:07:14.751 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_LOWPAN_CREDENTIAL: BasePermission{b292ce0 android.permission.READ_LOWPAN_CREDENTIAL}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.READ_LOWPAN_CREDENTIAL to package com.android.shell grant 2
  01-01 00:07:14.752 I/PackageManager(  743): Package com.android.shell checking android.permission.BLUETOOTH_STACK: BasePermission{1748b99 android.permission.BLUETOOTH_STACK}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH_STACK to package com.android.shell grant 2
  01-01 00:07:14.752 I/PackageManager(  743): Package com.android.shell checking android.permission.GET_ACCOUNTS: BasePermission{5e5c196 android.permission.GET_ACCOUNTS}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.GET_ACCOUNTS to package com.android.shell grant 3
  01-01 00:07:14.752 I/PackageManager(  743): Package com.android.shell checking android.permission.RETRIEVE_WINDOW_TOKEN: BasePermission{27e3e5e android.permission.RETRIEVE_WINDOW_TOKEN}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.RETRIEVE_WINDOW_TOKEN to package com.android.shell grant 2
  01-01 00:07:14.752 I/PackageManager(  743): Package com.android.shell checking android.permission.FRAME_STATS: BasePermission{175623f android.permission.FRAME_STATS}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.FRAME_STATS to package com.android.shell grant 2
  01-01 00:07:14.752 I/PackageManager(  743): Package com.android.shell checking android.permission.BIND_APPWIDGET: BasePermission{2afbc46 android.permission.BIND_APPWIDGET}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.BIND_APPWIDGET to package com.android.shell grant 2
  01-01 00:07:14.752 I/PackageManager(  743): Package com.android.shell checking android.permission.UPDATE_APP_OPS_STATS: BasePermission{c2d0964 android.permission.UPDATE_APP_OPS_STATS}
  01-01 00:07:14.752 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_APP_OPS_STATS to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.MODIFY_APPWIDGET_BIND_PERMISSIONS: BasePermission{ea4370c android.permission.MODIFY_APPWIDGET_BIND_PERMISSIONS}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_APPWIDGET_BIND_PERMISSIONS to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_APP_IDLE_STATE: BasePermission{5f1649f android.permission.CHANGE_APP_IDLE_STATE}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_APP_IDLE_STATE to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST: BasePermission{2d73705 android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.MOUNT_UNMOUNT_FILESYSTEMS: BasePermission{34b6cd7 android.permission.MOUNT_UNMOUNT_FILESYSTEMS}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.MOUNT_UNMOUNT_FILESYSTEMS to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.MOUNT_FORMAT_FILESYSTEMS: BasePermission{3f94855 android.permission.MOUNT_FORMAT_FILESYSTEMS}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.MOUNT_FORMAT_FILESYSTEMS to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.MODIFY_PHONE_STATE: BasePermission{5067f1d android.permission.MODIFY_PHONE_STATE}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_PHONE_STATE to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.NETWORK_SCAN: BasePermission{bebe26a android.permission.NETWORK_SCAN}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.NETWORK_SCAN to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.REGISTER_CALL_PROVIDER: BasePermission{d17a39b android.permission.REGISTER_CALL_PROVIDER}
  01-01 00:07:14.753 I/PackageManager(  743): Considering granting permission android.permission.REGISTER_CALL_PROVIDER to package com.android.shell grant 2
  01-01 00:07:14.753 I/PackageManager(  743): Package com.android.shell checking android.permission.REGISTER_CONNECTION_MANAGER: BasePermission{a67e35b android.permission.REGISTER_CONNECTION_MANAGER}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.REGISTER_CONNECTION_MANAGER to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.REGISTER_SIM_SUBSCRIPTION: BasePermission{bcc1338 android.permission.REGISTER_SIM_SUBSCRIPTION}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.REGISTER_SIM_SUBSCRIPTION to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.GET_APP_OPS_STATS: BasePermission{3431882 android.permission.GET_APP_OPS_STATS}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.GET_APP_OPS_STATS to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_APP_OPS_MODES: BasePermission{f61a7cd android.permission.MANAGE_APP_OPS_MODES}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_OPS_MODES to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.VIBRATE: BasePermission{79109c4 android.permission.VIBRATE}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.VIBRATE to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_ACTIVITY_STACKS: BasePermission{8e3b7f8 android.permission.MANAGE_ACTIVITY_STACKS}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ACTIVITY_STACKS to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.START_TASKS_FROM_RECENTS: BasePermission{cd314d1 android.permission.START_TASKS_FROM_RECENTS}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.START_TASKS_FROM_RECENTS to package com.android.shell grant 2
  01-01 00:07:14.754 I/PackageManager(  743): Package com.android.shell checking android.permission.START_ACTIVITIES_FROM_BACKGROUND: BasePermission{ddbb36 android.permission.START_ACTIVITIES_FROM_BACKGROUND}
  01-01 00:07:14.754 I/PackageManager(  743): Considering granting permission android.permission.START_ACTIVITIES_FROM_BACKGROUND to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.ACTIVITY_EMBEDDING: BasePermission{f375a37 android.permission.ACTIVITY_EMBEDDING}
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.ACTIVITY_EMBEDDING to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.CONNECTIVITY_INTERNAL: BasePermission{d87e95 android.permission.CONNECTIVITY_INTERNAL}
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.CONNECTIVITY_INTERNAL to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_COMPONENT_ENABLED_STATE: BasePermission{37ef27c android.permission.CHANGE_COMPONENT_ENABLED_STATE}
  01-01 00:07:14.755 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_COMPONENT_ENABLED_STATE to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_AUTO_FILL: BasePermission{5985ba4 android.permission.MANAGE_AUTO_FILL}
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_AUTO_FILL to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_CONTENT_CAPTURE: BasePermission{2a32d0d android.permission.MANAGE_CONTENT_CAPTURE}
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_CONTENT_CAPTURE to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_CONTENT_SUGGESTIONS: BasePermission{c4254c2 android.permission.MANAGE_CONTENT_SUGGESTIONS}
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_CONTENT_SUGGESTIONS to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_APP_PREDICTIONS: BasePermission{e1d62d3 android.permission.MANAGE_APP_PREDICTIONS}
  01-01 00:07:14.755 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_PREDICTIONS to package com.android.shell grant 2
  01-01 00:07:14.755 I/PackageManager(  743): Package com.android.shell checking android.permission.NETWORK_SETTINGS: BasePermission{a11abbb android.permission.NETWORK_SETTINGS}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.NETWORK_SETTINGS to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_WIFI_STATE: BasePermission{22a65e1 android.permission.CHANGE_WIFI_STATE}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_WIFI_STATE to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_TIME: BasePermission{2803d45 android.permission.SET_TIME}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.SET_TIME to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_TIME_ZONE: BasePermission{23e9808 android.permission.SET_TIME_ZONE}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.SET_TIME_ZONE to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.DISABLE_HIDDEN_API_CHECKS: BasePermission{8d18e10 android.permission.DISABLE_HIDDEN_API_CHECKS}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.DISABLE_HIDDEN_API_CHECKS to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_ROLE_HOLDERS: BasePermission{60e3ace android.permission.MANAGE_ROLE_HOLDERS}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ROLE_HOLDERS to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.OBSERVE_ROLE_HOLDERS: BasePermission{34dfdef android.permission.OBSERVE_ROLE_HOLDERS}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.OBSERVE_ROLE_HOLDERS to package com.android.shell grant 2
  01-01 00:07:14.756 I/PackageManager(  743): Package com.android.shell checking android.permission.STATUS_BAR_SERVICE: BasePermission{582b38f android.permission.STATUS_BAR_SERVICE}
  01-01 00:07:14.756 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR_SERVICE to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.STATUS_BAR: BasePermission{53255b6 android.permission.STATUS_BAR}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME: BasePermission{2b1bbe7 android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE: BasePermission{3be42ca android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_NOTIFICATION_ASSISTANT_SERVICE to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.WAKE_LOCK: BasePermission{833c2ee android.permission.WAKE_LOCK}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.WAKE_LOCK to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.CHANGE_OVERLAY_PACKAGES: BasePermission{ae28d09 android.permission.CHANGE_OVERLAY_PACKAGES}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_OVERLAY_PACKAGES to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.RESTRICTED_VR_ACCESS: BasePermission{764fb0e android.permission.RESTRICTED_VR_ACCESS}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.RESTRICTED_VR_ACCESS to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_BIND_INSTANT_SERVICE: BasePermission{551592f android.permission.MANAGE_BIND_INSTANT_SERVICE}
  01-01 00:07:14.757 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_BIND_INSTANT_SERVICE to package com.android.shell grant 2
  01-01 00:07:14.757 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_HARMFUL_APP_WARNINGS: BasePermission{6297b3c android.permission.SET_HARMFUL_APP_WARNINGS}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.SET_HARMFUL_APP_WARNINGS to package com.android.shell grant 2
  01-01 00:07:14.758 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_SENSORS: BasePermission{f9df0c5 android.permission.MANAGE_SENSORS}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_SENSORS to package com.android.shell grant 2
  01-01 00:07:14.758 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_AUDIO_POLICY: BasePermission{2f9ba1a android.permission.MANAGE_AUDIO_POLICY}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_AUDIO_POLICY to package com.android.shell grant 2
  01-01 00:07:14.758 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_CAMERA: BasePermission{524594b android.permission.MANAGE_CAMERA}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_CAMERA to package com.android.shell grant 2
  01-01 00:07:14.758 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_BLUETOOTH_WHEN_WIRELESS_CONSENT_REQUIRED: BasePermission{eb10f28 android.permission.MANAGE_BLUETOOTH_WHEN_WIRELESS_CONSENT_REQUIRED}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_BLUETOOTH_WHEN_WIRELESS_CONSENT_REQUIRED to package com.android.shell grant 2
  01-01 00:07:14.758 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_WIFI_WHEN_WIRELESS_CONSENT_REQUIRED: BasePermission{4f1d441 android.permission.MANAGE_WIFI_WHEN_WIRELESS_CONSENT_REQUIRED}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_WIFI_WHEN_WIRELESS_CONSENT_REQUIRED to package com.android.shell grant 2
  01-01 00:07:14.758 I/PackageManager(  743): Package com.android.shell checking android.permission.INSTALL_DYNAMIC_SYSTEM: BasePermission{4e95de6 android.permission.INSTALL_DYNAMIC_SYSTEM}
  01-01 00:07:14.758 I/PackageManager(  743): Considering granting permission android.permission.INSTALL_DYNAMIC_SYSTEM to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.CONTROL_KEYGUARD: BasePermission{7dd3f27 android.permission.CONTROL_KEYGUARD}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_KEYGUARD to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.SUSPEND_APPS: BasePermission{19bf5d4 android.permission.SUSPEND_APPS}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.SUSPEND_APPS to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.OBSERVE_APP_USAGE: BasePermission{a46737d android.permission.OBSERVE_APP_USAGE}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.OBSERVE_APP_USAGE to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.READ_CLIPBOARD_IN_BACKGROUND: BasePermission{6dd7272 android.permission.READ_CLIPBOARD_IN_BACKGROUND}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.READ_CLIPBOARD_IN_BACKGROUND to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.ENABLE_TEST_HARNESS_MODE: BasePermission{b54a6c3 android.permission.ENABLE_TEST_HARNESS_MODE}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.ENABLE_TEST_HARNESS_MODE to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_APPOPS: BasePermission{bac9b40 android.permission.MANAGE_APPOPS}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APPOPS to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.MANAGE_TEST_NETWORKS: BasePermission{34bca79 android.permission.MANAGE_TEST_NETWORKS}
  01-01 00:07:14.759 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_TEST_NETWORKS to package com.android.shell grant 2
  01-01 00:07:14.759 I/PackageManager(  743): Package com.android.shell checking android.permission.PACKET_KEEPALIVE_OFFLOAD: BasePermission{18c43be android.permission.PACKET_KEEPALIVE_OFFLOAD}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.PACKET_KEEPALIVE_OFFLOAD to package com.android.shell grant 2
  01-01 00:07:14.760 I/PackageManager(  743): Package com.android.shell checking android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS: BasePermission{850ec1f android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS to package com.android.shell grant 2
  01-01 00:07:14.760 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_WALLPAPER: BasePermission{144ee88 android.permission.SET_WALLPAPER}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.SET_WALLPAPER to package com.android.shell grant 2
  01-01 00:07:14.760 I/PackageManager(  743): Package com.android.shell checking android.permission.SET_WALLPAPER_COMPONENT: BasePermission{1602b6c android.permission.SET_WALLPAPER_COMPONENT}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.SET_WALLPAPER_COMPONENT to package com.android.shell grant 2
  01-01 00:07:14.760 I/PackageManager(  743): Package com.android.shell checking android.permission.CACHE_CONTENT: BasePermission{4b59535 android.permission.CACHE_CONTENT}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.CACHE_CONTENT to package com.android.shell grant 2
  01-01 00:07:14.760 I/PackageManager(  743): Package com.android.shell checking android.permission.BIND_EXPLICIT_HEALTH_CHECK_SERVICE: BasePermission{c4ddca android.permission.BIND_EXPLICIT_HEALTH_CHECK_SERVICE}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.BIND_EXPLICIT_HEALTH_CHECK_SERVICE to package com.android.shell grant 2
  01-01 00:07:14.760 I/PackageManager(  743): Package com.android.shell checking android.permission.INTERACT_ACROSS_PROFILES: BasePermission{3a22b3b android.permission.INTERACT_ACROSS_PROFILES}
  01-01 00:07:14.760 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_PROFILES to package com.android.shell grant 2
  01-01 00:07:14.761 I/PackageManager(  743): Package com.android.systemui checking android.permission.RECEIVE_BOOT_COMPLETED: BasePermission{57e6b34 android.permission.RECEIVE_BOOT_COMPLETED}
  01-01 00:07:14.761 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_BOOT_COMPLETED to package com.android.systemui grant 2
  01-01 00:07:14.761 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_EXTERNAL_STORAGE: BasePermission{454ae07 android.permission.READ_EXTERNAL_STORAGE}
  01-01 00:07:14.761 I/PackageManager(  743): Considering granting permission android.permission.READ_EXTERNAL_STORAGE to package com.android.systemui grant 3
  01-01 00:07:14.761 I/PackageManager(  743): Package com.android.systemui checking android.permission.WRITE_EXTERNAL_STORAGE: BasePermission{4ab56ff android.permission.WRITE_EXTERNAL_STORAGE}
  01-01 00:07:14.761 I/PackageManager(  743): Considering granting permission android.permission.WRITE_EXTERNAL_STORAGE to package com.android.systemui grant 3
  01-01 00:07:14.761 I/PackageManager(  743): Package com.android.systemui checking android.permission.WRITE_MEDIA_STORAGE: BasePermission{258c98a android.permission.WRITE_MEDIA_STORAGE}
  01-01 00:07:14.761 I/PackageManager(  743): Considering granting permission android.permission.WRITE_MEDIA_STORAGE to package com.android.systemui grant 2
  01-01 00:07:14.761 I/PackageManager(  743): Package com.android.systemui checking android.permission.WAKE_LOCK: BasePermission{833c2ee android.permission.WAKE_LOCK}
  01-01 00:07:14.761 I/PackageManager(  743): Considering granting permission android.permission.WAKE_LOCK to package com.android.systemui grant 2
  01-01 00:07:14.762 I/PackageManager(  743): Package com.android.systemui checking android.permission.INJECT_EVENTS: BasePermission{9ddeb44 android.permission.INJECT_EVENTS}
  01-01 00:07:14.762 I/PackageManager(  743): Considering granting permission android.permission.INJECT_EVENTS to package com.android.systemui grant 2
  01-01 00:07:14.762 I/PackageManager(  743): Package com.android.systemui checking android.permission.DUMP: BasePermission{efd7baa android.permission.DUMP}
  01-01 00:07:14.762 I/PackageManager(  743): Considering granting permission android.permission.DUMP to package com.android.systemui grant 2
  01-01 00:07:14.762 I/PackageManager(  743): Package com.android.systemui checking android.permission.WRITE_SETTINGS: BasePermission{7f20bfb android.permission.WRITE_SETTINGS}
  01-01 00:07:14.762 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SETTINGS to package com.android.systemui grant 2
  01-01 00:07:14.762 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_DEVICE_CONFIG: BasePermission{a8fc86c android.permission.READ_DEVICE_CONFIG}
  01-01 00:07:14.762 I/PackageManager(  743): Considering granting permission android.permission.READ_DEVICE_CONFIG to package com.android.systemui grant 2
  01-01 00:07:14.762 I/PackageManager(  743): Package com.android.systemui checking android.permission.STATUS_BAR_SERVICE: BasePermission{582b38f android.permission.STATUS_BAR_SERVICE}
  01-01 00:07:14.762 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR_SERVICE to package com.android.systemui grant 2
  01-01 00:07:14.762 I/PackageManager(  743): Package com.android.systemui checking android.permission.STATUS_BAR: BasePermission{53255b6 android.permission.STATUS_BAR}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.STATUS_BAR to package com.android.systemui grant 2
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.EXPAND_STATUS_BAR: BasePermission{1246e80 android.permission.EXPAND_STATUS_BAR}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.EXPAND_STATUS_BAR to package com.android.systemui grant 2
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.REMOTE_AUDIO_PLAYBACK: BasePermission{fda9258 android.permission.REMOTE_AUDIO_PLAYBACK}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.REMOTE_AUDIO_PLAYBACK to package com.android.systemui grant 2
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_USERS: BasePermission{bd62b15 android.permission.MANAGE_USERS}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USERS to package com.android.systemui grant 2
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_PROFILE: BasePermission{b211189 android.permission.READ_PROFILE}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.READ_PROFILE to package com.android.systemui grant 2
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_CONTACTS: BasePermission{885cd5c android.permission.READ_CONTACTS}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.READ_CONTACTS to package com.android.systemui grant 3
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONFIGURE_WIFI_DISPLAY: BasePermission{962658e android.permission.CONFIGURE_WIFI_DISPLAY}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.CONFIGURE_WIFI_DISPLAY to package com.android.systemui grant 2
  01-01 00:07:14.763 I/PackageManager(  743): Package com.android.systemui checking android.permission.WRITE_SECURE_SETTINGS: BasePermission{d7c418 android.permission.WRITE_SECURE_SETTINGS}
  01-01 00:07:14.763 I/PackageManager(  743): Considering granting permission android.permission.WRITE_SECURE_SETTINGS to package com.android.systemui grant 2
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.GET_APP_OPS_STATS: BasePermission{3431882 android.permission.GET_APP_OPS_STATS}
  01-01 00:07:14.764 I/PackageManager(  743): Considering granting permission android.permission.GET_APP_OPS_STATS to package com.android.systemui grant 2
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.USE_RESERVED_DISK: BasePermission{4f9c12c android.permission.USE_RESERVED_DISK}
  01-01 00:07:14.764 I/PackageManager(  743): Considering granting permission android.permission.USE_RESERVED_DISK to package com.android.systemui grant 2
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.BLUETOOTH: BasePermission{b5310ad android.permission.BLUETOOTH}
  01-01 00:07:14.764 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH to package com.android.systemui grant 2
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.BLUETOOTH_ADMIN: BasePermission{440ffe2 android.permission.BLUETOOTH_ADMIN}
  01-01 00:07:14.764 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH_ADMIN to package com.android.systemui grant 2
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.BLUETOOTH_PRIVILEGED: BasePermission{86fff73 android.permission.BLUETOOTH_PRIVILEGED}
  01-01 00:07:14.764 I/PackageManager(  743): Considering granting permission android.permission.BLUETOOTH_PRIVILEGED to package com.android.systemui grant 2
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_COARSE_LOCATION: BasePermission{8245500 android.permission.ACCESS_COARSE_LOCATION}
  01-01 00:07:14.764 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_COARSE_LOCATION to package com.android.systemui grant 3
  01-01 00:07:14.764 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.CHANGE_NETWORK_STATE: BasePermission{58bb452 android.permission.CHANGE_NETWORK_STATE}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_NETWORK_STATE to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_PRIVILEGED_PHONE_STATE: BasePermission{2d5a6 android.permission.READ_PRIVILEGED_PHONE_STATE}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.READ_PRIVILEGED_PHONE_STATE to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_WIFI_STATE: BasePermission{506348 android.permission.ACCESS_WIFI_STATE}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_WIFI_STATE to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.CHANGE_WIFI_STATE: BasePermission{22a65e1 android.permission.CHANGE_WIFI_STATE}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_WIFI_STATE to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.OVERRIDE_WIFI_CONFIG: BasePermission{495cffd android.permission.OVERRIDE_WIFI_CONFIG}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.OVERRIDE_WIFI_CONFIG to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_NETWORK_POLICY: BasePermission{3911b26 android.permission.MANAGE_NETWORK_POLICY}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_NETWORK_POLICY to package com.android.systemui grant 2
  01-01 00:07:14.765 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONNECTIVITY_INTERNAL: BasePermission{d87e95 android.permission.CONNECTIVITY_INTERNAL}
  01-01 00:07:14.765 I/PackageManager(  743): Considering granting permission android.permission.CONNECTIVITY_INTERNAL to package com.android.systemui grant 2
  01-01 00:07:14.766 I/PackageManager(  743): Package com.android.systemui checking android.permission.NETWORK_SETTINGS: BasePermission{a11abbb android.permission.NETWORK_SETTINGS}
  01-01 00:07:14.766 I/PackageManager(  743): Considering granting permission android.permission.NETWORK_SETTINGS to package com.android.systemui grant 2
  01-01 00:07:14.766 I/PackageManager(  743): Package com.android.systemui checking android.permission.TETHER_PRIVILEGED: BasePermission{41e1f06 android.permission.TETHER_PRIVILEGED}
  01-01 00:07:14.766 I/PackageManager(  743): Considering granting permission android.permission.TETHER_PRIVILEGED to package com.android.systemui grant 2
  01-01 00:07:14.766 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_NETWORK_USAGE_HISTORY: BasePermission{725367 android.permission.READ_NETWORK_USAGE_HISTORY}
  01-01 00:07:14.766 I/PackageManager(  743): Considering granting permission android.permission.READ_NETWORK_USAGE_HISTORY to package com.android.systemui grant 2
  01-01 00:07:14.766 I/PackageManager(  743): Package com.android.systemui checking android.permission.REQUEST_NETWORK_SCORES: BasePermission{b3ad7f5 android.permission.REQUEST_NETWORK_SCORES}
  01-01 00:07:14.766 I/PackageManager(  743): Considering granting permission android.permission.REQUEST_NETWORK_SCORES to package com.android.systemui grant 2
  01-01 00:07:14.766 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONTROL_VPN: BasePermission{24a6170 android.permission.CONTROL_VPN}
  01-01 00:07:14.766 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_VPN to package com.android.systemui grant 2
  01-01 00:07:14.766 I/PackageManager(  743): Package com.android.systemui checking android.permission.PEERS_MAC_ADDRESS: BasePermission{66a79ec android.permission.PEERS_MAC_ADDRESS}
  01-01 00:07:14.766 I/PackageManager(  743): Considering granting permission android.permission.PEERS_MAC_ADDRESS to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_USB: BasePermission{d5022b7 android.permission.MANAGE_USB}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_USB to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONTROL_DISPLAY_BRIGHTNESS: BasePermission{b74fb1 android.permission.CONTROL_DISPLAY_BRIGHTNESS}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_DISPLAY_BRIGHTNESS to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.DEVICE_POWER: BasePermission{c2dfe71 android.permission.DEVICE_POWER}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.DEVICE_POWER to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.MOUNT_UNMOUNT_FILESYSTEMS: BasePermission{34b6cd7 android.permission.MOUNT_UNMOUNT_FILESYSTEMS}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.MOUNT_UNMOUNT_FILESYSTEMS to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.MASTER_CLEAR: BasePermission{c411fcf android.permission.MASTER_CLEAR}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.MASTER_CLEAR to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.VIBRATE: BasePermission{79109c4 android.permission.VIBRATE}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.VIBRATE to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_SENSOR_PRIVACY: BasePermission{c3b0c96 android.permission.MANAGE_SENSOR_PRIVACY}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_SENSOR_PRIVACY to package com.android.systemui grant 2
  01-01 00:07:14.767 I/PackageManager(  743): Package com.android.systemui checking android.permission.REAL_GET_TASKS: BasePermission{d2e3cb9 android.permission.REAL_GET_TASKS}
  01-01 00:07:14.767 I/PackageManager(  743): Considering granting permission android.permission.REAL_GET_TASKS to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.GET_DETAILED_TASKS: BasePermission{5cd9147 android.permission.GET_DETAILED_TASKS}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.GET_DETAILED_TASKS to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.REORDER_TASKS: BasePermission{ed20869 android.permission.REORDER_TASKS}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.REORDER_TASKS to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.REMOVE_TASKS: BasePermission{34668fe android.permission.REMOVE_TASKS}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.REMOVE_TASKS to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.STOP_APP_SWITCHES: BasePermission{306ba68 android.permission.STOP_APP_SWITCHES}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.STOP_APP_SWITCHES to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.SET_SCREEN_COMPATIBILITY: BasePermission{eb4ad74 android.permission.SET_SCREEN_COMPATIBILITY}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.SET_SCREEN_COMPATIBILITY to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.START_ANY_ACTIVITY: BasePermission{4fe4017 android.permission.START_ANY_ACTIVITY}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.START_ANY_ACTIVITY to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.START_ACTIVITIES_FROM_BACKGROUND: BasePermission{ddbb36 android.permission.START_ACTIVITIES_FROM_BACKGROUND}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.START_ACTIVITIES_FROM_BACKGROUND to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.INTERACT_ACROSS_USERS: BasePermission{dc15e4c android.permission.INTERACT_ACROSS_USERS}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS to package com.android.systemui grant 2
  01-01 00:07:14.768 I/PackageManager(  743): Package com.android.systemui checking android.permission.INTERACT_ACROSS_USERS_FULL: BasePermission{b05c2f6 android.permission.INTERACT_ACROSS_USERS_FULL}
  01-01 00:07:14.768 I/PackageManager(  743): Considering granting permission android.permission.INTERACT_ACROSS_USERS_FULL to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.GET_TOP_ACTIVITY_INFO: BasePermission{927c04 android.permission.GET_TOP_ACTIVITY_INFO}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.GET_TOP_ACTIVITY_INFO to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_ACTIVITY_STACKS: BasePermission{8e3b7f8 android.permission.MANAGE_ACTIVITY_STACKS}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ACTIVITY_STACKS to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.START_ACTIVITY_AS_CALLER: BasePermission{f4035ed android.permission.START_ACTIVITY_AS_CALLER}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.START_ACTIVITY_AS_CALLER to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.START_TASKS_FROM_RECENTS: BasePermission{cd314d1 android.permission.START_TASKS_FROM_RECENTS}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.START_TASKS_FROM_RECENTS to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.GET_INTENT_SENDER_INTENT: BasePermission{1135c22 android.permission.GET_INTENT_SENDER_INTENT}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.GET_INTENT_SENDER_INTENT to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.INTERNAL_SYSTEM_WINDOW: BasePermission{4ee5af0 android.permission.INTERNAL_SYSTEM_WINDOW}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.INTERNAL_SYSTEM_WINDOW to package com.android.systemui grant 2
  01-01 00:07:14.769 I/PackageManager(  743): Package com.android.systemui checking android.permission.SYSTEM_ALERT_WINDOW: BasePermission{36bd733 android.permission.SYSTEM_ALERT_WINDOW}
  01-01 00:07:14.769 I/PackageManager(  743): Considering granting permission android.permission.SYSTEM_ALERT_WINDOW to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_FRAME_BUFFER: BasePermission{c7056ba android.permission.READ_FRAME_BUFFER}
  01-01 00:07:14.770 I/PackageManager(  743): Considering granting permission android.permission.READ_FRAME_BUFFER to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_APP_TOKENS: BasePermission{f9cc6b3 android.permission.MANAGE_APP_TOKENS}
  01-01 00:07:14.770 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_APP_TOKENS to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.REGISTER_WINDOW_MANAGER_LISTENERS: BasePermission{bbd5470 android.permission.REGISTER_WINDOW_MANAGER_LISTENERS}
  01-01 00:07:14.770 I/PackageManager(  743): Considering granting permission android.permission.REGISTER_WINDOW_MANAGER_LISTENERS to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.SET_ORIENTATION: BasePermission{17077b0 android.permission.SET_ORIENTATION}
  01-01 00:07:14.770 I/PackageManager(  743): Considering granting permission android.permission.SET_ORIENTATION to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.DISABLE_KEYGUARD: BasePermission{c0d41c6 android.permission.DISABLE_KEYGUARD}
  01-01 00:07:14.770 I/PackageManager(  743): Considering granting permission android.permission.DISABLE_KEYGUARD to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.MONITOR_INPUT: BasePermission{df743e9 android.permission.MONITOR_INPUT}
  01-01 00:07:14.770 I/PackageManager(  743): Considering granting permission android.permission.MONITOR_INPUT to package com.android.systemui grant 2
  01-01 00:07:14.770 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_DREAM_STATE: BasePermission{82f186e android.permission.READ_DREAM_STATE}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.READ_DREAM_STATE to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.WRITE_DREAM_STATE: BasePermission{8931b0f android.permission.WRITE_DREAM_STATE}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.WRITE_DREAM_STATE to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking com.android.alarm.permission.SET_ALARM: BasePermission{57b479c com.android.alarm.permission.SET_ALARM}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission com.android.alarm.permission.SET_ALARM to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS: BasePermission{eaeb4d android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.WRITE_EMBEDDED_SUBSCRIPTIONS to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONTROL_KEYGUARD: BasePermission{7dd3f27 android.permission.CONTROL_KEYGUARD}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_KEYGUARD to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.MODIFY_PHONE_STATE: BasePermission{5067f1d android.permission.MODIFY_PHONE_STATE}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_PHONE_STATE to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.GET_ACCOUNTS: BasePermission{5e5c196 android.permission.GET_ACCOUNTS}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.GET_ACCOUNTS to package com.android.systemui grant 3
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_ACCOUNTS: BasePermission{67ceb13 android.permission.MANAGE_ACCOUNTS}
  01-01 00:07:14.771 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_ACCOUNTS to package com.android.systemui grant 2
  01-01 00:07:14.771 I/PackageManager(  743): Package com.android.systemui checking android.permission.BIND_DEVICE_ADMIN: BasePermission{3f735a5 android.permission.BIND_DEVICE_ADMIN}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.BIND_DEVICE_ADMIN to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.CHANGE_COMPONENT_ENABLED_STATE: BasePermission{37ef27c android.permission.CHANGE_COMPONENT_ENABLED_STATE}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_COMPONENT_ENABLED_STATE to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.MEDIA_CONTENT_CONTROL: BasePermission{6254897 android.permission.MEDIA_CONTENT_CONTROL}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.MEDIA_CONTENT_CONTROL to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_KEYGUARD_SECURE_STORAGE: BasePermission{5384d7a android.permission.ACCESS_KEYGUARD_SECURE_STORAGE}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_KEYGUARD_SECURE_STORAGE to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.TRUST_LISTENER: BasePermission{6f0592b android.permission.TRUST_LISTENER}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.TRUST_LISTENER to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.USE_BIOMETRIC_INTERNAL: BasePermission{c746ef9 android.permission.USE_BIOMETRIC_INTERNAL}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.USE_BIOMETRIC_INTERNAL to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.USE_FINGERPRINT: BasePermission{3d6d4f2 android.permission.USE_FINGERPRINT}
  01-01 00:07:14.772 I/PackageManager(  743): Considering granting permission android.permission.USE_FINGERPRINT to package com.android.systemui grant 2
  01-01 00:07:14.772 I/PackageManager(  743): Package com.android.systemui checking android.permission.RESET_FINGERPRINT_LOCKOUT: BasePermission{1c34188 android.permission.RESET_FINGERPRINT_LOCKOUT}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.RESET_FINGERPRINT_LOCKOUT to package com.android.systemui grant 2
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_BIOMETRIC: BasePermission{54a8721 android.permission.MANAGE_BIOMETRIC}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_BIOMETRIC to package com.android.systemui grant 2
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_SLICE_PERMISSIONS: BasePermission{a6dc746 android.permission.MANAGE_SLICE_PERMISSIONS}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_SLICE_PERMISSIONS to package com.android.systemui grant 2
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS: BasePermission{850ec1f android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_KEYGUARD_SECURE_NOTIFICATIONS to package com.android.systemui grant 2
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.GET_RUNTIME_PERMISSIONS: BasePermission{e1a41bd android.permission.GET_RUNTIME_PERMISSIONS}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.GET_RUNTIME_PERMISSIONS to package com.android.systemui grant 2
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.SET_WALLPAPER: BasePermission{144ee88 android.permission.SET_WALLPAPER}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.SET_WALLPAPER to package com.android.systemui grant 2
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.CAMERA: BasePermission{9eee716 android.permission.CAMERA}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.CAMERA to package com.android.systemui grant 3
  01-01 00:07:14.773 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_MEDIA_PROJECTION: BasePermission{9995d07 android.permission.MANAGE_MEDIA_PROJECTION}
  01-01 00:07:14.773 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_MEDIA_PROJECTION to package com.android.systemui grant 2
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking android.permission.FOREGROUND_SERVICE: BasePermission{2eb39c7 android.permission.FOREGROUND_SERVICE}
  01-01 00:07:14.774 I/PackageManager(  743): Considering granting permission android.permission.FOREGROUND_SERVICE to package com.android.systemui grant 2
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking android.permission.RECORD_AUDIO: BasePermission{4866020 android.permission.RECORD_AUDIO}
  01-01 00:07:14.774 I/PackageManager(  743): Considering granting permission android.permission.RECORD_AUDIO to package com.android.systemui grant 3
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_VOICE_INTERACTION_SERVICE: BasePermission{b0eee34 android.permission.ACCESS_VOICE_INTERACTION_SERVICE}
  01-01 00:07:14.774 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_VOICE_INTERACTION_SERVICE to package com.android.systemui grant 2
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST: BasePermission{2d73705 android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST}
  01-01 00:07:14.774 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST to package com.android.systemui grant 2
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking android.permission.TABLET_MODE: BasePermission{227745d android.permission.TABLET_MODE}
  01-01 00:07:14.774 I/PackageManager(  743): Considering granting permission android.permission.TABLET_MODE to package com.android.systemui grant 2
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking com.android.systemui.permission.SELF: BasePermission{d2f11d2 com.android.systemui.permission.SELF}
  01-01 00:07:14.774 I/PackageManager(  743): Considering granting permission com.android.systemui.permission.SELF to package com.android.systemui grant 2
  01-01 00:07:14.774 I/PackageManager(  743): Package com.android.systemui checking android.permission.BIND_QUICK_SETTINGS_TILE: BasePermission{ee4c2a3 android.permission.BIND_QUICK_SETTINGS_TILE}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.BIND_QUICK_SETTINGS_TILE to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.MODIFY_DAY_NIGHT_MODE: BasePermission{7c6b9a0 android.permission.MODIFY_DAY_NIGHT_MODE}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_DAY_NIGHT_MODE to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.UPDATE_APP_OPS_STATS: BasePermission{c2d0964 android.permission.UPDATE_APP_OPS_STATS}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.UPDATE_APP_OPS_STATS to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.BATTERY_STATS: BasePermission{e8f9abf android.permission.BATTERY_STATS}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.BATTERY_STATS to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS: BasePermission{59d5490 android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.RECEIVE_MEDIA_RESOURCE_USAGE: BasePermission{debf959 android.permission.RECEIVE_MEDIA_RESOURCE_USAGE}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.RECEIVE_MEDIA_RESOURCE_USAGE to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_NOTIFICATIONS: BasePermission{50401b5 android.permission.MANAGE_NOTIFICATIONS}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_NOTIFICATIONS to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_VR_MANAGER: BasePermission{748791e android.permission.ACCESS_VR_MANAGER}
  01-01 00:07:14.775 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_VR_MANAGER to package com.android.systemui grant 2
  01-01 00:07:14.775 I/PackageManager(  743): Package com.android.systemui checking android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME: BasePermission{2b1bbe7 android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.RESET_SHORTCUT_MANAGER_THROTTLING: BasePermission{9f6e5ff android.permission.RESET_SHORTCUT_MANAGER_THROTTLING}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.RESET_SHORTCUT_MANAGER_THROTTLING to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.MODIFY_THEME_OVERLAY: BasePermission{a6dcfcc android.permission.MODIFY_THEME_OVERLAY}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_THEME_OVERLAY to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.MODIFY_ACCESSIBILITY_DATA: BasePermission{9d9d215 android.permission.MODIFY_ACCESSIBILITY_DATA}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.MODIFY_ACCESSIBILITY_DATA to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.CHANGE_ACCESSIBILITY_VOLUME: BasePermission{ff092a android.permission.CHANGE_ACCESSIBILITY_VOLUME}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_ACCESSIBILITY_VOLUME to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.BIND_RESOLVER_RANKER_SERVICE: BasePermission{1dde31b android.permission.BIND_RESOLVER_RANKER_SERVICE}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.BIND_RESOLVER_RANKER_SERVICE to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.ACCESS_INSTANT_APPS: BasePermission{c3b4ea5 android.permission.ACCESS_INSTANT_APPS}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_INSTANT_APPS to package com.android.systemui grant 2
  01-01 00:07:14.776 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS: BasePermission{fd4f27a android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS}
  01-01 00:07:14.776 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_REMOTE_APP_TRANSITION_ANIMATIONS to package com.android.systemui grant 2
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.permission.CHANGE_OVERLAY_PACKAGES: BasePermission{ae28d09 android.permission.CHANGE_OVERLAY_PACKAGES}
  01-01 00:07:14.777 I/PackageManager(  743): Considering granting permission android.permission.CHANGE_OVERLAY_PACKAGES to package com.android.systemui grant 2
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.permission.WATCH_APPOPS: BasePermission{88e1cb8 android.permission.WATCH_APPOPS}
  01-01 00:07:14.777 I/PackageManager(  743): Considering granting permission android.permission.WATCH_APPOPS to package com.android.systemui grant 2
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.car.permission.CONTROL_CAR_CLIMATE: null
  01-01 00:07:14.777 I/PackageManager(  743): Unknown permission android.car.permission.CONTROL_CAR_CLIMATE in package com.android.systemui
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.car.permission.CAR_DRIVING_STATE: null
  01-01 00:07:14.777 I/PackageManager(  743): Unknown permission android.car.permission.CAR_DRIVING_STATE in package com.android.systemui
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.car.permission.CAR_CONTROL_AUDIO_VOLUME: null
  01-01 00:07:14.777 I/PackageManager(  743): Unknown permission android.car.permission.CAR_CONTROL_AUDIO_VOLUME in package com.android.systemui
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.permission.MANAGE_DEBUGGING: BasePermission{63cba24 android.permission.MANAGE_DEBUGGING}
  01-01 00:07:14.777 I/PackageManager(  743): Considering granting permission android.permission.MANAGE_DEBUGGING to package com.android.systemui grant 2
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS: BasePermission{2edf3c9 android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS}
  01-01 00:07:14.777 I/PackageManager(  743): Considering granting permission android.permission.HIDE_NON_SYSTEM_OVERLAY_WINDOWS to package com.android.systemui grant 2
  01-01 00:07:14.777 I/PackageManager(  743): Package com.android.systemui checking android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS: BasePermission{e2b29bc android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS}
  01-01 00:07:14.777 I/PackageManager(  743): Considering granting permission android.permission.CONTROL_DISPLAY_COLOR_TRANSFORMS to package com.android.systemui grant 2
  01-01 00:07:14.778 I/PackageManager(  743): Package com.android.systemui checking android.permission.READ_CALL_LOG: BasePermission{1b56d2 android.permission.READ_CALL_LOG}
  01-01 00:07:14.778 I/PackageManager(  743): Considering granting permission android.permission.READ_CALL_LOG to package com.android.systemui grant 3
  01-01 00:07:14.778 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.INTERNET: BasePermission{8979394 android.permission.INTERNET}
  01-01 00:07:14.778 I/PackageManager(  743): Considering granting permission android.permission.INTERNET to package com.android.captiveportallogin grant 2
  01-01 00:07:14.778 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.ACCESS_NETWORK_STATE: BasePermission{2982c3b android.permission.ACCESS_NETWORK_STATE}
  01-01 00:07:14.778 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_NETWORK_STATE to package com.android.captiveportallogin grant 2
  01-01 00:07:14.778 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.ACCESS_WIFI_STATE: BasePermission{506348 android.permission.ACCESS_WIFI_STATE}
  01-01 00:07:14.778 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_WIFI_STATE to package com.android.captiveportallogin grant 2
  01-01 00:07:14.778 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.ACCESS_FINE_LOCATION: BasePermission{476a632 android.permission.ACCESS_FINE_LOCATION}
  01-01 00:07:14.778 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_FINE_LOCATION to package com.android.captiveportallogin grant 3
  01-01 00:07:14.779 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS: BasePermission{237b8b1 android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS}
  01-01 00:07:14.779 I/PackageManager(  743): Considering granting permission android.permission.CONNECTIVITY_USE_RESTRICTED_NETWORKS to package com.android.captiveportallogin grant 2
  01-01 00:07:14.779 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.NETWORK_BYPASS_PRIVATE_DNS: BasePermission{f927a91 android.permission.NETWORK_BYPASS_PRIVATE_DNS}
  01-01 00:07:14.779 I/PackageManager(  743): Considering granting permission android.permission.NETWORK_BYPASS_PRIVATE_DNS to package com.android.captiveportallogin grant 2
  01-01 00:07:14.779 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.MAINLINE_NETWORK_STACK: BasePermission{fdc8df6 android.permission.MAINLINE_NETWORK_STACK}
  01-01 00:07:14.779 I/PackageManager(  743): Considering granting permission android.permission.MAINLINE_NETWORK_STACK to package com.android.captiveportallogin grant 2
  01-01 00:07:14.779 I/PackageManager(  743): Package com.android.captiveportallogin checking android.permission.ACCESS_COARSE_LOCATION: BasePermission{8245500 android.permission.ACCESS_COARSE_LOCATION}
  01-01 00:07:14.779 I/PackageManager(  743): android.permission.ACCESS_COARSE_LOCATION is newly added for com.android.captiveportallogin
  01-01 00:07:14.779 I/PackageManager(  743): Considering granting permission android.permission.ACCESS_COARSE_LOCATION to package com.android.captiveportallogin grant 3
  01-01 00:07:14.780 W/PackageManager(  743): Unknown package com.android.carrierdefaultapp in sysconfig <app-link>
  01-01 00:07:14.780 V/PackageManager(  743): reconcileAppsData for null u0 0x3 migrateAppData=true
  01-01 00:07:14.787 I/SELinux (  460): SELinux: Loaded file_contexts
  01-01 00:07:14.807 W/installd(  460): Requested default storage /data/user_de/0/com.google.android.ext.services is not active; migrating from /data/data/com.google.android.ext.services
  01-01 00:07:14.832 W/installd(  460): Requested default storage /data/user_de/0/android is not active; migrating from /data/data/android
  01-01 00:07:14.855 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.857 W/installd(  460): Requested default storage /data/user_de/0/com.google.android.permissioncontroller is not active; migrating from /data/data/com.google.android.permissioncontroller
  01-01 00:07:14.881 W/installd(  460): Requested default storage /data/user_de/0/com.android.providers.settings is not active; migrating from /data/data/com.android.providers.settings
  01-01 00:07:14.905 W/installd(  460): Requested default storage /data/user_de/0/android.ext.shared is not active; migrating from /data/data/android.ext.shared
  01-01 00:07:14.928 W/installd(  460): Requested default storage /data/user_de/0/com.spreadtrum.ims is not active; migrating from /data/data/com.spreadtrum.ims
  01-01 00:07:14.951 W/installd(  460): Requested default storage /data/user_de/0/com.android.settings is not active; migrating from /data/data/com.android.settings
  01-01 00:07:14.956 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:14.975 W/installd(  460): Requested default storage /data/user_de/0/com.android.phone is not active; migrating from /data/data/com.android.phone
  01-01 00:07:14.997 I/commit_sys_config_file(  743): [package-perms-0,16]
  01-01 00:07:15.007 W/installd(  460): Requested default storage /data/user_de/0/com.android.shell is not active; migrating from /data/data/com.android.shell
  01-01 00:07:15.029 W/installd(  460): Requested default storage /data/user_de/0/com.android.systemui is not active; migrating from /data/data/com.android.systemui
  01-01 00:07:15.041 V/PackageManager(  743): reconcileAppsData finished 10 packages
  01-01 00:07:15.042 D/SystemServerInitThreadPool(  743): Started executing prepareAppData
  01-01 00:07:15.048 D/SystemServerTimingAsync(  743): AppDataFixup took to complete: 6ms
  01-01 00:07:15.057 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:15.081 I/SELinux (  743): SELinux: Loaded file_contexts
  01-01 00:07:15.097 I/commit_sys_config_file(  743): [package-user-0,6]
  01-01 00:07:15.097 I/commit_sys_config_file(  743): [package,56]
  
  01-01 00:07:15.097 I/boot_progress_pms_ready(  743): 18411
  
  ```

- boot_progress_pms_ready 到 boot_progress_ams_ready 耗时2512ms，主要是启动一些java service，其代码在frameworks/base/services/java/com/android/server/SystemServer.java +979，我们已经筛查出一些不必要的service，所以此部分耗时，优化空间已不大。

  ```c
  01-01 00:07:15.097 I/boot_progress_pms_ready(  743): 18411
      
  01-01 00:07:15.097 E/PackageManager(  743): There should probably be a verifier, but, none were found
  01-01 00:07:15.098 W/PackageManager(  743): Intent filter verifier not found
  01-01 00:07:15.102 D/PackageManager(  743): Ephemeral resolver NOT found; no matching intent filters
  01-01 00:07:15.103 D/PackageManager(  743): Instant App installer not found with android.intent.action.INSTALL_INSTANT_APP_PACKAGE
  01-01 00:07:15.103 D/PackageManager(  743): Clear ephemeral installer activity
  01-01 00:07:15.125 W/installd(  460): Requested default storage /data/user_de/0/com.android.packageinstaller is not active; migrating from /data/data/com.android.packageinstaller
  01-01 00:07:15.157 I/ServiceManager(  470): Waiting for service 'package_native' on '/dev/binder'...
  01-01 00:07:15.161 I/system_server(  743): Explicit concurrent copying GC freed 41746(3539KB) AllocSpace objects, 22(900KB) LOS objects, 45% free, 1839KB/3375KB, paused 70us total 55.194ms
  01-01 00:07:15.164 I/Watchdog(  743): Resuming HandlerChecker: main thread for reason: packagemanagermain. Pause count: 0
  01-01 00:07:15.171 D/SystemServerTiming(  743): StartPackageManagerService took to complete: 3996ms
  01-01 00:07:15.171 I/SystemServer(  743): StartUserManagerService
  01-01 00:07:15.171 I/SystemServiceManager(  743): Starting com.android.server.pm.UserManagerService$LifeCycle
  01-01 00:07:15.172 D/SystemServerTiming(  743): StartUserManagerService took to complete: 1ms
  01-01 00:07:15.172 I/SystemServer(  743): InitAttributerCache
  01-01 00:07:15.173 D/SystemServerTiming(  743): InitAttributerCache took to complete: 0ms
  01-01 00:07:15.173 I/SystemServer(  743): SetSystemProcess
  01-01 00:07:15.193 I/am_uid_running(  743): 1000
  01-01 00:07:15.197 I/lowmemorykiller(  432): lmkd data connection established
  01-01 00:07:15.197 I/am_uid_active(  743): 1000
      ...
      ...
  09-15 09:31:13.971 W/PackageManager.ModuleInfoProvider(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:13.971 D/SystemServerTiming(  743): MakePackageManagerServiceReady took to complete: 535ms
  09-15 09:31:13.971 I/SystemServer(  743): StartDeviceSpecificServices
  09-15 09:31:13.971 D/SystemServerTiming(  743): StartDeviceSpecificServices took to complete: 0ms
  09-15 09:31:13.971 I/SystemServer(  743): StartBootPhaseDeviceSpecificServicesReady
  09-15 09:31:13.971 I/SystemServiceManager(  743): Starting phase 520
  09-15 09:31:13.971 D/SystemServerTiming(  743): StartBootPhaseDeviceSpecificServicesReady took to complete: 0ms
  09-15 09:31:13.974 I/LmKillerTracker(  743): connected to lmkiller
  09-15 09:31:13.974 D/lowmemorykiller(  432): unix socket is connected:12
  09-15 09:31:13.975 W/UsageStatsService(  743): Event reported without a package name, eventType:15
  09-15 09:31:13.977 I/ActivityManagerEx(  743): pre start phone process
  09-15 09:31:13.977 I/am_uid_running(  743): 1001
  09-15 09:31:13.980 I/ActivityManager(  743): System now ready
  
  09-15 09:31:13.980 I/boot_progress_ams_ready(  743): 20923
  
  ```

- boot_progress_ams_ready 到 boot_progress_enable_screen 耗时529ms，优化空间不大

  ```c
  09-15 09:31:13.980 I/boot_progress_ams_ready(  743): 20923
  09-15 09:31:14.007 D/Zygote  (  391): Forked child process 918
  09-15 09:31:14.012 I/am_proc_start(  743): [0,918,1001,com.android.phone,added application,com.android.phone]
  09-15 09:31:14.013 I/ActivityManager(  743): Start proc 918:com.android.phone/1001 for added application com.android.phone
  09-15 09:31:14.061 D/PowerController.BattStats(  743): updatePowerMode: new mode:-1, now:21004
  09-15 09:31:14.062 I/SystemServer(  743): Making services ready
  09-15 09:31:14.062 I/SystemServer(  743): StartObservingNativeCrashes
  09-15 09:31:14.062 D/SystemServerTiming(  743): StartObservingNativeCrashes took to complete: 1ms
  09-15 09:31:14.063 I/SystemServer(  743): StartSystemUI
  09-15 09:31:14.064 D/SystemServerInitThreadPool(  743): Started executing WebViewFactoryPreparation
  09-15 09:31:14.064 I/SystemServer(  743): WebViewFactoryPreparation
  09-15 09:31:14.064 I/am_uid_running(  743): 10008
  09-15 09:31:14.064 I/WebViewUpdateServiceImpl(  743): Skipping one-time migration: no fallback provider
  09-15 09:31:14.066 D/SystemServerTiming(  743): StartSystemUI took to complete: 4ms
  09-15 09:31:14.066 I/SystemServer(  743): MakeNetworkManagementServiceReady
  09-15 09:31:14.067 W/NetworkManagement(  743): setDataSaverMode(): already false
  09-15 09:31:14.068 I/netd    (  390): firewallSetFirewallType(1) <0.01ms>
  09-15 09:31:14.069 D/SystemServerTiming(  743): MakeNetworkManagementServiceReady took to complete: 3ms
  09-15 09:31:14.070 I/SystemServer(  743): MakeIpSecServiceReady
  09-15 09:31:14.070 E/BatteryExternalStatsWorker(  743): no controller energy info supplied for telephony
  09-15 09:31:14.071 I/netd    (  390): isAlive() -> {"true"} <0.01ms>
  09-15 09:31:14.071 D/IpSecService(  743): IpSecService is ready
  09-15 09:31:14.071 D/SystemServerTiming(  743): MakeIpSecServiceReady took to complete: 2ms
  09-15 09:31:14.071 I/SystemServer(  743): MakeNetworkPolicyServiceReady
  09-15 09:31:14.072 W/NetworkPolicy(  743): setRestrictBackgroundUL: already false
  09-15 09:31:14.077 I/am_uid_running(  743): 1037
  09-15 09:31:14.077 I/netd    (  390): firewallReplaceUidChain("fw_standby", "false", []) -> {"true"} <0.08ms>
  09-15 09:31:14.080 D/SystemServerTimingAsync(  743): WebViewFactoryPreparation took to complete: 16ms
  09-15 09:31:14.081 D/SystemServerInitThreadPool(  743): Finished executing WebViewFactoryPreparation
  09-15 09:31:14.081 W/BestClock(  743): java.time.DateTimeException: Missing NTP fix
  09-15 09:31:14.084 D/ConnectivityService(  743): listenForNetwork for uid/pid:1000/743 NetworkRequest [ LISTEN id=5, [ Capabilities: NOT_RESTRICTED&TRUSTED&NOT_VPN&FOREGROUND Uid: 1000] ]
  09-15 09:31:14.085 D/SystemServerTiming(  743): MakeNetworkPolicyServiceReady took to complete: 13ms
  09-15 09:31:14.085 I/SystemServer(  743): PhaseThirdPartyAppsCanStart
  09-15 09:31:14.085 I/SystemServiceManager(  743): Starting phase 600
  09-15 09:31:14.086 I/ExplicitHealthCheckController(  743): Explicit health checks enabled.
  09-15 09:31:14.086 I/PackageWatchdog(  743): Syncing state, reason: health check state enabled
  09-15 09:31:14.086 I/PackageWatchdog(  743): Not pruning observers, elapsed time: 0ms
  09-15 09:31:14.086 I/PackageWatchdog(  743): Cancelling state sync, nothing to sync
  09-15 09:31:14.088 D/SprdLightsUtils(  743): id = 4; isBatteryLightOpen = true
  09-15 09:31:14.091 I/WallpaperManagerService(  743): No static wallpaper imagery; defaults will be shown
  09-15 09:31:14.091 D/Zygote  (  391): Forked child process 940
  09-15 09:31:14.091 V/WallpaperManagerService(  743): bindWallpaperComponentLocked: componentName=ComponentInfo{com.android.systemui/com.android.systemui.ImageWallpaper}
  09-15 09:31:14.094 W/WallpaperManagerService(  743): no current wallpaper -- first boot?
  09-15 09:31:14.094 V/WallpaperManagerService(  743): bindWallpaperComponentLocked: componentName=null
  09-15 09:31:14.094 V/WallpaperManagerService(  743): No default component; using image wallpaper
  09-15 09:31:14.096 I/am_proc_start(  743): [0,940,10008,com.android.systemui,service,{com.android.systemui/com.android.systemui.SystemUIService}]
  09-15 09:31:14.096 I/ActivityManager(  743): Start proc 940:com.android.systemui/u0a8 for service {com.android.systemui/com.android.systemui.SystemUIService}
  09-15 09:31:14.124 I/commit_sys_config_file(  743): [package-perms-0,9]
  09-15 09:31:14.124 I/PackageWatchdog(  743): Saving observer state to file
  09-15 09:31:14.150 W/SystemServiceManager(  743): Service com.android.server.trust.TrustManagerService took 53 ms in onBootPhase
  09-15 09:31:14.160 I/am_proc_bound(  743): [0,918,com.android.phone]
  09-15 09:31:14.160 D/SystemServerTiming(  743): PhaseThirdPartyAppsCanStart took to complete: 76ms
  09-15 09:31:14.160 I/SystemServer(  743): MakeLocationServiceReady
  09-15 09:31:14.181 I/am_uid_active(  743): 1001
  09-15 09:31:14.183 D/LocationBlacklist(  743): whitelist: []
  09-15 09:31:14.183 D/LocationBlacklist(  743): blacklist: []
  09-15 09:31:14.187 D/LocationManagerService(  743): passive provider attached
  09-15 09:31:14.189 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.gnss@2.0::IGnss/default in either framework or device manifest.
  09-15 09:31:14.189 D/GnssLocationProvider(  743): gnssHal 2.0 was null, trying 1.1
  09-15 09:31:14.190 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.gnss@1.1::IGnss/default in either framework or device manifest.
  09-15 09:31:14.190 D/GnssLocationProvider(  743): gnssHal 1.1 was null, trying 1.0
  09-15 09:31:14.191 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.gnss@1.0::IGnss/default in either framework or device manifest.
  09-15 09:31:14.196 D/Zygote  (  392): Forked child process 961
  09-15 09:31:14.197 I/LocationManagerService(  743): gnss location provider not support !
  09-15 09:31:14.197 D/LocationManagerService(  743): certificates for location providers pulled from: [com.android.location.fused]
  09-15 09:31:14.198 W/ServiceWatcher(  743): com.android.location.fused not found
  09-15 09:31:14.198 W/SystemServer(  743): ***********************************************
  09-15 09:31:14.198 D/LocationManagerService(  743): passive provider enabled is now false
  09-15 09:31:14.199 D/LocationManagerService(  743): passive provider useable is now true
  09-15 09:31:14.199 E/SystemServer(  743): BOOT FAILURE Notifying Location Service running
  09-15 09:31:14.199 E/SystemServer(  743): java.lang.IllegalStateException: Unable to find a fused location provider that is in the system partition with version 0 and signed with the platform certificate. Such a package is needed to provide a default fused location provider in the event that no other fused location provider has been installed or is currently available. For example, coreOnly boot mode when decrypting the data partition. The fallback must also be marked coreApp="true" in the manifest
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.LocationManagerService.ensureFallbackFusedProviderPresentLocked(LocationManagerService.java:773)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.LocationManagerService.initializeProvidersLocked(LocationManagerService.java:832)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.LocationManagerService.initializeLocked(LocationManagerService.java:333)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.LocationManagerService.systemRunning(LocationManagerService.java:313)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2260)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.199 E/SystemServer(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.199 E/SystemServer(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.199 I/LocationManagerService(  743): applyRequirementsLocked to com.android.server.LocationManagerService$LocationProvider@afa76ea prvider.
  09-15 09:31:14.200 D/SystemServerTiming(  743): MakeLocationServiceReady took to complete: 39ms
  09-15 09:31:14.200 I/SystemServer(  743): MakeCountryDetectionServiceReady
  09-15 09:31:14.200 I/am_wtf  (  743): [0,743,system_server,-1,SystemServer,Unable to find a fused location provider that is in the system partition with version 0 and signed with the platform certificate. Such a package is needed to provide a default fused location provider in the event that no other fused location provider has been installed or is currently available. For example, coreOnly boot mode when decrypting the data partition. The fallback must also be marked coreApp="true" in the manifest]
  09-15 09:31:14.200 D/SystemServerTiming(  743): MakeCountryDetectionServiceReady took to complete: 0ms
  09-15 09:31:14.200 I/SystemServer(  743): MakeInputManagerServiceReady
  09-15 09:31:14.200 W/ActivityManager(  743): Slow operation: 123ms so far, now at startProcess: returned from zygote!
  09-15 09:31:14.201 W/ActivityManager(  743): Slow operation: 124ms so far, now at startProcess: done updating battery stats
  09-15 09:31:14.201 I/am_proc_start(  743): [0,961,1037,WebViewLoader-armeabi-v7a,NULL,]
  09-15 09:31:14.202 W/ActivityManager(  743): Slow operation: 124ms so far, now at startProcess: building log message
  09-15 09:31:14.202 I/ActivityManager(  743): Start proc 961:WebViewLoader-armeabi-v7a/1037 [android.webkit.WebViewLibraryLoader$RelroFileCreator] for null
  09-15 09:31:14.202 W/ActivityManager(  743): Slow operation: 124ms so far, now at startProcess: starting to update pids map
  09-15 09:31:14.202 D/PowerManagerService(  743): acquireWakeLockInternal: lock=2492048, flags=0x1, tag="WiredAccessoryManager", ws=null, uid=1000, pid=743 packageName=android
  09-15 09:31:14.202 D/PowerManagerService(  743): updateWakeLockSummaryLocked: mWakefulness=Awake, mWakeLockSummary=0x1
  09-15 09:31:14.202 D/PowerManagerService(  743): updateUserActivitySummaryLocked: mWakefulness=Awake, mUserActivitySummary=0x1, nextTimeout=53000 (in 31855 ms)
  09-15 09:31:14.202 D/PowerManagerService(  743): updateDisplayPowerStateLocked: mDisplayReady=true, policy=3, mWakefulness=1, mWakeLockSummary=0x1, mUserActivitySummary=0x1, mBootCompleted=false, screenBrightnessOverride=102, useAutoBrightness=false, mScreenBrightnessBoostInProgress=false, mIsVrModeEnabled= false, sQuiescent=false
  09-15 09:31:14.202 D/PowerManagerService(  743): Acquiring suspend blocker "PowerManagerService.WakeLocks".
  09-15 09:31:14.202 I/DropBoxManagerService(  743): add tag=system_server_wtf isTagEnabled=true flags=0x2
  09-15 09:31:14.203 I/InputReader(  743): Reconfiguring input devices.  changes=0x00000030
  09-15 09:31:14.204 W/ActivityManager(  743): Slow operation: 126ms so far, now at startProcess: done updating pids map
  09-15 09:31:14.204 W/ActivityManager(  743): Slow operation: 126ms so far, now at startProcess: asking zygote to start proc
  09-15 09:31:14.205 D/SystemServerTiming(  743): MakeInputManagerServiceReady took to complete: 4ms
  09-15 09:31:14.205 I/SystemServer(  743): MakeTelephonyRegistryReady
  09-15 09:31:14.205 D/SystemServerTiming(  743): MakeTelephonyRegistryReady took to complete: 0ms
  09-15 09:31:14.205 I/SystemServer(  743): MakeMediaRouterServiceReady
  09-15 09:31:14.205 D/SystemServerTiming(  743): MakeMediaRouterServiceReady took to complete: 1ms
  09-15 09:31:14.205 I/SystemServer(  743): MakeMmsServiceReady
  09-15 09:31:14.206 I/MmsServiceBroker(  743): Delay connecting to MmsService until an API is called
  09-15 09:31:14.206 D/SystemServerTiming(  743): MakeMmsServiceReady took to complete: 0ms
  09-15 09:31:14.206 I/SystemServer(  743): IncidentDaemonReady
  09-15 09:31:14.206 D/SystemServerTiming(  743): IncidentDaemonReady took to complete: 1ms
  09-15 09:31:14.207 I/SystemServer(  743): PowerController Service systemReady
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): No service published for: uimode
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): android.os.ServiceManager$ServiceNotFoundException: No service published for: uimode
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.os.ServiceManager.getServiceOrThrow(ServiceManager.java:148)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.app.UiModeManager.<init>(UiModeManager.java:132)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.app.SystemServiceRegistry$53.createService(SystemServiceRegistry.java:670)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.app.SystemServiceRegistry$53.createService(SystemServiceRegistry.java:667)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.app.SystemServiceRegistry$CachedServiceFetcher.getService(SystemServiceRegistry.java:1416)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.app.SystemServiceRegistry.getSystemService(SystemServiceRegistry.java:1332)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at android.app.ContextImpl.getSystemService(ContextImpl.java:1805)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.power.sprdpower.PowerController.systemReady(PowerController.java:555)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2342)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.216 E/SystemServiceRegistry(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.218 I/am_wtf  (  743): [0,743,system_server,-1,SystemServiceRegistry,No service published for: uimode]
  09-15 09:31:14.219 I/DropBoxManagerService(  743): add tag=system_server_wtf isTagEnabled=true flags=0x2
  09-15 09:31:14.223 I/m.android.phon(  918): The ClassLoaderContext is a special shared library.
  09-15 09:31:14.225 D/PowerController(  743): ignoreProcStateForAppIdle: true
  09-15 09:31:14.226 D/PowerController(  743): handleMessage(MSG_INIT)
  09-15 09:31:14.231 D/PowerController.Const(  743): POWERGURU_INACTIVE_TIMEOUT: 1200000 POWERGURU_INACTIVE_TIMEOUT_LOWPOWER: 300000 WAKELOCK_INACTIVE_TIMEOUT: 1200000 WAKELOCK_INACTIVE_TIMEOUT_LOWPOWER: 300000 WAKELOCK_CONSTRAINT_DURATION: 30000 WAKELOCK_CONSTRAINT_DURATION_LOWPOWER: 5000 APPIDLE_INACTIVE_TIMEOUT: 1200000 APPIDLE_INACTIVE_TIMEOUT_LOWPOWER: 300000 APPIDLE_PAROLE_TIMEOUT: 240000 APPIDLE_PAROLE_TIMEOUT_LOWPOWER: 180000 APPIDLE_IDLE_TIMEOUT: 3600000 APPIDLE_IDLE_TIMEOUT_LOWPOWER: 7200000 BG_APPIDLE_THRESHOLD1: 3600000 BG_APPIDLE_THRESHOLD2: 7200000 BG_APPIDLE_THRESHOLD3: 14400000 BG_MAX_LAUNCHED_APP_KEEP: 3 BG_MAX_LAUNCHED_APP_KEEP_LOWPOWER: 2 GPS_INACTIVE_TIMEOUT: 1800000 GPS_INACTIVE_TIMEOUT_LOWPOWER: 300000
  09-15 09:31:14.231 D/PowerController.Const(  743): mLaunchWhitelist: 0
  09-15 09:31:14.231 D/PowerController.Const(  743): mLaunchBlacklist: 0
  09-15 09:31:14.232 I/sysui_multi_action(  743): [757,856,758,1,806,android,857,POWER,858,2]
  09-15 09:31:14.235 D/PowerController(  743): Begin create helpers 
  09-15 09:31:14.236 D/Zygote  (  391): Forked child process 980
  09-15 09:31:14.237 D/PowerController.Guru(  743): POWERGURU_TIMEOUT:1200000
  09-15 09:31:14.238 D/PowerController.AppIdle(  743): APPSTANDBY_TIMEOUT:1200000 APPSTANDBY_TIMEOUT2:240000 APPSTANDBY_PAROLE_TIMEOUT:3600000
  09-15 09:31:14.239 W/ActivityManager(  743): Slow operation: 161ms so far, now at startProcess: returned from zygote!
  09-15 09:31:14.240 W/ActivityManager(  743): Slow operation: 161ms so far, now at startProcess: done updating battery stats
  09-15 09:31:14.240 I/am_proc_start(  743): [0,980,1037,WebViewLoader-arm64-v8a,NULL,]
  09-15 09:31:14.240 W/ActivityManager(  743): Slow operation: 162ms so far, now at startProcess: building log message
  09-15 09:31:14.240 I/ActivityManager(  743): Start proc 980:WebViewLoader-arm64-v8a/1037 [android.webkit.WebViewLibraryLoader$RelroFileCreator] for null
  09-15 09:31:14.240 W/ActivityManager(  743): Slow operation: 162ms so far, now at startProcess: starting to update pids map
  09-15 09:31:14.240 W/ActivityManager(  743): Slow operation: 162ms so far, now at startProcess: done updating pids map
  09-15 09:31:14.241 D/SSense.SRecogCollector(  743): addRecognizer: Type 2
  09-15 09:31:14.241 D/PowerController.Wakelock(  743): WAKELOCK_CONSTRAIN_IDLE_THRESHOLD:1200000 WAKE_LOCK_DISABLE_THRESHOLD:30000
  09-15 09:31:14.242 D/SSense.SRecogCollector(  743): addRecognizer: Type 4
  09-15 09:31:14.243 D/SSense.SRecogCollector(  743): addRecognizer: Type 8
  09-15 09:31:14.243 D/SSense.SRecogCollector(  743): addRecognizer: Type 16
  09-15 09:31:14.243 D/SSense.SRecogCollector(  743): addRecognizer: Type 32
  09-15 09:31:14.244 D/SSense.SRecogCollector(  743): getStatusBarAndNavBarState: mStatusBarHeight:72 mNavBarHeight:144 mHasNavBar:false
  09-15 09:31:14.245 I/commit_sys_config_file(  743): [notification-policy,12]
  09-15 09:31:14.247 D/SSense.AppInfoUtil(  743): - loadInstalledPackages() for user: 0
  09-15 09:31:14.247 E/SSense.ConfigReader(  743): >>>file not found,java.io.FileNotFoundException: /system/etc/sprdssense_config.xml: open failed: ENOENT (No such file or directory)
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.google.android.ext.services Flag:3088be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:android Flag:30c8be09
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.launcher3 Flag:24cbbe45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.google.android.permissioncontroller Flag:30c83e05
  09-15 09:31:14.248 D/SSense.ConfigReader(  743): mVideoAppList: 0
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.providers.settings Flag:308abe05
  09-15 09:31:14.248 D/SSense.ConfigReader(  743): mGameAppList: 0
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.webview Flag:b088be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:android.ext.shared Flag:20883e45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.spreadtrum.ims Flag:20883e45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.packageinstaller Flag:30c83e45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.settings Flag:28c9be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.networkstack.permissionconfig Flag:3088be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.phone Flag:28c83e4d
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.shell Flag:2088be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.systemui Flag:30c83e0d
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:android.auto_generated_rro_product__ Flag:888be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:com.android.captiveportallogin Flag:38c8be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): PKG:android.auto_generated_rro_vendor__ Flag:888be45
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): mInstalledAppList: 0
  09-15 09:31:14.248 D/SSense.AppInfoUtil(  743): mInstalledAdminAppList: 0
  09-15 09:31:14.249 D/SSense.AppStateHMMPredict(  743): forceAppIdleEnabled:true
  09-15 09:31:14.249 D/SSense.AppStateHMMPredict(  743): enableApplyStandbyBucket:true
  09-15 09:31:14.249 D/PowerController.SysPrefConfig(  743): enabledServicesSetting:null
  09-15 09:31:14.249 D/SSense.StateTracker(  743): register Audio scene callback!
  09-15 09:31:14.250 E/PowerController.SysPrefConfig(  743): >>>file not found,java.io.FileNotFoundException: /data/system/SystemPreferredConfig.xml: open failed: ENOENT (No such file or directory)
  09-15 09:31:14.251 D/PowerController.BgClean(  743): FORCE_STOP_IDLE_THRESHOLD1:3600000 FORCE_STOP_IDLE_THRESHOLD2:7200000 FORCE_STOP_IDLE_THRESHOLD3:14400000 MAX_LAUNCHED_APP_KEEP:3 DOCLEAN_TIMEOUT: 60000
  09-15 09:31:14.251 D/SSense  (  743): registerWindowChangeListener
  09-15 09:31:14.251 D/DeviceIdleControllerEx(  743): Reading String list config from /system/etc/deviceidle.xml mPresetWhiteListLoaded:true
  09-15 09:31:14.252 D/PowerController.Gps(  743): GPS_CONSTRAINT_IDLE_THRESHOLD:1800000
  09-15 09:31:14.253 E/PowerController.Config(  743): >>>file not found,java.io.FileNotFoundException: /data/system/appPowerSaveConfig.xml: open failed: ENOENT (No such file or directory)
  09-15 09:31:14.253 E/PowerController.Config(  743): OTA upgrade state: false
  09-15 09:31:14.254 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.power@4.0::IPower/default in either framework or device manifest.
  09-15 09:31:14.255 E/PowerHALManager(  743): Get Power HIDL HAL service failed!!!
  09-15 09:31:14.255 W/System.err(  743): java.util.NoSuchElementException
  09-15 09:31:14.255 W/System.err(  743): 	at android.os.HwBinder.getService(Native Method)
  09-15 09:31:14.255 W/System.err(  743): 	at android.os.HwBinder.getService(HwBinder.java:83)
  09-15 09:31:14.255 W/System.err(  743): 	at vendor.sprd.hardware.power.V4_0.IPower.getService(IPower.java:70)
  09-15 09:31:14.255 W/System.err(  743): 	at vendor.sprd.hardware.power.V4_0.IPower.getService(IPower.java:77)
  09-15 09:31:14.255 W/System.err(  743): 	at android.os.PowerHALManager.<init>(PowerHALManager.java:52)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.power.sprdpower.HandlerForMemoryGts.<init>(HandlerForMemoryGts.java:56)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerHintCallback.<init>(PowerHintCallback.java:32)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.power.sprdpower.SmartSenseService.systemReady(SmartSenseService.java:264)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerController.systemReady(PowerController.java:650)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2342)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.256 W/System.err(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.256 W/System.err(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.256 E/PowerHALManager(  743): Power HAL service isn't working
  09-15 09:31:14.256 E/PowerHALManager(  743): linkToDeath() failed
  09-15 09:31:14.257 W/System.err(  743): java.lang.NullPointerException: Attempt to invoke interface method 'boolean vendor.sprd.hardware.power.V4_0.IPower.linkToDeath(android.os.IHwBinder$DeathRecipient, long)' on a null object reference
  09-15 09:31:14.257 W/System.err(  743): 	at android.os.PowerHALManager.createPowerHintScene(PowerHALManager.java:66)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.power.sprdpower.HandlerForMemoryGts.<init>(HandlerForMemoryGts.java:57)
  09-15 09:31:14.257 D/PowerController(  743): initPowerSaveHelpers() E
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerHintCallback.<init>(PowerHintCallback.java:32)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.power.sprdpower.SmartSenseService.systemReady(SmartSenseService.java:264)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerController.systemReady(PowerController.java:650)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2342)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.257 W/System.err(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.257 W/System.err(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.259 D/PowerController(  743): dump appconfig [AppPowerSaveConfig]
  09-15 09:31:14.259 D/PowerController(  743): com.sprd.sleepwakeuptest --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_NO_OPTIMIZE(2), secondaryLaunch: VALUE_NO_OPTIMIZE(2), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): sprdtest.message --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_NO_OPTIMIZE(2), secondaryLaunch: VALUE_NO_OPTIMIZE(2), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): com.spreadtrum.itestapp --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_NO_OPTIMIZE(2), secondaryLaunch: VALUE_NO_OPTIMIZE(2), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): com.sprd.bmte.coulomb --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_AUTO(0), secondaryLaunch: VALUE_AUTO(0), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): com.comcat.activity --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_NO_OPTIMIZE(2), secondaryLaunch: VALUE_NO_OPTIMIZE(2), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): com.greenpoint.android.mc10086.activity --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_NO_OPTIMIZE(2), secondaryLaunch: VALUE_NO_OPTIMIZE(2), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): com.jio.emiddleware --- PowerController.Config{ optimize: 1, alarm: VALUE_AUTO(0), wakelock: VALUE_AUTO(0), network: VALUE_AUTO(0), autoLaunch: VALUE_NO_OPTIMIZE(2), secondaryLaunch: VALUE_NO_OPTIMIZE(2), lockscreenCleanup: VALUE_NO_OPTIMIZE(2) }
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: com.sprd.sleepwakeuptest, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.259 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: sprdtest.message, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: com.spreadtrum.itestapp, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: com.sprd.bmte.coulomb, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.260 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.260 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: com.comcat.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: com.greenpoint.android.mc10086.activity, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_OPTIMIZE, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_OPTIMIZE(1)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController.Guru(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_ALARM, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_WAKELOCK, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_NETWORK, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_AUTOLAUNCH, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_SECONDARYLAUNCH, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_LOCKSCREENCLEANUP, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_NO_OPTIMIZE(2)
  09-15 09:31:14.261 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_POWERCONSUMERTYPE, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.262 D/PowerController(  743): onPowerSaveConfigChanged(), init: true, configType: TYPE_EXEMPTSOURCE, appName: com.jio.emiddleware, oldValue: VALUE_AUTO(0), newValue: VALUE_AUTO(0)
  09-15 09:31:14.262 D/PowerController(  743): PowerController.Guru
  09-15 09:31:14.262 D/PowerController(  743): [mWhiteList]: []
  09-15 09:31:14.262 D/PowerController(  743): [mBlackList]: []
  09-15 09:31:14.262 D/PowerController(  743): PowerController.AppIdle
  09-15 09:31:14.262 D/PowerController(  743): [mWhiteList]: []
  09-15 09:31:14.262 D/PowerController(  743): [mBlackList]: []
  09-15 09:31:14.262 D/PowerController(  743): PowerSaveHelper
  09-15 09:31:14.262 V/PowerDataBaseControl(  743): OTA upgrade status is false
  09-15 09:31:14.263 I/am_proc_bound(  743): [0,940,com.android.systemui]
  09-15 09:31:14.263 D/PowerDataBaseControl(  743): Output data base:/data/system/power_info.db
  09-15 09:31:14.263 E/PowerHALManager(  743): Power HAL service isn't working
  09-15 09:31:14.263 E/PowerHALManager(  743): linkToDeath() failed
  09-15 09:31:14.263 W/System.err(  743): java.lang.NullPointerException: Attempt to invoke interface method 'boolean vendor.sprd.hardware.power.V4_0.IPower.linkToDeath(android.os.IHwBinder$DeathRecipient, long)' on a null object reference
  09-15 09:31:14.263 W/System.err(  743): 	at android.os.PowerHALManager.createPowerHintScene(PowerHALManager.java:66)
  09-15 09:31:14.263 W/System.err(  743): 	at com.android.server.power.sprdpower.HandlerForMemoryGts.<init>(HandlerForMemoryGts.java:59)
  09-15 09:31:14.263 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerHintCallback.<init>(PowerHintCallback.java:32)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.power.sprdpower.SmartSenseService.systemReady(SmartSenseService.java:264)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerController.systemReady(PowerController.java:650)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2342)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.264 W/System.err(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.264 E/PowerHALManager(  743): Power HAL service isn't working
  09-15 09:31:14.264 E/PowerHALManager(  743): linkToDeath() failed
  09-15 09:31:14.264 W/System.err(  743): java.lang.NullPointerException: Attempt to invoke interface method 'boolean vendor.sprd.hardware.power.V4_0.IPower.linkToDeath(android.os.IHwBinder$DeathRecipient, long)' on a null object reference
  09-15 09:31:14.264 W/System.err(  743): 	at android.os.PowerHALManager.createPowerHintScene(PowerHALManager.java:66)
  09-15 09:31:14.264 W/System.err(  743): 	at com.android.server.power.sprdpower.HandlerForMemoryGts.<init>(HandlerForMemoryGts.java:61)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerHintCallback.<init>(PowerHintCallback.java:32)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.power.sprdpower.SmartSenseService.systemReady(SmartSenseService.java:264)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerController.systemReady(PowerController.java:650)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2342)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.265 W/System.err(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.265 W/System.err(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.266 I/am_uid_active(  743): 10008
  09-15 09:31:14.266 I/hwservicemanager(  306): getTransport: Cannot find entry vendor.sprd.hardware.power@4.0::IPower/default in either framework or device manifest.
  09-15 09:31:14.267 I/am_create_service(  743): [0,168502706,.SystemUIService,10008,940]
  09-15 09:31:14.267 E/PowerHintCallback(  743): Get Power HIDL HAL service failed!!!
  09-15 09:31:14.267 W/System.err(  743): java.util.NoSuchElementException
  09-15 09:31:14.267 W/System.err(  743): 	at android.os.HwBinder.getService(Native Method)
  09-15 09:31:14.267 W/System.err(  743): 	at android.os.HwBinder.getService(HwBinder.java:83)
  09-15 09:31:14.267 W/System.err(  743): 	at vendor.sprd.hardware.power.V4_0.IPower.getService(IPower.java:70)
  09-15 09:31:14.267 W/System.err(  743): 	at vendor.sprd.hardware.power.V4_0.IPower.getService(IPower.java:77)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerHintCallback.<init>(PowerHintCallback.java:35)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.power.sprdpower.SmartSenseService.systemReady(SmartSenseService.java:264)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.power.sprdpower.PowerController.systemReady(PowerController.java:650)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.SystemServer.lambda$startOtherServices$4$SystemServer(SystemServer.java:2342)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.-$$Lambda$SystemServer$YHlTFstuCrnYJae0u-RcVnGRga0.run(Unknown Source:53)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.am.ActivityManagerService.systemReady(ActivityManagerService.java:9142)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.am.ActivityManagerServiceEx.systemReady(ActivityManagerServiceEx.java:142)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.SystemServer.startOtherServices(SystemServer.java:2117)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.SystemServer.run(SystemServer.java:526)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.server.SystemServer.main(SystemServer.java:363)
  09-15 09:31:14.267 W/System.err(  743): 	at java.lang.reflect.Method.invoke(Native Method)
  09-15 09:31:14.267 W/System.err(  743): 	at com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run(RuntimeInit.java:503)
  09-15 09:31:14.268 W/System.err(  743): 	at com.android.internal.os.ZygoteInit.main(ZygoteInit.java:911)
  09-15 09:31:14.262 I/chatty  (  743): uid=1000(system) PowerController identical 1 line
  09-15 09:31:14.262 D/PowerController(  743): PowerSaveHelper
  09-15 09:31:14.268 I/SystemServer(  743): isCCSASupport = false
  09-15 09:31:14.268 V/PowerDataBaseControl(  743): copyDataBase = true
  09-15 09:31:14.268 I/ActivityManager(  743): Current user:0
  09-15 09:31:14.268 I/SystemServiceManager(  743): Calling onStartUser u0
  09-15 09:31:14.269 I/am_create_service(  743): [0,266248799,.KeyguardService,10008,940]
  09-15 09:31:14.269 D/ColorDisplayService(  743): setUp: currentUser=0
  09-15 09:31:14.271 I/am_create_service(  743): [0,116721019,.ImageWallpaper,10008,940]
  09-15 09:31:14.272 W/asset   (  918): unable to execute idmap2: Permission denied
  09-15 09:31:14.272 W/AssetManager(  918): 'idmap2 --scan' failed: no static="true" overlays targeting "android" will be loaded
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.tencent.mm type=3
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.tencent.mobileqq type=3
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=jp.naver.line.android type=3
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.android.music type=2
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.baidu.video type=6
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.android.fmradio type=2
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.sohu.newsclient type=5
  09-15 09:31:14.274 D/PowerDataBaseControl(  743): apk=com.taobao.taobao type=12
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.sina.weibo type=3
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.facebook.katana type=3
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.ximalaya.ting.android type=2
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.qiyi.video type=6
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.imangi.templerun2 type=1
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.tencent.mtt type=8
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.kugou.android type=2
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.UCMobile type=8
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.whatsapp type=3
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.codoon.gps type=13
  09-15 09:31:14.275 D/PowerController(  743): updateUidStateLocked: packageName:android.uid.systemui:10008, uid:10008 state change from PROCESS_STATE_CACHED_EMPTY to PROCESS_STATE_PERSISTENT
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.mobike.mobikeapp type=16
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.baidu.browser.apps type=8
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.tencent.qqlive type=6
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.tencent.qqmusic type=2
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.baidu.appsearch type=17
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.netease.onmyoji.baidu type=1
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.netease.onmyoji type=1
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=cmccwm.mobilemusic type=2
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.shuqi.controller type=7
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.baidu.searchbox type=17
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.qihoo.browser type=8
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.ting.mp3.android type=2
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.tencent.launcher type=17
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=cn.ledongli.ldl type=13
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.racergame.cityracing3d.baidu type=1
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.racergame.cityracing3d type=1
  09-15 09:31:14.275 D/PowerDataBaseControl(  743): apk=com.eg.android.AlipayGphone type=10
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=so.ofo.labofo type=16
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.tencent.tmgp.sgame type=1
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.youku.phone type=6
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.MobileTicket type=15
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.sdu.didi.psnger type=16
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.letv.android.client type=6
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.happyelements.AndroidAnimal type=1
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.ss.android.article.news type=5
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.thestore.main type=12
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.sohu.sohuvideo type=6
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.Qunar type=15
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=cn.damai type=14
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.jingdong.app.mall type=12
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.autonavi.minimap type=9
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=ctrip.android.view type=15
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.moji.mjweather type=14
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.cmbchina.ccd.pluto.cmbActivity type=10
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.achievo.vipshop type=12
  09-15 09:31:14.276 D/PowerDataBaseControl(  743): apk=com.skype.raider type=3
  09-15 09:31:14.277 D/PowerDataBaseControl(  743): apk=com.skype.m2 type=3
  09-15 09:31:14.277 D/PowerDataBaseControl(  743): apk=com.bbm type=3
  09-15 09:31:14.277 D/ColorDisplayService(  743): setup mNightValue = 1
  09-15 09:31:14.277 D/PowerDataBaseControl(  743): apk=com.twitter.android type=3
  09-15 09:31:14.275 D/SSense.StateTracker(  743): new AppUsageState for com.android.systemui
  09-15 09:31:14.278 W/TelecomManager(  743): Telecom Service not found.
  09-15 09:31:14.278 I/RoleManagerService(  743): Granting default permissions...
  09-15 09:31:14.277 D/PowerDataBaseControl(  743): apk=com.instagram.android type=3
  09-15 09:31:14.279 D/PowerDataBaseControl(  743): apk=com.facebook.orca type=3
  09-15 09:31:14.279 D/PowerDataBaseControl(  743): apk=com.viber.voip type=3
  09-15 09:31:14.279 D/PowerDataBaseControl(  743): apk=com.imo.android.imoim type=3
  09-15 09:31:14.279 D/PowerDataBaseControl(  743): apk=org.telegram.messenger type=3
  09-15 09:31:14.279 D/PowerDataBaseControl(  743): apk=com.google.android.talk type=3
  09-15 09:31:14.279 D/PowerDataBaseControl(  743): apk=com.facebook.mlite type=3
  09-15 09:31:14.280 D/PowerDataBaseControl(  743): apk=com.ss.android.ugc.aweme​ type=6
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.android.fmradio type:2
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.skype.raider type:3
  09-15 09:31:14.280 D/PowerController(  743): pkgName:so.ofo.labofo type:16
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.netease.onmyoji.baidu type:1
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.racergame.cityracing3d type:1
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.facebook.mlite type:3
  09-15 09:31:14.280 D/PowerController(  743): pkgName:org.telegram.messenger type:3
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.tencent.tmgp.sgame type:1
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.qiyi.video type:6
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.imangi.templerun2 type:1
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.youku.phone type:6
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.viber.voip type:3
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.tencent.qqmusic type:2
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.whatsapp type:3
  09-15 09:31:14.280 D/PowerController(  743): pkgName:jp.naver.line.android type:3
  09-15 09:31:14.280 D/PowerController(  743): pkgName:com.qihoo.browser type:8
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.ting.mp3.android type:2
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.MobileTicket type:15
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.tencent.mm type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.sdu.didi.psnger type:16
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.skype.m2 type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.baidu.searchbox type:17
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.codoon.gps type:13
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.instagram.android type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.letv.android.client type:6
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.tencent.launcher type:17
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.happyelements.AndroidAnimal type:1
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.tencent.qqlive type:6
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.baidu.appsearch type:17
  09-15 09:31:14.281 D/PowerController(  743): pkgName:cmccwm.mobilemusic type:2
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.tencent.mtt type:8
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.baidu.browser.apps type:8
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.thestore.main type:12
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.twitter.android type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:cn.ledongli.ldl type:13
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.ss.android.article.news type:5
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.UCMobile type:8
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.sohu.sohuvideo type:6
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.baidu.video type:6
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.tencent.mobileqq type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.kugou.android type:2
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.racergame.cityracing3d.baidu type:1
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.ximalaya.ting.android type:2
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.facebook.katana type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.facebook.orca type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.bbm type:3
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.Qunar type:15
  09-15 09:31:14.281 D/PowerController(  743): pkgName:cn.damai type:14
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.mobike.mobikeapp type:16
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.ss.android.ugc.aweme​ type:6
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.jingdong.app.mall type:12
  09-15 09:31:14.281 D/PowerController(  743): pkgName:com.autonavi.minimap type:9
  09-15 09:31:14.281 D/PowerController(  743): pkgName:ctrip.android.view type:15
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.sohu.newsclient type:5
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.shuqi.controller type:7
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.moji.mjweather type:14
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.google.android.talk type:3
  09-15 09:31:14.282 I/am_uid_running(  743): 10003
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.sina.weibo type:3
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.android.music type:2
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.imo.android.imoim type:3
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.taobao.taobao type:12
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.cmbchina.ccd.pluto.cmbActivity type:10
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.eg.android.AlipayGphone type:10
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.netease.onmyoji type:1
  09-15 09:31:14.282 D/PowerController(  743): pkgName:com.achievo.vipshop type:12
  09-15 09:31:14.282 D/PowerController.BgClean(  743): - loadInstalledPackages() for user: 0
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.google.android.ext.services Flag:3088be45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:android Flag:30c8be09
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.launcher3 Flag:24cbbe45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.google.android.permissioncontroller Flag:30c83e05
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.providers.settings Flag:308abe05
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.webview Flag:b088be45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:android.ext.shared Flag:20883e45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.spreadtrum.ims Flag:20883e45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.packageinstaller Flag:30c83e45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.settings Flag:28c9be45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.networkstack.permissionconfig Flag:3088be45
  09-15 09:31:14.283 D/PowerController.BgClean(  743): PKG:com.android.phone Flag:28c83e4d
  09-15 09:31:14.284 D/PowerController.BgClean(  743): PKG:com.android.shell Flag:2088be45
  09-15 09:31:14.284 D/PowerController.BgClean(  743): PKG:com.android.systemui Flag:30c83e0d
  09-15 09:31:14.284 D/PowerController.BgClean(  743): PKG:android.auto_generated_rro_product__ Flag:888be45
  09-15 09:31:14.284 D/PowerController.BgClean(  743): PKG:com.android.captiveportallogin Flag:38c8be45
  09-15 09:31:14.284 D/PowerController.BgClean(  743): PKG:android.auto_generated_rro_vendor__ Flag:888be45
  09-15 09:31:14.284 D/PowerController.BgClean(  743): mInstalledAppList: 0
  09-15 09:31:14.284 D/PowerController.BgClean(  743): mInstalledAdminAppList: 0
  09-15 09:31:14.284 D/PowerController.AppIdle(  743): APPSTANDBY_PAROLE_TIMEOUT:3600000 APPSTANDBY_TIMEOUT2:240000
  09-15 09:31:14.284 D/PowerController(  743): whitelistExceptIdle: 1
  09-15 09:31:14.284 D/PowerController(  743): app: com.android.shell
  09-15 09:31:14.284 D/PowerController(  743): mPowerSaveWhitelistExceptIdleAppList: 1
  09-15 09:31:14.284 D/PowerController(  743): App:com.android.shell
  09-15 09:31:14.284 D/PowerController(  743): mAppIdPowerSaveWhitelistExceptIdleAppList=[2000]
  09-15 09:31:14.285 E/PowerController(  743): >>>file not found,java.io.FileNotFoundException: /data/system/powercontroller.xml: open failed: ENOENT (No such file or directory)
  09-15 09:31:14.286 D/PowerController(  743): powercontroller.xml in/data/system doesn,t exist!!
  09-15 09:31:14.288 D/PowerController(  743): add com.android.dialer to internal applist of ultramode
  09-15 09:31:14.288 D/PowerController(  743): add com.android.messaging to internal applist of ultramode
  09-15 09:31:14.288 D/PowerController(  743): add com.android.contacts to internal applist of ultramode
  09-15 09:31:14.289 D/PowerController(  743): updateBatteryLevelLow() E, force: true, battLevel: 78
  09-15 09:31:14.289 D/PowerController(  743): mBatteryLevelLow: false
  09-15 09:31:14.289 D/PowerController(  743): updateBatteryLevelLow() X, mBatteryLevelLow: false
  09-15 09:31:14.289 D/PowerController(  743): initData(), mPowerSaveMode: -1 mPrePowerSaveMode:1
  09-15 09:31:14.289 D/PowerController(  743): updatePowerSaveMode(), wasPowered: true, mBatteryLevelLow: false
  09-15 09:31:14.289 D/PowerController(  743): updatePowerSaveMode(), set to MODECONFIG_USER, Power Save Mode: 1
  09-15 09:31:14.290 D/PowerController(  743): updatePowerSaveModeInternal(1), pre-mode: -1
  09-15 09:31:14.290 D/PowerController.BgClean(  743): updateLauncherAppEnabledSettings Exception:java.lang.IllegalArgumentException: Unknown package: com.sprd.powersavemodelauncher
  09-15 09:31:14.290 D/PowerController.BgClean(  743): updateLauncherAppEnabledSettings disable powersavemodelauncher
  09-15 09:31:14.290 D/PackageManager(  743): setEnabledSetting: packageName = com.sprd.powersavemodelauncher, className = null, newState = 2 ,flags = 0 ,userId = 0 ,callingPackage = android , callingUid = 1000 , allowedByPermission = true
  09-15 09:31:14.291 D/PowerController.BgClean(  743): updateLauncherAppEnabledSettings Exception:java.lang.IllegalArgumentException: Unknown package: com.sprd.powersavemodelauncher
  09-15 09:31:14.291 D/PowerController.BgClean(  743): updateLauncherAppEnabledSettings: NOT launcher app is enabled.ENABLE default!
  09-15 09:31:14.291 D/PackageManager(  743): setEnabledSetting: packageName = com.android.launcher3, className = com.android.launcher3.Launcher, newState = 0 ,flags = 0 ,userId = 0 ,callingPackage = null , callingUid = 1000 , allowedByPermission = true
  09-15 09:31:14.291 D/PowerController.BgClean(  743): updateLauncherAppEnabledSettings: enable ComponentInfo{com.android.launcher3/com.android.launcher3.Launcher} state:0 newMode:1
  09-15 09:31:14.291 D/PackageManager(  743): setEnabledSetting: packageName = com.android.launcher3, className = com.android.searchlauncher.SearchLauncher, newState = 0 ,flags = 0 ,userId = 0 ,callingPackage = null , callingUid = 1000 , allowedByPermission = true
  09-15 09:31:14.292 D/PowerController.BgClean(  743): updateLauncherAppEnabledSettings Exception:java.lang.IllegalArgumentException: Component class com.android.searchlauncher.SearchLauncher does not exist in com.android.launcher3
  09-15 09:31:14.292 D/PowerController(  743): oldDisabledLanucherAppList_UltraSave:null, new mDisabledLanucherAppList_UltraSave:null
  09-15 09:31:14.292 E/BatterySaverStateMachine(  743): Tried to disable BS when it's already OFF
  09-15 09:31:14.292 D/PowerController(  743): enterPowerSaveMode(), 1
  09-15 09:31:14.292 D/BatteryStatsService(  743): onPowerModeChanged(1)
  09-15 09:31:14.292 D/PowerController.BattStats(  743): updatePowerMode: new mode:1, now:21235
  09-15 09:31:14.292 D/PowerController(  743): postModeChangeBroadcast(), newMode:1, oldMode:-1
  09-15 09:31:14.293 W/ContextImpl(  743): Calling a method in the system process without a qualified user: android.app.ContextImpl.sendBroadcast:1045 com.android.server.power.sprdpower.PowerController.postModeChangeBroadcast:3972 com.android.server.power.sprdpower.PowerController.enterPowerSaveMode:3956 com.android.server.power.sprdpower.PowerController.handlePowerSaveModeChanged:4160 com.android.server.power.sprdpower.PowerController.updatePowerSaveModeInternal:3421 
  09-15 09:31:14.294 D/BroadcastQueue(  743): Add broadcast <BroadcastRecord{41429f8 u0 android.os.action.POWEREX_SAVE_MODE_CHANGED}> into [parallel | foreground], pending size 0
  09-15 09:31:14.294 D/BroadcastQueue(  743): Done with parallel broadcast [foreground] [BroadcastRecord{41429f8 u0 android.os.action.POWEREX_SAVE_MODE_CHANGED}]
  09-15 09:31:14.294 D/PowerController.Guru(  743): Current PowerSaveMode:1
  09-15 09:31:14.294 D/PowerController.AppIdle(  743): Current PowerSaveMode:1
  09-15 09:31:14.294 D/PowerController.Wakelock(  743): Current PowerSaveMode:1
  09-15 09:31:14.294 D/PowerController.BgClean(  743): Current PowerSaveMode:1
  09-15 09:31:14.294 D/PowerController.Gps(  743): Current PowerSaveMode:1
  09-15 09:31:14.300 D/PowerController(  743): writeConfig: mPrePowerSaveMode: -1
  09-15 09:31:14.308 D/PowerController(  743): initData() 2, mPowerSaveMode: 1 mPrePowerSaveMode:-1
  09-15 09:31:14.308 D/PowerController(  743): handleMessage(MSG_CHECK)
  09-15 09:31:14.308 I/commit_sys_config_file(  743): [settings-0-0,7]
  09-15 09:31:14.308 D/PowerController(  743): - checkAllAppStateInfo() E -
  09-15 09:31:14.309 D/PowerController(  743): mCharging:true mScreenOn:true mMobileConnected:false
  09-15 09:31:14.309 V/AlarmManager(  743): set(PendingIntent{85deda4: PendingIntentRecord{f3e570d android broadcastIntent}}) : type=3 listener=null listenerTag=null triggerAtTime=321251 win=225000 tElapsed=321251 maxElapsed=546251 interval=0 flags=0x8
  09-15 09:31:14.309 D/AlarmManagerService(  743): set alarm to kernel: 66.943000000, type=3 
  09-15 09:31:14.310 D/PowerController(  743): - checkBackgroundApp() for user: 0
  09-15 09:31:14.310 D/PowerController(  743): handleMessage(MSG_APP_STATE_CHANGED)
  09-15 09:31:14.310 D/PowerController(  743): - handleAppStateChanged() E -
  09-15 09:31:14.310 D/PowerController.AppState(  743): - reportAppStateEventInfo() E -
  09-15 09:31:14.312 D/PowerController(  743): packageName:com.android.systemui state:SYSTEM_INTERACTION user:0
  09-15 09:31:14.312 D/PowerController(  743): handleMessage(MSG_UID_STATE_CHANGED)
  09-15 09:31:14.312 D/PowerController(  743): - handleProcstateChanged() E - packageName:android.uid.systemui:10008 uid:10008 procState:PROCESS_STATE_PERSISTENT
  09-15 09:31:14.312 D/PowerController.AppState(  743): - reportAppProcStateInfo() E -
  09-15 09:31:14.312 D/PowerController.RecogA(  743): handleMessage(MSG_REPORT_EVENT)
  09-15 09:31:14.313 D/PowerController.AppState(  743): reportAppProcStateInfo: appName:android.uid.systemui:10008 uid:10008 is not exist, create it
  09-15 09:31:14.313 D/PowerController.RecogA(  743): handleMessage(MSG_REPORT_EVENT)
  09-15 09:31:14.315 D/Zygote  (  391): Forked child process 1004
  09-15 09:31:14.321 I/am_proc_start(  743): [0,1004,10003,com.google.android.permissioncontroller,service,{com.google.android.permissioncontroller/com.android.packageinstaller.role.service.RoleControllerServiceImpl}]
  09-15 09:31:14.321 I/ActivityManager(  743): Start proc 1004:com.google.android.permissioncontroller/u0a3 for service {com.google.android.permissioncontroller/com.android.packageinstaller.role.service.RoleControllerServiceImpl}
  09-15 09:31:14.321 I/ndroid.systemu(  940): The ClassLoaderContext is a special shared library.
  09-15 09:31:14.322 D/SceneRecognizer(  743): notifySceneStatusChanged: notify 1 receivers
  09-15 09:31:14.322 E/PowerHintCallback(  743): mServiceis null!!!
  09-15 09:31:14.323 D/AppSceneRecognizer(  743): ###handle app Event: Exit
  09-15 09:31:14.156 I/chatty  (  743): uid=1000 system_server identical 2 lines
  09-15 09:31:14.231 W/TelephonyManager(  743): telephony registry not ready.
  09-15 09:31:14.332 D/IccProviderExImpl(  918): IccProviderExImpl
  09-15 09:31:14.332 I/am_app_pub_providers(  918): 1
  09-15 09:31:14.367 W/asset   (  940): unable to execute idmap2: Permission denied
  09-15 09:31:14.367 W/AssetManager(  940): 'idmap2 --scan' failed: no static="true" overlays targeting "android" will be loaded
  09-15 09:31:14.372 D/TelephonyComponentFactory(  918): validated paths: null
  09-15 09:31:14.372 D/TelephonyComponentFactory(  918): Total components injected: 0
  09-15 09:31:14.377 D/TDC     (  918): updateOrInsert: inserting: Modem { uuid=modem, state=0, rilModel=0, rat={}, maxActiveVoiceCall=1, maxActiveDataCall=1, maxStandby=1 }
  09-15 09:31:14.377 D/TDC     (  918): updateOrInsert: inserting: Sim { uuid=sim, modemUuid=modem, state=0 }
  09-15 09:31:14.386 D/CdmaSSM (  918): subscriptionSource from settings: 0
  09-15 09:31:14.387 I/PhoneFactory(  918): Cdma Subscription set to 0
  09-15 09:31:14.388 D/TelephonyManager(  918): /proc/cmdline=earlycon=sprd_serial,0x70100000,115200n8 console=ttyS1,115200n8 loglevel=1 init=/init root=/dev/ram0 rw androidboot.hardware=s9863a1h10 androidboot.dtbo_idx=0 printk.devkmsg=on androidboot.boot_devices=soc/soc:ap-ahb/20600000.sdio lcd_id=ID35695 lcd_name=lcd_nt35695_truly_mipi_fhd lcd_base=fd580000 lcd_size=1920x1080 pixel_clock=153600000 logo_bpix=24 androidboot.ddrsize=2048M androidboot.ddrsize.range=[2048,)  sysdump_magic=85500000 modem=shutdown ltemode=lcsfb rfboard.id=0 rfhw.id=0 crystal=2 32k.less=1 modemboot.method=emmcboot  androidboot.verifiedbootstate=orange androidboot.flash.locked=0  androidboot.serialno=0123456789ABCDEF androidboot.vbmeta.device=PARTUUID=1.0 androidboot.vbmeta.avb_version=1.1 androidboot.vbmeta.device_state=unlocked androidboot.vbmeta.hash_alg=sha256 androidboot.vbmeta.size=38592 androidboot.vbmeta.digest=8851bbad25028c6719bc38ab68c2b070c2fdf1b2cde4644686d8b78f81c90f48 androidboot.vbmeta.invalidate_on_error=yes androidboot.veritymode=enforcing
  09-15 09:31:14.389 I/PhoneFactory(  918): Network Mode set to 9
  09-15 09:31:14.396 D/RILJ    (  918): RIL: init preferredNetworkType=9 cdmaSubscription=0) [SUBnull]
  09-15 09:31:14.404 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.4::IRadio/slot1 in either framework or device manifest.
  09-15 09:31:14.407 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.3::IRadio/slot1 in either framework or device manifest.
  09-15 09:31:14.413 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.2::IRadio/slot1 in either framework or device manifest.
  09-15 09:31:14.418 W/StorageManagerService(  743): No primary storage defined yet; hacking together a stub
  09-15 09:31:14.418 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.1::IRadio/slot1 in either framework or device manifest.
  09-15 09:31:14.422 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.0::IRadio/slot1 in either framework or device manifest.
  09-15 09:31:14.424 E/RILJ    (  918): getRadioProxy: mRadioProxy for slot1 is disabled [SUB0]
  09-15 09:31:14.424 E/RILJ    (  918): getRadioProxy: mRadioProxy == null [SUB0]
  09-15 09:31:14.424 E/RILJ    (  918): getRadioProxy: mRadioProxy for slot1 is disabled [SUB0]
  09-15 09:31:14.424 E/RILJ    (  918): getRadioProxy: mRadioProxy == null [SUB0]
  09-15 09:31:14.426 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio.deprecated@1.0::IOemHook/slot1 in either framework or device manifest.
  09-15 09:31:14.429 E/RILJ    (  918): IOemHook service is not on the device HAL: java.util.NoSuchElementException [SUB0]
  09-15 09:31:14.429 D/RILJ    (  918): Radio HAL version: -1.-1 [SUB0]
  09-15 09:31:14.429 I/PhoneFactory(  918): Network Mode set to 9
  09-15 09:31:14.429 D/RILJ    (  918): RIL: init preferredNetworkType=9 cdmaSubscription=0) [SUBnull]
  09-15 09:31:14.431 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.4::IRadio/slot2 in either framework or device manifest.
  09-15 09:31:14.431 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.3::IRadio/slot2 in either framework or device manifest.
  09-15 09:31:14.432 I/am_proc_bound(  743): [0,980,WebViewLoader-arm64-v8a]
  09-15 09:31:14.433 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.2::IRadio/slot2 in either framework or device manifest.
  09-15 09:31:14.434 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.1::IRadio/slot2 in either framework or device manifest.
  09-15 09:31:14.435 I/am_uid_active(  743): 1037
  09-15 09:31:14.436 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio@1.0::IRadio/slot2 in either framework or device manifest.
  09-15 09:31:14.437 D/PowerController(  743): handleMessage(MSG_APP_STATE_CHANGED)
  09-15 09:31:14.437 D/PowerController(  743): - handleAppStateChanged() E -
  09-15 09:31:14.437 D/PowerController.AppState(  743): - reportAppStateEventInfo() E -
  09-15 09:31:14.437 D/PowerController(  743): packageName:android state:SYSTEM_INTERACTION user:0
  09-15 09:31:14.437 E/RILJ    (  918): getRadioProxy: mRadioProxy for slot2 is disabled [SUB1]
  09-15 09:31:14.437 E/RILJ    (  918): getRadioProxy: mRadioProxy == null [SUB1]
  09-15 09:31:14.438 E/RILJ    (  918): getRadioProxy: mRadioProxy for slot2 is disabled [SUB1]
  09-15 09:31:14.438 E/RILJ    (  918): getRadioProxy: mRadioProxy == null [SUB1]
  09-15 09:31:14.438 D/PowerController.RecogA(  743): handleMessage(MSG_REPORT_EVENT)
  09-15 09:31:14.438 D/PowerController(  743): updateUidStateLocked: packageName:null, uid:1037 state change from PROCESS_STATE_CACHED_EMPTY to PROCESS_STATE_PERSISTENT
  09-15 09:31:14.438 I/hwservicemanager(  306): getTransport: Cannot find entry android.hardware.radio.deprecated@1.0::IOemHook/slot2 in either framework or device manifest.
  09-15 09:31:14.439 E/RILJ    (  918): IOemHook service is not on the device HAL: java.util.NoSuchElementException [SUB1]
  09-15 09:31:14.439 D/RILJ    (  918): Radio HAL version: -1.-1 [SUB1]
  09-15 09:31:14.439 D/SSense.StateTracker(  743): new AppUsageState for android
  09-15 09:31:14.441 D/UiccController(  918): Creating UiccController
  09-15 09:31:14.441 D/UiccController(  918): config_num_physical_slots = 1
  09-15 09:31:14.442 V/WebViewLibraryLoader(  980): RelroFileCreator (64bit = true), package: com.android.webview library: libwebviewchromium.so
  09-15 09:31:14.442 E/WebViewLibraryLoader(  980): can't create relro file; address space not reserved
  09-15 09:31:14.443 E/WebViewLibraryLoader(  980): failed to create relro file
  09-15 09:31:14.444 I/WebViewLoader-(  980): System.exit called, status: 0
  09-15 09:31:14.444 I/AndroidRuntime(  980): VM exiting with result code 0, cleanup skipped.
  09-15 09:31:14.471 D/ExtraIccRecords(  918): [ExtraIccRecords0] Create ExtendedIccRecords
  09-15 09:31:14.471 D/ExtraIccRecords(  918): [ExtraIccRecords1] Create ExtendedIccRecords
  09-15 09:31:14.474 I/PhoneFactory(  918): Creating SubscriptionController
  09-15 09:31:14.476 I/am_proc_bound(  743): [0,1004,com.google.android.permissioncontroller]
  09-15 09:31:14.479 D/ActivityManager(  743): Death received in com.android.server.am.ActivityManagerService$AppDeathRecipient@599d34b for thread android.os.BinderProxy@7e20128 , App:ProcessRecord{484de41 980:WebViewLoader-arm64-v8a/1037}, Pid:980
  09-15 09:31:14.480 I/am_uid_active(  743): 10003
  09-15 09:31:14.480 I/am_create_service(  743): [0,38853658,.RoleControllerServiceImpl,10003,1004]
  09-15 09:31:14.481 I/Zygote  (  391): Process 980 exited cleanly (0)
  09-15 09:31:14.482 D/PowerController(  743): handleMessage(MSG_APP_STATE_CHANGED)
  09-15 09:31:14.482 D/PowerController(  743): - handleAppStateChanged() E -
  09-15 09:31:14.482 D/PowerController.AppState(  743): - reportAppStateEventInfo() E -
  09-15 09:31:14.482 D/PowerController(  743): packageName:com.google.android.permissioncontroller state:SYSTEM_INTERACTION user:0
  09-15 09:31:14.483 D/PowerController.RecogA(  743): handleMessage(MSG_REPORT_EVENT)
  09-15 09:31:14.483 D/SSense.StateTracker(  743): new AppUsageState for com.google.android.permissioncontroller
  09-15 09:31:14.484 E/ActivityThread(  918): Failed to find provider info for telephony
  09-15 09:31:14.484 I/ActivityManager(  743): Process WebViewLoader-arm64-v8a (pid 980) has died: psvc PER 
  09-15 09:31:14.484 I/am_proc_died(  743): [0,980,WebViewLoader-arm64-v8a,-700,0]
  09-15 09:31:14.485 V/ActivityManager(  743): Clean up application record for ProcessRecord{484de41 980:WebViewLoader-arm64-v8a/1037} restarting=false allowRestart=true index=-1 replacingPid=false
  09-15 09:31:14.485 D/AndroidRuntime(  918): Shutting down VM
  09-15 09:31:14.485 I/libprocessgroup(  743): Successfully killed process cgroup uid 1037 pid 980 in 0ms
  09-15 09:31:14.493 D/HprofFactory(  918): Create HprofDebugEx
  09-15 09:31:14.497 I/am_low_memory(  743): 4
  09-15 09:31:14.500 I/am_crash(  743): [918,0,com.android.phone,684211789,java.lang.IllegalArgumentException,Unknown URI content://telephony/siminfo,ContentResolver.java,1989]
  09-15 09:31:14.501 D/PowerController(  743): updateUidStateLocked: packageName:com.google.android.permissioncontroller, uid:10003 state change from PROCESS_STATE_CACHED_EMPTY to PROCESS_STATE_BOUND_FOREGROUND_SERVICE
  09-15 09:31:14.501 D/PowerController(  743): updateUidStateLocked: packageName:null, uid:1037 state change from PROCESS_STATE_PERSISTENT to PROCESS_STATE_CACHED_EMPTY
  09-15 09:31:14.501 D/PowerController(  743): handleMessage(MSG_UID_STATE_CHANGED)
  09-15 09:31:14.501 D/PowerController(  743): - handleProcstateChanged() E - packageName:com.google.android.permissioncontroller uid:10003 procState:PROCESS_STATE_BOUND_FOREGROUND_SERVICE
  09-15 09:31:14.501 D/PowerController(  743): updateUidStateLocked: packageName:null, uid:1037 changed from non-cached to cached_empty, just return!
  09-15 09:31:14.501 D/PowerController.AppState(  743): - reportAppProcStateInfo() E -
  09-15 09:31:14.501 D/PowerController.RecogA(  743): handleMessage(MSG_REPORT_EVENT)
  09-15 09:31:14.505 I/DropBoxManagerService(  743): add tag=system_app_crash isTagEnabled=true flags=0x2
  09-15 09:31:14.505 V/RescueParty(  743): Disabled because of active USB connection
  
  09-15 09:31:14.509 I/boot_progress_enable_screen(  743): 21452
  
  ```

- boot_progress_enable_screen 到 sf_stop_bootanim 耗时5012ms，这段时间是整个过程中，耗时最长的，有极大优化空间。

  ```c
  09-15 09:31:14.509 I/boot_progress_enable_screen(  743): 21452
  09-15 09:31:14.510 D/WindowManager(  743): systemBooted: TIGO_CMAS_STATUS value = 0
  09-15 09:31:14.510 I/screen_toggled(  743): 1
  09-15 09:31:14.511 W/AlarmManager(  940): Unrecognized alarm listener com.android.systemui.keyguard.-$$Lambda$KeyguardSliceProvider$IhzByd8TsqFuOrSyuGurVskyPLo@ae4921f
  09-15 09:31:14.511 I/WindowManager(  743): Started waking up... (why=ON_BECAUSE_OF_UNKNOWN)
  09-15 09:31:14.511 I/WindowManager(  743): Finished waking up... (why=ON_BECAUSE_OF_UNKNOWN)
  09-15 09:31:14.511 I/WindowManager(  743): Screen turning on...
  09-15 09:31:14.511 W/KeyguardServiceDelegate(  743): onScreenTurningOn(): no keyguard service!
  09-15 09:31:14.512 I/sysui_multi_action(  743): [757,316,758,4,759,-1]
  09-15 09:31:14.512 I/ssioncontrolle( 1004): The ClassLoaderContext is a special shared library.
  09-15 09:31:14.513 I/Process (  918): Sending signal. PID: 918 SIG: 9
      ...
      ...
  09-15 09:31:19.400 D/PowerController.AppState(  743): - reportAppProcStateInfo() E -
  09-15 09:31:19.401 D/PowerController.RecogA(  743): handleMessage(MSG_REPORT_EVENT)
  09-15 09:31:19.427 D/Zygote  (  391): Forked child process 1448
  09-15 09:31:19.433 I/am_proc_start(  743): [0,1448,1001,com.android.phone,restart,com.android.phone]
  09-15 09:31:19.433 I/ActivityManager(  743): Start proc 1448:com.android.phone/1001 for restart com.android.phone
  09-15 09:31:19.433 D/SceneRecognizer(  743): notifySceneStatusChanged: notify 1 receivers
  09-15 09:31:19.433 E/PowerHintCallback(  743): mServiceis null!!!
  09-15 09:31:19.433 D/AppSceneRecognizer(  743): ###handle app Event: Exit
  09-15 09:31:19.512 W/WindowManager(  743): Keyguard drawn timeout. Setting mKeyguardDrawComplete
  09-15 09:31:19.518 I/WindowManager(  743): ******* TELLING SURFACE FLINGER WE ARE BOOTED!
  09-15 09:31:19.518 I/SurfaceFlinger(  437): Boot is finished (16869 ms)
  09-15 09:31:19.522 I/sf_stop_bootanim(  437): 26464
  
  ```

- sf_stop_bootanim 到 wm_boot_animation_done 耗时2ms，忽略

  ```c
  09-15 09:31:19.522 I/sf_stop_bootanim(  437): 26464
  09-15 09:31:19.524 D/        (  710): Gralloc UnRegister  w:1080, h:1920, f:0x1102, usage:0xb00, ui64Stamp:109 line = 2373
  09-15 09:31:19.524 D/        (  710): Gralloc UnRegister  w:1080, h:1920, f:0x1102, usage:0xb00, ui64Stamp:129 line = 2373
  09-15 09:31:19.524 I/wm_boot_animation_done(  743): 26467
  
  ```

  

## AndroidQ代码修正

- frameworks/base/core/java/com/android/internal/os/ZygoteInit.java
- system/core/init/init.cpp
- frameworks/base/services/java/com/android/server/SystemServer.java +979
  - 不可裁剪
    1. MakeLocationServiceReady 裁掉导致手机不断重启(在bootanimation和luncher界面来回切换)
    2. PhaseThirdPartyAppsCanStart 能启动到桌面，但是桌面黑屏
    3. MakePackageManagerServiceReady 能启动到桌面，但是安装app时导致安装失败
    4. MakePowerManagerServiceReady 裁掉导致手机luncher界面频繁黑屏
    5. MakeWindowManagerServiceReady 能启动到桌面，但是命令行无法运行antutu
    6. StartBootPhaseSystemServicesReady 无法启动到桌面
    7. StartMediaProjectionManager 桌面黑屏
    8. StartMediaSessionService 桌面黑屏
    9. StartJobScheduler 裁掉导致手机不断重启(在bootanimation和luncher界面来回切换)
    10. .StartAudioService 无法启动到桌面
    11.  StartNotificationManager 无法启动到桌面
    12.  StartConnectivityService 无法启动到桌面
    13.  StartNetworkPolicyManagerService 无法启动到桌面
    14.  StartNetworkManagementService 无法启动到桌面
    15.  StartDevicePolicyManager 桌面黑屏
    16.  StartLockSettingsService 无法启动到桌面
    17.  StartStorageManagerService 无法启动到桌面
    18.  MakeDisplayReady 无法启动到桌面
    19.  StartInputMethodManagerLifecycle 无法启动到桌面
    20.  WindowManagerServiceOnInitReady 无法启动到桌面
    21.  SetWindowManagerService 无法启动到桌面
    22.  StartWindowManagerService 无法启动到桌面
    23.  StartInputManagerService 无法启动到桌面
    24.  StartAlarmManagerService 无法启动到桌面
    25.  InstallSystemProviders 无法启动到桌面
    26.  StartContentService 无法启动到桌面
    27.  StartAccountManagerService 无法启动到桌面
    28.  StartWebViewUpdateService 影响antutu成绩
    29.  StartUsageService  无法启动到桌面
    30.  StartBatteryService 无法启动到桌面
    31.  StartOverlayManagerService 无法启动到桌面
    32.  SetSystemProcess 无法启动到桌面
    33.  StartPackageManagerService  无法启动到桌面
    34.  StartDisplayManager 无法启动到桌面
    35.  StartLightsService 无法启动到桌面
    36.  StartPowerManager 无法启动到桌面
    37.  StartActivityManager 无法启动到桌面
    38.  UriGrantsManagerService 无法启动到桌面
  - 可裁剪
    1. WaitForDisplay
    2. StartRollbackManagerService
    3. StartKeyAttestationApplicationIdProviderService
    4. StartKeyChainSystemService
    5. StartSchedulingPolicyService
    6. StartTelecomLoaderService
    7. StartTelephonyRegistry
    8. StartEntropyMixer
    9. StartVibratorService
    10. IpConnectivityMetrics
    11. NetworkWatchlistService
    12. PinnerService
    13. StartUiModeManager
    14. UpdatePackagesIfNeeded
    15. StartOemLockService
    16. StartContentSuggestionsService
    17. StartWifi
    18. StartWifiScanning
    19. StartWifiP2P
    20. StartTimeDetectorService
    21. StartStatsCompanionService
    22. MakeLockSettingsServiceReady
    23. MakeWindowManagerServiceReady
    24. MakeDisplayManagerServiceReady
    25. StartActivityManagerReadyPhase
    26. MakeNetworkStatsServiceReady
    27. MakeConnectivityServiceReady
    28. StartNetworkStack
    29. MakeNetworkTimeUpdateReady

## 模块修正

- `com.android.media.swcodec`模块不可移除，否则，antutu3D无法运行