"""Remove features Joey The Passion doesn't need from the EDOPro client (D:/YugiohReturn/edopro/gframe).

User request 2026-11-26:
  - remove Puzzles (main menu) and the Repositories top-bar menu
  - only the Joey The Passion card list (hide the "N/A" no-limit list; other lists are disabled in config)
  - lock duels to classic Master Rule 1 (no Speed/Rush/Goat/MR2-5, no custom extra rules)
  - hide modern mechanics in the deck editor (Synchro/Xyz/Pendulum/Link/Tuner/Maximum, Skill, scale, link markers)
  - never show cards outside the Joey The Passion whitelist
Idempotent: each edit is skipped if already applied.
"""
import io, re, os
os.chdir(r'D:\YugiohReturn\edopro\gframe')
MARK = 'JTP:'


def patch(path, old, new, regex=False):
    s = io.open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    new = new.replace('\n', nl)
    if not regex:
        old = old.replace('\n', nl)
        # already applied: a deletion whose text is gone, or an edit whose result is present
        if (new == '' and old not in s) or (new != '' and new in s):
            return 'skip'
        assert s.count(old) == 1, (path, old[:70], s.count(old))
        s = s.replace(old, new)
    else:
        if not re.search(old, s) and new in s:
            return 'skip'
        s, n = re.subn(old, lambda m: new, s, count=1)
        assert n == 1, (path, old[:70])
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    return 'ok'


R = []
# ---------------------------------------------------------------- top bar: Repositories
R.append(patch('game.cpp',
    '\tmRepositoriesInfo = mTopMenu->getSubMenu(mTopMenu->addItem(gDataManager->GetSysString(2045).data(), 1, true, true));\n',
    '\t{ // JTP: Repositories removed from the top bar; kept on a hidden menu because other code still updates it\n'
    '\t\tauto hiddenRepoMenu = irr::gui::CGUICustomMenu::addCustomMenu(env);\n'
    '\t\thiddenRepoMenu->setVisible(false);\n'
    '\t\tmRepositoriesInfo = hiddenRepoMenu->getSubMenu(hiddenRepoMenu->addItem(L"", 1, true, true));\n'
    '\t}\n'))
R.append(patch('game.cpp',
    '\tmTopMenu->setItemText(0, gDataManager->GetSysString(2045).data()); //mRepositoriesInfo\n'
    '\tmTopMenu->setItemText(1, gDataManager->GetSysString(1970).data()); //mAbout\n'
    '\tmTopMenu->setItemText(2, gDataManager->GetSysString(2040).data()); //mVersion\n',
    '\t// JTP: Repositories menu removed, so About/Version are items 0/1\n'
    '\tmTopMenu->setItemText(0, gDataManager->GetSysString(1970).data()); //mAbout\n'
    '\tmTopMenu->setItemText(1, gDataManager->GetSysString(2040).data()); //mVersion\n'))

# ---------------------------------------------------------------- main menu: Puzzles
R.append(patch('game.cpp',
    '\tdefaultStrings.emplace_back(btnSingleMode, 1201);\n\toffset += 35;\n',
    '\tdefaultStrings.emplace_back(btnSingleMode, 1201);\n\tbtnSingleMode->setVisible(false); // JTP: Puzzles removed (no offset, next button moves up)\n'))
R.append(patch('game.cpp',
    'wMainMenu = env->addWindow(Scale(mainMenuLeftX, 200, mainMenuRightX, 450), false, EDOPRO_VERSION_STRING);',
    'wMainMenu = env->addWindow(Scale(mainMenuLeftX, 200, mainMenuRightX, 415), false, EDOPRO_VERSION_STRING); // JTP: one button less'))
R.append(patch('game.cpp',
    'wMainMenu->setRelativePosition(ResizeWin(mainMenuLeftX, 200, mainMenuRightX, 450));',
    'wMainMenu->setRelativePosition(ResizeWin(mainMenuLeftX, 200, mainMenuRightX, 415)); // JTP'))

