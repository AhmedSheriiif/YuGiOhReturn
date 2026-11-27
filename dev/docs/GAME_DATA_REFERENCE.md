# Yu-Gi-Oh! Power of Chaos: Joey The Passion: Game Data Reference

Reverse-engineered on 2026-11-26. Status tags: **[confirmed]** = verified against the data or the decompiled code, **[inferred]** = strong pattern but not proven, **[unknown]** = not yet analyzed.

Game folder: `C:\Users\ahmed\OneDrive\Desktop\Yu-Gi-Oh!\Yu-Gi-Oh!\Joey The Passion`
Common folder: `...\Yu-Gi-Oh!\Yu-Gi-Oh!\Yu-Gi-Oh! Power of Chaos Common`

## 1. Shipped files

| File | Size | What it is |
|---|---|---|
| `joey_pc.exe` | 2.0 MB | Main game. Win32 x86, MSVC C++, 6,495 functions. Carries a `MYTH/DEViANCE` scene-crack tag (no-CD). SHA-256 `db8fe7b7…05b6de` |
| `data.dat` | 319 MB | KCEJYUGI archive, 3,568 entries (graphics, card DB, layouts, AI decks) |
| `Voice.dat` | 145 MB | KCEJYUGI archive, 132 entries (Joey voice and SFX WAVs, stored uncompressed) |
| `Region.dat` | 1 B | `0x11`, region/language byte, read by `FUN_0040f510` |
| `deck.ydc` | 130 B | Player deck (format in §5) |
| `exporter.exe` | 64 KB | Small MSVC tool (deck exporter?), no meaningful strings [unknown] |
| `SetupReg.exe` | 8 KB | Crack-group registry writer ("MYTH/DYNASTY"), writes `HKLM\SOFTWARE\KONAMI\Yu-Gi-Oh! Power Of Chaos[\system]` |
| `BattleLANv0.5.exe` | 268 KB | Third-party UDP LAN-broadcast forwarder (Infoceptor, 2002). Not part of the game |
| `setup.bat`, `READMENOW.txt` | | Crack-release install steps |

## 2. KCEJYUGI archive (`data.dat`, `Voice.dat`) [confirmed]

```
0x00  char[8]  "KCEJYUGI"
0x08  u32      entry_count
0x0C  entry[entry_count], each 0x10C bytes:
        char[256] name    (NUL-padded, every byte nibble-swapped: (b<<4|b>>4)&0xFF)
        u32       offset  (absolute file offset)
        u32       unpacked_size
        u32       packed_size  (== unpacked_size means stored raw)
```
Compression is **Okumura LZSS**: 4096-byte ring buffer filled with 0, write start `N-F` = 4078, flag byte read LSB-first (1 = literal byte, 0 = 2-byte match), `pos = b0 | (b1&0xF0)<<4`, `len = (b1&0x0F)+3`.
All 3,700 entries decompress to their exact declared sizes.

The directory name really is `bin#` (the exe opens `data/bin#/CARD_*.bin`).

Tools: `tools/kcej.py` (index, LZSS, extract) and `tools/extract_all.py`. Output goes to `extracted/data`, `extracted/voice`.

### data.dat contents
| Folder | Count | Content |
|---|---|---|
| `card/` | 778 | Full card art BMP 200×290 24-bit, plus `list_card.txt` (index → Konami ID → bmp) |
| `mini/` | 778 | Small card thumbnails |
| `bin#/` | 41 | Card database and dialog text (§3) |
| `cursor/` | 68 | Action cursors (`.yga`), one set per language e/f/g/i/s |
| `j/title`, `j/janken`, `j/list`, `j/tutorial` | | Menus, rock-paper-scissors, tutorial |
| `j/duel/*` | ~900 | Duel field, phases, chain, effects, LP, help, exodia, dialogs |
| `j/deck_c/*` | ~400 | Deck construction UI, import/export, replay, filters |
| `j/bust_up/*` | | Joey portrait reactions, win/lose/draw banners, summon cut-ins |
| `j/lan_duel/` | 40 | LAN duel screens |
| `j/file/` | 58 `.ydc` | AI decks: `cpu_0xx.ydc` (Joey levels), `ful_*.ydc` |

## 3. Card database (`bin#/`) [confirmed unless marked]
1,115 card slots (index 0 = card back). All tables are indexed by internal index `i`.

| File | Layout |
|---|---|
| `card_id.bin` | u16[1115]: Konami card ID (`list_card.txt` "0001:[1504]") |
| `card_intid.bin` | u16[2048]: reverse map from Konami ID to index [inferred] |
| `card_pass.bin` | u32[1115]: passcode as **BCD bytes in order** (`67 10 52 42` = 67105242) |
| `card_prop.bin` | u32[1115]: bitfield, see below |
| `card_pack.bin` | u16[1115]: values 0–6, pack/rarity/unlock group [inferred] |
| `card_name{eng,fra,ger,ita,jpn,spa}.bin` | char[1115][64] fixed-width names |
| `card_desc*.bin` + `card_indx*.bin` | descriptions blob + u32 offsets per index |
| `card_sort*.bin` | u16[2048]: alphabetical sort order |
| `dlg_text*.bin` + `dlg_indx*.bin` | UI/dialog strings + offsets |

