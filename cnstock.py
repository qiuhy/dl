# -*- coding: utf-8 -*-
"""
Created on 2017-05-11

@author: hy_qiu
"""
import csv
import re
import tempfile
import time
import uuid
import zipfile
from enum import Enum

from bs4 import BeautifulSoup

from crawler import *
from util.wraps import retry


class ReportType(Enum):
    fzb = '负债表'
    lrb = '利润表'
    llb = '流量表'


class HolderType(Enum):
    Top10 = '十大股东'
    Circular = '流通股东'


class ShareBonusType(Enum):
    sharebonus_1 = '分红'
    sharebonus_2 = '配股'


class ManagerType(Enum):
    gg = '高管'
    ds = '董事'
    js = '监事'

    @staticmethod
    def get_type(txt):
        for mt in ManagerType:
            if mt.value in txt:
                return mt.value
        else:
            return ManagerType.gg.value


def get_stocklist(wlist=None):
    ret = []
    url = 'http://www.cninfo.com.cn/cninfo-new/js/data/szse_stock.json'
    stockjson = get_json(url, charset='utf-8')
    if stockjson:
        stocklist = stockjson['stockList']
        for a in stocklist:
            if wlist is None or a['code'] in wlist:
                ret.append(a)
    return ret


class CNINFO(Crawler):
    """
    巨潮资讯网 www.cninfo.com.cn
    """

    def __init__(self, code, name='', orgid='', logger=None):
        Crawler.__init__(self, 'www.cninfo.com.cn', code=code, name=name, logger=logger)
        self.orgid = orgid
        return

    def get_anno(self, savepath, break_event=None, usetemp=False):
        if break_event is not None and break_event.is_set():
            return
        starttime = time.time()
        url = 'cninfo-new/announcement/query'
        pagesize = 50
        pageno = 0
        values = {'stock': self.code + ',' + self.orgid + ';',
                  'pageNum': pageno,
                  'pageSize': pagesize,
                  'tabName': 'fulltext',
                  'sortName': 'time',
                  'sortType': 'asc'}
        zfn = os.path.join(savepath, self.code + '.zip')
        zfmoved = False
        if os.path.exists(zfn):
            with zipfile.ZipFile(zfn, mode='a') as zf:
                existed = len(zf.filelist)
        else:
            existed = 0

        total = 0
        savebytes = 0
        succeed = 0
        failed = 0
        hasmore = True
        while hasmore:
            if break_event is not None and break_event.is_set():
                break
            ano = pageno * pagesize
            pageno += 1
            try:
                values['pageNum'] = pageno
                alist = self.get_json(url, values=values)
                hasmore = alist['hasMore']
                if pageno == 1:
                    total = alist['totalAnnouncement']
                    if total == 0:
                        self.logger.warning('Anno list is empty')
                        return
                    else:
                        if existed / total > 0.99:
                            self.logger.info('Anno Total %d Exists %d Skip it', total, existed)
                            return
                        elif usetemp:
                            zfn = file_copy2path(zfn, tempfile.gettempdir())
                            zfmoved = True
                            self.logger.info('Anno Total %d Exists %d copy to %s', total, existed, zfn)
                        else:
                            self.logger.info('Anno Total %d Exists %d', total, existed)
                if existed + succeed + failed >= total:
                    break
                self.logger.debug('Anno getting page %d (%d-%d/%d)', pageno,
                                  ano + 1, ano + pagesize, total)
            except Exception as e:
                self.logger.error(e)
                self.logger.error('Anno getting page %d FAIL', pageno)
                if pageno * pagesize >= total:
                    # is last page
                    return
                else:
                    continue

            with zipfile.ZipFile(zfn, mode='a') as zf:
                for ainfo in alist['announcements']:
                    if break_event is not None and break_event.is_set():
                        break
                    try:
                        ano += 1
                        asize = self.save_anno2zip(zf, ainfo)
                        if asize > 0:
                            succeed += 1
                            savebytes += asize
                            self.logger.debug('Anno %d/%d Success %d', ano, total, asize)
                    except Exception as e:
                        failed += 1
                        self.logger.error(e)
                        self.logger.error('Anno %d/%d FAIL ', ano, total)

        if usetemp and zfmoved:
            zfn = file_move2path(zfn, savepath)
            self.logger.info('Anno move to %s', zfn)

        usedtime = time.time() - starttime
        speed = savebytes / usedtime / 1024
        self.logger.info('Anno Total:%d Exists:%d Succeed:%d FAIL:%d Time used:%.3fs Speed:%.2fK/s',
                         total, existed, succeed, failed, usedtime, speed)
        return

    @staticmethod
    def get_annofilename(ainfo):
        pn, ext = os.path.splitext(ainfo['adjunctUrl'])  # 公告类型(pdf,html,js,....)
        ts = ainfo['announcementTime'] / 1000
        tm = time.strftime("%Y-%m-%d", time.localtime(ts))  # 公告日期
        # 替换文件名称中的无效字符(\/:*?"<>|)为‘_’
        fn = re.sub('[\\\/:*?"<>|]', '_', ainfo['announcementTitle']).strip()
        # 日期 [ID] 名称.类型
        fn = tm + ' [' + ainfo['announcementId'] + ']' + fn + ext
        return fn

    # return
    # >0 OK
    # =0 Exists
    # Except Fail
    def save_anno2zip(self, zf, ainfo):
        url = ainfo['adjunctUrl']
        fn = self.get_annofilename(ainfo)
        try:
            info = zf.getinfo(fn)
            if info.file_size > 0:
                return 0
        except KeyError:
            # not exists
            pass
        buf = self.get_read(url)
        if len(buf) > 0:
            zf.writestr(fn, buf, compress_type=zipfile.ZIP_DEFLATED)
            return len(buf)
        else:
            raise Exception('{} is zero'.format(url))

    def get_report(self, savepath, dbqueue=None):
        url = 'cninfo-new/data/query'
        values = {'keyWord': self.code,
                  'maxNum': '10',
                  'hq_or_cw': '2'}
        try:
            ret = self.get_json(url, values=values)
        except:
            ret = None

        if ret is None or len(ret) == 0:
            self.logger.info('无财务报表')
            return

        for bblx in ReportType:
            try:
                fn = '{}_{}.zip'.format(self.code, bblx.name)
                fn = os.path.join(savepath, fn)
                if os.path.exists(fn) and os.path.getsize(fn) > 0:
                    self.logger.info('%s Exists', bblx.value)
                    continue

                self.save_report(ret[0], bblx.name, fn)
                self.logger.info('%s Success %d', bblx.value, os.path.getsize(fn))

                if dbqueue:
                    isize = self.save_report2db(fn, bblx.name, dbqueue)
                    self.logger.info('%s Put to queue %d', bblx.value, isize)

            except Exception as e:
                self.logger.error(e)
                self.logger.error('%s FAIL', bblx.value)
        return

    @retry()
    def save_report(self, item, bbname, fn):
        url = 'cninfo-new/data/download'
        market = item['market']
        begyear = item['startTime']
        endyear = time.localtime().tm_year

        values = {'market': market,
                  'type': bbname,
                  'code': self.code,
                  'minYear': begyear,
                  'maxYear': endyear,
                  'orgid': self.orgid}
        response = self.get_response(url, values)
        info = response.info()
        if info['Content-Type'] == 'application/octet-stream':
            open(fn, mode='wb').write(response.read())
            return
        else:
            raise Exception('Unknown Content-Type:' + info['Content-Type'])

    @staticmethod
    def save_report2db(fn, bbname, dbqueue):
        cols = None
        insertedrows = 0
        sql = ''
        ops = []
        with zipfile.ZipFile(fn) as zf:
            for f in zf.filelist:
                content = zf.open(f).read().decode('gb18030')

                ishead = True
                for row in csv.reader(content.splitlines()):
                    if ishead:
                        ishead = False
                        if cols is None:
                            cols = row
                            sql = 'replace into ' + bbname + ' values(' + ','.join('?' * len(cols)) + ')'
                    else:
                        row[0] = row[0].lstrip(' \t')
                        if len(row[0]) > 0:  # code is not null
                            ops.append((sql, row))
                            insertedrows += 1

        if dbqueue:
            dbqueue.put(ops)

        return insertedrows

    def get_market(self):
        sc = self.code[0]
        if sc == '6' or sc == '9':
            return 'shmb'
        elif sc == '3':
            return 'szcn'
        elif self.code[:3] == '002':
            return 'szsme'
        else:
            return 'szmb'

    def get_brief(self, dbqueue=None):
        url = 'information/brief/' + self.get_market() + self.code + '.html'
        try:
            soup = BeautifulSoup(self.get_read(url), 'html5lib')
            div = soup.find('div', {'class': 'clear'})
            tb = div.find('table').find('tbody')
            keys = ['"机构ID"']
            vals = [self.code]
            iskey = True
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    if iskey:
                        keys.append('"{}"'.format(td.get_text(strip=True)[:-1]))
                    else:
                        vals.append(td.get_text(strip=True))
                    iskey = not iskey
            sql = 'replace into brief({}) values({})'.format(','.join(keys), ','.join('?' * len(keys)))
            if dbqueue:
                dbqueue.put([(sql, vals)])
            else:
                self.logger.debug(sql)
                self.logger.debug(vals)
            self.logger.info('公司简况 Succesed')

        except Exception as e:
            self.logger.error(e)
            self.logger.error('公司简况 FAIL')
        return


