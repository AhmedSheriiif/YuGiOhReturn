"""Host window + deck editor simplification for JTP (D:/YugiohReturn/edopro/gframe). User requests 2026-11-26.

Host a game:
  - hide Allowed Cards (fixed to OCG/TCG; the JTP whitelist decides legality)
  - always 1v1: hide team sizes + Relay; Best of 1/3/5 picked from a dropdown
  - hide Rule (always Master Rule 1) and the four checkboxes (forced to their defaults: off)
  - Deck Options and Custom Rule tabs moved to a hidden tab control (controls stay valid)
  - remaining rows moved up so there are no gaps
Deck editor:
  - hide alternate artworks (only the exact whitelisted code is listed, the one with JTP art)
  - Attribute filter without Divine; Type filter limited to the 20 JTP monster types
Idempotent.
"""
import io, os
os.chdir(r'D:\YugiohReturn\edopro\gframe')


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
# ---------------------------------------------------------------- hidden tabs
R.append(patch('game.cpp',
    '\twCreateHost = wtcCreateHost->getWindow();\n',
    '\twCreateHost = wtcCreateHost->getWindow();\n'
    '\t// JTP: Deck Options / Custom Rule tabs live on a hidden tab control (their controls stay valid, defaults apply)\n'
    '\tauto jtpHiddenHostTabs = env->addTabControl(Scale(0, 0, 10, 10), nullptr);\n'
    '\tjtpHiddenHostTabs->setVisible(false);\n'))
R.append(patch('game.cpp',
    'auto tDeckSettings = wtcCreateHost->addTab(gDataManager->GetSysString(12105).data());',
    'auto tDeckSettings = jtpHiddenHostTabs->addTab(gDataManager->GetSysString(12105).data()); // JTP: hidden'))
R.append(patch('game.cpp',
    'auto tCustomRules = wtcCreateHost->addTab(gDataManager->GetSysString(1630).data());',
    'auto tCustomRules = jtpHiddenHostTabs->addTab(gDataManager->GetSysString(1630).data()); // JTP: hidden'))

# ---------------------------------------------------------------- simplified Duel tab
R.append(patch('game.h',
    '\tirr::gui::IGUIButton* btnJoinHost;\n',
    '\tirr::gui::IGUIButton* btnJoinHost;\n\tirr::gui::IGUIComboBox* cbJtpBestOf; // JTP: Best of 1/3/5\n'))
R.append(patch('menu_handler.h',
    '\tBUTTON_JTP_WATCH_HOST, // JTP: join a LAN room as spectator\n',
    '\tBUTTON_JTP_WATCH_HOST, // JTP: join a LAN room as spectator\n\tCOMBOBOX_JTP_BEST_OF, // JTP: Best of 1/3/5 in Host a game\n'))
R.append(patch('game.cpp',
    '\t\tebHostNotes->setVisible(false);\n\n',
    '\t\tebHostNotes->setVisible(false);\n'
    '\t\t{ // JTP: simplified host settings: 1v1, Master Rule 1, defaults for everything else\n'
    '\t\t\tcbJtpBestOf = AddComboBox(env, Scale(140, 65, 300, 90), tDuelSettings, COMBOBOX_JTP_BEST_OF);\n'
    '\t\t\tfor(int bo : { 1, 3, 5 }) {\n'
    '\t\t\t\tauto idx = cbJtpBestOf->addItem(epro::format(L"{} {}", gDataManager->GetSysString(1381), bo).data(), bo);\n'
    '\t\t\t\tif(bo == gGameConfig->bestOf)\n'
    '\t\t\t\t\tcbJtpBestOf->setSelected(idx);\n'
    '\t\t\t}\n'
    '\t\t\tif(gGameConfig->bestOf != 1 && gGameConfig->bestOf != 3 && gGameConfig->bestOf != 5)\n'
    '\t\t\t\tcbJtpBestOf->setSelected(0);\n'
    '\t\t\tebBestOf->setText(epro::to_wstring(cbJtpBestOf->getItemData(cbJtpBestOf->getSelected())).data());\n'
    '\t\t\tfor(irr::gui::IGUIElement* e : { static_cast<irr::gui::IGUIElement*>(cbRule), static_cast<irr::gui::IGUIElement*>(ebTeam1),\n'
    '\t\t\t\t\tstatic_cast<irr::gui::IGUIElement*>(ebTeam2), static_cast<irr::gui::IGUIElement*>(ebBestOf),\n'
    '\t\t\t\t\tstatic_cast<irr::gui::IGUIElement*>(btnRelayMode), static_cast<irr::gui::IGUIElement*>(cbDuelRule),\n'
    '\t\t\t\t\tstatic_cast<irr::gui::IGUIElement*>(chkNoShuffleDeck), static_cast<irr::gui::IGUIElement*>(chkTcgRulings),\n'
    '\t\t\t\t\tstatic_cast<irr::gui::IGUIElement*>(chkNoCheckDeckContent), static_cast<irr::gui::IGUIElement*>(chkNoCheckDeckSize) })\n'
    '\t\t\t\te->setVisible(false);\n'
    '\t\t\tcbRule->setSelected(2); // OCG/TCG\n'
    '\t\t\tebTeam1->setText(L"1");\n'
    '\t\t\tebTeam2->setText(L"1");\n'
    '\t\t\tbtnRelayMode->setPressed(false);\n'
    '\t\t\tchkNoShuffleDeck->setChecked(false);\n'
    '\t\t\tchkTcgRulings->setChecked(false);\n'
    '\t\t\tchkNoCheckDeckContent->setChecked(false);\n'
    '\t\t\tchkNoCheckDeckSize->setChecked(false);\n'
    '\t\t\tconst std::wstring hiddenLabels[] = { gDataManager->GetSysString(1225).data(), gDataManager->GetSysString(1380).data(),\n'
    '\t\t\t\t\t\t\t\t\t\t\t  gDataManager->GetSysString(1381).data(), gDataManager->GetSysString(1236).data() };\n'
    '\t\t\tconst auto row60 = Scale(60), row240 = Scale(240);\n'
    '\t\t\tfor(auto* child : tDuelSettings->getChildren()) {\n'
    '\t\t\t\tif(child->getType() == irr::gui::EGUIET_STATIC_TEXT) {\n'
    '\t\t\t\t\tfor(const auto& label : hiddenLabels)\n'
    '\t\t\t\t\t\tif(label == child->getText())\n'
    '\t\t\t\t\t\t\tchild->setVisible(false);\n'
    '\t\t\t\t}\n'
    '\t\t\t\t// close the gaps: rows 65..95 move up 30, rows from Start LP move up 150\n'
    '\t\t\t\tauto rect = child->getRelativePosition();\n'
    '\t\t\t\tconst auto y = rect.UpperLeftCorner.Y;\n'
    '\t\t\t\tconst int shift = (y >= row240) ? Scale(150) : (y >= row60 ? Scale(30) : 0);\n'
    '\t\t\t\tif(shift) {\n'
    '\t\t\t\t\trect.UpperLeftCorner.Y -= shift;\n'
    '\t\t\t\t\trect.LowerRightCorner.Y -= shift;\n'
    '\t\t\t\t\tchild->setRelativePosition(rect);\n'
    '\t\t\t\t}\n'
    '\t\t\t}\n'
    '\t\t}\n\n'))
