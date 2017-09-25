# -*- coding: utf-8 -*-
"""
Created on 17-7-19

@author: hy_qiu
"""
import csv
import json
import multiprocessing.dummy as mt
import os

import requests
from bs4 import BeautifulSoup
from util.wraps import retry

import src.util.mt

logger = util.loginit.get_logger()

BREAK_EVENT = mt.Event()
_LOCK = mt.Lock()
_DONE = mt.Value('i', 0)
_FAIL = mt.Value('i', 0)
_EMPTY = mt.Value('i', 0)


@retry()
def get_soup(url, param=None):
    resp = requests.post(url, data=param, timeout=120)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html5lib')


def get_list():
    url = 'http://www.tjfdc.com.cn/Pages/fcdt/fcdtlist.aspx'
    # total = 0
    param = {}
    while True:
        soup = get_soup(url, param)
        # if total == 0:
        #     total = int(soup.find('span', id='SplitPageModule1_lblRecordCount').string)
        #     # pagecount = int(soup.find('span', id='SplitPageModule1_lblPageCount').string)
        #     logger.info('get list {}'.format(total))
        ul = soup.find('ul', {'class': 'piclist'})
        for li in ul.find_all('li'):
            if BREAK_EVENT.is_set():
                return
            a = li.find('a', {'class': 'picl_tit'})
            fid = a['href'].split('=')[-1]
            fname = a.get_text(strip=True)
            tr = list(li.find_all('tr'))[1]
            farea = list(tr.find_all('td'))[1].get_text(strip=True)
            yield fid, fname, farea
        form = soup.find('form')
        a = form.find('a', id='SplitPageModule1_lbnNextPage')
        if a.has_attr('disabled') and a['disabled'] == 'disabled':
            break
        param = {}
        for item in form.find_all('input', type='hidden'):
            if item.has_attr('value'):
                param[item['name']] = item['value']
            else:
                param[item['name']] = ''
        param['__EVENTTARGET'] = 'SplitPageModule1$lbnNextPage'
        param['__EVENTARGUMENT'] = ''