class Sina(Crawler):
    """
    新浪财经 vip.stock.finance.sina.com.cn
    """

    def __init__(self, code, name='', logger=None):
        Crawler.__init__(self, 'vip.stock.finance.sina.com.cn', code=code, name=name, logger=logger)
        return

    def get_holder2list(self, holder_type):
        if holder_type == HolderType.Top10:
            url = 'corp/go.php/vCI_StockHolder/stockid/{}.phtml'.format(self.code)
            tbid = 'Table1'
        elif holder_type == HolderType.Circular:
            url = 'corp/go.php/vCI_CirculateStockHolder/stockid/{}.phtml'.format(self.code)
            tbid = 'CirculateShareholderTable'
        else:
            return

        soup = BeautifulSoup(self.get_read(url), "html5lib")
        tb = soup.find('table', id=tbid)
        if tb is None:
            raise Exception('can''t find %s', tbid)

        rows = []
        enddate = ''
        rptdate = ''
        flag = 0

        for tr in tb.find_all('tr'):
            col = 0
            for td in tr.find_all('td'):
                col += 1
                val = ''
                for val in td.stripped_strings:
                    break
                if col == 1:
                    if val == '截至日期' or val == '截止日期':
                        flag = 1
                        for n in td.next_siblings:
                            if n.name == 'td':
                                enddate = n.get_text()
                    elif val == '公告日期':
                        flag = 2
                        for n in td.next_siblings:
                            if n.name == 'td':
                                rptdate = n.get_text()
                    elif flag == 2 and val == '编号':
                        flag = 3
                        break
                    elif flag == 3:
                        if val == '':
                            flag = 0
                            break
                        row = [enddate, rptdate]

                if flag != 3:
                    break

                if col in [1, 3]:
                    val = 0 if val == '' else int(val)
                elif col == 4:
                    val = 0 if val == '' else float(val)
                row.append(val)
                if col == 5:
                    rows.append(row)
                    break
        return rows

    def get_holder(self, dbqueue=None):
        for htype in HolderType:
            try:
                rows = self.get_holder2list(htype)
                if len(rows):
                    isize = self.save_holder(htype, rows, dbqueue)
                    self.logger.info('%s Put to queue %d', htype.value, isize)
                else:
                    self.logger.warning('%s Is zero', htype.value)
            except Exception as e:
                self.logger.error(e)
                self.logger.error('%s FAIL', htype.value)
                break
        return

    def save_holder(self, holder_type, rows, dbqueue):
        ops = []
        param = [holder_type.value, self.code]
        sql = 'delete from holder_list' \
              ' where holderID in (select holderID from holder where "股东类型" = ? and "机构ID" = ?)'
        ops.append((sql, param))
        sql = 'delete from holder where "股东类型" = ? and "机构ID" = ?'
        ops.append((sql, param))

        enddate = ''
        for row in rows:
            if enddate != row[0]:
                enddate = row[0]
                holderid = str(uuid.uuid1())
                sql = 'insert into holder values(?,?,?,?,?)'
                param = [holderid, holder_type.value, self.code, enddate, row[1]]
                ops.append((sql, param))

            sql = 'insert into holder_list values(' + ','.join('?' * 6) + ')'
            param = [holderid]
            for x in row[2:]:
                param.append(x)

            ops.append((sql, param))

        if dbqueue:
            dbqueue.put(ops)
        else:
            for op in ops:
                print(op)

        return len(ops)

    @retry()
    def get_sharebonushtml(self):
        host = 'money.finance.sina.com.cn'
        url = 'corp/go.php/vISSUE_ShareBonus/stockid/{}.phtml'.format(self.code)
        return get_read(host, url)

    def get_sharebonus(self, dbqueue=None):
        try:
            soup = BeautifulSoup(self.get_sharebonushtml(), "html5lib")
            self.save_sharebonus(dbqueue, soup, ShareBonusType.sharebonus_1)
            self.save_sharebonus(dbqueue, soup, ShareBonusType.sharebonus_2)
        except Exception as e:
            self.logger.error(e)
            self.logger.error('分红配股 Get FAIL')

        return

    def save_sharebonus(self, dbqueue, soup, sharebonus):
        try:
            tb = soup.find('table', id=sharebonus.name).find('tbody')
            maxcols = 8 if sharebonus == ShareBonusType.sharebonus_1 else 10
            rows = []
            for tr in tb.find_all('tr'):
                col = 0
                row = [self.code]
                for td in tr.find_all('td'):
                    col += 1
                    val = td.get_text(strip=True)
                    row.append(val.replace('--', ''))
                    if col == maxcols:
                        rows.append(row)
                        break

            if len(rows):
                if dbqueue:
                    ops = []
                    sql = 'replace into {} values({})'.format(sharebonus.name, ','.join('?' * (maxcols + 1)))
                    for row in rows:
                        ops.append((sql, row))
                    dbqueue.put(ops)
                    self.logger.info('%s Put to queue %d', sharebonus.value, len(rows))
                else:
                    for row in rows:
                        self.logger.debug(row)
            else:
                self.logger.warning('%s is zero', sharebonus.value)
        except Exception as e:
            self.logger.error(e)
            self.logger.error('%s FAIL', sharebonus.value)
        return

    def get_brief2(self, dbqueue=None):
        url = 'corp/go.php/vCI_CorpInfo/stockid/{}.phtml'.format(self.code)
        try:
            soup = BeautifulSoup(self.get_read(url), "html5lib")
            tb = soup.find('table', id='comInfo1').find('tbody')
            keys = ['"机构ID"']
            vals = [self.code]
            iskey = True
            for tr in tb.find_all('tr'):
                for td in tr.find_all('td'):
                    if iskey:
                        keys.append('"{}"'.format(td.get_text(strip=True)[:-1]))
                    else:
                        vals.append(td.get_text(strip=True))
                    iskey = not iskey

            sql = 'replace into brief2({}) values({})'.format(','.join(keys), ','.join('?' * len(keys)))
            if dbqueue:
                dbqueue.put([(sql, vals)])
            else:
                self.logger.debug(sql)
                self.logger.debug(vals)
            self.logger.info('公司简况2 Succesed')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('公司简况2 FAIL')

        return

    def get_manager(self, dbqueue=None):
        url = 'corp/go.php/vCI_CorpManager/stockid/{}.phtml'.format(self.code)
        try:
            soup = BeautifulSoup(self.get_read(url), "html5lib")
            ops = []
            names = []
            sql = 'replace into manager values({})'.format(','.join('?' * 7))
            for t in soup.find_all('table', id='comInfo1'):
                tb = t.find('tbody')
                ishead = True
                for tr in tb.find_all('tr'):
                    if ishead:
                        ishead = False
                        continue
                    col = 0
                    param = []
                    for td in tr.find_all('td'):
                        if 'colspan' in td.attrs:
                            break
                        col += 1
                        txt = td.get_text(strip=True)
                        if col == 1:
                            if txt in names:
                                break
                            elif self.get_person(txt, ops) > 0:
                                names.append(txt)
                                break
                            else:
                                param.append(self.code)
                        elif col == 2:
                            param.append(ManagerType.get_type(txt))
                        elif '--' == txt:
                            txt = ''
                        param.append(txt)
                    else:
                        param.append(0)
                        ops.append((sql, param))

            if len(ops):
                if dbqueue:
                    dbqueue.put(ops)
                else:
                    for op in ops:
                        print(op)
                self.logger.info('董监高 Put to queue %d', len(ops))
            else:
                self.logger.info('董监高 is zero')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('董监高 FAIL')
        return

    def get_person(self, name, mops):
        ops = []
        try:
            val = {'stockid': self.code, 'Name': name.encode('gb18030')}
            url = 'corp/view/vCI_CorpManagerInfo.php?{}'.format(urllib.parse.urlencode(val))
            soup = BeautifulSoup(self.get_read(url), "html5lib")
            div = soup.find('div', id='con02-6')

            tb = div.find('table', id='Table1').find('tbody')
            col = 0
            param = [self.code]
            for td in tb.find_all('td'):
                col += 1
                if col != 6:
                    param.append(td.get_text(strip=True))
            if '' != param[1]:
                sql = 'replace into person values({})'.format(','.join('?' * len(param)))
                ops.append((sql, param))

            tb = div.find('table', id='Table2').find('tbody')
            sql = 'replace into personstock values({})'.format(','.join('?' * 5))
            for tr in tb.find_all('tr'):
                col = 0
                param = [self.code, name]
                for td in tr.find_all('td'):
                    col += 1
                    if col in [3, 4, 5]:
                        txt = td.get_text(strip=True)
                        if col == 3:
                            txt = 0 if '' == txt else int(txt[:-1])
                        param.append(txt)
                ops.append((sql, param))

            tb = div.find('table', id='Table3').find('tbody')
            sql = 'replace into manager values({})'.format(','.join('?' * 7))
            for tr in tb.find_all('tr'):
                col = 0
                param = [self.code, name]
                for td in tr.find_all('td'):
                    col += 1
                    if col in [2, 3, 4, 5]:
                        txt = td.get_text(strip=True)
                        if col == 2:
                            param.append(ManagerType.get_type(txt))
                        elif col == 5:
                            txt = 0 if '' == txt else float(txt)
                        param.append(txt)
                ops.append((sql, param))

            mops.extend(ops)
            return len(ops)
        except Exception as e:
            self.logger.error(e)
            self.logger.error('董监高 %s FAIL', name)
            return 0


