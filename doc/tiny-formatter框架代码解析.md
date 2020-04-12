# tiny-formatter框架代码解析

## 1. tiny-formatter框架代码解析

- 对`tiny-formatter`框架代码的解析，正确的顺序应该是根据`platform/build/make/core/main.mk、platform/build/make/core/Makefile、platform/build/make/core/dex_preopt_odex_install.mk`三个文件中对`tiny-formatter/build/`目录下相关文件的包含顺序来分析。
- 以下我们已zebu平台版本为例，来展示`tiny-formatter`框架内各文件的包含顺序，haps平台与此类似。
- `platform/build/make/core/main.mk`共包含4个文件，其顺序如下:
  
  1.  `-include vendor/sprd/proprietories-source/tiny-formatter/build/build_tiny_definitions.mk`
  2.  `-include $(TINY_BASE_DIR)/build_tiny_property.mk`
  3.  `-include $(TINY_BASE_DIR)/build_tiny_custom_modules.mk`
  4.  `-include $(TINY_BASE_DIR)/build_tiny_product_modules.mk`
- `platform/build/make/core/Makefile`共包含2个文件，其顺序如下:
  1.  `-include $(TINY_BASE_DIR)/build_tiny_product_copy_files.mk`
  2.  `-include $(TINY_BASE_DIR)/build_tiny_files.mk`
- `platform/build/make/core/dex_preopt_odex_install.mk`共一个文件:
  1.  `-include $(TINY_BASE_DIR)/build_tiny_dex_preopt_odex_install.mk`
- 对以上7个文件内部包含分析，下面我们都以tiny-formatter相对路径来表示：

  1.  `tiny-formatter/build/build_tiny_definitions.mk`

     ```
     tiny-formatter/build/build_tiny_definitions.mk
     |-- tiny-formatter/build/common/tiny_definitions.mk
         |-- tiny-formatter/model/zebu/zebu_definitions.mk
     
     ```

  2.  `tiny-formatter/build/build_tiny_property.mk`

     ```
     tiny-formatter/build/build_tiny_property.mk
     |-- tiny-formatter/build/common/tiny_property.mk
         |-- tiny-formatter/model/mboot/mboot_property.mk
         |-- tiny-formatter/model/zebu/zebu_property.mk
     
     ```

  3.  `tiny-formatter/build/build_tiny_custom_modules.mk`

     ```
     tiny-formatter/build/build_tiny_custom_modules.mk
     |-- tiny-formatter/build/common/tiny.mk
         |-- tiny-formatter/model/zebu/zebu.mk
         |-- tiny-formatter/model/zebu/zebu_only_installed.mk
     
     ```

  4.  `tiny-formatter/build/build_tiny_product_modules.mk`

     ```
     tiny-formatter/build/build_tiny_product_modules.mk
     |-- tiny-formatter/build/common/tiny.mk
         |-- tiny-formatter/model/zebu/zebu.mk
         |-- tiny-formatter/model/zebu/zebu_only_installed.mk
     
     ```

  5.  `tiny-formatter/build/build_tiny_product_copy_files.mk`

     ```
     tiny-formatter/build/build_tiny_product_copy_files.mk
     |-- tiny-formatter/build/common/tiny_product_copy_files.mk
         |-- tiny-formatter/model/zebu_product_copy_files.mk
     
     ```

  6.  `tiny-formatter/build/build_tiny_files.mk`

     ```
     tiny-formatter/build/build_tiny_files.mk
     |-- tiny-formatter/build/common/tiny_files.mk
         |-- tiny-formatter/model/zebu/zebu_files.mk
         |-- tiny-formatter/model/zebu/zebu_only_installed.mk
         |-- tiny-formatter/build/common/tiny_modules_must_be_appened.mk
         |   |--tiny-formatter/model/mboot/mboot_modules_must_be_appened.mk
         |   |--tiny-formatter/model/zebu/zebu_modules_must_be_appened.mk
         |-- tiny-formatter/build/common/tiny_files_must_be_appened.mk
             |--tiny-formatter/model/mboot/mboot_files_must_be_appened.mk
     	  	|--tiny-formatter/model/mboot/mboot.mk
             |--tiny-formatter/model/zebu/zebu_files_must_be_appened.mk
     
     ```

  7.  `tiny-formatter/build/build_tiny_dex_preopt_odex_install.mk`
  
      ```
      tiny-formatter/build_tiny_dex_preopt_odex_install.mk
      |-- tiny-formatter/build/common/tiny_dex_preopt_odex_install.mk
      
      ```
  
      

## 2. tiny-formatter/build/build_tiny_definitions.mk

- `tiny-formatter/build/build_tiny_definitions.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
TINY_BASE_DIR := $(subst $(empty) $(empty),/,$(wordlist 1, 999, $(subst /,$(empty) $(empty),$(dir $(lastword $(MAKEFILE_LIST))))))
TINY_BASE_DIR_ROOT := $(subst $(empty) $(empty),/,$(wordlist 1, 999, $(subst /,$(empty) $(empty),$(dir $(TINY_BASE_DIR)))))
include $(TINY_BASE_DIR)/common/tiny_definitions.mk

```

定义变量TINY_BASE_DIR、TINY_BASE_DIR_ROOT，一般情况下，两个变量的值为：

```
TINY_BASE_DIR=vendor/sprd/proprietories-source/tiny-formatter/build
TINY_BASE_DIR_ROOT=vendor/sprd/proprietories-source/tiny-formatter

```

将tiny-formatter/build/common/tiny_definitions.mk包进来

- `tiny-formatter/build/common/tiny_definitions.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# ifeq ($(TINY_BUILD_VERSION), tiny) # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually
# 一般来说，我们在编译Android时，如果手动配置lunch，如 lunch s9863a1h10_Natv-userdebug-tiny@zebu,mboot，那么此时TARGET_BUILD_VERSION=tiny@zebu,mboot，如果TINY_BUILD_VERSION此前没有被赋值，则TINY_BUILD_VERSION也为tiny@zebu,mboot，如果我们是通过export TINY_BUILD_VERSION=tiny@zebu，mboot来为TINY_BUILD_VERSION赋值的，而且正常lunch，如lunch s9863a1h10_Natv-userdebug-native，那么此时TINY_BUILD_VERSION=tiny@zebu，mboot，TARGET_BUILD_VERSION=native
##################################################################
TINY_BUILD_VERSION ?= $(TARGET_BUILD_VERSION) 
##################################################################
TINY :=
# 11-14行，调用tiny_definitions.sh脚本，参数分别为TARGET_PRODUCT、TINY_BUILD_VERSION，来获取TINY_BUILD_MODEL值，TINY_BUILD_MODEL值为zebu或haps
TINY_BUILD_MODEL := $(shell $(TINY_BASE_DIR_ROOT)/build/common/tiny_definitions.sh $(TARGET_PRODUCT))
ifeq (,$(TINY_BUILD_MODEL))
TINY_BUILD_MODEL := $(shell $(TINY_BASE_DIR_ROOT)/build/common/tiny_definitions.sh $(TINY_BUILD_VERSION))
endif

# 17-36行，通过TINY_BUILD_VERSION判断是否为mboot版本，并设置TINY、TINY_ARGS、TARGET_MBOOT_VERSION、TINY_BUILD_VERSION变量
ifeq (mboot,$(findstring mboot, $(TINY_BUILD_VERSION)))
TINY := MBOOT
TINY_ARGS := mboot
# mboot is a shortcut for tiny@zebu,mboot
TARGET_MBOOT_VERSION := 2             # ums512_1h10_nosec-userdebug-mboot  for 安装mboot到ramdisk.img和system.img
ifeq (mboot0,$(TINY_BUILD_VERSION)) # ums512_1h10_nosec-userdebug-mboot1 for 安装mboot到system.img
TARGET_MBOOT_VERSION := 0             # ums512_1h10_nosec-userdebug-mboot0 for 安装mboot到ramdisk.img
endif
ifeq (mboot1,$(TINY_BUILD_VERSION))
TARGET_MBOOT_VERSION := 1
endif
ifeq (mboot2,$(TINY_BUILD_VERSION))
TARGET_MBOOT_VERSION := 2
endif
ifeq (,$(TINY_BUILD_MODEL))
WITH_FULL ?= true
else
TINY_BUILD_VERSION := tiny@$(TINY_BUILD_MODEL),mboot
endif
endif

ifeq (tiny@,$(findstring tiny@, $(TINY_BUILD_VERSION)))
ifneq ($(WITH_FULL),true)
WITH_FULL :=
endif
COMMA := ,
TINY := $(patsubst tiny@%,%, $(TINY_BUILD_VERSION)) # tiny@zebu,mboot or tiny@zebu,antutu7apk.no3D， 获取tiny@zebu,mboot中@后的字符给TINY
TINY := $(subst $(empty) $(empty),,$(TINY)) #将TINY中的空格去掉
TINY := $(subst $(COMMA),$(empty) $(empty),$(TINY)) #TINY中的逗号替换为空格
TINY_ARGS := $(subst $(empty) $(empty),$(COMMA),$(wordlist 2, 999, $(TINY))) #取TINY中第二个开始的的单词字符串，并将空格替换为逗号，TINY_BUILD_VERSION=tiny@zebu,mboot时，TINY_ARGS则为mboot
TINY := $(word 1, $(TINY)) #将TINY中第一个单词重新赋值给TINY，即zebu或haps
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_definitions.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_definitions.mk
endif
$(warning You can export TINY_BUILD_VERSION=mboot; lunch xxxx; make -j32; to build mboot version)
 #打印TINY TINY_ARGS TARGET_BUILD_VERSION TINY_BUILD_VERSION WITH_FULL MAKECMDGOALS变量
$(warning $(shell echo -e "\033[32mTiny build on TINY_BUILD_MODEL=$(TINY_BUILD_MODEL) TINY=$(TINY) TINY_ARGS=$(TINY_ARGS) TARGET_BUILD_VERSION=$(TARGET_BUILD_VERSION) TINY_BUILD_VERSION=$(TINY_BUILD_VERSION) WITH_FULL=$(WITH_FULL) MAKECMDGOALS=$(MAKECMDGOALS)\033[0m"))
# endif # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually


```

- `tiny-formatter/build/common/tiny_definitions.sh`

```shell
#!/bin/bash
TARGET_PRODUCT="$@"
for model in 'zebu' 'haps'; do
    [ "$(echo  "${TARGET_PRODUCT}" | grep ${model})" ] && { echo "${model}"; exit 0; }
done

true

```

- `tiny-formatter/model/zebu/zebu_definitions.mk`，根据WITH_FULL是否为空，来定义WITH_DEXPREOPT，并定义SELINUX_IGNORE_NEVERALLOWS为true

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
WITH_DEXPREOPT := true# Both of userdebug and user must use DEXPREOPT option to soft link to framework/.*vdex *.odex in /data/dalvik-cache/arm64/
endif
SELINUX_IGNORE_NEVERALLOWS := true# Ignore checkpolicy -M -c for sepolicy_policy.conf := $(intermediates)/policy.conf in system/sepolicy/Android.mk +85


```



## 3. tiny-formatter/build/build_tiny_property.mk

- `tiny-formatter/build/build_tiny_property.mk`：

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# 首先会判断TINY是否不等于空，如果不为空，则进入tiny-formatter/build/common/tiny_property.mk文件继续执行，如果等于空，则什么也不执行
ifneq ($(TINY),)
include $(TINY_BASE_DIR)/common/tiny_property.mk
endif

```

- `tiny-formatter/build/common/tiny_property.mk`, 将TINY=zebu， SELINUX_IGNORE_NEVERALLOWS=true添加到BOARD_SEPOLICY_M4DEFS中，将ro.tiny=$(TINY)，ro.tiny.mode="$(TINY_ARGS)"添加到ADDITIONAL_DEFAULT_PROPERTIES中，这两个属性最终会写到/system/etc/prop.default文件中，将ro.lockscreen.disable.default=true添加到ADDITIONAL_BUILD_PROPERTIES中，这个修改最终会写到/system/build.prop文件中，最后分别包含`tiny-formatter/model/mboot/mboot_property.mk`，`tiny-formatter/model/$(TINY)/$(TINY)_property.mk`文件，至于`$(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_property.mk`，我们一般不定义该文件

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# ifeq ($(TINY_BUILD_VERSION), tiny) # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually
BOARD_SEPOLICY_M4DEFS += TINY=$(TINY) # zebu.te m4 rules system/sepolicy/Android.mk system/sepolicy/definitions.mk
BOARD_SEPOLICY_M4DEFS += SELINUX_IGNORE_NEVERALLOWS=$(SELINUX_IGNORE_NEVERALLOWS)
# /system/etc/prop.default
ADDITIONAL_DEFAULT_PROPERTIES += \
	ro.tiny=$(TINY) \
	ro.tiny.mode="$(TINY_ARGS)"
