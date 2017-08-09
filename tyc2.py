# -*- coding: utf-8 -*-
"""
Created on 17-7-18

@author: hy_qiu
"""
import json
import multiprocessing.dummy as mt
import os
import re
import time

import requests
from bs4 import BeautifulSoup
import threading

import util.excel
import util.fileutil
import util.loginit
import util.mt
import util.verify
from util.wraps import retry

AGENT_FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'
# AGENT_Android7 = 'Mozilla/5.0 (Linux; U; Android 7.0; zh-cn;)'
# AGENT_iPhone3 = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16'
# 'Dalvik/2.1.0 (Linux; U; Android 7.0;)'
# 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13C75 Safari/601.1'
TYC_HOST = 'https://www.tianyancha.com'

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

BREAK_EVENT = mt.Event()
_LOCK = mt.Lock()
_DONE = mt.Value('i', 0)
_FAIL = mt.Value('i', 0)
_EMPTY = mt.Value('i', 0)

logger = util.loginit.get_logger('tyc2')


def wait_for_verify():
    logger.warning('wait_for_verify start')
    while not util.verify.chk_TYC():
        if BREAK_EVENT.is_set():
            return
        time.sleep(1)
    logger.warning('wait_for_verify OK')
    time.sleep(1)


def get_utm(key, utm_chars):
    asc = ord(str(key)[0])
    idx = (int(str(asc)[1]) + 1) % 10
    utm = ''.join([SOGOU[idx][int(c)] for c in utm_chars])
    return utm


def pgf_table(datainfo, div_head):
    tb = div_head.find('table', class_='companyInfo-table')
    if len(datainfo.colnames) == 0:
        for th in tb.thead.find_all('th'):
            datainfo.colnames.append(th.get_text(strip=True))
        datainfo.formatcolumn()
    for tr in tb.tbody.find_all('tr'):
        tds = list(tr.find_all('td'))
        item = {}
        for i in range(len(datainfo.colnames)):
            key = datainfo.colnames[i]
            if key == '':
                continue
            elif datainfo.cdfdict and key in datainfo.cdfdict.keys():
                item[key] = cdf_text(tds[i], datainfo.cdfdict[key])
            else:
                item[key] = tds[i].get_text(strip=True)
        yield item


def cdf_text(element, cdf=None):
    if cdf is None or cdf == '':
        return
    elif isinstance(cdf, str):
        tag = element.find(cdf)
        if tag:
            return tag.get_text(strip=True)
    elif callable(cdf):
        return cdf(element)
    else:
        return element.get_text(strip=True)


def cdf_more(element):
    span = element.find('span', class_='companyinfo_show_more_btn')
    if span and span.has_attr('onclick'):
        jsonstr = re.findall('\w+\((.+)\)', span['onclick'])
        if jsonstr and len(jsonstr):
            try:
                return json.loads(jsonstr[0])
            except:
                pass
    return ''


def get_base(soup):
    base = {}
    div = soup.find('div', class_='company_header_width')
    base['名称'] = div.div.span.get_text(strip=True)

    div_row = list(div.div.find_all('div', class_='new-c3', recursive=False))
    div_col = list(div_row[0].find_all('div'))
    base['电话'] = list(div_col[0].find_all('span'))[1].get_text(strip=True)
    base['邮箱'] = list(div_col[1].find_all('span'))[1].get_text(strip=True)
    div_col = list(div_row[1].find_all('div'))
    web = div_col[0].find('a')
    base['网址'] = web.get_text(strip=True) if web else ''
    base['地址'] = list(div_col[1].find_all('span'))[1].get_text(strip=True)
    hname = []
    div = div.find('div', class_='historyNameBox')
    if div:
        for h in div.find_all('div'):
            hname.append(h.get_text(strip=True))
    base['曾用名'] = hname

    div = soup.find('div', class_='baseInfo_model2017')
    tb = div.find('table', class_='companyInfo-table').tbody
    tds = list(tb.find_all('td'))
    a = tds[0].find('a', title=True)
    base['法人'] = a.get_text(strip=True)
    div_col = tds[1].find_all('div', class_='baseinfo-module-content-value')
    base['注册资本'] = div_col[0].get_text(strip=True)
    base['注册时间'] = div_col[1].get_text(strip=True)
    base['企业状态'] = div_col[2].get_text(strip=True)

    div = soup.find('div', class_='base2017')
    for td in div.find_all('td', class_='basic-td'):
        div = td.find('div')
        key = div.contents[0]
        key = key.strip('\r\n ')
        if key.endswith('：'):
            key = key[:-1]
        else:
            continue
        if key == '经营范围':
            val = div.find('span', class_='js-full-container').get_text(strip=True)
        else:
            val = re.sub('\s', '', div.find('span').get_text(strip=True))
        base[key] = val
    return base