class JRJ(Crawler):
    """
    金融界 stock.jrj.com.cn
    """

    def __init__(self, code, name='', logger=None):
        Crawler.__init__(self, 'stock.jrj.com.cn', code=code, name=name, logger=logger)
        return

    def get_lift_ban(self, dbqueue=None):
        url = 'action/xsjj/getXsjjInfoListByStockcode.jspa?stockcode={}'.format(self.code)
        try:
            data = json.loads(self.get_read(url)[len('var xsjjInfo='):-1])
            rows = []
            for d in data:
                for row in d['infoList']:
                    param = [self.code]
                    if 'holder_name' in row:
                        param.append(row['holder_name'])
                    else:
                        param.append('未知')
                    param.append(row['tradedate'][:10])
                    param.append(row['ref_name'])
                    param.append(row['unltd_vol'])
                    param.append(row['ifActLock'])
                    if 'lock_cond_prm' in row:
                        param.append(row['lock_cond_prm'])
                    else:
                        param.append('')
                    rows.append(param)

            if len(rows):
                sql = 'replace into lift_ban values({})'.format(','.join('?' * len(rows[0])))
                ops = []
                for param in rows:
                    ops.append((sql, param))
                if dbqueue:
                    dbqueue.put(ops)
                    self.logger.info('限售解禁 Put to queue %d', len(rows))
                else:
                    for row in ops:
                        print(row)
            else:
                self.logger.info('限售解禁 is zero')
        except Exception as e:
            self.logger.error(e)
            self.logger.error('限售解禁 FAIL')
        return


if __name__ == '__main__':
    # Sina('000001').get_manager()
    for stock in get_stocklist(['300188']):
        # print(stock)
        CNINFO(stock['code'], stock['zwjc'], stock['orgId']).get_brief('Anno')
        #     # JRJ(stock['code']).get_lift_ban()
        #     Sina(stock['code']).get_manamge()
