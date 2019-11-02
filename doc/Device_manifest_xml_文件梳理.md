# Android编译过程中对device manifest_*.xml类型文件的处理

## 1. 为什么要了解manifest_*.xml类型文件的处理

- 在`Android`优化裁剪过程中，我们有时会需要针对某一个`board`（如 `sprdroidq_trunk/device/sprd/sharkl5Pro`）下的`manifest_*.xml`文件进行调整，如：在整理`AndroidP sharkl5Pro source code overlay` 转译到`AndroidQ`上时，我们就遇到对 `sprdroidq_trunk/device/sprd/sharkl5Pro/common/manifest_main.xml`文件修改的问题，当然我们不可能直接对源文件进行修改，因为这样会影响到正常版本的编译，也不能将该文件直接拷贝到`vendor/sprd/proprietories-source/tiny-formatter`目录，以在编译的阶段进行替换，因为我们`tiny-formatter`的功能是针对所有项目的，不可能单独为某一个项目做针对性的修正。

- 那既然这样，我们就有必要查看在Android编译中对这些`manifest_*.xml`文件的处理流程。我们以`sprdroidq_trunk/device/sprd/sharkl5Pro/common/manifest_main.xml`文件为例来看该文件在编译过程中的流向。

  

## 2. 源码解析

- 文件`manifest_main.xml`路径：`sprdroidq_trunk/device/sprd/sharkl5Pro/common/manifest_main.xml`

- 查找该文件，发现如下代码：

  ```makefile
  [sprdroidq_trunk/device/sprd/sharkl5Pro/common/DeviceCommon.mk]
  
  DEVICE_MANIFEST_FILE += $(PLATCOMM)/manifest_main.xml
  
  ```

  从以上代码中我们可以知道，文件`manifest_main.xml`路径被赋值给了变量`DEVICE_MANIFEST_FILE`。

- 跟踪变量`DEVICE_MANIFEST_FILE`：

  ```makefile
  [sprdroidq_trunk/build/make/target/board/Android.mk]
  
  # Device Manifest
  ifdef DEVICE_MANIFEST_FILE
  # $(DEVICE_MANIFEST_FILE) can be a list of files
  include $(CLEAR_VARS)
  LOCAL_MODULE        := device_manifest.xml
  LOCAL_MODULE_STEM   := manifest.xml
  LOCAL_MODULE_CLASS  := ETC
  LOCAL_MODULE_PATH   := $(TARGET_OUT_VENDOR)/etc/vintf
  
  GEN := $(local-generated-sources-dir)/manifest.xml
  $(GEN): PRIVATE_DEVICE_MANIFEST_FILE := $(DEVICE_MANIFEST_FILE)
  $(GEN): $(DEVICE_MANIFEST_FILE) $(HOST_OUT_EXECUTABLES)/assemble_vintf
  	BOARD_SEPOLICY_VERS=$(BOARD_SEPOLICY_VERS) \
  	PRODUCT_ENFORCE_VINTF_MANIFEST=$(PRODUCT_ENFORCE_VINTF_MANIFEST) \
  	PRODUCT_SHIPPING_API_LEVEL=$(PRODUCT_SHIPPING_API_LEVEL) \
  	$(HOST_OUT_EXECUTABLES)/assemble_vintf -o $@ \
  		-i $(call normalize-path-list,$(PRIVATE_DEVICE_MANIFEST_FILE))
  
  LOCAL_PREBUILT_MODULE_FILE := $(GEN)
  include $(BUILD_PREBUILT)
  BUILT_VENDOR_MANIFEST := $(LOCAL_BUILT_MODULE)
  endif
  
  ```

  从以上代码中，我们可以看出`DEVICE_MANIFEST_FILE`最终被编译成`device_manifest.xml`模块，该模块对应文件即`$(TARGET_OUT_VENDOR)/etc/vintf/manifest.xml`，即`sprdroidq_trunk/device/sprd/sharkl5Pro/common/manifest_main.xml`最终将其内容合并到文件`out/target/product/ums512_1h10/vvendor/etc/vintf/manifest.xml`。

  

## 3. 修改策略

- 从源码解析中我们可以得出，`sprdroidq_trunk/device/sprd/sharkl5Pro/common/manifest_main.xml`最终将其内容合并到文件`out/target/product/ums512_1h10/vendor/etc/vintf/manifest.xml`。
- 而文件`out/target/product/ums512_1h10/vendor/etc/vintf/manifest.xml`的修改，我们是可以通过`tiny-formatter`的文件替换功能来实现的，我们将待替换的文件保存在 `sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter/model/zebu/src/image/vendor/etc/vintf/manifest.xml`，也就是说，无论我们想对文件`sprdroidq_trunk/device/sprd/sharkl5Pro/common/manifest_main.xml`做怎样的修改，都可转化为直接对`tiny-formatter`目录中对应的`manifest.xml`文件内做相应的修改。



## 4. 拓展

- 从针对某一个`board`的`manifest_main.xml`文件的修改转化为直接对`tiny-formatter/model/zebu/src/image/vendor/etc/vintf/manifest.xml`的修正，这种思路，或许对其他类似配置文件的转化有所启发。