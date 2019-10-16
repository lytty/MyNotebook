# Antutu常用操作
- 授权安装
  
    - sudo adb install -f -g antutu-benchmark-V7_3_1.apk; sudo adb install -f -g antutu_benchmark_v7_0_5_3d.apk
- 指定跑测case
    - sudo adb shell mkdir /sdcard/.antutu/
    - sudo adb push settings.xml /sdcard/.antutu/
- 启动命令
  
    - sudo adb shell am start -S -W -n com.antutu.ABenchMark/com.antutu.ABenchMark.ABenchMarkStart -e 74Sd42l35nH e57b6eb9906e27062fc7fcfcc820b957a5c33b649
- 获取结果
  
    - sudo adb shell cat /sdcard/.antutu/last_result.json
- Antutu测试项对应关系

  | 测试项 | 对应 |
  |-----:|------|
  |BID_3D_Refinery   |     GPU|
  |BID_3D_Coastline  | 	GPU|
  |BID_3D_Marooned   | 	GPU|
  |BID_3D_Physics    | 	CPU_MULTI|
  |BID_IMG_Fisheye   | 	UX_IMG|
  |BID_IMG_Blur      | 	UX_IMG|
  |BID_IMG_Decode    | 	UX_IMG|
  |BID_Delay  	   |	UX_USE_EXPERIENCE|
  |BID_WebView       |	UX_USE_EXPERIENCE|
  |BID_QRCode        |	UX_USE_EXPERIENCE|
  |BID_RAM_Speed     |	RAM|
  |BID_RAM_Access    | 	RAM|
  |BID_Storage       |	ROM|
  |BID_RandomIO      |	ROM|
  |BID_SequenceIO    | 	ROM|
  |BID_Database      |	ROM|
  |BID_FFT    	   |	CPU_MATH|
  |BID_GEMM   	   |	CPU_MATH|
  |BID_MAP    	   |	CPU_APP|
  |BID_PNG_Decode    | 	CPU_APP|
  |BID_2D_Physics    | 	CPU_APP|
  |BID_MultiThread   | 	CPU_MULTI|
  |BID_MultiTask     |	CPU_MULTI|
  |BID_HASH   	   |	UX_SEC|
  |BID_Secure        |	UX_SEC|
  |BID_XML    	   |	UX_DATA|
  |BID_Json   	   |	UX_DATA|
  |SID_RAM    	   |	RAM总分|
  |SID_ROM    	   |	ROM总分|
  |SID_CPU_MATH      |	CPU_MATH总分|
  |SID_CPU_APP       |    CPU_APP总分|
  |SID_CPU_MULTI     |	CPU_MULTI总分|
  |SID_UX_SEC        |	UX_SEC总分|
  |SID_UX_DATA       |	UX_DATA总分|
  |SID_UX_IMG        |	UX_IMG总分|
  |SID_UX_USE_EXPERIENCE | UX_USE_EXPERIENCE总分|
  |SID_3D_MAROONED   | 	GPU 3D_MAROONED分数|
  |SID_3D_COASTLINE  | 	GPU 3D_COASTLINE分数|
  |SID_3D_REFINERY   | 	GPU 3D_REFINERY分数|

---

# Antutu问题总结