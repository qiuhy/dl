# -*- coding: utf-8 -*-
"""
Created on 2017-05-24

@author: hy_qiu
"""

import json
import util.loginit
import multiprocessing.dummy as mt
import os
import re
import signal
import time
import zipfile

import requests
import xlrd

from enum import Enum
from util.wraps import retry

# 原始的字典 不知如何转换到实际使用的字典
_SGARR = [
    '6btfl5whqisecpmu98y2zkjrxn-034d1ao7vg',
    '18oszmb9fd7hcunvpy203j-ilktq46raw5exg',
    'gacthupf6x70diveq4b5kw9s-jly3onzm21r8',
    's6h0yldxeakzuf4rb-pg3nm7oci8v219qwtj5',
    'd49moi5kqncs6bjyxlav3tuh-rz207gp8f1we',
    'z5gch7ot2ka-exyj3l1us4bn8i6qp0drvmwf9',
    'px3d658ktlzb4nrvymga01c9-27qjhewusfoi',
    'q-udk7tz48xfvwp2e9om5g1jin63rlbhycas0',
    '7-gx65nuqzwtm0hoypifks9lr12v4e8cbadj3',
    '1t8zofl52yq9pgrxesd4nbuamchj3vi0-w7k6']

# 根据结果猜测的实际使用字典
SOGOU = [
    '6b-f2--5-----ec---98-------034d1a-7--',
    '18-------b9fd7-c--203-------46-a-5e--',
    '-6-0--3----d-ea---f43b-7-c-8-219----5',
    '-70d--ac----f6-e-4b5--9-----3----21-8',
    '--3-1--45-c-7--2-a-e--b-8-6--0d----f9',
    '----3d658----b4------a01c9-27-e---f--',
    '8---d-7--4-f---2e9--5-1---63--b--ca-0',
    'd49---5---c-6b----a-3------207--8f1-e',
    '7---65-------0-----f--9--12-4e8cbad-3',
    '1-8--fl52--9----e-d4-b-a-c--3--0--7-6']

TYC_HOST = 'm.tianyancha.com'
TYC_AGENT = 'Mozilla/5.0 (Linux; U; Android 7.0; zh-cn;)'
TYC_LOCK = mt.Lock()
TYC_DONE = mt.Value('i', 0)
TYC_FAIL = mt.Value('i', 0)

BREAK_EVENT = mt.Event()

logger = util.loginit.get_logger()


def read_excel(fn, maxrows=-1):
    wb = xlrd.open_workbook(fn)
    sheet = wb.sheet_by_index(0)
    dest = os.path.splitext(fn)[0]
    for i in range(sheet.nrows):
        # 忽略前两行 列头
        if i > 1:
            no = i - 1
            if no > maxrows > 0:
                break
            row = sheet.row(i)
            group = row[5].value.strip()
            name = row[3].value.strip()
            group = re.sub('[\\\/:*?"<>|]', '_', group)
            name = re.sub('[\\\/:*?"<>|]', '_', name)
            path = os.path.join(dest, group)
            yield path, name, 0


def get_company(path, name, id=0):
    try:
        if BREAK_EVENT.is_set():
            return
        TYC(path, name, id).get_all()

        with TYC_LOCK:
            TYC_DONE.value += 1
            done = TYC_DONE.value
        logger.info('{} Done {}'.format(name, done))
    except Exception as e:
        with TYC_LOCK:
            TYC_FAIL.value += 1
        logger.error('{} {}'.format(name, e))


def get_objitem(obj, key):
    o = obj
    if key:
        for k in key.split('.'):
            if k in o:
                o = o[k]
                if o is None:
                    break
            else:
                return None
        return o
    else:
        return None


def get_utm(key, fxck_chars):
    """
    :param key: 查询的关键字 string 或者 id (int)
    :param fxck_chars: 数组 存放utm码的每一位在字典行中的位置（0-36）
    :return: utm
    取key的第一位(union code)码  <127时等同于 ASCII码
    判断ASCII>10 取10进制的第2位作为字典行索引（0-9），如果 ASCII不足10 则直接用来作为字典行索引
    idx: 字典行索引（0-9）
    例如 key = '北京'
    ord('北') = 21271
    idx = 1
    """

    if isinstance(key, str):
        asc = ord(key[0])
    else:
        asc = ord(str(key)[0])

    if asc < 10:
        idx = asc
    else:
        idx = int(str(asc)[1])

    return ''.join([SOGOU[idx][int(c)] for c in fxck_chars])


