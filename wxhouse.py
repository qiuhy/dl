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
    url = 'http://www.wxhouse.com:9097/wwzs/getzxlpxx.action'
    pageno = 1
    totalpage = 0
    while True:
        param = {'page.currentPageNo': pageno, 'page.pageSize': 15}
        soup = get_soup(url, param)
        form = soup.find('form', id='searchForm')
        if totalpage == 0:
            totalpage = int(form.find('input', id='totalPageCount')['value'])

        tb = list(form.find_all('table'))[1]
        for a in tb.find_all('a'):
            fid = a['href'].split('=')[-1]
            fname = a.get_text(strip=True)
            yield fid, fname

        pageno += 1
        if pageno >= totalpage:
            break


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
    url = 'http://www.wxhouse.com:9097/wwzs/queryLpxxInfo.action?tplLpxx.id={}'.format(fid)
    soup = get_soup(url)
    tb = list(soup.find_all('table', {'class': 'searchdiv'}))[1]
    info = {}
    for tr in tb.find_all('tr'):
        tds = list(tr.find_all('td'))
        key = tds[0].get_text(strip=True)[:-1]
        val = tds[1].get_text(strip=True)
        info[key] = val
    return info


def get_saleinfo(fid):
    url = 'http://www.wxhouse.com:9097/wwzs/queryXsxzInfo.action?tplLpxx.id={}'.format(fid)
    soup = get_soup(url)
    tb = list(soup.find_all('table', {'class': 'searchdiv'}))[1]

    trs = list(tb.find_all('tr'))
    keys = []
    for td in trs[0].find_all('td'):
        keys.append(td.get_text(strip=True))

    info = []
    for tr in trs[1:]:
        i = 0
        sale = {}
        for td in tr.find_all('td'):
            sale[keys[i]] = td.get_text(strip=True)
            i += 1
        info.append(sale)
    return info


def save2json(no, fid, fname, fn):
    try:
        info = {'id': fid, 'name': fname, 'base': get_baseinfo(fid), 'sale': get_saleinfo(fid)}
        with open(fn, mode='w', encoding='utf-8') as fp:
            json.dump(info, fp, ensure_ascii=False)
        with _LOCK:
            _DONE.value += 1
            if len(info['sale']) == 0:
                _EMPTY.value += 1
                logger.warning('{} {} {} 无销售信息'.format(no, fid, fname))
            else:
                logger.info('{} {} {} {}'.format(no, fid, fname, len(info['sale'])))
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
    for row in csv.reader(open(get_listfile(path + '/list.csv'), encoding='utf-8')):
        total += 1
        no, fid, fname = row[0], row[1], row[2]
        # fpath = os.path.join(path, fid)
        fpath = path
        if not os.path.exists(fpath):
            os.mkdir(fpath)
        fn = os.path.join(fpath, fid + '.json')
        if os.path.exists(fn):
            exists += 1
        else:
            results.append(pool.apply_async(save2json, (no, fid, fname, fn)))

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
        logger.info('done:{} {} fail:{} '.format(_DONE.value, _EMPTY.value, _FAIL.value))


if __name__ == '__main__':
    main('e:/wxhouse')
    # print(get_saleinfo(111147))
