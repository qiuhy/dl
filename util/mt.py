# -*- coding: utf-8 -*-
"""
Created on 2017-06-08

@author: hy_qiu
"""
import signal
import logging
import itertools
import multiprocessing.dummy as mt

BREAK_EVENT = mt.Event()


def on_break(s, f):
    BREAK_EVENT.set()
    logging.getLogger('mt').warning('RECV BREAK SIGNAL {}!!!'.format(s))


def run2pool(fun, *argv, poolsize=10):
    signal.signal(signal.SIGTERM, on_break)
    signal.signal(signal.SIGINT, on_break)

    args = zip(*(a if hasattr(a, '__iter__') and not isinstance(a, str)
                 else itertools.repeat(a)
                 for a in argv))

    pool = mt.Pool(poolsize)
    ret = pool.starmap_async(fun, args)

    while not ret.ready():
        BREAK_EVENT.wait(1)
        if BREAK_EVENT.is_set():
            pool.terminate()
            pool.join()
            break

    return not BREAK_EVENT.is_set()
