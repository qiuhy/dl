# -*- coding: utf-8 -*-
"""
Created on 2017-06-08

@author: hy_qiu
"""
import util.mt as mt
import util.loginit
import time
import random
import threading
import requests
from bs4 import BeautifulSoup

logger = util.loginit.get_logger()


def testfunc(*args):
    logger.info('{}{}'.format(testfunc.__name__, args))
    time.sleep(random.random() * 3)


def test_mt():
    args1 = [i for i in range(100)]
    args2 = ['o' * random.randint(1, 10) for i in range(100)]

    if mt.run2pool(testfunc, 'test', None, args1, args2):
        logger.info('Done')
    else:
        logger.warning('Break!')


def test_requests():
    url = 'http://epaper.21jingji.com/html/2017-06/02/node_1.htm'
    resp = requests.get(url)
    resp.raise_for_status()
    soup= BeautifulSoup(resp.content, "html5lib")
    print(soup)

if __name__ == '__main__':
    test_mt()
