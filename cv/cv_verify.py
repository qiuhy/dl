# -*- coding: utf-8 -*-
"""
Created on 17-8-1

@author: hy_qiu
"""
import base64
import random
import time

import cv2
import numpy
import requests

MAIN_WINDOW_NAME = 'verify'
value1 = 4
max_value2 = 18 #最大旋转角度，10的倍数
value2 = max_value2 // 2  #起始角度，90
value3 = 2

curidx = 0
#RGB Format
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 255, 0)]


class Align:
    def __init__(self, align='cc'):
        self.halign = align[0].lower()
        self.valign = align[1].lower()
        if self.halign not in 'lcr':
            self.halign = 'c'
        if self.valign not in 'tcb':
            self.valign = 'c'

    def get_topleft(self, box, size):
        (bx, by, bw, bh) = box
        (sw, sh) = size
        x = y = 0
        if self.halign == 'l':
            x = bx
        elif self.halign == 'c':
            x = bx + int((bw - sw) / 2 + 0.5)
        elif self.halign == 'r':
            x = bx + bw - sw

        if self.valign == 't':
            y = by
        elif self.valign == 'c':
            y = by + int((bh - sh) / 2 + 0.5)
        elif self.valign == 'b':
            y = by + bh - sh

        return x, y

    def get_bottomleft(self, box, size):
        x, y = self.get_topleft(box, size)
        y += size[1]
        return x, y


