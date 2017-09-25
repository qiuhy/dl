# -*- coding: utf-8 -*-
"""
Created on 2017-05-17

@author: hy_qiu
"""

import json
import logging
import os
import re
import tempfile
import time
import zipfile

import requests
import xlrd
from bs4 import BeautifulSoup

from src.util.wraps import retry

TIMEOUT = 15

REGEX_TITLE = re.compile('[\\\/:*?"<>|\r\n]')


def get_stocklist():
    ret = []
    for url in ('http://sc.hkex.com.hk/TuniS/www.hkex.com.hk/chi/market/sec_tradinfo/stockcode/eisdeqty_c.htm',
                'http://sc.hkex.com.hk/TuniS/www.hkex.com.hk/chi/market/sec_tradinfo/stockcode/eisdgems_c.htm'):
        rep = requests.get(url)
        rep.encoding = 'utf-8'
        soup = BeautifulSoup(rep.text, 'html5lib')
        tb = soup.find('table', {'class': 'table_grey_border'})
        if tb is None:
            break
        headrow = True
        for tr in tb.find('tbody').find_all('tr'):
            if headrow:
                headrow = False
                continue
            col = 0
            stock = []
            for td in tr.find_all('td'):
                col += 1
                if col in (1, 2):
                    stock.append(td.get_text(strip=True))

            if len(stock) == 2:
                ret.append(stock)
    # if dbqueue:
    #     if len(ret):
    #         ops = []
    #         sql = 'replace into hk_brief(Code,Name) values(?,?)'
    #         for stock in ret:
    #             ops.append((sql, stock))
    #         dbqueue.put(ops)
    return ret


def get_ah(dbqueue=None):
    url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getANHData?node=hgt_ah'
    txt = re.sub(r'([{|,])(\w+):', r'\1"\2":', requests.get(url).text).replace('\\\'', '’')
    ahjson = json.loads(txt)
    ops = []
    sql = 'replace into hk_ah(HCode,ACode) values(?,?)'
    for ah in ahjson:
        param = [ah['h'], ah['a']]
        ops.append((sql, param))

    if dbqueue:
        dbqueue.put(ops)
    else:
        print(ops)
    return len(ops)


@retry()
def get_manager(logger=None, dbqueue=None):
    url = 'http://www.hkexnews.hk/reports/dirsearch/dirlist/Documents/Director_List.xls'
    response = requests.get(url)
    response.raise_for_status()
    fn = tempfile.mktemp('.xls')
    open(fn, 'wb').write(response.content)
    if logger:
        logger.info('HK Manager Download:%s', response.headers['Content-length'])
    st = xlrd.open_workbook(fn).sheet_by_index(0)
    ops = []
    for r in range(st.nrows):
        if r == 0:
            sql = """
            DROP TABLE IF EXISTS hk_manager;
            CREATE TABLE hk_manager(Code TEXT NOT NULL,EName TEXT,CName TEXT
            ,Capacity TEXT,Position TEXT,BeginDate TEXT,EndDate TEXT);
            """
            ops.append(sql)
            sql = 'insert into hk_manager values(?,?,?,?,?,?,?)'
        else:
            param = []
            if st.cell_value(r, 3) == 'Delisted':
                continue
            for c in [2, 4, 5, 6, 7, 8, 9]:
                param.append(st.cell_value(r, c))
            ops.append((sql, param))

    if len(ops):
        if dbqueue:
            dbqueue.put(ops)
        else:
            print(ops[0])
            print(ops[1])
            print(ops[2])
            print('...')
            print(ops[-1])
            print('Total {}'.format(len(ops) - 2))
        if logger:
            logger.info('HK Manager Saved :%d', len(ops))
    # ['Executive Director', '执行董事',
    #  'Alternate Director', '候补董事',
    #  'Independent Non Executive Director - A/F', '独立非执行董事',
    #  'Independent Non Executive Director', '独立非执行董事',
    #  'Non Executive Director', '非执行董事',
    #  ]
    if os.path.exists(fn):
        os.remove(fn)
    return len(ops)


# 持股信息 http://web.ifzq.gtimg.cn/appstock/hk/HkInfo/getRightsDirector?p=2&c=00700&max=30
# 分红信息 http://web.ifzq.gtimg.cn/appstock/hk/HkInfo/getDividends?p=1&c=00177&max=100

