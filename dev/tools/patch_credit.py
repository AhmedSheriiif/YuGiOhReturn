"""'Developed by AhmedSherif' credit (user request 2026-11-26): main menu, About box, exe properties. Idempotent."""
import io, os
os.chdir(r'D:\YugiohReturn\edopro\gframe')
CREDIT = 'Developed by AhmedSherif'


def patch(path, old, new):
    s = io.open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    o, n = old.replace('\n', nl), new.replace('\n', nl)
    if n in s:
        return 'skip'
    assert s.count(o) == 1, (path, old[:80], s.count(o))
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(o, n))
    return 'ok'


R = []
# main menu: credit line under the buttons (window grows by 25)
R.append(patch('game.cpp',
    '\tdefaultStrings.emplace_back(btnModeExit, 1210);\n\toffset += 35;\n#undef OFFSET\n',
    '\tdefaultStrings.emplace_back(btnModeExit, 1210);\n\toffset += 35;\n'
    '\t{ // JTP: developer credit\n'
    '\t\tauto credit = env->addStaticText(L"' + CREDIT + '", Scale(10, 30 + offset, mainMenuWidth - 10, 52 + offset), false, false, wMainMenu);\n'
    '\t\tcredit->setTextAlignment(irr::gui::EGUIA_CENTER, irr::gui::EGUIA_CENTER);\n'
    '\t\tcredit->setOverrideColor(irr::video::SColor(255, 255, 196, 40));\n'
    '\t}\n'
    '#undef OFFSET\n'))
R.append(patch('game.cpp',
    'Scale(mainMenuLeftX, 200, mainMenuRightX, 415), false, EDOPRO_VERSION_STRING); // JTP: one button less',
    'Scale(mainMenuLeftX, 200, mainMenuRightX, 440), false, EDOPRO_VERSION_STRING); // JTP: one button less + credit line'))
R.append(patch('game.cpp',
    'ResizeWin(mainMenuLeftX, 200, mainMenuRightX, 415)); // JTP',
    'ResizeWin(mainMenuLeftX, 200, mainMenuRightX, 440)); // JTP: + credit line'))
# About box
R.append(patch('game.cpp',
    'addCustomText(L"Yu-Gi-Oh! Joey The Passion\\n"',
    'addCustomText(L"Yu-Gi-Oh! Joey The Passion\\n"\n\t\t\t\t\t\t\t\t\t\t\tL"' + CREDIT + '\\n"'))
# exe properties
R.append(patch('ygopro.rc', 'VALUE "CompanyName", "JTP project"', 'VALUE "CompanyName", "AhmedSherif"'))
R.append(patch('ygopro.rc',
    'VALUE "FileDescription", "Yu-Gi-Oh! Joey The Passion (based on Project Ignis: EDOPro)"',
    'VALUE "FileDescription", "Yu-Gi-Oh! Joey The Passion - ' + CREDIT + ' (based on Project Ignis: EDOPro)"'))
print(R)