# /system/build.prop
ADDITIONAL_BUILD_PROPERTIES += \
	ro.lockscreen.disable.default=true
-include $(TINY_BASE_DIR_ROOT)/model/mboot/mboot_property.mk
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_property.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_property.mk
# endif # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually


```

- `tiny-formatter/model/mboot/mboot_property.mk`,主要调用了`tiny-formatter/model/mboot/src/android/setup.sh`

```makefile
#
# Copyright (C) 2019 UNISOC Communications Inc.
#
ifeq ($(TINY_ARGS), mboot)
ifeq (patching,patching)
$(warning $(shell echo -e "\033[36m############################## Environment setup : patching files for mboot ##############################\033[0m"))
$(warning $(shell echo -e "\033[36m$(shell TOP=$(TOP) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY_ARGS=$(TINY_ARGS) \
			TARGET_ARCH=$(TARGET_ARCH) \
			TARGET_PRODUCT=$(TARGET_PRODUCT) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			MODE=patching \
			$(TINY_BASE_DIR_ROOT)/model/mboot/src/android/setup.sh)\033[0m"))
endif # ifeq (paching,patching)
endif

```

- `tiny-formatter/model/mboot/src/android/setup.sh`

```shell
#!/bin/bash -x
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
BASE=$(dirname `readlink -f $0`) # 获取shell脚本的相对路径，$0即为当前shell脚本
function md5() { # 获取$1的MD5值
    echo $(md5sum $1 | cut -d' ' -f 1)
}
function copy_verify() { # 根据SRC与DST文件的md5值是否相同，来判断是否拷贝SRC文件到DST文件中
    SRC=$1
    DST=$2
    DIFF=$3
    [ $(md5 ${SRC}) = $(md5 ${DST}) ] || {
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; patch -p1 < ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/frameworks/native; patch -p1 < ${BASE}/frameworks/native/opengl/libagl/0001-Fix-sharkl3-package-build-error-on-libGLES_android.s.patch"
        # [ -e ${DST}.bak ] || cp ${DST} ${DST}.bak
        cp ${DST} ${DST}.bak # Update .bak file
        echo "patching ${DST}"
        cp ${SRC} ${DST}
    }
    # [ "${DIFF}" -a -e ${DST}.bak ] && diff -rNu ${SRC} ${DST}.bak
}
function revert_copy_verify() {# 根据SRC与DST文件的md5值是否相同，来判断是否还原DST文件
    SRC=$1
    DST=$2
    DIFF=$3
    [ $(md5 ${SRC}) = $(md5 ${DST}) ] && {
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; patch -p1 < ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/frameworks/native; patch -p1 < ${BASE}/frameworks/native/opengl/libagl/0001-Fix-sharkl3-package-build-error-on-libGLES_android.s.patch"
        # [ -e ${DST}.bak ] || cp ${DST} ${DST}.bak
        mv ${DST}.bak ${DST} # Update .bak file
        echo "Unpatching ${DST}"
    }
    # [ "${DIFF}" -a -e ${DST}.bak ] && diff -rNu ${SRC} ${DST}.bak
}
echo "tiny-formatter setuping ..."
[ "${MODE}" = "patching" ] && {
    if [ "${TINY_ARGS}" = "mboot" ]; then # 根据TINY_ARGS是否为mboot，来判断是否拷贝frameworks/native/cmds/atrace/atrace.cpp文件
        echo "mboot atrace to capter offline linux kernel systrace more beautiful than trace-cmd: /system/bin/atrace -z -b 10240 gfx input view wm am hal res dalvik rs sched freq idle load disk mmc -t 15 > /data/local/tmp/trace_output"
        echo "
抓取离线systrace步骤：

1. adb root, adb remount, adb shell
2. 检查/system/bin/atrace是否可用
3. 抓取： atrace -z -b 10240 gfx input view wm am hal res dalvik rs sched freq idle load disk mmc -t 15 > /data/local/tmp/trace_output
4. pull回本地： adb pull /data/local/tmp/trace_output .
5. 转换： systrace.py --from-file trace_output -o output.html
        "
        f=frameworks/native/cmds/atrace/atrace.cpp
        copy_verify ${BASE}/${f} ${TOP}/${f} true
    else
        f=frameworks/native/cmds/atrace/atrace.cpp
        revert_copy_verify ${BASE}/${f} ${TOP}/${f} true
    fi
    exit 0
}


```

- `tiny-formatter/model/zebu/zebu_property.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# ADDITIONAL_BUILD_PROPERTIES += sys.zebu.info=true
# ADDITIONAL_BUILD_PROPERTIES --> /system/build.prop
# ADDITIONAL_DEFAULT_PROPERTIES --> /system/etc/prop.default
# 根据TINY_ARGS是否包含antutu7apk、zebu.antutu7apk.3D，向ADDITIONAL_DEFAULT_PROPERTIES中添加sys.zebu.idle.seconds=*属性
ifneq ($(findstring antutu7apk,$(TINY_ARGS)),)
	# ADDITIONAL_DEFAULT_PROPERTIES += sys.zebu.idle.seconds=10
ifneq ($(findstring zebu.antutu7apk.3D,$(TINY_ARGS)),)
	ADDITIONAL_DEFAULT_PROPERTIES += sys.zebu.idle.seconds=2
else
	ADDITIONAL_DEFAULT_PROPERTIES += sys.zebu.idle.seconds=1
endif
endif

# 18~32行打印super.img、system.img、vendor.img、userdata.img、SE NeverAllow、HWC、GPU、API_LEVEL、VNDK、FULL_TREBLE等信息
$(warning $(shell echo -e "\033[31mIf USE_SPRD_HWCOMPOSER := false; then hwcomposer.$(TARGET_BOARD_PLATFORM) is removed and android launcher is ok without HWC & GPU\033[0m"))
$(warning --------------------------)
# bc是shell中一种任意精度的计算语言，可计算浮点数
$(warning $(shell echo -e "\033[32m####      super.img -$(shell printf "%8s" $(shell echo "scale=2;$(BOARD_SUPER_PARTITION_SIZE)/1024/1024" | bc))\033[0m M - dm sparse format"))
$(warning $(shell echo -e "\033[32m####     system.img -$(shell printf "%8s" $(shell echo "scale=2;$(BOARD_SYSTEMIMAGE_PARTITION_SIZE)/1024/1024" | bc))\033[0m M - ext4"))
$(warning $(shell echo -e "\033[32m####     vendor.img -$(shell printf "%8s" $(shell echo "scale=2;$(BOARD_VENDORIMAGE_PARTITION_SIZE)/1024/1024" | bc))\033[0m M - $(BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE)"))
$(warning $(shell echo -e "\033[32m####   userdata.img -$(shell printf "%8s" $(shell echo "scale=2;$(BOARD_USERDATAIMAGE_PARTITION_SIZE)/1024/1024" | bc))\033[0m M - $(BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE)"))
$(warning --------------------------)
$(warning $(shell echo -e "\033[32m####  SE NeverAllow - \033[0m\033[33mSELINUX_IGNORE_NEVERALLOWS = \033[0m\033[31m$(SELINUX_IGNORE_NEVERALLOWS)\033[0m"))
$(warning $(shell echo -e "\033[32m####  HWC           - \033[0m\033[33mUSE_SPRD_HWCOMPOSER        = \033[0m\033[31m$(USE_SPRD_HWCOMPOSER)\033[0m"))
$(warning $(shell echo -e "\033[32m####  GPU           - \033[0m\033[33mTARGET_GPU_PLATFORM        = \033[0m\033[31m$(TARGET_GPU_PLATFORM)\033[0m"))
$(warning $(shell echo -e "\033[32m####  API_LEVEL     - \033[0m\033[33mPRODUCT_SHIPPING_API_LEVEL = \033[0m\033[31m$(PRODUCT_SHIPPING_API_LEVEL)\033[0m"))
$(warning $(shell echo -e "\033[32m####  VNDK          - \033[0m\033[33mBOARD_VNDK_VERSION         = \033[0m\033[31m$(BOARD_VNDK_VERSION)\033[0m"))
$(warning $(shell echo -e "\033[32m####  FULL_TREBLE   - \033[0m\033[33mPRODUCT_FULL_TREBLE        = \033[0m\033[31m$(PRODUCT_FULL_TREBLE)\033[0m"))
$(warning --------------------------)

# 35~50 调用tiny-formatter/model/zebu/src/android/setup.sh脚本
ifeq (patching,patching)
$(warning $(shell echo -e "\033[36m############################## Environment setup : patching files ##############################\033[0m"))
$(warning $(shell echo -e "\033[36m$(shell TOP=$(TOP) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY=$(TINY) \
			TINY_ARGS=$(TINY_ARGS) \
			TINY_BUILD_MODEL=$(TINY_BUILD_MODEL) \
			TARGET_ARCH=$(TARGET_ARCH) \
			TARGET_PRODUCT=$(TARGET_PRODUCT) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			KERNEL_PATH=$(KERNEL_PATH) \
			TARGET_GPU_PLATFORM=$(TARGET_GPU_PLATFORM) \
			MODE=patching \
			TARGET_DEVICE_DIR=$(TARGET_DEVICE_DIR) \
			SELINUX_IGNORE_NEVERALLOWS=$(SELINUX_IGNORE_NEVERALLOWS) \
			$(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/android/setup.sh)\033[0m"))
endif # ifeq (paching,patching)

# 如果gpu使用soft模式
ifeq ($(TARGET_GPU_PLATFORM),soft)
# 不使用物理GPU, 使用Emulation GPU - soft gpu - gpu/soft.mk 2018/11/23 14:51:24 luther
# sprdroid9.0_trunk/frameworks/native/opengl/libs/EGL/Loader.cpp
# 324static void* load_system_driver(const char* kind) {
# 325    ATRACE_CALL();
# 326    class MatchFile {
# 327    public:
# 328        static std::string find(const char* kind) {
# 329            std::string result;
# 330            int emulationStatus = checkGlesEmulationStatus();
# 331            switch (emulationStatus) {
# 332                case 0:
# 333#if defined(__LP64__)
# 334                    result = "/vendor/lib64/egl/libGLES_android.so";
# 335#else
# 336                    result = "/vendor/lib/egl/libGLES_android.so";
# 337#endif
# 338                    return result;
# }}}}
#
# 76/* This function is called to check whether we run inside the emulator,
# 77 * and if this is the case whether GLES GPU emulation is supported.
# 78 *
# 79 * Returned values are:
# 80 *  -1   -> not running inside the emulator
# 81 *   0   -> running inside the emulator, but GPU emulation not supported
# 82 *   1   -> running inside the emulator, GPU emulation is supported
# 83 *          through the "emulation" host-side OpenGL ES implementation.
# 84 *   2   -> running inside the emulator, GPU emulation is supported
# 85 *          through a guest-side vendor driver's OpenGL ES implementation.
# 86 */
# 87static int
# 88 checkGlesEmulationStatus(void)
# 89{
# 90    /* We're going to check for the following kernel parameters:
# 91     *
# 92     *    qemu=1                      -> tells us that we run inside the emulator
# 93     *    android.qemu.gles=<number>  -> tells us the GLES GPU emulation status
# 94     *
# 95     * Note that we will return <number> if we find it. This let us support
# 96     * more additionnal emulation modes in the future.
# 97     */
# 98    char  prop[PROPERTY_VALUE_MAX];
# 99    int   result = -1;
# 100
# 101    /* First, check for qemu=1 */
# 102    property_get("ro.kernel.qemu",prop,"0");
# 103    if (atoi(prop) != 1)
# 104        return -1;
# 105
# 106    /* We are in the emulator, get GPU status value */
# 107    property_get("qemu.gles",prop,"0");
# 108    return atoi(prop);
# 109}
# 设置相关Soft gpu属性
$(warning $(shell echo -e "\033[32m############################## Soft GPU ##############################\033[0m"))
ADDITIONAL_BUILD_PROPERTIES += \
	ro.kernel.qemu=1 \
	ro.kernel.qemu.gles=0 \
	ro.opengles.version=196610 # For Antutu 3D

# PRODUCT_PACKAGES +=  \ ############### other modules must be appended ###############
#	libGLES_android \
#	libEGL       \
#	libGLESv1_CM \
#	libGLESv2 \
#	android.hardware.graphics.mapper@2.0-impl \
#	android.hardware.graphics.allocator@2.0-impl \
#	android.hardware.graphics.allocator@2.0-service \
#	android.hardware.graphics.composer@2.1-impl \
#	android.hardware.graphics.composer@2.1-service \
##	gralloc.$(TARGET_BOARD_PLATFORM).so

