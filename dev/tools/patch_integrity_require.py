"""Integrity check, part 3: the joiner REQUIRES the host's fingerprint (follow-up to patch_integrity.py).

The host sends STOC_JOIN_GAME, STOC_JTP_INTEGRITY, STOC_TYPE_CHANGE in that order. A modified host could
simply skip the fingerprint, so when STOC_TYPE_CHANGE arrives without a matching fingerprint the joiner
leaves the same way as on a mismatch. Idempotent.
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
R.append(patch('duelclient.h',
    "\tstatic bool jtp_integrity_failed; // JTP: host's game files differ from ours\n",
    "\tstatic bool jtp_integrity_failed; // JTP: host's game files differ from ours\n"
    "\tstatic bool jtp_integrity_ok; // JTP: host's fingerprint received and matching\n"
    "\tstatic void JtpLeaveForIntegrity(); // JTP: end the session with the integrity message\n"))
R.append(patch('duelclient.cpp',
    'bool DuelClient::jtp_integrity_failed = false; // JTP\n',
    'bool DuelClient::jtp_integrity_failed = false; // JTP\n'
    'bool DuelClient::jtp_integrity_ok = false; // JTP\n'))
# reset per connection
R.append(patch('duelclient.cpp',
    'bool DuelClient::StartClient(const epro::Address& ip, uint16_t port, uint32_t gameid, bool create_game) {\n\tif(connect_state)\n\t\treturn false;\n',
    'bool DuelClient::StartClient(const epro::Address& ip, uint16_t port, uint32_t gameid, bool create_game) {\n\tif(connect_state)\n\t\treturn false;\n'
    '\tjtp_integrity_ok = false; // JTP: every new connection must receive the host\'s fingerprint again\n'
    '\tjtp_integrity_failed = false;\n'))
# mismatch handling -> shared helper; match -> ok
R.append(patch('duelclient.cpp',
    '\t\tif(len - 1 >= mine.size() && memcmp(mine.data(), pdata, mine.size()) != 0) {\n'
    '\t\t\tjtp_integrity_failed = true;\n'
    '\t\t\tstd::vector<uint8_t> end_pkt{ INTERNAL_HANDLE_CONNECTION_END, 1 };\n'
    '\t\t\tto_analyze_mutex.lock();\n'
    '\t\t\tto_analyze.push_back(std::move(end_pkt));\n'
    '\t\t\tto_analyze_mutex.unlock();\n'
    '\t\t\tcv.notify_one();\n'
    '\t\t\tevent_base_loopexit(client_base, 0);\n'
    '\t\t}\n'
    '\t\tbreak;\n',
    '\t\tif(len - 1 >= mine.size() && memcmp(mine.data(), pdata, mine.size()) == 0)\n'
    '\t\t\tjtp_integrity_ok = true;\n'
    '\t\telse\n'
    '\t\t\tJtpLeaveForIntegrity();\n'
    '\t\tbreak;\n'))
# require it before the first type change
R.append(patch('duelclient.cpp',
    '\t\tis_host = ((pkt.type >> 4) & 0xf) != 0;\n\t\tif(jtp_join_as_spectator) {',
    '\t\tis_host = ((pkt.type >> 4) & 0xf) != 0;\n'
    '\t\tif(!jtp_integrity_ok) { // JTP: the host never proved its game files: leave\n'
    '\t\t\tif(!jtp_integrity_failed)\n'
    '\t\t\t\tJtpLeaveForIntegrity();\n'
    '\t\t\tbreak;\n'
    '\t\t}\n'
    '\t\tif(jtp_join_as_spectator) {'))
# the helper itself, right before StartClient
R.append(patch('duelclient.cpp',
    'bool DuelClient::StartClient(const epro::Address& ip, uint16_t port, uint32_t gameid, bool create_game) {\n',
    '// JTP: leave the room because the host\'s game files could not be verified. Queues the same internal\n'
    '// "connection ended" event a real disconnect produces, so the normal lobby cleanup runs (with our message).\n'
    'void DuelClient::JtpLeaveForIntegrity() {\n'
    '\tif(jtp_integrity_failed)\n'
    '\t\treturn;\n'
    '\tjtp_integrity_failed = true;\n'
    '\tstd::vector<uint8_t> end_pkt{ 0 /* INTERNAL_HANDLE_CONNECTION_END, defined further down */, 1 };\n'
    '\tto_analyze_mutex.lock();\n'
    '\tto_analyze.push_back(std::move(end_pkt));\n'
    '\tto_analyze_mutex.unlock();\n'
    '\tcv.notify_one();\n'
    '\tevent_base_loopexit(client_base, 0);\n'
    '}\n'
    'bool DuelClient::StartClient(const epro::Address& ip, uint16_t port, uint32_t gameid, bool create_game) {\n'))
print(R)
