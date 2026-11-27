"""Install edopro-pack/theme (graphics, skin, field art, audio) into the game folder.

- Stock EDOPro files we replace are moved once into <game>/_edopro_orig/ (never our own files).
- Files we installed are listed in <game>/_jtp_installed.txt, so reinstalling only updates them.
- Unchanged files are skipped, so it is safe to run while the game is open (files in use are reported).
"""
import os, shutil, filecmp

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.join(os.path.dirname(HERE), 'edopro-pack', 'theme')
GAME = r'D:\YugiohReturn\game'
BACKUP = os.path.join(GAME, '_edopro_orig')
MANIFEST = os.path.join(GAME, '_jtp_installed.txt')


def load_manifest():
    if not os.path.exists(MANIFEST):
        return set()
    return {l.strip() for l in open(MANIFEST, encoding='utf-8') if l.strip()}


def backup(rel, ours):
    """Move a stock EDOPro file out of the way, once."""
    if rel in ours:
        return
    src, dst = os.path.join(GAME, rel), os.path.join(BACKUP, rel)
    if os.path.exists(src) and not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)


def main():
    ours = load_manifest()
    # stock files that would shadow ours (PNG beats JPG; BGM tracks are picked at random per folder)
    # sounds we intentionally silence (phase change)
    for rel in ['sound/phase.wav']:
        p = os.path.join(GAME, rel.replace('/', os.sep))
        if os.path.exists(p):
            if rel.replace('/', os.sep) in ours:
                os.remove(p); ours.discard(rel.replace('/', os.sep))
            else:
                backup(rel.replace('/', os.sep), ours)
    for rel in ['textures/cover.jpg', 'textures/unknown.jpg']:
        backup(rel.replace('/', os.sep), ours)
    bgm = os.path.join(GAME, 'sound', 'BGM')
    for situation in (os.listdir(bgm) if os.path.isdir(bgm) else []):
        d = os.path.join(bgm, situation)
        for f in (os.listdir(d) if os.path.isdir(d) else []):
            backup(os.path.join('sound', 'BGM', situation, f), ours)

    copied = skipped = 0
    busy = []
    for rel_root in ['textures', 'skin', os.path.join('pics', 'field'), 'sound']:
        for root, _, files in os.walk(os.path.join(THEME, rel_root)):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, THEME)
                dst = os.path.join(GAME, rel)
                if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
                    ours.add(rel); skipped += 1
                    continue
                if os.path.exists(dst):
                    backup(rel, ours)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.copy2(src, dst); copied += 1
                except PermissionError:
                    busy.append(rel)
                ours.add(rel)
    open(MANIFEST, 'w', encoding='utf-8').write('\n'.join(sorted(ours)) + '\n')
    print('theme installed: %d updated, %d unchanged' % (copied, skipped))
    if busy:
        print('in use (close the game and run again):', busy)


if __name__ == '__main__':
    main()
