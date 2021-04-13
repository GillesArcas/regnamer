import os
import glob
import re
import time
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from tkinter import ttk


APP_NAME = 'regnamer'
REG_NAME = 'regexp.txt'


class App(tk.Tk):
    def __init__(self, parent):
        tk.Tk.__init__(self, parent)
        self.initialize(parent)
        self.directory = None

    def initialize(self, parent):
        # titre et icone
        self.title(APP_NAME)
        self.iconbitmap('regnamer.ico')

        # taille et position au démarrage de la fenêtre principale
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        w = ws * 4 / 5
        h = hs * 4 / 5
        x = (ws - w) / 2
        y = (hs - h) / 2
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

        # geometry of main window
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0, minsize=20)
        self.grid_columnconfigure(0, weight=1)

        # trap closing window to save list of regexp
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # button bar
        self.toolbar = tk.Frame(self, bd=1, relief=tk.RAISED)
        self.toolbar.grid(row=0, column=0, sticky=tk.W + tk.E, columnspan=2)

        # buttons
        self.create_button('Open', None, self.on_click_open)
        self.recursive = tk.IntVar()
        button = tk.Checkbutton(self.toolbar, text='Recursive', variable=self.recursive, command=self.on_check_rec)
        button.pack(side=tk.LEFT, padx=2, pady=2)
        self.showpath = tk.IntVar()
        self.pathbutton = tk.Checkbutton(self.toolbar, text='Path', variable=self.showpath)
        self.pathbutton.pack(side=tk.LEFT, padx=2, pady=2)
        self.sep = ttk.Separator(self.toolbar, orient='vertical')
        self.sep.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        self.create_button('Refresh', None, self.on_click_refresh)
        self.create_button('Rename', None, self.on_click_rename)

        # paned window to contains a frame (containing a treeview and its scrollbar) and a text
        self.paned_window = tk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned_window.grid(row=1, column=0, sticky=tk.W + tk.E + tk.S + tk.N)

        frame = tk.Frame(self.paned_window)
        self.paned_window.add(frame)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0, minsize=20)

        # table of file names
        self.treeview = Treeview(frame)
        self.treeview.grid(row=0, column=0, sticky=tk.W + tk.E + tk.S + tk.N)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.treeview.yview)
        vsb.grid(row=0, column=1, sticky=tk.S + tk.N)
        self.treeview.configure(yscrollcommand=vsb.set)
        self.cell_editing_on = False

        # text with list of regexp
        self.regtext = RegText(self.paned_window)
        self.paned_window.add(self.regtext)

        # status bar
        self.statusbar = StatusBar(self)
        self.statusbar.grid(row=2, column=0, sticky=tk.W + tk.E)


    def create_button(self, text, imageFilename, event):
        if imageFilename:
            img = tk.PhotoImage(file='resources\\' + imageFilename)
            button = tk.Button(self.toolbar, text=text, image=img, width=18, command=event, relief=tk.GROOVE)
            button.img = img
        else:
            button = tk.Button(self.toolbar, text=text, command=event, relief=tk.GROOVE)
        button.pack(side=tk.LEFT, padx=2, pady=2)
        # ToolTip(button, msg=text, msgFunc=None, follow=True, delay=0)
        return button

    def on_check_rec(self):
        if self.recursive.get():
            self.showpath.set(1)
            self.pathbutton.configure(state=tk.DISABLED)
        else:
            self.pathbutton.configure(state=tk.NORMAL)

    def on_click_open(self):
        load_names(self)

    def on_click_refresh(self):
        refresh_names(self)

    def on_click_rename(self):
        rename_names(self)

    def on_close(self):
        text = self.regtext.get('1.0', 'end')
        text = re.sub('\n+$', '\n', text)
        with open(REG_NAME, 'wt') as f:
            f.write(text)
        self.destroy()


class Treeview(ttk.Treeview):
    def __init__(self, parent):
        columns = ('Filename', 'New name', 'Path')

        ttk.Treeview.__init__(self, parent, height=18, show='headings', columns=columns)
        self.selectmode = "browse"

        self["displaycolumns"] = ('Filename', 'New name')
        self.column('Filename', anchor='w')
        self.column('New name', anchor='w')

        for column in columns:
            self.heading(column, text=column)

        self.bind('<Double-1>', set_cell_value)

        for col in columns:
            self.heading(col, text=col, command=lambda _col=col: treeview_sort_column(self, _col, False))


def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(reverse=reverse)
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))


def set_cell_value(event):
    treeview = event.widget
    root = treeview.master.master
    col = treeview.identify_column(event.x)
    row = treeview.identify_row(event.y)
    colnum = int(col.replace('#', ''))
    rownum = int(row.replace('I', ''), 16)

    if root.cell_editing_on or colnum == 1:
        return
    else:
        root.cell_editing_on = True

    item = treeview.focus()
    bbox = treeview.bbox(item, column=colnum - 1)

    entry = ttk.Entry(root)
    entry.place(x=bbox[0], y=bbox[1] + root.toolbar.winfo_height(), width=bbox[2])
    entry.insert(0, treeview.set(item, column=col))
    entry.focus_set()

    def saveedit(event):
        treeview.set(item, column=col, value=entry.get())
        entry.destroy()
        root.cell_editing_on = False

    def escape(event):
        entry.destroy()
        root.cell_editing_on = False

    entry.bind('<Return>', saveedit)
    entry.bind('<Escape>', escape)


