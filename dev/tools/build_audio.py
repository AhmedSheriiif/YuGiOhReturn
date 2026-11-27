"""Build the Joey The Passion audio set for the EDOPro-based client.

Source: extracted/voice/joey/english/{stream,internal}  (from Voice.dat)
Output: edopro-pack/theme/sound/  (EDOPro layout: SFX by name, BGM/<situation>/, chants by passcode)

NOTE: in this copy of the game the Joey voice lines (joey_NN.wav) and exodia_*.wav are
all-zero stubs (stripped by the scene release), so they are skipped automatically.
"""
import os, shutil, subprocess, wave, audioop

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
SRC = os.path.join(PROJ, 'extracted', 'voice', 'joey', 'english')
OUT = os.path.join(PROJ, 'edopro-pack', 'theme', 'sound')

# EDOPro BGM situation -> JTP stream tracks
BGM = {
    'menu': ['m_title', 'm_menu'],
    'deck': ['m_kaban'],                 # kaban = deck case (deck construction)
    'duel': ['m_duel1', 'm_duel2', 'm_duel3'],
    'advantage': ['m_yuri'],             # yuuri = winning
    'disadvantage': ['m_furi'],          # furi  = losing
    'win': ['m_win'],
    'lose': ['m_lose'],
}

# EDOPro sound effect -> JTP internal sfx
# (no 'phase' sound on purpose: phase changes are silent, user request 2026-11-26)
SFX = {
    'attack': 'attack', 'damage': 'damage', 'destroyed': 'card_normal_brake', 'equip': 'equip',
    'activate': 'magic_active', 'coinflip': 'coin', 'diceroll': 'dice', 'gainlp': 'life_up',
    'nextturn': 'turn_change', 'flip': 'card_open', 'draw': 'card_move',
    'set': 'card_move', 'specialsummon': 'reborn', 'playerenter': 'start',
}

# chants: card passcode -> (EDOPro chant folder, JTP file)
CHANTS = {
    74677422: ('summon', 'stream/m_red'),      # Red-Eyes B. Dragon summon jingle
    89631139: ('summon', 'stream/m_blue'),     # Blue-Eyes White Dragon
    23995346: ('summon', 'stream/m_ulti'),     # Blue-Eyes Ultimate Dragon
    24094653: ('activate', 'internal/fusion1'),  # Polymerization
    83764718: ('activate', 'internal/reborn'),   # Monster Reborn
    94212438: ('activate', 'internal/uija'),     # Destiny Board
}


def silent(path):
    w = wave.open(path)
    frames = w.readframes(w.getnframes())
    return len(frames) < 4096 or audioop.rms(frames, w.getsampwidth()) < 20


def to_ogg(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'fatal', '-y', '-i', src, '-c:a', 'libvorbis', '-q:a', '6', dst], check=True)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    n = 0
    for situation, tracks in BGM.items():
        for t in tracks:
            src = os.path.join(SRC, 'stream', t + '.wav')
            if os.path.exists(src) and not silent(src):
                to_ogg(src, os.path.join(OUT, 'BGM', situation, 'jtp_%s.ogg' % t)); n += 1
    for name, jtp in SFX.items():
        src = os.path.join(SRC, 'internal', jtp + '.wav')
        if os.path.exists(src) and not silent(src):
            os.makedirs(OUT, exist_ok=True)
            shutil.copy(src, os.path.join(OUT, name + '.wav')); n += 1
    for code, (kind, jtp) in CHANTS.items():
        src = os.path.join(SRC, *jtp.split('/')) + '.wav'
        if os.path.exists(src) and not silent(src):
            to_ogg(src, os.path.join(OUT, kind, '%d.ogg' % code)); n += 1
    voices = [f for f in os.listdir(os.path.join(SRC, 'internal')) if f.startswith('joey_')]
    real = [f for f in voices if not silent(os.path.join(SRC, 'internal', f))]
    print('audio files written:', n, '| Joey voice lines with real audio: %d/%d' % (len(real), len(voices)))


if __name__ == '__main__':
    main()
