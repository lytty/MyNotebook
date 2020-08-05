# sugon account

1.  外网xshell登陆，可操作storcli命令：

   ```
   shell 10.2.43.244 用户名：root 密码：parastor;123
   ```

2.  邮箱账号：xuhb@sugon.com, 密码：通用

3.  OA官网账号：xuhb, 密码：通用

4.  公司WIFI账号：Sugon_Staff, 密码：shuguang；连接成功后，进入web认证页面，账号：xuhb， 密码：通用

5. 光圈账号：邮箱，密码：通用

6. Vmware登陆账号：xuhb，密码：通用

7. 员工自助平台：https://ehr.sugon.com/sap/bc/webdynpro/sap/zhr_ss_wd_001?pernr=00869145#，账号：邮箱，密码：通用，使用IE浏览器

8. 云桌面：bitbucket:10.20.51.163:8060，账号：xuhb，密码：Sugon!1234

9. VMware登陆：服务器 10.2.29.5, 用户名：xuhb， 密码：通用

10. WPS云文档：xuhb, 密码：通用，内网云桌面WPS账号：xuhb，密码：Sugon!1234

11.   Xftp5， 本地向内网云桌面传送文件，内网服务器：10.2.29.6， 用户名：upload， 密码：upload

12.   云桌面：Xshell： ssh://xuhb@sugonyf.com@10.20.96.30:22, 密码：Sugon!1234

13.   本地服务器登陆，打开Xshell，ssh 10.2.19.21, 登录名：root，密码：parastor;123

## 分支代码下载流程

1.  云桌面登陆服务器， Xshell： ssh://xuhb@sugonyf.com@10.20.96.30:22, 密码：Sugon!1234，![image-20200716142831380](F:\MyNotebook\doc\picture\云桌面-1.png)
2.  在服务器中，/code目录下创建自己的目录，自己没有权限的话，请鲁亚飞、杜盼盼帮忙创建
3.  在自己目录中下载分支代码，git仓库地址，在我们的Bitbucket中获取，如下图![image-20200716143549844](F:\MyNotebook\doc\picture\云桌面-2.png)
4.  代码下载完成后，默认分支是master分支，需切换到我们自己的分支，分支名如下，分支切换命令`git checkout ps3-1.0.0-Test-ScriptLib-xuhb`![image-20200716143833179](F:\MyNotebook\doc\picture\云桌面-3.png)
5.  切换分支以后，我们的公共类存放路径：ps3/test/esat/scripts/libs，将来脚本测试存放路径：ps3/test/esat/scripts/module_scripts![image-20200716144235797](F:\MyNotebook\doc\picture\云桌面-4.png)

# 外网代码管理服务器

## 1. 本地外网环境配置

1.  本地（Windows系统）安装Git，安装完成后，打开Git Bash![image-20200717164842408](F:\MyNotebook\doc\picture\git-1.png)进入Git Bash后，切换到自己将要下载代码的路径，如下：![image-20200717165129453](F:\MyNotebook\doc\picture\git-2.png)

2. 如果习惯使用Linux终端，可在本地Microsoft Store下载模拟Ubuntu终端，如下：![image-20200717165509137](F:\MyNotebook\doc\picture\remote1.png)![image-20200717165818549](F:\MyNotebook\doc\picture\remote2.png)

   安装最新版本即可，安装完毕后，打开Ubuntu 20.04 LTS，如下图，使用Linux终端时，不需要安装Windows版本的git，如果当前终端没有git，直接使用Linux 命令`sudo apt install git`安装即可：![image-20200717170258356](F:\MyNotebook\doc\picture\remote3.png)
   
3.   注意：Git版本管理系统为程序员必备知识，务必熟学熟用，推荐学习网址：https://www.liaoxuefeng.com/wiki/896043488029600/896067008724000

## 2. 代码远程仓库

1. 我们的代码机存放在许海宾工位处，代码机24小时不断电。
2. 代码仓库路径：`xuhb@10.2.19.21:/home/xuhb/code/test.git`，下载命令：`git clone xuhb@10.2.19.21:/home/xuhb/code/test.git`，会提示需要输入密码：123@abAB，后续提交操作需要输入密码的话，都是此密码。
3. 代码下载到本地，即可对自己负责的代码进行更新、提交，常用操作指令如下：
   - 同步远程仓库命令：`git pull`
   
   - 代码提交相关命令：`git add .`, `git commit -m "***"`, `git push origin master`
   
   - 撤销`git add`操作：
   
     ```
     git reset HEAD 如果后面什么都不跟的话 就是上一次add 里面的全部撤销了
     git reset HEAD XXX/XXX/XXX.java 就是对某个文件进行撤销了
     ```
   
   - 撤销`git commit`操作：
   
     ```
     git reset --soft HEAD^
     ```
   
   - 小组成员评语
   
     ```
     李浩然：项目基础知识掌握扎实，脚本编写能力较强，积极听取他人建议，python语言基础能力待提高，程序员常备技能待提高。
     李静：学习能力强，工作细心，对特定项目模块知识掌握较强，脚本编写能力待进一步提高，python语言能力待提高，程序员常备技能待提高。
     王琦：项目整体掌握扎实，项目接触面广，脚本编写能力强，针对问题常常有自己的独特见解，python语言编码规范待提高，程序员常备技能待提高。
     王水澄：工作认真，对不懂的地方善于钻研，积极向他人学习，脚本编写能力较强，python语言编码能力待提高，程序员常备技能待提高。
     魏文波：工作扎实，解决问题能力强，乐于学习，脚本编写能力较强，python语言编码能力待提高，程序员常备技能待提高。
     
     ```
   
     