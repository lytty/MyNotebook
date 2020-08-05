# 测试代码Review及内网上传分支流程

## 1. 测试代码Review

- 测试用例脚本量大，数千个、上万个、十几万个脚本都是有可能的，如果将这些脚本上传到云桌面特定分支下，在bitbucket平台下review代码，逐字句敲键盘添加批注，在有限review人员，有限的时间内，几乎不可能完成，而且效率极其的低。
- 基于以下两点考虑，我们可以做到以较少的review人员，在有限的时间内，实现对大量脚本代码进行review，并高效率的添加批注。
  1.  编码工具Pycharm具备的实时模板功能；
  2.  测试模块下每个测试脚本只有测试步骤稍微的不同，这就一个规范问题可能出现在众多脚本中同时出现。
- 需要做的改变：
  1.  review代码不能放在内网云桌面bitbucket平台下进行；
  2.  添加批注只能在pycharm工具中来进行；
  3.  考虑到我们外网的便捷性，需要在外网配置单独的代码机，在其上面搭建Git代码管理仓库，供部门内部人员同步更新代码使用；
  4.  待外网脚本完全通过review后，可以统一传送到内网云桌面指定分支下。



### 1.1 测试代码review流程

1.  测试脚本编写人员将本地代码上传到外网指定仓库；
2.  review人员本地同步代码开始review，将不规范的代码标注出来，同时把带有标注的代码同步到远程仓库；
3.  测试脚本编写人员同步远程代码，根据标注进行代码修正，并将标注移除；
4.  测试脚本编写人员将已修正的最新代码上传到远程仓库。



### 1.2 外网代码机远程仓库

#### 1.2.1 本地外网环境配置

1.  本地（Windows10系统）安装Git（下载链接：https://git-scm.com/），安装完成后，打开Git Bash；![image-20200717164842408](F:\MyNotebook\doc\picture\git-1.png)

2.  进入Git Bash后，切换到自己将要下载代码的路径，如下：![image-20200717165129453](F:\MyNotebook\doc\picture\git-2.png)

3.  如果习惯使用Linux终端，可在本地Microsoft Store下载Ubuntu仿真终端，如下：![image-20200717165509137](F:\MyNotebook\doc\picture\remote1.png)![image-20200717165818549](F:\MyNotebook\doc\picture\remote2.png)

   安装最新版本即可，安装完毕后，打开Ubuntu 20.04 LTS，如下图，使用Linux终端时，不需要安装Windows版本的git，如果当前终端没有git，直接使用Linux 命令`sudo apt install git`安装即可：![image-20200717170258356](F:\MyNotebook\doc\picture\remote3.png)

4.  本地生成ssh公钥，在Git Bash窗口下，.ssh目录下如果没有如图所示的三个文件，则需要在本地手动生成ssh公钥，生成指令`ssh-keygen.exe`，如果是在Ubuntu仿真终端窗口下，则执行指令为`ssh-keygen`，默认安装到`~/.ssh`目录下。 ![image-20200803202232959](F:\MyNotebook\doc\picture\ssh.png)

5.  Git版本管理系统为程序员必备知识，务必熟学熟用，推荐学习网址：https://www.liaoxuefeng.com/wiki/896043488029600/896067008724000



#### 1.2.2 代码远程仓库

- 我们的代码机存放在许海宾工位处，代码机24小时不断电，已搭建好Git仓库，除管理员外，其他人不要擅自登陆代码机，更不可擅自修改远程仓库。

- 远程仓库路径：`xuhb@10.2.19.21:/home/xuhb/code/test.git`。

- 远程仓库同步到本地：`git clone xuhb@10.2.19.21:/home/xuhb/code/test.git`，会提示需要输入密码：123@abAB，后续提交操作需要输入密码的话，都是此密码。

- 因为每次同步、更新代码都需要输入密码，为减少密码频繁输入，可以将本地的`id_rsa.pub`文件发送给仓库管理员，经仓库管理员授权后，本地同步、更新代码时就不用再输入密码了。

- 当前远程仓库代码目录如下图所示，目前主要维护`test/esat/scripts/libs, test/esat/scripts/module_scripts`两个目录，`test/esat/scripts/libs`为公共库代码，`test/esat/scripts/module_scripts`为测试用例脚本，其他代码，因相关owner未同步远程仓库，暂未维护。                                                      ![image-20200804090349709](F:\MyNotebook\doc\picture\i1.png)

- `test`作为一个工程导入到`pycharm IDE`中，会在当前目录及其子目录下生成`.idea, __pycache__`相关目录，而这些目录及其包含的文件是不需要上传到我们的远程仓库的，这里提供一个方法，在`test`目录下创建`.gitignore`文件，写入以下内容，这样在每次执行代码上传操作时，可以让`git`自动忽略这些文件，当然，你也可以添加其他自己不想上传到远程仓库的文件：

  ```
  .idea
  /esat/scripts/module_scripts/my_case/*
  /esat/scripts/module_scripts/initial_case/cmd_test_1.py
  *__pycache__*
  ```

  

