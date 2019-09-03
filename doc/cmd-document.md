1. 服务器登录及文件传输
    - rdesktop -f 10.5.2.25 #远程登录天津本地服务器
    - rdesktop -f shwts01 [shwts02] #远程登录上海外网
    - 上海外网传文件至天津外网：
        1. 上海外网（Windows系统）点击“开始”—“运行”——输入“\\shasync\Data_Exchange_Tunnel\To_Tianjin\PLD_APPS\haibin.xu” 放入文件
        2. 天津外网（Ubuntu系统）smb://tjnas1/data_exchange_tunnel/From_Shanghai/PLD_APPS/haibin.xu  将数据拖到个人电脑桌面上使用
    - 天津外网传文件至上海外网：
        1. 天津外网（Ubuntu系统）smb://tjnas1/data_exchange_tunnel/To_Shanghai/PLD&FAE&CPM/haibin.xu  将数据上传
        2. 上海外网（Windows系统）点击“开始”—“运行”——输入“\\shasync\Data_Exchange_Tunnel\From_Tianjin\PLD&FAE&CPM\haibin.xu” 将数据拖到个人电脑桌面上使用
    - ResearchDownload: smb://shnas01/publicshared/ShareData/Debug_Tools/HistoryVersion
---

2. PIP安装软件包时，国外的源下载速度太慢，浪费时间。而且经常出现下载过程中超时现象。所以把PIP安装源替换成国内镜	像，可以大幅提升下载速度，还可以提高安装成功率， pip install -i https://pypi.tuna.tsinghua.edu.cn/simple [软件包名]
---

3. python版本切换： 执行下面的命令手动去选择python 版本：
   sudo update-alternatives --config python
---

4. pip 安装： sudo apt-get install python3-pip
---

5. smb://10.5.2.210, 10.5.2.52(公司网络登录ip)
---

6. debin,ubuntu删除所有带 rc 标记的dpkg包:
   dpkg -l | grep ^rc | cut -d' ' -f3 | sudo xargs dpkg --purge
---

7. 网址收藏：
   Django学习： https://docs.djangoproject.com/zh-hans/2.0/
   http://mirror.nsc.liu.se/centos-store/6.8/isos/x86_64/CentOS-6.8-x86_64-bin-DVD1.iso
---

8. Django：
   Python2.7 只能支持django version < 2, Django 2.0+ 需要Python3
   Python2.7 安装django使用如下命令： sudo pip install  -i https://pypi.tuna.tsinghua.edu.cn/simple "django<2"
---

9. Anaconda:
   - sudo ./Anaconda3-5.2.0-Linux-x86_64.sh 进行安装， 注意安装位置，默认安装在/root/anaconda3目录，建议修改为home
   - 删除时， 直接删除anaconda3目录即可（建议直接将该目录重命名，以免后期想使用时再重新安装）， 另外去除或注销.bashrc中的#export PATH=/***/anaconda3/bin:$PATH
   - 如果本地同时安装有anaconda3，　anaconda２，可通过在.bashrc文件中屏蔽一个，开启另一个来切换anaconda版本，切换后，务必重新执行一下.bashrc文件
   - 常用命令：
        ```
        activate  // 切换到base环境
        activate learn // 切换到learn环境
        conda create -n learn python=3  // 创建一个名为learn的环境并指定python版本为3(的最新版本)
        conda env list // 列出conda管理的所有环境
        conda list // 列出当前环境的所有包
        conda install requests 安装requests包
        conda remove requests 卸载requets包
        conda remove -n learn --all // 删除learn环境及下属所有包
        conda update requests 更新requests包
        conda env export > environment.yaml  // 导出当前环境的包信息
        conda env create -f environment.yaml  // 用配置文件创建新的虚拟环境
        ```
---

10. apt-get remove --purge xxx # 移除应用及配置
    apt-get autoremove # 移除没用的包
    dpkg -l | grep ^rc | cut -d' ' -f3 | sudo xargs dpkg --purge
---

