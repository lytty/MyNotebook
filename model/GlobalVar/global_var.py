#!/usr/bin/python3
#coding=utf-8

'''
    Copyright (C) 2018 Unisoc
    Created on Apr 23, 2018
    Filename: global_var.py

    @author: haibin.xu
'''
import os

class MyGlobalVar(object):
    def __init__(self):#初始化
        self._global_dict = {}
        model_list = ['cmd_line_arg', 'com_model', 'global_var', 'logout', 'model', 'all']
        dir_path = os.path.join(os.path.dirname(__file__), '../LogDir')
        for li in model_list:
            self.set_value(li, os.path.join(dir_path, li+'.log'))

    def set_value(self, key, value):
        """ 定义一个全局变量 """
        self._global_dict[key] = value

    def get_value(self, key, defValue=None):
        """ 获得一个全局变量,不存在则返回默认值 """
        try:
            return self._global_dict[key]
        except KeyError:
            return defValue

global glvar #全局对象
glvar = MyGlobalVar()

def main():
    pass

if __name__ == '__main__':
    main()