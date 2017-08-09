# -*- coding: utf-8 -*-


import logging.config
import multiprocessing.dummy as mt
import signal
import threading
from enum import Enum

import cnstock as cn
import hkstock as hk
import stockdb

BREAK_EVENT = mt.Event()
THREAD_LOCK = mt.Lock()
THREAD_NO = mt.Value('i', 0)
DBQUEUE = mt.Queue()
PARAMS = []

SAVEPATH = 'e:/stock/'


class StockInfoType(Enum):
    Anno = 'a'
    Brief = 'b'
    fin = 'f'
    Holder = 'h'
    Sharebonus = 's'
    Lift_ban = 'j'
    Manager = 'm'
    History = 'p'


def get_cn_stockinfo(stock):
    if BREAK_EVENT.is_set():
        return

    with THREAD_LOCK:
        THREAD_NO.value += 1
        tno = THREAD_NO.value

    code = stock['code']
    name = stock['zwjc']
    orgid = stock['orgId']
    tna = '#{}@{:9s}'.format(tno, mt.current_process().name)

    logger = logging.getLogger(code)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log/cn' + code + '.log', mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(name)s-%(levelname)-8s %(message)s')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('%s %s', code, name)

    try:
        logger.info('%s %s Start', tna, code)

        for p in PARAMS:
            if BREAK_EVENT.is_set():
                logger.info('%s %s Break!', tna, code)
                return
            elif p == StockInfoType.Anno:
                cn.CNINFO(code, name, orgid, logger).get_anno(SAVEPATH + 'CNAnno', BREAK_EVENT)
            elif p == StockInfoType.Brief:
                cn.CNINFO(code, name, orgid, logger).get_brief(DBQUEUE)
                cn.Sina(code, name, logger).get_brief2(DBQUEUE)
            elif p == StockInfoType.fin:
                cn.CNINFO(code, name, orgid, logger).get_report(SAVEPATH + 'CNReport', DBQUEUE)
            elif p == StockInfoType.Holder:
                cn.Sina(code, name, logger).get_holder(DBQUEUE)
            elif p == StockInfoType.Sharebonus:
                cn.Sina(code, name, logger).get_sharebonus(DBQUEUE)
            elif p == StockInfoType.Lift_ban:
                cn.JRJ(code, name, logger).get_lift_ban(DBQUEUE)
            elif p == StockInfoType.Manager:
                cn.Sina(code, name, logger).get_manager(DBQUEUE)
            elif p == StockInfoType.History:
                cn.NetEase(code, name, logger).get_historydata(SAVEPATH + 'History')
        logger.info('%s %s Done!', tna, code)
    except Exception as e:
        logger.error(e)


def get_cn_stock(logger):
    stocklist = cn.get_stocklist()
    logger.info('Stock count: %d', len(stocklist))

    pool = mt.Pool(20)
    result = pool.map_async(get_cn_stockinfo, stocklist)
    while not result.ready():
        BREAK_EVENT.wait(1)
        if BREAK_EVENT.is_set():
            pool.close()
            pool.join()
            logger.info('Break!')
            break


def get_3b_stockinfo(stock):
    if BREAK_EVENT.is_set():
        return

    with THREAD_LOCK:
        THREAD_NO.value += 1
        tno = THREAD_NO.value

    code = stock['code']
    name = stock['name']
    orgid = ''
    tna = '#{}@{:9s}'.format(tno, mt.current_process().name)

    logger = logging.getLogger(code)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log/3b' + code + '.log', mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(name)s-%(levelname)-8s %(message)s')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('%s %s', code, name)

    try:
        logger.info('%s %s Start', tna, code)

        for p in PARAMS:
            if BREAK_EVENT.is_set():
                logger.info('%s %s Break!', tna, code)
                return
            elif p == StockInfoType.Anno:
                cn.CNINFO(code, name, orgid, logger).get_3b_anno(SAVEPATH + '3BAnno', BREAK_EVENT)
            elif p == StockInfoType.Brief:
                # cn.CNINFO(code, name, orgid, logger).get_brief(DBQUEUE)
                cn.ChinaIPO(code, name, logger).get_3b_brief(DBQUEUE)
            # elif p == StockInfoType.fin:
            #     cn.CNINFO(code, name, orgid, logger).get_report(SAVEPATH + 'CNReport', DBQUEUE)
            elif p == StockInfoType.Holder:
                cn.ChinaIPO(code, name, logger).get_3b_holder(DBQUEUE)
            # elif p == StockInfoType.Sharebonus:
            #     cn.Sina(code, name, logger).get_sharebonus(DBQUEUE)
            # elif p == StockInfoType.Lift_ban:
            #     cn.JRJ(code, name, logger).get_lift_ban(DBQUEUE)
            elif p == StockInfoType.Manager:
                cn.ChinaIPO(code, name, logger).get_3b_manager(DBQUEUE)
            # elif p == StockInfoType.History:
            #     cn.NetEase(code, name, logger).get_historydata(SAVEPATH + 'History')
        logger.info('%s %s Done!', tna, code)
    except Exception as e:
        logger.error(e)


