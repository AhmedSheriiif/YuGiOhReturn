"""Spectator improvements for the JTP client (D:/YugiohReturn/edopro/gframe).  User request 2026-11-26.

1. LAN room list shows each room's state: "[Waiting: name]" or "[DUELING: A vs B | N watching]",
   plus a "Watch" button that joins any room as a spectator (before or during the duel).
   - the LAN broadcast reply gets a small appended JTPHostStatus block (magic-tagged, so the
     original HostPacket layout is untouched).
2. Late spectators (joining mid-duel) now update the spectator count for everyone.
3. Duel HUD: spectators see a "SPECTATING  A vs B | N watching" banner; duelists see "N watching".
Idempotent: every edit is skipped if already applied.
"""
import io, os, re
os.chdir(r'D:\YugiohReturn\edopro\gframe')


def patch(path, old, new):
    s = io.open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    old_n, new_n = old.replace('\n', nl), new.replace('\n', nl)
    if new_n in s:
        return 'skip'
    assert s.count(old_n) == 1, (path, old[:80], s.count(old_n))
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(old_n, new_n))
    return 'ok'


R = []
# ------------------------------------------------------------ protocol: status block + accessors
R.append(patch('network.h',
    'struct HostRequest {\n\tuint16_t identifier;\n};\n',
    'struct HostRequest {\n\tuint16_t identifier;\n};\n'
    '// JTP: appended after HostPacket in LAN broadcast replies (room state for the room list)\n'
    '#define JTP_STATUS_MAGIC 0x4A54\n'
    'struct JTPHostStatus {\n'
    '\tuint16_t magic;\n'
    '\tuint8_t duel_stage;\n'
    '\tuint8_t reserved;\n'
    '\tuint16_t watchers;\n'
    '\tuint16_t player1[20];\n'
    '\tuint16_t player2[20];\n'
    '};\n'))
R.append(patch('network.h',
    '\tvirtual void EndDuel() = 0;\n',
    '\tvirtual void EndDuel() = 0;\n'
    '\t// JTP: room status for LAN room list\n'
    '\tvirtual uint16_t JTPObserverCount() const { return 0; }\n'
    '\tvirtual void JTPDuelistNames(uint16_t* p1, uint16_t* p2) const { (void)p1; (void)p2; }\n'))
R.append(patch('generic_duel.h',
    '\tvoid ToObserver(DuelPlayer* dp) override;\n',
    '\tvoid ToObserver(DuelPlayer* dp) override;\n'
    '\tuint16_t JTPObserverCount() const override { return static_cast<uint16_t>(observers.size()); } // JTP\n'
    '\tvoid JTPDuelistNames(uint16_t* p1, uint16_t* p2) const override; // JTP\n'))
s = io.open('generic_duel.cpp', encoding='utf-8', newline='').read()
if 'GenericDuel::JTPDuelistNames' not in s:
    nl = '\r\n' if '\r\n' in s else '\n'
    s += nl.join(['', '// JTP: first duelist of each team, for the LAN room list',
                  'void ygo::GenericDuel::JTPDuelistNames(uint16_t* p1, uint16_t* p2) const {',
                  '\tif(!players.home.empty() && players.home.front().player)',
                  '\t\tmemcpy(p1, players.home.front().player->name, sizeof(uint16_t) * 20);',
                  '\tif(!players.opposing.empty() && players.opposing.front().player)',
                  '\t\tmemcpy(p2, players.opposing.front().player->name, sizeof(uint16_t) * 20);',
                  '}', ''])
    io.open('generic_duel.cpp', 'w', encoding='utf-8', newline='').write(s); R.append('ok')
else:
    R.append('skip')

# late spectator -> broadcast new count
R.append(patch('generic_duel.cpp',
    '\t\tCatchup(dp);\n\t\treturn;\n',
    '\t\tCatchup(dp);\n'
    '\t\t{ // JTP: a late spectator joined mid-duel, update everyone\'s spectator count\n'
    '\t\t\tSTOC_HS_WatchChange scwc;\n'
    '\t\t\tscwc.watch_count = (uint16_t)observers.size();\n'
    '\t\t\tNetServer::SendPacketToPlayer(nullptr, STOC_HS_WATCH_CHANGE, scwc);\n'
    '\t\t\tResendToAll();\n'
    '\t\t}\n'
    '\t\treturn;\n'))

