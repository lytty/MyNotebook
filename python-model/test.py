#! /usr/bin/env python
# -*- coding:utf-8 -*-

'''
    Copyright (C) 2018 Unisoc
    Created on Aug 02, 2018
    Filename: test.py
'''

__author__ = 'haibin.xu'

import os
import sys
import time
from ComFuncAndClas import Log

logger = Log('common').getLogger()
# current directory path
cur_dir = os.path.dirname(os.path.realpath(__file__))
# module path
lib_dir = os.path.join(cur_dir, 'lib')
tqdm_dir = os.path.join(lib_dir, 'tqdm-4.24')
termcolor_dir = os.path.join(lib_dir, 'termcolor-1.1.0')
sys.path.append(lib_dir)
sys.path.append(tqdm_dir)
sys.path.append(termcolor_dir)

# tqdm module test
'''
from tqdm import tqdm

for i in tqdm(range(100)):
    time.sleep(0.1)
    pass
logger.info('END')
'''

# termcolor module test
from termcolor import colored, cprint

text = colored('Hello, World!', 'red')
print(text)
cprint('Hello, World!', 'green', 'on_red')

print_red_on_cyan = lambda x: cprint(x, 'red', 'on_cyan')
print_red_on_cyan('Hello, World!')
print_red_on_cyan('Hello, Universe!')

cprint("Attention!", 'red', attrs=['bold'])
logger.info("haibin")