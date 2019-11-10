# 1. 更新代码至最新

# 2. 修改TARGET_GPU_PLATFORM变量：

- sprdroidq_trunk/device/sprd/sharkl3目录下修改了以下3个文件：

  modified:   common/BoardCommon.mk
  modified:   s9863a1h10/s9863a1h10_Base.mk
  modified:   s9863a1h10/s9863a1h10_Natv.mk
  TARGET_GPU_PLATFORM := rogue 修改为 TARGET_GPU_PLATFORM := soft

# 3. gsp编译报错：

- HAL_PIXEL_FORMAT_BGRX_8888报错：

```
“vendor/sprd/modules/gsp/GspR6P0Plane/GspR6P0PlaneImage.cpp:558:8: error: duplicate case value 'HAL_PIXEL_FORMAT_BGRA_8888'
  	case HAL_PIXEL_FORMAT_BGRX_8888:”

```

修改：`sprdroidq_trunk/vendor/sprd/external/drivers/gpu/soft/include/mali_gralloc_buffer.h `文件中增加如下patch

```
--- a/soft/include/mali_gralloc_buffer.h
+++ b/soft/include/mali_gralloc_buffer.h
@@ -77,6 +77,7 @@ enum
     HAL_PIXEL_FORMAT_YCbCr_420_SP = 0x15, /*OMX_COLOR_FormatYUV420SemiPlanar*/
     HAL_PIXEL_FORMAT_YCrCb_422_SP = 0x1B,
     HAL_PIXEL_FORMAT_YCrCb_420_P  = 0x1C,
+    HAL_PIXEL_FORMAT_BGRX_8888 = 0x107,
 };
 
 #ifdef __cplusplus

```



- MALI_YUV_BT2020_NARROW、MALI_YUV_BT2020_WIDE报错：

```
./vendor/sprd/external/drivers/gpu/gralloc_public.h:199:26: error: use of undeclared identifier 'MALI_YUV_BT2020_NARROW'
        USC_YUV_BT2020_NARROW = MALI_YUV_BT2020_NARROW,
                                ^
./vendor/sprd/external/drivers/gpu/gralloc_public.h:200:26: error: use of undeclared identifier 'MALI_YUV_BT2020_WIDE'
        USC_YUV_BT2020_WIDE   = MALI_YUV_BT2020_WIDE,

```

修改：`vendor/sprd/external/drivers/gpu/soft/include/mali_gralloc_private_interface_types.h`文件中增加第50、51两行

```
43 typedef enum
44 {
45         MALI_YUV_NO_INFO,
46         MALI_YUV_BT601_NARROW,
47         MALI_YUV_BT601_WIDE,
48         MALI_YUV_BT709_NARROW,
49         MALI_YUV_BT709_WIDE,
50         MALI_YUV_BT2020_NARROW,
51         MALI_YUV_BT2020_WIDE
52 } mali_gralloc_yuv_info;

```

- gsp编译通过
- gsp问题可以咨询chen.he(贺晨)

# 4. opengl编译问题

