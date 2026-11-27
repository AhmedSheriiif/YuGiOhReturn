"""Generate the Joey The Passion visual theme for the EDOPro-based client.

All art comes from the extracted original game (extracted/data, extracted/png).
Output: edopro-pack/theme/  (mirrors the game folder layout)
  textures/bg_menu.png, bg_deck.png, bg.png, cover.png, cover2.png, field*.png, AppIcon.png, unknown.png
  skin/YuGiOh Return/*.png + skin.xml
  pics/field/<passcode>.png      field-spell backgrounds from JTP
  icon/jtp.ico                   window/exe icon
"""
import os, re, shutil, sqlite3
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
J = os.path.join(PROJ, 'extracted', 'data', 'j')
DATA = os.path.join(PROJ, 'extracted', 'data')
PNG = os.path.join(PROJ, 'extracted', 'png', 'j')
OUT = os.path.join(PROJ, 'edopro-pack', 'theme')
GAME = r'D:\YugiohReturn\game'          # stock EDOPro assets used as layout templates
CDB = os.path.join(PROJ, 'downloads', 'babelcdb', 'cards.cdb')
W, H = 1920, 1080
SKIN = 'YuGiOh Return'

NAVY = (16, 28, 64)
GOLD = (255, 196, 40)


def out(*p):
    path = os.path.join(OUT, *p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def key_green(im):
    """JTP uses pure green (0,255,0..6) as transparency. Remove it and de-spill edges."""
    im = im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if g > 180 and r < 90 and b < 90:
                px[x, y] = (0, 0, 0, 0)
            elif g > r + 40 and g > b + 40:          # green fringe
                px[x, y] = (r, max(r, b), b, a)
    return im


def cover(im, size):
    """Scale to fill size and centre-crop."""
    return ImageOps.fit(im.convert('RGBA'), size, Image.LANCZOS)


def darken(im, f):
    return ImageEnhance.Brightness(im).enhance(f)


def vignette(im, strength=0.55):
    w, h = im.size
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((-w * 0.15, -h * 0.25, w * 1.15, h * 1.25), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) // 6))
    dark = Image.new('RGBA', (w, h), (0, 0, 0, int(255 * strength)))
    base = im.convert('RGBA').copy()
    base.alpha_composite(Image.composite(Image.new('RGBA', (w, h), (0, 0, 0, 0)), dark, mask))
    return base


def fence_background():
    """Chain-link fence from the title screen, without the centre logo."""
    t = Image.open(os.path.join(J, 'title', 'title_1_e.bmp')).convert('RGBA')
    strip = t.crop((0, 0, 150, 600))
    scale = H / 600
    strip = strip.resize((int(150 * scale), H), Image.LANCZOS)
    bg = Image.new('RGBA', (W, H))
    x, flip = 0, False
    while x < W:
        bg.paste(ImageOps.mirror(strip) if flip else strip, (x, 0))
        x += strip.width; flip = not flip
    return bg


# ---------------------------------------------------------------- backgrounds
def build_backgrounds():
    joey = key_green(Image.open(os.path.join(J, 'bust_up', 'start', 'reaction16.bmp')))
    joey = joey.crop(joey.getbbox())
    logo = key_green(Image.open(os.path.join(J, 'title', 'joey_logo.bmp')))
    logo = logo.crop(logo.getbbox())

    # main menu: fence + Joey + logo (menu window sits in the centre)
    bg = vignette(darken(fence_background(), 0.75), 0.5)
    jh = int(H * 0.92)
    j = joey.resize((int(joey.width * jh / joey.height), jh), Image.LANCZOS)
    shadow = Image.new('RGBA', j.size, (0, 0, 0, 0)); shadow.putalpha(j.getchannel('A').point(lambda a: a * 0.6))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    bg.alpha_composite(shadow, (40 + 18, H - jh + 14))
    bg.alpha_composite(j, (40, H - jh))
    # keep the logo above the centred menu window (menu starts at ~40% of the height)
    lw = 640
    l = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    bg.alpha_composite(l, ((W - lw) // 2 + 300, 12))
    bg.convert('RGB').save(out('textures', 'bg_menu.png'))

    # deck editor: graffiti garage, darkened so panels stay readable
    deck = Image.open(os.path.join(J, 'list', 'list_bg.bmp'))
    vignette(darken(cover(deck, (W, H)), 0.55), 0.45).convert('RGB').save(out('textures', 'bg_deck.png'))

    # duel: brick wall with the "duel" graffiti
    duel = Image.open(os.path.join(J, 'bust_up', 'start', 'statobg_e.bmp'))
    vignette(darken(cover(duel, (W, H)), 0.6), 0.5).convert('RGB').save(out('textures', 'bg.png'))


# ---------------------------------------------------------------- duel field
def build_fields():
    plate = Image.open(os.path.join(J, 'duel', 'field', 'fie_normal.bmp')).convert('RGBA')
    for name in ['field', 'field2', 'field3', 'field4', 'fieldSP', 'fieldSP2', 'fieldSP3', 'fieldSP4']:
        tpl = Image.open(os.path.join(GAME, 'textures', name + '.png')).convert('RGBA')
        base = darken(plate.resize(tpl.size, Image.LANCZOS), 0.8)
        base.alpha_composite(tpl)
        base.save(out('textures', name + '.png'))


def build_field_spells():
    """JTP field-spell art -> pics/field/<passcode>.png, using the game's own field.txt
    (fie_<key>.bmp  //  <konami id>:<name>) and our konami-id -> passcode resolution."""
    import sys
    sys.path.insert(0, HERE)
    from jtp_db import load, resolve
    cards = load()
    code, _, _ = resolve(cards, CDB)
    by_konami = {c['konami_id']: c['index'] for c in cards}
    txt = open(os.path.join(J, 'duel', 'field', 'field.txt'), 'rb').read().decode('shift_jis', 'replace')
    done = []
    for m in re.finditer(r'(fie_\w+)_f\?\.yga\s*//\s*(\d{4}):', txt):
        key, kid = m.group(1), int(m.group(2))
        idx = by_konami.get(kid)
        src = os.path.join(J, 'duel', 'field', key + '.bmp')
        if idx is None or idx not in code or not os.path.exists(src):
            continue
        Image.open(src).convert('RGB').save(out('pics', 'field', '%d.png' % code[idx]))
        done.append('%s=%s' % (key, cards[idx]['name']))
    return done


# ---------------------------------------------------------------- cards
def build_cards():
    back = Image.open(os.path.join(DATA, 'card', 'card_ura.bmp')).convert('RGB').resize((400, 580), Image.LANCZOS)
    back.save(out('textures', 'cover.png'))
    back.save(out('textures', 'cover2.png'))
    back.resize((177, 254), Image.LANCZOS).save(out('textures', 'unknown.png'))


# ---------------------------------------------------------------- icon
def build_icon():
    joey = key_green(Image.open(os.path.join(J, 'bust_up', 'start', 'reaction16.bmp')))
    bb = joey.getbbox()
    # head region: top portion of the figure
    x0, y0, x1, y1 = bb
    side = int((x1 - x0) * 0.42)
    cx = x0 + int((x1 - x0) * 0.40)
    face = joey.crop((cx - side // 2, y0, cx + side // 2, y0 + side))
    tile = Image.new('RGBA', face.size, NAVY + (255,))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle((0, 0, face.width - 1, face.height - 1), radius=face.width // 6, fill=NAVY + (255,),
                        outline=GOLD + (255,), width=max(3, face.width // 40))
    tile.alpha_composite(face)
    mask = Image.new('L', face.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, face.width - 1, face.height - 1), radius=face.width // 6, fill=255)
    tile.putalpha(mask)
    tile = tile.resize((256, 256), Image.LANCZOS)
    tile.save(out('icon', 'jtp.ico'), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    tile.resize((1024, 1024), Image.LANCZOS).save(out('textures', 'AppIcon.png'))


# ---------------------------------------------------------------- GUI skin
def plank_strip(src_name, white_thr=200):
    """Return (strip, band_height): a text-free vertical slice of a wooden plank."""
    im = Image.open(os.path.join(J, 'title', src_name)).convert('RGB')
    w, h = im.size
    px = im.load()
    def plank_px(p):
        r, g, b = p
        wood = r > 95 and r > b + 30
        text = min(p) > 200 or (r > 70 and g < 70 and b < 40)
        return wood or text
    rows = [sum(plank_px(px[x, y]) for x in range(w)) / w > 0.8 for y in range(h)]
    bands, y = [], 0
    while y < h:
        if rows[y]:
            y0 = y
            while y < h and rows[y]: y += 1
            if y - y0 >= 24: bands.append((y0, y))
        y += 1
    best = None
    for y0, y1 in bands:
        clean = [all(min(px[x, yy]) < white_thr for yy in range(y0 + 1, y1 - 1)) for x in range(w)]
        x = 0
        while x < w:
            if clean[x]:
                x0 = x
                while x < w and clean[x]: x += 1
                if best is None or x - x0 > best[2] - best[0]:
                    best = (x0, y0, x, y1)
            x += 1
    x0, y0, x1, y1 = best
    margin = 2
    return im.crop((x0 + margin, y0, x1 - margin, y1))


def make_plank(strip, size, bright=1.0, sat=1.0, border=(60, 25, 8)):
    w, h = size
    s = strip.resize((strip.width, h), Image.LANCZOS)
    p = Image.new('RGB', (w, h))
    x, flip = 0, False
    while x < w:
        p.paste(ImageOps.mirror(s) if flip else s, (x, 0))
        x += s.width; flip = not flip
    p = ImageEnhance.Color(ImageEnhance.Brightness(p).enhance(bright)).enhance(sat).convert('RGBA')
    d = ImageDraw.Draw(p)
    d.rectangle((0, 0, w - 1, h - 1), outline=border + (255,), width=2)
    d.line((2, 2, w - 3, 2), fill=(255, 220, 160, 90))           # top highlight
    d.line((2, h - 3, w - 3, h - 3), fill=(0, 0, 0, 110))        # bottom shade
    return p


def panel(size, fill, border, alpha=235, bar=0):
    w, h = size
    p = Image.new('RGBA', size, fill + (alpha,))
    d = ImageDraw.Draw(p)
    # subtle vertical gradient
    for y in range(h):
        f = 1.0 - 0.35 * y / h
        d.line((0, y, w, y), fill=tuple(int(c * f) for c in fill) + (alpha,))
    if bar:
        d.rectangle((0, 0, w, bar), fill=(150, 60, 10, alpha))
    d.rectangle((0, 0, w - 1, h - 1), outline=border + (255,), width=2)
    return p


def build_skin():
    src = os.path.join(GAME, 'skin', 'Purple - Obsessed')
    dst = os.path.join(OUT, 'skin', SKIN)
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst)
    strong = plank_strip('menu_e_ani6.bmp')
    make_plank(strong, (256, 48), bright=0.62).save(os.path.join(dst, 'button.png'))
    make_plank(strong, (256, 48), bright=0.95, sat=1.25, border=GOLD).save(os.path.join(dst, 'ButtonPressed.png'))
    make_plank(strong, (256, 48), bright=0.45, sat=0.15, border=(40, 40, 40)).save(os.path.join(dst, 'ButtonDisabled.png'))
    make_plank(strong, (213, 107), bright=0.5).save(os.path.join(dst, 'TabButton.png'))
    make_plank(strong, (213, 107), bright=0.85, sat=1.2, border=GOLD).save(os.path.join(dst, 'TabButtonPressed.png'))
    panel((128, 128), NAVY, GOLD, 235, bar=0).save(os.path.join(dst, 'windowbg.png'))
    panel((128, 128), (10, 18, 44), (120, 90, 30), 245).save(os.path.join(dst, 'TabControl.png'))
    panel((64, 64), (6, 12, 30), (110, 80, 25), 235).save(os.path.join(dst, 'sunkenpane.png'))
    panel((50, 50), (18, 32, 72), (60, 70, 110), 255).save(os.path.join(dst, 'MenuBar.png'))
    panel((50, 50), (18, 32, 72), GOLD, 245).save(os.path.join(dst, 'MenuPane.png'))
    panel((50, 50), (150, 70, 15), GOLD, 255).save(os.path.join(dst, 'MenuPressed.png'))

    xml = open(os.path.join(src, 'skin.xml'), encoding='utf-8').read()
    def col(tag, rgba):
        nonlocal xml
        a, r, g, b = rgba
        xml, n = re.subn(r'<%s a="\d+" r="\d+" g="\d+" b="\d+" />' % tag,
                         '<%s a="%d" r="%d" g="%d" b="%d" />' % (tag, a, r, g, b), xml)
        assert n, tag
    xml = re.sub(r'<Name data="[^"]*" />', '<Name data="%s" />' % SKIN, xml)
    xml = re.sub(r'<Author data="[^"]*" />', '<Author data="JTP project (based on Purple - Obsessed by Icematoro)" />', xml)
    xml = re.sub(r'<Desc data="[^"]*"/?>', '<Desc data="YuGiOh Return theme (art from Yu-Gi-Oh! Power of Chaos: Joey The Passion)"/>', xml)
    col('EGDC_3D_SHADOW', (255, 150, 70, 15))
    col('EGDC_3D_HIGH_LIGHT', (255, 10, 18, 44))
    col('EGDC_ACTIVE_CAPTION', (255,) + GOLD)
    col('EGDC_INACTIVE_CAPTION', (255, 230, 220, 190))
    col('EGDC_TOOLTIP_BACKGROUND', (210, 20, 34, 80))
    col('EGDC_TOOLTIP', (255, 255, 240, 210))
    col('EGDC_SCROLLBAR', (255, 30, 46, 96))
    col('EGDC_ICON', (255, 150, 70, 15))
    col('EGDC_ICON_HIGH_LIGHT', (255,) + GOLD)
    col('CheckBoxColor', (255,) + GOLD)
    col('CARDINFO_TYPES_COLOR', (255,) + GOLD)
    col('CARDINFO_STATS_COLOR', (255,) + GOLD)
    col('CARDINFO_ARCHETYPE_TEXT_COLOR', (255,) + GOLD)
    col('CARDINFO_PASSCODE_SCOPE_TEXT_COLOR', (255, 255, 230, 160))
    col('CARDINFO_IMAGE_BACKGROUND', (255, 8, 14, 34))
    col('DUELFIELD_TOOLTIP_TEXT_BACKGROUND_COLOR', (215, 12, 22, 56))
    open(os.path.join(dst, 'skin.xml'), 'w', encoding='utf-8').write(xml)


def build_cmd_buttons():
    """Colored wooden planks for the in-duel card command menu (Summon/Set/Activate/...).
    Same plank texture as the UI buttons, tinted per action so they are easy to tell apart."""
    strong = plank_strip('menu_e_ani6.bmp')
    tints = {
        'summon': (40, 150, 60),     # green: Normal/Special Summon
        'set': (40, 90, 190),        # blue: Set
        'activate': (210, 150, 20),  # gold: Activate / effects
        'attack': (190, 35, 35),     # red: Attack
        'repos': (120, 60, 170),     # purple: change position
        'other': None,               # plain wood: list, reset
    }
    for name, tint in tints.items():
        plank = make_plank(strong, (272, 60), bright=0.7, border=(20, 12, 4)).convert('RGB')
        if tint:
            color = Image.new('RGB', plank.size, tint)
            plank = Image.blend(plank, color, 0.45)
        plank = plank.convert('RGBA')
        d = ImageDraw.Draw(plank)
        d.rectangle((0, 0, plank.width - 1, plank.height - 1), outline=GOLD + (255,), width=2)
        plank.save(out('textures', 'cmd_%s.png' % name))


if __name__ == '__main__':
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    build_cmd_buttons(); print('command buttons ok')
    build_backgrounds(); print('backgrounds ok')
    build_fields(); print('fields ok')
    print('field spells:', build_field_spells())
    build_cards(); print('card backs ok')
    build_icon(); print('icon ok')
    build_skin(); print('skin ok')
