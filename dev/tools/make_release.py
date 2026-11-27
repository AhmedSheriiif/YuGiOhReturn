"""Package a YuGiOh Return release from the game folder.

  python tools/make_release.py 0.1.1 --base-url https://<host>/jtp/releases

Produces releases/<version>/:
  YuGiOhReturn-<version>-full.zip     whole game, for new players (download page)
  YuGiOhReturn-<version>-update.zip   only files added/changed since the previous release (for the in-game updater)
  manifest.json              sha256 of every shipped file (the next release diffs against it)
  release.json               {version, notes, assets:[{name,url,md5}]} -> paste/publish on the site (/admin/releases)

The in-game updater (EDOPro ClientUpdater) downloads each asset, checks its MD5, and unzips it over the game
folder (renaming the running exe to .old first), then restarts. It can add/overwrite files but never deletes,
so removed files are only listed in release.json ("removed") for information.

Never shipped (player data): settings, the player's own decks, replays, logs, backups, git folders.
"""
import argparse, hashlib, json, os, re, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
GAME = r'D:\YugiohReturn\game'
OUT_ROOT = r'D:\YugiohReturn\releases'   # on D: (C: is nearly full; keeps big zips out of OneDrive)

EXCLUDE_DIRS = {'.git', '_edopro_orig', 'replay', 'screenshots', 'updates', 'logs', '__pycache__'}
EXCLUDE_FILES = {'config/system.conf', 'config/user_configs.json', 'error.log', '_jtp_installed.txt',
                 'config/system.edopro-orig.conf', 'config/configs.edopro-orig.json', 'update.sh', '.edopro_lock'}

# Fresh installs (full zip only, never in update zips) get a clean default settings file: EDOPro's stock
# system.conf with the JTP defaults applied, none of the developer's personal settings.
DEFAULT_SETTINGS = {
    'nickname': 'Duelist',
    'skin': 'YuGiOh Return',
    'lastlflist': None,              # filled in from the installed banlist (see default_lflist_hash)
    'automonsterpos': '1',           # place monsters automatically
    'autospellpos': '1',             # place spells/traps automatically
    'lastallowedcards': '2',         # OCG/TCG
    'bestOf': '1',
    'music_volume': '50',
    'sound_volume': '60',
    'enable_music': '1',
    'enable_sound': '1',
}


def lflist_hash(path):
    """EDOPro's banlist id (DeckManager::LoadLFListSingle) for the first list in an .lflist.conf file."""
    h = None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\r\n')
        if not line or line[0] == '#':
            continue
        if line[0] == '!':
            if h is not None:
                break
            h = 0x7dfcee6a
            continue
        if h is None or ' ' not in line or line.startswith('$'):
            continue
        code_s, rest = line.split(' ', 1)
        try:
            code, count = int(code_s), int(rest.split()[0])
        except ValueError:
            continue
        if code == 0:
            continue
        m = 0xffffffff
        h = (h ^ (((code << 18) | (code >> 14)) & m) ^ (((code << (27 + count)) & m) | (code >> (5 - count)))) & m
    return h


def default_lflist_hash():
    """The banlist new players start with: the first .lflist.conf installed in the game (alphabetical)."""
    folder = os.path.join(GAME, 'lflists')
    files = sorted(f for f in os.listdir(folder) if f.endswith('.lflist.conf'))
    if not files:
        raise SystemExit('no banlist installed in ' + folder)
    return str(lflist_hash(os.path.join(folder, files[0])))


def default_system_conf():
    DEFAULT_SETTINGS['lastlflist'] = default_lflist_hash()
    src = os.path.join(GAME, 'config', 'system.edopro-orig.conf')
    lines = open(src, encoding='utf-8').read().splitlines()
    out, seen = [], set()
    for line in lines:
        m = re.match(r'^(\w+)\s*=', line)
        if m and m.group(1) in DEFAULT_SETTINGS:
            line = '%s = %s' % (m.group(1), DEFAULT_SETTINGS[m.group(1)])
            seen.add(m.group(1))
        out.append(line)
    missing = set(DEFAULT_SETTINGS) - seen
    if missing:
        raise SystemExit('default system.conf is missing keys: %s' % sorted(missing))
    return ('\n'.join(out) + '\n').encode('utf-8')
EXCLUDE_PATTERNS = [re.compile(p) for p in (r'\.log$', r'\.old$', r'\.dmp$', r'\.tmp$', r'(^|/)\.git')]


def shipped(rel):
    rel = rel.replace('\\', '/')
    if rel in EXCLUDE_FILES or any(p.search(rel) for p in EXCLUDE_PATTERNS):
        return False
    if any(part in EXCLUDE_DIRS for part in rel.split('/')[:-1]):
        return False
    # unused upstream content: Project Ignis card lists (not read; JTP lists live in lflists/) and puzzles (removed)
    if rel.startswith(('repositories/lflists/', 'puzzles/', 'expansions/ci/')):
        return False
    # decks: only Joey's AI decks; personal decks (including the developer's "JTP My ..." ones) stay private
    if rel.startswith('deck/') and not os.path.basename(rel).startswith('JTP AI '):
        return False
    return True


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def scan():
    files = {}
    for root, dirs, names in os.walk(GAME):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for n in names:
            full = os.path.join(root, n)
            rel = os.path.relpath(full, GAME).replace('\\', '/')
            if shipped(rel):
                files[rel] = sha256(full)
    return files


