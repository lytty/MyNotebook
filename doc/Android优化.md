# AndroidQ 裁剪

## 1. androidQ 裁剪前期准备
- 下载 androidQ 工程
	- repo init -u ssh://gitadmin@gitmirror.spreadtrum.com/platform/manifest.git -b sprdroidq_trunk
	- repo sync -c -f
<br \>
<br \>
- 下载 pac、manifest.xml 文件
	- 在 `http://10.0.1.99:8080/jenkins/job/sprdroidq_trunk/` 中下载某一节点的pac文件（如：s9863a1h10_Natv-userdebug-native_SUPER_SHARKL3.pac.gz），首先烧机检查该pac文件是否可使手机正常启动，如果手机正常启动，下载该节点下对应的 manifest.xml 文件。
<br \>
<br \>
- 更新 androidQ 代码的 manifest.xml：
	- 拷贝已下载的 manifest.xml 文件到 sprdroidq_trunk/.repo/manifests/ 目录下，注意，不要与该目录下的文件重名；
	- croot;
	- repo init -m manifest.xml;
	- repo sync -c -f
<br \>
<br \>
- AndroidQ 代码编译
	- 正常全编 AndroidQ 代码，如果代码编译失败，请重新更新pac节点，以及对应的 manifest.xml 文件，并重新按上述步骤更新代码；
	- 如果代码编译成功，使用 ResearchDownload 烧机工具，将已编译好的 super.img、vbmeta-sign.img、vbmeta-systerm.img、vbmeta-vendor.img 替换 pac文件中对应的各文件，然后烧机，如果手机无法正常启动，请按照以上步骤重新更换节点等文件；
	- 如果手机正常启动，则androidQ 裁剪前期准备工作完成
<br \>
<br \>
<br \>
<br \>

## 2. androidQ 裁剪编译
- 删除 sprdroidq_trunk/out
	- cd sprdroidq_trunk;
	- rm -rf out;
<br \>
<br \>
- 带裁剪功能编译
	- cd sprdroidq_trunk;
	- source build/envsetup.sh;
	- lunch s9863a1h10_Natv-userdebug-tiny@zebu;注意此处根据自己所要编译的版本为准
	- make -j16;
<br \>
<br \>
- 烧机验证
	- 将已编译好的 super.img、vbmeta-sign.img、vbmeta-systerm.img、vbmeta-vendor.img 替换 pac文件中对应的各文件，然后烧机，如果手机正常启动，则可进行下一步APPS类型的模块裁剪；
	- 如果手机无法正常启动，则表示裁剪框架中将一些不能删除的模块给删除了（这种情况一般发上在不同android版本间的裁剪，如一些模块在androidP上可以裁剪，但移植到androidQ上便出了问题），需要筛查相关模块；
<br \>
<br \>
<br \>
<br \>

## 3. androidQ 获取裁剪所需的相关文件
- 所有待安装的modules
	- 我们的裁剪框架代码中没有输出包含所有modules的文件，只是将其以log的形式打印了出来，我们可以在编译的log中把这部分拷贝出来，其具体内容如下：
	```
        {[ tiny product_MODULES modules 3645 ]
        [ modules_to_install ] : PQTune.sp9863a_32
        LOCAL_PATH = vendor/sprd/proprietories-source/engpc/modules/PQTune/Android.mk
        LOCAL_MODULE_TAGS = optional
        LOCAL_MODULE_CLASS = SHARED_LIBRARIES
        out/target/product/s9863a1h10/vendor/lib/npidevice/PQTune.sp9863a.so
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
        [ modules_to_install ] : android.hardware.audio.effect@5.0-impl_32
        LOCAL_PATH = hardware/interfaces/audio/effect/all-versions/default/Android.bp
        LOCAL_MODULE_TAGS = optional
        LOCAL_MODULE_CLASS = SHARED_LIBRARIES
        out/target/product/s9863a1h10/vendor/lib/hw/android.hardware.audio.effect@5.0-impl.so
        -- depends
        libbase.vendor_32
        ...
        ...
        
        [ modules_to_install ] : libblas_32
        LOCAL_PATH = external/cblas/Android.bp
        LOCAL_MODULE_TAGS = optional
        LOCAL_MODULE_CLASS = SHARED_LIBRARIES
        out/target/product/s9863a1h10/system/lib/libblas.so
        -- depends
        libc++_32
        libc_32
        libm_32
        libdl_32
        [ tiny product_MODULES modules 3645 ]}
	```
	- 从以上的log中我们可以看出，当前待安装的modules个数为3645个，这3645个module会打印在以{[ tiny product_MODULES modules 3645 ]、[ tiny product_MODULES modules 3645 ]}分别为首尾的log中间，针对每个module，我们打印出其module名字（[ modules_to_install ]：之后的）、LOCAL_PATH属性（该module对应的Android.bp或Android.mk路径）、LOCAL_MODULE_TAGS属性、LOCAL_MODULE_CLASS属性（该module类型）、生成的输出文件路径（以out开头）、所依赖的modules（-- depends和下一个[ modules_to_install ]中间的）。
	- 我们所要删除的模块均来自这些中间，下文我们以 all_modules.txt 称呼该log文件。
