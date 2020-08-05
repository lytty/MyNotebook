# Common_cmd

## 1. 服务器操作

>   天津外网服务器

```
rdesktop -f 10.5.2.25 #远程登录天津本地服务器

```

>   上海外网服务器

```
rdesktop -f shwts19 [shwts02] #远程登录上海外网

```

>   编译服务器：

```
ssh -X haibin.xu@tjand02[(10.5.2.51)], 密码：外网密码

```

>   服务器与本地文件传输

```
scp authorized_keys haibin.xu@tjand02:~/.ssh

scp -r dt.img system.img kernel vendor.img spreadtrum\\haibin.xu@10.5.41.89:~/Desktop/sharkl5_8.1_img/sharkl5_8.1_img

多文件拷贝使用 `scp -r`

```



## 2. 天津上海文件传输

>   上海外网传文件至天津外网：

```
上海外网（Windows系统）点击“开始”—“运行”——输入“\\shasync\Data_Exchange_Tunnel\To_Tianjin\PLD_APPS\haibin.xu” 放入文件

天津外网（Ubuntu系统）smb://tjnas1/data_exchange_tunnel/From_Shanghai/PLD_APPS/haibin.xu  将数据拖到个人电脑桌面上使用

```

>   天津外网传文件至上海外网：

```
天津外网（Ubuntu系统）smb://tjnas1/data_exchange_tunnel/To_Shanghai/PLD&FAE&CPM/haibin.xu  将数据上传
 
上海外网（Windows系统）点击“开始”—“运行”——输入“\\shasync\Data_Exchange_Tunnel\From_Tianjin\PLD&FAE&CPM\haibin.xu” 将数据拖到个人电脑桌面上使用

```



## 3. 相关路径及网址：

>   ResearchDownload版本下载路径:

```
smb://shnas01/publicshared/ShareData/Debug_Tools/HistoryVersion

```

>   克隆盘保存路径：

```
 http://10.5.41.60:8000/l/images/apk/

```

>   公司网络ip

```
smb://10.5.2.210
smb://10.5.2.52

```



## 4. Python相关操作

>   安装pip

```
sudo apt-get install python3-pip

```

>   PIP安装软件包时，国外的源下载速度太慢，浪费时间。而且经常出现下载过程中超时现象。所以把PIP安装源替换成国内镜像，可以大幅提升下载速度，还可以提高安装成功率

```
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple [软件包名]

```

>   python版本切换，执行下面的命令手动去选择python 版本：

```
sudo update-alternatives --config python

```

>   Django学习：

-   https://docs.djangoproject.com/zh-hans/2.0/
-   http://mirror.nsc.liu.se/centos-store/6.8/isos/x86_64/CentOS-6.8-x86_64-bin-DVD1.iso

>   Django安装：

-   Python2.7 只能支持django version < 2, Django 2.0+ 需要Python3，Python2.7 安装django使用如下命令：

```
sudo pip install  -i https://pypi.tuna.tsinghua.edu.cn/simple "django<2"

```

>   Anaconda

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

>   apt-get remove 移除Python3库时，直接在库的名字上加3即可，例如：

```
sudo apt-get remove python-six, 移除默认Python版本的库，
sudo apt-get remove python3-six, 则移除Python3版本的库

```



## 5. Linux操作

>   debin,ubuntu删除所有带 rc 标记的dpkg包:

```
dpkg -l | grep ^rc | cut -d' ' -f3 | sudo xargs dpkg --purge

```

>   移除操作

```
apt-get remove --purge xxx # 移除应用及配置
apt-get autoremove # 移除没用的包
dpkg -l | grep ^rc | cut -d' ' -f3 | sudo xargs dpkg --purge

```

>   解决无法启动VS code和Chrome浏览器问题：

```
sudo apt install libnss3=2:3.15.4-1ubuntu7

```

>   更改文件、文件夹归属

