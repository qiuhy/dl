# -*- coding: utf-8 -*-
"""
Created on 17-7-25

@author: hy_qiu
"""
import requests
from bs4 import BeautifulSoup
from util.wraps import retry
import csv
import util.loginit
import os
import json
import multiprocessing.dummy as mt
import util.mt
import re

logger = util.loginit.get_logger()
sess = requests.session()
sess.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'

BREAK_EVENT = mt.Event()
_LOCK = mt.Lock()
_DONE = mt.Value('i', 0)
_FAIL = mt.Value('i', 0)
_EMPTY = mt.Value('i', 0)


@retry()
def get_soup(url, param=None):
    resp = sess.post(url, data=param, timeout=120)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html5lib')
    return soup


def get_list():
    url = 'http://www.tjlandmarket.com/Pages/gongsgg.aspx?id=crjggg'
    param = {}
    hasnext = True
    while hasnext:
        soup = get_soup(url, param)
        form = soup.find('form', id='aspnetForm')
        for item in form.find_all('input', type='hidden'):
            if item.has_attr('name') and item.has_attr('value'):
                param[item['name']] = item['value']

        div = form.find('div', id='WebPartWPQ2')
        wid = div['webpartid'].replace('-', '_')
        tid = 'ctl00_ctl12_g_{}_GridViewWebPart'.format(wid)
        tb = div.find('table', id=tid)
        for a in tb.find_all('a'):
            fid = a['href'].split('=')[-1]
            fname = a.get_text(strip=True)
            yield fid, fname

        for a in div.find_all('a'):
            if a.get_text(strip=True) == '下一页':
                if a.has_attr('disabled'):
                    hasnext = False
                else:
                    param['__EVENTTARGET'] = 'ctl00$ctl12$g_{}$ctl02'.format(wid)
                    param['__EVENTARGUMENT'] = ''


def get_listfile(fn):
    if os.path.exists(fn):
        return fn
    with open(fn, mode='w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        no = 0
        for fid, fname in get_list():
            no += 1
            writer.writerow([no, fid, fname])
            if no % 100 == 0:
                logger.info('get list {}'.format(no))
    logger.info('get list total {} '.format(no))
    return fn


def get_baseinfo(fid):
    url = 'http://www.tjlandmarket.com/Lists/List15/DispForm.aspx?ID={}'.format(fid)
    soup = get_soup(url)
    div = soup.find('div', id='WebPartWPQ2')
    tb = div.find('table', align='center')
    if tb is None:
        tb = div.find('table')
    info = {}
    for tr in tb.find_all('tr'):
        tds = list(tr.find_all('td'))
        key = tds[0].get_text(strip=True)
        if key.endswith('：'):
            key = key[:-1]
        else:
            continue
        val = tds[1].get_text(strip=True)
        info[key] = val
    return info


def save2json(no, fid, fname, fn):
    try:
        info = {'id': fid, 'base': get_baseinfo(fid)}
        with open(fn, mode='w', encoding='utf-8') as fp:
            json.dump(info, fp, ensure_ascii=False)
        with _LOCK:
            _DONE.value += 1
        logger.info('{} {} {}'.format(no, fid, fname))
    except Exception as e:
        with _LOCK:
            _FAIL.value += 1
        logger.error('{} {} {} FAIL {}'.format(no, fid, fname, e))


def main(path):
    if not os.path.exists(path):
        os.mkdir(path)

    util.mt.allow_break(BREAK_EVENT)
    pool = mt.Pool(10)
    exists = 0
    total = 0
    results = []
    # pat = re.compile('^(.+)[\uff08\(](.+)[\uff09\)}].*?(\d{4})-.*$')
    pat = re.compile('^.+?(\d{4})-.*$')
    for row in csv.reader(open(get_listfile(path + '/list.csv'), encoding='utf-8')):
        total += 1
        no, fid, fname = row[0], row[1], row[2]
        if fname == '':
            continue
        try:
            year = pat.match(fname).groups()[0]
        except:
            year = '无年度'
        fpath = os.path.join(path, year)
        if not os.path.exists(fpath):
            os.mkdir(fpath)
        fname = re.sub('[:\\\/\.]', '', fname)
        fn = os.path.join(fpath, fname + '.json')
        if os.path.exists(fn):
            exists += 1
        else:
            results.append(pool.apply_async(save2json, (no, fid, fname, fn)))
            # pass

    logger.info('total:{} exists:{} need to download:{}'.format(total, exists, len(results)))
    if len(results) == 0:
        return

    while True:
        if BREAK_EVENT.is_set():
            pool.terminate()
            pool.join()
            break
        else:
            running = False
            for a in results:
                if not a.ready():
                    running = True
                    break
            if not running:
                break
        BREAK_EVENT.wait(1)
    with _LOCK:
        logger.info('done:{} fail:{} '.format(_DONE.value, _FAIL.value))


if __name__ == '__main__':
    main('e:/tjtd')
    # print(get_baseinfo(2448))
