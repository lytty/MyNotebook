# tiny-formatter框架恢复模块功能

>   在zebu、haps平台上启动新项目时，通常情况下，我们只需要关注Android 版本启动到launcher就可以了，所有tiny Android版本通常会将不影响Android启动的一些模块裁去，这里就包含大部分的app模块，但是基于某些特殊的需求，需要恢复特定的模块功能，这时候，就需要在tin-formatter框架中将已经裁去的模块重新添加进来，而一个特定功能的恢复，往往涉及诸多模块的添加，本文，便提供一种普遍的添加特定功能的操作思路。

>   我们以已经以前期已经完成的恢复手机Camera功能和wifi功能为例，具体讲解。

## 1. 本地Android工程检查

>   1）在恢复某个模块功能之前，我们需要确保本地代码的有效性，最好是最新的代码，且没有修改过，可以执行`m2 -R`命令，将曾经修改的代码恢复。
>
>   2）务必保证`tiny-formatter`仓库为最新的。
>
>   3）编译完整的Android版本，烧录手机后，验证手机是否正常开机，手机camera功能是否正常可用。
>
>   4）如果手机启动异常（一般情况下，手机正常启动的话，camera功能也是正常的），建议去Jenkins(`http://10.0.1.99:8080/jenkins/job/sprdroidr_trunk/`)下载一个最近的正常的Android版本的manifest.xml（需要下载相应的pac包验证），然后以此manifest.xml为base，来更新Android工程，但`tiny-formatter`仓库仍要保证最新的，然后重复第三步。
>
>   5）直到本地的Android工程编译的代码可以使手机正常启动，且camera功能正常可用。这样就可用确保在非裁剪的Android版本下，camera功能是正常的，后续在编译tiny版本时，如果camera异常，则肯定是因为tiny-formatter仓库的原因。

## 2. Camera功能恢复流程

## 2.1 恢复Camera相关模块及文件

>   恢复camera功能，首先恢复的Camera app，因为我们的app裁剪多以类似正则的形式在`model/haps/haps_files.mk`文件内进行裁剪，如下所示：

```makefile
 # app/priv-app
files_not_to_install += \
         /system_ext/app/% \
         /system_ext/priv-app/% \
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

```

>   因为是基于文件来裁剪的，所以恢复Camera app模块，需要首先要确定模块名字，查找模块名字，此处提供以下几个方法：

-   烧录完整Android版本，在以上代码中列出的目录，分别查找Camera相关的app，一般情况下，camera app的目录名称就是该app模块的模块名。

-   获取在tiny Android版本编译过程中，`modules_to_install`安装清单，这个清单没有自动拷贝到相关文件中，只能手动的在编译log中获取，建议后期保存，内容如下，可以查找含有`LOCAL_MODULE_CLASS = APPS`的所有模块，一般大概在25~30个左右，然后找到Camera关键字的应用。