# server: append status to broadcast reply
R.append(patch('netserver.cpp',
    '\t\tBufferIO::EncodeUTF16(duel_mode->name, hp.name, 20);\n'
    '\t\tsendto(fd, (const char*)&hp, sizeof(HostPacket), 0, (sockaddr*)&bc_addr, bc_addr.ss_family == AF_INET ? sizeof(sockaddr_in) : sizeof(sockaddr_in6));\n',
    '\t\tBufferIO::EncodeUTF16(duel_mode->name, hp.name, 20);\n'
    '\t\tstruct { HostPacket hp; JTPHostStatus st; } jtp_pkt{}; // JTP: room status appended\n'
    '\t\tjtp_pkt.hp = hp;\n'
    '\t\tjtp_pkt.st.magic = JTP_STATUS_MAGIC;\n'
    '\t\tjtp_pkt.st.duel_stage = static_cast<uint8_t>(duel_mode->duel_stage);\n'
    '\t\tjtp_pkt.st.watchers = duel_mode->JTPObserverCount();\n'
    '\t\tduel_mode->JTPDuelistNames(jtp_pkt.st.player1, jtp_pkt.st.player2);\n'
    '\t\tsendto(fd, (const char*)&jtp_pkt, sizeof(jtp_pkt), 0, (sockaddr*)&bc_addr, bc_addr.ss_family == AF_INET ? sizeof(sockaddr_in) : sizeof(sockaddr_in6));\n'))

# client: read status, show it in the room list
R.append(patch('duelclient.cpp',
    '\t\tHostPacket packet{};\n'
    '\t\tint ret = recvfrom(fd, reinterpret_cast<char*>(&packet), sizeof(packet), 0, (sockaddr*)&bc_addr, &sz);\n'
    '\t\tif(ret < static_cast<int>(sizeof(HostPacket)))\n'
    '\t\t\treturn;\n',
    '\t\tstruct { HostPacket hp; JTPHostStatus st; } jtp_pkt{}; // JTP: optional room status after HostPacket\n'
    '\t\tint ret = recvfrom(fd, reinterpret_cast<char*>(&jtp_pkt), sizeof(jtp_pkt), 0, (sockaddr*)&bc_addr, &sz);\n'
    '\t\tif(ret < static_cast<int>(sizeof(HostPacket)))\n'
    '\t\t\treturn;\n'
    '\t\tHostPacket& packet = jtp_pkt.hp;\n'
    '\t\tconst bool jtp_has_status = ret >= static_cast<int>(sizeof(jtp_pkt)) && jtp_pkt.st.magic == JTP_STATUS_MAGIC;\n'))
R.append(patch('duelclient.cpp',
    '\t\t\tmainGame->lstHostList->addItem(hoststr.data());\n',
    '\t\t\tif(jtp_has_status) { // JTP: room state first, so in-progress duels are easy to spot\n'
    '\t\t\t\twchar_t n1[20], n2[20];\n'
    '\t\t\t\tBufferIO::DecodeUTF16(jtp_pkt.st.player1, n1, 20);\n'
    '\t\t\t\tBufferIO::DecodeUTF16(jtp_pkt.st.player2, n2, 20);\n'
    '\t\t\t\tstd::wstring status;\n'
    '\t\t\t\tif(jtp_pkt.st.duel_stage == DUEL_STAGE_BEGIN)\n'
    '\t\t\t\t\tstatus = n1[0] ? epro::format(L"[Waiting: {}] ", n1) : std::wstring(L"[Waiting] ");\n'
    '\t\t\t\telse\n'
    '\t\t\t\t\tstatus = epro::format(L"[DUELING: {} vs {} | {} watching] ", n1, n2, jtp_pkt.st.watchers);\n'
    '\t\t\t\thoststr = status + hoststr;\n'
    '\t\t\t}\n'
    '\t\t\tmainGame->lstHostList->addItem(hoststr.data());\n'))

# ------------------------------------------------------------ Watch button
R.append(patch('menu_handler.h',
    '\tDONT_SHUFFLE_DECK,\n};\n',
    '\tDONT_SHUFFLE_DECK,\n\tBUTTON_JTP_WATCH_HOST, // JTP: join a LAN room as spectator\n};\n'))
R.append(patch('game.h',
    '\tirr::gui::IGUIButton* btnJoinHost;\n',
    '\tirr::gui::IGUIButton* btnJoinHost;\n\tirr::gui::IGUIButton* btnWatchHost; // JTP\n'))
R.append(patch('game.cpp',
    '\tdefaultStrings.emplace_back(btnLanRefresh, 1217);\n',
    '\tdefaultStrings.emplace_back(btnLanRefresh, 1217);\n'
    '\tbtnWatchHost = env->addButton(Scale(350, 325, 450, 350), wLanWindow, BUTTON_JTP_WATCH_HOST, L"Watch"); // JTP\n'))
