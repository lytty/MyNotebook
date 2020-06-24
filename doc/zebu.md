# ZEBU 分之代码

1. base manifest： http://10.0.1.99:8080/jenkins/job/sprdroid8.1_trunk_sharkl3_daily_build/24/artifact/manifest.xml

# ZEBU dump寄存器命令
1. d.dump anp:0x31000000++0x37F

# ZEBU 查看屏幕亮与否命令
1.  `cat /sys/class/backlight/sprd_backlight/actual_brightness`


# ZEBU 登录流程
1. 申请VNC账号: plinux_zebu1:4, 密码：sciuser
2. 申请Vdi（内网账号）： haibin.xu, 123@abAB
3. 本地安装VMware Horizon Client
4. 按照《VDI平台用户手册》使用VDI账号进入VDI平台
5. 在VDI平台中点击vncviewer，使用vnc账号登录vnc
6. ZEBU资源申请： M2， zeburuntime23

# ZEBU环境搭建
1. 登录vnc后， 在/proj_pld目录下创建自己的目录（/proj_pld/haibin.xu/）
2. 在自己目录内（/proj_pld/haibin.xu/），创建项目zebu（如从其他地方拷贝sharkl5_pha_zs3_new_rtl0.9_2_for_ddrfinal_waveform）
3. 拷贝img目录至本地（一般按sharkl5_pha_zs3_new_rtl0.9_2_for_ddrfinal_waveform/zebu_run/sharkl5_img链接文件路径来拷贝）
4. 检查sharkl5_pha_zs3_new_rtl0.9_2_for_ddrfinal_waveform/zebu_run/script/load_yf_gpu.tcl中img配置路径是否正确
5. 向dongjia.wang申请zebu runtime资源（其会分配给你Runtime端口号， 以及片资源号： M*, 一般会直接给你配置好的setup_1703.csh配置文件， 直接拷贝至本地zebu_run/目录， 替换原有的即可， 但注意拷贝一下原有的配置文件）。
6. ssh -X <haibin.xu>@zeburuntime23  密码是内网密码
7. source setup_1703.csh
8. make emu

# ZEBU 异常处理
1. zebu正在运行时， 出错关闭流程：
    - 关闭“ZEBU run control interface”窗口中的clock
    - 点击exit

# ZEBU工程
- 代码分支： sprdroid8.1_trunk_zebu_dev
- 在ZEBU分支上提交代码后，编译处img， 转到zebu上即可

# ZEBU跑分
- 获取跑分apk的img，在本地通过sudo mount -t ext4 -o rw cache_sharkl5gpu_new_antutu.img [dirname]命令获取img内部文件， 按照需求修正其setting.xml文件
- 使用umount [dirname]命令打包成img文件
- 拷贝到zubu下项目的img目录
- 拆分img, 使用zebu_run目录下split128.py
- 打开designFeatures,查看加载的脚本：`$memoryInitDB = 'script/*.tcl'`
- 打开'script/*.tcl'脚本，查找`ZEBU_Memory_loadFromFile`命令下的两条`proj_*`开头的参数行，在`ZeBu Run Control Interface`窗口的`Tcl command`窗口键入以上两条`ZEBU_Memory_loadFromFile proj_*`命令
- 在串口（即：`*******UART*******(on zeburuntime21)`窗口）中键入以下命令：
    ```
    1. su
    2. mount -t ext4 -o rw /dev/block/memdisk.3 cache #memdisk后的数字按照sprdroid8.1_trunk_zebu_dev/kernel/arch/arm64/boot/dts/sprd目录下相应board的dtsi文件中，如spsharkl5_zebu.dts，在reserved-memory中查找cache， 按照0（system）,1（vendor）,2（userdata）,3（cache）来确定：
    reserved-memory {
        #address-cells = <2>;
        #size-cells = <2>;
        ranges;
        memdisk_reserved: memdisk@100000000{
            reg = <0x1 0x00000000 0x0 0x48000000>,   /* system 1152M */
                  <0x0 0xc0000000 0x0 0x1ff00000>,      /* vendor 512M */
                  <0x0 0xe0000000 0x0 0x1ff00000>,      /* userdata 512M */
                  <0x1 0x48100000 0x0 0x11300000>;      /* cache 275M */
        };
        fb_reserved: framebuffer@18a800000{
                reg = <0x0 0x8a800000 0x0 0x2fd0000>;
        };
        overlay_reserved: overlaybuffer@18d800000{
                reg = <0x0 0x8d800000 0x0 0x7080000>;
        };
        mm_reserved: multimediabuffer@194900000{
                reg = <0x0 0x94900000 0x0 0x11040000>;
        };
    };
    3. cd cache; ls -l; #即可看到我们上传的img已mount到cache中
    4. chmod 777 -R ./; #更改cache中文件权限
    5. mkdir -p /data/local/tmp
    6. mkdir /sdcard/.antutu/
    7. cp settings.xml /sdcard/.antutu/
    8. cd /
    9. ln -s /cache/sb /data/local/tmp/
    10. ./cache/sb/rs0
    ```
    - 注： 因为rs0中执行rs 82 13 10有问题， 所以在报错后需要执行以下代码,
    ```
    input keyevent 82; sleep 2; input keyevent 82; am start -S -W -n com.antutu.ABenchMark/com.antutu.ABenchMark.ABenchMarkStart -e 74Sd42l35nH e57b6eb9906e27062fc7fcfcc820b957a5c33b649

    
    ```