class QueryInfo(object):
    def __init__(self, cate, url, islist, datafield, totalfield):
        self.cate = cate
        self.url = 'http://{}/{}'.format(TYC_HOST, url)
        self.islist = islist
        self.datafield = datafield
        self.totalfield = totalfield


class QueryInfoEnum(Enum):
    company = QueryInfo('基本信息', 'v2/company/{id}.json', False, 'data', None)
    staff = QueryInfo('主要人员', 'expanse/staff.json?id={id}&ps={ps}&pn={pn}',
                      True, 'data.result', 'data.total')
    changeinfo = QueryInfo('变更信息', 'expanse/changeinfo.json?id={id}&ps={ps}&pn={pn}',
                           True, 'data.result', 'data.total')
    holder = QueryInfo('股东信息', 'expanse/holder.json?id={id}&ps={ps}&pn={pn}',
                       True, 'data.result', 'data.total')
    inverst = QueryInfo('对外投资', 'expanse/inverst.json?id={id}&ps={ps}&pn={pn}',
                        True, 'data.result', 'data.total')
    equityChange = QueryInfo('对外投资-股权变更', 'expanse/inverst.json?id={id}&ps={ps}&pn={pn}',
                             True, 'data.result', 'data.total')
    branch = QueryInfo('分支机构', 'expanse/branch.json?id={id}&ps={ps}&pn={pn}',
                       True, 'data.result', 'data.total')
    report = QueryInfo('年报信息', 'annualreport/newReport.json?id={id}&year={year}'
                       , False, 'data', None)
    team = QueryInfo('核心团队', 'expanse/findTeamMember.json?name={name}&ps={ps}&pn={pn}'
                     , True, 'data.page.rows', 'data.page.total')
    equity = QueryInfo('股权出质', 'expanse/companyEquity.json?name={name}&ps={ps}&pn={pn}',
                       True, 'data.items', 'data.count')
    bond = QueryInfo('债券信息', 'extend/getBondList.json?companyName={name}&ps={ps}&pn={pn}',
                     True, 'data.bondList', 'data.totalRows')
    RongZi = QueryInfo('融资历史', 'expanse/findHistoryRongzi.json?name={name}&ps={ps}&pn={pn}',
                       True, 'data.page.rows', 'data.page.total')
    Tzanli = QueryInfo('投资事件', 'expanse/findTzanli.json?name={name}&ps={ps}&pn={pn}',
                       True, 'data.page.rows', 'data.page.total')
    taxCredit = QueryInfo('税务评定', 'expanse/taxcredit.json?id={id}&ps={ps}&pn={pn}',
                          True, 'data.items', 'data.count')
    court = QueryInfo('法院公告', 'v2/court/{name}.json?ps={ps}&pn={pn}',
                      True, 'courtAnnouncements', 'total')
    lawsuit = QueryInfo('法律诉讼', 'v2/getlawsuit/{name}.json?ps={ps}&page={pn}',
                        True, 'data.items', 'data.total')
    ZhiXing = QueryInfo('被执行人', 'expanse/zhixing.json?id={id}&ps={ps}&pn={pn}',
                        True, 'data.items', 'data.count')
    punishment = QueryInfo('行政处罚', 'expanse/punishment.json?name={name}&ps={ps}&pn={pn}',
                           True, 'data.items', 'data.count')
    abnormal = QueryInfo('经营异常', 'expanse/abnormal.json?id={id}&ps={ps}&pn={pn}',
                         True, 'data.result', 'data.total')
    checkInfo = QueryInfo('抽查检查', 'expanse/companyCheckInfo.json?name={name}&ps={ps}&pn={pn}',
                          True, 'data.items', 'data.count')
    IcpList = QueryInfo('网站备案', 'IcpList/{id}.json',
                        True, 'data', None)
    product = QueryInfo('企业业务', 'expanse/findProduct.json?name={name}&ps={ps}&pn={pn}',
                        True, 'data.page.rows', 'data.page.total')
    # JingPin = QueryInfo('竞品信息', 'expanse/findJingpin.json?name={name}&ps={ps}&pn={pn}',
    #                     True, 'data.page.rows', 'data.page.total')
    appbkinfo = QueryInfo('产品信息', 'expanse/appbkinfo.json?id={id}&ps={ps}&pn={pn}',
                          True, 'data.items', 'data.count')
    TmList = QueryInfo('商标信息', 'tm/getTmList.json?id={id}&ps={ps}&pageNum={pn}',
                       True, 'data.items', 'data.viewtotal')
    purchaseland = QueryInfo('购地信息', 'expanse/purchaseland.json?name={name}&ps={ps}&pn={pn}',
                             True, 'data.companyPurchaseLandList', 'data.totalRows')
    patent = QueryInfo('专利信息', 'expanse/patent.json?id={id}&ps={ps}&pn={pn}',
                       True, 'data.items', 'data.viewtotal')
    bid = QueryInfo('招投标', 'expanse/bid.json?id={id}&ps={ps}&pn={pn}',
                    True, 'data.items', 'data.viewtotal')
    qualification = QueryInfo('资质证书', 'expanse/qualification.json?id={id}&ps={ps}&pn={pn}',
                              True, 'data.items', 'data.count')
    copyReg = QueryInfo('著作权', 'expanse/copyReg.json?id={id}&ps={ps}&pn={pn}',
                        True, 'data.items', 'data.viewtotal')
    getEmployment = QueryInfo('招聘信息', 'extend/getEmploymentList.json?companyName={name}&ps={ps}&pn={pn}',
                              True, 'data.companyEmploymentList', 'data.totalRows')

    # 企业关系 http://dis.tianyancha.com/dis/getInfoById/{id}.json