```
sudo chown -R SPREADTRUM\\haibin.xu:SPREADTRUM\\domain^users file/dir

```

>   查看文件大小命令

```
目录： `du -h`
文件： `ll -h`

```

>   查看目录大小

```
du -sh [dir]

```

>   升级libnss后，有可能导致vs code、chrome浏览器启动失败，可使用以下命令进行解决：

```
sudo apt install libnss3=2:3.15.4-1ubuntu7

```

>   打patch时参数为： `patch -p1 < x.patch` 撤销方法为： `patch -Rp1 < x.patch` 

>   多线程下载命令: `axel -an [线程数] [网址]`

>   Linux下rm -rf删除文件夹报错_ Device or resource busy

```
1. 在终端执行 lsof +D 再加上无法删除文件的目录
2. kill -9 pid
3. sudo umount dir
4. rm -rf dir

```

>   SVN访问方式：

```
1. 浏览器： http://shexsvn01/!/#SYSSW/view/head/TJSYSPF
2. linux系统： svn co  http://shexsvn01/svn/SYSSW/TJSYSPF 也可以单独co一个特定的目录，比如tmp目录 svn co  http://shexsvn01/svn/SYSSW/TJSYSPF/tmp
3. windows服务器： 使用repo-browser，然后直接拖拽自己需要的文档到本地

```

>   sshfs mount远程服务器目录

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

>   视频转gif命令：ffmpeg -i vokoscreen-2019-07-29_11-33-40.mkv out.gif

>   meld命令，文件比对，类似于beyondcompare

>   pandoc文档格式转换

```
pandoc test.md -t dokuwiki -o test.txt

```

>   图片尺寸格式修改命令

```
mogrify -resize 356x294 -format png Image4.jpeg

```

>   如何去掉文件里的^M

1.   用vim打开那些在win编辑过的文档的时候执行如下操作
2.   `:set ff=unix`，这样那个^M的问题也顺带解决了

>   find相关命令

查找当前目录下以manif开头（不区分大小写）的文件： `find ./ -iname manif* -type f`

>   sysdump文件合并: `cat sysdump.core.* > systdump`

>   sysdump 触发方式

1.   命令方式（该方式为linux kernel默认自带功能）`echo 'c' > /proc/sysrq-trigger`
2.   组合键方式，根据不同项目手机组合键的方式可能不同，一般为同时按下音量上下键，然后连续两次按下power键

> 目录下所有文件内关键字替换

`grep -inr "a"  -rl ./* | xargs -i sed -i  "s/a/b/g" {}`

## 6. Android相关操作

>   Android 代码下载

```shell
repo init -u ssh://gitadmin@gitmirror.unisoc.com/platform/manifest -b <branch> -c --no-tags 
repo sync -c --no-tags 参数会让下载加快
repo init 也可以使用 -c --no-tags 啦，init过程飞快

```

>   9.0 代码下载

```shell
repo init -u ssh://gitadmin@gitmirror.unisoc.com/platform/manifest.git -b sprdroid9.0_trunk
repo sync -c -f

```

>   10.0代码下载

```shell
# http://wikiserver.spreadtrum.com/SoftwareSystem/wiki/Android10.0
repo init -u ssh://gitadmin@gitmirror.spreadtrum.com/platform/manifest.git -b sprdroidq_trunk
repo sync -c -f

```

>   更新manifest.xml

```shell
croot;
cd .repo/manifests;
[copy your manifest.xml to current directory]
croot;
repo init -m [your manifest file]

```

>   Android 代码编译

```
source build/envsetup.sh
lunch
kheader
make bootimage
make -j8

```
>   Android 代码提交

```
git pull
git commit
repo upload

```

>   串口log抓取命令

```
sudo minicom -D /dev/ttyUSB0 -C minicom.log
sudo gcom /dev/ttyUSB2

```

>   查看屏幕亮与否命令:

```
cat /sys/class/backlight/sprd_backlight/actual_brightness

```

>   模拟手机水平从下往上滑屏操作