11. 解决无法启动VS code和Chrome浏览器问题：
    sudo apt install libnss3=2:3.15.4-1ubuntu7
---

12. 模拟水平从下往上滑屏操作
    adb shell input swipe 500 500 500 200 
---

13. Android 代码下载
    ```shell
    repo init -u ssh://gitadmin@gitmirror.unisoc.com/platform/manifest -b <branch> -c --no-tags 
    repo sync -c --no-tags 参数会让下载加快
    repo init 也可以使用 -c --no-tags 啦，init过程飞快
    ```

    9.0 代码下载
    
    ```shell
    repo init -u ssh://gitadmin@gitmirror.unisoc.com/platform/manifest.git -b sprdroid9.0_trunk
    repo sync -c -f
    ```

    
    10.0代码下载
    
    ```shell
    # http://wikiserver.spreadtrum.com/SoftwareSystem/wiki/Android10.0
    repo init -u ssh://gitadmin@gitmirror.spreadtrum.com/platform/manifest.git -b sprdroidq_trunk
    repo sync -c -f
    ```

    更新manifest.xml
    
    ```shell
    croot;
    cd .repo/manifests;
    [copy your manifest.xml to current directory]
    croot;
    repo init -m [your manifest file]
    ```
---

14. - 更改文件、文件夹归属
    `sudo chown -R SPREADTRUM\\haibin.xu:SPREADTRUM\\domain^users file/dir`
    - 查看目录大小
    `du -sh [dir]`
---

15. - Android 代码编译
```
        source build/envsetup.sh
        lunch
        kheader
        make bootimage
        make -j8
```
    - 编译服务器：
        - ssh -X haibin.xu@tjand02[(10.5.2.51)], 密码：外网密码
        - 文件拷贝：
            - `scp authorized_keys haibin.xu@tjand02:~/.ssh`
            - `scp -r dt.img system.img kernel vendor.img spreadtrum\\haibin.xu@10.5.41.70:~/Desktop/sharkl5_8.1_img/sharkl5_8.1_img`
            - 多文件拷贝使用 `scp -r`


    - 注： 更改manifest.xml后， 需要执行 repo init -m defaul.xml 已更新此xml下的代码
---

16. Android 代码提交
    git pull
    git commit
    repo upload
---

17. 升级libnss后，有可能导致vs code、chrome浏览器启动失败，可使用以下命令进行解决：
    sudo apt install libnss3=2:3.15.4-1ubuntu7
---

18. apt-get remove 移除Python3库时，直接在库的名字上加3即可，例如：
    sudo apt-get remove python-six, 移除默认Python版本的库，
    sudo apt-get remove python3-six, 则移除Python3版本的库
---

19. 打patch时参数为： `patch -p1 < x.patch` 撤销方法为： `patch -Rp1 < x.patch` 
---

20. vim/vi 中字符串替换：
    - 全替换： :%s/vivian/sky/（等同于 :g/vivian/s//sky/） 替换每一行的第一个 vivian 为 sky 
    - 单行替换： 
        - 替换第一个:s/vivian/sky/ 替换当前行第一个 vivian 为 sky 
        - 替换所有:s/vivian/sky/g 替换当前行所有 vivian 为 sky 
---

21. 串口log抓取命令：
    `sudo minicom -D /dev/ttyUSB0 -C minicom.log`
    `sudo gcom /dev/ttyUSB2`
---

22. 查看屏幕亮与否命令:
    - `cat /sys/class/backlight/sprd_backlight/actual_brightness`
---

23. researchDownload 读取手机分区内容到PC的方法：
    - Flash Operations将需要从手机中dump出来的分区打钩
    - Main Page下载界面只将FDL1和FDL2打钩
    - 点击下载，即可将手机文件dump到PC指定路径
---

24. 多线程下载命令：
    `axel -an [线程数] [网址]`
---

25. 查看文件大小命令：
    目录： `du -h`；
    文件： `ll -h`;
---