#### 1.2.3 git常用指令 

- 代码下载到本地，即可对自己负责的代码进行更新、提交，常用操作指令如下：

  > 同步远程仓库命令：`git pull`

  > 代码提交相关命令：`git add .`, `git commit -m "***"`, `git push origin master`

  > 撤销`git add`操作：

  ```
  git reset HEAD 如果后面什么都不跟的话 就是上一次add 里面的全部撤销了
  git reset HEAD XXX/XXX/XXX.java 就是对某个文件进行撤销了
  ```

  > 撤销`git commit`操作：

  ```
  git reset --soft HEAD^
  ```



### 1.3 Pycharm工具使用

#### 1.3.1 Pycharm安装

- `Pycharm IDE`直接去官方下载安装就可以，https://www.jetbrains.com/pycharm/download/#section=windows，需要注意的是，请下载`Community`版本，![image-20200804093117897](F:\MyNotebook\doc\picture\i3.png)



#### 1.3.2 Pycharm配置Python

- 关于`Pycharm`配置`Python`解释器的方法，网上有很多，此处不再过多介绍，大家可以自行搜索，如：https://www.cnblogs.com/lifangzheng/p/11122240.html
- `Python`解释器的安装，大家可以直接下载官方`Python`(https://www.python.org/)，也可以安装`Anaconda`(https://www.anaconda.com/products/individual)，`Anaconda`是一个开源的`Python`发行版本，其包含了`conda、Python`等180多个科学包及其依赖项。



#### 1.3.3 Pycharm导入代码

- 代码导入，如下图，直接`open`自己代码目录就可以：![image-20200804092804874](F:\MyNotebook\doc\picture\i2.png)



#### 1.3.4 Pycharm安装 Autopep8 插件

- 我们所有的代码必须符合`PEP8`编程规范，所以需要在`Pycharm IDE`中安装`Autopep8`插件，使得`Pycharm IDE`工具可以按照`PEP8`规范自动检查我们的代码。

- `Pycharm IDE`中安装`Autopep8`插件的方法，可以自行网上搜索，https://blog.csdn.net/CPS1016347441/article/details/100377084

- 当代码不符合`PEP8`规范时，`Pycharm IDE`会自动提示，如下图所示，只需按照提示相应修改就可以：![image-20200804102107832](F:\MyNotebook\doc\picture\i5.png)

  当消除所有提示后，则表明我们的代码已符合`PEP8`规范，此时，右上角会有一个绿色的对号显示，如下图所示：![image-20200804102631389](F:\MyNotebook\doc\picture\i4.png)



#### 1.3.5 Pycharm 调试代码

- 代码调试不只有添加log，然后运行打印log这么单调，`Pycharm IDE`同其他`IDE`工具一样，同样可以单步、打断点、步入函数调试，相关调试方法可以参考链接：https://blog.csdn.net/u011331731/article/details/72801449/

- 常用调试快捷键如下：

  ```
  F7: 进入函数
  F8：单步调试
  F9：执行到下个断点处
  ```

  注意，如果本地执行这三个快捷键没有反应，请先操作`Fn + Esc`，然后再使用。



#### 1.3.6 Pycharm 使用技巧

- 我们所有的脚本几乎都会以类似下面的格式来开头，                        ![image-20200804103049075](F:\MyNotebook\doc\picture\i6.png)

  为避免重复性操作，`Pycharm IDE`提供了`python`脚本模板配置功能，配置方法如下：![image-20200804103430388](F:\MyNotebook\doc\picture\i7.png)

  这样，在我们每次创建一个新的`python`脚本时，就会自动把模板中的内容填写进来。

- `Pycharm IDE`的实时模板功能，为我们添加一些固定的标注信息提供了可能，如下图所示，![image-20200804104115604](F:\MyNotebook\doc\picture\i8.png)

  这样，当我们在代码中键入`hc`时，`Pycharm IDE`会自动显示模板匹配信息，如下：![image-20200804104331220](F:\MyNotebook\doc\picture\i9.png)

  选择后，会在当前位置自动填充模板信息，时间为当前添加时间，我们review测试用例脚本时，添加批注信息就是使用的这个功能：![image-20200804104629526](F:\MyNotebook\doc\picture\i10.png)



### 1.4 测试代码Review

- 在`Review`代码前，务必要在本地同步更新代码，使当前的代码处于最新状态，如下图所示：![image-20200804105429434](F:\MyNotebook\doc\picture\i11.png)

- `Review`代码目前只关注规范问题，至于代码的合理性问题，需代码编写人员自行调试运行修正，批注信息需保持统一格式，这样便于后期统计信息，如：![image-20200804104629526](F:\MyNotebook\doc\picture\i10.png)

- 如果在`Review`代码的过程中，其他人同步更新了远程分支，当本地`Review`代码结束后需要上传带有批注信息的代码时，因为本地代码已经不是最新的代码了，此时可以通过如下操作进行提交：

  ```
  git stash; #将添加批注信息的代码保存到暂存区中
  git pull;  #更新本地代码
  git stash pop; #将带有批注的修改添加到最新的代码中,此过程可能会有冲突，需解决冲突后，再进行后续步骤
  git add .;
  git commit -m "****";
  git push origin master
  ```

- 在`Review`代码的过程中，对于一些通用的规范问题，或不在规范内的其他问题，需总结规范，并定期更新部门规范文档，以及在内部群里列出问题供大家及时参考校正，如下图所示：![image-20200804112602434](F:\MyNotebook\doc\picture\i12.png)

- 编码规范补充文档会定期更新到我们的WPS云文档中，目前最新版本：`存储研发六部/6-规范文档/PS3编码规范补充_Python_20200801_许海宾.docx`



## 2. 代码内网上传

### 2.1 内网云桌面登陆

- 软件：`VMware Horizon Client`
- 添加服务器，如下图：![image-20200804153002455](F:\MyNotebook\doc\picture\i15.png)
- 点击连接，如下图：![image-20200804153052996](F:\MyNotebook\doc\picture\i16.png)
- 点击继续，进入登陆界面，账号为自己邮箱前缀，如下：![image-20200804153227028](F:\MyNotebook\doc\picture\i17.png)
- 登陆后，是如下状态：                                                          ![image-20200804153447593](F:\MyNotebook\doc\picture\i18.png)
- 双击`StorageCloud`，即可进入内网研发桌面：![image-20200804153806487](F:\MyNotebook\doc\picture\i19.png)
- 在内网云桌面中，打开`运行`窗口，输入`\\10.2.29.6`，如下图所示，在upload目录中，新建自己的文件夹，并创建桌面快捷方式：![image-20200804155505886](F:\MyNotebook\doc\picture\i20.png)



### 2.2 外网向内网传输文件

- 软件：`xftp`

- 使用`Xftp 6`软件向内网云桌面传送文件，配置内网`ip, user, password`，密码与用户名相同，如下：![image-20200804144543670](F:\MyNotebook\doc\picture\i13.png)
- 找到自己的目录，直接将要传输的文件拖拽过去即可，如下图所示![image-20200804144905211](F:\MyNotebook\doc\picture\i14.png)

- 代码经过外网`Review`并修正后，便可以通过以上流程导入内网，原则上，导入仍由代码编写人员自行导入。



### 2.3 内网远程仓库

#### 2.3.1 内网环境配置

- 软件：内网`XShell`

- 配置登陆服务器，主机IP如下：

  ![image-20200804164000621](F:\MyNotebook\doc\picture\i21.png)

- 用户名如下（注意切换为自己的名字）：![image-20200804164147640](F:\MyNotebook\doc\picture\i22.png)

- 点击`确定`后，会让输入密码，我们的密码为统一密码：`Sugon!1234`

- 登陆成功后，切换到`/code`目录下，如果没有自己的目录，联系管理员（王翰）让其帮忙创建![image-20200804164524199](F:\MyNotebook\doc\picture\i23.png)



#### 2.3.2 内网拉取远程仓库

- 切换到自己目录![image-20200804165034108](F:\MyNotebook\doc\picture\i24.png)

- 获取远程仓库路径![image-20200804165407218](F:\MyNotebook\doc\picture\i25.png)

- 下载代码![image-20200804165703931](F:\MyNotebook\doc\picture\i26.png)

- 此时代码所处的分支为`master`分支![image-20200804170023933](F:\MyNotebook\doc\picture\i27.png)

- 因为我们前期有好多人已经创建了自己的分支，也打算将外网的代码先上传到自己的分支上，此时就需要切换到自己的分支，分支切换：`git checkout -b localBranch origin/remoteBranch`，其中`localBranch`为本地跟踪分支，可以自定义，建议与远程分支名保持一致，如：![image-20200804171945594](F:\MyNotebook\doc\picture\i28.png)

  `git branch -vv`可以查看本地跟踪的远程分支

  

#### 2.3.3 代码导入本地分支中并上传

- 我们的外网代码前面已经从外网拷贝到`10.2.29.6\\xuhb`位置处，只要将其拷贝到`10.29.96.30\\share_ps3test\\xuhb`目录下即可，而`10.29.96.30\\share_ps3test\\xuhb`就是我们本地仓库的位置，建议将这两个路径映射成网络驱动器，具体方法可以咨询王翰。![image-20200804173317369](F:\MyNotebook\doc\picture\i29.png)

- 后面就是在`Xshell`终端界面进行代码上传，操作方法：`git add .; git commit -m "***"`, `git push`命令如下：![image-20200804174122379](F:\MyNotebook\doc\picture\i30.png)

  