# -*- coding: utf-8 -*-
"""
Created on 2017-05-09

@author: hy_qiu
"""

import sqlite3
import logging
import os


class DB:
    def __init__(self, dbname):
        self.chkdb(dbname)
        self.dbname = dbname

        pn, fn = os.path.split(self.dbname)
        self.logger = logging.getLogger(fn)
        fn = os.path.splitext(fn)[0]
        self.logger.setLevel(logging.DEBUG)
        fn = os.path.join(pn, fn + '.log')
        fh = logging.FileHandler(fn, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        return

    @staticmethod
    def chkdb(dbname):
        if not os.path.exists(dbname):
            pn, dn = os.path.split(dbname)
            dn, ext = os.path.splitext(dn)
            with open(os.path.join(pn, dn + '.sql'), 'rt', encoding='utf-8') as sf:
                sql = sf.read()
            with sqlite3.connect(dbname) as con:
                con.executescript(sql)
                con.commit()
                print('Create DB {} Succeed'.format(dbname))
        return True

    def runwithqueue(self, queue):
        with sqlite3.connect(self.dbname) as con:
            self.logger.info('DB %s Opened', self.dbname)
            while True:
                ops = queue.get()
                if ops is None:
                    break

                self.do_oplist(con, ops)
                queue.task_done()
        self.logger.info('DB %s Closed', self.dbname)

    def do_oplist(self, con, ops):
        rows = 0
        op = None
        try:
            if isinstance(ops, list):
                for op in ops:
                    if self.do_op(con, op):
                        rows += 1
            elif isinstance(ops, tuple):
                op = ops
                if self.do_op(con, op):
                    rows += 1
            con.commit()
            self.logger.debug('commit:%d', rows)
        except Exception as e:
            self.logger.error(e)
            if op:
                self.logger.error(op)
            con.rollback()
            self.logger.error('rollback')

    @staticmethod
    def do_op(con, op):
        param = None
        if isinstance(op, str):
            sql = op
        elif isinstance(op, tuple):
            sql = op[0]
            if len(op) > 1:
                param = op[1]
        else:
            return False
        if param:
            con.execute(sql, param)
        else:
            con.executescript(sql)
        return True