########### VNDK logic, core lib in default namespace can't be accesed by namespace sphal from /vendor side 2018/11/23 15:30:44 luther
# Two methods can be used
# 1. Create them in /system/lib[64]/vndk as the common vendor used lib
# 2. Create them in /vendor/lib[64] as vendor specific lib (this is better from now on)
# cp /system/lib64/libpixelflinger.so /vendor/lib64
# cp /system/lib64/libETC1.so /vendor/lib64
# cp /system/lib64/libui.so /vendor/lib64
# cp /system/lib64/android.hardware.graphics.allocator@2.0.so /vendor/lib64/
# cp /system/lib64/android.hardware.configstore@1.0.so /vendor/lib64
# cp /system/lib64/android.hardware.configstore-utils.so /vendor/lib64
# cp /system/lib64/android.hardware.configstore@1.1.so /vendor/lib64
# cp /system/lib64/libdrm.so /vendor/lib64/
# cp /system/lib64/android.frameworks.bufferhub@1.0.so /vendor/lib64/
# 如果BOARD_VNDK_VERSION不为空，调用tiny-formatter/model/zebu/src/android/setup.sh脚本
ifneq ($(BOARD_VNDK_VERSION),)
$(warning $(shell echo -e "\033[32m############################## BOARD_VNDK_VERSION=$(BOARD_VNDK_VERSION), setup patching environment ##############################\033[0m"))
$(warning $(shell echo -e "\033[36m$(shell TOP=$(TOP) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY=$(TINY) \
			TARGET_ARCH=$(TARGET_ARCH) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			KERNEL_PATH=$(KERNEL_PATH) \
			TARGET_GPU_PLATFORM=$(TARGET_GPU_PLATFORM) \
			TARGET_DEVICE_DIR=$(TARGET_DEVICE_DIR) \
			$(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/android/setup.sh)\033[0m"))
else
$(error $(shell echo -e "\033[32m############################## Should be BOARD_VNDK_VERSION=current in device/<brand>/<soc>/common/DeviceCommon.mk for libGLES_android ##############################\033[0m"))
endif
endif

# ONE_SHOT_MAKEFILE 是一个变量，当使用“mm”编译某个目录下的模块时，此变量的值即为当前指定路径下的 Make 文件的路径。tiny-manifest-create文件是一个Python脚本，主要是对manifest文件进行操作处理
ifeq ($(ONE_SHOT_MAKEFILE),)
$(warning $(shell echo -e "\033[40;33m$(shell TOP=$(TOP) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY=$(TINY) \
			TARGET_ARCH=$(TARGET_ARCH) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			KERNEL_PATH=$(KERNEL_PATH) \
			TARGET_GPU_PLATFORM=$(TARGET_GPU_PLATFORM) \
			$(TINY_BASE_DIR_ROOT)/tool/tiny-manifest-create -m)\033[0m"))
endif

```

- `tiny-formatter/model/zebu/src/android/setup.sh`，进一步调用`tiny-formatter/model/zebu/src/android/common/setup.sh`，并将所有参数传递给`tiny-formatter/model/zebu/src/android/common/setup.sh`

```makefile
#!/bin/bash -x
#
# Copyright (C) 2019 UNISOC Communications Inc.
#
BASE=$(dirname `readlink -f $0`)/
${BASE}/common/setup.sh $@

```

- `tiny-formatter/model/zebu/src/android/common/setup.sh`

```makefile
#!/bin/bash -x
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
BASE=$(dirname `readlink -f $0`)/src
function md5() {
    echo $(md5sum $1 | cut -d' ' -f 1)
}
function copy_verify() {
    SRC=$1
    DST=$2
    DIFF=$3
    [ "$(md5 ${SRC})" = "$(md5 ${DST})" ] || {
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; patch -p1 < ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/frameworks/native; patch -p1 < ${BASE}/frameworks/native/opengl/libagl/0001-Fix-sharkl3-package-build-error-on-libGLES_android.s.patch"
        # [ -e ${DST}.bak ] || cp ${DST} ${DST}.bak
        cp ${DST} ${DST}.bak # Update .bak file
        echo "patching ${DST}"
        cp ${SRC} ${DST}
    }
    # [ "${DIFF}" -a -e ${DST}.bak ] && diff -rNu ${SRC} ${DST}.bak
}
function revert_copy_verify() {
    SRC=$1
    DST=$2
    DIFF=$3
    [ "$(md5 ${SRC})" = "$(md5 ${DST})" ] && {
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; patch -p1 < ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/build/make; git am ${BASE}/build/make/tools/0001-Fix-libGLES_android-build-error-check_link_type.py.patch"
        # bash -c "cd ${TOP}/frameworks/native; patch -p1 < ${BASE}/frameworks/native/opengl/libagl/0001-Fix-sharkl3-package-build-error-on-libGLES_android.s.patch"
        # [ -e ${DST}.bak ] || cp ${DST} ${DST}.bak
        mv ${DST}.bak ${DST} # Update .bak file
        echo "Unpatching ${DST}"
    }
    # [ "${DIFF}" -a -e ${DST}.bak ] && diff -rNu ${SRC} ${DST}.bak
}
echo "tiny-formatter setuping ..."
# 如果MODE=="patching"，那么拷贝框架内的sprd_serial.c替换原始的相应文件，并修改gpu timeout 从50修正为500
if [ "${MODE}" = "patching" ]; then
    # env
    if [ "`echo ${TINY_BUILD_MODEL} | egrep 'zebu|haps'`" ]; then # Ex. TINY_BUILD_MODEL=haps或zebu
        echo "zebu Transactor baud rate is not 115200n81, u-boot can't auto append a right baud rate to chose cmdline, Ex. 5M or 3M baud rate - hot patching is the helpless choice"
        # serial
        f=bsp/kernel/${KERNEL_PATH}/drivers/tty/serial/sprd_serial.c
        copy_verify ${BASE}/${f} ${TOP}/${f} true
        # gpu timeout
        [ "$(sed -n '/msecs_to_jiffies(50));/p' ${TOP}/bsp/kernel/${KERNEL_PATH}/drivers/gpu/drm/drm_atomic_helper.c)" ] && {
            sed -i 's/msecs_to_jiffies(50));/msecs_to_jiffies(500));/' ${TOP}/bsp/kernel/${KERNEL_PATH}/drivers/gpu/drm/drm_atomic_helper.c
        }
    else
        # serial
        f=bsp/kernel/${KERNEL_PATH}/drivers/tty/serial/sprd_serial.c
        revert_copy_verify ${BASE}/${f} ${TOP}/${f} true
        # gpu timeout
        [ "$(sed -n '/msecs_to_jiffies(500));/p' ${TOP}/bsp/kernel/${KERNEL_PATH}/drivers/gpu/drm/drm_atomic_helper.c)" ] && {
            sed -i 's/msecs_to_jiffies(500));/msecs_to_jiffies(50));/' ${TOP}/bsp/kernel/${KERNEL_PATH}/drivers/gpu/drm/drm_atomic_helper.c
        }
    fi

    echo "SELINUX_IGNORE_NEVERALLOWS := ${SELINUX_IGNORE_NEVERALLOWS} process"
    # 如果SELINUX_IGNORE_NEVERALLOWS==true，修正system/sepolicy/Android.mk文件
    if [ "${SELINUX_IGNORE_NEVERALLOWS}" = "true" ]; then
        [ "$(sed -n '/^ifeq ($(TARGET_BUILD_VARIANT),user/p' ${TOP}/system/sepolicy/Android.mk)" ] && {
            sed -i 's/^ifeq ($(TARGET_BUILD_VARIANT),user)/ifeq ($(TARGET_BUILD_VARIANT),tiny-user)/' ${TOP}/system/sepolicy/Android.mk
        }
        [ "$(sed -n '/"$(TARGET_BUILD_VARIANT)" = "user"/p' ${TOP}/system/sepolicy/Android.mk)" ] && {
            sed -i 's/"$(TARGET_BUILD_VARIANT)" = "user"/"$(TARGET_BUILD_VARIANT)" = "tiny-user"/' ${TOP}/system/sepolicy/Android.mk
        }
    else
        [ "$(sed -n '/^ifeq ($(TARGET_BUILD_VARIANT),tiny-user/p' ${TOP}/system/sepolicy/Android.mk)" ] && {
            sed -i 's/^ifeq ($(TARGET_BUILD_VARIANT),tiny-user)/ifeq ($(TARGET_BUILD_VARIANT),user)/' ${TOP}/system/sepolicy/Android.mk
        }
        [ "$(sed -n '/"$(TARGET_BUILD_VARIANT)" = "tiny-user"/p' ${TOP}/system/sepolicy/Android.mk)" ] && {
            sed -i 's/"$(TARGET_BUILD_VARIANT)" = "tiny-user"/"$(TARGET_BUILD_VARIANT)" = "user"/' ${TOP}/system/sepolicy/Android.mk
        }
    fi
    echo $(cd ${TOP}/system/sepolicy/; git diff HEAD Android.mk)

	# [ -f ${TARGET_DEVICE_DIR}/${TINY_BUILD_MODEL}/setup.sh ]判断该文件是否存在
    [ -f ${TARGET_DEVICE_DIR}/${TINY_BUILD_MODEL}/setup.sh ] && {
        echo "Special Action - include ${TARGET_DEVICE_DIR}/${TINY_BUILD_MODEL}/setup.sh"
        . ${TARGET_DEVICE_DIR}/${TINY_BUILD_MODEL}/setup.sh
    }
    # std_svc.h、std_svc_setup.c文件拷贝
    [ '1' ] && {
        echo "MR mr.ko for Monitor Registers Checking Logic in BL31 - hot patching is the helpless choice"
        f=vendor/sprd/proprietories-source/arm-trusted-firmware-1.3/include/services/std_svc.h
        copy_verify ${BASE}/${f} ${TOP}/${f} true
        f=vendor/sprd/proprietories-source/arm-trusted-firmware-1.3/services/std_svc/std_svc_setup.c
        copy_verify ${BASE}/${f} ${TOP}/${f} true
    }
else
    # TARGET_GPU_PLATFORM := soft in device/sprd/<SoC>/common/BoardCommon.mk
    [ "${TARGET_GPU_PLATFORM}" = "soft" ] && {
        f=build/make/tools/check_link_type.py
        copy_verify ${BASE}/${f} ${TOP}/${f} true
        f=frameworks/native/opengl/libagl/Android.bp
        copy_verify ${BASE}/${f}.tiny ${TOP}/${f} true
    }
fi

true


```



## 4. tiny-formatter/build/build_tiny_custom_modules.mk

- `tiny-formatter/build/build_tiny_custom_modules.mk`，该文件较简单，不再解析

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifneq ($(TINY),)
ifeq ($(ONE_SHOT_MAKEFILE),)
modules_list := $(CUSTOM_MODULES)
modules_desc := CUSTOM_MODULES
include $(TINY_BASE_DIR)/common/tiny.mk
CUSTOM_MODULES := $(modules_list)
# CUSTOM_MODULES := $(filter $(CUSTOM_MODULES), $(modules_list))
endif
endif

```

- `tiny-formatter/build/common/tiny.mk`:

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# ifeq ($(TINY_BUILD_VERSION), tiny) # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually
output_info ?= true
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_installed.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_installed.mk
modules := $(modules_list)

ifeq ($(output_info), true)
modules_count := $(words $(modules)) #打印$(modules_desc)的一些安装信息，此处是CUSTOM_MODULES
$(info {[ tiny $(modules_desc) modules $(modules_count) ])
$(foreach m, $(modules), $(info [ modules_to_install ] : $(m)) \
	$(eval LOCAL_PATH := $(shell \
					[ -f $(firstword $(ALL_MODULES.$(m).PATH))/Android.mk ] && echo "$(firstword $(ALL_MODULES.$(m).PATH))/Android.mk"; \
					[ -f $(firstword $(ALL_MODULES.$(m).PATH))/Android.bp ] && echo "$(firstword $(ALL_MODULES.$(m).PATH))/Android.bp")) \
    $(info $(LOCAL_PATH)) \
	$(info LOCAL_MODULE_TAGS =$(shell echo "$(ALL_MODULES.$(m).TAGS)" | sed 's/ /\n/g' | sort | uniq)) \
	$(info LOCAL_MODULE_CLASS =$(shell echo "$(ALL_MODULES.$(m).CLASS)" | sed 's/ /\n/g' | sort | uniq)) \
	$(foreach f, $(call module-installed-files, $(m)), $(info $(f) --$(m)-- $(LOCAL_PATH))) \
	$(info -- depends) \
	$(foreach f, $(ALL_MODULES.$(m).REQUIRED_FROM_TARGET), $(info $(f))))
$(warning [ tiny $(modules_desc) modules $(modules_count) ]})
endif

-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY).mk #包含zebu.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY).mk

ifeq (0,1)
modules_removed += \
	DownloadProvider \
	Browser2 \
	DeskClock \
	Email
endif