def vkey(v):
    return tuple(int(x) for x in v.split('.'))


def previous_manifest(version):
    if not os.path.isdir(OUT_ROOT):
        return None, {}
    older = sorted((d for d in os.listdir(OUT_ROOT) if re.fullmatch(r'\d+\.\d+\.\d+', d) and vkey(d) < vkey(version)), key=vkey)
    if not older:
        return None, {}
    prev = older[-1]
    return prev, json.load(open(os.path.join(OUT_ROOT, prev, 'manifest.json'), encoding='utf-8'))


FULL_ZIP_FOLDER = 'YuGiOhReturn/'   # the full download extracts into its own folder


def write_zip(path, rels, extra=None, prefix=''):
    # update zips: paths relative to the game folder (the updater unzips them in place)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel in sorted(rels):
            z.write(os.path.join(GAME, *rel.split('/')), prefix + rel)
        for rel, data in (extra or {}).items():
            z.writestr(prefix + rel, data)


INDEX_DIR = r'D:\YugiohReturn\updates'   # committed to the YuGiOhReturn GitHub repo (the game reads it from there)


def write_update_index():
    """For every released version, write updates/<version>.json = the update zips it still needs
    (every newer release's assets, oldest first). The game fetches its own file on start; the newest
    version has no file (404 = up to date)."""
    releases = []
    for d in os.listdir(OUT_ROOT):
        path = os.path.join(OUT_ROOT, d, 'release.json')
        if re.fullmatch(r'\d+\.\d+\.\d+', d) and os.path.exists(path):
            releases.append(json.load(open(path, encoding='utf-8')))
    releases.sort(key=lambda r: vkey(r['version']))
    os.makedirs(INDEX_DIR, exist_ok=True)
    written = []
    for i, rel in enumerate(releases):
        pending = [a for newer in releases[i + 1:] for a in newer['assets']]
        target = os.path.join(INDEX_DIR, rel['version'] + '.json')
        if pending:
            json.dump(pending, open(target, 'w', encoding='utf-8'), indent=2)
            written.append(rel['version'])
        elif os.path.exists(target):
            os.remove(target)
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('version', help='e.g. 0.1.1 (must match JTP_VERSION_* in gframe/config.h)')
    ap.add_argument('--base-url', required=True, help='public folder URL where the zips will be hosted')
    ap.add_argument('--notes', default='')
    ap.add_argument('--full-url', default='', help='public link of the full zip (e.g. MediaFire/Drive) if not hosted at base-url')
    a = ap.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+', a.version):
        raise SystemExit('version must look like 1.2.3')

    out = os.path.join(OUT_ROOT, a.version)
    os.makedirs(out, exist_ok=True)
    current = scan()
    prev, prev_files = previous_manifest(a.version)
    changed = [r for r, h in current.items() if prev_files.get(r) != h]
    removed = sorted(set(prev_files) - set(current))

    full_name = 'YuGiOhReturn-%s-full.zip' % a.version
    write_zip(os.path.join(out, full_name), current, extra={'config/system.conf': default_system_conf()},
              prefix=FULL_ZIP_FOLDER)
    assets = []
    if prev is not None:
        upd_name = 'YuGiOhReturn-%s-update.zip' % a.version
        write_zip(os.path.join(out, upd_name), changed)
        assets.append({'name': upd_name, 'url': '%s/%s/%s' % (a.base_url.rstrip('/'), a.version, upd_name),
                       'md5': md5(os.path.join(out, upd_name))})
    json.dump(current, open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8'), indent=0, sort_keys=True)
    release = {'version': a.version, 'previous': prev, 'notes': a.notes, 'assets': assets,
               'full': {'name': full_name, 'url': a.full_url or '%s/%s/%s' % (a.base_url.rstrip('/'), a.version, full_name),
                        'md5': md5(os.path.join(out, full_name))},
               'changedFiles': len(changed), 'removed': removed}
    json.dump(release, open(os.path.join(out, 'release.json'), 'w', encoding='utf-8'), indent=2)
    size = lambda n: '%.1f MB' % (os.path.getsize(os.path.join(out, n)) / 1e6)
    print('release %s (previous: %s)' % (a.version, prev or 'none - first release, full zip only'))
    print('  files shipped: %d | changed since previous: %d | removed: %d' % (len(current), len(changed), len(removed)))
    print('  %s %s' % (full_name, size(full_name)))
    for x in assets:
        print('  %s %s' % (x['name'], size(x['name'])))
    print('  ->', os.path.join(out, 'release.json'))
    print('  update index (versions that will be offered this update):', write_update_index() or 'none yet')


if __name__ == '__main__':
    main()
