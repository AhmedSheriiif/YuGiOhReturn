"""Load the Joey The Passion card database (extracted/data/bin) into Python dicts."""
import struct, os, re
ROOT = os.path.join(os.path.dirname(__file__), '..', 'extracted', 'data')
N = 1115

def bcd(v):
    s = ''.join('%02x' % x for x in struct.pack('<I', v))
    return int(s) if s.isdigit() else None

def load():
    b = lambda f: open(os.path.join(ROOT, 'bin', f), 'rb').read()
    ids = struct.unpack('<%dH' % N, b('card_id.bin'))
    pas = struct.unpack('<%dI' % N, b('card_pass.bin'))
    prop = struct.unpack('<%dI' % N, b('card_prop.bin'))
    names = b('card_nameeng.bin')
    cards = []
    for i in range(N):
        v = prop[i]
        cards.append(dict(index=i, konami_id=ids[i], passcode=bcd(pas[i]),
            name=names[i*64:(i+1)*64].split(b'\0')[0].decode('latin1'),
            defense=(v & 0x1ff)*10, attack=((v>>9)&0x1ff)*10, kind=(v>>18)&3,
            type=(v>>20)&0x1f, level=(v>>25)&0xf, attribute=(v>>29)&7))
    # art file per index from list_card.txt
    txt = open(os.path.join(ROOT, 'card', 'list_card.txt'), 'rb').read().decode('latin1')
    for m in re.finditer(r'//\s*(\d{4}):\[(\d{4})\][^\n]*\n([^\r\n/]+\.bmp)', txt):
        cards[int(m.group(1))]['art'] = m.group(3).strip()
    return cards

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def resolve(cards, cdb_path):
    """Map each JTP card to an EDOPro passcode. Returns (mapping index->code, how index->method, unresolved)."""
    import sqlite3
    db = sqlite3.connect(cdb_path)
    rows = list(db.execute('select d.id, t.name, d.alias from datas d join texts t on t.id=d.id'))
    byid = {r[0]: r for r in rows}
    byname = {}
    for cid, name, alias in rows:
        if alias == 0: byname.setdefault(norm(name), cid)
    m, how, bad = {}, {}, []
    for c in cards[1:]:
        pc, i = c['passcode'], c['index']
        if pc in byid:
            m[i], how[i] = (byid[pc][2] or pc), 'passcode'; continue
        if norm(c['name']) in byname:
            m[i], how[i] = byname[norm(c['name'])], 'name'; continue
        if pc:  # masked: digits at even positions are the real first 4 digits
            s = '%08d' % pc; pre = s[0] + s[2] + s[4] + s[6]
            cand = [r[0] for r in rows if r[2] == 0 and '%08d' % r[0] .startswith(pre)] if False else \
                   [r[0] for r in rows if r[2] == 0 and ('%08d' % r[0]).startswith(pre)]
            if len(cand) == 1: m[i], how[i] = cand[0], 'masked-prefix'; continue
        bad.append(c)
    return m, how, bad