class HKStock:
    def __init__(self, code='', name='', logger=None):
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

    def get_brief(self, dbqueue=None):
        try:
            val = {'c': self.code}
            url = 'http://web.ifzq.gtimg.cn/appstock/hk/HkInfo/getBasicInfo'
            response = requests.get(url, val)
            txt = response.json()
            data = txt['data']

            dbfield = ['Code', 'Name', '"公司名称"', '"行业"', '"董事长"', '"主要持股人"', '"公司秘书"',
                       '"注册地址"', '"公司地址"', '"上市日期"', '"核数师"', '"法律顾问"',
                       '"经营范围"', '"主要往来银行"', '"网站"', '"电话"', '"电子邮箱"', '"传真"']
            keys = ['CMP_NAME_CN', 'SECTOR_NAME', 'CHAIRMAN', 'MASTER_HAREHOLDER', 'SECRETARY',
                    'REG_OFFICE', 'HEAD_OFFICE', 'LISTING_DATE', 'AUDITORS', 'LADVISORS',
                    'ACTIVITIES', 'BANKERS', 'WEBSITE', 'TEL', 'EMAIL', 'FAX']
            sql = 'replace into hk_brief({}) values({})'.format(','.join(dbfield), ','.join('?' * len(dbfield)))
            param = [self.code, self.name]
            for k in keys:
                v = data[k]
                if isinstance(v, list):
                    v = ' '.join(v)
                param.append(v)
            op = (sql, param)

            if dbqueue:
                dbqueue.put(op)
            else:
                print(op)
            self.logger.info('公司简况 Succesed')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('公司简况 FAIL')
        return

    def get_report(self, path=None, dbqueue=None):
        try:
            # 1 fzb 2 llb 3 lrb
            url = 'http://web.ifzq.gtimg.cn/appstock/hk/HkInfo/getFinReport'
            zf = None
            for rpt_type in (1, 2, 3):
                rpt_name = ['hk_fzb', 'hk_llb', 'hk_lrb'][rpt_type - 1]
                val = {'type': rpt_type,
                       'reporttime_type': -1,
                       'code': self.code,
                       'startyear': 1900,
                       'endyear': time.localtime().tm_year}
                jsonobj = requests.get(url, val).json()
                if 'data' in jsonobj and 'data' in jsonobj['data']:
                    data = jsonobj['data']['data']
                    sql = ''
                    total = 0
                    ops = []
                    if path:
                        zf = zipfile.ZipFile('{}/{}_{}.zip'.format(path, self.code, rpt_name), mode='w')
                    for row in data:
                        if sql == '':
                            sql = 'replace into {} ({}) values ({})'.format(rpt_name,
                                                                            ','.join(row.keys()),
                                                                            ','.join('?' * len(row)))
                        if 'is_null_row' not in row:
                            if dbqueue:
                                ops.append((sql, tuple(row.values())))
                            total += 1
                            if zf:
                                fn = '{}_{}_{}.json'.format(row['fd_year'], row['fd_type'], row['reporttype_name'])
                                zf.writestr(fn, json.dumps(row), compress_type=zipfile.ZIP_DEFLATED)
                    if zf:
                        zf.close()
                    if total > 0:
                        if dbqueue:
                            dbqueue.put(ops)
                        self.logger.info('财务报表 %s %d', rpt_name, total)
                    else:
                        self.logger.info('财务报表 %s is zero', rpt_name)

                self.logger.info('财务报表 Succesed')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('财务报表 FAIL')
            if zf:
                zf.close()
        return

    def get_anno(self, path=None, break_event=None):
        url = 'http://www.hkexnews.hk/listedco/listconews/advancedsearch/search_active_main_c.aspx'
        zf = None
        try:
            anno_no = 0
            total = 0
            skip = 0
            succ = 0
            fail = 0
            starttime = time.time()
            savebytes = 0
            if path:
                zf = zipfile.ZipFile(path + '/' + self.code + '.zip', mode='a')

            sess = requests.Session()
            soup = self.get_anno_soup(sess, url, None)
            form = soup.find('form', id='aspnetForm')

            val = {'ctl00$rdo_SelectDateOfRelease': 'rbManualRange',
                   'ctl00$sel_DateOfReleaseFrom_d': '01',
                   'ctl00$sel_DateOfReleaseFrom_m': '04',
                   'ctl00$sel_DateOfReleaseFrom_y': '1999',
                   'ctl00$sel_DateOfReleaseTo_d': '{:02d}'.format(time.localtime().tm_mday),
                   'ctl00$sel_DateOfReleaseTo_m': '{:02d}'.format(time.localtime().tm_mon),
                   'ctl00$sel_DateOfReleaseTo_y': '{:04d}'.format(time.localtime().tm_year),
                   'ctl00$rdo_SelectDocType': 'rbAll',
                   'ctl00$rdo_SelectSortBy': 'rbDateTime',
                   # 'ctl00$hfAlert': '',
                   # 'ctl00$sel_tier_1': -2,
                   # 'ctl00$sel_tier_2': -2,
                   # 'ctl00$sel_tier_2_group': -2,
                   # 'ctl00$sel_DocTypePrior2006': -1,
                   'ctl00$txt_stock_code': self.code,
                   'ctl00$txt_stock_name': '',
                   'ctl00$txtKeyWord': ''}
            for vinput in form.find_all('input'):
                if 'value' in vinput.attrs and vinput['type'] == 'hidden':
                    val[vinput['name']] = vinput['value']

            while True:
                if break_event and break_event.is_set():
                    return
                soup = self.get_anno_soup(sess, url, val)
                if total == 0:
                    tiptxt = soup.find('span', id='ctl00_lblDisplay').get_text(strip=True)
                    total = int(tiptxt.split(' ')[6])
                    anno_no = total
                form = soup.find('form', id='aspnetForm')
                tb = form.find('table', id='ctl00_gvMain')

                for a in tb.find_all('a', {'class': 'news'}):
                    if break_event and break_event.is_set():
                        return

                    if a['id'].startswith('ctl00_gvMain_') and a['id'].endswith('_hlTitle'):
                        anno_title = a.get_text(strip=True)
                        anno_href = a['href']
                    else:
                        continue

                    fn = anno_href.split('/')[-1].split('.')
                    anno_id = fn[0]
                    anno_ext = fn[-1]
                    fn = '{} {}.{}'.format(anno_id, REGEX_TITLE.sub('', anno_title), anno_ext)
                    try:
                        writed = self.save_anno(zf, anno_href, fn)
                        if writed == 0:
                            skip += 1
                            self.logger.debug('%d/%d Exists Skip', anno_no, total)
                        else:
                            savebytes += writed
                            succ += 1
                            self.logger.debug('%d/%d Succesed %d', anno_no, total, writed)
                    except Exception as e:
                        self.logger.error('%d/%d %s FAIL', anno_no, total, e)
                        fail += 1

                    anno_no -= 1

                if not self.get_anno_next(form, val):
                    break

            usedtime = time.time() - starttime
            speed = savebytes / usedtime / 1024
            self.logger.info('公告信息 Total:%d Exists:%d Succesed:%d FAIL:%d Time used:%.3fs Speed:%.2fK/s',
                             total, skip, succ, fail, usedtime, speed)
        except Exception as e:
            self.logger.error(e)
            self.logger.error('公告信息 FAIL')
        finally:
            if zf:
                zf.close()
        return

    @staticmethod
    def get_anno_next(form, val):
        val.clear()
        for vinput in form.find_all('input'):
            if vinput['type'] == 'hidden':
                val[vinput['name']] = vinput['value']
            elif vinput['name'] == 'ctl00$btnNext':
                val['ctl00$btnNext.x'] = 3
                val['ctl00$btnNext.y'] = 3
        return 'ctl00$btnNext.x' in val

    @retry()
    def get_anno_soup(self, sess, url, val=None):
        rep = sess.post(url, val)
        rep.encoding = 'utf-8'
        return BeautifulSoup(rep.text, 'html5lib')

    @retry()
    def save_anno(self, zf, href, fn):
        url = 'http://www.hkexnews.hk/' + href
        if zf:
            try:
                info = zf.getinfo(fn)
                if info.file_size > 0:
                    return 0
            except:
                pass
            rep = requests.get(url, timeout=TIMEOUT)
            zf.writestr(fn, rep.content, compress_type=zipfile.ZIP_DEFLATED)
        else:
            rep = requests.head(href)
        return int(rep.headers['Content-Length'])


if __name__ == '__main__':
    # HKStock('00177').get_report('e:/stock/HKReport')
    get_manager()
