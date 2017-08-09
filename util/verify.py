# -*- coding: utf-8 -*-
"""
Created on 17-7-17

@author: hy_qiu
"""
import base64
import io
import json
import time
import tkinter as tk

import PIL.Image
import PIL.ImageTk
import requests


class TYC_Verify(tk.Frame):
    def __init__(self, bg, tg, master=None):
        super().__init__(master)
        self.clicklist = []
        self.on_createwidgets()
        self.on_init(bg, tg)

    def on_createwidgets(self):
        self.bg = tk.Canvas()
        self.tg = tk.Canvas()
        self.ls = tk.Listbox()
        self.ok = tk.Button(text="OK", command=self.on_ok)
        self.clear = tk.Button(text="Clear", command=self.on_clear)
        self.bg.bind('<Button-1>', self.on_click)

        self.bg.place(x=10, y=10, width=320, height=100)
        self.tg.place(x=10, y=120, width=120, height=30)
        self.ls.place(x=340, y=10, width=70, height=140)

        self.ok.place(x=200, y=120, width=60, height=30)
        self.clear.place(x=270, y=120, width=60, height=30)

    def on_init(self, bg, tg):
        self.ibg = PIL.ImageTk.PhotoImage(PIL.Image.open(bg))
        self.itg = PIL.ImageTk.PhotoImage(PIL.Image.open(tg))
        self.bg.create_image(0, 0, anchor=tk.NW, image=self.ibg)
        self.tg.create_image(0, 0, anchor=tk.NW, image=self.itg)

    def on_clear(self):
        self.ls.delete(0, tk.END)
        self.clicklist.clear()
        self.bg.delete('select_rect')
        pass

    def on_ok(self):
        self.quit()
        pass

    def on_click(self, event):
        boxsize = 16

        if event.x > boxsize:
            if event.x > 320 - boxsize:
                x = 320 - boxsize
            else:
                x = event.x
        else:
            x = boxsize

        if event.y > boxsize:
            if event.y > 100 - boxsize:
                y = 100 - boxsize
            else:
                y = event.y
        else:
            y = boxsize

        self.clicklist.append({'x': x, 'y': y})
        self.ls.insert(tk.END, '{} ({},{})'.format(len(self.clicklist), x, y))
        self.bg.create_rectangle(x - boxsize, y - boxsize, x + boxsize, y + boxsize
                                 , outline='red', width=1, tags='select_rect')
        # self.bg.create_oval(x - boxsize, y - boxsize, x + boxsize, y + boxsize
        #                          , outline='red', width=1, tags='select_rect')
        return


def get_verify_base64(bg, tg):
    bg = io.BytesIO(base64.standard_b64decode(bg))
    tg = io.BytesIO(base64.standard_b64decode(tg))
    return get_verify(bg, tg)


def get_verify(bg, tg):
    dlg = TYC_Verify(bg, tg)
    w = 420
    h = 160
    x = int((dlg.winfo_screenwidth() - w) / 2)
    y = int((dlg.winfo_screenheight() - h) / 2)
    app = dlg.winfo_toplevel()
    app.geometry('{}x{}+{}+{}'.format(w, h, x, y))
    app.resizable(False, False)
    dlg.master.title('天眼查-验证')
    dlg.mainloop()
    ret = dlg.clicklist
    try:
        app.destroy()
    except:
        pass
    return ret


def chk_TYC():
    url = 'http://antirobot.tianyancha.com/captcha/getCaptcha.json?t={}'.format(int(time.time() * 1000))
    resp = requests.get(url).json()
    data = resp['data']
    clicklist_json = json.dumps(get_verify_base64(data['bgImage'], data['targetImage']))
    url = 'http://antirobot.tianyancha.com/captcha/checkCaptcha.json'
    param = {'captchaId': data['id'], 'clickLocs': clicklist_json, 't': int(time.time() * 1000)}
    resp = requests.get(url, param)
    data = resp.json()
    if data['state'] == 'ok':
        return True
    else:
        return False


def get_verify_image():
    url = 'http://antirobot.tianyancha.com/captcha/getCaptcha.json?t={}'.format(int(time.time() * 1000))
    resp = requests.get(url).json()
    data = resp['data']
    return base64.standard_b64decode(data['bgImage']), base64.standard_b64decode(data['targetImage'])


def save_verify_image(path, count=10):
    import glob
    beg = 0
    for fn in glob.glob(path + '/bg[0-9][0-9][0-9][0-9].png'):
        i = int(fn[-8:-4])
        if beg < i:
            beg = i
    beg += 1
    for i in range(count):
        bg, tg = get_verify_image()
        with open(path + '/bg{:04d}.png'.format(beg + i), mode='wb') as f:
            f.write(bg)
        with open(path + '/tg{:04d}.png'.format(beg + i), mode='wb') as f:
            f.write(tg)
        # if i % 100 == 0:
        print(beg + i)


if __name__ == '__main__':
    # print(chk_TYC())
    save_verify_image('e:/tyc2/verify')