```
adb shell input swipe 500 500 500 200 

```

>   researchDownload 读取手机分区内容到PC的方法：

1.   Flash Operations将需要从手机中dump出来的分区打钩
2.   Main Page下载界面只将FDL1和FDL2打钩
3.   点击下载，即可将手机文件dump到PC指定路径

>   本地制作userdata.img磁盘的方法和步骤

```
sudo apt install android-tools-fsutils
#新建一个data目录
#制作一个512M大小的userdata.img磁盘
make_ext4fs -T -1 -L data -l $((512*1024*1024)) -a data userdata.img data/

```

>   adb采集整机CPU使用率和分核CPU使用率

```
adb shell cat /proc/stat

```

>   img文件mount到本地

1.   查看img文件格式： `file vendor.img`
2.   如果是sprase格式，使用simg2img命令转换： 如 `simg2img vendor.img vendor.img.raw`
3.   mount到本地：`mkdir vendor; sudo mount -t ext4 -o rw vendor.img.raw vendor`

## 7. Vim/Vi相关操作

>   中字符串替换：

```
全替换： :%s/vivian/sky/（等同于 :g/vivian/s//sky/） 替换每一行的第一个 vivian 为 sky 
替换第一个:s/vivian/sky/ 替换当前行第一个 vivian 为 sky 
替换所有:s/vivian/sky/g 替换当前行所有 vivian 为 sky 

```

>   vi/vim 中如何在每行行首或行尾插入指定字符串 

-   行首 :%s/^/your_word/

- 行尾 :%s/$/your_word/

>   按键操作：

- 注释：ctrl+v 进入列编辑模式,向下或向上移动光标,把需要注释的行的开头标记起来,然后按大写的I,再插入注释符,比如”#”,再按Esc,就会全部注释了。
- 删除：先按v,进入visual模式,横向选中列的个数(如”#”注释符号,需要选中两列),再按Esc,再按ctrl+v 进入列编辑模式,向下或向上移动光标,选中注释部分,然后按d, 就会删除注释符号（#）。
- PS：当然不一定是shell的注释符”#”，也可以是”//”，或者其他任意的字符；vim才不知道什么是注释符呢，都是字符而已。

>   使用替换命令：

- 在全部内容的行首添加//号注释
    `:% s/^/\/\//g`
- 在2~50行首添加//号注释
    `:2,50 s/^/\/\//g`
- 在2~50行首删除//号
    `:2,50 s/^\/\///g`

>   vim鼠标模式打开与关闭

1) 开启鼠标模式

:set mouse=x, x取值如下, 例如:set mouse=a, 开启所有模式的mouse支持

```
n 普通模式
v 可视模式
i 插入模式
c 命令行模式
h 在帮助文件里，以上所有的模式
a 以上所有的模式
r 跳过 |hit-enter| 提示
A 在可视模式下自动选择
```

2) 关闭鼠标模式

:set mouse=, =后面不要跟任何值, 可以关闭鼠标模式

>   vim选中字符复制/剪切/粘贴

1) 进入 visual block 模式

```
d  剪切操作
y  复制操作
p  粘贴操作
^  选中当前行，光标位置到行首（或者使用键盘的HOME键）
$  选中当前行，光标位置到行尾（或者使用键盘的END键）
```

>   块插入相同字符

- 进入 visual block 模式
- 选中需要操作的行
- shift + i
- 编辑插入内容
- esc退出，查看编辑效果

>   刷新当前已打开的文件

- `：e`

>   查看和编辑二进制文件

- `vim -b egenea-base.ko`   加上-b参数，以二进制打开
- 然后输入命令 ` :%!xxd -g 1`  切换到十六进制模式显示

>   多行删除

- 首先在命令模式下，输入“：set nu”显示行号； 
- 通过行号确定你要删除的行； 
- 命令输入“：32,65d”,回车键，32-65行就被删除了
- :% g/abc/d 删除指定格式的行
- :g/^\s*$/d 删除空行

