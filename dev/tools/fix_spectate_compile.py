"""Fix-ups for patch_spectate.py (applied to source and folded into the patch script)."""
import io, os
SRC = r'D:\YugiohReturn\edopro\gframe'
PATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patch_spectate.py')


def rewrite(path, old, new, encoding='utf-8'):
    s = io.open(path, encoding=encoding, newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    o, n = old.replace('\n', nl), new.replace('\n', nl)
    if o in s:
        s = s.replace(o, n)
        io.open(path, 'w', encoding=encoding, newline='').write(s)
        return 'fixed'
    return 'n/a'


# 1) qualify the out-of-namespace definition
print(rewrite(os.path.join(SRC, 'generic_duel.cpp'),
              'void GenericDuel::JTPDuelistNames(', 'void ygo::GenericDuel::JTPDuelistNames('))
print(rewrite(PATCH, "'void GenericDuel::JTPDuelistNames(uint16_t* p1, uint16_t* p2) const {',",
              "'void ygo::GenericDuel::JTPDuelistNames(uint16_t* p1, uint16_t* p2) const {',"))

# 2) jtp_join_as_spectator must be public: declare it next to the public GetSpectatorsCount()
print(rewrite(os.path.join(SRC, 'duelclient.h'),
              '\tstatic uint32_t watching;\n\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button\n',
              '\tstatic uint32_t watching;\n'))
print(rewrite(os.path.join(SRC, 'duelclient.h'),
              '\tstatic int GetSpectatorsCount() {\n',
              '\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button\n\tstatic int GetSpectatorsCount() {\n'))
print(rewrite(PATCH,
    "R.append(patch('duelclient.h',\n"
    "    '\\tstatic uint32_t watching;\\n',\n"
    "    '\\tstatic uint32_t watching;\\n\\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button\\n'))\n",
    "R.append(patch('duelclient.h',\n"
    "    '\\tstatic int GetSpectatorsCount() {\\n',\n"
    "    '\\tstatic bool jtp_join_as_spectator; // JTP: set by the Watch button (public)\\n\\tstatic int GetSpectatorsCount() {\\n'))\n"))