```verilog
{[ tiny CUSTOM_MODULES modules 25 ]
[ modules_to_install ] : hcidump
vendor/sprd/modules/wcn/bt/hcidump/Android.mk
LOCAL_MODULE_TAGS = optional
LOCAL_MODULE_CLASS = EXECUTABLES
out/target/product/s9863a1h10/system/bin/hcidump --hcidump-- vendor/sprd/modules/wcn/bt/hcidump/Android.mk
-- depends
[ modules_to_install ] : cmd_services
vendor/sprd/tools/root_cmd_service/Android.mk
LOCAL_MODULE_TAGS = optional
LOCAL_MODULE_CLASS = EXECUTABLES
out/target/product/s9863a1h10/system/bin/cmd_services --cmd_services-- vendor/sprd/tools/root_cmd_service/Android.mk
out/target/product/s9863a1h10/system/etc/init/cmd_services.rc --cmd_services-- vendor/sprd/tools/root_cmd_service/Android.mk
-- depends
...
vendor/sprd/proprietories-source/tiny-formatter/build/common/tiny.mk:23: warning: [ tiny CUSTOM_MODULES modules 25 ]}
{[ tiny product_MODULES modules 4399 ]
[ modules_to_install ] : PQTune.sp9863a_32
vendor/sprd/proprietories-source/engpc/modules/PQTune/Android.mk
LOCAL_MODULE_TAGS = optional
LOCAL_MODULE_CLASS = SHARED_LIBRARIES
out/target/product/s9863a1h10/vendor/lib/npidevice/PQTune.sp9863a.so --PQTune.sp9863a_32-- vendor/sprd/proprietories-source/engpc/modules/PQTune/Android.mk
-- depends
libcutils.vendor_32
libutils.vendor_32
libxml2.vendor_32
liblog.vendor_32
libdrm.vendor_32
libc++.vendor_32
libc.vendor_32
libm.vendor_32
libdl.vendor_32
[ modules_to_install ] : android.hardware.audio.effect@6.0-impl_32
hardware/interfaces/audio/effect/all-versions/default/Android.bp
LOCAL_MODULE_TAGS = optional
LOCAL_MODULE_CLASS = SHARED_LIBRARIES
out/target/product/s9863a1h10/vendor/lib/hw/android.hardware.audio.effect@6.0-impl.so --android.hardware.audio.effect@6.0-impl_32-- hardware/interfaces/audio/effect/all-versions/default/Android.bp
-- depends
libbase.vendor_32
libcutils.vendor_32
libeffects_32
libfmq.vendor_32
libhidlbase.vendor_32
libhidlmemory.vendor_32
liblog.vendor_32
libutils.vendor_32
android.hardware.audio.common-util.vendor_32
android.hidl.memory@1.0.vendor_32
android.hardware.audio.common@6.0.vendor_32
android.hardware.audio.common@6.0-util.vendor_32
android.hardware.audio.effect@6.0.vendor_32
libc++.vendor_32
libc.vendor_32
libm.vendor_32
libdl.vendor_32
...
[ modules_to_install ] : libblas_32
external/cblas/Android.bp
LOCAL_MODULE_TAGS = optional
LOCAL_MODULE_CLASS = SHARED_LIBRARIES
out/target/product/s9863a1h10/system/lib/libblas.so --libblas_32-- external/cblas/Android.bp
-- depends
libc++_32
libc_32
libm_32
libdl_32
vendor/sprd/proprietories-source/tiny-formatter/build/common/tiny.mk:23: warning: [ tiny product_MODULES modules 4399 ]}

```

-   咨询camera app模块owner，获取camera app的安装路径、模块名等信息。

-   获取到camera app相关应用的模块后，添加进文件`model/haps/haps_modules_must_be_appened.mk`中。
-   在haps目录下，搜索camera关键字`grep -inr camera`，根据搜索结果，模块类型的添加进文件`model/haps/haps_modules_must_be_appened.mk`中，文件类型的添加进文件`model/haps/haps_files_must_be_appened.mk`中。

## 2.2 恢复Camera相关属性及设置

>   对于一些属性和设置相关的恢复，我们一般直接在原文件中进行修改，如`model/haps/src/haps.rc`，`android/image/haps/vendor/etc/permissions/handheld_core_hardware.xml`， `android/image/haps/vendor/etc/vintf/manifest.xml`



## 2.3 编译tiny版本

-   待上述camera相关的模块、文件、属性、设置等全部恢复后，可以进行第一次编译验证，烧录编译好的版本，验证camera一般功能，如camera app是否正常打开，是否正常拍照，是否正常调整焦距等操作，如果一切正常，则camera功能恢复工作至此结束，可以对相关的文件稍作注释修正，即可提交。
-   但是一般情况下，很难实现一次就正常通过的，即camera功能异常情况下（包括camera app没有显示在桌面上，camera app打开失败，camera app闪退等等），此时，我们一般需要根据log，来分析camera模块还需要哪些依赖。此处可以向camera owner咨询。如果camera owner也无法确认，则继续看后续操作流程。
-   当无法从camera owner，异常log中获取有效信息时，此时就需要用排除法来锁定camera所依赖的其他模块。

## 2.4 锁定依赖项

-   锁定依赖项，遵循的是先锁定具体文件，再锁定文件内的具体项这样一个策略。

-   锁定文件策略，大致先判断出`tiny-formatter/build/build_tiny_property.mk`、`tiny-formatter/build/build_tiny_custom_modules.mk`、`tiny-formatter/build/build_tiny_product_modules.mk`、`tiny-formatter/build/build_tiny_product_copy_files.mk`、`tiny-formatter/build/build_tiny_files.mk`、`tiny-formatter/build/build_tiny_dex_preopt_odex_install.mk`，判断方法即直接在各自文件中，注释掉其包含的相关mk文件。