# 修改分区大小
 - 两个文件：
    - platform/kernel/arch/arm64/boot/dts/sprd/spsharkl5_zebu.dts
    ```
    0x48000000 1152M
    0x40000000 1024M 1073741824
    0x38400000 900M  943718400
    0x35200000 850M  891289600
    0x32000000 800M  838860800
    0x2ee00000 750M
    0x28000000 640M  671088640
    0x25800000 600M  629145600
    0x20000000 512M  536870912
    0x19000000 400M  419430400
    0x14000000 320M
    0x12c00000 300M  314572800
    0x10000000 256M
    0x03200000 50M   52428800
    
    ```
    ```
    memdisk_reserved: memdisk@100000000{
        reg = <0x1 0x00000000 0x0 0x35200000>, /* 850M */
        <0x0 0xc0000000 0x0 0x19000000>, /* 400M */
        <0x0 0xe0000000 0x0 0x20000000>, /* 512M */
        <0x1 0x48100000 0x0 0x03200000>; /* 50M */
    };
    ```
    - device/sprd/sharkl5/spsharkl5_zebu/BoardConfig.mk
    ```
    BOARD_USERDATAIMAGE_PARTITION_SIZE := 268435456
    ```

# zebu时长参考：
- sharkl5 zebu
    ```
    0.000000 ------- 2.013075      ===>     10:17:29 -------- 11:32:39       ==> 36.916988521min/s
    0.000000 ------- 6.602142      ===>     10:17:29 -------- 14:14:12       ==> 35.854525193min/s
    0.000000 ------- 18.789003     ===>     00:08:30 -------- 11:13:11
      ==> 35.376189643min/s 
    ```

# zebu相关命令
    ```
    cd cache; ls -l; chmod 777 -R ./; mkdir /sdcard/.antutu/; cp setting.xml /sdcard/.antutu/; pm install -f -g antutu-benchmark-V6_3_3.apk; pm install -f -g antutupingce3D_6010101.apk
    
    pm install -f -g antutu-benchmark-v7.1.0-1-20180916_zebu-release.apk; pm install -f -g antutu-benchmark-v7.1.0-1-20180916_zebu-release.apk;
    
    am start -S -W -n com.antutu.ABenchMark/com.antutu.ABenchMark.ABenchMarkStart -e 74Sd42l35nH e57b6eb9906e27062fc7fcfcc820b957a5c33b649
    ```
- 设置printk等级
    ```
    cat /proc/sys/kernel/printk
    echo "1 1 1 1" > /proc/sys/kernel/printk
    ```
- 终止antutu运行
    ```
    am force-stop[clear] com.antutu.ABenchMark 
    ```

# board创建, 以sharkl5-zebu创建为例
- chipram
    - `http://review.source.spreadtrum.com/gerrit/#/c/527090/`

- vendor/sprd/modules/wcn
    - `http://review.source.spreadtrum.com/gerrit/#/c/526703/`

- device/sprd/sharkl5
    - `http://review.source.spreadtrum.com/gerrit/#/c/526660/`

- u-boot15
    - `http://review.source.spreadtrum.com/gerrit/#/c/527064/`

- kernel/common
    - `http://review.source.spreadtrum.com/gerrit/#/c/527962/`