def pfg_staff(di, div_head):
    for div in div_head.find_all('div', class_='staffinfo-module-container'):
        title = div.div.div.get_text(strip=True)
        tname = div.div.a.get_text(strip=True)
        yield {'姓名': tname, '职位': title}


def pgf_stockbrife(di, div_head):
    brife = {}
    tb = div_head.find('table', class_='companyInfo-table')
    for tr in tb.find_all('tr'):
        tds = list(tr.find_all('td'))
        for i in range(len(tds)):
            if tds[i].has_attr('class') and 'table-left' in tds[i]['class']:
                key = tds[i].get_text(strip=True)
                brife[key] = tds[i + 1].get_text(strip=True)
    yield brife


def pgf_teamMember(di, div_head):
    for div in div_head.find_all('div', class_='team-item'):
        name = div.find('div', class_='team-name').get_text(strip=True)
        title = div.find('div', class_='team-title').get_text(strip=True)
        brife = div.find('ul').get_text(strip=True)
        yield {'姓名': name, '职位': title, '简介': brife}


def pgf_firmProduct(di, div_head):
    for div in div_head.find_all('div', class_='product-item'):
        title = div.find('span', class_='title').get_text(strip=True)
        hangye = div.find('div', class_='hangye').get_text(strip=True)
        yeweu = div.find('div', class_='yeweu').get_text(strip=True)
        yield {'名称': title, '类型': hangye, '简介': yeweu}