>   此处我们只需要注释掉各文件包含的第一层即可，我们以`tiny-formatter/build/build_tiny_property.mk`为例，如下所示，注释掉第5行即可。

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifneq ($(TINY),)
#include $(TINY_BASE_DIR)/common/tiny_property.mk
endif


```

### 2.4.1 锁定`build`目录文件

>   锁定文件，需要首先确定最上层文件，在tiny-formatter框架中，`build`目录下的文件为Android编译时最先调用的，一般情况下，我们重点关注`tiny-formatter/build/build_tiny_property.mk`、`tiny-formatter/build/build_tiny_custom_modules.mk`、`tiny-formatter/build/build_tiny_product_modules.mk`、`tiny-formatter/build/build_tiny_product_copy_files.mk`、`tiny-formatter/build/build_tiny_files.mk`这5个文件，其中`tiny-formatter/build/build_tiny_custom_modules.mk`、`tiny-formatter/build/build_tiny_product_modules.mk`、`tiny-formatter/build/build_tiny_files.mk`这3个文件尤为重要，可以先锁定这3个文件，如果注释掉这3个文件中包含的第一层，camera功能正常，则无需再去关注其他文件了。

>   按照经验，此处列出锁定文档的基本顺序：`tiny-formatter/android/image/haps/vendor/etc/permissions/handheld_core_hardware.xml`、 `tiny-formatter/android/image/haps/vendor/etc/vintf/manifest.xml`、`tiny-formatter/build/build_tiny_property.mk`、`tiny-formatter/build/build_tiny_product_modules.mk`、`tiny-formatter/build/build_tiny_custom_modules.mk`、`tiny-formatter/build/build_tiny_files.mk`。
>
>   至于每次操作几个文件，建议还是基于从多向少的原则来操作，即开始同时注释多个文件，如果camera功能正常，则相应消去注释，进一步收缩范围，如果camera功能不正常，则继续扩大注释范围，如此反复，直到确定camera功能正常的最小文件范围。
>
>   上述文件包含层次如下，其中，mboot相关文件，因为不涉及裁剪，所以可以忽略，编译haps工程，只需要关注haps相关文件，关注zebu工程，只需要关注zebu相关文件即可。

- `tiny-formatter/build/build_tiny_property.mk`

```
tiny-formatter/build/build_tiny_property.mk
|-- tiny-formatter/build/common/tiny_property.mk
    |-- tiny-formatter/model/mboot/mboot_property.mk
    |-- tiny-formatter/model/zebu/zebu_property.mk

```

-   `tiny-formatter/build/build_tiny_custom_modules.mk`

```
tiny-formatter/build/build_tiny_custom_modules.mk
|-- tiny-formatter/build/common/tiny.mk
    |-- tiny-formatter/model/zebu/zebu.mk
    |-- tiny-formatter/model/zebu/zebu_only_installed.mk

```

-   `tiny-formatter/build/build_tiny_product_modules.mk`

```
tiny-formatter/build/build_tiny_product_modules.mk
|-- tiny-formatter/build/common/tiny.mk
    |-- tiny-formatter/model/zebu/zebu.mk
    |-- tiny-formatter/model/zebu/zebu_only_installed.mk

```

-   `tiny-formatter/build/build_tiny_product_copy_files.mk`

```
tiny-formatter/build/build_tiny_product_copy_files.mk
|-- tiny-formatter/build/common/tiny_product_copy_files.mk
    |-- tiny-formatter/model/zebu_product_copy_files.mk

```

-   `tiny-formatter/build/build_tiny_files.mk`

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

-   `tiny-formatter/build/build_tiny_dex_preopt_odex_install.mk`

```
tiny-formatter/build_tiny_dex_preopt_odex_install.mk
|-- tiny-formatter/build/common/tiny_dex_preopt_odex_install.mk

```



### 2.4.2 锁定`build/common`目录文件

>   当确定`build`目录下相关文件后，进一步跟进，即按照相同的版本锁定`build/common`目录下的`tiny_*.mk`文件，在对`build/common`目录下的`tiny_*.mk`文件进行操作时，需要同时消去上一次build目录下的注释修改，比如，我们第一次锁定了`tiny-formatter/build/build_tiny_property.mk`，进行了以下操作：

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifneq ($(TINY),)
#include $(TINY_BASE_DIR)/common/tiny_property.mk
endif

```

>   当我们在对`build/common/tiny_property.mk`进行操作时，此时，就需要恢复`build/build_tiny_property.mk`文件的原有状态，即消去其第5行的注释符。