def get_feature(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = numpy.float32(gray)
    dst = cv2.cornerHarris(gray, 2, 3, 0.04)
    img[dst > 0.01 * dst.max()] = [0, 0, 255]
    return img

    # dst = cv2.goodFeaturesToTrack(gray, 200, 0.01, 2)
    # for n in dst:
    #     pos = n[0]
    #     img[int(pos[1]), int(pos[0])] = [0, 0, 255]

    # dst = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2. THRESH_BINARY_INV, 5, 0)
    # # img[dst > 0.01 * dst.max()] = [0, 0, 255]
    # img = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)
    # return img


def get_tgimg(img):
    """
    处理提示图片，提取提示字符
    :param img: 提示图片
    :type img:
    :return: 返回原图描边，提示图片按顺序用不同颜色框,字符特征图片列表
    :rtype: img 原图, out 特征图片列表（每个字）, templets 角度变换后的图
    """
    imgBW = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = imgBW.shape
    _, imgBW = cv2.threshold(imgBW, 0, 255,
                             cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    img2 = cv2.erode(imgBW, None, iterations=3)
    img2 = cv2.dilate(img2, None, iterations=3)
    out = numpy.full((20 + h, 20 + w), 255, numpy.uint8)
    copy_image(out, 10, 10, img2)
    out, cnts, hierarchy = cv2.findContours(out, cv2.RETR_LIST,
                                            cv2.CHAIN_APPROX_NONE)
    rects = []
    # cnts[-1]  边框
    for cnt in cnts[:-1]:
        cnt -= 10
        x1 = cnt[:, :, 0].min()
        y1 = cnt[:, :, 1].min()
        x2 = cnt[:, :, 0].max()
        y2 = cnt[:, :, 1].max()

        x1 = 0 if x1 < 0 else x1
        y1 = 0 if y1 < 0 else y1
        x2 = w - 1 if x2 > w - 1 else x2
        y2 = h - 1 if y2 > h - 1 else y2
        rects.append((x1, y1, x2, y2))
        cv2.drawContours(img, cnt, -1, [0, 0, 255])
        # cv2.rectangle(img, (x1, y1), (x2, y2), [0, 0, 255])
    rects.sort()

    out = numpy.full(imgBW.shape, 255, numpy.uint8)
    x0 = spacing = 3
    templets = []
    for x1, y1, x2, y2 in rects:
        imgchar = numpy.full((30, 30), 255, numpy.uint8)
        tmpl = imgBW[y1:y2 + 1, x1:x2 + 1]
        if value2 != (max_value2 // 2):
            tmpl = rotate_image(tmpl, (max_value2 // 2 - value2) * 10)
        templets.append(tmpl)
        copy_image(imgchar, 0, (30 - y2 + y1 - 1) // 2, tmpl)
        copy_image(out, x0, 0, imgchar)
        x0 += x2 - x1 + 1 + spacing

    out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    i = 0
    x0 = spacing
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(out, (x0, 0), (x0 + x2 - x1 + 1, 29), COLORS[i])
        x0 += x2 - x1 + 1 + spacing
        i += 1
    return img, out, templets


def get_bgimg(img, templets):
    """
    处理背景图
    :param img:
    :type img: ndarray
    :param templets: 实例图片列表
    :type templets: list
    :return: 处理后背景图，匹配区域用响应颜色框，四种匹配方式对应4个不同位置提示
            1minLoc 2maxLoc 正常的匹配结果
            3minLoc 4maxLoc 反转后匹配结果
    :rtype:
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if value3 == 0:
        ret, dst = cv2.threshold(gray, 0, 255,
                                 cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
    elif value3 == 1:
        ret, dst = cv2.threshold(gray, 0, 255,
                                 cv2.THRESH_BINARY_INV + cv2.THRESH_TRIANGLE)
    elif value3 == 2:
        ret, dst = cv2.threshold(gray, 0, 255,
                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        ret, dst = cv2.threshold(gray, 0, 255,
                                 cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    methods = (cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED, cv2.TM_CCORR,
               cv2.TM_CCORR_NORMED, cv2.TM_CCOEFF, cv2.TM_CCOEFF_NORMED)

    dst2 = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)
    matchs = []
    for t in templets:
        method = methods[value1 % len(methods)]
        match = []

        result = cv2.matchTemplate(dst, t, method)
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
        match.append((minLoc, t.shape))
        match.append((maxLoc, t.shape))

        t ^= 255
        result = cv2.matchTemplate(dst, t, method)
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
        match.append((minLoc, t.shape))
        match.append((maxLoc, t.shape))

        matchs.append(match)

    i = 0
    for m in matchs:
        no = 0
        for (x, y), (w, h) in m:
            no += 1
            cv2.rectangle(dst2, (x, y), (x + w, y + h), COLORS[i])
            if no == 1:
                align = 'lt'
            elif no == 2:
                align = 'rt'
            elif no == 3:
                align = 'lb'
            elif no == 4:
                align = 'rb'
            else:
                align = 'cc'

            # 1minLoc 2maxLoc
            # 3minLoc 4maxLoc 反转后匹配结果
            put_text(dst2, 'x', (x, y, w, h), COLORS[i], align)
        i += 1
    return dst2


def rotate_image(img, angle):
    # 以图片中学为原点，逆时针旋转
    # angle 旋转角度（度） 正值表示逆时针旋转
    # getRotationMatrix2D(center, angle, scale) → retval
    # cv2.warpAffine(src, M, dsize[, dst[, flags[, borderMode[, borderValue]]]]) → dst
    ssize = img.shape
    center = (ssize[0] / 2, ssize[1] / 2)
    m = cv2.getRotationMatrix2D(center, angle, scale=1)
    dst = cv2.warpAffine(img, m, ssize, borderValue=(255, 255, 255))
    return dst


def put_text(img, text, box, color, align='cc'):
    font_face = cv2.FONT_HERSHEY_PLAIN
    font_scale = 1
    thickness = 1
    retval, baseline = cv2.getTextSize(text, font_face, font_scale, thickness)
    x, y = Align(align).get_bottomleft(box, retval)
    # y -= baseline
    y -= thickness
    cv2.putText(img, text, (x, y), font_face, font_scale, color, thickness)


def get_edges(img):
    threshold = 1
    edges = cv2.Canny(img, 100, 200)
    img[edges > 0] = [0, 0, 255]
    return img


def get_grbcut(img):
    bgdmodel = numpy.zeros((1, 65), numpy.float64)
    fgdmodel = numpy.zeros((1, 65), numpy.float64)
    mask = numpy.zeros(img.shape[:2], dtype=numpy.uint8)
    rect = (0, 0, img.shape[0], img.shape[1])
    cv2.grabCut(img, mask, rect, bgdmodel, fgdmodel, 1, cv2.GC_INIT_WITH_RECT)
    # cv2.grabCut(img, mask, rect, bgdmodel, fgdmodel, 1, cv2.GC_INIT_WITH_MASK)
    mask2 = numpy.where((mask == 1) | (mask == 3), 255, 0).astype('uint8')
    output = cv2.bitwise_and(img, img, mask=mask2)
    return output


def get_sobel(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    x = cv2.Sobel(gray, -1, 0, 1, 3)
    y = cv2.Sobel(gray, -1, 1, 0, 3)
    output = cv2.addWeighted(x, 0.5, y, 0.5, 0)
    return cv2.cvtColor(output, cv2.COLOR_GRAY2BGR)


def get_watershed(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, dst = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # noise removal
    kernel = numpy.ones((3, 3), numpy.uint8)
    opening = cv2.morphologyEx(dst, cv2.MORPH_OPEN, kernel, iterations=2)
    # sure background area
    sure_bg = cv2.dilate(opening, kernel, iterations=3)
    # Finding sure foreground area
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    ret, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(),
                                 255, 0)
    # Finding unknown region
    sure_fg = numpy.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)
    # Marker labelling
    ret, markers = cv2.connectedComponents(sure_fg)
    # Add one to all labels so that sure background is not 0, but 1
    markers = markers + 1
    # Now, mark the region of unknown with zero
    markers[unknown == 255] = 0
    markers = cv2.watershed(img, markers)
    img[markers == -1] = [0, 0, 255]
    return img


def get_threshold(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, dst = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)

    # dst = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)
    # dst = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 0)
    # return cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)


def get_img(idx, fromlocal=True):
    if fromlocal:
        imgpath = 'e:/tyc2/verify'
        bgimg = cv2.imread(imgpath + '/bg{:04d}.png'.format(idx),
                           cv2.IMREAD_ANYCOLOR)
        tgimg = cv2.imread(imgpath + '/tg{:04d}.png'.format(idx),
                           cv2.IMREAD_ANYCOLOR)
    else:
        url = 'http://antirobot.tianyancha.com/captcha/getCaptcha.json?t={}'.format(
            int(time.time() * 1000))
        resp = requests.get(url).json()
        data = resp['data']
        bg = base64.standard_b64decode(data['bgImage'])
        tg = base64.standard_b64decode(data['targetImage'])
        nparr = numpy.frombuffer(bg, numpy.uint8)
        bgimg = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)

        nparr = numpy.frombuffer(tg, numpy.uint8)
        tgimg = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    return bgimg, tgimg


def copy_image(dst, x, y, src):
    h, w = src.shape[:2]
    numpy.copyto(dst[y:y + h, x:x + w], src)


def on_change1(pos, userdata=None):
    global value1
    value1 = pos
    on_draw()
    pass


def on_change2(pos, userdata=None):
    global value2
    value2 = pos
    on_draw()
    pass


def on_change3(pos, userdata=None):
    global value3
    value3 = pos
    on_draw()
    pass


def on_draw():
    bkimg = numpy.full((270, 340, 3), 255, numpy.uint8)
    bgimg, tgimg = get_img(curidx)
    tgimg, tgimg2, templets = get_tgimg(tgimg)
    bgimg2 = get_bgimg(bgimg, templets)
    copy_image(bkimg, 10, 10, bgimg)
    copy_image(bkimg, 10, 120, bgimg2)
    copy_image(bkimg, 10, 230, tgimg)
    copy_image(bkimg, 140, 230, tgimg2)
    show_image(bkimg, MAIN_WINDOW_NAME)


def show_image(img, title='debug'):
    cv2.namedWindow(title, cv2.WINDOW_KEEPRATIO)
    cv2.imshow(title, img)


def cv2test():
    global curidx, value1
    cv2.namedWindow(MAIN_WINDOW_NAME, cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(MAIN_WINDOW_NAME, 340, 370)
    cv2.setWindowTitle(MAIN_WINDOW_NAME, 'verify')
    cv2.createTrackbar('match', MAIN_WINDOW_NAME, value1, 5, on_change1)
    cv2.createTrackbar('angle', MAIN_WINDOW_NAME, value2, max_value2,
                       on_change2)
    cv2.createTrackbar('threshold', MAIN_WINDOW_NAME, value3, 3, on_change3)
    history = []
    curidx = 118
    history.append(curidx)
    while True:
        cv2.setWindowTitle(MAIN_WINDOW_NAME, 'verify {}'.format(curidx))
        on_draw()
        key = cv2.waitKeyEx()
        if key in (0x20, ):  # Spacce
            value1 += 1
            value1 %= 6
            cv2.setTrackbarPos('match', MAIN_WINDOW_NAME, value1)
        elif key in (0x270000, 0x0d):  # Right, Enter
            curidx = random.randint(1, 338)
            history.append(curidx)
            if len(history) > 100:
                history.pop(0)
        elif key in (0x250000, 8):  # Left,Backspace
            if len(history):
                curidx = history.pop()
        elif key in (27, -1):  # Esc CloseAllWindow
            cv2.destroyAllWindows()
            break
        else:
            print(hex(key))


if __name__ == '__main__':
    cv2test()