<br \>
<br \>
- installed-files*.txt
	- 这类文件不用我们手动抓取，在编译结束后，会在 out/target/product/s9863a1h10/ 目录下自动生成。
	- AndroidQ中需要我们关注3个文件：installed-files.txt、installed-files-product.txt、installed-files-vendor.txt。
		- installed-files.txt： 该文件记录所有安装在/system/目录下的文件；
		- installed-files-product.txt：该文件记录所有安装在/product/目录下的文件；
		- installed-files-vendor.txt：该文件记录所有安装在/vendor/目录下的文件；
	- 所有文件中均显示该文件的大小，但文件大小都是以字节数来表示的，不易阅读，可使用android 裁剪辅助脚本工具做一下转换；
	- 因为我们裁剪都是以模块为单位的，所以对于installed-files*.txt中各文件，我们需要在all_modules.txt 文件中，找到其对应的module名字；
	- 一般情况下，我们会首先检测裁剪框架中包含的相关裁剪模块（tiny-formatter/model/zebu/zebu.mk）,以及特定的文件（tiny-formatter/model/zebu/zebu_fles.mk）,其次检测所有的APPS类型的模块，最后才是根据需要（是否进一步压缩空间）来决定是否删除installed-files*.txt文件中较大文件对应的模块。
<br \>
<br \>
- android 裁剪辅助脚本
<br \>
<br \>
<br \>
<br \>

## 4. androidQ 裁剪框架检测
- 编译裁剪框架
	- 按照第2章节进行裁剪编译，烧机验证，如果手机正常启动，antutu正常运行，则裁剪框架没有问题，否则，检查已裁剪的模块。
	- 裁剪的模块列表和非安装文件列表分别保存在tiny-formatter/model/zebu/zebu.mk，tiny-formatter/model/zebu/zebu_fles.mk两个文件下，分别由变量modules_removed、files_not_to_install记录。
<br \>
<br \>
- tiny-formatter/model/zebu/zebu_fles.mk
	- 该mk文件一般列出一些非模块可删除的文件，一般是一些xml、rc文件，保存在变量files_not_to_install下。
	- 该mk文件主要列出不被安装的文件（files_not_to_install变量），一般来说，该mk文件导致裁剪编译验证失败的可能性不大，所以该mk文件检测，我们一般采取带裁剪功能的整体编译，即更改 tiny-formatter/model/zebu/zebu.mk 文件名（更改zebu.mk文件，使得其内部的模块列表不被裁剪），带裁剪编译，如果验证成功，则表明 tiny-formatter/model/zebu/zebu_fles.mk 文件不是裁剪编译验证失败的原因。
	- 如果验证失败，可通过打印的log查看是否有必需的文件在 files_not_to_install变量下，或者在一正常pac版本的情况下，逐一删除files_not_to_install包含的文件，以查看哪些文件的删除导致了手机的启动异常，找到之后，在files_not_to_install变量下将其移除即可。
	- androidQ 中，该mk文件中包含的裁剪项不影响手机正常启动。