class RegText(tk.Text):
    def __init__(self, parent):
        tk.Text.__init__(self, parent, wrap="none")
        # self.grid(row=2, column=0, sticky=tk.W + tk.E + tk.S + tk.N)
        self.bind("<Double-Button-1>", self.on_control_click_init)
        self.bind("<Double-ButtonRelease-1>", self.on_control_click)
        self.tag_configure("highlight", background="white", foreground="blue")

        with open(REG_NAME) as f:
            self.insert(tk.END, f.read())

    def clicked_paragraph(self, event):
        """
        Return the lines, and the starting and ending line numbers (1-based).
        Note that self.index(tk.INSERT) is not yet updated on Button event.
        Therefore, use self.index("@%x,%y")
        """
        text = self.get('1.0', 'end').splitlines()
        line = int(self.index("@%s,%s" % (event.x, event.y)).split('.')[0])

        # find first and last line of paragraph (delimited by empty lines)
        line1 = line
        while line1 > 1 and text[line1 - 1 - 1].strip():
            line1 -= 1
        line2 = line
        while line2 <= len(text) and text[line2 - 1].strip():
            line2 += 1

        return text[line1 - 1:line2 - 1], line1, line2

    def on_control_click_init(self, event):
        # Tags are applied when event handler finished. Therefore, resetting
        # the tag is delayed in the following event.
        _, line1, line2 = self.clicked_paragraph(event)
        self.tag_add("highlight", f'{line1}.0', f'{line2}.end')

    def on_control_click(self, event):
        # _, line1, line2 = self.clicked_paragraph(event)
        # self.tag_add("highlight", f'{line1}.0', f'{line2}.end')
        # self.update_idletasks()

        time.sleep(0.15)
        para, line1, line2 = self.clicked_paragraph(event)

        # left hand side and right hand side of replacement rule
        para = para + [''] * 2
        lhs = para[1]
        rhs = para[2]

        regtext = event.widget
        root = regtext.master.master
        treeview = root.treeview

        # retrieve file names then clear table
        data = [(treeview.set(item, 'Filename'), treeview.set(item, 'New name')) for item in treeview.get_children()]
        treeview.delete(*treeview.get_children())

        # apply substitution and fill table again
        for index, (filename, newname) in enumerate(data):
            newname = extend_sub(lhs, rhs, filename)
            treeview.insert('', index, values=(filename, newname))

        self.tag_remove("highlight", "1.0", "end")
        self.tag_remove("sel", "1.0", "end")


class StatusBar(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.text = tk.StringVar()
        self.label = tk.Label(self, bd=1, relief=tk.FLAT, anchor=tk.W,
                           textvariable=self.text,
                           font=('arial', 10, 'normal'))
        self.label.pack(fill=tk.X)
        self.text.set('Double click on new name to edit (enter or exit to finish). Double-click on regexp to apply to all new names.')


def extend_sub(lhs, rhs, string):
    # implement rhs extension from boost
    # www.boost.org/doc/libs/1_44_0/libs/regex/doc/html/boost_regex/format/perl_format.html
    rhs = rhs.replace(r'\U', r'\\U')
    rhs = rhs.replace(r'\L', r'\\L')
    rhs = rhs.replace(r'\E', r'\\E')
    rhs = rhs.replace(r'\u', r'\\u')
    rhs = rhs.replace(r'\l', r'\\l')
    result = re.sub(lhs, rhs, string)

    result = re.sub(r'\\U(.*?)(?:\\E|$)', handle_upper, result)
    result = re.sub(r'\\L(.*?)(?:\\E|$)', handle_lower, result)
    result = re.sub(r'\\u(.)', handle_upper, result)
    result = re.sub(r'\\l(.)', handle_lower, result)
    result = re.sub(r'\\E', '', result)

    return result


def handle_upper(match):
    return match.group(1).upper()


def handle_lower(match):
    return match.group(1).lower()


def populate_table(root, directory, treeview):
    # clear table
    treeview.delete(*treeview.get_children())

    if root.recursive.get():
        filestream = glob.glob(os.path.join(directory, '**', '*.*'), recursive=True)
    else:
        filestream = glob.glob(os.path.join(directory, '*.*'), recursive=False)

    for index, fullname in enumerate(filestream):
        filename = os.path.basename(fullname)
        pathname = os.path.dirname(fullname)
        if root.showpath.get():
            treeview.insert('', index, values=(fullname, fullname, pathname))
        else:
            treeview.insert('', index, values=(filename, filename, pathname))


def load_names(root):
    directory = tk.filedialog.askdirectory()
    root.directory = directory
    root.title(f'{APP_NAME} - {root.directory}')
    populate_table(root, directory, root.treeview)


def refresh_names(root):
    populate_table(root, root.directory, root.treeview)


def rename_names(root):
    for item in root.treeview.get_children():
        filename = root.treeview.set(item, 'Filename')
        newname = root.treeview.set(item, 'New name')
        if filename != newname:
            try:
                os.rename(os.path.join(root.directory, filename),
                          os.path.join(root.directory, newname))
            except:
                tk.messagebox.showerror(title='Rename error', message='Unable to rename ' + filename)
    populate_table(root, root.directory, root.treeview)


def run():
    app = App(None)
    app.mainloop()


if __name__ == "__main__":
    run()
