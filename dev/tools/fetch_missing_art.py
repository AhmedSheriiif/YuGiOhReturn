"""Download card images for JTP cards that have no art in the game (pack group 0: cards from the
other Power of Chaos games, shown in JTP with the generic token_sl.bmp placeholder).

Source: YGOPRODeck card images by passcode (https://images.ygoprodeck.com/images/cards/<id>.jpg).
Downloaded once into downloads/card_images/<passcode>.jpg (cache; existing files are skipped).
build_edopro_pack.py then uses them for those cards.
"""
import csv, os, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
CSV = os.path.join(PROJ, 'edopro-pack', 'jtp_cards.csv')
DST = os.path.join(PROJ, 'downloads', 'card_images')
URL = 'https://images.ygoprodeck.com/images/cards/{}.jpg'
PLACEHOLDER = 'token_sl.bmp'


def main():
    os.makedirs(DST, exist_ok=True)
    rows = list(csv.DictReader(open(CSV, encoding='utf-8')))
    want = sorted({r['edopro_passcode'] for r in rows
                   if r['art'] == PLACEHOLDER and r['edopro_passcode'] and not r['match'].startswith('EXCLUDED')})
    got = skipped = 0
    failed = []
    for code in want:
        path = os.path.join(DST, code + '.jpg')
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            skipped += 1
            continue
        req = urllib.request.Request(URL.format(code), headers={'User-Agent': 'JTP-card-art-fetcher/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise ValueError('too small')
            open(path, 'wb').write(data)
            got += 1
        except Exception as e:
            failed.append((code, str(e)))
        time.sleep(0.12)   # stay well under the site's rate limit
    print('needed %d | downloaded %d | already had %d | failed %d' % (len(want), got, skipped, len(failed)))
    for code, err in failed:
        print('  FAILED', code, err)


if __name__ == '__main__':
    main()
