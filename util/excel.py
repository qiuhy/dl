# -*- coding: utf-8 -*-
"""
Created on 17-7-28

@author: hy_qiu
"""

import xlrd


def read_excel(fn, sheetindex=0, startrow=0):
    wb = xlrd.open_workbook(fn)
    sheet = wb.sheet_by_index(sheetindex)
    for i in range(sheet.nrows):
        if i < startrow:
            continue
        yield i, sheet.row(i)
