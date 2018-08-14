#!/usr/bin/python3
#coding=utf-8

'''
    Copyright (C) 2018 Unisoc
    Created on Apr 23, 2018
    Filename: logout.py

    @author: haibin.xu
'''

import logging
import logging.config
from GlobalVar.global_var import glvar
import sys
import os

class Log_cfg(object):
    def __init__(self, loggername, cfgfile):#初始化
        self.logname = loggername
        self.cfgfile = cfgfile
        logging.config.fileConfig(self.cfgfile)

    def get_logger(self):
        return logging.getLogger(self.logname)

console_handler = logging.StreamHandler(sys.stdout)

class Log(object):
    def __init__(self, loggername, logfile, formatter='%(asctime)s %(name)s \
%(module)s %(funcName)s %(lineno)s %(levelname)-8s: %(message)s'):#初始化
        self.logname = loggername
        self.logfile = logfile
        # 指定logger输出格式
        self.formatter = logging.Formatter(formatter)
        # 获取logger实例，如果参数为空则返回root logger
        self.logger = logging.getLogger(self.logname)

    def get_logger(self):
        # 文件日志
        file_handler = logging.FileHandler(self.logfile)
        file_handler.setFormatter(self.formatter)  # 可以通过setFormatter指定输出格式
        # 控制台日志
        global console_handler
        console_handler.formatter = self.formatter  # 也可以直接给formatter赋值
        # 为logger添加的日志处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        # 指定日志的最低输出级别，默认为WARN级别
        self.logger.setLevel(logging.DEBUG)
        return self.logger

def main():
#---------------------- 以下为代码配置logging-------------------------------------#
#     # 获取logger实例，如果参数为空则返回root logger
#     logger = logging.getLogger("AppName")
#     # 指定logger输出格式
#     formatter = logging.Formatter('%(asctime)s %(module)s %(funcName)s %(lineno)s %(levelname)-8s: %(message)s')
#     # 文件日志
#     file_handler = logging.FileHandler("test.log")
#     file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式
#     # 控制台日志
#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.formatter = formatter  # 也可以直接给formatter赋值
#     # 为logger添加的日志处理器
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
#     # 指定日志的最低输出级别，默认为WARN级别
#     logger.setLevel(logging.DEBUG)
#---------------------- 以上为代码配置logging-------------------------------------#

#---------------------- 以下为文件配置logging-------------------------------------#
#     filepath = os.path.join(os.path.dirname(__file__), 'logging.conf')
#     logging.config.fileConfig(filepath)
#     logger = logging.getLogger("common")
#---------------------- 以上为代码配置logging-------------------------------------#
    logger = Log("common", glvar.get_value('logout')).get_logger()

    # 输出不同级别的log
    logger.debug('this is debug info')
    logger.info('this is information')
    logger.warn('this is warning message')
    logger.error('this is error message')
    logger.fatal('this is fatal message, it is same as logger.critical')
    logger.critical('this is critical message')

    try:
        1 / 0
    except:
    # 等同于error级别，但是会额外记录当前抛出的异常堆栈信息
        logger.exception('this is an exception message')

if __name__ == '__main__':
    main()