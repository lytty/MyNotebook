# git常用命令

1.  git stash

   - 在使用git的时候往往会保存一些东西，在保存的时候使用的就是git stash
   - 当利用git stash pop弹出来会有些耗费时间，这时可以使用git stash show来查看stash里面保存的内容
   - git stash时出错：needs merge ***
     - 解决：git reset HEAD， 然后再 git stash 即可

2.  git add

   - git add . （空格+ 点） 表示当前目录所有文件，不小心就会提交其他文件

   - git add 如果添加了错误的文件的话

   - 撤销操作

     > git status 先看一下add 中的文件
     > git reset HEAD 如果后面什么都不跟的话 就是上一次add 里面的全部撤销了
     > git reset HEAD XXX/XXX/XXX.java 就是对某个文件进行撤销了

3.  跟踪分支

   - 设定：远程主机名origin，远程分支名remoteBranch，本地分支名localBranch

   - 讨论两种情况：

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
    - 查看本地跟踪分支对应的远程分支：git branch -vv（两个v），就能够看到本地分支跟踪的远程分支

   - 其他相关命令

     > 解除跟踪关系：git branch --unset-upstream localBranch
     >
     > 删除本地分支：git branch -d localBranch
     >
     > 强制删除本地分支：git branch -D localBranch
     >
     > 删除远程分支：git push origin --delete remoteBranch 或者 git push origin :remoteBranch

   - 实例 tiny-formatter：

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

4.  git commit

   - **git commit** 主要是将暂存区里的改动给提交到本地的版本库。每次使用git commit 命令我们都会在本地版本库生成一个40位的哈希值，这个哈希值也叫commit-id，commit-id在版本回退的时候是非常有用的，它相当于一个快照,可以在未来的任何时候通过与git reset的组合命令回到这里.

   - **git commit -m “message”** 这种是比较常见的用法，-m 参数表示可以直接输入后面的“message”，如果不加 -m参数，那么是不能直接输入message的，而是会调用一个编辑器一般是vim来让你输入这个message，message即是我们用来简要说明这次提交的语句。还有另外一种方法，当我们想要提交的message很长或者我们想描述的更清楚更简洁明了一点，我们可以使用这样的格式，如下：

     ```
     git commit -m ‘

     message1

     message2

     message3

     ’

     ```

   - **git commit -a -m “massage”** 其他功能如-m参数，加的-a参数可以将所有已跟踪文件中的执行修改或删除操作的文件都提交到本地仓库，即使它们没有经过git add添加到暂存区，注意，新加的文件（即没有被git系统管理的文件）是不能被提交到本地仓库的。建议一般不要使用-a参数，正常的提交还是使用git add先将要改动的文件添加到暂存区，再用git commit 提交到本地版本库。

   - **git commit --amend** 如果我们不小心提交了一版我们不满意的代码，并且给它推送到服务器了，在代码没被merge之前我们希望再修改一版满意的，而如果我们不想在服务器上abondon，那么我们怎么做呢？

     **git commit --amend** 也叫追加提交，它可以在不增加一个新的commit-id的情况下将新修改的代码追加到前一次的commit-id中。

   - 撤销git commit

     使用**git reset --soft HEAD^，注意，仅仅是撤回commit操作，您写的代码仍然保留

5. git show commit-id, 查看某个提交的修改内容

6. git log --author=haibin.xu, 查看某个owner的所有提交

7.

8.

9.

10.

11.

12.

13.
