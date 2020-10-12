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

12.   云桌面：Xshell： ssh://xuhb@sugonyf.com@10.20.96.30:22, 密码：Sugon!1234,  root    Perseus;123

13.  云桌面：share_ps3test(\\10.20.96.30)创建网络驱动器，密码 111111

14. 本地服务器登陆，打开Xshell，ssh 10.2.16.6, 登录名：root，密码：parastor;123

## 分支代码下载流程

1.  云桌面登陆服务器， Xshell： ssh://xuhb@sugonyf.com@10.20.96.30:22, 密码：Sugon!1234，![image-20200716142831380](F:\MyNotebook\doc\picture\云桌面-1.png)
2.  在服务器中，/code目录下创建自己的目录，自己没有权限的话，请鲁亚飞、杜盼盼帮忙创建
3.  在自己目录中下载分支代码，git仓库地址，在我们的Bitbucket中获取，如下图![image-20200716143549844](F:\MyNotebook\doc\picture\云桌面-2.png)
4.  代码下载完成后，默认分支是master分支，需切换到我们自己的分支，分支名如下，分支切换命令`git checkout ps3-1.0.0-Test-ScriptLib-xuhb`![image-20200716143833179](F:\MyNotebook\doc\picture\云桌面-3.png)
5.  切换分支以后，我们的公共类存放路径：ps3/test/esat/scripts/libs，将来脚本测试存放路径：ps3/test/esat/scripts/module_scripts![image-20200716144235797](F:\MyNotebook\doc\picture\云桌面-4.png)