class DataInfo:
    _datalist = {'seniorPeople': {'ps': 10, 'searchParam': 'id'},
                 'holdingCompany': {'ps': 10, 'searchParam': 'id'},
                 'announcement': {'ps': 10, 'searchParam': 'id'},
                 'equityChange': {'ps': 10, 'searchParam': 'id'},
                 'bonus': {'ps': 10, 'searchParam': 'id'},
                 'staff': {'ps': 20, 'searchParam': 'id'},
                 'holder': {'ps': 20, 'searchParam': 'id'},
                 'invest': {'ps': 20, 'searchParam': 'id'},
                 'changeinfo': {'ps': 5, 'searchParam': 'id'},
                 'branch': {'ps': 10, 'searchParam': 'id'},
                 'touzi': {'ps': 10, 'searchParam': 'name'},
                 'rongzi': {'ps': 10, 'searchParam': 'name'},
                 'teamMember': {'ps': 5, 'searchParam': 'name'},
                 'firmProduct': {'ps': 15, 'searchParam': 'name'},
                 'jingpin': {'ps': 10, 'searchParam': 'name'},
                 'lawsuit': {'ps': 10, 'searchParam': 'name'},
                 'court': {'ps': 5, 'searchParam': 'name'},
                 'zhixing': {'ps': 5, 'searchParam': 'id'},
                 'abnormal': {'ps': 5, 'searchParam': 'id'},
                 'punish': {'ps': 5, 'searchParam': 'name'},
                 'illegal': {'ps': 5, 'searchParam': 'name'},
                 'equity': {'ps': 5, 'searchParam': 'name'},
                 'mortgage': {'ps': 5, 'searchParam': 'name'},
                 'towntax': {'ps': 5, 'searchParam': 'id'},
                 'bid': {'ps': 10, 'searchParam': 'id'},
                 'bond': {'ps': 5, 'searchParam': 'name'},
                 'purchaseland': {'ps': 5, 'searchParam': 'name'},
                 'recruit': {'ps': 10, 'searchParam': 'name'},
                 'taxcredit': {'ps': 5, 'searchParam': 'id'},
                 'check': {'ps': 5, 'searchParam': 'name'},
                 'qualification': {'ps': 5, 'searchParam': 'id'},
                 'product': {'ps': 5, 'searchParam': 'id'},
                 'tmInfo': {'ps': 5, 'searchParam': 'id'},
                 'patent': {'ps': 5, 'searchParam': 'id'},
                 'copyright': {'ps': 5, 'searchParam': 'id'},
                 'icp': {'ps': 5, 'searchParam': 'id'}
                 }

    def __init__(self, name, key, cdfdict=None, coldict=None, pgf=None, headdict=None):
        # cdfdict(column define function): dict { 列名称 : '' (忽略此列) 或 指定tag 或 自定义列操作函数}
        # coldict: {column index or column name:column name}
        # pgf(page function): function(datainfo,div_head) 用户自定义页面解析函数
        self.name = name
        self.key = key
        if headdict:
            self.headdict = headdict
        else:
            self.headdict = {'id': '_container_' + key}

        try:
            self.pageszie = self._datalist[key]['ps']
            self.searchby = self._datalist[key]['searchParam']
        except:
            pass
        self.url = '{}/pagination/{}.xhtml'.format(TYC_HOST, key)
        self.cdfdict = cdfdict
        self.coldict = coldict
        self.colnames = []  # table.thead.th
        if pgf:
            self.pgf = pgf
        else:
            self.pgf = pgf_table

    def formatcolumn(self):
        if not isinstance(self.coldict, dict):
            return
        for k in self.coldict.keys():
            if isinstance(k, int):
                self.colnames[k] = self.coldict[k]
            elif isinstance(k, str):
                for i in range(len(self.colnames)):
                    if self.colnames[i] == k:
                        self.colnames[i] = self.coldict[k]
                        break