26. 本地制作userdata.img磁盘的方法和步骤
    ```
    sudo apt install android-tools-fsutils
    #新建一个data目录
    #制作一个512M大小的userdata.img磁盘
    make_ext4fs -T -1 -L data -l $((512*1024*1024)) -a data userdata.img data/
    ```
---

27. Linux下rm -rf删除文件夹报错_ Device or resource busy
    ```
    1. 在终端执行 lsof +D 再加上无法删除文件的目录
    2. kill -9 pid
    3. sudo umount dir
    4. rm -rf dir
    ```
---

28. adb采集整机CPU使用率和分核CPU使用率
    ```
    adb shell cat /proc/stat
    ```
---

29. SVN访问方式：
    ```
    1. 浏览器： http://shexsvn01/!/#SYSSW/view/head/TJSYSPF
    2. linux系统： svn co  http://shexsvn01/svn/SYSSW/TJSYSPF 也可以单独co一个特定的目录，比如tmp目录 svn co  http://shexsvn01/svn/SYSSW/TJSYSPF/tmp
    3. windows服务器： 使用repo-browser，然后直接拖拽自己需要的文档到本地
    ```
---

30. sshfs mount远程服务器目录
    ```
    1. 安装sshfs
        $ sudo apt-get install sshfs
    2. 创建本地mount目录
        $ mkdir ~43
    3. 将远程服务器目录mount到本地
        $ sshfs "luther.ge@10.5.2.43:" ~/43
    4. 操作43目录
        $ ls ~/43
    ```
---

31. yp提交工具安装
    - 查找tiny-formatter目录，获取路径“ssh://...”
        ‘’‘
        haibin.xu@tjand02:~/sprdroid9.0_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git remote -v
        korg	ssh://gitadmin@gitmirror.unisoc.com/vendor/sprd/proprietories-source/tiny-formatter (fetch)
        korg	ssh://gitadmin@gitmirror.unisoc.com/vendor/sprd/proprietories-source/tiny-formatter (push)
        ’‘’
    - 本地拷贝
        ‘’‘
        git clone ssh://gitadmin@gitmirror.unisoc.com/vendor/sprd/proprietories-source/tiny-formatter
        ’‘’
    - 切换分支
        ‘’‘
        cd tiny-formatter
        git branch -a
        git checkout origin/sprdroid9.0_trunk
        ’‘’
    - 获取yp所在目录
        ‘’‘
        cd tiny-formatter/tool
        pwd
        /home/local/SPREADTRUM/haibin.xu/tiny-formatter/tool
        ’‘’
    - 添加环境变量
        ‘’‘
        vim ～/.bashrc
        在最后添加：export PATH=/home/local/SPREADTRUM/haibin.xu/tiny-formatter/tool:$PATH
        保存退出
        source ～/.bashrc
        ’‘’
---

32. 解压缩命令
- tar
    ```
    -c: 建立压缩档案
    -x：解压
    -t：查看内容
    -r：向压缩归档文件末尾追加文件
    -u：更新原压缩包中的文件

    这五个是独立的命令，压缩解压都要用到其中一个，可以和别的命令连用但只能用其中一个。下面的参数是根据需要在压缩或解压档案时可选的。

    -z：有gzip属性的
    -j：有bz2属性的
    -Z：有compress属性的
    -v：显示所有过程
    -O：将文件解开到标准输出

    下面的参数-f是必须的

    -f: 使用档案名字，切记，这个参数是最后一个参数，后面只能接档案名。
    
    # tar -cf all.tar *.jpg
    这条命令是将所有.jpg的文件打成一个名为all.tar的包。-c是表示产生新的包，-f指定包的文件名。

    # tar -rf all.tar *.gif
    这条命令是将所有.gif的文件增加到all.tar的包里面去。-r是表示增加文件的意思。

    # tar -uf all.tar logo.gif
    这条命令是更新原来tar包all.tar中logo.gif文件，-u是表示更新文件的意思。

    # tar -tf all.tar
    这条命令是列出all.tar包中所有文件，-t是列出文件的意思

    # tar -xf all.tar
    这条命令是解出all.tar包中所有文件，-t是解开的意思
    ```