R.append(patch('menu_handler.cpp',
    '\t\tcase irr::gui::EGET_COMBO_BOX_CHANGED: {\n\t\t\tswitch (id) {\n',
    '\t\tcase irr::gui::EGET_COMBO_BOX_CHANGED: {\n\t\t\tswitch (id) {\n'
    '\t\t\tcase COMBOBOX_JTP_BEST_OF: { // JTP: Best of 1/3/5 -> hidden best-of field\n'
    '\t\t\t\tauto cb = mainGame->cbJtpBestOf;\n'
    '\t\t\t\tmainGame->ebBestOf->setText(epro::to_wstring(cb->getItemData(cb->getSelected())).data());\n'
    '\t\t\t\tbreak;\n'
    '\t\t\t}\n'))

# ---------------------------------------------------------------- deck editor
R.append(patch('deck_con.cpp',
    '\t\tauto flit = filterList->GetLimitationIterator(&data._data);\n\t\tint count = 3;\n',
    '\t\tauto flit = filterList->GetLimitationIterator(&data._data);\n'
    '\t\tif(filterList->whitelist && flit != filterList->content.end() && flit->first != data._data.code)\n'
    '\t\t\treturn false; // JTP: hide alternate artworks, list only the exact whitelisted card\n'
    '\t\tint count = 3;\n'))
R.append(patch('game.cpp',
    'for (uint32_t filter = 0x1, i = 1010; filter <= ATTRIBUTE_DIVINE; filter <<= 1, i++)',
    'for (uint32_t filter = 0x1, i = 1010; filter < ATTRIBUTE_DIVINE; filter <<= 1, i++) // JTP: no Divine'))
R.append(patch('game.cpp',
    '\tstatic constexpr auto CURRENTLY_KNOWN_RACES = 32;\n'
    '\tuint32_t i = 0;\n'
    '\tfor(; i < CURRENTLY_KNOWN_RACES; ++i)\n'
    '\t\tcbRace->addItem(gDataManager->GetSysString(gDataManager->GetRaceStringIndex(i)).data(), i + 1);\n'
    '\tfor(; i < 64; ++i) {\n'
    '\t\tauto idx = gDataManager->GetRaceStringIndex(i);\n'
    '\t\tif(gDataManager->HasSysString(idx))\n'
    '\t\t\tcbRace->addItem(gDataManager->GetSysString(idx).data(), i + 1);\n'
    '\t}\n',
    '\t// JTP: only the 20 monster types that exist in Joey The Passion (Warrior .. Reptile = bits 0..19)\n'
    '\tstatic constexpr uint32_t JTP_RACES = 20;\n'
    '\tfor(uint32_t i = 0; i < JTP_RACES; ++i)\n'
    '\t\tcbRace->addItem(gDataManager->GetSysString(gDataManager->GetRaceStringIndex(i)).data(), i + 1);\n'))
print(R)