>   撤销与恢复撤销

- 撤销：u
- 恢复撤销：Ctrl + r

## 8. git操作

>   yp提交工具安装

-   查找tiny-formatter目录，获取路径“ssh://...”

```
haibin.xu@tjand02:~/sprdroid9.0_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git remote -v
korg	ssh://gitadmin@gitmirror.unisoc.com/vendor/sprd/proprietories-source/tiny-formatter (fetch)
korg	ssh://gitadmin@gitmirror.unisoc.com/vendor/sprd/proprietories-source/tiny-formatter (push)


```

-   本地拷贝

```
git clone ssh://gitadmin@gitmirror.unisoc.com/vendor/sprd/proprietories-source/tiny-formatter

```

- 切换分支

```
cd tiny-formatter
git branch -a
git checkout origin/sprdroid9.0_trunk

```

- 获取yp所在目录

```
cd tiny-formatter/tool
pwd
/home/local/SPREADTRUM/haibin.xu/tiny-formatter/tool

```

- 添加环境变量

```
vim ～/.bashrc
在最后添加：export PATH=/home/local/SPREADTRUM/haibin.xu/tiny-formatter/tool:$PATH
保存退出
source ～/.bashrc

```

>   git push出现“Read from socket failed: Connection reset by peer”问题

```
cd /etc/ssh;
sudo chmod 0644 *;
sudo chmod 0600 ssh_host_dsa_key ssh_host_rsa_key;
cd;sudo /etc/init.d/ssh restart;
回到原目录，重新push即可。

```

>   git stash

1) 在使用git的时候往往会保存一些东西，在保存的时候使用的就是git stash

2) 当利用git stash pop弹出来会有些耗费时间，这时可以使用git stash show来查看stash里面保存的内容

3) git stash时出错：needs merge ***, 解决：git reset HEAD， 然后再 git stash 即可

>   git add

1) git add . （空格+ 点） 表示当前目录所有文件，不小心就会提交其他文件

2) git add 如果添加了错误的文件的话

3) 撤销操作

```
git status 先看一下add 中的文件
git reset HEAD 如果后面什么都不跟的话 就是上一次add 里面的全部撤销了
git reset HEAD XXX/XXX/XXX.java 就是对某个文件进行撤销了

```

>   跟踪分支

1) 设定：远程主机名origin，远程分支名remoteBranch，本地分支名localBranch

2) 讨论两种情况：

```
一、远程分支存在，本地分支不存在

　　1、新建本地分支：git branch localBranch

　　　  然后跟踪本地分支：git branch -u origin/remoteBranch localBranch

　　2、直接新建并跟踪

　　　　1）git checkout --track origin/remoteBranch，但是这样新建的本地分支一定和跟踪的远程分支同名

　　　　2）git checkout -b localBranch origin/remoteBranch，这样新建的本地分支名（localBranch）可以自定义

二、远程分支不存在，本地分支存在

　　git push -u origin localBranch:remoteBranch
　　
```

3) 查看本地跟踪分支对应的远程分支：git branch -vv（两个v），就能够看到本地分支跟踪的远程分支

4) 其他相关命令

```
解除跟踪关系：git branch --unset-upstream localBranch

删除本地分支：git branch -d localBranch

强制删除本地分支：git branch -D localBranch

删除远程分支：git push origin --delete remoteBranch 或者 git push origin :remoteBranch

```

4) 实例 tiny-formatter：

