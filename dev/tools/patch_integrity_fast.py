"""Faster integrity fingerprint (follow-up to patch_integrity.py). Idempotent.

Only card scripts that can actually be played are hashed: c<passcode>.lua for every card on the loaded
banlists (all JTP lists are whitelists, so that is the whole legal pool), plus every non-card script
(rules/utility), the card databases, the banlists and the exe. ~1,300 files instead of ~28,000.
The fingerprint is also computed in the background right after the game starts, so the first join
never waits for it.
"""
import io, os, re
os.chdir(r'D:\YugiohReturn\edopro\gframe')

NEW_FUNC = r'''// JTP: fingerprint of the files that decide a duel. Paths are relative to the game folder (the working
// directory), sorted, and hashed together with their contents. Card scripts are limited to cards that can
// be played (on a loaded banlist); rule/utility scripts, card databases, banlists and the exe are all hashed.
const std::array<uint8_t, 16>& ygo::Utils::JtpContentFingerprint() {
	static const std::array<uint8_t, 16> fingerprint = [] {
		namespace fs = std::filesystem;
		std::set<uint32_t> playable;
		if(gdeckManager) {
			for(const auto& list : gdeckManager->_lfList)
				for(const auto& entry : list.content)
					playable.insert(entry.first);
		}
		auto wanted_script = [&playable](const std::string& file) {
			// c<digits>.lua is a card script: only hash playable cards; anything else is a shared script
			if(file.size() > 5 && file[0] == 'c' && std::all_of(file.begin() + 1, file.end() - 4, [](char c) { return c >= '0' && c <= '9'; })) {
				const auto code = static_cast<uint32_t>(std::strtoul(file.c_str() + 1, nullptr, 10));
				return playable.empty() || playable.count(code) > 0;
			}
			return true;
		};
		std::vector<fs::path> files;
		auto add_tree = [&](const fs::path& root, std::initializer_list<const char*> exts) {
			std::error_code ec;
			if(!fs::is_directory(root, ec))
				return;
			for(fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec), end; !ec && it != end; it.increment(ec)) {
				if(it->is_directory(ec) && it->path().filename() == ".git") {
					it.disable_recursion_pending();
					continue;
				}
				if(!it->is_regular_file(ec))
					continue;
				auto ext = it->path().extension().string();
				std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
				for(const char* e : exts) {
					if(ext == e) {
						if(ext != ".lua" || wanted_script(it->path().filename().string()))
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
		const fs::path exe_path(GetExePath()); // hashed under its file name only (the install folder varies)
		epro::MD5Context ctx;
		std::vector<char> buffer(1 << 16);
		files.push_back(exe_path);
		for(const auto& path : files) {
			auto name = (path == exe_path ? path.filename() : path).generic_string();
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
'''


def replace_func(path):
    s = io.open(path, encoding='utf-8', newline='').read()
    if 'wanted_script' in s:
        return 'skip'
    start = s.index('// JTP: fingerprint of the files that decide a duel.')
    end = s.index('\treturn fingerprint;\n}', start) if '\treturn fingerprint;\n}' in s else s.index('\treturn fingerprint;\r\n}', start)
    end = s.index('}', end + len('\treturn fingerprint;')) + 1
    nl = '\r\n' if '\r\n' in s else '\n'
    s = s[:start] + NEW_FUNC.replace('\n', nl).rstrip() + s[end:]
    if '#include <set>' not in s:
        s = s.replace('#include <algorithm>', '#include <algorithm>' + nl + '#include <set>', 1)
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    return 'ok'


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


R = [replace_func('utils.cpp')]
# warm-up: compute the fingerprint in the background once the card data and banlists are loaded
R.append(patch('gframe.cpp',
    '\t\tupdater.CheckUpdates();\n#if EDOPRO_WINDOWS\n',
    '\t\tupdater.CheckUpdates();\n'
    '\tepro::thread([] { ygo::Utils::JtpContentFingerprint(); }).detach(); // JTP: warm the integrity fingerprint\n'
    '#if EDOPRO_WINDOWS\n'))
R.append(patch('gframe.cpp', '#include "client_updater.h"\n', '#include "client_updater.h"\n#include "epro_thread.h" // JTP\n'))
print(R)