<br \>
<br \>
- tiny-formatter/model/zebu/zebu.mk
	- 该mk文件一般列出我们待要删除的模块，模块名保存在变量分别由变量modules_removed下。
	- zebu.mk下模块有大量的模块（一般有上百个），我们不可能一个一个来验证，一般采用二分法批量验证。
	- 首先在all_modules.txt文件中获取zebu.mk文件中包含模块所对应的输出文件，删除一个模块，只需要在手机里删除其对应的输出文件即可，如模块`PQTune.sp9863a_32`对应的输出文件`out/target/product/s9863a1h10/vendor/lib/npidevice/PQTune.sp9863a.so`，我们只需要在手机中删除`vendor/lib/npidevice/PQTune.sp9863a.so`即可。
	- 其次，对于批量模块的验证，可使用我们的 android裁剪辅助脚本工具，可将zebu.mk中的模块所属的输出文件全部输出，然手使用shell脚本批量删除即可，格式如下：
	```
        #!/bin/bash

        sudo adb kill-server;sudo adb start-server
        sudo adb root;
        sudo adb remount;reset

        # module: WAPPushManager
        # type: APPS
        sudo adb shell rm /system/app/WAPPushManager/WAPPushManager.apk
        sudo adb shell rm /system/app/WAPPushManager/oat/arm64/WAPPushManager.odex
        sudo adb shell rm /system/app/WAPPushManager/oat/arm64/WAPPushManager.vdex

        # module: LiveWallpapersPicker
        # type: APPS
        sudo adb shell rm /system/app/LiveWallpapersPicker/LiveWallpapersPicker.apk
        sudo adb shell rm /system/app/LiveWallpapersPicker/oat/arm64/LiveWallpapersPicker.odex
        sudo adb shell rm /system/app/LiveWallpapersPicker/oat/arm64/LiveWallpapersPicker.vdex

        # module: CtsShimPrebuilt
        # type: APPS
        sudo adb shell rm /system/app/CtsShimPrebuilt/CtsShimPrebuilt.apk
        ...
        ...
        sudo adb reboot
	```
	- 批量二分法验证，即先删除一般模块，重启后，如果手机正常启动（在手机启动后，最好再检查一下删除的文件是否已经确定删除），antutu正常运行，则该部分模块可移除，如果手机无法正常启动，则给部分模块中有不可移除模块，可取删除的模块文件中的一半push到手机。注意：为保证后续的重复验证，在对模块文件进行删除前，请先将这些模块文件 pull 到本地。
	- AndroidQ 中部分不可移除的模块如下：
	```
	libprotobuf-cpp-full
	android.hardware.wifi@1.0.vendor
	android.hardware.wifi@1.0.vendor_32
	android.hardware.light@2.0-service
	android.hardware.memtrack@1.0-service
	android.hardware.sensors@1.0-service
	android.hardware.usb@1.1-service
	android.hardware.wifi@1.0-service
	android.hardware.vibrator@1.0-service
	vendor.sprd.hardware.connmgr@1.0-service
	vendor.sprd.hardware.gnss@2.0-service
	vendor.sprd.hardware.log@1.0-service
	vendor.sprd.hardware.thermal@1.0-service
	android.hardware.soundtrigger@2.0
	device_manifest.xml
	```
- 重新编译裁剪版本
	- tiny-formatter/model/zebu/zebu.mk，tiny-formatter/model/zebu/zebu_fles.mk两个文件下的裁剪项验证完毕后，重新编译裁剪版本，重新烧机验证，此时基本上验证通过。如果仍有问题（起码目前为止，还没有这种情况），就需要抓取log查看了。
<br \>
<br \>
<br \>
<br \>

## 5. androidQ APPS类型模块裁剪

- 裁剪APPS类型模块主要是为了压缩img占用空间，以便留出更多空间供其他验证使用。
<br \>
<br \>
- 查找APPS类型模块
	- 使用 android裁剪脚本工具从all_modules.txt 文件中获取 APPS 类型的模块；
