# -*- coding: utf-8 -*-
"""
Created on 17-7-28

@author: hy_qiu
"""
import os


def check_filepath(fn):
    path = os.path.split(fn)[0]
    if not os.path.exists(path):
        os.mkdir(path)