- 压缩
    ```
    tar -cvf jpg.tar *.jpg //将目录里所有jpg文件打包成tar.jpg 

    tar -czf jpg.tar.gz *.jpg   //将目录里所有jpg文件打包成jpg.tar后，并且将其用gzip压缩，生成一个gzip压缩过的包，命名为jpg.tar.gz

    tar -cjf jpg.tar.bz2 *.jpg //将目录里所有jpg文件打包成jpg.tar后，并且将其用bzip2压缩，生成一个bzip2压缩过的包，命名为jpg.tar.bz2

    tar -cZf jpg.tar.Z *.jpg   //将目录里所有jpg文件打包成jpg.tar后，并且将其用compress压缩，生成一个umcompress压缩过的包，命名为jpg.tar.Z

    rar a jpg.rar *.jpg //rar格式的压缩，需要先下载rar for linux

    zip jpg.zip *.jpg //zip格式的压缩，需要先下载zip for linux
    ```

- 解压
    ```
    tar -xvf file.tar //解压 tar包

    tar -xzvf file.tar.gz //解压tar.gz

    tar -xjvf file.tar.bz2   //解压 tar.bz2

    tar -xZvf file.tar.Z   //解压tar.Z

    unrar e file.rar //解压rar

    unzip file.zip //解压zip
    ```
- 总结
    ```
    1、*.tar 用 tar -xvf 解压

    2、*.gz 用 gzip -d或者gunzip 解压

    3、*.tar.gz和*.tgz 用 tar -xzf 解压

    4、*.bz2 用 bzip2 -d或者用bunzip2 解压

    5、*.tar.bz2用tar -xjf 解压

    6、*.Z 用 uncompress 解压

    7、*.tar.Z 用tar -xZf 解压

    8、*.rar 用 unrar e解压

    9、*.zip 用 unzip 解压
    ```
- https://www.cnblogs.com/manong--/p/8012324.html
---

33. windows10 启动opengrok 
- java -Xmx524m -jar C:\opengrok\lib\opengrok.jar -W "C:\opengrok\data\configuration.xml" -c C:\ctags\ctags.exe -P -S -v -s "C:\opengrok\source" -d "C:\opengrok\data"
- java -Xmx524m -jar "G:\\opengrok-1.2.8\\lib\\opengrok.jar" -W "G:\\opengrok-1.2.8\\data\\configuration.xml" -c "C:\\Program Files\\opengrok\\ctags\\ctags.exe" -P -S -v -s "G:\\opengrok-1.2.8\\source" -d "G:\\opengrok-1.2.8\\data"
- 启动tomcat bin中的startup.bat

34. ubuntu 启动opengrok
- /opt/tomcat8/bin/shutdown.sh && /opt/tomcat8/bin/startup.sh
- opengrok-indexer -j /usr/lib/jvm/java-1.8.0-openjdk-amd64/bin/java -J=-Djava.util.logging.config.file=/var/opengrok/logging.properties -a /opt/opengrok/lib/opengrok.jar --  -s /index/src -d /opt/opengrok/database/data -H -P -S -G -W /opt/opengrok/etc/configuration.xml -U http://localhost:8080/source
- ubuntu配置opengrok： https://luomuxiaoxiao.com/?p=56

35. 视频转gif命令：ffmpeg -i vokoscreen-2019-07-29_11-33-40.mkv out.gif

36. mboot打开adbd：
    - 在5s的阶段：
    adbd-setup.sh; sleep 1; rm /system/bin/sh; ln -s /msystem/bin/sh /system/bin/sh

37. git push出现“Read from socket failed: Connection reset by peer”问题：
    - cd /etc/ssh;
    - sudo chmod 0644 *;
    - sudo chmod 0600 ssh_host_dsa_key ssh_host_rsa_key;
    - cd;sudo /etc/init.d/ssh restart;
    回到原目录，重新push即可。