ifeq ($(output_info), true)
modules_removed := $(filter $(modules), $(modules_removed)) #把moduless中包含的modules_removed文件，modules_removed变量主要在zebu.mk中赋值，并不是所有的modules_removed都存在于moduless中，此处只把modules中包含的给过滤出来，并重新赋值给modules_removed
$(info {[ tiny $(modules_desc) modules try to remove $(words $(modules_removed)) ])
$(foreach m, $(modules_removed), $(info [ modules_removed ] : $(m)))
$(warning [ tiny $(modules_desc) modules try to remove $(words $(modules_removed)) ]})
endif

modules := $(filter-out $(modules_removed), $(modules)) # 从moduless中移除待删除的模块
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_only_installed.mk # 给modules添加一些需要安装的模块
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_only_installed.mk
modules_left := $(words $(modules)) # 统计modules中包含的模块数量
modules := $(filter $(modules_list), $(modules)) # 返回存在于modules和modules_list共有的模块并重新赋值给modules
modules_list := $(modules) # 重新统计modules中包含的模块数量

ifeq ($(output_info), true) #打印信息
$(info {[ tiny $(modules_desc) modules_installed $(modules_left), Removed $(shell bash -c 'echo "$(modules_count)-$(modules_left)" | bc') ])
$(foreach m, $(modules), $(info [ modules_installed ] : $(m)))
$(warning [ tiny $(modules_desc) modules_installed $(modules_left), Removed $(shell bash -c 'echo "$(modules_count)-$(modules_left)" | bc') ]})
endif
# endif # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually


```

- `tiny-formatter/model/zebu/zebu.mk`， `zebu.mk`主要是为modules_removed赋值，该值是待移除的模块

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
# Debug module
modules_removed += \
	libylog_32 ylogkat libylog \
	hcidump \
	mlogservice \
	collect_apr_server

ifeq ($(WITH_TOMBSTONED),)
modules_removed += \
	tombstoned debuggerd \
	crash_dump crash_dump_32 crash_dump.policy crash_dump.policy_32
endif

# Other module
modules_removed += \
	NotoSerifCJK-Regular.ttc \
	NotoSansCJK-Regular.ttc \
	NotoColorEmoji.ttf \
	NotoSansSymbols-Regular-Subsetted.ttf \
	NotoSansEgyptianHieroglyphs-Regular.ttf \
	NotoSansCuneiform-Regular.ttf \
	log_service \
	slogmodem \
	mdnsd \
	gatekeeperd \
	uncrypt \
	wificond \
	bugreport \
	incidentd \
	mtpd \
	racoon \
	statsd \
	traced \
	connmgr_cli \
	connmgr \
	engpc \
	audio.primary.default_32 \
	audio.primary.default \
	audio.primary.$(TARGET_BOARD_PLATFORM)_32 \
	audio.primary.$(TARGET_BOARD_PLATFORM) \
	usbd \
	blank_screen \
	bootstat \
	dumpstate \
	vendor.sprd.hardware.radio@1.0 \
	ju_ipsec_server \
	gpsd \
	libLLVM_android \
	libavatar_32 \
	libbluetooth \
	libbluetooth_32 \
	libmme_jrtc_32 \
	libcameraservice \
	libcameraservice_32 \
	libstagefright_soft_vpxenc_32 \
	libstagefright_soft_vpxenc.vendor_32 \
	libtflite \
	libtflite_32 \
	libchrome \
	libchrome_32 \
	android.hardware.radio@1.0 \
	android.hardware.radio@1.0_32 \
	android.hardware.radio@1.1 \
	android.hardware.radio@1.1_32 \
	libRSCpuRef \
	libRSCpuRef_32 \
	libcamsensor \
	libcamsensor_32 \
	libSprdImageFilter \
	libSprdImageFilter_32 \
	libwvhidl_32 \
	libSegLite \
	libSegLite_32 \
	wpa_supplicant \
	wpa_supplicant.conf \
	vendor.sprd.hardware.radio@1.0.vendor \
	vendor.sprd.hardware.radio@1.0.vendor_32 \
	libsprdscenedetect \
	libsprdscenedetect_32 \
	libkeypadnpi_32 \
	liblcdnpi_32 \
	gatord

# Device board module
modules_removed += \
	android.hardware.biometrics.fingerprint@2.1-service \
	android.hardware.bluetooth@1.0-service.unisoc \
	android.hardware.camera.provider@2.4-service_32 \
	android.hardware.dumpstate@1.0-service \
	vendor.sprd.hardware.aprd@1.0-service \
	vendor.sprd.hardware.aprd@1.0-impl_32 \
	vendor.sprd.hardware.aprd@1.0-impl \
	vendor.sprd.hardware.aprd@1.0.vendor \
	vendor.sprd.hardware.aprd@1.0.vendor_32 \
	vendor.sprd.hardware.thermal@1.0 \
	android.hardware.thermal@1.1 \
	vndservice \
	vndservicemanager \
	urild \
	librilcore \
	libimpl-ril \
	librilutils \
	libatci \
	libFactoryRadioTest \
	charge \
	srtd \
	thermald \
	hostapd \
	libsrmi_32 \
	libsrmi \
	srmi_proxyd  \
	CtsShimPrebuilt \
	CtsShimPrivPrebuilt \
	android.hardware.vibrator@1.0-service \
	vendor.sprd.hardware.log@1.0-service \
	gps.default \
	gps.default_32 \
	libgpspc_32 \
	collect_apr \
	aprctl \
	apr.conf.etc \
	apr.cmcc.conf \
	apr.cmcc.conf.user \
	ylogsource.conf

# xml module
modules_removed += \
	device_manifest.xml

# start optimization module
modules_removed += \
	Traceur \
	buffdump.conf \
	cndaemon \
	com.android.apex.cts.shim.v1_prebuilt \
	iptables \
	ip6tables \
	resize2fs \
	cmd_services

## follow modules, can not get install files
#modules_removed += \
#   	ylog_common \
#	cplogctl \
#	iqfeed \
#	cameraserver \
#	minicamera \
#	modem_control \
#	refnotify \
#	dhcp6s \
#	tiny_firewall.sh \
#	data_rps.sh \
#	netbox.sh \
#	dataLogDaemon \
#	ims_bridged \
#	ip_monitor.sh \
#	libavatar \
#	libmme_jrtc \
#	android.hardware.radio@1.0.vendor \
#	android.hardware.radio@1.0.vendor_32 \
#	android.hardware.radio@1.1.vendor \
#	android.hardware.radio@1.1.vendor_32 \
#	android.hardware.radio@1.2.vendor \
#	android.hardware.radio@1.2.vendor_32 \
#	libRSCpuRef.vendor \
#	libRSCpuRef.vendor_32 \
#	libsprdfaceid \
#	cp_diskserver \
#	phasecheckserver \
#	factorytest \
#	ext_data \
#	sprdstorageproxyd \
#	rpmbserver \
#	tsupplicant

ifneq ($(USE_SPRD_HWCOMPOSER),true)
$(warning $(shell echo -e "\033[31mREMOVE hwcomposer.$(TARGET_BOARD_PLATFORM) forcely, then android launcher is ok without HWC & GPU ##############################\033[0m"))
modules_removed += \
	hwcomposer.$(TARGET_BOARD_PLATFORM)
$(warning $(shell echo -e "\033[31mREMOVE hwcomposer.$(TARGET_BOARD_PLATFORM) forcely, then android launcher is ok without HWC & GPU ##############################\033[0m"))
endif
endif


```

- `tiny-formatter/model/zebu/zebu_only_installed.mk`，该文件主要向modules变量添加需要安装的模块

```m
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
# modules := zebu zebu.envsetup zebu.auto \
#	zebu.antutu7apk.no3D zebu.antutu7apk.3D \

endif

```



## 5. tiny-formatter/build/build_tiny_product_modules.mk

- `tiny-formatter/build/build_tiny_product_modules.mk`，build_tiny_product_modules.mk文件中主要是对product_MODULES进行处理，与build_tiny_custom_modules.mk文件中对CUSTOM_MODULES处理的流程基本相同，此处对模块移除的过程（以下4-9行）具体分析。

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifneq ($(TINY),)
ifeq ($(ONE_SHOT_MAKEFILE),)
modules_list := $(product_MODULES)
modules_desc := product_MODULES
include $(TINY_BASE_DIR)/common/tiny.mk
product_MODULES := $(modules_list)
# 通过调用module-installed-files函数获取product_MODULES中各模块的安装文件，并将out/host目录下的文件从这些安装文件中移除，最后赋值给变量product_target_FILES
product_target_FILES =  $(filter-out $(HOST_OUT_ROOT)/%,$(call module-installed-files, $(product_MODULES)))
# 通过调用resolve-product-relative-paths函数将product_target_FILES中的安装文件所关联的文件添加进来，并重新赋值给product_target_FILES变量
product_target_FILES += $(call resolve-product-relative-paths, $(foreach cf,$(call get-product-var,$(INTERNAL_PRODUCT),PRODUCT_COPY_FILES),$(call word-colon,2,$(cf))))
# product_MODULES := $(filter $(product_MODULES), $(modules_list))
endif
endif

```



## 6. tiny-formatter/build/build_tiny_product_copy_files.mk

- `tiny-formatter/build/build_tiny_product_copy_files.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifneq ($(TINY),)
ifeq ($(ONE_SHOT_MAKEFILE),)
include $(TINY_BASE_DIR)/common/tiny_product_copy_files.mk
# 对tiny_unique_product_copy_files_pairs进一步处理，如果tiny_unique_product_copy_files_pairs中的文件对（源文件、目标文件）不在TINY_PRODUCT_COPY_FILES中，则将该文件对重新赋值给tiny_unique_product_copy_files_pairs
tiny_unique_product_copy_files_pairs :=
$(foreach cf,$(TINY_PRODUCT_COPY_FILES), \
    $(if $(filter $(tiny_unique_product_copy_files_pairs),$(cf)),,\
        $(eval tiny_unique_product_copy_files_pairs += $(cf))))
unique_product_copy_files_pairs := $(tiny_unique_product_copy_files_pairs) $(unique_product_copy_files_pairs)
endif
endif

```

- `tiny-formatter/build/common/tiny_product_copy_files.mk`，主要是包含zebu_product_copy_files.mk

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_product_copy_files.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_product_copy_files.mk

```

