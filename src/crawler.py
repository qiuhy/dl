# -*- coding: utf-8 -*-
"""
Created on 2017-05-05

@author: hy_qiu
"""
import json
import logging
import os
import urllib.parse
import urllib.request

from src.util.wraps import retry

TIMEOUT = 15


def file_copy2path(fn, pn):
    if not os.path.exists(fn) or not os.path.isfile(fn):
        return ''

    if not os.path.exists(pn):
        os.makedirs(pn)

    nfn = os.path.join(pn, os.path.split(fn)[1])
    open(nfn, "wb").write(open(fn, "rb").read())
    return nfn


def file_move2path(fn, pn):
    nfn = file_copy2path(fn, pn)
    if nfn != '':
        os.remove(fn)
    return nfn


def get_response(url, values=None):
    host = url.split('/')[2].strip()
    headers = {'Host': host,
               'User-Agent': 'Mozilla/5.0'}
    if values:
        postdata = urllib.parse.urlencode(values).encode('utf-8')
    else:
        postdata = None

    request = urllib.request.Request(url, postdata, headers)
    response = urllib.request.urlopen(request, timeout=TIMEOUT)
    return response


def get_read(url, values=None, charset=None):
    r = get_response(url, values)
    if charset is None:
        ctv = r.getheader('Content-Type')
        if ctv:
            # 'Content-Type	application/json; charset=utf-8'
            for t in ctv.split(';'):
                if t.strip().lower().startswith('charset='):
                    charset = t.strip()[8:]
                    break
    if charset:
        return r.read().decode(charset)
    else:
        return r.read()


def get_json(url, values=None, charset=None):
    return json.loads(get_read(url, values, charset))


class Crawler:
    def __init__(self, host='', code='', name='', logger=None):
        self.host = host
        self.code = code
        self.name = name

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(code)
            self.logger.setLevel(logging.DEBUG)
            fh = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(name)s-%(levelname)-8s %(message)s')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        return

    def get_hosturl(self, url):
        if self.host is None or self.host == '':
            return url
        else:
            return 'http://{}/{}'.format(self.host, url)

    @retry()
    def get_response(self, url, values=None):
        return get_response(self.get_hosturl(url), values)

    @retry()
    def get_json(self, url, values=None, charset=None):
        return get_json(self.get_hosturl(url), values, charset)

    @retry()
    def get_read(self, url, values=None, charset=None):
        return get_read(self.get_hosturl(url), values, charset)