def get_listfile(fn):
    if os.path.exists(fn):
        return fn
    with open(fn, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        no = 0
        for fid, fname, farea in get_list():
            no += 1
            writer.writerow([no, farea, fname])
            if no % 100 == 0:
                logger.info('get list {}'.format(no))
    logger.info('get list total {} '.format(no))
    return fn


def get_id(fname):
    url = 'http://www.tjfdc.com.cn/Pages/fcdt/fcdtlist.aspx?&XMMC={}'.format(fname)
    soup = get_soup(url)
    ul = soup.find('ul', {'class': 'piclist'})
    for li in ul.find_all('li'):
        a = li.find('a', {'class': 'picl_tit'})
        fid = a['href'].split('=')[-1]
        # tr = list(li.find_all('tr'))[1]
        # farea = list(tr.find_all('td'))[1].get_text(strip=True)
        if fname == a.get_text(strip=True):
            return fid


def get_base(fid):
    url = 'http://www.tjfdc.com.cn/Pages/fcdt/fcdt.aspx?fid={}'.format(fid)
    soup = get_soup(url)
    info = {}
    tb = soup.find('div', id='divBasicInfo').table
    for tr in tb.find_all('tr'):
        key = ''
        for span in tr.find_all('span'):
            val = span.get_text(strip=True)
            if span.has_attr('class') and 'gray9' in span['class']:
                key = val[:-1]
                # if key == '楼盘名称':
                #     info[key] = list(tr.find_all('td'))[1].get_text(strip=True)
            elif span.has_attr('id'):
                info[key] = val
    return info


def get_build(fid):
    url = 'http://www.tjfdc.com.cn/Pages/fcdt/LouDongList.aspx?selmnu=FCSJ_XMXX_LPB&fid={}'.format(fid)
    spid = 'LouDongList1_rptLouDongList_ctl{:02d}_lbl{}'
    param = {}
    build_list = []
    while True:

        soup = get_soup(url, param)
        div = soup.find('div', id='divLouDongList')
        form = soup.find('form', id='form1')
        param = {}
        for item in form.find_all('input', type='hidden'):
            if item.has_attr('value'):
                param[item['name']] = item['value']

        rowid = 0
        while True:
            if BREAK_EVENT.is_set():
                raise Exception('BREAK EVENT is set')
            rowid += 1
            sp = div.find('span', id=spid.format(rowid, 'PROJECTNAME'))
            if sp is None:
                break
            build_item = {}
            build_item['楼栋名称'] = sp.get_text(strip=True)
            build_item['楼号'] = div.find('a', id=spid.format(rowid, 'BUILDNO')).get_text(strip=True)
            build_item['销售许可证号'] = div.find('span', id=spid.format(rowid, 'LICNOMAIN')).get_text(strip=True)
            build_item['开盘日期'] = div.find('span', id=spid.format(rowid, 'STARTDATE')).get_text(strip=True)
            build_item['住宅销售均价'] = div.find('span', id=spid.format(rowid, 'MMPRICE_ZZ')).get_text(strip=True)
            build_item['非住宅销售均价'] = div.find('span', id=spid.format(rowid, 'MMPRICE_FZZ')).get_text(strip=True)
            build_item['可售套数'] = div.find('span', id=spid.format(rowid, 'COUNT_WS')).get_text(strip=True)
            param['__EVENTTARGET'] = spid.format(rowid, 'BUILDNO').replace('_', '$')
            param['__EVENTARGUMENT'] = ''
            try:
                fsoup = get_soup(url, param)
                build_item['总套数'] = fsoup.find('span', id='LouDongInfo1_lblHouseCount').get_text(strip=True)
                build_item['房屋坐落'] = fsoup.find('span', id='LouDongInfo1_lblHOUSEADDR').get_text(strip=True)
                build_item['公司名称'] = fsoup.find('span', id='LouDongInfo1_lblDEP_NAME').get_text(strip=True)
            except Exception as e:
                logger.warning('{} {} FAIL {}'.format(build_item['楼栋名称'], build_item['楼号'], e))

            build_list.append(build_item)

        a = form.find('a', id='LouDongList1_SplitPageIconModule1_lbnNextPage')
        if a.has_attr('disabled') and a['disabled'] == 'disabled':
            break
        param['__EVENTTARGET'] = 'LouDongList1$SplitPageIconModule1$lbnNextPage'
        param['__EVENTARGUMENT'] = ''

    return build_list


def save2json(no, fname, fn):
    try:
        fid = get_id(fname)
        if fid is None:
            raise Exception('名称无效！')
        info = {'name': fname, 'base': get_base(fid), 'build': get_build(fid)}
        with open(fn, mode='w', encoding='utf-8') as fp:
            json.dump(info, fp, ensure_ascii=False)
        with _LOCK:
            _DONE.value += 1
            if len(info['build']) == 0:
                _EMPTY.value += 1
                logger.warning('{} {} 无楼栋信息'.format(no, fname))
            else:
                logger.info('{} {} {}'.format(no, fname, len(info['build'])))
    except Exception as e:
        with _LOCK:
            _FAIL.value += 1
        logger.error('{} {} FAIL {}'.format(no, fname, e))


def main(path, names=None):
    if not os.path.exists(path):
        os.mkdir(path)

    src.util.mt.allow_break(BREAK_EVENT)
    pool = mt.Pool(10)
    exists = 0
    total = 0
    results = []
    for row in csv.reader(open(get_listfile(path + '/list.csv'))):
        total += 1
        no, farea, fname = row[0], row[1], row[2]
        if names and fname not in names:
            continue
        fpath = os.path.join(path, farea)
        if not os.path.exists(fpath):
            os.mkdir(fpath)
        fn = os.path.join(fpath, fname + '.json')
        if os.path.exists(fn):
            exists += 1
        else:
            results.append(pool.apply_async(save2json, (no, fname, fn)))

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
        logger.info('done:{} {}  fail:{}'.format(_DONE.value, _EMPTY.value, _FAIL.value))


if __name__ == '__main__':
    main('e:/tjfdc')
