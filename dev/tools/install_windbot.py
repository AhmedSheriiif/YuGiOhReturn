"""Install the JTP WindBot build into the game folder with Joey's decks as AI opponents.

Source build: D:/YugiohReturn/windbot/bin/Release (our fork, branch jtp, with JoeyExecutor).
Decks:        edopro-pack/deck/JTP AI <name>.ydk  ->  WindBot/Decks/AI_JTP_<name>.ydk
bots.json:    only Joey The Passion opponents (deck "JTP_<name>" -> JoeyExecutor).
"""
import os, shutil, json, glob, re

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(os.path.dirname(HERE), 'edopro-pack', 'deck')
BUILD = r'D:\YugiohReturn\windbot\bin\Release'
GAME = r'D:\YugiohReturn\game'
DST = os.path.join(GAME, 'WindBot')

THEMES = {'ge1': 'Warriors', 'ge2': 'Warriors II', 'umi': 'Umi Sea', 'val': 'Magnet Warriors',
          'dec': 'Deck Destruction', 'fus': 'Fusion', 'gam': 'Gamble', 'hik': 'Light', 'ins': 'Insects',
          'mix': 'Mix', 'red': 'Red-Eyes', 'too': 'Toon', 'uij': 'Germ Burn', 'exo': 'Exodia',
          'grv': 'Gravity Bind', 'hnd': 'Hand Control', 'yam': 'Yami', 'all': 'All-Star'}


def main():
    if os.path.exists(DST):
        shutil.rmtree(DST)
    shutil.copytree(BUILD, DST, ignore=shutil.ignore_patterns('*.pdb', 'Decks', 'bots.json'))
    os.makedirs(os.path.join(DST, 'Decks'))
    bots = []
    for p in sorted(glob.glob(os.path.join(PACK, 'JTP AI *.ydk'))):
        key = os.path.basename(p)[len('JTP AI '):-4]          # cpu_000 / ful_1red
        shutil.copy(p, os.path.join(DST, 'Decks', 'AI_JTP_%s.ydk' % key))
        m = re.match(r'cpu_(\d)(\d)(\d)', key)
        if m:
            tier = int(m.group(2))
            name = 'Joey Lv.%d - Deck %s' % (tier + 1, m.group(3))
            difficulty = 1 + tier
        else:
            m = re.match(r'ful_(\d)(\w+)', key)
            tier, theme = int(m.group(1)), m.group(2)
            name = 'Joey %s Lv.%d' % (THEMES.get(theme, theme.title()), tier + 1)
            difficulty = 1 + tier
        bots.append({'name': name, 'deck': 'JTP_' + key, 'difficulty': difficulty, 'masterRules': [1, 2, 3, 4, 5]})
    bots.sort(key=lambda b: (b['difficulty'], b['name']))
    json.dump(bots, open(os.path.join(DST, 'bots.json'), 'w', encoding='utf-8'), indent=4)
    print('installed WindBot with %d Joey opponents -> %s' % (len(bots), DST))


if __name__ == '__main__':
    main()
