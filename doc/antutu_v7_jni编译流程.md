# antutu v7 jni编译
## jni 路径
    ```
    |-- antutu
    |-- main.7000601.com.antutu.benchmark.full.obb
    |-- v7
    |   |-- CMakeLists.txt
    |   |-- README
    |   |-- app_v7_r5
    |   |-- gen
    |   `-- jni_r1
    `-- v8

    jni_r1
    |-- Android.mk
    |-- Application.mk
    |-- Doxyfile
    |-- PhysX
    |-- abench.c
    |-- abench.h
    |-- abenchn.cpp
    |-- antutu.c
    |-- antutulib.sublime-project
    |-- antutulib.sublime-workspace
    |-- aphysx.cpp
    |-- build.sh
    |-- cpu
    |-- curl
    |-- doxytheme
    |-- fillrate
    |-- info64
    |-- java
    |-- libpng
    |-- manpage.h
    |-- nbench
    |-- score_calculation.cpp
    |-- utils
    |-- view3d
    `-- zlib

    ```
---

## 编译环境配置
1. NDK版本
    - jni 默认使用android-ndk-r13b版本，下载链接：
    ```
    https://developer.android.google.cn/ndk/downloads/older_releases.html#ndk-13b-downloads
    ```
2. Platform
    - jni 默认使用Mac OS X Platform版本，darwin-x86_64编译链进行编译，因为Ubuntu上直接使用android-ndk-r13b-darwin-x86_64来编译的话，会因为代码格式问题编译出错，所以我们使用选用android-ndk-r13b-linux-x86_64版本；
3. 编译环境
    - 解压android-ndk-r13b-linux-x86_64.zip至预定目录, 如解压至目录/home/***/Android/android-ndk-r13b；
    - 在.bashrc中添加如下内容（NDK路径必须与解压路径保持一致）：
        ```
        NDK=/home/***/Android/android-ndk-r13b
        export NDK
        ```
    - 保存退出，执行 source .bashrc
---

## jni 编译
1. jni 默认使用android-ndk-r13b版本编译，而且其各模块内的脚本Makefile中默认使用的是darwin-x86_64编译链:
    ```
    PhysX/Snippets/compiler/android_x86/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/x86-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Snippets/compiler/android_arm/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Snippets/compiler/android_x86_64/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/x86_64-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Snippets/compiler/android_arm64/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Source/compiler/android_x86/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/x86-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Source/compiler/android_arm/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/arm-linux-androideabi-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Source/compiler/android_x86_64/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/x86_64-4.9/prebuilt/darwin-x86_64/bin
    PhysX/Source/compiler/android_arm64/Makefile:6:NDK_BIN_DIR = $(NDKROOT)/toolchains/aarch64-linux-android-4.9/prebuilt/darwin-x86_64/bin
    ```

2. 如果在Ubuntu上直接使用android-ndk-r13b-darwin-x86_64来编译的话，会因为代码格式问题编译出错，所以需要修正以上各Makefile中的编译链， 修改如下：
    ```
    “darwin-x86_64” 修正为 “linux-x86_64”
    ```

3. 编译libcpu
    ```
    jni_r1
    |-- cpu
    ```
    - cd cpu; 执行：$NDK/ndk-build NDK_PROJECT_PATH=./../../ APP_BUILD_SCRIPT=Android.mk

4. 删除相关文件中的“-pic”
    ```
    Snippets/compiler/android_x86_64/Makefile.SnippetHugePileOfConvexes.mk:215:SnippetHugePileOfConvexes_checked_lflags  += -fPIC -pic -Wl,-z,noexecstack -L$(NDKROOT)/sources/cxx-stl/gnu-libstdc++/4.9/libs/x86_64 -Wl,-rpath-link=$(NDKROOT)/platforms/android-21/arch-arm/usr/lib
    Snippets/compiler/android_x86_64/Makefile.SnippetHugePileOfConvexes.mk:338:SnippetHugePileOfConvexes_profile_lflags  += -fPIC -pic -Wl,-z,noexecstack -L$(NDKROOT)/sources/cxx-stl/gnu-libstdc++/4.9/libs/x86_64 -Wl,-rpath-link=$(NDKROOT)/platforms/android-21/arch-arm/usr/lib
    Snippets/compiler/android_x86_64/Makefile.SnippetHugePileOfConvexes.mk:459:SnippetHugePileOfConvexes_release_lflags  += -fPIC -pic -lcpu -Wl,-z,noexecstack -L$(NDKROOT)/sources/cxx-stl/gnu-libstdc++/4.9/libs/x86_64 -Wl,-rpath-link=$(NDKROOT)/platforms/android-21/arch-arm/usr/lib
    ```

5. 编译PhysX
- PhysX路径
    ```
    jni_r1
    |-- PhysX
    |   |-- Bin
    |   |-- Include
    |   |-- Snippets
    |   |-- Source
    |   |-- build.sh
    |   |-- media
    |   |-- readme_android.html
    |   |-- readme_ios.html
    |   |-- readme_linux.html
    |   |-- readme_osx.html
    |   |-- readme_win.html
    |   |-- release_notes.html
    |   `-- version-PhysX.txt
    ```
- cd PhysX; 执行编译脚本： ./build.sh
- 执行编译脚本后，在jni_r1/PhysX目录下会生成Lib目录并重写Bin目录，如下：
    ```
    |-- PhysX
    |    |-- Bin
    |   |   |-- android21_arm64
    |   |   |-- android21_x86_64
    |   |   |-- android9_neon
    |   |   |-- android9_x86
    |   |   `-- push.sh
    |   |-- Lib
    |   |   |-- android21_arm64
    |   |   |-- android21_x86_64
    |   |   |-- android9_neon
    |   |   `-- android9_x86
    ```
- 修正Lib、Bin目录下文件夹的名称：
    ```
    cd Bin;
    mv android21_arm64 arm64-v8a;
    mv android21_x86_64 x86_64;
    mv android9_neon armeabi-v7a;
    mv android9_x86 x86;
    cd ../Lib;
    mv android21_arm64 arm64-v8a;
    mv android21_x86_64 x86_64;
    mv android9_neon armeabi-v7a;
    mv android9_x86 x86;
    ```

6. 编译jni so
- cd jni_r1;
- 执行编译脚本： ./build.sh