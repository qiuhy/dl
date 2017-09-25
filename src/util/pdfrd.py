# -*- coding: utf-8 -*-
"""
Created on 17-8-10

@author: hy_qiu
"""
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.layout import *
from pdfminer.converter import PDFPageAggregator
import cv2
import numpy
from PIL import Image, ImageDraw, ImageFont
import io
from collections import Iterable

DPI = 96 / 72


class PdfMinerWrapper(object):
    """
    Usage:
    with PdfMinerWrapper('2009t.pdf') as doc:
        for page in doc:
           #do something with the page
    """

    def __init__(self, pdf_doc, pdf_pwd=''):
        self.pdf_doc = pdf_doc
        self.pdf_pwd = pdf_pwd

    def __enter__(self):
        # open the pdf file
        self.fp = open(self.pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(self.fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument()
        # connect the parser and document objects
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize(self.pdf_pwd)
        self.doc = doc
        return self

    def _parse_pages(self):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(all_texts=True)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in self.doc.get_pages():
            interpreter.process_page(page)
            # receive the LTPage object for this page
            layout = device.get_result()
            # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
            if isinstance(layout, LTPage):
                yield layout

    def __iter__(self):
        return iter(self._parse_pages())

    def __exit__(self, _type, value, traceback):
        self.fp.close()

    def get_items(self, page, level=0, toprint=False):
        if toprint:
            print('{} + {} '.format(' ' * (level * 2), page))
        for item in page:
            if isinstance(item, Iterable) and not isinstance(item, LTTextLine):
                for child in self.get_items(item, level=level + 1, toprint=toprint):
                    yield child
            else:
                if not isinstance(item, LTAnon):
                    if toprint:
                        r = Rect(item.bbox, round(page.height * DPI))
                        print('{} . {} {}'.format(' ' * ((level + 1) * 2), item, r))
                    yield item


class Segment:
    def __init__(self, beg, end):
        if beg > end:
            raise Exception('beg cannot be greater than end')
        self.beg = beg
        self.end = end

    def __repr__(self):
        return '({},{})'.format(self.beg, self.end)

    def merge(self, seg):
        if seg.end < self.beg - 1 or seg.beg > self.end + 1:
            return False
        else:
            self.beg = min(seg.beg, self.beg)
            self.end = max(seg.end, self.end)
            return True

    def is_attach(self, pos):
        return (self.beg - 1) <= pos <= (self.end + 1)


def merge_segments(segments):
    if len(segments) > 1:
        segments.sort(key=lambda s: s.beg)
        s0 = segments[0]
        result = []
        for si in segments[1:]:
            if not s0.merge(si):
                result.append(s0)
                s0 = si
        result.append(s0)
        return result
    else:
        return segments


class Rect:
    def __init__(self, box, height=0):
        if height:
            x0 = box[0] * DPI
            x1 = box[2] * DPI
        else:
            x0 = box[0]
            x1 = box[2]
        self.w = round(x1 - x0)
        self.x0 = round(x0)
        self.x1 = self.x0 + self.w

        if height:
            y0 = height - box[3] * DPI
            y1 = height - box[1] * DPI
        else:
            y0 = box[1]
            y1 = box[3]
        self.h = round(y1 - y0)
        if height:
            self.y1 = round(y1)
            self.y0 = self.y1 - self.h
        else:
            self.y0 = round(y0)
            self.y1 = self.y0 + self.h

        self._text = {}

    def __repr__(self):
        linetexts = []
        for y in sorted(self._text.keys()):
            linedict = self._text[y]
            linetext = '{}:'.format(y)
            for x in sorted(linedict.keys()):
                linetext += linedict[x]
            linetexts.append(linetext)

        return '({},{})-({},{}) {}'.format(self.x0, self.y0, self.x1, self.y1, ','.join(linetexts))

    def lefttop(self):
        return self.x0, self.y0

    def rightbottom(self):
        return self.x1, self.y1

    def is_same(self, r):
        if isinstance(r, Rect):
            return self.x0 == r.x0 and self.y0 == r.y0 and self.x1 == r.x1 and self.y1 == r.y1
        else:
            return False

    def is_empty(self):
        return self.w < 2 or self.h < 2

    def is_inner(self, pt):
        x, y = pt[0], pt[1]
        return self.x0 < x < self.x1 and self.y0 < y < self.y1

    def add_text(self, pt, text):
        # if isinstance( text,LTTextLine):
        #     for ch in text:
        #         if isinstance(ch,LTChar):
        #             ch.bbox
        x, y = pt[0], pt[1]
        if self.is_inner((x, y)):
            for ch in text:
                if isinstance(ch, LTChar):
                    if y in self._text.keys():
                        self._text[y][ch.x0] = ch.get_text()
                    else:
                        self._text[y] = {ch.x0: ch.get_text()}
            return True

        return False

    def get_text(self):
        text = []
        for y in sorted(self._text.keys()):
            linedict = self._text[y]
            linetext = ''.join([linedict[x] for x in sorted(linedict.keys())])
            text.append(linetext)
            # for x in sorted(linedict.keys()):
            #     linetext += linedict[x]
            # if len(text):
            #     text += '\n' + linetext
            # else:
            #     text = linetext
        return '\n'.join(text)


class PDF_Table:
    def __init__(self):
        self._hsegs = {}
        self._vsegs = {}
        self._table = []

    def __repr__(self):
        st = ''
        if len(self._hsegs):
            st += 'hsegs:{}\n'.format(self._hsegs)
        if len(self._vsegs):
            st += 'vsegs:{}\n'.format(self._vsegs)
        if len(self._table):
            for row in self._table:
                st += str(row) + '\n'
        return st

    def append_line(self, r):
        if r.w:
            for y in (r.y0, r.y1):
                hseg = Segment(r.x0, r.x1)
                if y in self._hsegs:
                    self._hsegs[y].append(hseg)
                else:
                    self._hsegs[y] = [hseg]

        if r.h:
            for x in (r.x0, r.x1):
                vseg = Segment(r.y0, r.y1)
                if x in self._vsegs:
                    self._vsegs[x].append(vseg)
                else:
                    self._vsegs[x] = [vseg]

    def merge_lines(self):
        for y in self._hsegs:
            self._hsegs[y] = merge_segments(self._hsegs[y])
        for x in self._vsegs:
            self._vsegs[x] = merge_segments(self._vsegs[x])

    def make_cells(self):
        hkey = sorted(self._hsegs.keys())
        vkey = sorted(self._vsegs.keys())
        for i, y1 in enumerate(hkey[1:], start=1):
            for hs1 in self._hsegs[y1]:
                vsegs = {}
                for x in vkey:
                    if hs1.is_attach(x):
                        for vs in self._vsegs[x]:
                            if vs.beg + 3 <= y1 <= vs.end + 1:
                                vsegs[x] = vs
                                break

                if len(vsegs) < 2:
                    continue

                xkey = sorted(vsegs.keys())
                for j in range(len(xkey) - 1):
                    x0, x1 = xkey[j], xkey[j + 1]
                    vs0, vs1 = vsegs[x0], vsegs[x1]
                    if (x1 - x0) < 2:
                        continue
                    for k in range(i - 1, -1, -1):
                        y0 = hkey[k]
                        is_crossy0 = False
                        if vs0.is_attach(y0) and vs1.is_attach(y0):
                            for hs0 in self._hsegs[y0]:
                                if hs0.is_attach(x0) and hs0.is_attach(x1):
                                    is_crossy0 = True
                                    break

                        if is_crossy0:
                            r = Rect((x0, y0, x1, y1))
                            if not r.is_empty():
                                yield r
                            break

    def make_table(self):
        self._table.clear()
        self.merge_lines()
        y0 = 0
        row = []
        for c in sorted(self.make_cells(), key=lambda x: (x.y0, x.x0)):
            if y0 != c.y0:
                if len(row):
                    self._table.append(row)
                row = []
                y0 = c.y0
            row.append(c)
        if len(row):
            self._table.append(row)

    def get_cells(self):
        for row in self._table:
            for c in row:
                yield c


def pdftest(fn):
    with PdfMinerWrapper(fn) as pf:
        for page in pf:
            pagetitle = 'page{}'.format(page.pageid)
            print('showpage:', pagetitle)
            ph = round(page.height * DPI)
            pw = round(page.width * DPI)

            im = Image.new("RGB", (pw, ph), (255, 255, 255))
            draw = ImageDraw.Draw(im)

            tb = PDF_Table()

            for item in pf.get_items(page):
                if isinstance(item, LTRect):
                    r = Rect(item.bbox, ph)
                    tb.append_line(r)
                elif isinstance(item, LTLine):
                    r = Rect(item.bbox, ph)
                    if r.h == 0 or r.w == 0:
                        # 水平或垂直
                        tb.append_line(r)
            tb.make_table()

            for item in pf.get_items(page):
                if isinstance(item, LTTextLine):
                    r = Rect(item.bbox, ph)
                    for c in tb.get_cells():
                        if c.add_text(r.lefttop(), item):
                            break
                    else:
                        for ch in item:
                            if isinstance(ch, LTChar):
                                r = Rect(ch.bbox, ph)
                                text = ch.get_text().strip()
                                if len(text):
                                    font = ImageFont.truetype('msyh.ttc', round(ch.size * DPI))
                                    draw.text(r.lefttop(), text, fill=(0, 0, 0), font=font)
                                    # print(ch.fontname,ch.size)
                                    # draw.text(r.lefttop(), text, fill=(0, 0, 0))
                elif isinstance(item, LTImage):
                    r = Rect(item.bbox, ph)
                    data = item.stream.get_data()
                    try:
                        with io.BytesIO(data) as f:
                            img = Image.open(f)
                            img.load()

                    except Exception as e:
                        img = Image.frombuffer('RGB', item.srcsize, data, 'raw', 'RGB', 0, 1)

                    img = img.resize((r.w, r.h))
                    im.paste(img, r.lefttop())

            for y in tb._hsegs:
                for hs in tb._hsegs[y]:
                    draw.line([hs.beg, y, hs.end, y], fill=(255, 0, 255))
            for x in tb._vsegs:
                for vs in tb._vsegs[x]:
                    draw.line([x, vs.beg, x, vs.end], fill=(255, 0, 255))

            for r in tb.get_cells():
                draw.rectangle([r.lefttop(), r.rightbottom()], outline=(0, 0, 255))
                text = r.get_text()
                if len(text):
                    font = ImageFont.truetype('msyh.ttc', 12)
                    draw.text(r.lefttop(), text, fill=(0, 0, 255), font=font)

            # with open(fn + '_' + pagetitle + '.png', mode='wb') as f:
            #     im.save(f)
            opencv_img = cv2.cvtColor(numpy.array(im), cv2.COLOR_RGB2BGR)
            cv2.namedWindow(pagetitle, cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow(pagetitle, pw, ph)
            cv2.imshow(pagetitle, opencv_img)
            key = cv2.waitKeyEx(0)
            if key in (0x20, 0x0d):
                continue
            else:
                break

        cv2.destroyAllWindows()


if __name__ == '__main__':
    fn = '2017-01-05 [1202991367]关于2013年非公开发行股份解除限售的提示性公告.PDF'
    fn = '2017-04-17 [1203319431][券商公告]信达证券股份有限公司关于北京三川世纪能源科技股份公司2016年度募集资金存放与实际使用情况的专项核查报告.PDF'
    fn = '2016-03-10 [1202033380]2015年度募集资金存放与实际使用情况专项报告及鉴证报告.PDF'
    fn = '2010-08-25 [58349826]2010年半年度报告摘要.PDF'
    fn = '2017-03-17 [1203167521]2016年年度报告摘要.PDF'
    fn = '2017-03-17 [1203167519]2016年年度报告.PDF'
    pdftest('d:/数据处理/pdftest/' + fn)