```
haibin.xu@tjand02:~/sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git branch
* (detached from ac15a59)
haibin.xu@tjand02:~/sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git branch -a
* (detached from ac15a59)
  remotes/korg/master
  ...
  remotes/korg/sprdroidq_trunk
  ...
  remotes/m/sprdroidq_trunk -> korg/sprdroidq_trunk
haibin.xu@tjand02:~/sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git checkout -b sprdroidq_trunk korg/sprdroidq_trunk
Branch sprdroidq_trunk set up to track remote branch sprdroidq_trunk from korg.
Switched to a new branch 'sprdroidq_trunk'
haibin.xu@tjand02:~/sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git branch
* sprdroidq_trunk

haibin.xu@tjand02:~/sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git pull
From ssh://gitmirror.spreadtrum.com/vendor/sprd/proprietories-source/tiny-formatter
 * [new branch]      sprdroid9.0_trunk_18c_itel_cus_dev -> korg/sprdroid9.0_trunk_18c_itel_cus_dev
 * [new branch]      sprdroid9.0_trunk_sharkl5pro_binning_dev -> korg/sprdroid9.0_trunk_sharkl5pro_binning_dev
Already up-to-date.
haibin.xu@tjand02:~/sprdroidq_trunk/vendor/sprd/proprietories-source/tiny-formatter$ git pull .
From .
 * branch            HEAD       -> FETCH_HEAD
Already up-to-date.

```

>   为Android工程下所有项目建立跟踪分支： repo start localbranch --all

>   git commit

1) **git commit** 主要是将暂存区里的改动给提交到本地的版本库。每次使用git commit 命令我们都会在本地版本库生成一个40位的哈希值，这个哈希值也叫commit-id，commit-id在版本回退的时候是非常有用的，它相当于一个快照,可以在未来的任何时候通过与git reset的组合命令回到这里.

2) **git commit -m “message”** 这种是比较常见的用法，-m 参数表示可以直接输入后面的“message”，如果不加 -m参数，那么是不能直接输入message的，而是会调用一个编辑器一般是vim来让你输入这个message，message即是我们用来简要说明这次提交的语句。还有另外一种方法，当我们想要提交的message很长或者我们想描述的更清楚更简洁明了一点，我们可以使用这样的格式，如下：

```
git commit -m ‘

message1

message2

message3

’

```

3) **git commit -a -m “massage”** 其他功能如-m参数，加的-a参数可以将所有已跟踪文件中的执行修改或删除操作的文件都提交到本地仓库，即使它们没有经过git add添加到暂存区，注意，新加的文件（即没有被git系统管理的文件）是不能被提交到本地仓库的。建议一般不要使用-a参数，正常的提交还是使用git add先将要改动的文件添加到暂存区，再用git commit 提交到本地版本库。

4) **git commit --amend** 如果我们不小心提交了一版我们不满意的代码，并且给它推送到服务器了，在代码没被merge之前我们希望再修改一版满意的，而如果我们不想在服务器上abondon，那么我们怎么做呢？ **git commit --amend** 也叫追加提交，它可以在不增加一个新的commit-id的情况下将新修改的代码追加到前一次的commit-id中。

>   撤销git commit

使用**git reset --soft HEAD^**，注意，仅仅是撤回commit操作，您写的代码仍然保留

>   git show commit-id, 查看某个提交的修改内容

>   git log --author=haibin.xu, 查看某个owner的所有提交

>   cherry-pick撤销: git cherry-pick --abort

>   git revert,可以撤销指定的提交，而不影响该提交后面的已提交的内容

```
git revert -n 8b89621019c9adc6fc4d242cd41daeb13aeb9861

```

> 查看clone地址 `git remote -v`

## 9. 解压缩命令

>   tar

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

>   压缩

```
tar -cvf jpg.tar *.jpg //将目录里所有jpg文件打包成tar.jpg 

tar -czf jpg.tar.gz *.jpg   //将目录里所有jpg文件打包成jpg.tar后，并且将其用gzip压缩，生成一个gzip压缩过的包，命名为jpg.tar.gz

tar -cjf jpg.tar.bz2 *.jpg //将目录里所有jpg文件打包成jpg.tar后，并且将其用bzip2压缩，生成一个bzip2压缩过的包，命名为jpg.tar.bz2

tar -cZf jpg.tar.Z *.jpg   //将目录里所有jpg文件打包成jpg.tar后，并且将其用compress压缩，生成一个umcompress压缩过的包，命名为jpg.tar.Z

rar a jpg.rar *.jpg //rar格式的压缩，需要先下载rar for linux

zip jpg.zip *.jpg //zip格式的压缩，需要先下载zip for linux
```

