"""YuGiOh Return Banlist Editor (developer tool, not part of the game download).

Double-click to open (or: pythonw tools/banlist_editor.pyw).
- Pick or create a banlist, search a card, set Forbidden / Limited / Semi-Limited / Unlimited.
- Save writes tools/banlists/<slug>.json and also installs the list into the local game
  (D:\\YugiohReturn\\game\\lflists) so you can try it immediately.
- To give it to players: build + release a game update (tools/build_pc.ps1, then tools/make_release.py).
"""
import os, sys, tkinter as tk
from tkinter import ttk, messagebox, simpledialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jtp_banlists as B

try:
    from PIL import Image, ImageTk
except ImportError:  # the editor still works, just without card pictures
    Image = ImageTk = None

GAME_LFLISTS = r'D:\YugiohReturn\game\lflists'
PICS = os.path.join(B.PROJ, 'edopro-pack', 'pics')
STATUS_BY_LABEL = {'Unlimited (3)': 3, 'Semi-Limited (2)': 2, 'Limited (1)': 1, 'Forbidden (0)': 0}
LABEL_BY_STATUS = {v: k for k, v in STATUS_BY_LABEL.items()}
COLORS = {0: '#ff6b6b', 1: '#ffb347', 2: '#ffe066', 3: ''}


class Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('YuGiOh Return Banlist Editor')
        self.geometry('1000x640')
        self.minsize(820, 520)
        self.cards = B.load_cards()
        self.by_code = {c[0]: c for c in self.cards}
        B.ensure_default()
        self.slug = B.DEFAULT_SLUG
        self.data = B.load_banlist(self.slug)
        self.dirty = False
        self.selected = None
        self._photo = None
        self._build()
        self._load_lists()
        self.protocol('WM_DELETE_WINDOW', self._on_close)

    # ------------------------------------------------------------------ layout
    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill='x')
        ttk.Label(top, text='Banlist:').pack(side='left')
        self.list_combo = ttk.Combobox(top, state='readonly', width=34)
        self.list_combo.pack(side='left', padx=6)
        self.list_combo.bind('<<ComboboxSelected>>', lambda e: self._switch_list())
        ttk.Button(top, text='New', command=self._new_list).pack(side='left')
        ttk.Button(top, text='Rename', command=self._rename_list).pack(side='left', padx=4)
        ttk.Button(top, text='Delete', command=self._delete_list).pack(side='left')
        ttk.Button(top, text='Save (and install in my game)', command=self._save).pack(side='right')

        body = ttk.Frame(self, padding=(8, 0, 8, 8))
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(1, weight=1)

        search_row = ttk.Frame(body)
        search_row.grid(row=0, column=0, sticky='ew', pady=(0, 6))
        ttk.Label(search_row, text='Search:').pack(side='left')
        self.search = tk.StringVar()
        self.search.trace_add('write', lambda *_: self._refresh_cards())
        entry = ttk.Entry(search_row, textvariable=self.search)
        entry.pack(side='left', fill='x', expand=True, padx=6)
        entry.focus_set()
        self.only_restricted = tk.BooleanVar(value=False)
        ttk.Checkbutton(search_row, text='Only restricted', variable=self.only_restricted,
                        command=self._refresh_cards).pack(side='left')

        cols = ('name', 'status', 'passcode')
        self.tree = ttk.Treeview(body, columns=cols, show='headings', selectmode='browse')
        for col, text, width in (('name', 'Card', 300), ('status', 'Status', 110), ('passcode', 'Passcode', 90)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor='w')
        for status, color in COLORS.items():
            if color:
                self.tree.tag_configure('s%d' % status, background=color)
        scroll = ttk.Scrollbar(body, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=1, column=0, sticky='nsew')
        scroll.grid(row=1, column=0, sticky='nse')
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._on_select())

        side = ttk.Frame(body, padding=(10, 0, 0, 0))
        side.grid(row=0, column=1, rowspan=2, sticky='nsew')
        self.card_title = ttk.Label(side, text='Select a card', font=('Segoe UI', 11, 'bold'), wraplength=320)
        self.card_title.pack(anchor='w')
        self.image_label = ttk.Label(side)
        self.image_label.pack(anchor='w', pady=6)
        self.status_var = tk.StringVar(value='')
        status_box = ttk.LabelFrame(side, text='Status in this banlist', padding=6)
        status_box.pack(fill='x')
        for label in STATUS_BY_LABEL:
            ttk.Radiobutton(status_box, text=label, value=label, variable=self.status_var,
                            command=self._set_status).pack(anchor='w')
        ttk.Label(side, text='Current restrictions:').pack(anchor='w', pady=(10, 2))
        self.restricted = tk.Listbox(side, height=10)
        self.restricted.pack(fill='both', expand=True)
        self.restricted.bind('<<ListboxSelect>>', lambda e: self._jump_from_restricted())
        self.status_bar = ttk.Label(self, text='', anchor='w', padding=(8, 2))
        self.status_bar.pack(fill='x')

    # ------------------------------------------------------------------ lists
    def _load_lists(self, select=None):
        self.slugs = B.list_banlists()
        names = [B.load_banlist(s)['name'] for s in self.slugs]
        self.list_combo['values'] = names
        idx = self.slugs.index(select or self.slug) if (select or self.slug) in self.slugs else 0
        self.list_combo.current(idx)
        self.slug = self.slugs[idx]
        self.data = B.load_banlist(self.slug)
        self.dirty = False
        self._refresh_all()

    def _confirm_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel('Unsaved changes', 'Save changes to "%s" first?' % self.data['name'])
        if answer is None:
            return False
        if answer:
            self._save()
        return True

    def _switch_list(self):
        new_slug = self.slugs[self.list_combo.current()]
        if new_slug == self.slug:
            return
        if not self._confirm_discard():
            self.list_combo.current(self.slugs.index(self.slug))
            return
        self._load_lists(new_slug)

    def _new_list(self):
        if not self._confirm_discard():
            return
        name = simpledialog.askstring('New banlist', 'Name of the new banlist:', parent=self)
        if not name or not name.strip():
            return
        slug = B.slugify(name)
        if slug in B.list_banlists():
            messagebox.showerror('New banlist', 'A banlist with a similar name already exists.')
            return
        copy = messagebox.askyesno('New banlist', 'Start from a copy of "%s"?\n(No = start with no restrictions)' % self.data['name'])
        B.save_banlist(slug, {'name': name.strip(), 'limits': dict(self.data['limits']) if copy else {}})
        self._load_lists(slug)

    def _rename_list(self):
        name = simpledialog.askstring('Rename banlist', 'New name:', initialvalue=self.data['name'], parent=self)
        if name and name.strip():
            self.data['name'] = name.strip()
            self.dirty = True
            self._save()
            self._load_lists(self.slug)

    def _delete_list(self):
        if self.slug == B.DEFAULT_SLUG:
            messagebox.showinfo('Delete banlist', 'The main "Joey The Passion" list can\'t be deleted (clear its restrictions instead).')
            return
        if not messagebox.askyesno('Delete banlist', 'Delete "%s"? This can\'t be undone.' % self.data['name']):
            return
        os.remove(os.path.join(B.BANLIST_DIR, self.slug + '.json'))
        installed = os.path.join(GAME_LFLISTS, self.slug + '.lflist.conf')
        if os.path.exists(installed):
            os.remove(installed)
        self.dirty = False
        self._load_lists(B.DEFAULT_SLUG)

    # ------------------------------------------------------------------ cards
    def _status_of(self, code):
        return self.data['limits'].get(code, 3)

    def _refresh_all(self):
        self._refresh_cards()
        self._refresh_restricted()
        self._update_status_bar()

    def _refresh_cards(self):
        q = self.search.get().strip().lower()
        only = self.only_restricted.get()
        self.tree.delete(*self.tree.get_children())
        for code, name, _ in sorted(self.cards, key=lambda c: c[1].lower()):
            status = self._status_of(code)
            if only and status == 3:
                continue
            if q and q not in name.lower() and q != str(code):
                continue
            self.tree.insert('', 'end', iid=str(code), values=(name, LABEL_BY_STATUS[status], code),
                             tags=('s%d' % status,) if status != 3 else ())

    def _refresh_restricted(self):
        self.restricted.delete(0, 'end')
        self._restricted_codes = []
        for status in (0, 1, 2):
            for code in sorted((c for c, s in self.data['limits'].items() if s == status),
                               key=lambda c: self.by_code.get(c, (c, str(c)))[1].lower()):
                name = self.by_code.get(code, (code, '#%d' % code))[1]
                self.restricted.insert('end', '%s  -  %s' % (LABEL_BY_STATUS[status], name))
                self._restricted_codes.append(code)

    def _update_status_bar(self):
        counts = {s: sum(1 for v in self.data['limits'].values() if v == s) for s in (0, 1, 2)}
        self.status_bar.config(text='%s%s  |  Forbidden: %d   Limited: %d   Semi-Limited: %d   |  %d cards in the pool' % (
            self.data['name'], ' (unsaved changes)' if self.dirty else '', counts[0], counts[1], counts[2], len(self.cards)))

    def _on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        self._show_card(int(sel[0]))

    def _show_card(self, code):
        self.selected = code
        name = self.by_code[code][1]
        self.card_title.config(text='%s  (%d)' % (name, code))
        self.status_var.set(LABEL_BY_STATUS[self._status_of(code)])
        pic = os.path.join(PICS, '%d.jpg' % code)
        if Image and os.path.exists(pic):
            img = Image.open(pic)
            img.thumbnail((200, 290))
            self._photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self._photo, text='')
        else:
            self.image_label.config(image='', text='(no picture)')

    def _set_status(self):
        if self.selected is None:
            return
        status = STATUS_BY_LABEL[self.status_var.get()]
        if status == 3:
            self.data['limits'].pop(self.selected, None)
        else:
            self.data['limits'][self.selected] = status
        self.dirty = True
        keep = str(self.selected)
        self._refresh_all()
        if self.tree.exists(keep):
            self.tree.selection_set(keep)
            self.tree.see(keep)

    def _jump_from_restricted(self):
        sel = self.restricted.curselection()
        if not sel:
            return
        code = self._restricted_codes[sel[0]]
        self.search.set('')
        if self.tree.exists(str(code)):
            self.tree.selection_set(str(code))
            self.tree.see(str(code))
        self._show_card(code)

    # ------------------------------------------------------------------ save
    def _save(self):
        B.save_banlist(self.slug, self.data)
        installed = ''
        if os.path.isdir(GAME_LFLISTS):
            with open(os.path.join(GAME_LFLISTS, self.slug + '.lflist.conf'), 'w', encoding='utf-8', newline='\n') as f:
                f.write(B.to_lflist(self.data, self.cards))
            installed = '\nInstalled in your game (restart the game to see it).'
        self.dirty = False
        self._update_status_bar()
        messagebox.showinfo('Saved', 'Saved "%s".%s\n\nTo send it to players, build and release a game update.' % (self.data['name'], installed))

    def _on_close(self):
        if self._confirm_discard():
            self.destroy()


if __name__ == '__main__':
    Editor().mainloop()
