# -*- coding: utf-8 -*-
"""
Created on 17-7-17

@author: hy_qiu
"""
import tkinter as tk
import PIL.Image, PIL.ImageTk
import base64
import io


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
    return dlg.clicklist


if __name__ == '__main__':
    print(get_verify('e:/tyc/bg.png', 'e:/tyc/tg.png'))