>   对`build/common/tiny_property.mk`进行操作时，我们看到该make文件设置了3个ro属性值，以及包含了3个make文件，其中TARGET_DEVICE_DIR为Android源码device目录对应的文件，因为我们现在还没有在对应目录下增加文件，所以可以不用关注。
>
>   此处还应该检查设置的3个ro属性是否影响camera的功能，因为这里的ro属性值可能在其他地方（tiny-formatter框架外）被使用，我们之前在做AndroidQ启动优化时，就在`frameworks/base/services/java/com/android/server/SystemServer.java`代码中使用了`ro.tiny`属性，已阻止tiny版本下某些serive的启动，而这一点恰是影响camera功能的一个因素，不过现在不用担心了，AndroidR上没有相应的修改。
>
>   `mboot_property.mk`文件可适当关注，一般情况下该文件不影响模块的功能恢复。
>
>   综上所述，即该文件的验证需要关注的有ro属性，`model/mboot/mboot_property.mk`，`model/$(TINY)/$(TINY)_property.mk`三个点，文件的验证，依然是通过注释的方式来操作。

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
# ifeq ($(TINY_BUILD_VERSION), tiny) # tiny base on sprdroid9.0_trunk/build/make$ git show 27be3fd282a437d0c5d88d53075f7c789e1e6d1a or export TINY_BUILD_VE    RSION=tiny@zebu manually
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

>   camera模块恢复的过程中，`model/mboot/mboot_property.mk`，`model/$(TINY)/$(TINY)_property.mk`都没有影响，只有一个`ro.tiny`属性问题，将涉及的`frameworks/base/services/java/com/android/server/SystemServer.java`代码恢复后，camera功能正常，即`build/common/tiny_property.mk`目录验证完毕。
>
>   其他tiny文件的验证流程基本上都是如此。

### 2.4.2 锁定`model/haps`目录文件

>   下面我们来验证一下，最终文件中，模块的筛查，比如`model/haps/haps.mk`，其调用流程`build/build_tiny_custom_modules.mk -> build/common/tiny.mk -> model/haps/haps.mk`，该文件代码如下：

```makefile
#
# Copyright (C) 2018 UNISOC Communications Inc.
#
ifeq ($(WITH_FULL),)
# Debug module
modules_removed += \
	libylog_32 ylogkat libylog ylog_common \
	hcidump \
	cplogctl \
	mlogservice \
	collect_apr_server

ifeq ($(WITH_TOMBSTONED),xxx)
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
	iqfeed \
	slogmodem \
	mdnsd \
	gatekeeperd \
	uncrypt \
	wificond \
	bugreport \
	cameraserver \
	minicamera \
	incidentd \
	mtpd \
	racoon \
	statsd \
	traced \
	modem_control \
	connmgr_cli \
	connmgr \
	engpc \
	refnotify \
	audio.primary.default_32 \
	audio.primary.default \
	audio.primary.$(TARGET_BOARD_PLATFORM)_32 \
	audio.primary.$(TARGET_BOARD_PLATFORM) \
	usbd \
	blank_screen \
	bootstat \
	dumpstate \
	vendor.sprd.hardware.radio@1.0 \
	dhcp6s \
	tiny_firewall.sh \
	data_rps.sh \
	netbox.sh \
	dataLogDaemon \
	ims_bridged \
	ip_monitor.sh \
	ju_ipsec_server \
	gpsd \
	libLLVM_android \
	libavatar \
	libavatar_32 \
	libbluetooth \
	libbluetooth_32 \
	libmme_jrtc \
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
	android.hardware.radio@1.0.vendor \
	android.hardware.radio@1.0.vendor_32 \
	android.hardware.radio@1.1 \
	android.hardware.radio@1.1_32 \
	android.hardware.radio@1.1.vendor \
	android.hardware.radio@1.1.vendor_32 \
	android.hardware.radio@1.2.vendor \
	android.hardware.radio@1.2.vendor_32 \
	libRSCpuRef \
	libRSCpuRef_32 \
	libRSCpuRef.vendor \
	libRSCpuRef.vendor_32 \
	libcamsensor \
	libcamsensor_32 \
	libSprdImageFilter \
	libSprdImageFilter_32 \
	libsprdfaceid \
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
	cp_diskserver \
	urild \
	librilcore \
	libimpl-ril \
	librilutils \
	libatci \
	libFactoryRadioTest \
	charge \
	phasecheckserver \
	factorytest \
	ext_data \
	srtd \
	thermald \
	hostapd \
	sprdstorageproxyd \
	rpmbserver \
	tsupplicant \
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
	resize2fs \
	cmd_services

# media video hw so result Abort message
modules_removed += \
	libomx_m4vh263dec_hw_sprd \
	libomx_m4vh263dec_hw_sprd_32 \
	libomx_hevcdec_hw_sprd \
	libomx_hevcdec_hw_sprd_32 \
	libomx_hevcenc_hw_sprd \
	libomx_hevcenc_hw_sprd_32 \
	libomx_avcdec_hw_sprd \
	libomx_avcdec_hw_sprd_32 \
	libomx_avcenc_hw_sprd \
	libomx_avcenc_hw_sprd_32 \
	libomx_vpxdec_hw_sprd \
	libomx_vpxdec_hw_sprd_32 \
	libomx_vpxenc_hw_sprd \
	libomx_vpxenc_hw_sprd_32 \
	libomx_vp9dec_hw_sprd \
	libomx_vp9dec_hw_sprd_32

# list some modules which can not be moved
#modules_removed += \
#	iptables \  ## iptables,ip6tables result netd start failed
#	ip6tables

ifneq ($(USE_SPRD_HWCOMPOSER),true)
$(warning $(shell echo -e "\033[31mREMOVE hwcomposer.$(TARGET_BOARD_PLATFORM) forcely, then android launcher is ok without HWC & GPU ##############################\033[0m"))
modules_removed += \
	hwcomposer.$(TARGET_BOARD_PLATFORM)
$(warning $(shell echo -e "\033[31mREMOVE hwcomposer.$(TARGET_BOARD_PLATFORM) forcely, then android launcher is ok without HWC & GPU ##############################\033[0m"))
endif
endif


```

