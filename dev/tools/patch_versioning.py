"""Phase 1: JTP versioning + version lock + update-check plumbing (D:/YugiohReturn/edopro/gframe). Idempotent.

- JTP_VERSION_MAJOR/MINOR/PATCH in config.h (bump here for every release).
- Network version: client major = 200 + JTP major, client minor = JTP minor. So JTP never matches stock
  EDOPro (41.x), and different JTP minor versions refuse each other (patch releases stay compatible).
- Version-mismatch popup explains which JTP version the room uses.
- HTTP user agent starts with "JTP-<OS>-<version>"; the update check appends ?v=<version>&os=<OS>.
"""
import io, os
os.chdir(r'D:\YugiohReturn\edopro\gframe')


def patch(path, old, new):
    s = io.open(path, encoding='utf-8', newline='').read()
    # files may have mixed line endings (earlier edits): try CRLF first, then LF
    for nl in ('\r\n', '\n'):
        o, n = old.replace('\n', nl), new.replace('\n', nl)
        if n in s:
            return 'skip'
        if s.count(o) == 1:
            break
    assert s.count(o) == 1, (path, old[:80], s.count(o))
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(o, n))
    return 'ok'


R = []
R.append(patch('config.h',
    '#define JTP_VERSION_STRING "0.1.0"\n',
    '// JTP release version: bump for every release. MINOR changes are network-breaking, PATCH ones are not.\n'
    '#define JTP_VERSION_MAJOR 0\n'
    '#define JTP_VERSION_MINOR 1\n'
    '#define JTP_VERSION_PATCH 0\n'
    '#define JTP_VERSION_STRING STR(JTP_VERSION_MAJOR) "." STR(JTP_VERSION_MINOR) "." STR(JTP_VERSION_PATCH)\n'
    '#define JTP_NET_VERSION_BASE 200 // network client major = 200 + JTP major (never equals stock EDOPro)\n'))
R.append(patch('config.h',
    '#define JTP_NET_VERSION_BASE 200 // network client major = 200 + JTP major (never equals stock EDOPro)\n',
    '#define JTP_NET_VERSION_BASE 200 // network client major = 200 + JTP major (never equals stock EDOPro)\n'
    '// JTP: static update index on GitHub (no website involved). The game fetches <UPDATE_URL>/<version>.json,\n'
    '// a JSON array of {name,url,md5} update zips; no file (404) = up to date. Written by tools/make_release.py.\n'
    '// Override at launch with: JTP.exe -u <url>\n'
    '#ifndef UPDATE_URL\n'
    '#define UPDATE_URL "https://raw.githubusercontent.com/AhmedSheriiif/jtp-game-updates/main/updates"\n'
    '#endif\n'))
R.append(patch('config.h',
    '#define CLIENT_VERSION ((EDOPRO_VERSION_MAJOR & 0xff) | ((EDOPRO_VERSION_MINOR & 0xff) << 8) | ((OCG_VERSION_MAJOR & 0xff) << 16) | ((OCG_VERSION_MINOR & 0xff) << 24))',
    '#define CLIENT_VERSION (((JTP_NET_VERSION_BASE + JTP_VERSION_MAJOR) & 0xff) | ((JTP_VERSION_MINOR & 0xff) << 8) | ((OCG_VERSION_MAJOR & 0xff) << 16) | ((OCG_VERSION_MINOR & 0xff) << 24)) // JTP'))
R.append(patch('utils.cpp',
    'static const std::string agent = epro::format("EDOPro-" OSSTRING "-" STR(EDOPRO_VERSION_MAJOR) "." STR(EDOPRO_VERSION_MINOR) "." STR(EDOPRO_VERSION_PATCH)" {}",',
    'static const std::string agent = epro::format("JTP-" OSSTRING "-" JTP_VERSION_STRING " (EDOPro " STR(EDOPRO_VERSION_MAJOR) "." STR(EDOPRO_VERSION_MINOR) "." STR(EDOPRO_VERSION_PATCH) ") {}", // JTP'))
R.append(patch('client_updater.cpp',
    '\tif(curlPerform(update_url.data(), &payload) != CURLE_OK)\n\t\treturn;\n',
    '\t// JTP: static update index (GitHub). <UPDATE_URL>/<this version>.json lists the update zips this\n'
    '\t// version still needs, oldest first. A missing file (HTTP 404) means "up to date".\n'
    '\tauto url = update_url;\n'
    '\tif(!url.empty() && url.back() != \'/\')\n'
    '\t\turl += \'/\';\n'
    '\turl += JTP_VERSION_STRING ".json";\n'
    '\tif(curlPerform(url.data(), &payload) != CURLE_OK)\n\t\treturn;\n'))
R.append(patch('duelclient.cpp',
    '\t\t\t\t\tauto version = BufferIO::getStruct<VersionError>(pdata, len).version;\n'
    '\t\t\t\t\tmainGame->PopupMessage(epro::format(gDataManager->GetSysString(1423),\n'
    '\t\t\t\t\t\t\t\t\t\t\t\t\t   version.client.major, version.client.minor,\n'
    '\t\t\t\t\t\t\t\t\t\t\t\t\t   version.core.major, version.core.minor));\n',
    '\t\t\t\t\tauto version = BufferIO::getStruct<VersionError>(pdata, len).version;\n'
    '\t\t\t\t\tif(version.client.major >= JTP_NET_VERSION_BASE) // JTP: explain in JTP version terms\n'
    '\t\t\t\t\t\tmainGame->PopupMessage(epro::format(L"This room uses Yu-Gi-Oh! Joey The Passion v{}.{}.\\nYour game is v{}.\\n\\nPlease update: restart the game to get the latest version.",\n'
    '\t\t\t\t\t\t\t\t\t\t\t\t\t\t   version.client.major - JTP_NET_VERSION_BASE, version.client.minor, L"" JTP_VERSION_STRING));\n'
    '\t\t\t\t\telse\n'
    '\t\t\t\t\tmainGame->PopupMessage(epro::format(gDataManager->GetSysString(1423),\n'
    '\t\t\t\t\t\t\t\t\t\t\t\t\t   version.client.major, version.client.minor,\n'
    '\t\t\t\t\t\t\t\t\t\t\t\t\t   version.core.major, version.core.minor));\n'))
print(R)