# ---------------------------------------------------------------- classic rules only
R.append(patch('game.cpp',
    '\tduel_param = gGameConfig->lastDuelParam;\n',
    '\tduel_param = DUEL_MODE_MR1; // JTP: classic rules only (ignores the saved lastDuelParam)\n'))
R.append(patch('game.cpp',
    '\t\tforbiddentypes = gGameConfig->lastDuelForbidden;\n',
    '\t\tforbiddentypes = DUEL_MODE_MR1_FORB; // JTP: classic rules only\n'))
R.append(patch('game.cpp',
    'cbDuelRule = AddComboBox(env, Scale(140, 125, 300, 150), tDuelSettings, COMBOBOX_DUEL_RULE);\n',
    'cbDuelRule = AddComboBox(env, Scale(140, 125, 300, 150), tDuelSettings, COMBOBOX_DUEL_RULE);\n'
    '\t\tcbDuelRule->setEnabled(false); // JTP: locked to Master Rule 1\n'))
R.append(patch('game.cpp',
    'defaultStrings.emplace_back(btnRuleCards, 1625);\n',
    'defaultStrings.emplace_back(btnRuleCards, 1625);\n'
    '\t\tbtnRuleCards->setVisible(false); // JTP: no custom extra rules\n'))
R.append(patch('game.cpp',
    r'\tcb->addItem\(gDataManager->GetSysString\(1260\)\.data\(\)\);\r?\n(\tcb->addItem\(gDataManager->GetSysString\(\d+\)\.data\(\)\);\r?\n){7}',
    '\tcb->addItem(gDataManager->GetSysString(1260).data()); // JTP: Master Rule 1 only\n', regex=True))

# ---------------------------------------------------------------- card lists: hide "N/A"
R.append(patch('game.cpp',
    '\tfor (auto &list : gdeckManager->_lfList) {\n'
    '\t\tauto hostIndex = cbHostLFList->addItem(list.listName.data(), list.hash);\n',
    '\tfor (auto &list : gdeckManager->_lfList) {\n'
    '\t\t// JTP: the trailing "N/A" (no limits) list is not offered\n'
    '\t\tif(gdeckManager->_lfList.size() > 1 && &list == &gdeckManager->_lfList.back())\n'
    '\t\t\tcontinue;\n'
    '\t\tauto hostIndex = cbHostLFList->addItem(list.listName.data(), list.hash);\n'))
R.append(patch('game.cpp',
    '\tauto prev = cbDBLFList->getSelected();\n'
    '\tcbDBLFList->removeItem(static_cast<irr::u32>(nullLFlist));\n'
    '\tcbDBLFList->addItem(gdeckManager->_lfList[nullLFlist].listName.data(), gdeckManager->_lfList[nullLFlist].hash);\n'
    '\tcbDBLFList->setSelected(prev);\n'
    '\tprev = cbHostLFList->getSelected();\n'
    '\tcbHostLFList->removeItem(static_cast<irr::u32>(nullLFlist));\n'
    '\tcbHostLFList->addItem(gdeckManager->_lfList[nullLFlist].listName.data(), gdeckManager->_lfList[nullLFlist].hash);\n'
    '\tcbHostLFList->setSelected(prev);\n',
    '\tauto prev = cbDBLFList->getSelected();\n'
    '\tif(nullLFlist == 0) { // JTP: "N/A" is only listed when it is the only list\n'
    '\tcbDBLFList->removeItem(static_cast<irr::u32>(nullLFlist));\n'
    '\tcbDBLFList->addItem(gdeckManager->_lfList[nullLFlist].listName.data(), gdeckManager->_lfList[nullLFlist].hash);\n'
    '\tcbDBLFList->setSelected(prev);\n'
    '\tprev = cbHostLFList->getSelected();\n'
    '\tcbHostLFList->removeItem(static_cast<irr::u32>(nullLFlist));\n'
    '\tcbHostLFList->addItem(gdeckManager->_lfList[nullLFlist].listName.data(), gdeckManager->_lfList[nullLFlist].hash);\n'
    '\tcbHostLFList->setSelected(prev);\n'
    '\t}\n'
    '\tprev = cbHostLFList->getSelected();\n'))

