#!/usr/bin/python3
#coding=utf-8

'''
    Copyright (C) 2018 Unisoc
    Created on Apr 23, 2018
    Filename: cmd_line_args.py
    
    @author: haibin.xu
'''
import os
import sys
import getopt
from LogOutPut.logout import Log
from GlobalVar.global_var import glvar

logger = Log("cmd_line", glvar.get_value('cmd_line_arg')).get_logger()

argv = [['cmd_line_arg.py'],\
        ['cmd_line_arg.py', '-h'], ['cmd_line_arg.py', '--help'],\
        ['cmd_line_arg.py', '-v'], ['cmd_line_arg.py', '--version'],\
        ['cmd_line_arg.py', '-m', 'model'], ['cmd_line_arg.py', '--version', 'model'],\
        ['cmd_line_arg.py', '-a', 'args'], ['cmd_line_arg.py', '--args', 'args'],\
        ['cmd_line_arg.py', '-o', 'out'], ['cmd_line_arg.py', '--output', 'output']]

def usage():
    print("""
Usage:sys.args[0] [option]
-h or --help：显示帮助信息
-m or --module：模块名称   例如：ansible all -m shell -a 'date'
-a or --args：模块对于的参数  例如：ansible all -m shell -a 'date'
-v or --version：显示版本
-o or --output: 显示输出
        """)

def test(arg):
    sys.argv = arg

def main():
    if len(sys.argv) == 1:
        test(argv[6])

    if len(sys.argv) == 1:
        usage()
        sys.exit()

    try:
        logger.info('sys.argv = %s' %(sys.argv))
        opts, args = getopt.getopt(sys.argv[1:], "ho:m:a:v", ["help", "output=", "module=", "args=", "version="])   # sys.argv[1:] 过滤掉第一个参数(它是脚本名称，不是参数的一部分)
        logger.info('opts = %s, args = %s' %(opts, args))
    except getopt.GetoptError:
        logger.error("argv error,please input")

#  使用短格式分析串“ho:m:a:”
#  当一个选项只表示开关状态时，即后面不带任何参数时，在分析串中写入选项字符，例如：-h表示获取帮助信息，显示完成即可，不需任何参数
#  当一个选项后面需要带附加参数时，在分析串中写入选项字符同时后面加一个“：”号，例如：-m表示指定模块名称，后面需加模块名称

#  使用长格式分析串列表：["help", "output="]。
#  长格式串也可以有开关状态，即后面不跟"="号。如果跟一个等号则表示后面还应有一个参数。这个长格式表示"help"是一个开关选项；"output="则表示后面应该带一个参数。
#  print(opts)
#  print(args)
#  调用getopt函数。函数返回两个列表：opts和args。
#  opts为分析出的格式信息，是一个两元组的列表。每个元素为：(选项串,附加参数)。如果没有附加参数则为空串''。
#  args为不属于格式信息的剩余的命令行参数。
#  整个过程使用异常来包含，这样当分析出错时，就可以打印出使用信息来通知用户如何使用这个程序。

# 以下部分即根据分析出的结果做相应的处理，并将处理结果返回给用户
    for cmd, arg in opts:  # 使用一个循环，每次从opts中取出一个两元组，赋给两个变量。cmd保存选项参数，arg为附加参数。接着对取出的选项参数进行处理。
        if cmd in ("-h", "--help"):
            logger.info("help info")
            sys.exit()
        elif cmd in ("-o", "--output"):
            output = arg
            logger.info("output =", output)
        elif cmd in ("-m", "--module"):
            module_name = arg
            logger.info("module_name =", module_name)
        elif cmd in ("-a", "--module_args"):
            module_args = arg
            logger.info("module_args =", module_args)
        elif cmd in ("-v", "--version"):
            logger.info("%s version 1.0" % sys.argv[0])

if __name__ == '__main__':
    main()