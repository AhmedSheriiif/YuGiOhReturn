"""Bigger, color-coded, spaced card command buttons (Summon/Set/Activate/...) in duels. User request
2026-11-26. Buttons become 136x30 with a 6px gap and use tinted plank textures (textures/cmd_*.png,
made by tools/build_theme.py). Idempotent.
"""
import io, os
os.chdir(r'D:\YugiohReturn\edopro\gframe')


def patch(path, old, new):
    s = io.open(path, encoding='utf-8', newline='').read()
    for nl in ('\r\n', '\n'):
        o, n = old.replace('\n', nl), new.replace('\n', nl)
        if n in s:
            return 'skip'
        if s.count(o) == 1:
            io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(o, n))
            return 'ok'
    raise AssertionError((path, old[:80]))


R = []
R.append(patch('game.cpp',
    '\tdefaultStrings.emplace_back(btnReset, 1162);\n\t//deck edit\n',
    '\tdefaultStrings.emplace_back(btnReset, 1162);\n'
    '\t{ // JTP: bigger, color-coded command buttons (positions are set in ClientField::ShowMenu)\n'
    '\t\tconst std::pair<irr::gui::IGUIButton*, const epro::path_char*> styled[] = {\n'
    '\t\t\t{ btnActivate, EPRO_TEXT("./textures/cmd_activate.png") }, { btnOperation, EPRO_TEXT("./textures/cmd_activate.png") },\n'
    '\t\t\t{ btnSummon, EPRO_TEXT("./textures/cmd_summon.png") }, { btnSPSummon, EPRO_TEXT("./textures/cmd_summon.png") },\n'
    '\t\t\t{ btnMSet, EPRO_TEXT("./textures/cmd_set.png") }, { btnSSet, EPRO_TEXT("./textures/cmd_set.png") },\n'
    '\t\t\t{ btnAttack, EPRO_TEXT("./textures/cmd_attack.png") }, { btnRepos, EPRO_TEXT("./textures/cmd_repos.png") },\n'
    '\t\t\t{ btnShowList, EPRO_TEXT("./textures/cmd_other.png") }, { btnReset, EPRO_TEXT("./textures/cmd_other.png") },\n'
    '\t\t};\n'
    '\t\tfor(const auto& [button, texture] : styled) {\n'
    '\t\t\tbutton->setRelativePosition(Scale(4, 0, 140, 30));\n'
    '\t\t\tif(auto* tex = driver->getTexture(texture)) {\n'
    '\t\t\t\tbutton->setImage(tex);\n'
    '\t\t\t\tbutton->setPressedImage(tex);\n'
    '\t\t\t\tbutton->setScaleImage(true);\n'
    '\t\t\t}\n'
    '\t\t}\n'
    '\t}\n'
    '\t//deck edit\n'))
R.append(patch('event_handler.cpp',
    '\tint height = mainGame->Scale(1);\n\tauto increase = mainGame->Scale(21);\n',
    '\tint height = mainGame->Scale(4); // JTP: bigger buttons with a 6px gap\n\tauto increase = mainGame->Scale(36);\n'))
R.append(patch('event_handler.cpp',
    '\tmainGame->wCmdMenu->setRelativePosition(irr::core::recti(x - mainGame->Scale(20), y - mainGame->Scale(20) - height, x + mainGame->Scale(80), y - mainGame->Scale(20)));\n',
    '\tmainGame->wCmdMenu->setRelativePosition(irr::core::recti(x - mainGame->Scale(20), y - mainGame->Scale(20) - height, x + mainGame->Scale(124), y - mainGame->Scale(20))); // JTP: wider menu\n'))
# every button position inside ShowMenu: x offset 4 instead of 1 (centred in the wider menu)
s = io.open('event_handler.cpp', encoding='utf-8', newline='').read()
n = s.count('->setRelativePosition(irr::core::vector2di(1, height));')
s = s.replace('->setRelativePosition(irr::core::vector2di(1, height));', '->setRelativePosition(irr::core::vector2di(mainGame->Scale(4), height));')
io.open('event_handler.cpp', 'w', encoding='utf-8', newline='').write(s)
R.append('button x-offset updated: %d' % n)
print(R)
