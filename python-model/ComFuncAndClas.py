#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''
    Copyright (C) 2018 Unisoc
    Created on Apr 23, 2018
    Filename: ComFuncAndClas.py
'''

__author__ = 'haibin.xu'

import os
import sys
import logging
from hashlib import md5

cur_dir = os.path.dirname(os.path.realpath(__file__))
console_handler = logging.StreamHandler(sys.stdout)


def md5_file(name):
    md5value = md5()
    with open(name, 'rb') as fp:
        md5value.update(fp.read())

    return md5value.hexdigest()

class Log(object):
    '''
    log recorder
    '''
    def __init__(self, loggername, formatter='%(asctime)s \
%(module)-15s %(funcName)-10s %(lineno)-4s %(levelname)-8s: %(message)s'):#初始化
        self.logname = loggername
        # 指定logger输出格式
        self.formatter = logging.Formatter(formatter)
        # 获取logger实例，如果参数为空则返回root logger
        self.logger = logging.getLogger(self.logname)

    def getLogger(self):
        # 控制台日志
        global console_handler
        console_handler.formatter = self.formatter  # 也可以直接给formatter赋值
        self.logger.addHandler(console_handler)
        # 指定日志的最低输出级别，默认为WARN级别
        self.logger.setLevel(logging.DEBUG)
        return self.logger

logger = Log('common').getLogger()

def remove_all_stale_files(base_dir, file_fmt=[]):
    '''
    Scan directories for specific file format and delete them.
    '''
    if file_fmt == []:
        logger.info('No need to scan and delete specific file.')
        sys.exit()

    for dirname, _, filenames in os.walk(base_dir):
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext in file_fmt:
                stale_path = os.path.join(dirname, filename)
                os.remove(stale_path)

        try:
            os.removedirs(dirname)
        except OSError:
            pass

def cmdExecute(cmd):
    '''
    execute the shell command
    '''
    if (os.system(cmd) != 0):
        logger.error('Command "{}" execute error, exit'.format(cmd))
        sys.exit()

    return True

def main():
    # 输出不同级别的log
    pass


if __name__ == '__main__':
    main()
