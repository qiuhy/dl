# -*- coding: utf-8 -*-
"""
Created on 17-9-12

@author: hy_qiu
"""

import urllib.parse
import json

def encodeURI(url):
    urllib.parse.quote(url, safe='~@#$&()*!+=:;,.?/\'')


def decodeURI(url):
    urllib.parse.unquote(url)


def encodeURIComponent(obj):
    # 模拟Javascript的encodeURIComponent
    return urllib.parse.quote(json.dumps(obj, separators=(',', ':')), safe='~()*!.\'')


def decodeURIComponent(str):
    # 模拟Javascript的decodeURIComponent
    return urllib.parse.unquote(str)