<br \>
<br \>
- 裁剪APPS类型模块
	- 在手机运行正常的情况下，删除APPS模块相应的输出文件，重启手机，检测手机是否正常启动，正常启动后，再次确认删除的文件是否被真正删除，真正删除后，运行antutu检查（目前在所有APPS模块中，删除后不影响手机正常启动，但是影响antutu正常运行的只有 webview 一个模块），所有这一系列操作都检测完毕后，才能确定该模块是否可被移除。当然，我们还是使用批量二分法来验证。
	- APPS类型模块位置比较集中，主要分布在以下几个目录：system/app、system/vital-app、system/priv-app、product/overlay、product/app、product/priv-app、vendor/app，APPS类型模块数量在上百个，而不可移除的模块只有少数几个，也就是说，我们APPS类型模块的移除列表也将近上百个，这是个很长的列表，为避免这种情况，我们的裁剪框架设计了这样一种方式，即在tiny-formatter/model/zebu/zebu_fles.mk文件中，定义变量 files_not_to_install ，将不需要安装的文件添加到该变量下，如下：
	```
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
	```
	`/system/app/%`表示不再往`/system/app/`目录下安装文件。而对于不可移除的APPS模块文件，我们在 zebu_modules_must_be_appened.mk 文件下定义了变量 modules_must_be_appended，将必须添加的模块添加到该变量下，如下：
	```
	# app/priv-app
	modules_must_be_appended += \
	DefaultContainerService \
	ExtServices \
	PackageInstaller \
	Settings \
	SettingsProvider \
	Shell \
	ExtShared \
	webview
	```
	- 不可移除的APPS类型模块列表：
	```
	ExtServices
	PackageInstaller
	SettingsProvider
	Shell
	ExtShared
	webview
	ims
	TeleService
	PermissionController
	```
<br \>
<br \>
<br \>
<br \>

## 6. androidQ 文件替换
- 文件替换，主要是在一些配置文件中使用，这类文件中有许多相关功能的配置，我们需要对一些配置进行屏蔽（也是需要通过反复验证来判断哪些功能的配置可以屏蔽），此时，就需要将已经验证好的文件去替换原有的文件。
- 在我们tiny-formatter文件替换有两种方式,一种是直接使用Android 编译提供的现成的文件拷贝机制，这种拷贝方式，我们主要在 tiny-formatter/model/zebu/zebu_product_copy_files.mk 文件中实现，如下：
	```
	TINY_PRODUCT_COPY_FILES += \
           $(TINY_BASE_DIR_ROOT)/model/$(TINY)/src/image/vendor/etc/permissions/handheld_core_hardware.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/handheld_core_hardware.xml
	```
- 另一种方式，使用Python脚本直接复制，这种方式，我们主要在 tiny-formatter/model/zebu/zebu_copy_file.sh 脚本中实现，如下：
	```
	cp -rf ${TINY_BASE_DIR_ROOT}/model/zebu/src/image/vendor/etc/vintf/manifest.xml ${PRODUCT_OUT}/vendor/etc/vintf/manifest.xml;
	```
- 两种文件拷贝方式，优先使用第一种方式，当某些文件拷贝导致Android编译失败时，此时，再考虑使用第二种方式。

<br \>
<br \>
<br \>
<br \>
## 7. androidQ 裁剪效率
- Android 模块的裁剪更像一个体力活，需要反复的来回验证，除了常用的二分法验证，就提高效率而言，我们更建议，在验证模块是否可移除的时候，使用mboot版本来验证，mboot版本的编译及使用，我们在《mboot验证》中已详细介绍。
- 使用mboot版本验证的一个好处是，我们可以在Android init阶段将验证的模块进行裁剪，而当该模块因为移除而导致系统无法正常启动时，在重启的过程中，我们无需再次将该模块文件push到手机里，即上一次删除的模块文件会在下一次重启时被恢复，这样我们的模块验证效率会大大提升。
- Android 裁剪的主要作用是减少将来img文件的大小，我们无需对所有模块进行验证，也没有这个必要，在对APP模块，配置文件，service模块进行裁剪后，如果还需要进一步压缩img的大小，我们可以查看此时Android工程编译后的install*.txt文件，从中筛选出较大的一些文件，再去裁剪其对应的模块即可。
