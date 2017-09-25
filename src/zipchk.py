# -*- coding: utf-8 -*-
"""
Created on 2017-04-28

@author: hy_qiu
"""
import zipfile
import os


def chk_zipfile(fn):
    zerofile = 0
    dupfile = 0  # duplicate file
    fnlist = []
    if not os.path.exists(fn):
        print('{} no such file'.format(fn))
        return False
    try:
        with zipfile.ZipFile(fn) as zf:
            if len(zf.filelist) == 0:
                return True
            for fi in zf.filelist:
                if fi.file_size == 0:
                    zerofile += 1
                    print('{}->{} is zero file'.format(fn, fi.filename))
                elif fi.filename in fnlist:
                    dupfile += 1
                    print('{}->{} is duplicate'.format(fn, fi.filename))
                else:
                    fnlist.append(fi.filename)
        if dupfile:
            print(fn, ' duplicate files', dupfile)
        if zerofile:
            print(fn, ' zero files', zerofile)
        return zerofile == 0 and dupfile == 0
    except Exception as e:
        print(fn, e)
        os.remove(fn)
        print(fn, 'removed')
        return False


def chk_all(path, code):
    ret = True
    pn = os.path.join(path, code)
    for entry in os.scandir(pn):
        if entry.is_file() and entry.name.endswith('.zip'):
            if not chk_zipfile(entry.path):
                ret = False
    return ret


def chkpath(path):
    ok = 0
    fail = 0
    for entry in os.scandir(path):
        if entry.is_dir() and entry.name.isnumeric():
            code = entry.name
            if chk_all(path, code):
                ok += 1
            else:
                fail += 1
                print(code, 'Fail')
            if ok % 100 == 0:
                print('checked ok:', ok)
    print('Total:{} OK:{} Fail:{}'.format(ok + fail, ok, fail))


if __name__ == '__main__':
    chkpath('g:/info/')
