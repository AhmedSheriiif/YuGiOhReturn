"""Rename the game to "YuGiOh Return" (exe YuGiOhReturn.exe), point the updater at the YuGiOhReturn GitHub
repo, and turn automatic monster / spell-trap placement on by default.

Idempotent: run it after the other patch_*.py scripts (build_pc.ps1 does this). Each edit is skipped when the
new text is already present. The version number is NOT set here: edit JTP_VERSION_* in gframe/config.h.
"""
import io, os, sys

ENGINE = os.environ.get('YGR_ENGINE', r'D:\YugiohReturn\edopro')
G = os.path.join(ENGINE, 'gframe')

EDITS = {
    'config.h': [
        ('// Override at launch with: JTP.exe -u <url>', '// Override at launch with: YuGiOhReturn.exe -u <url>'),
        ('"https://raw.githubusercontent.com/AhmedSheriiif/jtp-game-updates/main/updates"',
         '"https://raw.githubusercontent.com/AhmedSheriiif/YuGiOhReturn/main/updates"'),
        ('#define JTP_GAME_TITLE L"Yu-Gi-Oh! Joey The Passion"', '#define JTP_GAME_TITLE L"YuGiOh Return"'),
        ('#define EDOPRO_VERSION_STRING L"Yu-Gi-Oh! Joey The Passion | v"', '#define EDOPRO_VERSION_STRING L"YuGiOh Return | v"'),
    ],
    'duelclient.cpp': [
        ('L"This room uses Yu-Gi-Oh! Joey The Passion v{}.{}.', 'L"This room uses YuGiOh Return v{}.{}.'),
    ],
    'game.cpp': [
        ('addCustomText(L"Yu-Gi-Oh! Joey The Passion\\n"', 'addCustomText(L"YuGiOh Return\\n"'),
    ],
    'game_config.inl': [
        ('OPTION(epro::path_string, skin, EPRO_TEXT("Joey The Passion"))', 'OPTION(epro::path_string, skin, EPRO_TEXT("YuGiOh Return"))'),
        ('OPTION_ALIASED(bool, chkMAutoPos, automonsterpos, false)', 'OPTION_ALIASED(bool, chkMAutoPos, automonsterpos, true)'),
        ('OPTION_ALIASED(bool, chkSTAutoPos, autospellpos, false)', 'OPTION_ALIASED(bool, chkSTAutoPos, autospellpos, true)'),
    ],
    'utils.cpp': [
        ('epro::format("JTP-" OSSTRING', 'epro::format("YuGiOhReturn-" OSSTRING'),
    ],
    'utils_gui.cpp': [
        ('params.WindowCaption = EPRO_TEXT("Yu-Gi-Oh! Joey The Passion");', 'params.WindowCaption = EPRO_TEXT("YuGiOh Return");'),
        ('device->setWindowCaption(L"Yu-Gi-Oh! Joey The Passion");', 'device->setWindowCaption(L"YuGiOh Return");'),
    ],
    'ygopro.rc': [
        ('VALUE "OriginalFilename", "JTP.exe"', 'VALUE "OriginalFilename", "YuGiOhReturn.exe"'),
        ('VALUE "ProductName", "Yu-Gi-Oh! Joey The Passion"', 'VALUE "ProductName", "YuGiOh Return"'),
        ('VALUE "FileDescription", "Yu-Gi-Oh! Joey The Passion - Developed by AhmedSherif',
         'VALUE "FileDescription", "YuGiOh Return - Developed by AhmedSherif'),
    ],
}


def main():
    failed = 0
    for name, edits in EDITS.items():
        path = os.path.join(G, name)
        raw = io.open(path, encoding='utf-8', newline='').read()
        nl = '\r\n' if '\r\n' in raw else '\n'
        text = raw
        for old, new in edits:
            o, n = old.replace('\n', nl), new.replace('\n', nl)
            if n in text:
                continue
            if o not in text:
                print('!! %s: text not found: %s' % (name, old[:70]))
                failed += 1
                continue
            text = text.replace(o, n)
        if text != raw:
            io.open(path, 'w', encoding='utf-8', newline='').write(text)
            print('patched', name)
    if failed:
        sys.exit(1)
    print('YuGiOh Return patch OK')


if __name__ == '__main__':
    main()
