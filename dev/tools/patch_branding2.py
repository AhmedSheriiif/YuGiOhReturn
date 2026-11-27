"""Second batch of branding edits to D:/YugiohReturn/edopro/gframe (CRLF-safe)."""
import io, re, os
os.chdir(r'D:\YugiohReturn\edopro\gframe')


def edit_re(path, pat, repl):
    s = io.open(path, encoding='utf-8', newline='').read()
    s2, n = re.subn(pat, repl, s, count=1)
    assert n == 1, (path, pat)
    io.open(path, 'w', encoding='utf-8', newline='').write(s2)


edit_re('game.cpp',
        r'addCustomText\(L"Project Ignis: EDOPro\\n"(\r?\n)(\t+)L"The bleeding-edge automatic duel simulator\\n"',
        lambda m: ('addCustomText(L"Yu-Gi-Oh! Joey The Passion\\n"' + m.group(1) + m.group(2) +
                   'L"A fan remake of Yu-Gi-Oh! Power of Chaos: Joey The Passion.\\n"' + m.group(1) + m.group(2) +
                   'L"Based on Project Ignis: EDOPro, the open-source automatic duel simulator.\\n"'))
edit_re('game_config.inl', r'OPTION\(epro::path_string, skin, EPRO_TEXT\("none"\)\)',
        lambda m: 'OPTION(epro::path_string, skin, EPRO_TEXT("Joey The Passion"))')
for old, new in [('"OriginalFilename", "EDOPro.exe"', '"OriginalFilename", "JTP.exe"'),
                 ('"ProductName", "Project Ignis: EDOPro"', '"ProductName", "Yu-Gi-Oh! Joey The Passion"'),
                 ('"CompanyName", "Project Ignis"', '"CompanyName", "JTP project"'),
                 ('"FileDescription", "Project Ignis: EDOPro, the bleeding-edge automatic duel simulator"',
                  '"FileDescription", "Yu-Gi-Oh! Joey The Passion (based on Project Ignis: EDOPro)"')]:
    edit_re('ygopro.rc', re.escape(old), lambda m, new=new: new)
print('ok')