class TYC(object):
    def __init__(self, path, name, id=0):
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except:
            pass
        self.path = path
        self.sess = requests.session()
        self.sess.headers['User-Agent'] = 'User-Agent:' + TYC_AGENT
        self.name = name

        if id == 0:
            self.id = self.get_id()
            if self.id == 0:
                raise Exception('Not Found')
        else:
            self.id = id

        self.zfn = os.path.join(path, name + '.zip')

        logger.info('{} {}'.format(self.name, self.id))

    @retry()
    def get_json_cookie(self, url, id=0):
        if id == 0:
            self.set_cookie(id)
        else:
            self.set_cookie(self.id)
        return self.sess.get(url).json()

    @retry()
    def get_json(self, url):
        return self.sess.get(url).json()

    def set_cookie(self, key):
        # 取得token 和 fxck_chars
        # 'http://dis.tianyancha.com/qq/{}.json?random={}'.format(self.id, int(time.time() * 1000))

        tongji_url = 'http://{}/tongji/{}.json?random={}'.format(TYC_HOST, key, int(time.time() * 1000))
        tongji_json = self.get_json(tongji_url)
        tongji_data = tongji_json['data']['v'].split(',')
        js_code = ''.join([chr(int(code)) for code in tongji_data])
        token = re.findall('token=(\w+);', js_code)[0]
        fxck_chars = re.findall('\'([\d\,]+)\'', js_code)[0].split(',')
        utm = get_utm(key, fxck_chars)

        self.sess.cookies.set('token', token)
        self.sess.cookies.set('_utm', utm)

    def get_id(self):
        url = 'http://{}/v2/search/{}.json'.format(TYC_HOST, self.name)
        self.set_cookie(self.name)
        data = self.get_json(url)
        if data['data'] is None:
            return 0
        for d in data['data']:
            if '<em>{}</em>'.format(self.name) == d['name']:
                return int(d['id'])
        return 0

    def get_all(self):
        with zipfile.ZipFile(self.zfn, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            for qe in QueryInfoEnum:
                q = qe.value
                if BREAK_EVENT.is_set():
                    break
                try:
                    info = zf.getinfo(q.cate + '.json')
                    logger.info('{} {} Exist Skip'.format(self.name, q.cate))
                    continue
                except:
                    pass
                try:
                    if qe == QueryInfoEnum.report:
                        rows = self.save_report(zf, q)
                    elif qe == QueryInfoEnum.equityChange:
                        rows = self.save_equitychange(zf, q)
                    else:
                        rows = self.save_json(zf, q)

                    if rows:
                        logger.info('{} {} {}'.format(self.name, q.cate, rows))
                except Exception as e:
                    logger.error('{} {} FAIL {}'.format(self.name, q.cate, e))

    def save_json(self, zf, q):
        fn = q.cate + '.json'
        rows = 0
        tfn = 'tmp/{}_{}.tmp'.format(q.cate, self.id)
        if q.islist:
            total = 0
            pn = 0

            with open(tfn, mode='wt', encoding='utf-8') as f:
                while True:
                    pn += 1
                    url = q.url.format(id=self.id, name=self.name, ps=50, pn=pn)
                    result = self.get_json_cookie(url)
                    data = get_objitem(result, q.datafield)
                    if not isinstance(data, list):
                        break
                    elif len(data) == 0:
                        break

                    for row in data:
                        f.writelines(json.dumps(row, ensure_ascii=False))
                        rows += 1

                    if total == 0:
                        total = get_objitem(result, q.totalfield)
                        if total:
                            total = int(total)
                        else:
                            break

                    if total <= rows:
                        break
                    if total < pn * 10:
                        break

                    if BREAK_EVENT.is_set():
                        break
        else:
            url = q.url.format(id=self.id, name=self.name)
            result = self.get_json_cookie(url)
            data = get_objitem(result, q.datafield)
            if data is None:
                return 0
            with open(tfn, mode='wt', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
                rows = 1

        zf.write(tfn, fn)
        os.remove(tfn)
        return rows

    def save_report(self, zf, q):
        rdata = ''
        rows = 0
        for year in range(2013, time.localtime().tm_year):
            if BREAK_EVENT.is_set():
                break
            try:
                result = self.get_json_cookie(q.url.format(id=self.id, year=year))
                data = get_objitem(result, q.datafield)
                if data is None or 'baseInfo' not in data:
                    continue
                else:
                    rdata += json.dumps(data, ensure_ascii=False) + '\n'
                    rows += 1
            except Exception as e:
                logger.error('{} {} {} FAIL {}'.format(self.name, q.cate, year, e))
        if rows:
            zf.writestr(q.cate + '.json', rdata)

        return rows

    def save_equitychange(self, zf, q):
        fn = q.cate + '.json'
        rows = 0
        tfn = 'tmp/{}_{}.tmp'.format(q.cate, self.id)
        total = 0
        pn = 0
        saved = 0
        with open(tfn, mode='wt', encoding='utf-8') as f:
            while True:
                pn += 1
                url = q.url.format(id=self.id, name=self.name, ps=50, pn=pn)
                result = self.get_json_cookie(url)
                data = get_objitem(result, q.datafield)
                if not isinstance(data, list):
                    break
                elif len(data) == 0:
                    break

                for row in data:
                    rows += 1
                    if 'id' not in row:
                        continue
                    iid = row['id']
                    iname = row['name']
                    for year in range(2013, time.localtime().tm_year):
                        if BREAK_EVENT.is_set():
                            break
                        try:
                            d = self.get_equitychange(iid, iname, year)
                            if d:
                                f.write(json.dumps(d, ensure_ascii=False) + '\n')
                                saved += 1
                        except Exception as e:
                            logger.error('{} {} - {} {} FAIL {}'.format(self.name, q.cate, iname, year, e))

                if total == 0:
                    total = get_objitem(result, q.totalfield)
                    if total:
                        total = int(total)
                    else:
                        break

                if total <= rows:
                    break
                if total < pn * 10:
                    break
                if BREAK_EVENT.is_set():
                    break

        zf.write(tfn, fn)
        os.remove(tfn)
        return saved

    def get_equitychange(self, id, name, year):
        q = QueryInfoEnum.report.value
        result = self.get_json_cookie(q.url.format(id=id, year=year), id=id)
        data = get_objitem(result, q.datafield)
        if data:
            ec = data['equityChangeInfoList']
            sh = data['shareholderList']
            if (isinstance(ec, list) and len(ec) > 0) or (isinstance(sh, list) and len(sh) > 0):
                return {'id': id, 'name': name, 'year': year,
                        'equityChangeInfoList': ec,
                        'shareholderList': sh
                        }


def on_break(s, f):
    BREAK_EVENT.set()


def chk_argv(argv):
    try:
        if not os.path.exists(argv[1]):
            return False
        return True
    except:
        return False


def main(*argv):
    if not chk_argv(argv):
        print('usage:tyc.py [excelfile]')
        return

    begtime = time.time()

    excelfile = argv[1]
    signal.signal(signal.SIGTERM, on_break)
    signal.signal(signal.SIGINT, on_break)
    pool = mt.Pool(20)
    ret = pool.starmap_async(get_company, read_excel(excelfile))

    while not ret.ready():
        BREAK_EVENT.wait(1)
        if BREAK_EVENT.is_set():
            logger.warning('RECV BREAK SIGNAL!!!')
            pool.close()
            pool.join()
            logger.info('Break!')
            break
    with TYC_LOCK:
        done = TYC_DONE.value
        fail = TYC_FAIL.value

    logger.info('Finish Done:{} Fail:{} Time:{:.2f} '.format(done, fail,time.time() - begtime))


def chk_name(excelfile):
    irow = 0
    logger.disabled = True
    for p, n, id in read_excel(excelfile):
        irow += 1
        try:
            TYC(p, n, id)
            print(irow, n, 'OK!')
        except Exception as e:
            print(irow, n, e)


if __name__ == '__main__':
    import sys

    main(*sys.argv)
    # get_company('e:/tyc/中粮茶业', '中土畜环球木业（北京）有限公司')
    # chk_name('e:/tyc/17户集团成员名单.xls')
