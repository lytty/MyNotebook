# tiny-formatter 裁剪

## 1. tiny-formatter 裁剪功能相关文件路径

- tiny-formatter路径：platform/vendor/sprd/proprietories-source/tiny-formatter

## 2. 文件解析

- platform/vendor/sprd/proprietories-source/tiny-formatter/build/build_tiny_definitions.mk

  ```makefile
  TINY_BASE_DIR := $(subst $(empty) $(empty),/,$(wordlist 1, 999, $(subst /,$(empty) $(empty),$(dir $(lastword $(MAKEFILE_LIST))))))
  TINY_BASE_DIR_ROOT := $(subst $(empty) $(empty),/,$(wordlist 1, 999, $(subst /,$(empty) $(empty),$(dir $(TINY_BASE_DIR)))))
  include $(TINY_BASE_DIR)/common/tiny_definitions.mk
  ```

  1. TINY_BASE_DIR 获取当前文件所在的目录， 即platform/vendor/sprd/proprietories-source/tiny-formatter/build
  2. TINY_BASE_DIR_ROOT 获取根目录，即tiny-formatter目录，platform/vendor/sprd/proprietories-source/tiny-formatter

- platform/vendor/sprd/proprietories-source/tiny-formatter/build/common/tiny_definitions.mk

  ```makefile
  1  #
  2  # Copyright (C) 2018 UNISOC Communications Inc.
  3  #
  4  # ifeq ($(TARGET_BUILD_VERSION), tiny) # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TARGET_BUILD_VERSION=tiny@zebu manually
  5  ifeq (mboot,$(TARGET_BUILD_VERSION))
  6  # mboot is a shortcut for tiny@zebu,mboot
  7  TARGET_BUILD_VERSION := tiny@zebu,mboot
  8  ifneq (zebu,$(findstring zebu, $(TARGET_PRODUCT)))
  9  WITH_FULL := true
  10 endif
  11 endif
  12
  13 ifeq (tiny@,$(findstring tiny@, $(TARGET_BUILD_VERSION)))
  14 COMMA := ,
  15 TINY := $(patsubst tiny@%,%, $(TARGET_BUILD_VERSION)) # tiny@zebu,mboot or tiny@zebu,antutu7apk.no3D
  16 TINY := $(subst $(empty) $(empty),,$(TINY))
  17 TINY := $(subst $(COMMA),$(empty) $(empty),$(TINY))
  18 TINY_ARGS := $(subst $(empty) $(empty),$(COMMA),$(wordlist 2, 999, $(TINY)))
  19 TINY := $(word 1, $(TINY))
  20 -include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_definitions.mk
  21 -include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_definitions.mk
  22 else
  23 TINY :=
  24 endif
  25 # endif # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TARGET_BUILD_VERSION=tiny@zebu manually
  ```

  根据lunch输入combo参数定义TARGET_BUILD_VERSION、WITH_FULL、TINY、TINY_ARGS，具体定义如下：我们以sp9832e_1h10_native-userdebug-gms为例

  - sp9832e_1h10_native-userdebug-mboot，则TARGET_BUILD_VERSION会被重新赋值为tiny@zebu,mboot，即mboot是tiny@zebu,mboot的简称。TINY_ARGS: mboot，TINY：zebu
  - 第20， 21中 include前加“-”，表示当该文件不存在时，不报错

- platform/vendor/sprd/proprietories-source/tiny-formatter/model/zebu/zebu_definitions.mk

  ```makefile
  4 ifeq ($(WITH_FULL),)
  5 WITH_DEXPREOPT := true# Both of userdebug and user must use DEXPREOPT option to soft link to framework/.*vdex *.odex in /data/dalvik-cache/arm64/
  6 endif
  7 SELINUX_IGNORE_NEVERALLOWS := true# Ignore checkpolicy -M -c for sepolicy_policy.conf := $(intermediates)/policy.conf in system/sepolicy/Android.mk +85
  8 include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/mboot.mk
  ```

  根据WITH_FULL参数值定义WITH_DEXPREOPT，另外，SELINUX在此定义，即忽略权限检测

  

- platform/vendor/sprd/proprietories-source/tiny-formatter/model/zebu/mboot.mk

  ```makefile
  5 ifeq ($(TINY_ARGS), mboot)
  6 # MAKECMDGOALS := bootimage $(MAKECMDGOALS)
  7 # TARGET_NO_RECOVERY := true# No recovery.img
  8 $(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
  9 $(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
  10 $(warning )
  11 $(warning )
  12 $(warning )
  13 $(warning $(shell echo -e "\033[4;35mYou can export WITH_FULL=true; lunch xxxx-tiny@zebu,mboot; make -j32; to build a full android images; then mboot# \033[0m\033[32mandroid.start \033[0m\033[4;35mto debug Android 9/10/11/12/13/xxx\033[0m"))
  14 ifeq ($(WITH_RAMDISK), true)
  15 BOARD_BUILD_SYSTEM_ROOT_IMAGE := false# Then ramdisk.img will be appended like : INTERNAL_BOOTIMAGE_ARGS += --ramdisk $(INSTALLED_RAMDISK_TARGET) when $(MKBOOTIMG) mkbootimg
  16 $(warning $(shell echo -e "\033[4;31mkernel/arch/arm64/boot/dts/xxxx/xxxx.dts Change .dts chosen@bootargs from root=/dev/mmcblk0p30 to root=/dev/ram0\033[0m"))
  17 else
  18 #BOARD_DISABLE_SELINUX_FC := true# Need build/core ea68adc6681985026601b8fb790aad859e35003c - http://review.source.spreadtrum.com/gerrit/#/c/535463/
  19 $(warning $(shell echo -e "\033[4;31mYou can export WITH_RAMDISK=true; make -j32; to build ramdisk.img into boot.img, but should change kernel/arch/arm64/boot/dts/xxxx/xxxx.dts .dts chosen@bootargs from root=/dev/mmcblk0p30 to root=/dev/ram0\033[0m"))
  20 endif
  21 $(warning )
  22 $(warning )
  23 $(warning )
  24 $(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
  25 $(warning $(shell echo -e "\033[32m######################################################################\033[0m"))
  26 endif
  ```

  定义BOARD_BUILD_SYSTEM_ROOT_IMAGE，并打印一些log，make编译时，四条绿色“##########”中间的log即是mboot.mk打印的。





