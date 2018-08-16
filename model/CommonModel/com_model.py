#!/usr/bin/python3
#coding=utf-8

'''
    Copyright (C) 2018 Unisoc
    Created on Apr 23, 2018
    Filename: com_model.py
    
    @author: haibin.xu
'''
from LogOutPut.logout import Log
from GlobalVar.global_var import glvar
from LogOutPut.logout import Log

logger = Log("common", glvar.get_value('com_model')).get_logger()

def main():
    logger.info("Hello World !")

if __name__ == '__main__':
    main()