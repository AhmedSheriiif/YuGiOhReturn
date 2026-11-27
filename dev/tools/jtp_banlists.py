"""Banlists for the JTP game (developer-side; never shipped as source).

Each banlist is a JSON file in tools/banlists/<slug>.json:
    {"name": "Joey The Passion", "limits": {"<passcode>": 0|1|2, ...}}
Only restricted cards are stored (0 = Forbidden, 1 = Limited, 2 = Semi-Limited). Every other
Joey The Passion card is Unlimited (3). Cards outside the JTP pool are never legal (whitelist).

to_lflist() turns one into an EDOPro lflist file (lflists/<slug>.lflist.conf) that the game reads.
"""
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
BANLIST_DIR = os.path.join(HERE, 'banlists')
CARDS_CSV = os.path.join(PROJ, 'edopro-pack', 'jtp_cards.csv')
LIMIT_NAMES = {0: 'Forbidden', 1: 'Limited', 2: 'Semi-Limited', 3: 'Unlimited'}
DEFAULT_SLUG = 'yugioh-return'   # only used when no banlist exists at all


CDB = os.path.join(PROJ, 'downloads', 'babelcdb', 'cards.cdb')


def _official_name(code):
    """A few JTP cards have no English name in the game data; use the official one instead."""
    try:
        import sqlite3
        row = sqlite3.connect(CDB).execute('select name from texts where id=?', (code,)).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def load_cards():
    """[(passcode, name, index)] for every legal JTP card, one entry per passcode."""
    seen, out = set(), []
    for r in csv.DictReader(open(CARDS_CSV, encoding='utf-8')):
        if not r['edopro_passcode'] or r['match'].startswith('EXCLUDED'):
            continue
        code = int(r['edopro_passcode'])
        if code in seen:
            continue
        seen.add(code)
        name = r['jtp_name'].strip() or _official_name(code) or '#%d' % code
        out.append((code, name, int(r['index'])))
    return out


def slugify(name):
    s = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return s or 'banlist'


def list_banlists():
    os.makedirs(BANLIST_DIR, exist_ok=True)
    return sorted(f[:-5] for f in os.listdir(BANLIST_DIR) if f.endswith('.json'))


def load_banlist(slug):
    data = json.load(open(os.path.join(BANLIST_DIR, slug + '.json'), encoding='utf-8'))
    data['limits'] = {int(k): int(v) for k, v in data.get('limits', {}).items()}
    return data


def save_banlist(slug, data):
    os.makedirs(BANLIST_DIR, exist_ok=True)
    out = {'name': data['name'], 'limits': {str(k): v for k, v in sorted(data['limits'].items()) if v in (0, 1, 2)}}
    json.dump(out, open(os.path.join(BANLIST_DIR, slug + '.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


def ensure_default():
    """There is always at least one banlist (an empty 'YuGiOh Return' one if you deleted them all)."""
    if not list_banlists():
        save_banlist(DEFAULT_SLUG, {'name': 'YuGiOh Return', 'limits': {}})


def to_lflist(data, cards):
    lines = ['#[%s]' % data['name'], '!%s' % data['name'], '$whitelist']
    for code, name, _ in sorted(cards):
        lines.append('%d %d --%s' % (code, data['limits'].get(code, 3), name))
    return '\n'.join(lines) + '\n'


def write_lflists(dest_dir, cards=None):
    """Write every banlist as <dest_dir>/<slug>.lflist.conf; returns the slugs written."""
    cards = cards or load_cards()
    ensure_default()
    os.makedirs(dest_dir, exist_ok=True)
    slugs = list_banlists()
    for slug in slugs:
        with open(os.path.join(dest_dir, slug + '.lflist.conf'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(to_lflist(load_banlist(slug), cards))
    return slugs
