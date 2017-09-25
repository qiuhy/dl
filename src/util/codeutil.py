# -*- coding: utf-8 -*-
"""
Created on 2017-05-24

@author: hy_qiu
"""

# from  Crypto.Cipher import AES

# 统一社会信用代码 RegCode = 1位登记管理部门代码+ 1位机构类别代码 + 6位行政区划码 + 9位组织机构代码 + 1位校验码
# 组织结构代码 OrgCode = 8位代码(0-9,A-Z) + 1位校验码
# 税务登记号码 TexCode = 6位行政区划码 + 9位组织机构代码


def chk_regcode(regcode):
    # 验证统一社会信用代码
    if chk_orgcode(regcode[8:-1]):
        return regcode[-1] == get_regcheck(regcode[:-1])
    else:
        return False


def get_regcheck(regcode):
    weight = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]
    ch = '0123456789ABCDEFGHJKLMNPQRTUWXY'

    if len(regcode) != 17:
        return
    csum = 0
    for i in range(17):
        c = regcode[i].upper()
        ci = ch.find(c)
        if ci < 0:
            return
        csum += ci * weight[i]

    c18 = 31 - csum % 31
    return ch[c18]


def chk_orgcode(orgcode):
    # 验证组织结构代码
    return orgcode[-1] == get_orgcheck(orgcode[:-1])


def get_orgcheck(orgcode):
    weight = [3, 7, 9, 10, 5, 8, 4, 2]
    # 计算组织结构代码的校验码(第九位)

    if len(orgcode) != 8:
        return

    csum = 0
    for i in range(8):
        ci = ord(orgcode[i].upper())
        if 48 <= ci <= 57:  # 0-9 0-9
            ci -= ord('0')
        elif 65 <= ci <= 90:  # A-Z 10-35
            ci -= ord('A') - 10
        else:
            return
        csum += ci * weight[i]
    c9 = 11 - csum % 11
    if c9 == 10:
        return 'X'
    elif c9 == 11:
        return '0'
    else:
        return str(c9)


if __name__ == '__main__':
    # print(get_orgcheck('63378833'))
    # print(chk_orgcode('633788336'))
    # print(get_regcheck('91110000000000000'))
    # print(chk_regcode('91320213586657279T'))
    pass