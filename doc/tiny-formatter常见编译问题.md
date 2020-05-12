# tiny-formatter常见编译问题

## 1. AndroidR QogirL6 gatekeeper问题

```log
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:121] Sysprop ro.boot.product.hardware.sku=
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/vendor/odm/etc/vintf/manifest.xml': No such file or directory
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/vendor/odm/etc/manifest.xml': No such file or directory
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:83] List 'out/target/product/ums9230_haps/vendor/odm/etc/vintf/manifest/': No such file or directory
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:83] List 'out/target/product/ums9230_haps/system/etc/vintf/': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.2.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.legacy.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.device.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.1.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.5.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.4.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/compatibility_matrix.3.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system/etc/vintf/manifest.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:83] List 'out/target/product/ums9230_haps/system_ext/etc/vintf/': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/system_ext/etc/vintf/manifest.xml': SUCCESS
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:83] List 'out/target/product/ums9230_haps/product/etc/vintf/': No such file or directory
checkvintf I 04-10 17:51:37 26604 26604 check_vintf.cpp:73] Fetch 'out/target/product/ums9230_haps/vendor/etc/vintf/compatibility_matrix.xml': SUCCESS
checkvintf E 04-10 17:51:37 26604 26604 check_vintf.cpp:511] files are incompatible: Device manifest and framework compatibility matrix are incompatible: HALs incompatible. Matrix level = 4. Manifest level = 4. The following requirements are not met:
checkvintf E 04-10 17:51:37 26604 26604 check_vintf.cpp:511] android.hardware.gatekeeper:
checkvintf E 04-10 17:51:37 26604 26604 check_vintf.cpp:511]     required: @1.0::IGatekeeper/default
checkvintf E 04-10 17:51:37 26604 26604 check_vintf.cpp:511]     provided: 
checkvintf E 04-10 17:51:37 26604 26604 check_vintf.cpp:511] 
INCOMPATIBLE

```

分析： haps/zebu版本编译时，tiny-formatter中会将out目录下的/vendor/etc/vintf/manifest.xml替换为tiny-formatter中相应文件（tiny-formatter对应文件中会注释掉或移除一些hidl，其中就包括gatekeeper），这就导致最终的/vendor/etc/vintf/manifest.xml 与compatibility matrix不匹配，而报出以上异常 

解决方案1： 修改tiny-formatter中对应xml文件：http://review.source.unisoc.com/gerrit/#/c/667788/

解决方案2： 仿照`sharkl3、sharkl5Pro`工程中gatekeeper的配置，配置`QogirL6`工程配置，主要有以下两个文件：

1.   sprdroidr_trunk/device/sprd/mpool/product/soc/msoc/qogirl6/march/arm64/manifest.xml
2.   sprdroidr_trunk/device/sprd/mpool/module/security/msoc/qogirl6/qogirl6.mk

gatekeeper模块owner： 邬金平 (Jinping Wu)



## 2. boot.img too large问题

```log
FAILED: out/target/product/ums9230_haps/boot.img out/target/product/ums9230_haps/ramdisk-recovery.img
/bin/bash -c "(mkdir -p out/target/product/ums9230_haps/recovery ) && (mkdir -p out/target/product/ums9230_haps/recovery/root/sdcard out/target/product/ums9230_haps/recovery/root/tmp ) && (rsync -a --exclude=sdcard --exclude=/root/sepolicy --exclude=/root/plat_file_contexts --exclude=/root/plat_property_contexts --exclude=/root/system_ext_file_contexts --exclude=/root/system_ext_property_contexts --exclude=/root/vendor_file_contexts --exclude=/root/vendor_property_contexts --exclude=/root/odm_file_contexts --exclude=/root/odm_property_contexts --exclude=/root/product_file_contexts --exclude=/root/product_property_contexts  out/target/product/ums9230_haps/root out/target/product/ums9230_haps/recovery ) && (ln -sf /system/bin/init out/target/product/ums9230_haps/recovery/root/init ) && (find out/target/product/ums9230_haps/recovery/root -maxdepth 1 -name 'init*.rc' -type f -not -name \"init.recovery.*.rc\" | xargs rm -f ) && (cp out/target/product/ums9230_haps/root/init.recovery.*.rc out/target/product/ums9230_haps/recovery/root/ 2> /dev/null || true ) && (mkdir -p out/target/product/ums9230_haps/recovery/root/res ) && (rm -rf out/target/product/ums9230_haps/recovery/root/res/* ) && (cp -rf bootable/recovery/res-xxhdpi/* out/target/product/ums9230_haps/recovery/root/res ) && (cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates/installing_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//installing_security_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//erasing_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//error_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//no_command_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//cancel_wipe_data_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//factory_data_reset_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//try_again_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//wipe_data_confirmation_text.png out/target/product/ums9230_haps/recovery/root/res/images/ &&  cp -rf out/target/product/ums9230_haps/obj/PACKAGING/recovery_text_res_intermediates//wipe_data_menu_header_text.png out/target/product/ums9230_haps/recovery/root/res/images/ && true ) && (cp -f bootable/recovery/fonts/18x32.png out/target/product/ums9230_haps/recovery/root/res/images/font.png ) && (ln -sf prop.default out/target/product/ums9230_haps/recovery/root/default.prop ) && (out/host/linux-x86/bin/mkbootfs -d out/target/product/ums9230_haps/system out/target/product/ums9230_haps/recovery/root | out/host/linux-x86/bin/minigzip > out/target/product/ums9230_haps/ramdisk-recovery.img ) && (out/host/linux-x86/bin/mkbootimg --kernel out/target/product/ums9230_haps/kernel  --ramdisk out/target/product/ums9230_haps/ramdisk-recovery.img --os_version 10 --os_patch_level 2020-05-05 --kernel_offset 0x00008000 --ramdisk_offset 0x05400000 --header_version 3 --pagesize=4096 --output  out/target/product/ums9230_haps/boot.img ) && (size=\$(for i in  out/target/product/ums9230_haps/boot.img; do stat -c \"%s\" \"\$i\" | tr -d '\\n'; echo +; done; echo 0); total=\$(( \$( echo \"\$size\" ) )); printname=\$(echo -n \" out/target/product/ums9230_haps/boot.img\" | tr \" \" +); maxsize=\$((   47185920-0)); if [ \"\$total\" -gt \"\$maxsize\" ]; then echo \"error: \$printname too large (\$total > \$maxsize)\"; false; elif [ \"\$total\" -gt \$((maxsize - 32768)) ]; then echo \"WARNING: \$printname approaching size limit (\$total now; limit \$maxsize)\"; fi )"
error: +out/target/product/ums9230_haps/boot.img too large (48857088 > 47185920)

```

分析： mboot版本编译时，往ramdisk中存放的文件过多，导致最后bootimage打包时超过限制，打包失败

解决： 将一些无关紧要的文件移除，不再往ramdisk中存放，http://review.source.unisoc.com/gerrit/#/c/668105/