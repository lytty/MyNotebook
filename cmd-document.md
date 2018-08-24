1. 服务器登录及文件传输
    - rdesktop -f 10.5.2.25 #远程登录天津本地服务器
    - rdesktop -f shwts01[shwts02] #远程登录上海外网
    - 上海外网传文件至天津外网：
    
        1. 上海外网（Windows系统）点击“开始”—“运行”——输入“\\shasync\Data_Exchange_Tunnel\To_Tianjin\PLD_APPS\haibin.xu” 放入文件
        2. 天津外网（Ubuntu系统）smb://tjnas1/data_exchange_tunnel/From_Shanghai/PLD_APPS/haibin.xu  将数据拖到个人电脑桌面上使用
    - 天津外网传文件至上海外网：
        1. 天津外网（Ubuntu系统）smb://tjnas1/data_exchange_tunnel/To_Shanghai/PLD&FAE&CPM/haibin.xu  将数据上传
        2. 上海外网（Windows系统）点击“开始”—“运行”——输入“\\shasync\Data_Exchange_Tunnel\From_Tianjin\PLD&FAE&CPM\haibin.xu” 将数据拖到个人电脑桌面上使用

2. PIP安装软件包时，国外的源下载速度太慢，浪费时间。而且经常出现下载过程中超时现象。所以把PIP安装源替换成国内镜	像，可以大幅提升下载速度，还可以提高安装成功率， pip install -i https://pypi.tuna.tsinghua.edu.cn/simple [软件包名]

3. python版本切换： 执行下面的命令手动去选择python 版本：
   sudo update-alternatives --config python

4. pip 安装： sudo apt-get install python3-pip

5. smb://10.5.2.210, 10.5.2.52(公司网络登录ip)

6. debin,ubuntu删除所有带 rc 标记的dpkg包:
   dpkg -l | grep ^rc | cut -d' ' -f3 | sudo xargs dpkg --purge

7. 网址收藏：
   Django学习： https://docs.djangoproject.com/zh-hans/2.0/
   http://mirror.nsc.liu.se/centos-store/6.8/isos/x86_64/CentOS-6.8-x86_64-bin-DVD1.iso

8. Django：
   Python2.7 只能支持django version < 2, Django 2.0+ 需要Python3
   Python2.7 安装django使用如下命令： sudo pip install  -i https://pypi.tuna.tsinghua.edu.cn/simple "django<2"

9. Anaconda:
   sudo ./Anaconda3-5.2.0-Linux-x86_64.sh 进行安装， 注意安装位置，默认安装在/root/anaconda3目录，建议修改为home
   删除时， 直接删除anaconda3目录即可（建议直接将该目录重命名，以免后期想使用时再重新安装）， 另外去除或注销.bashrc中的#export PATH=/***/anaconda3/bin:$PATH

10. apt-get remove --purge xxx # 移除应用及配置
    apt-get autoremove # 移除没用的包

11. 解决无法启动VS code和Chrome浏览器问题：
    sudo apt install libnss3=2:3.15.4-1ubuntu7

12. 模拟水平从下往上滑屏操作
    adb shell input swipe 500 500 500 200 

13. Android 代码下载
    repo init -u gitadmin@gitmirror.unisoc.com:android/platform/manifest.git -b sprdroid8.1_trunk
    repo sync的时候加上 -c --no-tags 参数会让下载加快
    repo init 也可以使用 -c --no-tags 啦，init过程飞快

14. 更改文件、文件夹归属
    sudo chown -R SPREADTRUM\\haibin.xu:SPREADTRUM\\domain^users file/dir

15. Android 代码编译
    source build/envsetup.sh
    lunch
    kheader
    make bootimage
    make -j8

16. Android 代码提交
    git pull
    git commit
    repo upload

17. 升级libnss后，有可能导致vs code、chrome浏览器启动失败，可使用以下命令进行解决：
    sudo apt install libnss3=2:3.15.4-1ubuntu7

18. apt-get remove 移除Python3库时，直接在库的名字上加3即可，例如：
    sudo apt-get remove python-six, 移除默认Python版本的库，
    sudo apt-get remove python3-six, 则移除Python3版本的库，