TYC_DATALIST = [
    # 股票信息
    DataInfo('企业简介', 'stockbrife', pgf=pgf_stockbrife, headdict={'id': 'nav-main-stockNum'}),
    DataInfo('高管信息', 'seniorPeople', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('参股控股', 'holdingCompany'),
    DataInfo('股本变动', 'equityChange'),
    DataInfo('分红情况', 'bonus'),

    # 企业背景
    DataInfo('股东信息', 'holder', cdfdict={'股东': 'a', '认缴出资': 'span'}, coldict={0: '股东'}),
    DataInfo('主要人员', 'staff', pgf=pfg_staff),
    DataInfo('对外投资', 'invest', cdfdict={'被投资法定代表人': 'a'}),
    DataInfo('变更记录', 'changeinfo'),
    DataInfo('企业年报', 'report', headdict={'tyc-event-ch': 'CompangyDetail.nianbao'}),
    DataInfo('分支机构', 'branch'),

    # 企业发展
    DataInfo('融资历史', 'rongzi'),
    DataInfo('核心团队', 'teamMember', pgf=pgf_teamMember),
    DataInfo('企业业务', 'firmProduct', pgf=pgf_firmProduct),
    DataInfo('投资事件', 'touzi'),

    # 司法风险
    DataInfo('法律诉讼', 'lawsuit'),
    DataInfo('法院公告', 'court', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('失信人', 'shixinren', cdfdict={'详情': cdf_more}, coldict={-1: '详情'},
             headdict={'tyc-event-ch': 'CompangyDetail.shixinren'}),
    DataInfo('被执行人', 'zhixing'),

    # 经营风险
    DataInfo('经营异常', 'abnormal'),
    DataInfo('行政处罚', 'punish', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('股权出质', 'equity'),
    DataInfo('动产抵押', 'mortgage', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('欠税公告', 'towntax'),

    # 经营状况
    DataInfo('招投标', 'bid'),
    DataInfo('债券信息', 'bond', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('购地信息', 'purchaseland', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('招聘信息', 'recruit', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('税务评级', 'taxcredit'),
    DataInfo('抽查检查', 'check'),
    DataInfo('产品信息', 'product', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),

    # 知识产权
    DataInfo('商标信息', 'tmInfo', coldict={'商标': ''}),
    DataInfo('专利信息', 'patent', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('著作权', 'copyright', cdfdict={'详情': cdf_more}, coldict={-1: '详情'}),
    DataInfo('网站备案', 'icp')
]


class TYC2:
    def __init__(self, name, id=0):
        self.sess = requests.session()
        self.sess.headers['User-Agent'] = AGENT_FIREFOX
        if id == 0:
            id = self.get_companyid(name)
        if id:
            self.cid = id
            self.cname = name
        else:
            raise Exception('名称不匹配')

    @retry()
    def get_response(self, url, param=None):
        with _LOCK:
            resp = self.sess.get(url, params=param, timeout=60)
            if resp.status_code != 200:
                logger.debug('{} {} {}'.format(resp.status_code, url, param if param else ''))
            # print(threading.current_thread().name, resp.status_code, url, param)

            if resp.status_code in [401, 403, 503] \
                    or resp.url.startswith(TYC_HOST + '/login?') \
                    or resp.url.find('/antirobot.tianyancha.com/captcha/verify?') >= 0:
                wait_for_verify()
                resp = self.sess.get(url, params=param, timeout=60)

            resp.raise_for_status()
            return resp

    def get_soup(self, url, param=None):
        resp = self.get_response(url, param)
        soup = BeautifulSoup(resp.text, 'html5lib')
        return soup

    @retry()
    def set_cookie(self, key):
        # 取得token 和 utm_chars
        url = '{}/tongji/{}.json'.format(TYC_HOST, key)
        resp = self.get_response(url, {'_': int(time.time() * 1000)})
        try:
            tongji_json = resp.json()
            tongji_data = tongji_json['data'].split(',')
            js_code = ''.join([chr(int(code)) for code in tongji_data])
            token = re.findall('token=(\w+);', js_code)[0]
            utm_chars = re.findall('\'([\d\,]+)\'', js_code)[0].split(',')
            utm = get_utm(key, utm_chars)

            self.sess.cookies.set('token', token)
            self.sess.cookies.set('_utm', utm)
        except Exception as e:
            raise e

    def get_report_detail(self, href):
        report = {}
        soup = self.get_soup(TYC_HOST + href)

        div_body = soup.find('div', class_='report_body')
        div_content = list(div_body.find_all('div', recursive=False))[1]
        for div in list(div_content.find_all('div', class_=True)):
            title = div.find('div', class_='report_title')
            tb = div.find('table', class_='table')
            if title is None or tb is None:
                continue
            rpt_key = title.get_text(strip=True)
            thead = tb.find('thead')
            if thead:
                keys = []
                rows = []
                for th in thead.find_all('th'):
                    keys.append(th.get_text(strip=True))

                for tr in tb.tbody.find_all('tr'):
                    tds = list(tr.find_all('td'))
                    row = {}
                    for i in range(len(keys)):
                        row[keys[i]] = tds[i].get_text(strip=True)
                    rows.append(row)
                if len(rows):
                    report[rpt_key] = rows
            else:
                tds = list(tb.find_all('td'))
                item = {}
                for i in range(len(tds)):
                    if tds[i].has_attr('class') and 'report_key' in tds[i]['class']:
                        key = tds[i].get_text(strip=True)
                        item[key] = tds[i + 1].get_text(strip=True)
                report[rpt_key] = item
        return report

    def get_report(self, div_head):
        report = []
        if div_head:
            for rpt in div_head.find_all('div', class_='report_item_2017'):
                year = rpt.div.get_text(strip=True)
                href = rpt.find('a')['href']
                d = self.get_report_detail(href)
                if d:
                    d['年度'] = year
                    report.append(d)
        return report

    def get_data(self, soup, datainfo):
        data = []
        pageno = 1
        totalpage = 0

        div_head = soup.find('div', datainfo.headdict)
        while div_head:
            if BREAK_EVENT.is_set():
                return
            for item in datainfo.pgf(datainfo, div_head):
                data.append(item)

            pager = div_head.find('div', class_='company_pager')
            if pager:
                totalpage = int(pager.find('div', class_='total').get_text(strip=True)[1:-1])
            pageno += 1
            if pageno > totalpage:
                break
            if datainfo.searchby == 'id':
                self.set_cookie(self.cid)
                param = {'ps': datainfo.pageszie, 'pn': pageno, 'id': self.cid, '_': int(time.time() * 1000)}
            else:
                self.set_cookie(self.cname)
                param = {'ps': datainfo.pageszie, 'pn': pageno, 'name': self.cname, '_': int(time.time() * 1000)}

            div_head = self.get_soup(datainfo.url, param)

        return data

    def get_company(self):
        url = '{}/company/{}'.format(TYC_HOST, self.cid)
        soup = self.get_soup(url)

        comyany = dict()
        comyany['id'] = str(self.cid)
        comyany['基本信息'] = get_base(soup)
        for ti in TYC_DATALIST:
            if BREAK_EVENT.is_set():
                return
            if ti.key == 'report':
                data = self.get_report(soup.find('div', ti.headdict))
            else:
                data = self.get_data(soup, ti)
            if data and len(data):
                comyany[ti.name] = data
                logger.info('{} {} {}'.format(self.cname, ti.name, len(data)))

        return comyany

    def get_companyid(self, cname):
        url = '{}/search'.format(TYC_HOST)
        soup = self.get_soup(url, {'key': cname})
        div_list = soup.find('div', class_='search_result_container')
        if div_list:
            for div in div_list.find_all('div', class_='search_result_single'):
                a = div.find('a', {'tyc-event-ch': 'CompanySearch.Company'})
                if a and cname == a.get_text(strip=True):
                    cid = a['href'].split('/')[-1]
                    return cid


def save_company(no, name, fn):
    try:
        c = TYC2(name).get_company()
        if c:
            util.fileutil.check_filepath(fn)
            with open(fn, mode='wt', encoding='utf-8') as f:
                json.dump(c, f, ensure_ascii=False, indent='\t')
            with _LOCK:
                _DONE.value += 1
                logger.info('{} {} OK '.format(no, name))
    except Exception as e:
        with _LOCK:
            _FAIL.value += 1
        logger.error('{} {} FAIL {}'.format(no, name, e))


def main(fn, startrow, namecol, pathcol, sheetindex=0):
    if not os.path.exists(fn):
        print('{} dose not exists')
        return
    basepath = os.path.splitext(fn)[0]
    if not os.path.exists(basepath):
        os.mkdir(basepath)

    exists = 0
    total = 0
    results = []
    pool = mt.Pool(10)
    util.mt.allow_break(BREAK_EVENT)
    for no, row in util.excel.read_excel(fn, sheetindex=sheetindex, startrow=startrow):
        name = row[namecol].value.strip()
        if name == '':
            continue

        path = row[pathcol].value.strip()
        path = os.path.join(basepath, path)
        jfn = os.path.join(path, name + '.json')

        total += 1
        if os.path.exists(jfn):
            exists += 1
        else:
            results.append(pool.apply_async(save_company, (no, name, jfn)))

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
    main('e:/tyc2/17户集团成员名单汇总.xls', 2, 1, 5, 1)
    # 厦门市美亚柏科信息股份有限公司 31333007
    # 北京百度网讯科技有限公司 22822
    # TYC2('北京北汽恒盛置业有限公司顺义餐饮管理分公司').get_company()
