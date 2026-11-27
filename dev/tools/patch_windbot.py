"""Patch WindBot (D:/YugiohReturn/windbot) for Joey The Passion: JTP_* decks use JoeyExecutor."""
import io, re, os
os.chdir(r'D:\YugiohReturn\windbot')


def edit(path, old, new):
    s = io.open(path, encoding='utf-8-sig', newline='').read()
    if new in s:
        return
    assert s.count(old) == 1, (path, old)
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new))


nl = '\r\n' if b'\r\n' in open('Game/DecksManager.cs', 'rb').read() else '\n'
edit('Game/DecksManager.cs',
     '            if (deck != null && _decks.ContainsKey(deck))',
     '            if (deck != null && !_decks.ContainsKey(deck) && deck.StartsWith("JTP_"))' + nl +
     '            {' + nl +
     '                // Joey The Passion decks: generic classic AI with the deck file AI_<deck>.ydk' + nl +
     '                infos = new DeckInstance("AI_" + deck, typeof(WindBot.Game.AI.Decks.JoeyExecutor), "Normal");' + nl +
     '                Logger.WriteLine("JTP deck, loading " + infos.Deck);' + nl +
     '            }' + nl +
     '            else if (deck != null && _decks.ContainsKey(deck))')

# WindBot.csproj compiles Game\AI\Decks\*.cs, so JoeyExecutor.cs is picked up automatically.
print('windbot patched')