>   对于以上文件的筛查，我们一般使用二分法，来判断，即注释掉一半，编译版本，验证camera功能是否正常，如果正常，则注释部分包含camera依赖项，如果不正常，则继续扩大注释范围，如此往复，最终确定camera功能在该文件中的所有依赖项。

>   haps目录下其他文件筛查方法与此类似。

## 2.5 camera功能恢复的所有依赖项

>   经过以上步骤，获得最终的camera功能恢复的所有依赖项，具体如下，对应gerrit(http://review.source.unisoc.com/gerrit/#/c/672629/):

```
/*tiny-formatter/android/image/haps/vendor/etc/permissions/handheld_core_hardware.xml*/
...
    <feature name="android.hardware.camera" />
...

/*tiny-formatter/android/image/haps/vendor/etc/vintf/manifest.xml*/
...
    <hal format="hidl">
        <name>android.hardware.camera.provider</name>
        <transport>hwbinder</transport>
        <version>2.4</version>
        <interface>
            <name>ICameraProvider</name>
            <instance>legacy/0</instance>
        </interface>
        <fqname>@2.4::ICameraProvider/legacy/0</fqname>
    </hal>
...

/*tiny-formatter/model/haps/haps_files_must_be_appened.mk*/
# recovery camera functions
files_must_be_appended += \
	/vendor/etc/init/camera.rc

/*tiny-formatter/model/haps/haps_modules_must_be_appened.mk*/
# recovery camera function
modules_must_be_appended += \
	CameraCalibration \
	DreamCamera2 \
	QuickCamera \
	CameraIPControl \
	cameraserver_32 \
	cameraserver \
	minicamera \
	libcameraservice_32 \
	libcameraservice \
	android.hardware.camera.provider@2.4-service_32 \
	MediaProvider

/*tiny-formatter/model/haps/src/haps.rc*/
	#setprop config.disable_cameraservice true

```

## 3. wifi功能恢复流程
### 3.1 恢复wifi相关模块及文件
> wifi 功能的恢复流程大体上类似 2.camera功能恢复流程，可综合两部分进行参考：

> 首先恢复 WiFi 相关模块，因为我们的app裁剪多以类似正则的形式在`model/haps/haps.mk` & `model/haps/haps_files.mk`两个文件内进行裁剪，部分内容如下：

```makefile
# model/haps/haps.mk
modules_removed += \
	NotoSerifCJK-Regular.ttc \
	NotoSansCJK-Regular.ttc \
	NotoColorEmoji.ttf \
	NotoSansSymbols-Regular-Subsetted.ttf \
	NotoSansEgyptianHieroglyphs-Regular.ttf \
	NotoSansCuneiform-Regular.ttf \
	log_service \
	iqfeed \
	slogmodem \
	mdnsd \
	gatekeeperd \
	uncrypt \
	# 有明显wifi字眼的模块
	wificond \ 
	bugreport \

# model/haps/haps_files.mk
# app/priv-app
files_not_to_install += \
    /system_ext/app/% \
	# 经测试部分wifi模块在priv-app内
    /system_ext/priv-app/% \
    /system/app/% \
    /system/priv-app/% \
    /system/preloadapp/% \
    /system/vital-app/% \
    /system/overlay/% \

# model/haps/haps_files.mk
# Other files
files_not_to_install += \
	/system/etc/init/coredump.rc \
	/system/etc/init/perfprofd.rc \
	/system/etc/init/logtagd.rc \
	# 有明显wcn字眼的依赖文件
	/vendor/etc/init/wcn.rc \
```

> 因为是基于文件来裁剪的，此处首先查找了wifi模块的名字,查找wifi模块名字，此处提供以下几个方法：

- 烧录完整Android版本，在以上代码中列出的目录，分别查找wifi相关的app,一般情况下为带有wifi字眼的APP模块,相关字眼(`wifi`,`wcn`，`vpn`,`Network`,`ipaddr`,`ip6`）等等。

- 获取在tiny Android版本编译过程中，`modules_to_install`安装清单，可以查找含有`LOCAL_MODULE_CLASS = APPS`的所有模块，一般大概在25~30个左右，然后找到wifi关键字的应用,部分内容参考camera处的列举内容。

- 咨询wifi app模块owner，获取wifi app的安装路径、模块名等信息。

- 通过二分法在`haps.mk`、`haps_files.mk` 内进行其他相关模块或文件的筛选。

- 在haps目录下，搜索wifi相关字眼如：`grep -inr wifi`等。

- 根据上述查找以及搜索结果，相关模块添加进文件`model/haps/haps_modules_must_be_appened.mk`中，依赖文件添加进文件`model/haps/haps_files_must_be_appened.mk`中。

### 3.2 恢复wifi相关属性及设置
> wifi属性字眼：`wifi`,'wcn'，`vpn`,`Network`,`ipaddr`,'ip6'等。
>
> WiFi部分属性设置需要从上述wifi字眼中排查过滤。

- 对于一些属性和设置相关的恢复，我们一般直接在原文件中进行修改，如`model/haps/src/haps.rc`，`android/image/haps/vendor/etc/permissions/handheld_core_hardware.xml`， `android/image/haps/vendor/etc/vintf/manifest.xml`



### 3.3 编译tiny版本

>   待上述wifi模块、文件、属性设置等在`haps_modules_must_be_appened.mk` &`haps_files_must_be_appened.mk` & `handheld_core_hardware.xml` & `manifest.xml`全部恢复后，可以进一步编译验证、烧录编译好的版本。

>   验证wifi 功能过程中相关情况如下：

1. 测试设置中wifi栏能否点击进去。（如有闪退情况，请查带有字眼的模块是否全部添加上 & 查看上述xml文件内相关字眼的属性是否开启）

2. 点击WiFi开启按钮，查看WiFi是否能够搜索处其他WiFi信号。（如无法开启或者搜索不到其他WiFi信号，请结合依赖文件及xml进行过滤排查）

3. 连接WiFi查看是否正常（此处常常会获取不到ip，但能连上不能上网，此时需查找network相关模块或依赖性文件） 

>   但是一般情况下，很难实现一次就正常通过的，即wifi功能异常情况下，此时，我们一般需要根据log，以及上述情况来分析wifi模块还需要哪些依赖。此时可向wifi owner咨询。如果wifi owner也无法确认，则可以上述其他方法尝试及继续后续流程。


### 3.4 锁定其他依赖项
- 当无法从WiFi owner，异常log中获取有效信息时，此时就需要用排除法来锁定所依赖的其他模块。
- camera部分已将该方法描述很详细，此处不在赘述。 

- 此时也可以将其他可能依赖的文件，通过adb push 到手机相应目录进行排查。也可以按照二分法进行编译、烧入手机进行验证。

### 3.5 wifi功能恢复的所有依赖项

>   经过以上步骤，获得最终的wifi功能恢复的所有依赖项，具体如下，对应gerrit(http://review.source.unisoc.com/gerrit/#/c/674043/):

```
/*tiny-formatter/android/image/haps/vendor/etc/vintf/manifest.xml*/

    <hal format="hidl">
        <name>vendor.sprd.hardware.network</name>
        <transport>hwbinder</transport>
        <version>1.0</version>
        <interface>
            <name>INetworkControl</name>
            <instance>default</instance>
        </interface>
        <fqname>@1.0::INetworkControl/default</fqname>
    </hal>
   <hal format="hidl">
        <name>vendor.sprd.hardware.wifi.hostapd</name>
        <transport>hwbinder</transport>
        <version>1.1</version>
        <interface>
            <name>IHostapd</name>
            <instance>default</instance>
        </interface>
        <fqname>@1.1::IHostapd/default</fqname>
    </hal>


/*tiny-formatter/model/haps/haps_modules_must_be_appened.mk*/
# recover wifi function
modules_must_be_appended += \
	wificond \
	wpa_supplicant \
	wpa_supplicant.conf \
	com.android.apex.cts.shim.v1_prebuilt \
	iptables \
	ip6tables \
	InProcessNetworkStack \
	PlatformNetworkPermissionConfig \
	SprdVoWifiService \
	VpnDialogs


/*tiny-formatter / model/haps/haps_files_must_be_appened.mk*/
# recovery wifi functions
files_must_be_appended += \
	/vendor/etc/init/wcn.rc \
	/vendor/lib64/liblcscp.so

```
## 4. 模块恢复注意事项

### 4.1 Android工程代码检查

-   在所有恢复工作开始之前，必须保证本地或者服务器上的Android代码正常，具体参照第1章节所述。Android代码正常后，进行第一次全编译，并保存`out/target/product/×××`目录下所有文件，最好拷贝至本地，供后续使用。

### 4.2 模块恢复流程

-   在保证Android代码正常后，开启tiny版本编译，建议首先注释掉build目录文件中涉及的第一层包含的代码，以及相关的两个xml文件（`tiny-formatter/android/image/haps/vendor/etc/permissions/handheld_core_hardware.xml， tiny-formatter/android/image/haps/vendor/etc/vintf/manifest.xml`），两个xml文件可以先将模块相关的节点打开，即先验证xml文件，保证，在其他模块都不发挥作用的情况下，首先筛查出xml中影响的因素。
-   xml文件筛查完毕后，打开`build/build_tiny_property.mk`注释，恢复其功能，如果camera功能正常，继续下一步，如果不正常，在该文件内进一步筛查，直至camera功能正常。
-   打开`tiny-formatter/build/build_tiny_custom_modules.mk`注释，恢复其功能，如果camera功能正常，继续下一步，如果不正常，在该文件内进一步筛查，直至camera功能正常。
-   打开`tiny-formatter/build/build_tiny_custom_modules.mk`注释，恢复其功能，如果camera功能正常，继续下一步，如果不正常，在该文件内进一步筛查，直至camera功能正常。
-   打开`tiny-formatter/build/build_tiny_files.mk`注释，恢复其功能，如果camera功能正常，继续下一步，如果不正常，在该文件内进一步筛查，直至camera功能正常。

### 4.3 模块验证辅助

-   对于最终模块的验证，可以使用mboot功能辅助验证，但有时候，mboot功能验证不太准确，即使mboot功能筛查完所有依赖项，最后还是需要通过编译版本来最终确定。
-   在mboot模式下对模块的验证过程中，需要批量删除或批量加载模块文件，此时，建议使用shell脚本进行操作，模块相关文件，可以在第一次全编译时的out目录获取到。
-   对于模块对应的安装文件，需要到模块安装清单中获取，此处可以写一个Python脚本，实现输入模块名，输出模块所有安装文件路径的功能。

### 4.4 版本编译

-   模块的恢复工作需要经常进程Android版本的编译，在第一次编译完成后，修改相关文件重新编译时，千万不要把整个out目录全删了，只需要在`out/target/product/×××`目录下删除`img, bin, vendor, system, product, root`等目录及文件即可，这样再编译时，会减少很多时间，如果是在服务器上，大概也就十几分钟时间。

### 4.5 添加依赖项

-   在`model/haps/haps_modules_must_be_appened.mk`，`model/haps/haps_files_must_be_appened.mk`中添加依赖项时，最好不要追加，建议另起一行，添上注释，描述清楚这些模块添加的由来。