# ---------------------------------------------------------------- deck editor: modern mechanics
R.append(patch('game.cpp',
    '\t\t{1077, DeckBuilder::CARD_TYPE_FILTER_SKILL},\n', ''))
R.append(patch('game.cpp',
    'std::array<std::pair<uint32_t, DeckBuilder::CARD_TYPE_FILTER>, 5> items{ {',
    'std::array<std::pair<uint32_t, DeckBuilder::CARD_TYPE_FILTER>, 4> items{ { // JTP: no Skill cards'))
for line in [
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1063).data(), TYPE_MONSTER + TYPE_SYNCHRO);\n',
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1073).data(), TYPE_MONSTER + TYPE_XYZ);\n',
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1074).data(), TYPE_MONSTER + TYPE_PENDULUM);\n',
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1076).data(), TYPE_MONSTER + TYPE_LINK);\n',
        '\t\tcbCardType2->addItem(epro::format(L"{}|{}", gDataManager->GetSysString(1054), gDataManager->GetSysString(1062)).data(), TYPE_MONSTER + TYPE_NORMAL + TYPE_TUNER);\n',
        '\t\tcbCardType2->addItem(epro::format(L"{}|{}", gDataManager->GetSysString(1054), gDataManager->GetSysString(1074)).data(), TYPE_MONSTER + TYPE_NORMAL + TYPE_PENDULUM);\n',
        '\t\tcbCardType2->addItem(epro::format(L"{}|{}", gDataManager->GetSysString(1063), gDataManager->GetSysString(1062)).data(), TYPE_MONSTER + TYPE_SYNCHRO + TYPE_TUNER);\n',
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1062).data(), TYPE_MONSTER + TYPE_TUNER);\n',
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1065).data(), TYPE_MONSTER + TYPE_MAXIMUM);\n',
        '\t\tcbCardType2->addItem(gDataManager->GetSysString(1076).data(), TYPE_SPELL + TYPE_LINK);\n']:
    R.append(patch('game.cpp', line, ''))
R.append(patch('game.cpp',
    '\tebScale->setTextAlignment(irr::gui::EGUIA_CENTER, irr::gui::EGUIA_CENTER);\n\tstSearch =',
    '\tebScale->setTextAlignment(irr::gui::EGUIA_CENTER, irr::gui::EGUIA_CENTER);\n'
    '\tstScale->setVisible(false); // JTP: no Pendulum scales\n'
    '\tebScale->setVisible(false);\n'
    '\tstSearch ='))
R.append(patch('game.cpp',
    'defaultStrings.emplace_back(btnMarksFilter, 1374);\n',
    'defaultStrings.emplace_back(btnMarksFilter, 1374);\n'
    '\tbtnMarksFilter->setVisible(false); // JTP: no Link markers\n'))
R.append(patch('deck_con.cpp',
    'if (mainGame->cbCardType2->getSelected() == 8) {',
    'if (mainGame->cbCardType2->getItemData(mainGame->cbCardType2->getSelected()) == (TYPE_MONSTER + TYPE_LINK)) { // JTP: by data, items were removed'))

# ---------------------------------------------------------------- never show non-whitelisted cards
R.append(patch('deck_con.cpp',
    'if((filter_lm != LIMITATION_FILTER_NONE || filterList->whitelist) && filter_lm != LIMITATION_FILTER_ALL) {',
    'if(((filter_lm != LIMITATION_FILTER_NONE || filterList->whitelist) && filter_lm != LIMITATION_FILTER_ALL) || filterList->whitelist) { // JTP: whitelist always applies'))

print(R)
