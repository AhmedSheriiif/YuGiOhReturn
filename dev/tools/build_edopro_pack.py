"""Build an EDOPro resource pack from extracted Joey The Passion data.

Output (edopro-pack/):
  pics/<passcode>.jpg            card art from JTP
  lflists/jtp.lflist.conf        whitelist: only JTP cards are legal
  deck/JTP *.ydk                 Joey's AI decks + player decks
  textures/cover.jpg             JTP card back
  jtp_cards.csv                  index -> passcode mapping report
"""
import os, sys, struct, glob, csv, collections
sys.path.insert(0, os.path.dirname(__file__))
from jtp_db import load, resolve
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
DATA = os.path.join(PROJ, 'extracted', 'data')
OUT = os.path.join(PROJ, 'edopro-pack')
CDB = os.path.join(PROJ, 'downloads', 'babelcdb', 'cards.cdb')
GAME = r"C:\Users\ahmed\OneDrive\Desktop\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion"
USER_DECK_DIRS = [GAME, r"C:\Users\ahmed\OneDrive\Desktop\Yu-Gi-Oh! Power Chaos common"]

MANUAL = {143: 76792184, 800: 11901678, 980: 90660762}  # renamed cards
EXCLUDED = {1107: "Glory of the King's Hand (video-game-only card, not in EDOPro)"}
PLACEHOLDER_ART = {'token_sl.bmp'}  # JTP shows a generic picture for these
DOWNLOADED_ART = os.path.join(PROJ, 'downloads', 'card_images')


def read_ydc(path):
    b = open(path, 'rb').read(); o = 8; lists = []
    while o + 2 <= len(b) and len(lists) < 3:
        n, = struct.unpack_from('<H', b, o); o += 2
        lists.append(list(struct.unpack_from('<%dH' % n, b, o))); o += 2 * n
    while len(lists) < 3: lists.append([])
    return lists


def main():
    cards = load()
    code, how, bad = resolve(cards, CDB)
    for i, c in MANUAL.items(): code[i], how[i] = c, 'manual'
    # user request 2026-11-26: no Divine cards in the game (Obelisk, Slifer, Ra; JTP type 24)
    for c in cards[1:]:
        if c['type'] == 24:
            code.pop(c['index'], None)
            how[c['index']] = 'EXCLUDED-divine'
    unresolved = [c for c in bad if c['index'] not in MANUAL]
    by_konami = {c['konami_id']: c['index'] for c in cards}

    for d in ('pics', 'lflists', 'deck', 'textures'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    # card art
    written, skipped_placeholder = set(), []
    downloaded_used = 0
    for c in cards[1:]:
        i = c['index']
        if i not in code: continue
        if code[i] in written: continue
        if c['art'] in PLACEHOLDER_ART:
            # card from the other Power of Chaos games: use the downloaded image (tools/fetch_missing_art.py)
            dl = os.path.join(DOWNLOADED_ART, '%d.jpg' % code[i])
            if not os.path.exists(dl):
                skipped_placeholder.append(c['name']); continue
            Image.open(dl).convert('RGB').resize((200, 290), Image.LANCZOS).save(
                os.path.join(OUT, 'pics', '%d.jpg' % code[i]), quality=92)
            downloaded_used += 1
        else:
            src = os.path.join(DATA, 'card', c['art'])
            Image.open(src).convert('RGB').save(os.path.join(OUT, 'pics', '%d.jpg' % code[i]), quality=92)
        written.add(code[i])
    Image.open(os.path.join(DATA, 'card', 'card_ura.bmp')).convert('RGB').save(
        os.path.join(OUT, 'textures', 'cover.jpg'), quality=92)

    # legal pool (the banlist files themselves are written at the end from tools/banlists/*.json)
    legal = sorted({(code[c['index']], c['name']) for c in cards[1:] if c['index'] in code})

    # decks
    def to_ydk(lists, title, dst):
        main_, extra, side = ([code[by_konami[k]] for k in L if by_konami.get(k) in code] for L in lists)
        dropped = sum(len(L) for L in lists) - len(main_) - len(extra) - len(side)
        with open(dst, 'w', encoding='utf-8', newline='\n') as f:
            f.write('#created by JTP converter (%s)\n#main\n' % title)
            f.writelines('%d\n' % x for x in main_)
            f.write('#extra\n'); f.writelines('%d\n' % x for x in extra)
            f.write('!side\n'); f.writelines('%d\n' % x for x in side)
        return dropped
    deck_report = []
    srcs = [(p, 'JTP AI ' + os.path.basename(p)[:-4]) for p in sorted(glob.glob(os.path.join(DATA, 'j', 'file', '*.ydc')))]
    for d in USER_DECK_DIRS:
        srcs += [(p, 'JTP My ' + os.path.basename(p)[:-4].lstrip('!')) for p in sorted(glob.glob(os.path.join(d, '*.ydc')))]
    for p, title in srcs:
        dropped = to_ydk(read_ydc(p), title, os.path.join(OUT, 'deck', title + '.ydk'))
        if dropped: deck_report.append((title, dropped))

    with open(os.path.join(OUT, 'jtp_cards.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['index', 'konami_id', 'jtp_name', 'edopro_passcode', 'match', 'art'])
        for c in cards[1:]:
            w.writerow([c['index'], c['konami_id'], c['name'], code.get(c['index'], ''), how.get(c['index'], 'EXCLUDED'), c['art']])

    print('resolved:', collections.Counter(how.values()), '| unresolved:', [c['name'] for c in unresolved])
    print('legal cards in whitelist:', len(legal), '| pics written:', len(written),
          '| from downloaded art:', downloaded_used, '| still without art:', skipped_placeholder)
    print('decks:', len(srcs), '| decks with dropped cards:', deck_report)

    # banlists (edited with tools/banlist_editor.pyw, stored in tools/banlists/*.json)
    from jtp_banlists import write_lflists
    for stale in glob.glob(os.path.join(OUT, 'lflists', '*.lflist.conf')):
        os.remove(stale)
    print('banlists:', write_lflists(os.path.join(OUT, 'lflists')))


if __name__ == '__main__':
    main()
