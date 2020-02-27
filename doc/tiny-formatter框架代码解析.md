# tiny-formatter框架代码解析

## tiny-formatter/build/build_tiny_definitions.mk

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
##################################################################
TINY_BUILD_VERSION ?= $(TARGET_BUILD_VERSION)
##################################################################
TINY :=
TINY_BUILD_MODEL := $(shell $(TINY_BASE_DIR_ROOT)/build/common/tiny_definitions.sh $(TARGET_PRODUCT))
ifeq (,$(TINY_BUILD_MODEL))
TINY_BUILD_MODEL := $(shell $(TINY_BASE_DIR_ROOT)/build/common/tiny_definitions.sh $(TINY_BUILD_VERSION))
endif
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
TINY := $(patsubst tiny@%,%, $(TINY_BUILD_VERSION)) # tiny@zebu,mboot or tiny@zebu,antutu7apk.no3D
TINY := $(subst $(empty) $(empty),,$(TINY))
TINY := $(subst $(COMMA),$(empty) $(empty),$(TINY))
TINY_ARGS := $(subst $(empty) $(empty),$(COMMA),$(wordlist 2, 999, $(TINY)))
TINY := $(word 1, $(TINY))
-include $(TINY_BASE_DIR_ROOT)/model/$(TINY)/$(TINY)_definitions.mk
-include $(TARGET_DEVICE_DIR)/$(TINY)/$(TINY)_definitions.mk
endif
$(warning You can export TINY_BUILD_VERSION=mboot; lunch xxxx; make -j32; to build mboot version)
$(warning $(shell echo -e "\033[32mTiny build on TINY_BUILD_MODEL=$(TINY_BUILD_MODEL) TINY=$(TINY) TINY_ARGS=$(TINY_ARGS) TARGET_BUILD_VERSION=$(TARGET_BUILD_VERSION) TINY_BUILD_VERSION=$(TINY_BUILD_VERSION) WITH_FULL=$(WITH_FULL) MAKECMDGOALS=$(MAKECMDGOALS)\033[0m"))
# endif # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VERSION=tiny@zebu manually


```