def get_3b_stock(logger):
    stocklist = cn.get_3b_stocklist()
    logger.info('Stock count: %d', len(stocklist))

    pool = mt.Pool(20)
    result = pool.map_async(get_3b_stockinfo, stocklist)
    while not result.ready():
        BREAK_EVENT.wait(1)
        if BREAK_EVENT.is_set():
            pool.close()
            pool.join()
            logger.info('Break!')
            break


def get_hk_stockinfo(stock):
    if BREAK_EVENT.is_set():
        return

    with THREAD_LOCK:
        THREAD_NO.value += 1
        tno = THREAD_NO.value

    code = stock[0]
    name = stock[1]
    tna = '#{}@{:9s}'.format(tno, mt.current_process().name)

    logger = logging.getLogger(code)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log/hk' + code + '.log', mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(name)s-%(levelname)-8s %(message)s')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('%s %s', code, name)

    try:
        logger.info('%s %s Start', tna, code)

        for p in PARAMS:
            if BREAK_EVENT.is_set():
                logger.info('%s %s Break!', tna, code)
                return
            elif p == StockInfoType.Anno:
                hk.HKStock(code, name, logger).get_anno(SAVEPATH + 'HKAnno', BREAK_EVENT)
            elif p == StockInfoType.Brief:
                hk.HKStock(code, name, logger).get_brief(DBQUEUE)
            elif p == StockInfoType.fin:
                hk.HKStock(code, name, logger).get_report(SAVEPATH + 'HKReport', DBQUEUE)
                # elif p == StockInfoType.Holder:
                #     cn.Sina(code, name, logger).get_holder(DBQUEUE)
                # elif p == StockInfoType.Sharebonus:
                #     cn.Sina(code, name, logger).get_sharebonus(DBQUEUE)
                # elif p == StockInfoType.Lift_ban:
                #     cn.JRJ(code, name, logger).get_lift_ban(DBQUEUE)
                # elif p == StockInfoType.Manager:
                #     cn.Sina(code, name, logger).get_manager(DBQUEUE)

        logger.info('%s %s Done!', tna, code)
    except Exception as e:
        logger.error(e)


def get_hk_stock(logger):
    if StockInfoType.Brief in PARAMS:
        logger.info('AH Stock: %d', hk.get_ah(DBQUEUE))

    hkthread = None
    if StockInfoType.Manager in PARAMS:
        hkthread = threading.Thread(target=hk.get_manager, args=(logger, DBQUEUE,))
        hkthread.start()
        logger.info('HK Manager Start')

    if StockInfoType.Anno in PARAMS or StockInfoType.Brief in PARAMS or StockInfoType.fin in PARAMS:
        stocklist = hk.get_stocklist()
        logger.info('HK Stock: %d', len(stocklist))
        pool = mt.Pool(20)
        result = pool.map_async(get_hk_stockinfo, stocklist)
        while not result.ready():
            BREAK_EVENT.wait(1)
            if BREAK_EVENT.is_set():
                logger.warning('RECV BREAK SIGNAL!!!')
                pool.close()
                pool.join()
                logger.info('Break!')
                break

    if hkthread:
        hkthread.join()


def on_break(s, f):
    BREAK_EVENT.set()


def get_stock(market):
    signal.signal(signal.SIGTERM, on_break)
    signal.signal(signal.SIGINT, on_break)

    logging.config.fileConfig("logging.conf")
    logger = logging.getLogger()
    logger.info('%s Beginning', market)

    dbname = 'db/{}stock.db'.format(market)
    dbthread = threading.Thread(target=stockdb.DB(dbname).runwithqueue, args=(DBQUEUE,))
    dbthread.start()
    if market == 'cn':
        get_cn_stock(logger)
    elif market == 'hk':
        get_hk_stock(logger)
    elif market == '3b':
        get_3b_stock(logger)
    elif market == 'us':
        pass
    DBQUEUE.put(None)
    dbthread.join()
    logger.info('%s Done!', market)


def main(argv):
    try:
        market = ''
        for arg in argv:
            arg = arg.lower()
            if arg.startswith('-m:'):
                market = arg[3:]
                if market not in ('cn', 'hk', '3b', 'us'):
                    raise Exception('')
            elif arg.startswith('-i:'):
                for c in arg[3:]:
                    p = StockInfoType(c)
                    if p not in PARAMS:
                        PARAMS.append(p)
        if market == '' or len(PARAMS) == 0:
            raise Exception('unknow usage')
        get_stock(market)
    except:
        usage = 'usage:{} -m:[market] -i:[info]\nmarket:[cn, hk, 3b, us]\ninfo:[{}]\n{}'
        print(usage.format(__file__, ''.join([x.value for x in StockInfoType]),
                           '\n'.join(['\t' + x.value + ':' + x.name for x in StockInfoType])))


if __name__ == '__main__':
    import sys

    main(sys.argv[1:])
