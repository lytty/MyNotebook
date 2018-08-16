#!/usr/bin/python3
#coding=utf-8

'''
    Copyright (C) 2018 Unisoc
    Created on Apr 27, 2018
    Filename: model.py

    @author: haibin.xu
'''
import os
import sys
import logging

from GlobalVar.global_var import glvar
from CmdLineArg import cmd_line_arg
from CommonModel import com_model
from LogOutPut import logout
from LogOutPut.logout import Log

logger = Log("common", glvar.get_value('model')).get_logger()

def RemoveAllStalePycFiles(base_dir):
    """Scan directories for old .pyc files without a .py file and delete them."""
    for dirname, _, filenames in os.walk(base_dir):
        if '.git' in dirname:
            continue
        for filename in filenames:
            root, ext = os.path.splitext(filename)
            if ext != '.pyc':
                continue

            pyc_path = os.path.join(dirname, filename)
            py_path = os.path.join(dirname, root + '.py')

            try:
                if not os.path.exists(py_path):
                    os.remove(pyc_path)
            except OSError:
                # Wrap OS calls in try/except in case another process touched this file.
                pass

        try:
            os.removedirs(dirname)
        except OSError:
            # Wrap OS calls in try/except in case another process touched this dir.
            pass

def createlog(model_list, path):
    if len(model_list) == 0:
        logger.error('no models, no create log file !')
        return

    if not os.path.isdir(path):
        logger.error('%s is not a correct direct path !' %path)
        return

    for model_name in model_list:
        logname = model_name + '.log'
        if logname not in os.listdir(path):
            os.mknod(os.path.join(path, logname))

    return

def init():
    RemoveAllStalePycFiles(os.path.dirname(__file__))
    model_list = ['cmd_line_arg', 'com_model', 'global_var', 'logout', 'model', 'all']
    log_path = os.path.join(os.path.dirname(__file__), 'LogDir')
    createlog(model_list, log_path)

def main():
    init()
    cmd_line_arg.main()
    com_model.main()
    logout.main()
    logger.info(glvar._global_dict)

if __name__ == '__main__':
    main()