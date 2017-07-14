# -*- coding: utf-8 -*-
"""
Created on 2017-06-08

@author: hy_qiu
"""
import logging
import sys
import os


class LevelFilter:
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


def get_logger(name=None):
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    pfm = sys._getframe().f_back
    pyn = pfm.f_locals['__file__']
    path, pfn = os.path.split(pyn)
    fn, ext = os.path.splitext(pfn)

    fmt = logging.Formatter('%(asctime)s %(name)s %(levelname).1s %(message)s')
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(fmt)
    sh.addFilter(LevelFilter(logging.WARNING))
    logger.addHandler(sh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = logging.FileHandler(os.path.join(path, fn + '.log'), mode='w', encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