>   解压

```
tar -xvf file.tar //解压 tar包

tar -xzvf file.tar.gz //解压tar.gz

tar -xjvf file.tar.bz2   //解压 tar.bz2

tar -xZvf file.tar.Z   //解压tar.Z

unrar e file.rar //解压rar

unzip file.zip //解压zip
```

>   总结

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

相关链接：https://www.cnblogs.com/manong--/p/8012324.html



## 10. opengrok配置

>   windows10 启动opengrok 

1.   java -Xmx524m -jar C:\opengrok\lib\opengrok.jar -W "C:\opengrok\data\configuration.xml" -c C:\ctags\ctags.exe -P -S -v -s "C:\opengrok\source" -d "C:\opengrok\data"
2.   java -Xmx524m -jar "D:\\Opengrok\\opengrok\\lib\\opengrok.jar" -W "D:\\Opengrok\\opengrok\\data\\configuration.xml" -c "C:\\ProgramData\\chocolatey\\lib\\universal-ctags\\tools\\ctags.exe" -P -S -v -s "D:\\Opengrok\\opengrok\\source" -d "D:\\Opengrok\\opengrok\\data"
3.   启动tomcat bin中的startup.bat

>   ubuntu 启动opengrok

1.   /opt/tomcat8/bin/shutdown.sh && /opt/tomcat8/bin/startup.sh
2.   opengrok-indexer -j /usr/lib/jvm/java-1.8.0-openjdk-amd64/bin/java -J=-Djava.util.logging.config.file=/var/opengrok/logging.properties -a /opt/opengrok/lib/opengrok.jar --  -s /index/src -d /opt/opengrok/database/data -H -P -S -G -W /opt/opengrok/etc/configuration.xml -U http://localhost:8080/source

>   ubuntu配置opengrok： https://luomuxiaoxiao.com/?p=56



## 11. clion快捷方式

```
ctrl+8	Show usage函数或变量使用信息快速提示框
ctrl+]	Find usage函数或变量使用信息详细展示，使用左下角窗体的上下箭头快速在代码文件遍历查看
ctrl+0	全局查找字符串
ctrl+n	查找类定义
ctrl+\	查找symbol定义
ctrl+p	往前跳
ctrl+[	往后跳
ctrl+i	调用关系层次结构Call Hierarchy
ctrl+h	列出类的继承关系，比如一个virtual方法，可以通过此方式找到类然后，进一步找到继承类对应的virtual方法实现
ctrl+-	折叠光标所在函数或类
ctrl+=	展开光标所在函数或类
ctrl+shift+n	打开文件
ctrl+shift+alt+n	查找symbol定义
ctrl+shift+[	跳转到当前代码所在函数或者类头部
ctrl+shift+]	跳转到当前代码所在函数或者类尾部
ctrl+shift+m	在靠近的最外层caret之间跳转，即括号匹配体中来回跳转
ctrl+shift+Backtrace	回到上一次编译的地方Last Edit Location
ctrl+shift+alt+Backtrace	回到下一次编辑的地方（自定义快捷键）Next Edit Location
ctrl+letf或right	前后按单词跳转
ctrl+g	跳转到指定行
ctrl+e	最近打开过的文件
alt+shift+c	查看最近修改过的文件（快速定位最近修改的文件挺方便的）
ctrl+q	显示注释文档
alt+↑/↓	快速定位方法头部
```

## 12 Excel快捷操作

1.  Excel如何多个单元格同时输入一样的文字
   - 打开Excel
   - 选中需要输入的单元格
   - 输入文字
   - 键盘同时按下【Ctrl】+【Enter】 
   - 完成输入! END
2. 