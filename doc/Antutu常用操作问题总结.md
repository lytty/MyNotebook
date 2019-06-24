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
---

# Antutu问题总结