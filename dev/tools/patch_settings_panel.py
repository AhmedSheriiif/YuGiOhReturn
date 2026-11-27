"""Simple JTP Settings panel (user request 2026-11-26), opened from a main-menu "Settings" button.

Controls reuse EDOPro's own GUI ids (sound/music toggles, volume sliders, fullscreen) and are registered with
MenuHandler::MakeElementSynchronized, so EDOPro's existing handlers apply them and keep them in sync with the
full settings window. Language uses its own id and forwards to gSettings.cbCurrentLocale + ApplyLocale.
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
# ids
R.append(patch('menu_handler.h',
    '\tCOMBOBOX_JTP_BEST_OF, // JTP: Best of 1/3/5 in Host a game\n',
    '\tCOMBOBOX_JTP_BEST_OF, // JTP: Best of 1/3/5 in Host a game\n'
    '\tBUTTON_JTP_SETTINGS, // JTP: main menu Settings button\n'
    '\tBUTTON_JTP_SETTINGS_OK, // JTP: close the Settings panel\n'
    '\tCOMBOBOX_JTP_LANGUAGE, // JTP: language in the Settings panel\n'))
# members
R.append(patch('game.h',
    '\tirr::gui::IGUIComboBox* cbJtpBestOf; // JTP: Best of 1/3/5\n',
    '\tirr::gui::IGUIComboBox* cbJtpBestOf; // JTP: Best of 1/3/5\n'
    '\t// JTP: simple Settings panel\n'
    '\tirr::gui::IGUIButton* btnJtpSettings;\n'
    '\tirr::gui::IGUIWindow* wJtpSettings;\n'
    '\tirr::gui::IGUICheckBox* jtpChkSound;\n'
    '\tirr::gui::IGUIScrollBar* jtpScrSound;\n'
    '\tirr::gui::IGUICheckBox* jtpChkMusic;\n'
    '\tirr::gui::IGUIScrollBar* jtpScrMusic;\n'
    '\tirr::gui::IGUICheckBox* jtpChkFullscreen;\n'
    '\tirr::gui::IGUIComboBox* jtpCbLanguage;\n'))

# main menu button (between Decks and Exit), window grows by 35
R.append(patch('game.cpp',
    '\tdefaultStrings.emplace_back(btnDeckEdit, 1204);\n\toffset += 35;\n',
    '\tdefaultStrings.emplace_back(btnDeckEdit, 1204);\n\toffset += 35;\n'
    '\tbtnJtpSettings = env->addButton(OFFSET(10, 135, 270, 165), wMainMenu, BUTTON_JTP_SETTINGS, L"Settings"); // JTP\n'
    '\toffset += 35;\n'))
R.append(patch('game.cpp',
    'Scale(mainMenuLeftX, 200, mainMenuRightX, 440), false, EDOPRO_VERSION_STRING); // JTP: one button less + credit line',
    'Scale(mainMenuLeftX, 200, mainMenuRightX, 475), false, EDOPRO_VERSION_STRING); // JTP: -Puzzles +Settings +credit line'))
R.append(patch('game.cpp',
    'ResizeWin(mainMenuLeftX, 200, mainMenuRightX, 440)); // JTP: + credit line',
    'ResizeWin(mainMenuLeftX, 200, mainMenuRightX, 475)); // JTP: -Puzzles +Settings +credit line'))

# panel construction at the end of the settings-window builder
R.append(patch('game.cpp',
    '\t\tdefaultStrings.emplace_back(gSettings.chkNativeMouse, 12103);\n#endif\n\t}\n}\n#undef WStr\n',
    '\t\tdefaultStrings.emplace_back(gSettings.chkNativeMouse, 12103);\n#endif\n\t}\n'
    '\t{ // JTP: simple Settings panel\n'
    '\t\twJtpSettings = env->addWindow(Scale(0, 0, 380, 300), false, L"Settings");\n'
    '\t\twJtpSettings->getCloseButton()->setVisible(false);\n'
    '\t\twJtpSettings->setVisible(false);\n'
    '\t\tauto addLabel = [&](uint32_t strid, irr::core::recti rect) {\n'
    '\t\t\tauto st = env->addStaticText(gDataManager->GetSysString(strid).data(), rect, false, false, wJtpSettings);\n'
    '\t\t\tst->setTextAlignment(irr::gui::EGUIA_UPPERLEFT, irr::gui::EGUIA_CENTER);\n'
    '\t\t\tdefaultStrings.emplace_back(st, strid);\n'
    '\t\t};\n'
    '\t\tauto addVolume = [&](int id, int pos, irr::core::recti rect) {\n'
    '\t\t\tauto scr = env->addScrollBar(true, rect, wJtpSettings, id);\n'
    '\t\t\tscr->setMax(100);\n'
    '\t\t\tscr->setMin(0);\n'
    '\t\t\tscr->setPos(pos);\n'
    '\t\t\tscr->setLargeStep(5);\n'
    '\t\t\tscr->setSmallStep(1);\n'
    '\t\t\tmenuHandler.MakeElementSynchronized(scr);\n'
    '\t\t\treturn scr;\n'
    '\t\t};\n'
    '\t\tjtpChkSound = env->addCheckBox(gGameConfig->enablesound, Scale(20, 35, 360, 60), wJtpSettings, CHECKBOX_ENABLE_SOUND, gDataManager->GetSysString(2047).data());\n'
    '\t\tmenuHandler.MakeElementSynchronized(jtpChkSound);\n'
    '\t\tdefaultStrings.emplace_back(jtpChkSound, 2047);\n'
    '\t\taddLabel(2049, Scale(40, 62, 120, 85));\n'
    '\t\tjtpScrSound = addVolume(SCROLL_SOUND_VOLUME, gGameConfig->soundVolume, Scale(125, 65, 360, 82));\n'
    '\t\tjtpChkMusic = env->addCheckBox(gGameConfig->enablemusic, Scale(20, 95, 360, 120), wJtpSettings, CHECKBOX_ENABLE_MUSIC, gDataManager->GetSysString(2046).data());\n'
    '\t\tmenuHandler.MakeElementSynchronized(jtpChkMusic);\n'
    '\t\tdefaultStrings.emplace_back(jtpChkMusic, 2046);\n'
    '\t\taddLabel(2048, Scale(40, 122, 120, 145));\n'
    '\t\tjtpScrMusic = addVolume(SCROLL_MUSIC_VOLUME, gGameConfig->musicVolume, Scale(125, 125, 360, 142));\n'
    '\t\tjtpChkFullscreen = env->addCheckBox(gGameConfig->fullscreen, Scale(20, 160, 360, 185), wJtpSettings, CHECKBOX_FULLSCREEN, gDataManager->GetSysString(2060).data());\n'
    '\t\tmenuHandler.MakeElementSynchronized(jtpChkFullscreen);\n'
    '\t\tdefaultStrings.emplace_back(jtpChkFullscreen, 2060);\n'
    '\t\taddLabel(2067, Scale(20, 197, 120, 220));\n'
    '\t\tjtpCbLanguage = AddComboBox(env, Scale(125, 195, 360, 220), wJtpSettings, COMBOBOX_JTP_LANGUAGE);\n'
    '\t\tfor(irr::u32 i = 0; i < gSettings.cbCurrentLocale->getItemCount(); ++i)\n'
    '\t\t\tjtpCbLanguage->addItem(gSettings.cbCurrentLocale->getItem(i));\n'
    '\t\tjtpCbLanguage->setSelected(gSettings.cbCurrentLocale->getSelected());\n'
    '\t\tauto more = env->addButton(Scale(20, 250, 210, 280), wJtpSettings, BUTTON_SHOW_SETTINGS, gDataManager->GetSysString(2059).data());\n'
    '\t\tdefaultStrings.emplace_back(more, 2059);\n'
    '\t\tauto ok = env->addButton(Scale(230, 250, 360, 280), wJtpSettings, BUTTON_JTP_SETTINGS_OK, gDataManager->GetSysString(1211).data());\n'
    '\t\tdefaultStrings.emplace_back(ok, 1211);\n'
    '\t}\n'
    '}\n#undef WStr\n'))
R.append(patch('game.cpp',
    '\tSetCentered(gSettings.window);\n',
    '\tSetCentered(gSettings.window);\n\tSetCentered(wJtpSettings); // JTP\n'))

# handlers: open / close / language
R.append(patch('menu_handler.cpp',
    '\t\t\tcase BUTTON_DECK_EDIT: {\n',
    '\t\t\tcase BUTTON_JTP_SETTINGS: { // JTP: refresh from current config, then show the panel\n'
    '\t\t\t\tmainGame->jtpChkSound->setChecked(gGameConfig->enablesound);\n'
    '\t\t\t\tmainGame->jtpScrSound->setPos(gGameConfig->soundVolume);\n'
    '\t\t\t\tmainGame->jtpChkMusic->setChecked(gGameConfig->enablemusic);\n'
    '\t\t\t\tmainGame->jtpScrMusic->setPos(gGameConfig->musicVolume);\n'
    '\t\t\t\tmainGame->jtpChkFullscreen->setChecked(gGameConfig->fullscreen);\n'
    '\t\t\t\tmainGame->jtpCbLanguage->setSelected(mainGame->gSettings.cbCurrentLocale->getSelected());\n'
    '\t\t\t\tmainGame->PopupElement(mainGame->wJtpSettings);\n'
    '\t\t\t\tmainGame->env->setFocus(mainGame->wJtpSettings);\n'
    '\t\t\t\tbreak;\n'
    '\t\t\t}\n'
    '\t\t\tcase BUTTON_JTP_SETTINGS_OK: {\n'
    '\t\t\t\tmainGame->HideElement(mainGame->wJtpSettings);\n'
    '\t\t\t\tbreak;\n'
    '\t\t\t}\n'
    '\t\t\tcase BUTTON_DECK_EDIT: {\n'))
R.append(patch('menu_handler.cpp',
    '\t\t\tcase COMBOBOX_JTP_BEST_OF: { // JTP: Best of 1/3/5 -> hidden best-of field\n',
    '\t\t\tcase COMBOBOX_JTP_LANGUAGE: { // JTP: same as choosing the language in the full settings window\n'
    '\t\t\t\tconst auto sel = mainGame->jtpCbLanguage->getSelected();\n'
    '\t\t\t\tif(sel >= 0 && sel != mainGame->gSettings.cbCurrentLocale->getSelected()) {\n'
    '\t\t\t\t\tmainGame->gSettings.cbCurrentLocale->setSelected(sel);\n'
    '\t\t\t\t\tmainGame->ApplyLocale(sel);\n'
    '\t\t\t\t}\n'
    '\t\t\t\tbreak;\n'
    '\t\t\t}\n'
    '\t\t\tcase COMBOBOX_JTP_BEST_OF: { // JTP: Best of 1/3/5 -> hidden best-of field\n'))
print(R)