- `tiny-formatter/model/zebu_product_copy_files.mk`，添加拷贝文件对到TINY_PRODUCT_COPY_FILES变量

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
TINY_PRODUCT_COPY_FILES += \
	$(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/android/common/image/vendor/etc/permissions/handheld_core_hardware.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/handheld_core_hardware.xml
# when some files can not copy with TINY_PRODUCT_COPY_FILES method, call zebu_copy_files.sh for these files copy in zebu_files_must_be_appened.mk
endif

```



## 7. tiny-formatter/build/build_tiny_files.mk

- `tiny-formatter/build/build_tiny_files.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifneq ($(TINY),)
ifeq ($(ONE_SHOT_MAKEFILE),)
# 获取所有安装模块文件（ALL_DEFAULT_INSTALLED_MODULES），将其赋值给files_to_install
files_to_install := $(ALL_DEFAULT_INSTALLED_MODULES)
# tiny-formatter/build/common/tiny_files.mk会对files_to_install做进一步处理
include $(TINY_BASE_DIR)/common/tiny_files.mk
# 将处理后的files_to_install重新赋值给ALL_DEFAULT_INSTALLED_MODULES
ALL_DEFAULT_INSTALLED_MODULES := $(files_to_install)
# ALL_DEFAULT_INSTALLED_MODULES := $(filter $(ALL_DEFAULT_INSTALLED_MODULES), $(files_to_install))
endif
endif

```

- `tiny-formatter/build/common/tiny_files.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# ifeq ($(TINY_BUILD_VERSION), tiny) # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually
output_info ?= false
# 把PRODUCT_OUT（如sprdroidr_trunk/out/target/product/s9863a1h10）目录下的所有文件赋值给FILES_TO_INSTALL_PRODUCT
FILES_TO_INSTALL_PRODUCT := $(filter $(PRODUCT_OUT)/%, $(files_to_install))
# 把除去PRODUCT_OUT（如sprdroidr_trunk/out/target/product/s9863a1h10）目录下的所有文件的其他文件赋值给FILES_TO_INSTALL_OTHERS
FILES_TO_INSTALL_OTHERS := $(filter-out $(PRODUCT_OUT)/%, $(files_to_install))
# 获取files_to_install变量中的文件数量
files_to_install_count := $(words $(files_to_install))
# 将FILES_TO_INSTALL_PRODUCT变量中的所有文件的前缀（如sprdroidr_trunk/out/target/product/s9863a1h10）去掉
files_to_install := $(patsubst $(PRODUCT_OUT)/%,/%,$(FILES_TO_INSTALL_PRODUCT))
# zebu_files_installed.mk文件目前暂不存在，将来可能会添加
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_files_installed.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_files_installed.mk
# 保存files_to_install到files_to_install_raw
files_to_install_raw := $(files_to_install)

# 打印files_to_install信息
ifeq ($(output_info), true)
$(info {[ tiny files_to_install $(files_to_install_count) ])
$(foreach m, $(files_to_install), $(info [ files_to_install ] : $(m)))
$(warning [ tiny files_to_install $(files_to_install_count) ]})
endif

# 包含tiny-formatter/model/zebu/zebu_files.mk
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_files.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_files.mk

ifeq (0,1)
# files_not_to_install += $(addprefix %, vdex odex oat art prof apk so rc ogg ttf txt kl bin jar otf png ko xml hyb conf)
# files_not_to_install += /system/bin/%
files_not_to_install := /system/%
endif

# 打印移除的文件files_not_to_install
ifeq ($(output_info), true)
# files_not_to_install := $(filter $(files_to_install), $(files_not_to_install)) # /system/% will be removed, so drop this line
$(info {[ tiny files_not_to_install $(words $(files_not_to_install)) ])
$(foreach m, $(files_not_to_install), $(info [ files_not_to_install ] : $(m)))
$(warning [ tiny files_not_to_install $(words $(files_not_to_install)) ]})
endif

# 从files_to_install中将包含的所有待移除文件清单移除除去，并重新赋值给files_to_install
files_to_install := $(filter-out $(files_not_to_install), $(files_to_install))
# 添加需要安装的文件
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_files_only_installed.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_files_only_installed.mk
modules_desc := 'must be appened'
# 添加需要安装的模块文件
-include $(TINY_BASE_DIR)/common/tiny_modules_must_be_appened.mk
-include $(TINY_BASE_DIR)/common/tiny_files_must_be_appened.mk
# ifeq (0,1)
# FILES_TO_INSTALL_OTHERS += $(filter-out $(PRODUCT_OUT)/%, $(modules_must_be_appended_FILES))
# FILES_TO_INSTALL_PRODUCT_must_be_appened := $(filter $(PRODUCT_OUT)/%, $(modules_must_be_appended_FILES))
# files_to_install_must_be_appened := $(patsubst $(PRODUCT_OUT)/%,/%,$(FILES_TO_INSTALL_PRODUCT_must_be_appened))
# files_to_install := $(filter $(files_to_install_raw), $(files_to_install) $(files_to_install_must_be_appened))
# endif
# 获取files_to_install_raw和files_to_install共同的文件清单，然后重新赋值给files_to_install
files_to_install := $(filter $(files_to_install_raw), $(files_to_install))
# 给files_to_install中文件清单添加前缀PRODUCT_OUT（如sprdroidr_trunk/out/target/product/s9863a1h10），然后合并FILES_TO_INSTALL_OTHERS、files_to_install、modules_must_be_appended_FILES三个变量，再赋值给files_to_install
files_to_install := $(FILES_TO_INSTALL_OTHERS) $(addprefix $(PRODUCT_OUT), $(files_to_install)) $(modules_must_be_appended_FILES)
# 统计files_to_install中文件数量
files_installed_count := $(words $(files_to_install))

# 打印files_to_install信息
ifeq ($(output_info), true)
$(info {[ tiny files_installed $(files_installed_count), Removed $(shell bash -c 'echo "$(files_to_install_count)-$(files_installed_count)" | bc') ])
$(foreach m, $(files_to_install), $(info [ files_installed ] : $(m)))
$(warning [ tiny files_installed $(files_installed_count), Removed $(shell bash -c 'echo "$(files_to_install_count)-$(files_installed_count)" | bc') ]})
endif
# endif # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually


```

- `tiny-formatter/model/zebu/zebu_files.mk`，该文件内主要给files_not_to_install赋值，其中`%`表示该目录下所有文件

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
# app/priv-app
files_not_to_install += \
	/system/app/% \
	/system/priv-app/% \
	/system/preloadapp/% \
	/system/vital-app/% \
	/system/overlay/% \
	/vendor/app/% \
	/vendor/priv-app/% \
	/vendor/preloadapp/% \
	/vendor/overlay/% \
	/vendor/vital-app/% \
	/product/app/% \
	/product/priv-app/% \
	/product/preloadapp/% \
	/product/overlay/% \
	/product/vital-app/% \
	/oem/app/% \
	/oem/priv-app/% \
	/oem/preloadapp/% \
	/oem/overlay/% \
	/oem/vital-app/% \
	/odm/app/% \
	/odm/priv-app/% \
	/odm/preloadapp/% \
	/odm/overlay/% \
	/odm/vital-app/%

# Other files
files_not_to_install += \
	/system/etc/init/coredump.rc \
	/system/etc/init/perfprofd.rc \
	/system/etc/init/cgroup_blkio.rc \
	/system/etc/init/init-debug.rc \
	/system/etc/init/logtagd.rc \
	/vendor/etc/init/wcn.rc \
	/vendor/etc/init/autotest.rc \
	/vendor/etc/init/ylog_lite.rc \
	/vendor/etc/init/init.leddrv.rc \
	/vendor/etc/init/init.sunwave.rc \
	/vendor/etc/init/init.vibdrv.rc \
	/vendor/etc/init/init.tcs3430.rc \
	/vendor/etc/permissions/% \
	/system/etc/permissions/android.software.managed_users.xml \
	/vendor/lib64/libsupl.so \
	/vendor/lib/libsupl.so \
	/vendor/lib64/liblcscp.so \
	/vendor/lib/liblcscp.so \
	/vendor/etc/rx_data.pcm \
	/system/xbin/simpleperf \
	/system/xbin/simpleperf32 \
	/vendor/lib/libengbt.so \
	/vendor/lib64/libengbt.so \
	/system/bin/collect_apr \
	/vendor/etc/init/camera.rc \
	/vendor/sprd/proprietories-source/autotest/autotest.pc

# # native
# ifeq ($(TINY_ARGS), native)
# WITH_ADB ?= false # Disable adb by default in tiny@native mode
# ifneq ($(WITH_ADB), true) # Without adb, following files should be removed
# files_not_to_install += \
# 	/root/init.rc \
# 	/root/init.usb.rc \
# 	/root/init.usb.configfs.rc \
# 	/root/init.common.rc \
# 	/root/init.storage.rc \
# 	/root/init.ram.rc \
# 	/root/init.lovelyfonts.rc \
# 	/root/init.recovery.$(TARGET_BOARD).rc \
# 	/root/init.$(TARGET_BOARD).usb.rc \
# 	/root/init.$(TARGET_BOARD).rc \
# 	/root/init.zygote64.rc /root/init.zygote64_32.rc /root/init.zygote32.rc /root/init.zygote32_64.rc \
# 	/system/build.prop \
# 	/vendor/build.prop \
# 	/vendor/etc/init/% \
# 	/system/etc/init/%
# endif
# endif

ifeq ($(TARGET_GPU_PLATFORM),soft)
files_not_to_install += \
	/vendor/lib/modules/pvrsrvkm.ko
endif
endif


```

- `tiny-formatter/model/zebu/zebu_files_only_installed.mk`，将需要添加的文件赋值给files_to_install

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
# 6-15行主要是向files_to_install变量中添加TINY_PRODUCT_COPY_FILES文件中的拷贝文件
#############################################################
$(foreach f, $(TINY_PRODUCT_COPY_FILES),\
 $(eval _cpm_words := $(subst :,$(empty) $(empty),$(f)))\
    $(eval _cpm_word1 := $(word 1,$(_cpm_words)))\
    $(eval _cpm_word2 := $(word 2,$(_cpm_words)))\
    $(if $(_cpm_word2),\
        $(eval files_to_install += /$(_cpm_word2))\
        $(warning files_installed forced = /$(_cpm_word2))\
        ))
#############################################################
files_to_install += \

endif

```

- `tiny-formatter/build/common/tiny_modules_must_be_appened.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# 包含tiny-formatter/model/mboot/mboot_modules_must_be_appened.mk
-include $(TINY_BASE_DIR_ROOT)/model/mboot/mboot_modules_must_be_appened.mk
# 包含tiny-formatter/model/zebu(haps)/zebu(haps)_modules_must_be_appened.mk
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_modules_must_be_appened.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_modules_must_be_appened.mk
# 获取ALL_MODULES、modules_must_be_appended共有的模块，然后重新赋值给modules_must_be_appended
modules_must_be_appended := $(filter $(ALL_MODULES), $(modules_must_be_appended))
# 统计modules_must_be_appended包含的模块数量
modules_count := $(words $(modules_must_be_appended))
# 打印modules_must_be_appended模块信息
$(info {[ tiny $(modules_desc) modules $(modules_count) ])
$(foreach m, $(modules_must_be_appended), $(info [ modules_must_be_appended ] : $(m)) \
	$(info LOCAL_PATH = $(shell \
					[ -f $(firstword $(ALL_MODULES.$(m).PATH))/Android.mk ] && echo "$(firstword $(ALL_MODULES.$(m).PATH))/Android.mk"; \
					[ -f $(firstword $(ALL_MODULES.$(m).PATH))/Android.bp ] && echo "$(firstword $(ALL_MODULES.$(m).PATH))/Android.bp")) \
	$(info LOCAL_MODULE_TAGS =$(shell echo "$(ALL_MODULES.$(m).TAGS)" | sed 's/ /\n/g' | sort | uniq)) \
	$(info LOCAL_MODULE_CLASS =$(shell echo "$(ALL_MODULES.$(m).CLASS)" | sed 's/ /\n/g' | sort | uniq)) \
	$(foreach f, $(call module-installed-files, $(m)), $(info $(f))) \
	$(foreach f, $(ALL_MODULES.$(m).REQUIRED_FROME_TARGET), $(info $(f))))
# 调用module-installed-files函数获取modules_must_be_appended内模块的所有安装文件，并赋值给modules_must_be_appended_FILES
modules_must_be_appended_FILES := $(call module-installed-files, $(modules_must_be_appended))
$(warning [ tiny $(modules_desc) modules $(modules_count) ]})


```

- `tiny-formatter/model/mboot/mboot_modules_must_be_appened.mk`，如果编译的是mboot版本，则向modules_must_be_appended添加mboot相关模块

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# root
ifeq ($(TINY_ARGS), mboot)
modules_must_be_appended += \
	init adbd toybox busybox adbd-setup.sh adbd-uninstall.sh

# mboot
modules_must_be_appended += mboot.envsetup
endif

```

- `tiny-formatter/model/zebu/zebu_modules_must_be_appened.mk`，向modules_must_be_appended变量添加模块，这些模块是必须要安装的

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# root
modules_must_be_appended += \
	init adbd toybox busybox adbd-setup.sh adbd-uninstall.sh mr.ko

# SELinux
modules_must_be_appended += \
	plat_file_contexts \
	plat_property_contexts \
	plat_service_contexts \
	plat_seapp_contexts

# zebu
modules_must_be_appended += zebu zebu.envsetup zebu.auto zebu.install \
	zebu.antutu7apk.no3D zebu.antutu7apk.3D zebu.antutu6apk

# app/priv-app
modules_must_be_appended += \
	SettingsProvider \
	Shell \
	webview \
	ims \
	TeleService \
	ExtShared \
	Settings \
	GooglePermissionControllerPrebuilt \
	GoogleExtServicesPrebuilt \
	FusedLocation \
	ModuleMetadata

ifeq ($(TARGET_BUILD_VERSION),gsm)
modules_must_be_appended += PermissionController
else
modules_must_be_appended += PackageInstaller
endif

# SystemUI export WITH_SYSTEMUI=true
WITH_SYSTEMUI := true
ifeq ($(WITH_SYSTEMUI), true)
# Feature app_widgets must be added too in vendor/etc/permissions/handheld_core_hardware.xml
# <feature name="android.software.app_widgets" />
# console:/ # dumpsys package f
# android.software.app_widgets
modules_must_be_appended += \
	Launcher3QuickStep \
	SystemUI
endif

ifeq ($(TARGET_GPU_PLATFORM),soft)
modules_must_be_appended += \
	libGLES_android \
	libEGL       \
	libGLESv1_CM \
	libGLESv2
endif


```

- `tiny-formatter/build/common/tiny_files_must_be_appened.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
-include $(TINY_BASE_DIR_ROOT)/model/mboot/mboot_files_must_be_appened.mk
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_files_must_be_appened.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_files_must_be_appened.mk
files_to_install += $(files_must_be_appended)

```

- `tiny-formatter/model/mboot/mboot_files_must_be_appened.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# mboot - busybox
ifeq ($(TINY_ARGS), mboot)
# From build/core/Makefile
# BUILT_RAMDISK_TARGET := $(PRODUCT_OUT)/ramdisk.img
# We just build this directly to the install location.
# INSTALLED_RAMDISK_TARGET := $(BUILT_RAMDISK_TARGET)
#***************************************************************************
#* Change .dts chosen@bootargs from root=/dev/mmcblk0p30 to root=/dev/ram0 *
#* then ramdisk.img will be mounted as root dir replacing 9.0 system       *
#* $ export WITH_RAMDISK=true; make bootimage -j32                         *
#* If you want to let busybox as init and Android 9.0 system.img as rootfs *
#* you can keep .dts chosen@bootargs root=/dev/mmcblk0p30                  *
#* $ make -j32                                                             *
#***************************************************************************
# mboot - busybox
# 20-24行设置mboot值，并使ramdisk.img，boot.img，system.img，system_image_info.txt都依赖于mboot
mboot := $(PRODUCT_OUT)/mboot.bin
$(PRODUCT_OUT)/ramdisk.img: $(mboot)
$(PRODUCT_OUT)/boot.img: $(mboot)
$(PRODUCT_OUT)/system.img: $(mboot)
$(call intermediates-dir-for,PACKAGING,systemimage)/system_image_info.txt: $(mboot)
# build/make/tools/releasetools/build_image.py out/target/product/sp9832e_1h10/system out/target/product/sp9832e_1h10/obj/PACKAGING/systemimage_intermediates/system_image_info.txt out/target/product/sp9832e_1h10/obj/PACKAGING/systemimage_intermediates/system.img out/target/product/sp9832e_1h10/system
# BOARD_USES_FULL_RECOVERY_IMAGE := true# We carry a full copy of the recovery image - no patching needed -- build/core/Makefile
# 包含tiny-formatter/model/mboot/mboot.mk
-include $(TINY_BASE_DIR_ROOT)/model/mboot/mboot.mk
# 删除PRODUCT_OUT（例如sprdroidr_trunk/out/target/product/s9863a1h10）目录下的root目录
$(shell rm -rf $(PRODUCT_OUT)/root)
# 给MBOOT_INTERNAL_RAMDISK_FILES赋值，包括TARGET_ROOT_OUT下所有文件，ALL_GENERATED_SOURCES，ALL_DEFAULT_INSTALLED_MODULES，以及modules_must_be_appended_FILES
MBOOT_INTERNAL_RAMDISK_FILES := $(filter $(TARGET_ROOT_OUT)/%, \
	$(ALL_GENERATED_SOURCES) \
	$(ALL_DEFAULT_INSTALLED_MODULES) \
	$(modules_must_be_appended_FILES))

# 初始化MBOOT_DEPENDENCIES为空
MBOOT_DEPENDENCIES :=
# 从TARGET_DEVICE_DIR中分别获取TARGET_DEVICE_SOC和TARGET_DEVICE_BOARD
TARGET_DEVICE_SOC := $(word 3, $(subst /,$(empty) $(empty), $(TARGET_DEVICE_DIR)))# device/<vendor>/<soc>/<board>
TARGET_DEVICE_BOARD := $(word 4, $(subst /,$(empty) $(empty), $(TARGET_DEVICE_DIR)))# device/<vendor>/<soc>/<board>
# $(warning TARGET_DEVICE_SOC=$(TARGET_DEVICE_SOC))
# ifeq ($(WITH_ADB), true)
# 给MBOOT_DEPENDENCIES添加值
MBOOT_DEPENDENCIES += $(TARGET_OUT)/bin/adbd $(TARGET_OUT)/bin/init $(TARGET_OUT)/bin/ueventd
MBOOT_DEPENDENCIES += $(TARGET_RAMDISK_OUT)/init # For ramdisk.img
# endif
#.PHONY: mboot
# 配置mboot依赖项
$(mboot): $(MBOOT_INTERNAL_RAMDISK_FILES) $(MBOOT_DEPENDENCIES)
	# 调用pretty函数，打印后面的第一个参数，即"Target mboot image: $@"
	$(call pretty,"Target mboot image: $@")
	# $(hide) if [ -d $(TARGET_ROOT_OUT) ]; then rm -rf $(TARGET_ROOT_OUT); else true; fi
	# $(hide) \
	# if [ -d $(TARGET_ROOT_OUT) ]; then \
	# 	rm -rf $(TARGET_ROOT_OUT); \
	# else \
	# 	true; \
	# fi
	# 创建mboot.bin文件
	$(hide) touch $(mboot)
	# 创建root目录
	$(hide) mkdir -p $(TARGET_ROOT_OUT)
	# 调用model/mboot/install.sh脚本
	$(hide) \
		TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
		TINY=$(TINY) \
		TARGET_ARCH=$(TARGET_ARCH) \
		TARGET_OUT=$(TARGET_OUT) \
		TARGET_OUT_VENDOR=$(TARGET_OUT_VENDOR) \
		TARGET_ROOT_OUT=$(TARGET_ROOT_OUT) \
		TARGET_OUT_INTERMEDIATES=$(TARGET_OUT_INTERMEDIATES) \
		TARGET_DEVICE_SOC=$(TARGET_DEVICE_SOC) \
		TARGET_BOARD_PLATFORM=x$(TARGET_BOARD_PLATFORM) \
		TARGET_DEVICE_BOARD=$(TARGET_DEVICE_BOARD) \
		WITH_FULL=$(WITH_FULL) \
		TARGET_PRODUCT=$(TARGET_PRODUCT) \
		TARGET_RAMDISK_OUT=$(TARGET_RAMDISK_OUT) \
		TARGET_MBOOT_VERSION=$(TARGET_MBOOT_VERSION) \
		WITH_RAMDISK=x$(WITH_RAMDISK) \
		$(TINY_BASE_DIR_ROOT)/model/mboot/install.sh

# ifeq (,$(filter true, $(TARGET_NO_KERNEL) $(TARGET_NO_RECOVERY)))
# BOARD_RECOVERY_IMAGE_PREPARE := \
# 	$(BOARD_RECOVERY_IMAGE_PREPARE) \
# 	mv $(TARGET_RECOVERY_ROOT_OUT)/msystem/metc/* $(TARGET_RECOVERY_ROOT_OUT)/etc; \
# 	rmdir $(TARGET_RECOVERY_ROOT_OUT)/msystem/metc; \
# 	true;
#
# #.PHONY: mboot-recovery.img
# mboot-recovery := $(PRODUCT_OUT)/mboot-recovery.img
# $(PRODUCT_OUT)/recovery.img: $(mboot-recovery)
# $(mboot-recovery): $(PRODUCT_OUT)/boot.img
# 	# INSTALLED_RECOVERYIMAGE_TARGET := $(PRODUCT_OUT)/recovery.img
# 	# mboot/sbin size will exceeded BOARD_RECOVERYIMAGE_PARTITION_SIZE, build error like : recovery.img too large (36874240 > 36630528)
# 	$(call pretty,"Target mboot-recovery image: $@")
# 	$(hide) touch $(mboot-recovery)
# 	$(hide) \
# 		TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
# 		TINY=$(TINY) \
# 		TARGET_ARCH=$(TARGET_ARCH) \
# 		TARGET_OUT=$(TARGET_OUT) \
# 		TARGET_ROOT_OUT=$(TARGET_ROOT_OUT) \
# 		TARGET_OUT_INTERMEDIATES=$(TARGET_OUT_INTERMEDIATES) \
# 		TARGET_DEVICE_SOC=$(TARGET_DEVICE_SOC) \
# 		TARGET_BOARD_PLATFORM=x$(TARGET_BOARD_PLATFORM) \
# 		TARGET_DEVICE_BOARD=$(TARGET_DEVICE_BOARD) \
# 		WITH_FULL=$(WITH_FULL) \
# 		TARGET_PRODUCT=$(TARGET_PRODUCT) \
# 		TARGET_RAMDISK_OUT=$(TARGET_RAMDISK_OUT) \
#		TARGET_MBOOT_VERSION=$(TARGET_MBOOT_VERSION) \
# 		WITH_RAMDISK=x$(WITH_RAMDISK) \
# 		MODE=recovery \
# 		$(TINY_BASE_DIR_ROOT)/model/mboot/install.sh
#
# #.PHONY: mboot-recovery-done.img
# mboot-recovery-done :=  $(PRODUCT_OUT)/mboot-recovery-done.img
# $(DEFAULT_GOAL): $(mboot-recovery-done)
# $(mboot-recovery-done): $(PRODUCT_OUT)/recovery.img
# 	# INSTALLED_RECOVERYIMAGE_TARGET := $(PRODUCT_OUT)/recovery.img
# 	# mboot/sbin size will exceeded BOARD_RECOVERYIMAGE_PARTITION_SIZE, build error like : recovery.img too large (36874240 > 36630528)
# 	$(call pretty,"Target mboot-recovery-done image: $@")
# 	$(hide) touch $(mboot-recovery-done)
# 	$(hide) \
# 		TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
# 		TINY=$(TINY) \
# 		TARGET_ARCH=$(TARGET_ARCH) \
# 		TARGET_OUT=$(TARGET_OUT) \
# 		TARGET_ROOT_OUT=$(TARGET_ROOT_OUT) \
# 		TARGET_OUT_INTERMEDIATES=$(TARGET_OUT_INTERMEDIATES) \
# 		TARGET_DEVICE_SOC=$(TARGET_DEVICE_SOC) \
# 		TARGET_BOARD_PLATFORM=x$(TARGET_BOARD_PLATFORM) \
# 		TARGET_DEVICE_BOARD=$(TARGET_DEVICE_BOARD) \
# 		WITH_FULL=$(WITH_FULL) \
# 		TARGET_PRODUCT=$(TARGET_PRODUCT) \
# 		TARGET_RAMDISK_OUT=$(TARGET_RAMDISK_OUT) \
# 		WITH_RAMDISK=x$(WITH_RAMDISK) \
# 		MODE=recovery_done \
# 		$(TINY_BASE_DIR_ROOT)/model/mboot/install.sh
# endif # ifeq(,$(filter true, $(TARGET_NO_KERNEL) $(TARGET_NO_RECOVERY)))
#
endif # !ifeq ($(TINY_ARGS), mboot)


```

- `tiny-formatter/model/mboot/mboot.mk`，该make文件只是打印了一些log，没有其他具体操作

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# mboot - busybox
ifeq ($(TINY_ARGS), mboot)
# MAKECMDGOALS := bootimage $(MAKECMDGOALS)
# TARGET_NO_RECOVERY := true# No recovery.img
$(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
$(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
$(warning )
$(warning )
$(warning )
$(warning $(shell echo -e "\033[4;35mYou can export WITH_FULL=true; lunch xxxx-tiny@zebu,mboot; make -j32; to build a full android images; then mboot# \033[0m\033[32mandroid.start \033[0m\033[4;35mto debug Android 9/10/11/12/13/xxx\033[0m"))
ifeq ($(WITH_RAMDISK), true)
BOARD_BUILD_SYSTEM_ROOT_IMAGE := false# Then ramdisk.img will be appended like : INTERNAL_BOOTIMAGE_ARGS += --ramdisk $(INSTALLED_RAMDISK_TARGET) when $(MKBOOTIMG) mkbootimg
$(warning $(shell echo -e "\033[4;31mkernel/arch/arm64/boot/dts/xxxx/xxxx.dts Change .dts chosen@bootargs from root=/dev/mmcblk0p30 to root=/dev/ram0\033[0m"))
else
#BOARD_DISABLE_SELINUX_FC := true# Need build/core ea68adc6681985026601b8fb790aad859e35003c - http://review.source.spreadtrum.com/gerrit/#/c/535463/
$(warning $(shell echo -e "\033[4;31mYou can export WITH_RAMDISK=true; make -j32; to build ramdisk.img into boot.img, but should change kernel/arch/arm64/boot/dts/xxxx/xxxx.dts .dts chosen@bootargs from root=/dev/mmcblk0p30 to root=/dev/ram0\033[0m"))
endif
$(warning )
$(warning )
$(warning )
$(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
$(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
endif


```

- `tiny-formatter/model/mboot/install.sh`

```shell
#!/bin/bash
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# env >&2
function get_pwd_abs() {
lcurdir=$1
while [ "${lcurdir}" != "/" ]; do
    if [ -e ${lcurdir}/$2 ]; then
        echo "${lcurdir}"
        break;
    fi
    lcurdir=$(readlink -f ${lcurdir}/..)
done
}

BUSYBOX_INIT= # 安装busybox init作为第一个init, 放到root/和ramdisk/下 2019/12/15 18:39:16 luther
# 配置一些变量值，以下为各变量参考值
#TARGET_ARCH=arm64
#TINY_BASE_DIR_ROOT=vendor/sprd/proprietories-source/tiny-formatter
#TARGET_ROOT_OUT=out/target/product/s9863a1h10/root
#TARGET_OUT=out/target/product/s9863a1h10/system
#MBOOT=vendor/sprd/proprietories-source/tiny-formatter/model/mboot
#ENV=out/target/product/s9863a1h10/root/mboot/env-setup

ROOT_ABS=`pwd`
[ "${TARGET_ARCH}" ] || TARGET_ARCH=arm64
[ "${TINY_BASE_DIR_ROOT}" ] || TINY_BASE_DIR_ROOT="$(get_pwd_abs $(dirname `readlink -f $0`) model/mboot)"
[ "${TARGET_ROOT_OUT}" ] || { echo "TARGET_ROOT_OUT must be defined EX. TARGET_ROOT_OUT=luther-OS-root-dir mboot-deploy-as-root-stub-os.sh"; exit 0; }
[ -d ${TARGET_ROOT_OUT} ] || mkdir -p ${TARGET_ROOT_OUT}
[ "${TARGET_OUT}" ] || TARGET_OUT=${TARGET_ROOT_OUT}

MBOOT=${TINY_BASE_DIR_ROOT}/model/mboot
ENV=${TARGET_ROOT_OUT}/mboot/env-setup

# 1. root
# renames=(init)
# for r in ${renames[@]}; do
#     [ -L ${TARGET_ROOT_OUT}/${r} -o -e ${TARGET_ROOT_OUT}/${r} ] && mv ${TARGET_ROOT_OUT}/${r} ${TARGET_ROOT_OUT}/android.${r}
# done
## vendor/sprd/proprietories-source/tiny-formatter/model/mboot/arm64目录下所有文件拷贝到out/target/product/s9863a1h10/root目录下，该目录下主要包括两个链接文件 msystem，init，一个目录sbin，如下：
## msystem -> /sbin/msystem
## init -> /msystem/bin/busybox
## sbin
cp -a ${MBOOT}/${TARGET_ARCH}/* ${TARGET_ROOT_OUT}
## vendor/sprd/proprietories-source/tiny-formatter/model/mboot/tool/android/* 目录下所有文件拷贝到out/target/product/s9863a1h10/root/sbin目录下， 该目录下主要是一些可执行文件，如下：android.start chcon-init_exec-label env.sh  ka lz mboot-auto2 mso-20M.img.tar.bz2 ps rw strace-all android.start.first.stage dt-node-list k ll mboot-auto mboot-chroot-hook mso.img.tar.bz2 reboot sreboot systrace
cp ${MBOOT}/tool/android/* ${TARGET_ROOT_OUT}/sbin/

[ 1 ] && {
	## 删除out/target/product/s9863a1h10/root/sbin目录下的busybox gawk bash文件
    for REMOVE in sbin/busybox sbin/gawk sbin/bash; do # 因为recovery.img超出分区大小，在不修改分区的情况下，删除不常用的工具 2019/10/23 17:29:37 luther
        rm -f ${TARGET_ROOT_OUT}/${REMOVE}
    done
    ## 定义out/target/product/s9863a1h10/root/sbin/busybox链接文件，使其链接到/msystem/bin/busybox
    ln -s /msystem/bin/busybox ${TARGET_ROOT_OUT}/sbin/busybox
    ## 此处为安装busybox init作为第一个init, 放到root/和ramdisk/下，目前BUSYBOX_INIT为空，不执行
    [ "${BUSYBOX_INIT}" ] && {
        rm -f ${TARGET_ROOT_OUT}/init
        ln -s /msystem/bin/busybox ${TARGET_ROOT_OUT}/init
    }
}
## 定义out/target/product/s9863a1h10/root/sbin/android.start链接文件，使其链接到/sbin/android.start
ln -s /sbin/android.start ${TARGET_ROOT_OUT}/android.start

# 给console service修改名称和追加disabled属性, 避免mboot的shell和console竞争串口数据 2019/10/25 10:53:30 luther
sed -i 's#service console /\(.*\)#service console-mboot /\1\n    disabled#' ${TARGET_ROOT_OUT}/*.rc
sed -i 's#service console /\(.*\)#service console-mboot-vendor /\1\n    disabled#' ${TARGET_OUT_VENDOR}/etc/init/*.rc
sed -i 's#service console /\(.*\)#service console-mboot-system /\1\n    disabled#' ${TARGET_OUT}/etc/init/*.rc
sed -i 's#service console /\(.*\)#service console-mboot-system /\1\n    disabled#' ${TARGET_OUT}/etc/init/hw/*.rc

# [ "${TARGET_MBOOT_VERSION}" != "0" ] && { # mboot安装到/system/bin下，调试AndroidQ Second阶段 2019/07/27 18:53:48 luther
# #     mv ${TARGET_OUT}/bin/init ${TARGET_OUT}/bin/android.init
# #     mv ${TARGET_OUT}/bin/ueventd ${TARGET_OUT}/bin/android.ueventd
# #     ln -s /msystem/bin/busybox ${TARGET_OUT}/bin/init
# #     ln -s android.init ${TARGET_OUT}/bin/ueventd
#      rm -f ${TARGET_ROOT_OUT}/android.init
#      ln -s /system/bin/init ${TARGET_ROOT_OUT}/android.init
# }

## 查找out/target/product/s9863a1h10/root out/target/product/s9863a1h10/system 目录下符合'.mboot'的文件并删除
find ${TARGET_ROOT_OUT} -name '.mboot' | xargs rm -f
find ${TARGET_OUT} -name '.mboot' | xargs rm -f
# 2. env-setup
## 配置环境变量
[ 'true' ] && {
mkdir -p $(dirname ${ENV}) ##创建目录out/target/product/s9863a1h10/root/mboot/env-setup
echo -n 0 > ${TARGET_ROOT_OUT}/mboot/selinux ##向out/target/product/s9863a1h10/root/mboot/selinux文件中写入0
cat >${ENV} <<__AEOF ##向out/target/product/s9863a1h10/root/mboot/env-setup文件中写入89~93行内容
export TARGET_DEVICE_SOC=${TARGET_DEVICE_SOC}
export TARGET_BOARD_PLATFORM=${TARGET_BOARD_PLATFORM:1:100}
export TARGET_DEVICE_BOARD=${TARGET_DEVICE_BOARD}
export TARGET_PRODUCT=${TARGET_PRODUCT}
export WITH_FULL=${WITH_FULL}
__AEOF
chmod 755 ${ENV} ## 修改out/target/product/s9863a1h10/root/mboot/env-setup文件权限
}
# 3. misc others
# [ "${WITH_ADB}" = "xtrue" ] && {
[ "xtrue" = "xtrue" ] && {
	## 拷贝adbd
    [ '' ] && {
        rm -f ${TARGET_ROOT_OUT}/sbin/adbd
        cp ${TARGET_OUT_INTERMEDIATES}/EXECUTABLES/adbd_intermediates/adbd ${TARGET_ROOT_OUT}/sbin
    }
    ##ADBS=out/target/product/s9863a1h10/root/mboot/tool/adbd TARGET_DEVICE_SOC=sharkl3，当前ADBS目录下只有Android.mk  default-setup.sh  default-uninstall.sh三个文件，所以执行else语句
    ADBS=${MBOOT}/tool/adbd
    if [ -f ${ADBS}/${TARGET_DEVICE_SOC}.sh ]; then
        cp ${ADBS}/${TARGET_DEVICE_SOC}.sh ${TARGET_ROOT_OUT}/sbin/adbd-setup.sh
    else
        cp ${ADBS}/default-setup.sh ${TARGET_ROOT_OUT}/sbin/adbd-setup.sh ##将out/target/product/s9863a1h10/root/mboot/tool/adbd/default-setup.sh文件拷贝并重命名到out/target/product/s9863a1h10/root/sbin/adbd-setup.sh
        echo "mboot : ${ADBS}/default-setup.sh -> ${ADBS}/${TARGET_DEVICE_SOC}.sh to ${TARGET_ROOT_OUT}/sbin/adbd-setup.sh" >&2
    fi
    chmod 755 ${TARGET_ROOT_OUT}/sbin/adbd-setup.sh ##修改out/target/product/s9863a1h10/root/sbin/adbd-setup.sh权限
}
# 4. ln -s /system/bin to /bin for adb shell
# ln -s /bin ${TARGET_ROOT_OUT}/system/
# N. last - true should be the last command or exit 0
[ "${TARGET_MBOOT_VERSION}" == "0" -o "${TARGET_MBOOT_VERSION}" == "2" ] && { # mboot安装到ramdisk.img下，调试AndroidQ First阶段 2019/07/27 18:53:48 luther
    # setup ramdisk folder for AndroidQ OverlayFS
    ##创建软连接 from '/sbin/android.start' to 'out/target/product/s9863a1h10/ramdisk/android.start'
    ln -s /sbin/android.start ${TARGET_RAMDISK_OUT}/android.start
    # mv ${TARGET_RAMDISK_OUT}/init ${TARGET_RAMDISK_OUT}/android.init
    ##创建软链接 from '/sbin/msystem' to 'out/target/product/s9863a1h10/ramdisk//msystem
    ln -s /sbin/msystem ${TARGET_RAMDISK_OUT}/
    [ "${BUSYBOX_INIT}" ] && {
        rm -f ${TARGET_RAMDISK_OUT}/init
        ln -s /msystem/bin/busybox ${TARGET_RAMDISK_OUT}/init
    }
    ##将out/target/product/s9863a1h10/root/mboot拷贝到out/target/product/s9863a1h10/ramdisk目录下
    cp -a ${TARGET_ROOT_OUT}/mboot ${TARGET_RAMDISK_OUT}/
    ##创建out/target/product/s9863a1h10/ramdisk/sbin目录，out/target/product/s9863a1h10/ramdisk/system/bin目录
    mkdir -p ${TARGET_RAMDISK_OUT}/sbin/ ${TARGET_RAMDISK_OUT}/system/bin
    ##创建软链接 from '/msystem/bin/busybox' to 'out/target/product/s9863a1h10/ramdisk/system/bin/sh'
    ln -s /msystem/bin/busybox ${TARGET_RAMDISK_OUT}/system/bin/sh
    # (cd ${TARGET_ROOT_OUT}/sbin; cp -a android.start.first.stage mboot-chroot-hook mso.img.tar.bz2 msystem lsz lrz ll k android.start adbd-setup.sh adbd mboot-auto mboot-auto2 ${ROOT_ABS}/${TARGET_RAMDISK_OUT}/sbin/;)
    ##拷贝out/target/product/s9863a1h10/root/sbin目录下所有文件到out/target/product/s9863a1h10/ramdisk/sbin目录下
    cp -a ${TARGET_ROOT_OUT}/sbin/* ${TARGET_RAMDISK_OUT}/sbin/
    ##删除out/target/product/s9863a1h10/ramdisk/sbin目录下files中包含的文件
    files=(gcc-* simpleperf trace-cmd.static strace bash tree gawk lsz lrz tree busybox)
    for f in ${files[@]}; do
        rm -rf ${TARGET_RAMDISK_OUT}/sbin/$f
    done
    ##重命名out/target/product/s9863a1h10/ramdisk/sbin/android.start文件为android.start.second.stage
    mv ${TARGET_RAMDISK_OUT}/sbin/android.start ${TARGET_RAMDISK_OUT}/sbin/android.start.second.stage
    ##重命名out/target/product/s9863a1h10/ramdisk/sbin/android.start.first.stage文件为android.start
    mv ${TARGET_RAMDISK_OUT}/sbin/android.start.first.stage ${TARGET_RAMDISK_OUT}/sbin/android.start
    ##修正out/target/product/s9863a1h10/ramdisk/sbin/msystem/metc/inittab文件内容
    sed -i 's!^::respawn:-/msystem/bin/sh!::once:-/msystem/bin/sh!' ${TARGET_RAMDISK_OUT}/sbin/msystem/metc/inittab
}

[ '1' ] && {
	##修正out/target/product/s9863a1h10/root/sbin/msystem/metc/profile文件
    sed -i 's!/sbin/mboot-auto!/sbin/mboot-auto2!g' ${TARGET_ROOT_OUT}/sbin/msystem/metc/profile
    ##修正out/target/product/s9863a1h10/root/sbin/msystem/metc/init.d/rcS文件
    sed -i 's/\(.*mdev.*\)/# \1/' ${TARGET_ROOT_OUT}/sbin/msystem/metc/init.d/rcS
}

true


```



- `tiny-formatter/model/zebu/zebu_files_must_be_appened.mk`

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# $(warning $(shell echo -e "\033[32m############################## TARGET_GPU_PLATFORM=$(TARGET_GPU_PLATFORM) ##############################\033[0m"))
## 当编译soft GPU时执行
ifeq ($(TARGET_GPU_PLATFORM),soft)
# ifneq ($(BOARD_VNDK_VERSION),)
$(warning $(shell echo -e "\033[32m############################## BOARD_VNDK_VERSION=$(BOARD_VNDK_VERSION), installing files ##############################\033[0m"))
#.PHONY: TINYSOFTGPU
TINYSOFTGPU:= $(PRODUCT_OUT)/TINYSOFTGPU
$(PRODUCT_OUT)/vendor.img : $(TINYSOFTGPU)
$(TINYSOFTGPU): $(PRODUCT_OUT)/system.img
	$(hide) touch $(TINYSOFTGPU)
	$(hide) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY=$(TINY) \
			TARGET_ARCH=$(TARGET_ARCH) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			TARGET_GPU_PLATFORM=$(TARGET_GPU_PLATFORM) \
			BOARD_VNDK_VERSION=$(BOARD_VNDK_VERSION) \
			$(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/android/install.sh
# endif # ifneq ($(BOARD_VNDK_VERSION),)
endif # ifeq ($(TARGET_GPU_PLATFORM),soft)

ifeq (true,true)
## 增加ramdisk.img、boot.img、system.img依赖
dtb2dts := $(PRODUCT_OUT)/dtb2dts.dts
$(PRODUCT_OUT)/ramdisk.img: $(dtb2dts)
$(PRODUCT_OUT)/boot.img: $(dtb2dts)
$(PRODUCT_OUT)/system.img: $(dtb2dts)
# device/sprd/<SoC>/common/generate_dtb_image.mk
# $(dtb2dts): dtbimage 因为bsp定义了make命令，如果不使用/usr/bin/make来编译android的话，kernel和ko会被首先编译，所以dtb已经生成 2019/10/24 08:36:31 luther
$(dtb2dts):
	$(hide) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY=$(TINY) \
			TARGET_ARCH=$(TARGET_ARCH) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			MODE=dts \
			KERNEL_OUT=$(shell readlink -f $(TARGET_BSP_OUT)/../obj/kernel) \
			TARGET_DTB=$(BSP_DTB_NAME) \
			$(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/android/install.sh
endif

## 如果MAKECMDGOALS为空，删除PRODUCT_OUT下的相关目录
ifeq (,$(MAKECMDGOALS))
$(shell rm -rf $(PRODUCT_OUT)/system $(PRODUCT_OUT)/vendor $(PRODUCT_OUT)/product $(PRODUCT_OUT)/socko $(PRODUCT_OUT)/odmko $(PRODUCT_OUT)/recovery $(PRODUCT_OUT)/cache $(PRODUCT_OUT)/data $(PRODUCT_OUT)/root $(PRODUCT_OUT)/ramdisk)
endif

## 如果WITH_FULL ！= true，分别调用zebu/src/android/common/copy_files.sh、zebu/zebu_copy_files.sh
## copy_files.sh主要实现vendor/etc/vintf/manifest.xml的拷贝， zebu_copy_files.sh不存在，不需要执行
ifneq ($(WITH_FULL),true)
$(warning $(shell PRODUCT_OUT=$(PRODUCT_OUT) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) TINY_BUILD_MODEL=$(TINY_BUILD_MODEL) $(TINY_BASE_DIR_ROOT)/model/zebu/src/android/common/copy_files.sh))
$(warning $(shell PRODUCT_OUT=$(PRODUCT_OUT) TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) $(TINY_BASE_DIR_ROOT)/model/zebu/zebu_copy_files.sh))
endif

$(warning $(shell echo -e "\033[32m############################## Installing manifest.xml WITH_FULL = $(WITH_FULL) with MAKECMDGOALS = $(MAKECMDGOALS) ##############################\033[0m"))
$(warning $(shell \
			TINY_BASE_DIR_ROOT=$(TINY_BASE_DIR_ROOT) \
			TINY=$(TINY) \
			TARGET_ARCH=$(TARGET_ARCH) \
			PRODUCT_OUT=$(PRODUCT_OUT) \
			MODE=manifest \
			$(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/android/install.sh))

ifneq ($(WITH_FULL),true)
## 定义函数simg2img_convert，该函数功能是将sparse img转换为正常的img
define simg2img_convert
	$(call pretty,"Target zebu image: $(2)")
	if [ "`/usr/bin/file $(1) | /bin/grep "sparse"`" -o \
		 "`/usr/bin/file $(1) | /usr/bin/cut -d' ' -f 2`" = "data" \
		]; then \
		$(BUILD_OUT_EXECUTABLES)/simg2img $(1) $(2); \
		true; \
	else \
		cp $(1) $(2); \
		true; \
	fi
endef

## 以下分别通过调用simg2img_convert函数将super.img、socko.img、system.img、vendor.img、cache.img、userdata.img转换生成对应的zebu-super.img、zebu-socko.img、zebu-system.img、zebu-vendor.img、zebu-cache.img、zebu-userdata.img
#.PHONY: zebu-super.img
zebu-super := $(PRODUCT_OUT)/zebu-super.img
$(DEFAULT_GOAL): $(zebu-super)
$(zebu-super): $(PRODUCT_OUT)/super.img
	$(hide) $(call simg2img_convert,$^,$@)

#.PHONY: zebu-socko.img
zebu-socko := $(PRODUCT_OUT)/zebu-socko.img
$(DEFAULT_GOAL): $(zebu-socko)
$(zebu-socko): $(PRODUCT_OUT)/socko.img
	$(hide) $(call simg2img_convert,$^,$@)

#.PHONY: zebu-system.img
zebu-system := $(PRODUCT_OUT)/zebu-system.img
$(DEFAULT_GOAL): $(zebu-system)
$(zebu-system): $(PRODUCT_OUT)/system.img
	$(hide) $(call simg2img_convert,$^,$@)

#.PHONY: zebu-vendor.img
zebu-vendor:= $(PRODUCT_OUT)/zebu-vendor.img
$(DEFAULT_GOAL): $(zebu-vendor)
$(zebu-vendor): $(PRODUCT_OUT)/vendor.img
	$(hide) $(call simg2img_convert,$^,$@)

#.PHONY: zebu-cache.img
zebu-cache := $(PRODUCT_OUT)/zebu-cache.img
$(DEFAULT_GOAL): $(zebu-cache)
$(zebu-cache): $(PRODUCT_OUT)/cache.img
	$(hide) $(call simg2img_convert,$^,$@)

#.PHONY: zebu-userdata.img
zebu-userdata :=  $(PRODUCT_OUT)/zebu-userdata.img
$(DEFAULT_GOAL): $(zebu-userdata)
$(zebu-userdata): $(PRODUCT_OUT)/userdata.img
	$(hide) $(call simg2img_convert,$^,$@)

# $(simg2img_convert,system.img)
# $(simg2img_convert,userdata.img)
# $(simg2img_convert,vendor.img)
# $(simg2img_convert,cache.img)
endif
# *.rc
## 一些必须安装的rc文件
files_must_be_appended += \
	/root/ueventd.rc \
	/root/ueventd.$(TARGET_BOARD).rc \
	/root/init.environ.rc

```

- `tiny-formatter/model/zebu/src/android/install.sh`

```shell
#!/bin/bash
#
# Copyright (C) 2019 UNISOC Communications Inc.
#
BASE=$(dirname `readlink -f $0`)/
${BASE}/common/install.sh $@

```

- `tiny-formatter/model/zebu/src/android/common/install.sh`

```shell
#!/bin/bash
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
## BASE=tiny-formatter/model/zebu/src/android/common/src
BASE=$(dirname `readlink -f $0`)/src
echo "tiny-formatter installing ..."

## 对manifest处理
if [ "${MODE}" = "manifest" ]; then
    # echo "`pwd` : `ls .manifest.xml.[0-9]*`"
    for m in $(ls out/manifests/manifest.xml.[0-9]* | sort | tail -n 3); do
        # md=$(echo ${m} | sed 's/^\.//')
        ## 超过50M的manifest.xml文件跳过
        [[ $(/usr/bin/du -b ${m} | cut -f1) -gt 50*1024*1024 ]] && { echo 'manifest file size bigger than 50M, skip copying it to save system.img space'; continue; } # Skip more than 50M manifest.xxx.local.status file because of so many & big not merged files size
        # for d in root system vendor; do
        ## 将manifest拷贝到新建的out/target/product/s9863a1h10/system、out/target/product/s9863a1h10/vendor目录下
        for d in system vendor; do
            [ -d ${PRODUCT_OUT}/${d} ] || mkdir -p ${PRODUCT_OUT}/${d}
            cp -a ${m} ${PRODUCT_OUT}/${d}/ #$(basename ${md})
        done
    done
fi

## 对dts文件处理，此处通过调用tiny-formatter/tool/dtb2dts,tiny-formatter/tool/dtsort工具对${PRODUCT_OUT}/dtb2dts.dts进行处理，经将该文件重命名为${PRODUCT_OUT}/dtb2dts-${TARGET_DTB}.dts，最后将该文件拷贝到新建的out/target/product/s9863a1h10/root目录
if [ "${MODE}" = "dts" ]; then
    DTB2DTS_FILE=${PRODUCT_OUT}/dtb2dts.dts
    source ${TINY_BASE_DIR_ROOT}/tool/dtb2dts | tee ${DTB2DTS_FILE}
    ${TINY_BASE_DIR_ROOT}/tool/dtsort ${DTB2DTS_FILE}
    m=${PRODUCT_OUT}/dtb2dts-${TARGET_DTB}.dts
    echo ${m}
    mv ${DTB2DTS_FILE} ${m}
    for d in root; do
        [ -d ${PRODUCT_OUT}/${d} ] || mkdir -p ${PRODUCT_OUT}/${d}
        cp -a ${m} ${PRODUCT_OUT}/${d}/
    done
fi

## 以下代码是对Soft gpu模式进行处理
# TARGET_GPU_PLATFORM := soft in device/brand/SoC/BoardVersion/AndroidProducts.mk
[ "${TARGET_GPU_PLATFORM}" = "soft" ] && {
# VNDK let's /vendor can't access core lib, but can access /system/vndk and /system/vndk-sp
# cp /system/lib64/libpixelflinger.so /vendor/lib64
# cp /system/lib64/libETC1.so /vendor/lib64
# cp /system/lib64/libui.so /vendor/lib64
# cp /system/lib64/android.hardware.graphics.allocator@2.0.so /vendor/lib64/
# cp /system/lib64/android.hardware.configstore@1.0.so /vendor/lib64
# cp /system/lib64/android.hardware.configstore-utils.so /vendor/lib64
# cp /system/lib64/android.hardware.configstore@1.1.so /vendor/lib64
# cp /system/lib64/libdrm.so /vendor/lib64/
# cp /system/lib64/android.frameworks.bufferhub@1.0.so /vendor/lib64/
# TARGET_GPU_PLATFORM=soft BOARD_VNDK_VERSION=current TARGET_ARCH=arm64 PRODUCT_OUT=~/sprdroid9.0_trunk/out/target/product/sp9832e_1h10 ./install.sh
    [ "${BOARD_VNDK_VERSION}" ] && {
        LIBS=(libpixelflinger.so libETC1.so ## 将LIBS下的所有库从out/target/product/s9863a1h10/system/lib(64)/ 拷贝到out/target/product/s9863a1h10/vendor/lib(64)/ 下
            libui.so android.hardware.graphics.allocator@*
            android.hardware.configstore@* android.hardware.configstore-utils.so
            libdrm.so android.frameworks.bufferhub@1.0.so)
        for l in ${LIBS[@]}; do
            for m in lib lib64; do
                [ "$(ls ${PRODUCT_OUT}/system/$m/$l 2>/dev/null)" ] && {
                    [ "$(ls ${PRODUCT_OUT}/vendor/$m/$l 2>/dev/null)" ] || {
                        mkdir -p ${PRODUCT_OUT}/vendor/$m
                        cp -f ${PRODUCT_OUT}/system/$m/$l ${PRODUCT_OUT}/vendor/$m
                    }
                }
            done
        done
    }
    [ "${TARGET_ARCH}" = "arm64xx" ] && {## 向vendor/lib（64）/egl/目录下拷贝libGLES_android.so文件
# 136K -rwxr-xr-x 1 1477 2000 135K 11月 23 19:07 vendor/lib64/egl/libGLES_android.so
# 112K -rwxr-xr-x 1 1477 2000 110K 11月 23 19:13 vendor/lib/egl/libGLES_android.so
        [ -e ${PRODUCT_OUT}/vendor/lib64/egl/libGLES_android.so ] || {
            mkdir -p ${PRODUCT_OUT}/vendor/lib64/egl
            cp ${BASE}/frameworks/native/opengl/libagl/libGLES_android.so.arm64 ${PRODUCT_OUT}/vendor/lib64/egl/libGLES_android.so
        }
        [ -e ${PRODUCT_OUT}/vendor/lib/egl/libGLES_android.so ] || {
            mkdir -p ${PRODUCT_OUT}/vendor/lib/egl
            cp ${BASE}/frameworks/native/opengl/libagl/libGLES_android.so.arm ${PRODUCT_OUT}/vendor/lib/egl/libGLES_android.so
        }
    }
}

true


```

