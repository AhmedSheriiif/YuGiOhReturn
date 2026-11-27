"""Game-file integrity check for LAN play (user request 2026-11-26). Idempotent.

In LAN play the HOST runs the duel (its card scripts, card databases and banlists decide everything), so a
player joining a room must be sure the host's files are unmodified. The game fingerprints (MD5) every file that
affects a duel: script/**/*.lua, expansions/**/*.cdb, repositories/**/*.lua|*.cdb, lflists/*.conf and JTP.exe.
The host sends its fingerprint to each joiner (STOC_JTP_INTEGRITY); a joiner whose own fingerprint differs
is disconnected with an explanation. Limit: a host who rebuilds the exe to send a fake fingerprint is not
caught; only a server-run duel (VPS phase) closes that.
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
    raise AssertionError((path, old[:80], s.count(old)))


def append_once(path, marker, text):
    s = io.open(path, encoding='utf-8', newline='').read()
    if marker in s:
        return 'skip'
    nl = '\r\n' if '\r\n' in s else '\n'
    io.open(path, 'w', encoding='utf-8', newline='').write(s.rstrip() + nl + text.replace('\n', nl))
    return 'ok'


R = []
R.append(patch('network.h',
    '#define STOC_HS_WATCH_CHANGE\t0x22\n',
    '#define STOC_HS_WATCH_CHANGE\t0x22\n'
    '#define STOC_JTP_INTEGRITY\t0xe0 // JTP: host -> joiner, 16-byte MD5 fingerprint of the duel-relevant game files\n'))
R.append(patch('utils.h',
    '\t\tstatic const epro::path_string& GetExePath();\n',
    '\t\tstatic const epro::path_string& GetExePath();\n'
    '\t\t// JTP: MD5 of every duel-relevant game file (scripts, card DBs, banlists, exe); computed once.\n'
    '\t\tstatic const std::array<uint8_t, 16>& JtpContentFingerprint();\n'))
R.append(patch('utils.cpp',
    '#include "replay.h"\n',
    '#include "replay.h"\n#include "crypto.h" // JTP: content fingerprint\n#include <filesystem>\n#include <fstream>\n#include <algorithm>\n'))
R.append(append_once('utils.cpp', 'Utils::JtpContentFingerprint()', '''

// JTP: fingerprint of the files that decide a duel. Paths are relative to the game folder (the working
// directory), sorted, and hashed together with their contents, so any edited/added/removed card script,
// card database, banlist or exe changes it.
const std::array<uint8_t, 16>& ygo::Utils::JtpContentFingerprint() {
	static const std::array<uint8_t, 16> fingerprint = [] {
		namespace fs = std::filesystem;
		std::vector<fs::path> files;
		auto add_tree = [&files](const fs::path& root, std::initializer_list<const char*> exts) {
			std::error_code ec;
			if(!fs::is_directory(root, ec))
				return;
			for(fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec), end; !ec && it != end; it.increment(ec)) {
				if(!it->is_regular_file(ec))
					continue;
				auto ext = it->path().extension().string();
				std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
				for(const char* e : exts) {
					if(ext == e) {
						files.push_back(it->path());
						break;
					}
				}
			}
		};
		add_tree("script", { ".lua" });
		add_tree("expansions", { ".cdb" });
		add_tree("repositories", { ".lua", ".cdb" });
		add_tree("lflists", { ".conf" });
		std::sort(files.begin(), files.end());
		files.push_back(fs::path(GetExePath()));
		epro::MD5Context ctx;
		std::vector<char> buffer(1 << 16);
		for(const auto& path : files) {
			auto name = path.generic_string();
			ctx.update(name.data(), name.size() + 1);
			std::ifstream in(path, std::ios::binary);
			while(in) {
				in.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
				if(in.gcount() > 0)
					ctx.update(buffer.data(), static_cast<size_t>(in.gcount()));
			}
		}
		return ctx.final();
	}();
	return fingerprint;
}
'''))

# host: send the fingerprint right after STOC_JOIN_GAME (both the lobby path and the mid-duel spectator path)
SEND = ('\t\t{ // JTP: let the joiner verify this host\'s game files\n'
        '\t\t\tauto fp = Utils::JtpContentFingerprint();\n'
        '\t\t\tNetServer::SendBufferToPlayer(dp, STOC_JTP_INTEGRITY, fp.data(), fp.size());\n'
        '\t\t}\n')
R.append(patch('generic_duel.cpp',
    '\t\tNetServer::SendPacketToPlayer(dp, STOC_JOIN_GAME, scjg);\n\t\tNetServer::SendPacketToPlayer(dp, STOC_TYPE_CHANGE, sctc);\n\t\tdp->type = NETPLAYER_TYPE_OBSERVER;\n',
    '\t\tNetServer::SendPacketToPlayer(dp, STOC_JOIN_GAME, scjg);\n' + SEND +
    '\t\tNetServer::SendPacketToPlayer(dp, STOC_TYPE_CHANGE, sctc);\n\t\tdp->type = NETPLAYER_TYPE_OBSERVER;\n'))
R.append(patch('generic_duel.cpp',
    '\tNetServer::SendPacketToPlayer(dp, STOC_JOIN_GAME, scjg);\n\tNetServer::SendPacketToPlayer(dp, STOC_TYPE_CHANGE, sctc);\n\tIteratePlayers(',
    '\tNetServer::SendPacketToPlayer(dp, STOC_JOIN_GAME, scjg);\n' + SEND.replace('\t\t', '\t', 1).replace('\n\t\t\t', '\n\t\t').replace('\n\t\t}', '\n\t}') +
    '\tNetServer::SendPacketToPlayer(dp, STOC_TYPE_CHANGE, sctc);\n\tIteratePlayers('))

# client: compare, and on mismatch end the session with a clear message
R.append(patch('duelclient.h',
    '\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button\n',
    '\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button\n'
    '\tstatic bool jtp_integrity_failed; // JTP: host\'s game files differ from ours\n'))
R.append(patch('duelclient.cpp',
    'bool DuelClient::jtp_join_as_spectator = false; // JTP\n',
    'bool DuelClient::jtp_join_as_spectator = false; // JTP\nbool DuelClient::jtp_integrity_failed = false; // JTP\n'))
R.append(patch('duelclient.cpp',
    '\tcase STOC_GAME_MSG: {\n\t\tanalyzeMutex.lock();\n',
    '\tcase STOC_JTP_INTEGRITY: { // JTP: refuse hosts whose duel files differ from ours\n'
    '\t\tconst auto& mine = Utils::JtpContentFingerprint();\n'
    '\t\tif(len - 1 >= mine.size() && memcmp(mine.data(), pdata, mine.size()) != 0) {\n'
    '\t\t\tjtp_integrity_failed = true;\n'
    '\t\t\tstd::vector<uint8_t> end_pkt{ INTERNAL_HANDLE_CONNECTION_END, 1 };\n'
    '\t\t\tto_analyze_mutex.lock();\n'
    '\t\t\tto_analyze.push_back(std::move(end_pkt));\n'
    '\t\t\tto_analyze_mutex.unlock();\n'
    '\t\t\tcv.notify_one();\n'
    '\t\t\tevent_base_loopexit(client_base, 0);\n'
    '\t\t}\n'
    '\t\tbreak;\n'
    '\t}\n'
    '\tcase STOC_GAME_MSG: {\n\t\tanalyzeMutex.lock();\n'))
R.append(patch('duelclient.cpp',
    '\t\t\t\tmainGame->wChat->setVisible(false);\n\t\t\t\tif(iseof)\n',
    '\t\t\t\tmainGame->wChat->setVisible(false);\n'
    '\t\t\t\tif(jtp_integrity_failed) { // JTP\n'
    '\t\t\t\t\tjtp_integrity_failed = false;\n'
    '\t\t\t\t\tmainGame->PopupMessage(L"You left this room: the host\'s game files are different from yours.\\n\\n"\n'
    '\t\t\t\t\t\tL"Either one of you has an outdated game (restart it to update) or the host\'s files were modified.");\n'
    '\t\t\t\t} else\n'
    '\t\t\t\tif(iseof)\n'))
print(R)
