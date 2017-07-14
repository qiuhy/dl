# -*- coding: utf-8 -*-
"""
Created on 2017-06-07

@author: hy_qiu
"""

import requests
import time
import os
import zipfile
from bs4 import BeautifulSoup
from util.wraps import retry
import util.mt as mt
from util.loginit import get_logger

PATH = ''

logger = get_logger()


def get_dates():
    logger.info('get_dates Start')
    now = time.localtime()
    year = now.tm_year
    month = now.tm_mon
    dates = []
    url = 'http://epaper.21jingji.com/html/{}-{:02d}/period.xml'
    while True:
        try:
            root = get_soup(url.format(year, month))
        except:
            break
        for period in root.find_all('period'):
            period_date = period.find('period_date')
            dates.append(period_date.get_text().split('-'))

        month -= 1
        if month == 0:
            year -= 1
            month = 12
    logger.info('get_dates {}'.format(len(dates)))
    return dates


def get_paper(date):
    path = os.path.join(PATH, date[0])
    try:
        if not os.path.exists(path):
            os.mkdir(path)
    except:
        pass
    logger.info('{} Start'.format('-'.join(date)))
    try:
        zfn = os.path.join(path, '-'.join(date) + '.zip')
        url = 'http://epaper.21jingji.com/html/{}-{}/{}/node_1.htm'.format(date[0], date[1], date[2])
        soup = get_soup(url)
        news_list = soup.find('div', {'class': 'news_list'})
        news_count = 0
        news_fail = 0
        with zipfile.ZipFile(zfn, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            for ul in news_list.find_all('ul'):
                for li in ul.find_all('li'):
                    # if breakevent.is_set():
                    #     logger.info('{} Break'.format('-'.join(date)))
                    #     return
                    a = li.find('a')
                    if a:
                        fn = a.get('href')[:-4] + '.txt'

                        if a.get_text(strip=True) == '广告':
                            continue
                        news_count += 1
                        try:
                            info = zf.getinfo(fn)
                            if info.file_size > 0:
                                continue
                        except KeyError:
                            # not exists
                            pass
                        try:
                            zf.writestr(fn, get_news(a.get('href'), date))
                        except Exception as e:
                            logger.error(e)
                            logger.error('{} {} Fail'.format('-'.join(date), a.get('href')))
                            news_fail += 1
        if news_fail:
            logger.info('{} Fail:{}/{}'.format('-'.join(date), news_fail, news_count))
        else:
            logger.info('{} Done {}'.format('-'.join(date), news_count))
    except Exception as e:
        logger.error(e)
        logger.error('{} FAIL'.format('-'.join(date)))


def get_news(href, date):
    url = 'http://epaper.21jingji.com/html/{date[0]}-{date[1]}/{date[2]}/{href}'.format(date=date, href=href)
    soup = get_soup(url)
    cont = soup.find('div', {'class': 'news_content'})
    news = ''
    for title in cont.find_all('h1'):
        t = title.get_text(strip=True)
        if t != '':
            news += t + '\n'
    for p in cont.find_all('p'):
        news += p.get_text() + '\n'
    return news


@retry()
def get_soup(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html5lib")


def chk_argv(argv):
    global PATH
    try:
        PATH = argv[1]
        if PATH == '':
            return False

        if not os.path.exists(PATH):
            os.mkdir(PATH)
        return True
    except:
        return False


def get_all():
    dates = get_dates()
    if mt.run2pool(get_paper, dates):
        logger.info('Done!')


if __name__ == '__main__':
    import sys

    if chk_argv(sys.argv):
        get_all()
        # get_paper('2017-06-02'.split('-'))
    else:
        print('usage 21jj.py [path]')