R.append(patch('game.cpp',
    '\twhile(!restart && device->run()) {\n\t\tDispatchQueue();\n',
    '\twhile(!restart && device->run()) {\n\t\tDispatchQueue();\n'
    '\t\tbtnWatchHost->setEnabled(btnJoinHost->isEnabled()); // JTP: Watch follows Join\n'))
R.append(patch('menu_handler.cpp',
    '\t\t\tcase BUTTON_JOIN_HOST: {\n\t\t\t\ttry {\n',
    '\t\t\tcase BUTTON_JTP_WATCH_HOST:\n'
    '\t\t\tcase BUTTON_JOIN_HOST: {\n'
    '\t\t\t\tDuelClient::jtp_join_as_spectator = (id == BUTTON_JTP_WATCH_HOST); // JTP\n'
    '\t\t\t\ttry {\n'))
R.append(patch('menu_handler.cpp',
    '\t\t\tcase BUTTON_JOIN_HOST2: {\n',
    '\t\t\tcase BUTTON_JOIN_HOST2: {\n\t\t\t\tDuelClient::jtp_join_as_spectator = false; // JTP\n'))
R.append(patch('menu_handler.cpp',
    '\t\tcase irr::gui::EGET_LISTBOX_SELECTED_AGAIN: {\n\t\t\tswitch(id) {\n\t\t\tcase LISTBOX_LAN_HOST: {\n',
    '\t\tcase irr::gui::EGET_LISTBOX_SELECTED_AGAIN: {\n\t\t\tswitch(id) {\n\t\t\tcase LISTBOX_LAN_HOST: {\n'
    '\t\t\t\tDuelClient::jtp_join_as_spectator = false; // JTP: double-click joins as player\n'))
R.append(patch('duelclient.h',
    '\tstatic int GetSpectatorsCount() {\n',
    '\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button (public)\n\tstatic int GetSpectatorsCount() {\n'))
R.append(patch('duelclient.cpp',
    'uint32_t DuelClient::watching = 0;\n',
    'uint32_t DuelClient::watching = 0;\nbool DuelClient::jtp_join_as_spectator = false; // JTP\n'))
R.append(patch('duelclient.cpp',
    '\t\tis_host = ((pkt.type >> 4) & 0xf) != 0;\n',
    '\t\tis_host = ((pkt.type >> 4) & 0xf) != 0;\n'
    '\t\tif(jtp_join_as_spectator) { // JTP: Watch button, move to a spectator seat right after joining\n'
    '\t\t\tjtp_join_as_spectator = false;\n'
    '\t\t\tif(selftype < mainGame->dInfo.team1 + mainGame->dInfo.team2)\n'
    '\t\t\t\tSendPacketToServer(CTOS_HS_TOOBSERVER);\n'
    '\t\t}\n'))

# ------------------------------------------------------------ duel HUD
R.append(patch('drawing.cpp',
    '\tDrawShadowText(lpcFont, gDataManager->GetNumString(dInfo.turn), Resize(635, 5, 685, 40), Resize(0, 0, 2, 0), skin::DUELFIELD_TURN_COUNT_VAL, 0x80000000, true);\n',
    '\tDrawShadowText(lpcFont, gDataManager->GetNumString(dInfo.turn), Resize(635, 5, 685, 40), Resize(0, 0, 2, 0), skin::DUELFIELD_TURN_COUNT_VAL, 0x80000000, true);\n'
    '\t// JTP: spectator HUD\n'
    '\tif(!dInfo.isReplay && !dInfo.isSingleMode) {\n'
    '\t\tconst auto watchers = DuelClient::GetSpectatorsCount();\n'
    '\t\tif(dInfo.player_type == 7) {\n'
    '\t\t\tconst std::wstring s1 = self.empty() ? std::wstring() : self.front();\n'
    '\t\t\tconst std::wstring s2 = oppo.empty() ? std::wstring() : oppo.front();\n'
    '\t\t\tconst auto banner = epro::format(L"SPECTATING     {}  vs  {}     |     {} watching", s1, s2, watchers);\n'
    '\t\t\tconst auto rect = Resize(420, 56, 900, 78);\n'
    '\t\t\tdriver->draw2DRectangle(0xc0101c40, rect);\n'
    '\t\t\tdriver->draw2DRectangleOutline(rect, 0xffffc428);\n'
    '\t\t\tDrawShadowText(textFont, banner, rect, Resize(1, 1, 1, 1), 0xffffc428, 0xff000000, true, true);\n'
    '\t\t} else if(watchers > 0) {\n'
    '\t\t\tDrawShadowText(textFont, epro::format(L"{} watching", watchers), Resize(600, 40, 720, 56), Resize(1, 1, 1, 1), 0xffd0d0d0, 0xff000000, true, true);\n'
    '\t\t}\n'
    '\t}\n'))
print(R)