### `card_prop.bin` bitfield
```
bits  0- 8  DEF / 10
bits  9-17  ATK / 10
bits 18-19  kind: 0 Normal, 1 Effect, 2 Fusion (Continuous for S/T), 3 Ritual
bits 20-24  type: 1 Dragon 2 Zombie 3 Fiend 4 Pyro 5 Sea Serpent 6 Rock 7 Machine 8 Fish
                  9 Dinosaur 10 Insect 11 Beast 12 Beast-Warrior 13 Plant 14 Aqua
                  15 Warrior 16 Winged Beast 17 Fairy 18 Spellcaster 19 Thunder 20 Reptile
                  21 TRAP 22 SPELL 23 (Glory of the King's Hand) 24 Divine-Beast
bits 25-28  level
bits 29-31  attribute: 1 Light 2 Dark 3 Water 4 Fire 5 Earth 6 Wind (S/T: 0 or 1)
```
Card effects are **not** in data files. They are hard-coded in `joey_pc.exe`.

## 4. Images
- `.bmp`: standard Windows BMP.
- `.yga` [confirmed]: `"yga\0"`, u32 width, u32 height, u32 compressed_flag, u32 unpacked_size, u32 packed_size, then LZSS data → 32-bit **BGRA** pixels. `tools/yga2png.py` converted all 537 → `extracted/png/`.
- `.sue`: `"SUECAT"` thumbnail catalogue [unknown].
- Layout `.txt` files: `name  XXXYYY[...]  // Shift-JIS comment`, which places sprites at packed coordinates.

## 5. Deck file `.ydc` [confirmed]
```
0x00 u8[8]  header (purpose unknown, e.g. 01 f3 12 00 57 54 cb 3f)
then 3 lists, each: u16 count, u16[count] Konami card IDs
  list0 = main deck (40), list1 = fusion deck (≤10?), list2 = side deck (8)
```

## 6. Save data and registry
- Registry (32-bit view): `HKLM\SOFTWARE\WOW6432Node\KONAMI\Yu-Gi-Oh! Power Of Chaos\system`
  - `InstallDirJ`: game folder, `CommonDir`: shared folder, `Lang` (2 = English?), `flcrc`: save checksum (binary)
  - LAN: `PlayerName` (default "Nameless"), `HostName`, `PortNo`
- `<CommonDir>\system.dat`: save file (5,062 B), bit-packed, verified against `flcrc` (`FUN_0045ca80`) [format unknown]
- ⚠ **Current setup mismatch:** `CommonDir` = `C:\Users\ahmed\OneDrive\Desktop\Yu-Gi-Oh! Power Chaos common` (contains only custom `.ydc` decks, **no system.dat**). The real Common folder has only `system111.dat` and backups.

## 7. Engine and tech stack (from the decompiled exe) [confirmed]
- Graphics: **DirectDraw** (CLSID D7B70EE0…), "Please Install DirectX9"
- Audio: **DirectSound** + **DirectShow** AMMultiMediaStream (voice/BGM, `.PAX/.PAD`), MSACM
- Input: **DirectInput** (`dinput.dll` loaded dynamically)
- Network: **DirectPlay 8 Peer** (CLSID 286F484D…), TCP/IP service provider. `FUN_004014e0` builds an `IDirectPlay8Address` from `HostName` + `port` and calls `EnumHosts`. There is no Winsock import.
  - DirectPlay is a deprecated Windows feature (must be enabled under "Legacy Components" on Win10/11). This is a likely cause of LAN bugs.
- Command-line switches: `-Leng`, `-Lita` (language), `-speedy`, `-nosound`; debug string `FPS:%d/%d`.

## 8. Reverse-engineering artifacts
- `re/decompiled_all.c`: Ghidra pseudocode for all 6,495 functions
- `re/functions.tsv`, `re/imports.txt`, `re/strings_xrefs.txt` (string → referencing functions)
- Ghidra project: `C:\Users\ahmed\tools\ghidra_projects\JoeyPassion` (needs JDK 21: `C:\Program Files\Java\jdk-21.0.12`)

## 9. Open questions
- Duel rules engine and card-effect implementations: where they live in the exe
- `system.dat` encoding and `flcrc` algorithm
- DirectPlay message protocol (packet types exchanged during a LAN duel)
- `.sue` format, `.ydc` header meaning, `card_pack` semantics, `exporter.exe` purpose

## 10. Implication for an Android online port
The original exe cannot run on Android, and its netcode is Windows-only DirectPlay. A practical port is a **new client** (Unity/Godot or web/PWA) that reuses the extracted assets and card DB above, with a new rules engine and a server for online play. All the asset and data formats needed for that are now decoded.
